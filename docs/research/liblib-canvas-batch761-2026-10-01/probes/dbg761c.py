#!/usr/bin/env python3
"""batch 761 探针 c：滚轮「隔一个才动」是产品行为还是探针读数滞后？

761a/761b 都看到同一个形状：4 次滚轮，`Δy = [0, 240, 0, -240]`。
两种解释都说得通：

  (A) 产品行为 —— 4 次里只有 2 次真的生效（up2 / down2）
  (B) 探针读数滞后一拍 —— `store.viewport` 的提交比我的读数晚，于是
      「up1 的位移」被记在了 up2 那一格上

单看读数分不开。三条独立证据同时上：

① **中途不读** —— 连发 4 次滚轮，只在最后读一次。总位移是 4×240=960 就说明
   每次都生效（(B)），是 2×240=480 就说明只有一半生效（(A)）。
② **DOM transform 当第三方** —— `.react-flow__viewport` 的 matrix 由 React Flow
   直接改，不经过 store 提交；如果 DOM 也只动 2 次，(B) 就站不住。
③ **应用自己的账** —— `window.__libtv_viewport_owner_log` 里每次真正落地的
   视口会记一条 `viewport-accepted`，中间帧记 `live-frame`。数一数接受了几次。

另外顺手把两件事钉掉：
  - 缩放按钮在 640–850px 隐藏 ⟹ `data-viewport-menu-trigger` 是缩放菜单
    **唯一**入口（grep 已证），所以那一段只剩 ⌘+/⌘-/⌘0 三个快捷键。
  - 640px 以下会不会又露出来（`sm:` 是 min-width 变体，两段都要覆盖才能断言）。
"""
import json
import pathlib
import re
from playwright.sync_api import sync_playwright

BASE = "http://localhost:4317"
RAW = pathlib.Path(
    "/Users/yangjiefeng/Documents/wubuku/liblib-tv"
    "/docs/research/liblib-canvas-batch761-2026-10-01/raw/vb761c.json")

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
   accepted:l.filter(e=>e.reason==='viewport-accepted').length,
   liveFrames:l.filter(e=>e.reason==='live-frame').length,
   logLen:l.length};}"""

PANE_PT = """()=>{for(let y=140;y<innerHeight-220;y+=12)
 for(let x=180;x<innerWidth-200;x+=12){
  const e=document.elementFromPoint(x,y); if(!e||!e.closest)continue;
  if(!e.closest('.react-flow__pane'))continue;
  if(e.closest('.react-flow__node')||e.closest('.react-flow__edge'))continue;
  if(e.closest('button,input,select,textarea,[role="button"]'))continue;
  return {x:x,y:y};}
 return null;}"""


def count_accepted(pg):
    return pg.evaluate(
        "()=>(window.__libtv_viewport_owner_log||[])"
        ".filter(e=>e.reason==='viewport-accepted').length")


def burst(pg, n, dy, gap):
    """连发 n 次滚轮，中途不读，只在最后读一次 —— 专门分辨 (A) / (B)"""
    before = pg.evaluate(READ)
    acc_before = count_accepted(pg)
    for _ in range(n):
        pg.mouse.wheel(0, dy)
        pg.wait_for_timeout(gap)
    pg.wait_for_timeout(1400)
    after = pg.evaluate(READ)
    acc_after = count_accepted(pg)
    return {"n": n, "deltaY": dy, "gap": gap,
            "before": before, "after": after,
            "storeDy": round(after["store"]["y"] - before["store"]["y"], 2),
            "storeDz": round(after["store"]["zoom"]
                             - before["store"]["zoom"], 4),
            "domDy": (after["dom"]["y"] - before["dom"]["y"]
                      if after["dom"] and before["dom"] else None),
            "domDz": (round(after["dom"]["zoom"] - before["dom"]["zoom"], 4)
                      if after["dom"] and before["dom"] else None),
            "acceptedDelta": acc_after - acc_before}


def zoom_trigger(width):
    return """(w)=>{const t=document.querySelector(
      '[data-viewport-menu-trigger="zoom"]');
     if(!t) return {inDom:false};
     const cs=getComputedStyle(t), ps=getComputedStyle(t.parentElement);
     const r=t.getBoundingClientRect();
     return {inDom:true, w:Math.round(r.width),
       parentDisplay:ps.display, display:cs.display,
       parentClass:(t.parentElement.getAttribute('class')||'').slice(0,90),
       text:t.textContent.trim(),
       visible:r.width>0 && ps.display!=='none' && cs.display!=='none'};}""" \
        .replace("(w)=>{", "()=>{")


def main():
    res = {"batch": 761, "probe": "c", "rounds": []}
    with sync_playwright() as p:
        br = p.chromium.launch()
        for _ in range(2):
            R = {}
            pg = br.new_page(viewport={"width": 1440, "height": 1000})
            pg.goto(BASE, wait_until="networkidle")
            pg.wait_for_selector(".react-flow__node", timeout=20000)
            pg.wait_for_timeout(1100)

            pt = pg.evaluate(PANE_PT)
            R["panePoint"] = pt
            if not pt:
                R["FAILED"] = "找不到 pane 空白点"
                pg.close()
                res["rounds"].append(R)
                continue
            pg.mouse.move(pt["x"], pt["y"])
            pg.wait_for_timeout(500)

            # ① 中途不读的连发
            R["burstSlow"] = burst(pg, 4, -120, 250)      # 4 次向上
            pg.mouse.move(pt["x"], pt["y"])
            pg.wait_for_timeout(600)
            R["burstFast"] = burst(pg, 6, -120, 40)       # 6 次向上、几乎连发
            pg.mouse.move(pt["x"], pt["y"])
            pg.wait_for_timeout(600)
            R["burstDown"] = burst(pg, 3, 120, 250)      # 3 次向下

            # ② 缩放按钮在 560 / 700 / 800 / 900 / 1440 各是什么状态
            trig = []
            for w in (560, 700, 800, 900, 1440):
                pg.set_viewport_size({"width": w, "height": 900})
                pg.wait_for_timeout(700)
                t = pg.evaluate(zoom_trigger(w))
                t["width"] = w
                trig.append(t)
            R["triggerByWidth"] = trig
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
    for k in ("burstSlow", "burstFast", "burstDown"):
        b = r1.get(k, {})
        print("%-10s ×%d Δy=%s storeΔy=%s domΔy=%s storeΔz=%s 接受次数Δ=%s"
              % (k, b.get("n", 0), b.get("deltaY"), b.get("storeDy"),
                 b.get("domDy"), b.get("storeDz"), b.get("acceptedDelta")))
        if b.get("after"):
            print("            after: store=%s dom=%s accepted=%d live=%d"
                  % (json.dumps(b["after"]["store"], ensure_ascii=False),
                     json.dumps(b["after"]["dom"], ensure_ascii=False),
                     b["after"]["accepted"], b["after"]["liveFrames"]))
    for t in r1.get("triggerByWidth", []):
        print("宽度 %-5d 缩放按钮 可见=%-5s w=%-3s 父display=%-5s text=%s"
              % (t.get("width"), t.get("visible"), t.get("w"),
                 t.get("parentDisplay"), t.get("text")))


if __name__ == "__main__":
    main()
