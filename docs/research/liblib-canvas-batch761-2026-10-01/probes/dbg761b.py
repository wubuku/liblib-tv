#!/usr/bin/env python3
"""batch 761 探针 b：响应式视口那半支 + 把滚轮重测成不受探针干扰的版本

761a 已经坐实的：桌面档 `desktopViewport` 逐位生效
（store x=-583.8 / y=260.8 / zoom=0.526，与 `page.tsx:163` 的常量全等）。

这一段补三件事：

① **紧凑档**：`page.tsx:452` 与 `:1148` 都用
   `window.matchMedia("(max-width: 768px)").matches ? compactViewport : desktopViewport`
   ⟹ 宽度 ≤768 时首屏应当逐位等于 `{x:17, y:128, zoom:0.28}`。
   两档用同一段代码跑，做成真正的 A/B，而不是各跑各的。

② **滚轮重测**：761a 那四步里「第一步 Δ 全 0、第二步才动」的形状，
   高度怀疑是**探针自己的问题** —— `settle()` 只盯 zoom，而滚轮平移是
   d3 过渡、zoom 全程不变 ⟹ settle 立刻返回，第一个滚轮还在动画里，
   第二个就被吞了。所以这里改成**固定长等待、不轮询**，四步各等 900ms。
   Δz 是否恒为 0 才算站得住。

③ **缩放指示器在窄屏还在不在**：`BottomToolbar.tsx:122` 的容器 class 是
   `sm:max-[850px]:hidden` ⟹ 按 Tailwind 语义（`sm:` 是 min-width 变体）
   640–850px 这一段该被隐藏，低于 640px 又该露出来。这个组合本身就可疑，
   实测一下。

④ 顺带把 `window.__libtv_viewport_owner_log` 的真实内容抓下来 ——
   这套「bootstrap / stable 视口归属」机制是 batch 748 留下的
   「调试钩子来源」那条线索的落点。
"""
import json
import pathlib
import re
from playwright.sync_api import sync_playwright

BASE = "http://localhost:4317"
RAW = pathlib.Path(
    "/Users/yangjiefeng/Documents/wubuku/liblib-tv"
    "/docs/research/liblib-canvas-batch761-2026-10-01/raw/vb761b.json")

DESKTOP = {"x": -583.8, "y": 260.8, "zoom": 0.526}
COMPACT = {"x": 17, "y": 128, "zoom": 0.28}

VP = """()=>{const u=window.__libtv_ui_store.getState();
 const s=window.__libtv_store.getState(); const c=s.getActiveCanvas();
 const vp=(c&&c.viewport)||null;
 const dom=document.querySelector('.react-flow__viewport');
 let domZoom=null,domXY=null;
 if(dom){const cs=getComputedStyle(dom).transform;
  if(cs&&cs!=='none'){const m=cs.match(/matrix\\(([^,]+),[^,]+,[^,]+,([^,]+),([^,]+),([^\\)]+)\\)/);
   if(m){domXY=[Math.round(+m[3]),Math.round(+m[4])];
         domZoom=Math.round(+m[1]*1000)/1000;}}}
 const trig=document.querySelector('[data-viewport-menu-trigger="zoom"]');
 let trigVis=null;
 if(trig){const r=trig.getBoundingClientRect(); const cs=getComputedStyle(trig);
   trigVis={inDom:true,w:Math.round(r.width),h:Math.round(r.height),
            display:cs.display,visibility:cs.visibility,
            parentDisplay:getComputedStyle(trig.parentElement).display,
            parentClass:(trig.parentElement.getAttribute('class')||'').slice(0,120),
            text:trig.textContent.trim()};}
 return {zoomLevel:u.zoomLevel,
   store:vp?{x:Math.round(vp.x*100)/100,y:Math.round(vp.y*100)/100,
             zoom:Math.round(vp.zoom*1000)/1000}:null,
   dom:domZoom===null?null:{zoom:domZoom,x:domXY[0],y:domXY[1]},
   triggerText:trig?trig.textContent.trim():null,
   triggerVisible:trigVis,
   innerWidth:innerWidth, innerHeight:innerHeight,
   mq768:window.matchMedia('(max-width: 768px)').matches,
   activeCanvasId:s.activeCanvasId};}"""

OWNER_LOG = "()=>{const l=window.__libtv_viewport_owner_log;"\
            "return l===undefined?null:{length:l.length,"\
            "entries:l.slice(0,12).map(e=>({canvasId:e.canvasId,status:e.status,"\
            "reason:e.reason,ownership:e.ownership}))};}"

PANE_PT = """()=>{for(let y=140;y<innerHeight-220;y+=12)
 for(let x=180;x<innerWidth-200;x+=12){
  const e=document.elementFromPoint(x,y); if(!e||!e.closest)continue;
  if(!e.closest('.react-flow__pane'))continue;
  if(e.closest('.react-flow__node')||e.closest('.react-flow__edge'))continue;
  if(e.closest('button,input,select,textarea,[role="button"]'))continue;
  return {x:x,y:y};}
 return null;}"""


def near(a, b, tol=0.001):
    return (a is not None and b is not None
            and abs(a - b) <= tol)


def vp_matches(store, const):
    if not store:
        return False
    return {"x": near(store["x"], const["x"]),
            "y": near(store["y"], const["y"]),
            "zoom": near(store["zoom"], const["zoom"])}


def d3(a, b):
    if not a or not b:
        return None
    return {"dx": round(b["x"] - a["x"], 2), "dy": round(b["y"] - a["y"], 2),
            "dz": round(b["zoom"] - a["zoom"], 4)}


def load_at(br, w, h):
    pg = br.new_page(viewport={"width": w, "height": h})
    pg.goto(BASE, wait_until="networkidle")
    pg.wait_for_selector(".react-flow__node", timeout=20000)
    pg.wait_for_timeout(1100)        # 只等渲染，不做任何交互
    return pg


def clean_wheel(pg, label):
    """固定长等待、不轮询 —— 专治「第一步 Δ 全 0」那种探针自伤"""
    pt = pg.evaluate(PANE_PT)
    if not pt:
        return {"FAILED": "找不到 pane 空白点"}
    pg.mouse.move(pt["x"], pt["y"])
    pg.wait_for_timeout(500)
    prev = pg.evaluate(VP)["store"]
    steps = []
    for name, dy in (("up1", -120), ("up2", -120), ("down1", 120),
                     ("down2", 120)):
        pg.mouse.wheel(0, dy)
        pg.wait_for_timeout(900)      # ← 不轮询，固定等动画走完
        cur = pg.evaluate(VP)
        steps.append({"step": name, "deltaY": dy, "store": cur["store"],
                      "delta": d3(prev, cur["store"]),
                      "indicator": cur["zoomLevel"]})
        prev = cur["store"]
    deltas = [s["delta"] for s in steps if s["delta"]]
    return {"point": pt, "steps": steps,
            "allDzZero": all(abs(d["dz"]) < 1e-9 for d in deltas),
            "anyDyMoved": any(abs(d["dy"]) > 0 for d in deltas),
            "anyDxMoved": any(abs(d["dx"]) > 0 for d in deltas),
            "dyValues": [d["dy"] for d in deltas]}


def wheel_over_node(pg):
    """滚轮落在节点上会怎样？（handle 带 nopan，正文没有）"""
    pos = pg.evaluate("""()=>{const els=[...document.querySelectorAll(
        '.react-flow__node:not([data-id^="g-"])')];
      for(const el of els){const r=el.getBoundingClientRect();
        if(r.width<60||r.height<50) continue;
        if(r.x<20||r.y<20||r.right>innerWidth-20||r.bottom>innerHeight-160) continue;
        const x=Math.round(r.x+r.width/2), y=Math.round(r.y+r.height/2);
        const e=document.elementFromPoint(x,y);
        if(!e) continue;
        return {x:x,y:y,node:el.getAttribute('data-id'),
                tag:e.tagName,
                cls:(e.getAttribute('class')||'').slice(0,80),
                nodrag:!!(e.closest('.nodrag')), nopan:!!(e.closest('.nopan'))};}
      return null;}""")
    if not pos:
        return {"FAILED": "找不到视口内的节点"}
    pg.mouse.move(pos["x"], pos["y"])
    pg.wait_for_timeout(400)
    before = pg.evaluate(VP)["store"]
    pg.mouse.wheel(0, -120)
    pg.wait_for_timeout(900)
    cur = pg.evaluate(VP)
    return {"point": pos, "before": before, "after": cur["store"],
            "delta": d3(before, cur["store"]),
            "nodePositionChanged": before != cur["store"] and
            before is not None and
            (before["x"] != cur["store"]["x"]
             or before["y"] != cur["store"]["y"])}


def main():
    res = {"batch": 761, "probe": "b",
           "constants": {"desktopViewport": DESKTOP, "compactViewport": COMPACT},
           "rounds": []}
    with sync_playwright() as p:
        br = p.chromium.launch()
        for _ in range(2):
            R = {}
            # ---------- ① 两档 A/B ----------
            for label, w, h, const in (("desktop", 1440, 1000, DESKTOP),
                                       ("compact", 700, 900, COMPACT),
                                       ("midband", 800, 900, DESKTOP)):
                pg = load_at(br, w, h)
                v = pg.evaluate(VP)
                R.setdefault("viewports", []).append({
                    "label": label, "requested": {"w": w, "h": h},
                    "measured": {"innerWidth": v["innerWidth"],
                                 "innerHeight": v["innerHeight"],
                                 "mq768": v["mq768"]},
                    "store": v["store"], "dom": v["dom"],
                    "indicator": v["zoomLevel"],
                    "triggerText": v["triggerText"],
                    "triggerVisible": v["triggerVisible"],
                    "matchesConstant": vp_matches(v["store"], const),
                    "expectedConstant": const,
                    "ownerLog": pg.evaluate(OWNER_LOG)})
                pg.close()

            # ---------- ② 干净滚轮（桌面档）----------
            pg = load_at(br, 1440, 1000)
            R["wheelPane"] = clean_wheel(pg, "pane")
            R["wheelNode"] = wheel_over_node(pg)
            R["ownerLogAfterWheel"] = pg.evaluate(OWNER_LOG)

            # ---------- ③ 窗口改宽后的重投影 ----------
            before = pg.evaluate(VP)
            pg.set_viewport_size({"width": 700, "height": 900})
            pg.wait_for_timeout(1200)
            after = pg.evaluate(VP)
            R["reproject"] = {"before": before, "after": after,
                              "delta": d3(before["store"], after["store"]),
                              "afterMatchesCompact":
                                  vp_matches(after["store"], COMPACT),
                              "ownerLog": pg.evaluate(OWNER_LOG)}
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
    for v in r1["viewports"]:
        tv = v["triggerVisible"] or {}
        print("%-9s 请求%-5d 实测%-5d mq768=%-5s store=%s 命中常量=%s | 缩放按钮 w=%s disp=%s 父disp=%s"
              % (v["label"], v["requested"]["w"], v["measured"]["innerWidth"],
                 v["measured"]["mq768"],
                 json.dumps(v["store"], ensure_ascii=False),
                 v["matchesConstant"], tv.get("w"), tv.get("display"),
                 tv.get("parentDisplay")))
        print("            ownerLog=%s" % json.dumps(v["ownerLog"], ensure_ascii=False)[:200])
    w = r1["wheelPane"]
    if "FAILED" in w:
        print("滚轮:", w)
    else:
        print("滚轮(固定等待) dy 序列 =", w["dyValues"])
        print("  全程 Δzoom 恒 0 =", w["allDzZero"], "| 有平移 =", w["anyDyMoved"],
              "| 有横移 =", w["anyDxMoved"])
    n = r1["wheelNode"]
    print("节点上滚轮:", json.dumps(n, ensure_ascii=False)[:260])
    print("滚轮后 ownerLog 条数 =",
          (r1["ownerLogAfterWheel"] or {}).get("length"))
    rp = r1["reproject"]
    print("改宽 1440→700: Δ=%s | 变成紧凑常量=%s"
          % (json.dumps(rp["delta"], ensure_ascii=False), rp["afterMatchesCompact"]))
    print("  ownerLog=", json.dumps(rp["ownerLog"], ensure_ascii=False)[:300])


if __name__ == "__main__":
    main()
