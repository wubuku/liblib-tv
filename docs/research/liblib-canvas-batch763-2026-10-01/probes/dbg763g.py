#!/usr/bin/env python3
"""batch 763 探针 g：两次加载的导演台基础对象数不一样，是异步加载还是构造不确定？

763b 两轮实测：round 1 树里 6 个对象（含 character），round 2 只有 5 个（无 character）。
这会让 B1 属性面板的控件数跟着变（35 vs 33），所以必须定性，否则
「B1 两轮不一致」就没法归因到焦点行为上。

本探针在 1440 宽度开一次导演台后，**在同一次会话里按时间点连读 4 次**对象列表
（0.6s / 1.6s / 3.2s / 6.0s），两轮：
  - 若对象数随时间增长 ⟹ 异步加载（character 之类要等资源/清单）
  - 若一次到位且两轮总数仍不同 ⟹ 构造本身不确定
两种结论对「B1 差异归因」的影响完全不同，必须分开记。
"""
import json
import pathlib
from playwright.sync_api import sync_playwright

BASE = "http://localhost:4317"
OUT = pathlib.Path(
    "/Users/yangjiefeng/Documents/wubuku/liblib-tv"
    "/docs/research/liblib-canvas-batch763-2026-10-01/raw/vb763g.json")

TIMES_MS = [600, 1600, 3200, 6000]

OBJECTS = """()=>{const d=document.querySelector(
  '[role="dialog"][aria-modal="true"]');
 if(!d) return {err:'no dialog'};
 const t=d.querySelector('aside[aria-label="场景对象"]');
 if(!t) return {err:'no tree'};
 const rows=[];
 for(const e of t.querySelectorAll('[data-director-object-id]')){
   const r=e.getBoundingClientRect();
   if(r.width<=0||r.height<=0) continue;
   rows.push({id:e.getAttribute('data-director-object-id'),
     kind:e.getAttribute('data-director-object-kind'),
     selected:e.getAttribute('data-director-object-selected'),
     text:(e.textContent||'').trim().slice(0,20)});}
 const ids=rows.map(r=>r.id);
 const dup=ids.filter((v,i)=>ids.indexOf(v)!==i);
 return {count:rows.length, rows:rows,
   duplicateIds:[...new Set(dup)],
   kinds:rows.reduce((a,r)=>{a[r.kind]=(a[r.kind]||0)+1; return a;},{}),
   fullLengths:ids.map(s=>s.length)};}"""

SCAN_CLICK = """(sel)=>{const el=document.querySelector(sel);
 if(!el) return {missing:true};
 const r=el.getBoundingClientRect();
 for(let f=0.1; f<=0.95; f+=0.07) for(let g=0.1; g<=0.95; g+=0.07){
   const x=Math.round(r.x+r.width*f), y=Math.round(r.y+r.height*g);
   if(x<2||y<2||x>innerWidth-2||y>innerHeight-2) continue;
   const e=document.elementFromPoint(x,y);
   if(e&&e.closest&&e.closest(sel)) return {pt:[x,y]};}
 return {noHit:true};}"""


def settle(pg, tries=8, gap=220):
    prev, same = None, 0
    for _ in range(36):
        cur = pg.evaluate("""()=>{const v=window.__libtv_store.getState()
          .getActiveCanvas().viewport; return [v.x,v.y,v.zoom].join('|');}""")
        same = same + 1 if cur == prev else 0
        prev = cur
        if same >= tries:
            return cur
        pg.wait_for_timeout(gap)
    return prev


def run_round(pg, R):
    pg.set_viewport_size({"width": 1440, "height": 1000})
    pg.goto(BASE, wait_until="networkidle")
    pg.wait_for_selector(".react-flow__node", timeout=25000)
    pg.wait_for_timeout(1200)
    pg.keyboard.press("Meta+0")
    pg.wait_for_timeout(600)
    settle(pg)
    s = pg.evaluate(SCAN_CLICK, "[data-open-director]")
    if not s.get("pt"):
        R["FAILED_open"] = s
        return
    R["openClick"] = s
    pg.mouse.click(s["pt"][0], s["pt"][1])
    try:
        pg.wait_for_selector('[role="dialog"][aria-modal="true"]', timeout=25000)
    except Exception:
        R["FAILED_open"] = "点了但没 dialog"
        return
    R["samples"] = []
    elapsed = 0
    for t in TIMES_MS:
        pg.wait_for_timeout(t - elapsed)
        elapsed = t
        r = pg.evaluate(OBJECTS)
        r["atMs"] = t
        R["samples"].append(r)
        print("   t=%-5s count=%-3s kinds=%s dup=%s"
              % (t, r.get("count"), json.dumps(r.get("kinds"),
                                              ensure_ascii=False),
                 r.get("duplicateIds")))
    counts = [x.get("count") for x in R["samples"]]
    R["countSeries"] = counts
    R["grewOverTime"] = (len(set(counts)) > 1)
    R["duplicateIdsFinal"] = R["samples"][-1].get("duplicateIds")


def main():
    res = {"batch": 763, "probe": "g",
           "question": "两次加载基础对象数不同：异步加载还是构造不确定？",
           "timesMs": TIMES_MS, "rounds": []}
    with sync_playwright() as p:
        br = p.chromium.launch()
        pg = br.new_page(viewport={"width": 1440, "height": 1000})
        try:
            for i in range(2):
                R = {}
                res["rounds"].append(R)
                print("round %d" % (i + 1))
                run_round(pg, R)
        finally:
            OUT.parent.mkdir(parents=True, exist_ok=True)
            try:
                br.close()
            except Exception:
                pass
            OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1),
                           encoding="utf-8")
    a, b = res["rounds"]
    print("\ncountSeries 两轮 =", a.get("countSeries"), "/",
          b.get("countSeries"))
    print("会话内随时间增长 =", a.get("grewOverTime"), "/",
          b.get("grewOverTime"))
    print("两轮最终 count =", (a.get("samples") or [{}])[-1].get("count"),
          "/", (b.get("samples") or [{}])[-1].get("count"))
    print("重复 id =", a.get("duplicateIdsFinal"), "/",
          b.get("duplicateIdsFinal"))
    for i, R in enumerate(res["rounds"], 1):
        rows = (R.get("samples") or [{}])[-1].get("rows") or []
        print("r%d 完整 id 长度集合 = %s"
              % (i, sorted({len(x["id"]) for x in rows})))
        for x in rows:
            print("     %-34s %-9s %s" % (x["id"], x["kind"], x["text"]))
    print("wrote %s" % OUT)


if __name__ == "__main__":
    main()
