#!/usr/bin/env python3
"""batch 761 探针 a：画布「缩放」这条线的首轮普查

静态侦察给了四条可判的合同：

  ① `page.tsx:1547/1549` **panOnScroll 与 zoomOnScroll 同时开**，而 `:1551`
     `panActivationKeyCode={null}` ⟹ 连「按 Space 临时关掉平移」这条退路都没有。
     两个开关抢同一个滚轮事件 ⟹ 到底谁赢，必须实测。
  ② `uiStore.ts:223` zoomLevel 初值**硬编码 54**，而 canvas-2 的真实初始 zoom
     是 `desktopViewport.zoom = 0.526`（52.6%）。`setZoomLevel` 只在
     onViewportChange 里被调用 ⟹ 首屏那个百分比要么短暂错、要么一直错。
     **所以必须在任何交互之前读。**
  ③ `BottomToolbar.tsx:142-168` 的缩放菜单给了明确合同：in=+0.1 / out=-0.1 /
     fit=fitView / 50 / 100 / 800(=maxZoom)，且菜单按钮与快捷键 `⌘+`/`⌘-`/`⌘0`
     **是同两个回调**。
  ④ `NodeResizer` 在 LibTV 侧**根本不存在**（只有 FrameOS 的），`page.tsx` 也没传
     `nodesResizable` ⟹ 节点能不能改尺寸，只能实测拖边角看 DOM 与 store。

⚠ 本版修掉上一轮探针的四处问题（记为 R39–R42，见 README）：
  - C0 原本在 `Meta+0` **之后**读 ⟹ 首屏读数根本没被测到（本版提到最前）
  - 滚轮只记布尔 ⟹ 「向上滚完全没反应、向下滚才平移」这个不对称无从解释
    （本版拆成 4 步，逐步记 Δx/Δy/Δzoom）
  - C10 resize 之前**没复位视口** ⟹ 上一格 clamp 把 zoom 停在 8，节点全在视口外，
    `NODE()` 返回 null，整格记成 FAILED（本版每格前 fit）
  - clamp 两轮不一致 ⟹ 加 settle 轮询，等 zoom 真的停稳再读

每个格子都记 zoom 三处来源：uiStore.zoomLevel / store canvas.viewport /
DOM `.react-flow__viewport` 的 transform。**当轮现取 zoom 做换算**，不许抄上一格。
"""
import json
import pathlib
import re
from playwright.sync_api import sync_playwright

BASE = "http://localhost:4317"
OUT = pathlib.Path(
    "/Users/yangjiefeng/Documents/wubuku/liblib-tv"
    "/docs/research/liblib-canvas-batch761-2026-10-01/raw/vb761a.json")
W, H = 1440, 1000

VP = """()=>{const u=window.__libtv_ui_store.getState();
 const s=window.__libtv_store.getState();
 const c=s.getActiveCanvas();
 const vp=(c&&c.viewport)||null;
 const dom=document.querySelector('.react-flow__viewport');
 let domZoom=null, domXY=null;
 if(dom){const cs=getComputedStyle(dom).transform;
   if(cs&&cs!=='none'){
     const m=cs.match(/matrix\\(([^,]+),[^,]+,[^,]+,([^,]+),([^,]+),([^\\)]+)\\)/);
     if(m){domXY=[Math.round(+m[3]),Math.round(+m[4])];
            domZoom=Math.round(+m[1]*1000)/1000;}}}
 const trig=document.querySelector('[data-viewport-menu-trigger="zoom"]');
 return {zoomLevel:u.zoomLevel,
   store:vp?{x:Math.round(vp.x*100)/100,y:Math.round(vp.y*100)/100,
             zoom:Math.round(vp.zoom*1000)/1000}:null,
   dom:domZoom===null?null:{zoom:domZoom,x:domXY[0],y:domXY[1]},
   triggerText:trig?trig.textContent.trim():null,
   activeCanvasId:s.activeCanvasId};}"""

DERIVED = """()=>{const u=window.__libtv_ui_store.getState();
 const s=window.__libtv_store.getState(); const c=s.getActiveCanvas();
 const vp=(c&&c.viewport)||null;
 const trig=document.querySelector('[data-viewport-menu-trigger="zoom"]');
 const real=vp?Math.round(vp.zoom*100):null;
 const txt=trig?trig.textContent.trim():null;
 return {realPercent:real, indicator:u.zoomLevel, triggerText:txt,
   indicatorMatchesReal:u.zoomLevel===real,
   triggerMatchesIndicator:txt===String(u.zoomLevel)+'%',
   triggerMatchesReal:txt===String(real)+'%'};}"""

PANE_PT = """()=>{for(let y=140;y<innerHeight-220;y+=12)
 for(let x=180;x<innerWidth-260;x+=12){
  const e=document.elementFromPoint(x,y); if(!e||!e.closest)continue;
  if(!e.closest('.react-flow__pane'))continue;
  if(e.closest('.react-flow__node')||e.closest('.react-flow__edge'))continue;
  if(e.closest('button,input,select,textarea,[role="button"]'))continue;
  return {x:x,y:y};}
 return null;}"""

NODE = """()=>{const els=[...document.querySelectorAll('.react-flow__node')];
 for(const el of els){const id=el.getAttribute('data-id');
  if(!id) continue;
  if(id.startsWith('g-')) continue;
  const r=el.getBoundingClientRect();
  if(r.width<40||r.height<40) continue;
  if(r.x<10||r.y<10||r.right>innerWidth-10||r.bottom>innerHeight-150) continue;
  const s=window.__libtv_store.getState(); const c=s.getActiveCanvas();
  const n=c.nodes.find(x=>x.id===id);
  return {id:id, rect:{x:Math.round(r.x),y:Math.round(r.y),
                       w:Math.round(r.width),h:Math.round(r.height)},
          storeW:n?n.width:null, storeH:n?n.height:null,
          styleW:n&&n.style?n.style.width:null,
          styleH:n&&n.style?n.style.height:null};}
 return null;}"""

NODE_RECT = """(id)=>{const el=document.querySelector('.react-flow__node[data-id="'+id+'"]');
 if(!el) return null; const r=el.getBoundingClientRect();
 const s=window.__libtv_store.getState(); const c=s.getActiveCanvas();
 const n=c.nodes.find(x=>x.id===id);
 return {w:Math.round(r.width),h:Math.round(r.height),
   x:Math.round(r.x),y:Math.round(r.y),
   storeW:n?n.width:null,storeH:n?n.height:null,
   styleW:n&&n.style?n.style.width:null,styleH:n&&n.style?n.style.height:null,
   measured:n&&n.measured?n.measured:null};}"""

RESIZE_CTL = "()=>document.querySelectorAll('.react-flow__resize-control').length"
RESIZE_HANDLE = "()=>[...document.querySelectorAll('[class*=resize]')].length"

HIT = """(a)=>{const x=a[0],y=a[1];const e=document.elementFromPoint(x,y);
 if(!e) return {tag:null,cls:null,node:null};
 const n=e.closest?e.closest('.react-flow__node'):null;
 return {tag:e.tagName, cls:(e.getAttribute('class')||'').slice(0,90),
         node:n?n.getAttribute('data-id'):null};}"""


def zoom_now(pg):
    return pg.evaluate(
        "()=>{const c=window.__libtv_store.getState().getActiveCanvas();"
        "return c&&c.viewport?c.viewport.zoom:null;}")


def settle(pg, tries=14, ms=140):
    """等 zoom 真的停稳：连续两次读到同一个值才算稳（动画 duration 160–260ms）。"""
    prev = object()
    for _ in range(tries):
        z = zoom_now(pg)
        if z == prev:
            return z
        prev = z
        pg.wait_for_timeout(ms)
    return prev


def fit(pg):
    pg.keyboard.press("Meta+0")
    pg.wait_for_timeout(450)
    return settle(pg)


def d3(a, b):
    """两个 store 快照的三元差；缺任一侧返回 None（不许默认 0 蒙过去）。"""
    if not a or not b:
        return None
    return {"dx": round(b["x"] - a["x"], 2), "dy": round(b["y"] - a["y"], 2),
            "dz": round(b["zoom"] - a["zoom"], 4)}


def click(pg, sel, why):
    el = pg.query_selector(sel)
    if not el:
        raise SystemExit("FATAL %s: 找不到 %s —— 当场停" % (why, sel))
    box = el.bounding_box()
    if not box:
        raise SystemExit("FATAL %s: %s 没有 bounding box" % (why, sel))
    cx, cy = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
    h = pg.evaluate(HIT, [cx, cy])
    pg.mouse.click(cx, cy)
    pg.wait_for_timeout(300)
    settle(pg)
    return {"selector": sel, "at": [int(cx), int(cy)], "hit": h}


def open_zoom_menu(pg):
    return click(pg, '[data-viewport-menu-trigger="zoom"]', "打开缩放菜单")


def close_menu(pg):
    pg.mouse.click(720, 300)
    pg.wait_for_timeout(350)


def run_round(pg, R):
    # ---------- C0 首屏：任何交互之前 ----------
    R["C0_initial"] = {"vp": pg.evaluate(VP),
                       "derived": pg.evaluate(DERIVED),
                       "resizeControls": pg.evaluate(RESIZE_CTL),
                       "resizeLikeElements": pg.evaluate(RESIZE_HANDLE)}

    fit(pg)
    R["afterFit"] = {"vp": pg.evaluate(VP), "derived": pg.evaluate(DERIVED)}

    # ---------- 滚轮：拆成 4 步，逐步记差值 ----------
    pt = pg.evaluate(PANE_PT)
    R["panePoint"] = pt
    if not pt:
        R["wheel"] = {"FAILED": "找不到 pane 空白点"}
    else:
        pg.mouse.move(pt["x"], pt["y"])
        steps = []
        prev = pg.evaluate(VP)
        steps.append({"step": "start", "store": prev["store"]})
        for name, dy in (("up1", -120), ("up2", -120), ("down1", 120),
                         ("down2", 120)):
            pg.mouse.wheel(0, dy)
            pg.wait_for_timeout(320)
            settle(pg)
            cur = pg.evaluate(VP)
            steps.append({"step": name, "deltaY": dy, "store": cur["store"],
                          "delta": d3(prev["store"], cur["store"]),
                          "indicator": cur["zoomLevel"]})
            prev = cur
        R["wheel"] = {"steps": steps,
                      "zoomEverChanged": any(
                          (s.get("delta") or {}).get("dz") for s in steps),
                      "xyEverChanged": any(
                          (s.get("delta") or {}).get("dx")
                          or (s.get("delta") or {}).get("dy") for s in steps)}
        R["wheelDerived"] = pg.evaluate(DERIVED)

    # ---------- 菜单读数 + 六个动作 ----------
    open_zoom_menu(pg)
    R["C1_menu"] = pg.evaluate(
        "()=>{const c=document.querySelector('[data-zoom-current]');"
        "return {current:c?c.textContent.trim():null,"
        "actions:[...document.querySelectorAll('[data-zoom-action]')]"
        ".map(b=>b.getAttribute('data-zoom-action'))};}")
    R["C1_derived"] = pg.evaluate(DERIVED)

    acts = []
    for key in ("100", "in", "out", "fit", "800", "50"):
        b = pg.evaluate(VP)["store"]
        h = click(pg, '[data-zoom-action="%s"]' % key, "菜单动作 " + key)
        acts.append({"key": key, "before": b, "hit": h,
                     "after": pg.evaluate(VP)["store"],
                     "derived": pg.evaluate(DERIVED)})
    R["actions"] = acts
    close_menu(pg)

    # ---------- 键盘三键 vs 菜单按钮是否等价 ----------
    kb = []
    for k, name in (("Meta+Equal", "Meta+"), ("Meta+Minus", "Meta-"),
                    ("Meta+0", "Meta0")):
        b = pg.evaluate(VP)["store"]
        pg.keyboard.press(k)
        pg.wait_for_timeout(300)
        settle(pg)
        kb.append({"key": name, "before": b,
                   "after": pg.evaluate(VP)["store"],
                   "delta": d3(b, pg.evaluate(VP)["store"]),
                   "derived": pg.evaluate(DERIVED)})
    R["keyboard"] = kb

    # ---------- clamp ----------
    clamp = {}
    for key, name, times in (("out", "min", 26), ("in", "max", 90)):
        fit(pg)
        open_zoom_menu(pg)
        start = pg.evaluate(VP)["store"]
        for _ in range(times):
            pg.click('[data-zoom-action="%s"]' % key)
            pg.wait_for_timeout(45)
        pg.wait_for_timeout(500)
        settle(pg)
        clamp[name] = {"times": times, "start": start,
                       "store": pg.evaluate(VP)["store"],
                       "derived": pg.evaluate(DERIVED)}
        close_menu(pg)
    R["clamp"] = clamp

    # ---------- 节点能否 resize（★ 每格前必须 fit，上一格把 zoom 停在 8）----------
    fit(pg)
    nd = pg.evaluate(NODE)
    R["node"] = nd
    if not nd:
        R["resize"] = {"FAILED": "fit 之后仍找不到视口内的普通节点"}
    else:
        cells = []
        for name, fx, fy, dx, dy in (
                ("rightEdge", 1.0, 0.5, 80, 0),
                ("bottomEdge", 0.5, 1.0, 0, 60),
                ("corner", 1.0, 1.0, 80, 60)):
            fit(pg)                                  # ← 每格前复位，绝不带上一格状态
            cur = pg.evaluate(NODE)
            if not cur:
                cells.append({"where": name, "FAILED": "fit 后节点不可见"})
                continue
            r = cur["rect"]
            sx, sy = int(r["x"] + r["w"] * fx) - 2, int(r["y"] + r["h"] * fy) - 2
            b0 = pg.evaluate(NODE_RECT, cur["id"])
            hit = pg.evaluate(HIT, [sx, sy])
            pg.mouse.move(sx, sy)
            pg.mouse.down()
            for i in range(1, 7):
                pg.mouse.move(sx + dx * i // 6, sy + dy * i // 6)
                pg.wait_for_timeout(25)
            pg.mouse.up()
            pg.wait_for_timeout(450)
            settle(pg)
            b1 = pg.evaluate(NODE_RECT, cur["id"])
            cells.append({
                "where": name, "nodeId": cur["id"], "start": [sx, sy],
                "hit": hit, "hitOwnNode": hit.get("node") == cur["id"],
                "before": b0, "after": b1,
                "domWidthChanged": b0["w"] != b1["w"],
                "domHeightChanged": b0["h"] != b1["h"],
                "storeWidthChanged": b0["storeW"] != b1["storeW"],
                "storeHeightChanged": b0["storeH"] != b1["storeH"],
                "positionChanged": (b0["x"], b0["y"]) != (b1["x"], b1["y"]),
            })
            pg.keyboard.press("Meta+z")
            pg.wait_for_timeout(350)
        R["resize"] = {"cells": cells,
                       "resizeControls": pg.evaluate(RESIZE_CTL),
                       "resizeLikeElements": pg.evaluate(RESIZE_HANDLE)}


def main():
    res = {"batch": 761, "probe": "a", "rounds": []}
    with sync_playwright() as p:
        br = p.chromium.launch()
        pg = br.new_page(viewport={"width": W, "height": H})
        for _ in (1, 2):
            pg.goto(BASE, wait_until="networkidle")
            pg.wait_for_selector(".react-flow__node", timeout=20000)
            pg.wait_for_timeout(1100)          # 只等渲染，**不做任何交互**
            R = {}
            run_round(pg, R)
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
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")

    print("consistent =", res["consistent"], "| diff =", sorted(diff))
    c0 = r1["C0_initial"]
    print("C0 首屏: 指示器=%s 真实=%s 一致=%s | trigger=%s | zoom=%s"
          % (c0["derived"]["indicator"], c0["derived"]["realPercent"],
             c0["derived"]["indicatorMatchesReal"],
             c0["derived"]["triggerText"], c0["vp"]["store"]["zoom"]))
    print("C0 resizeControls=%s resizeLike=%s"
          % (c0["resizeControls"], c0["resizeLikeElements"]))
    print("fitView 后: zoom=%s 指示器=%s"
          % (r1["afterFit"]["vp"]["store"]["zoom"],
             r1["afterFit"]["derived"]["indicator"]))
    for s in r1.get("wheel", {}).get("steps", []):
        dl = s.get("delta")
        print("  滚轮 %-6s Δ=%s" % (s["step"], json.dumps(dl, ensure_ascii=False)))
    print("  滚轮 zoom 变过=%s XY 变过=%s"
          % (r1["wheel"].get("zoomEverChanged"),
             r1["wheel"].get("xyEverChanged")))
    print("菜单:", json.dumps(r1.get("C1_menu"), ensure_ascii=False))
    for a in r1.get("actions", []):
        print("  菜单 %-4s %s → %s | 指示器 %s | 一致=%s"
              % (a["key"], (a["before"] or {}).get("zoom"),
                 (a["after"] or {}).get("zoom"), a["derived"]["indicator"],
                 a["derived"]["indicatorMatchesReal"]))
    for k in r1.get("keyboard", []):
        print("  键盘 %-6s Δ=%s" % (k["key"],
                                    json.dumps(k["delta"], ensure_ascii=False)))
    for n, c in (r1.get("clamp") or {}).items():
        print("  clamp %-3s 起点 %s ×%-3d → %s（指示器 %s）"
              % (n, (c["start"] or {}).get("zoom"), c["times"],
                 (c["store"] or {}).get("zoom"), c["derived"]["indicator"]))
    rs = r1.get("resize", {})
    print("resizeControls=%s resizeLike=%s"
          % (rs.get("resizeControls"), rs.get("resizeLikeElements")))
    for c in rs.get("cells", []):
        if "FAILED" in c:
            print("  ✗", c["where"], c["FAILED"])
        else:
            print("  %-11s 命中自己=%-5s DOM宽变=%-5s DOM高变=%-5s store宽变=%-5s 位移=%s"
                  % (c["where"], c["hitOwnNode"], c["domWidthChanged"],
                     c["domHeightChanged"], c["storeWidthChanged"],
                     c["positionChanged"]))


if __name__ == "__main__":
    main()
