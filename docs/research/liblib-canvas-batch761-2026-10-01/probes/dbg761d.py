#!/usr/bin/env python3
"""batch 761 探针 d：store 视口与 DOM 视口分叉，是动画没走完还是真的丢了提交？

761c 的 burstDown 抓到一个矛盾：

  3 次向下滚轮，每格固定 120 ⟹ 期望 Δy = -360
  实测 DOM  `.react-flow__viewport`  Δy = -360  ✅
  实测 store `canvas.viewport`       Δy = -240  ❌ 少了一格
  （读取点在最后一次滚轮之后 1400ms）

两种解释：
  (A) 动画/提交还在路上 —— 再等一会两者就相等
  (B) 有一帧 live-frame 从未被提交成 viewport-accepted ⟹ store 真的落后了

这条要紧，因为 store 里的 `canvas.viewport` 是**会被持久化到画布对象**的：
落后一格意味着切换画布再切回来、或者将来接上真持久化时，视口会被恢复到错的位置。

判法：在同一页上按时间点连续读 store 与 DOM，看两者是否收敛。
再用 ownerLog 的尾部（每条 reason/status）看最后到底发生了什么。
"""
import json
import pathlib
import re
from playwright.sync_api import sync_playwright

BASE = "http://localhost:4317"
RAW = pathlib.Path(
    "/Users/yangjiefeng/Documents/wubuku/liblib-tv"
    "/docs/research/liblib-canvas-batch761-2026-10-01/raw/vb761d.json")

READ = """()=>{const s=window.__libtv_store.getState(); const c=s.getActiveCanvas();
 const vp=(c&&c.viewport)||null;
 const dom=document.querySelector('.react-flow__viewport');
 let dz=null,dx=null,dy=null;
 if(dom){const cs=getComputedStyle(dom).transform;
  if(cs&&cs!=='none'){const m=cs.match(/matrix\\(([^,]+),[^,]+,[^,]+,([^,]+),([^,]+),([^\\)]+)\\)/);
   if(m){dz=Math.round(+m[1]*10000)/10000;dx=+m[3];dy=+m[4];}}}
 const l=window.__libtv_viewport_owner_log||[];
 return {store:vp?{x:Math.round(vp.x*100)/100,y:Math.round(vp.y*100)/100,
                   zoom:Math.round(vp.zoom*1000)/1000}:null,
   dom:dz===null?null:{zoom:dz,x:Math.round(dx),y:Math.round(dy)},
   gap:null,
   tail:l.slice(-8).map(e=>({status:e.status,reason:e.reason,
                             ownership:e.ownership})),
   logLen:l.length};}"""

PANE_PT = """()=>{for(let y=140;y<innerHeight-220;y+=12)
 for(let x=180;x<innerWidth-200;x+=12){
  const e=document.elementFromPoint(x,y); if(!e||!e.closest)continue;
  if(!e.closest('.react-flow__pane'))continue;
  if(e.closest('.react-flow__node')||e.closest('.react-flow__edge'))continue;
  if(e.closest('button,input,select,textarea,[role="button"]'))continue;
  return {x:x,y:y};}
 return null;}"""


def read(pg):
    r = pg.evaluate(READ)
    if r["store"] and r["dom"]:
        r["gap"] = {"x": round(r["store"]["x"] - r["dom"]["x"], 2),
                    "y": round(r["store"]["y"] - r["dom"]["y"], 2),
                    "zoom": round(r["store"]["zoom"] - r["dom"]["zoom"], 4)}
    return r


def main():
    res = {"batch": 761, "probe": "d", "rounds": []}
    with sync_playwright() as p:
        br = p.chromium.launch()
        for _ in range(2):
            R = {}
            pg = br.new_page(viewport={"width": 1440, "height": 1000})
            pg.goto(BASE, wait_until="networkidle")
            pg.wait_for_selector(".react-flow__node", timeout=20000)
            pg.wait_for_timeout(1100)
            pt = pg.evaluate(PANE_PT)
            if not pt:
                R["FAILED"] = "找不到 pane 空白点"
                pg.close()
                res["rounds"].append(R)
                continue
            pg.mouse.move(pt["x"], pt["y"])
            pg.wait_for_timeout(500)

            R["t0"] = read(pg)
            # 3 次向下滚轮，中间不读
            for _ in range(3):
                pg.mouse.wheel(0, 120)
                pg.wait_for_timeout(250)
            # 立刻读，然后按时间点连读，看是否收敛
            marks = {}
            acc = 0
            for ms in (0, 500, 1500, 3000, 5000):
                if ms:
                    pg.wait_for_timeout(ms - acc)
                    acc = ms
                marks["t+%dms" % ms] = read(pg)
            R["timeline"] = marks
            gaps = [m["gap"] for m in marks.values()]
            R["converged"] = gaps[-1] == {"x": 0.0, "y": 0.0, "zoom": 0.0}
            R["gapSeries"] = gaps
            # 收敛后再来一次同样的滚轮，看「落后一格」是否可复现
            pg.mouse.move(pt["x"], pt["y"])
            pg.wait_for_timeout(400)
            b = read(pg)
            for _ in range(3):
                pg.mouse.wheel(0, -120)
                pg.wait_for_timeout(250)
            pg.wait_for_timeout(3000)
            a = read(pg)
            R["secondBurst"] = {"before": b, "after": a, "gap": a["gap"],
                                "storeDy": round(a["store"]["y"] - b["store"]["y"], 2),
                                "domDy": round(a["dom"]["y"] - b["dom"]["y"], 2)}
            pg.close()
            res["rounds"].append(R)
        br.close()

    def strip(o):
        if isinstance(o, str):
            return re.sub(r"-\d{10,}-[a-z0-9]{6}\b", "-<gen>", o)
        if isinstance(o, dict):
            return {k: strip(v) for k, v in o.items()}
        if isinstance(o, list):
            return [strip(v) for v in o]
        return o

    r1, r2 = res["rounds"][0], res["rounds"][1]
    diff = {k: {"round1": strip(r1.get(k)), "round2": strip(r2.get(k))}
            for k in set(r1) | set(r2) if strip(r1.get(k)) != strip(r2.get(k))}
    res["roundDiff"] = diff
    res["consistent"] = (len(diff) == 0)
    RAW.parent.mkdir(parents=True, exist_ok=True)
    RAW.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")

    print("consistent =", res["consistent"], "| diff =", sorted(diff))
    print("store−DOM 差距时间线:", json.dumps(r1.get("gapSeries"),
                                              ensure_ascii=False))
    print("5 秒后是否收敛:", r1.get("converged"))
    for k, m in (r1.get("timeline") or {}).items():
        if m.get("store"):
            print("  %-9s store.y=%-9s dom.y=%-9s 差距=%s logLen=%d"
                  % (k, m["store"]["y"], m["dom"]["y"], json.dumps(m["gap"]),
                     m["logLen"]))
    print("尾部日志:", json.dumps((r1.get("t+5000ms") or {}).get("tail"),
                                  ensure_ascii=False))
    sb = r1.get("secondBurst") or {}
    print("第二轮 3 次上滚: storeΔy=%s domΔy=%s 差距=%s"
          % (sb.get("storeDy"), sb.get("domDy"),
             json.dumps(sb.get("gap"), ensure_ascii=False)))


if __name__ == "__main__":
    main()
