#!/usr/bin/env python3
"""batch 763 探针 a：导演台断点边界 + Esc 优先级阶梯

762 结清了焦点围栏，留了两块没碰的：

**① Batch 622 那个 1px 缝的修复到底成没成立。**
代码注释（`DirectorDesk.tsx:380-390`）记着一件很具体的事：
Tailwind v4 把 `max-[899px]` 编成 `@media (width < 899px)`（≤898 走窄屏），
JS 原来写 `matchMedia("(max-width: 899px)")`（≤899），**差一个像素** ⟹
vw=899 那一档 JS 判移动端、CSS 判桌面，场景树与属性列被**可见地**渲染出来
却又被 `inert` 整棵加上 ⟹ 22 枚控件**可见但点不动**。
Batch 622 把阈值改成 `matchMedia("(max-width: 898px)")` 对齐 CSS。

**注释说的是「改了」，没人验过「真的好了」。**本探针在 896–901 六档上逐档量：
布局落在哪一边、两列的 `inert`/`aria-hidden`/几何、以及**点下去到底有没有反应**
（行为判据，不只读属性）。

**② Esc 是十条优先级（`DirectorDesk.tsx:482` 与 `:549-569`）**，
排错一档就会被上一档吞掉。逐档走：
  导出面板开着 → Esc 只关面板、导演台仍在 → 再按一次才关
  焦点在 input/textarea → Esc **不该**关（`:481 if (isEditable) return;`）

真实点击一律先 `elementFromPoint` 断言命中；每格前重开导演台。
"""
import json
import pathlib
import re
from playwright.sync_api import sync_playwright

BASE = "http://localhost:4317"
OUT = pathlib.Path(
    "/Users/yangjiefeng/Documents/wubuku/liblib-tv"
    "/docs/research/liblib-canvas-batch763-2026-10-01/raw/vb763a.json")

WIDTHS = [896, 897, 898, 899, 900, 901]

# 断点读数：两列的 inert / aria-hidden / 几何 + 能否点得动 + JS 侧的判定
BREAKPOINT = """()=>{const d=document.querySelector('[role="dialog"][aria-modal="true"]');
 if(!d) return {open:false};
 const tree=d.querySelector('aside[aria-label="场景对象"]');
 const insp=d.querySelector('aside[aria-label="属性"]');
 const desc=(el)=>{if(!el) return null; const r=el.getBoundingClientRect();
   const cs=getComputedStyle(el);
   return {inert:!!el.inert, ariaHidden:el.getAttribute('aria-hidden'),
     display:cs.display, visibility:cs.visibility,
     rect:{x:Math.round(r.x),y:Math.round(r.y),
           w:Math.round(r.width),h:Math.round(r.height)},
     visibleArea:Math.round(r.width)*Math.round(r.height),
     mobilePanelState:el.getAttribute('data-director-mobile-panel-state'),
     focusScope:el.getAttribute('data-director-focus-scope')};};
 // JS 侧的判定：898/899 两条 media 的实测结果
 const mq898=window.matchMedia('(max-width: 898px)').matches;
 const mq899=window.matchMedia('(max-width: 899px)').matches;
 const mq899css=window.matchMedia('(width < 899px)').matches;
 // 行为判据：树里第一个可见可聚焦控件，点下去到底有没有反应
 const cand=tree?[...tree.querySelectorAll('button,[tabindex]')].find(e=>{
   const r=e.getBoundingClientRect();
   return r.width>8&&r.height>8&&getComputedStyle(e).visibility!=='hidden';}):null;
 let hit=null, clickWorks=null;
 if(cand){const r=cand.getBoundingClientRect();
   const x=Math.round(r.x+r.width/2), y=Math.round(r.y+r.height/2);
   if(x>2&&y>2&&x<innerWidth-2&&y<innerHeight-2){
     const e=document.elementFromPoint(x,y);
     const inside=e&&e.closest?e.closest('aside[aria-label="场景对象"]'):null;
     hit={x:x,y:y,tag:e?e.tagName:null,insideTree:!!inside,
          // 命中点是否落在树内 —— 树若 inert，浏览器会让点击穿透到别处
          topTagInside: inside ? !!e.closest('aside[aria-label="场景对象"]')
                               : false};
   }}
 return {open:true, innerWidth:innerWidth,
   mq898:mq898, mq899:mq899, mqWidthLt899:mq899css,
   jsSaysMobile:mq898, cssSaysMobile:mq899css,
   tree:desc(tree), inspector:desc(insp),
   treeFirstControl:hit};}"""

DESK = """()=>{const d=document.querySelector('[role="dialog"][aria-modal="true"]');
 if(!d) return {open:false};
 return {open:true, innerWidth:innerWidth,
   focusState:d.getAttribute('data-director-focus-state'),
   exportTrigger:(()=>{const b=d.querySelector('[data-director-export-trigger]');
     return b?{present:true, ariaExpanded:b.getAttribute('aria-expanded'),
               disabled:b.disabled,
               text:(b.textContent||'').trim()}:{present:false};})(),
   exportPanel:!!d.querySelector('[data-liblib-overlay="export"]')
     || !!d.querySelector('[data-director-export-submit]'),
   activeGesture:d.getAttribute('data-director-active-gesture')||'',
   lastCommand:d.getAttribute('data-director-last-command')||'',
   historyPast:d.getAttribute('data-director-history-past'),
   historyFuture:d.getAttribute('data-director-history-future')};}"""

ACTIVE = """()=>{const d=document.querySelector('[role="dialog"][aria-modal="true"]');
 const a=document.activeElement;
 return {open:!!d, inDialog:d?(d===a||d.contains(a)):false,
   tag:a?a.tagName:null, type:a?a.getAttribute('type'):null,
   ariaLabel:a?a.getAttribute('aria-label'):null,
   isContentEditable:a?!!a.isContentEditable:false};}"""

HIT = """(a)=>{const x=a[0],y=a[1],sel=a[2];const e=document.elementFromPoint(x,y);
 if(!e) return {tag:null,ok:false};
 const t=e.closest(sel);
 return {tag:e.tagName, ok:!!t,
   ariaLabel:t?t.getAttribute('aria-label'):null};}"""


def open_director(pg):
    el = pg.query_selector("[data-open-director]")
    if not el:
        return {"FAILED": "画布上找不到「打开导演台」"}
    pg.evaluate("()=>{const b=document.querySelector('[data-open-director]');"
                "if(b) b.scrollIntoView({block:'center'});}")
    pg.wait_for_timeout(400)
    el = pg.query_selector("[data-open-director]")
    box = el.bounding_box()
    cx, cy = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
    hit = pg.evaluate(HIT, [cx, cy, "[data-open-director]"])
    if not hit.get("ok"):
        raise SystemExit("FATAL「打开导演台」坐标没命中 —— 当场停")
    pg.mouse.click(cx, cy)
    try:
        pg.wait_for_selector('[role="dialog"][aria-modal="true"]', timeout=25000)
    except Exception:
        return {"FAILED": "点了但 dialog 没出现"}
    pg.wait_for_timeout(2400)
    return {"at": [int(cx), int(cy)]}


def run_round(pg, R):
    # ---------- ① 断点六档（★ 必须先打开导演台，否则量的是空页面）----------
    r = open_director(pg)
    if "FAILED" in r:
        R["FAILED"] = r["FAILED"]
        return
    bp = []
    for w in WIDTHS:
        pg.set_viewport_size({"width": w, "height": 1000})
        pg.wait_for_timeout(1000)
        bp.append(pg.evaluate(BREAKPOINT))
    R["breakpoint"] = bp
    pg.set_viewport_size({"width": 1440, "height": 1000})
    pg.wait_for_timeout(1000)
    pg.keyboard.press("Escape")
    pg.wait_for_timeout(1200)

    # ---------- ② Esc 阶梯 ----------
    ladder = []
    # 档 0：基准（无面板）—— 762 已验，这里复核一遍作为阶梯的起点
    r = open_director(pg)
    if "FAILED" in r:
        R["FAILED"] = r["FAILED"]
        return
    d0 = pg.evaluate(DESK)
    pg.keyboard.press("Escape")
    pg.wait_for_timeout(1100)
    d0b = pg.evaluate(DESK)
    ladder.append({"step": "baseline-no-panel", "before": d0,
                   "afterEsc": d0b, "closed": d0b["open"] is False,
                   "focusAfter": pg.evaluate(ACTIVE)})

    # 档 1：打开导出面板
    r = open_director(pg)
    if "FAILED" not in r:
        b = pg.query_selector("[data-director-export-trigger]")
        hit = None
        if b:
            box = b.bounding_box()
            cx, cy = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
            hit = pg.evaluate(HIT, [cx, cy, "[data-director-export-trigger]"])
            if not hit.get("ok"):
                raise SystemExit("FATAL 导出按钮坐标没命中 —— 当场停")
            pg.mouse.click(cx, cy)
            pg.wait_for_timeout(1200)
        s1a = pg.evaluate(DESK)
        pg.keyboard.press("Escape")
        pg.wait_for_timeout(1100)
        s1b = pg.evaluate(DESK)
        ladder.append({"step": "export-panel-open", "clickHit": hit,
                       "before": s1a, "afterEsc": s1b,
                       "closedWorkspace": s1b["open"] is False,
                       "exportClosed":
                           (s1a["exportTrigger"].get("ariaExpanded") == "true"
                            and s1b["exportTrigger"].get("ariaExpanded")
                            == "false")})
        # 档 2：再按一次 Esc，应该这次才关导演台
        pg.keyboard.press("Escape")
        pg.wait_for_timeout(1100)
        s2 = pg.evaluate(DESK)
        ladder.append({"step": "second-esc", "afterEsc": s2,
                       "closedWorkspace": s2["open"] is False,
                       "focusAfter": pg.evaluate(ACTIVE)})

    # 档 3：焦点落在可编辑控件里时 Esc 不该关
    r = open_director(pg)
    if "FAILED" not in r:
        info = pg.evaluate("""()=>{const d=document.querySelector(
            '[role="dialog"][aria-modal="true"]');
          const f=[...d.querySelectorAll('input:not([type=file]),textarea')]
            .find(e=>{const r=e.getBoundingClientRect();
              return r.width>20&&r.height>10;});
          if(!f) return {found:false};
          const r=f.getBoundingClientRect();
          return {found:true, tag:f.tagName, type:f.getAttribute('type'),
                  x:Math.round(r.x+r.width/2), y:Math.round(r.y+r.height/2)};}""")
        R["editableProbe"] = info
        if info.get("found"):
            pg.mouse.click(info["x"], info["y"])
            pg.wait_for_timeout(400)
            before = pg.evaluate(ACTIVE)
            pg.keyboard.press("Escape")
            pg.wait_for_timeout(1100)
            after = pg.evaluate(DESK)
            ladder.append({"step": "esc-in-editable", "info": info,
                           "activeBefore": before, "afterEsc": after,
                           "closedWorkspace": after["open"] is False})
            # 收尾：焦点离开可编辑控件后再按 Esc
            pg.mouse.click(700, 500)
            pg.wait_for_timeout(300)
            pg.keyboard.press("Escape")
            pg.wait_for_timeout(1100)
            s4 = pg.evaluate(DESK)
            ladder.append({"step": "esc-after-leaving-editable", "afterEsc": s4,
                           "closedWorkspace": s4["open"] is False,
                           "focusAfter": pg.evaluate(ACTIVE)})
        else:
            pg.keyboard.press("Escape")
            pg.wait_for_timeout(1000)

    R["escLadder"] = ladder


def main():
    res = {"batch": 763, "probe": "a", "widths": WIDTHS, "rounds": []}
    with sync_playwright() as p:
        br = p.chromium.launch()
        pg = br.new_page(viewport={"width": 1440, "height": 1000})
        for _ in range(2):
            pg.goto(BASE, wait_until="networkidle")
            pg.wait_for_selector(".react-flow__node", timeout=25000)
            pg.wait_for_timeout(1200)
            pg.keyboard.press("Meta+0")
            pg.wait_for_timeout(900)
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
    if r1.get("FAILED"):
        print("FAILED:", r1["FAILED"])
    print("--- 断点六档 ---")
    for b in r1.get("breakpoint", []):
        t, i = b.get("tree") or {}, b.get("inspector") or {}
        print("vw=%-4s JS移动=%-5s CSS移动=%-5s | 树 inert=%-5s aria-hidden=%-6s "
              "display=%-6s w=%-4s | 属性 inert=%-5s display=%-6s w=%s"
              % (b.get("innerWidth"), b.get("jsSaysMobile"),
                 b.get("cssSaysMobile"), t.get("inert"), t.get("ariaHidden"),
                 t.get("display"), (t.get("rect") or {}).get("w"),
                 i.get("inert"), i.get("display"), (i.get("rect") or {}).get("w")))
    print("--- Esc 阶梯 ---")
    for s in r1.get("escLadder", []):
        print("  %-26s 导演台关掉=%-5s %s"
              % (s["step"], s.get("closedWorkspace"),
                 json.dumps({k: v for k, v in s.items()
                             if k in ("closed", "exportClosed",
                                      "focusAfter")}, ensure_ascii=False)[:170]))
    ep = r1.get("editableProbe")
    if ep:
        print("可编辑控件:", json.dumps(ep, ensure_ascii=False))


if __name__ == "__main__":
    main()
