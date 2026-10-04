#!/usr/bin/env python3
"""batch 762 探针 a：导演台的焦点围栏与键盘可达性（首轮普查）

748 挂起了一条「导演台键盘/焦点围栏未测」。静态侦察发现导演台是一整块
`role="dialog" aria-modal="true"`（`DirectorDesk.tsx:901-902`），外面挂着：

  :896  data-director-focus-scope="workspace"
  :897  data-director-focus-return={returnDisposition}
  :898  data-director-focus-state={activeMobileFocusScope ? mobile-X : workspace}
  :1182 inert={treeMobileInactive || viewportPanelsCollapsed}     ← 场景树面板
  :1179 aria-hidden={viewportPanelsCollapsed || treeMobileInactive ? "true" : undefined}

入口也是现成的：种子画布里有 1 个 `script-execution` 节点，
它的 `data-open-director` 按钮 `onClick` 直接调 `openDirectorDesk(id, activeCanvasId)`。

`aria-modal="true"` 的承诺是「模态对话框外的世界对辅助技术不可达」，
本探针逐条去核这个承诺：

  ① 打开导演台 → dialog 出现、`focus-scope/state/return` 三枚读数
  ② 打开瞬间 `document.activeElement` 落在谁身上？**有没有真的进 dialog**
  ③ 连按 N 次 Tab —— 焦点**会不会跑到 dialog 外面去**（围栏的核心断言）
  ④ Shift+Tab 反向同样测一遍
  ⑤ Esc 干什么：关整个导演台 / 只关移动端面板 / 什么都不干
  ⑥ `inert` 与 `aria-hidden` 是否同步；inert 的面板里到底还有几个可 Tab 到的元素
  ⑦ 关掉导演台后焦点回到哪（`data-director-focus-return` 是否真的做了返回）

每格之前都回到画布起点，绝不把上一格的状态带进下一格。
"""
import json
import pathlib
from playwright.sync_api import sync_playwright

BASE = "http://localhost:4317"
OUT = pathlib.Path(
    "/Users/yangjiefeng/Documents/wubuku/liblib-tv"
    "/docs/research/liblib-canvas-batch762-2026-10-01/raw/vb762a.json")

# 导演台那三枚焦点读数 + dialog 本体
DESK = """()=>{const d=document.querySelector('[role="dialog"][aria-modal="true"]');
 if(!d) return {open:false};
 const cs=getComputedStyle(d);
 return {open:true,
   focusScope:d.getAttribute('data-director-focus-scope'),
   focusState:d.getAttribute('data-director-focus-state'),
   focusReturn:d.getAttribute('data-director-focus-return'),
   ariaModal:d.getAttribute('aria-modal'),
   ariaLabel:d.getAttribute('aria-label'),
   rect:{x:Math.round(d.getBoundingClientRect().x),
         y:Math.round(d.getBoundingClientRect().y),
         w:Math.round(d.getBoundingClientRect().width),
         h:Math.round(d.getBoundingClientRect().height)},
   zIndex:cs.zIndex, position:cs.position,
   panelsCollapsed:d.getAttribute('data-director-panels-collapsed'),
   isTopmostAtCenter:(()=>{const r=d.getBoundingClientRect();
     const e=document.elementFromPoint(r.x+r.width/2,r.y+r.height/2);
     return e?(d.contains(e)||d===e):false;})()};}"""

# 当前焦点是谁 + 是否在 dialog 内 + 能不能 Tab 到
ACTIVE = """()=>{const d=document.querySelector('[role="dialog"][aria-modal="true"]');
 const a=document.activeElement;
 if(!a) return {none:true};
 const desc=(e)=>({tag:e.tagName,
   id:e.id||null,
   ariaLabel:e.getAttribute('aria-label'),
   dataDirectorNode:e.getAttribute('data-director-node-id'),
   dataOpenDirector:e.getAttribute('data-open-director'),
   dataRailEntry:e.getAttribute('data-director-rail-entry'),
   role:e.getAttribute('role'),
   cls:(e.getAttribute('class')||'').slice(0,70),
   text:(e.textContent||'').trim().slice(0,24)});
 return {body:document.body===a,
   inDialog:d?(d===a||d.contains(a)):false,
   el:desc(a),
   dialogCount:document.querySelectorAll('[role="dialog"][aria-modal="true"]').length,
   inertDialogs:[...document.querySelectorAll('[aria-modal="true"]')]
     .filter(x=>x.inert).length};}"""

# dialog 内的可聚焦元素有多少（inert 的子树应算 0 个）
FOCUSABLE = """()=>{const d=document.querySelector('[role="dialog"][aria-modal="true"]');
 if(!d) return {open:false};
 const sel='a[href],button,input,select,textarea,[tabindex]';
 const all=[...d.querySelectorAll(sel)].filter(e=>{
   if(e.disabled) return false;
   const t=e.getAttribute('tabindex');
   if(t!==null && Number(t)<0) return false;
   return true;});
 const cs=getComputedStyle;
 const reach=all.filter(e=>cs(e).display!=='none' && cs(e).visibility!=='hidden');
 return {open:true, focusableTotal:all.length, reachable:reach.length,
   zeroTabIndex:all.filter(e=>e.getAttribute('tabindex')==='0').length,
   positiveTabIndex:all.filter(e=>{const t=e.getAttribute('tabindex');
     return t!==null && Number(t)>0;}).length,
   focusScopeCount:document.querySelectorAll('[data-director-focus-scope]').length};}"""

# 面板的 inert / aria-hidden 一致性
PANELS = """()=>{const d=document.querySelector('[role="dialog"][aria-modal="true"]');
 if(!d) return {open:false};
 const out=[];
 for(const el of d.querySelectorAll('aside,section,[data-director-focus-scope],'
     +'[aria-label="场景对象"],[aria-label="属性"]')){
  const cs=getComputedStyle(el);
  out.push({tag:el.tagName, ariaLabel:el.getAttribute('aria-label'),
    scope:el.getAttribute('data-director-focus-scope'),
    inert:!!el.inert, ariaHidden:el.getAttribute('aria-hidden'),
    display:cs.display, visibility:cs.visibility,
    rect:{w:Math.round(el.getBoundingClientRect().width),
          h:Math.round(el.getBoundingClientRect().height)}});}
 return {open:true, panels:out};}"""

CANVAS_UP = "()=>!!document.querySelector('[data-open-director]')"
HIT = """(a)=>{const x=a[0],y=a[1];const e=document.elementFromPoint(x,y);
 if(!e) return {tag:null,cls:null,ok:false};
 const t=e.closest('[data-open-director]');
 return {tag:e.tagName, cls:(e.getAttribute('class')||'').slice(0,70),
   ok:!!t, text:(t?t.textContent:'').trim().slice(0,20)};}"""


def click_open_director(pg):
    el = pg.query_selector("[data-open-director]")
    if not el:
        return {"FAILED": "画布上找不到「打开导演台」按钮"}
    pg.evaluate("()=>{const b=document.querySelector('[data-open-director]');"
                "if(b) b.scrollIntoView({block:'center'});}")
    pg.wait_for_timeout(400)
    el = pg.query_selector("[data-open-director]")
    box = el.bounding_box()
    cx, cy = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
    hit = pg.evaluate(HIT, [cx, cy])
    if not hit.get("ok"):
        raise SystemExit("FATAL 「打开导演台」坐标 %s 没命中（实际 %s）—— 当场停"
                         % ([int(cx), int(cy)], hit))
    pg.mouse.click(cx, cy)
    return {"at": [int(cx), int(cy)], "hit": hit}


def tab_walk(pg, n, shift=False):
    """连按 n 次 Tab，逐步记焦点落点与是否仍在 dialog 内"""
    seq = []
    seq.append({"after": -1, **(pg.evaluate(ACTIVE) or {})})
    for i in range(n):
        pg.keyboard.press("Shift+Tab" if shift else "Tab")
        pg.wait_for_timeout(90)
        a = pg.evaluate(ACTIVE) or {}
        seq.append({"after": i, "inDialog": a.get("inDialog"),
                    "tag": (a.get("el") or {}).get("tag"),
                    "ariaLabel": (a.get("el") or {}).get("ariaLabel"),
                    "text": (a.get("el") or {}).get("text"),
                    "isBody": a.get("body")})
    escaped = [s for s in seq if s.get("inDialog") is False]
    return {"steps": len(seq), "escapedCount": len(escaped),
            "escapedAt": [s["after"] for s in escaped],
            "bodyHits": [s["after"] for s in seq if s.get("isBody")],
            "seq": seq}


def run_round(pg, R):
    R["canvasUp"] = pg.evaluate(CANVAS_UP)
    R["beforeOpen"] = pg.evaluate(ACTIVE)

    opened = click_open_director(pg)
    R["clickOpen"] = opened
    if "FAILED" in opened:
        R["FAILED"] = opened["FAILED"]
        return

    # 导演台是 dynamic(ssr:false) 懒加载，给足时间
    try:
        pg.wait_for_selector('[role="dialog"][aria-modal="true"]', timeout=25000)
    except Exception:
        R["FAILED"] = "点了「打开导演台」但 25s 内没出现 aria-modal 对话框"
        R["deskAfterWait"] = pg.evaluate(DESK)
        return
    pg.wait_for_timeout(2500)        # 等面板与懒加载子组件落定

    R["D1_desk"] = pg.evaluate(DESK)
    R["D1_focusable"] = pg.evaluate(FOCUSABLE)
    R["D1_activeOnOpen"] = pg.evaluate(ACTIVE)
    R["D1_panels"] = pg.evaluate(PANELS)

    # ② 打开瞬间焦点有没有真的进 dialog（D1_activeOnOpen）
    # ③ Tab 遍历
    R["D2_tabForward"] = tab_walk(pg, 24)
    R["D3_activeAfterTab"] = pg.evaluate(ACTIVE)
    # ④ Shift+Tab 反向
    R["D4_tabBackward"] = tab_walk(pg, 12, shift=True)
    R["D5_activeAfterShiftTab"] = pg.evaluate(ACTIVE)

    # ⑤ Esc
    pg.keyboard.press("Escape")
    pg.wait_for_timeout(1200)
    R["D6_afterEsc"] = {"desk": pg.evaluate(DESK),
                        "active": pg.evaluate(ACTIVE),
                        "canvasUp": pg.evaluate(CANVAS_UP)}

    # ⑥ 若 Esc 关掉了整个导演台，重新打开再测 inert 面板与焦点返回
    if not (R["D6_afterEsc"]["desk"] or {}).get("open"):
        pg.wait_for_timeout(600)
        R["D7_focusAfterClose"] = pg.evaluate(ACTIVE)
        R["D7_focusReturnAttr"] = pg.evaluate(
            "()=>{const e=document.querySelector('[data-open-director]');"
            "return e?e.getAttribute('data-director-focus-return'):null;}")
        reopened = click_open_director(pg)
        R["D8_reopen"] = reopened
        try:
            pg.wait_for_selector('[role="dialog"][aria-modal="true"]',
                                 timeout=25000)
            pg.wait_for_timeout(2200)
            R["D8_desk"] = pg.evaluate(DESK)
            R["D8_panels"] = pg.evaluate(PANELS)
            R["D8_focusable"] = pg.evaluate(FOCUSABLE)
            # 折叠面板后 inert/aria-hidden 是否同步
            R["D8_collapse"] = pg.evaluate("""()=>{
              const t=document.querySelector('[data-director-panels-collapsed]');
              const btn=[...document.querySelectorAll('button')]
                .find(b=>/收起|折叠|展开/.test(b.textContent||''));
              return {collapsedAttr:t?t.getAttribute(
                          'data-director-panels-collapsed'):null,
                      collapseButtonText:btn?btn.textContent.trim():null};}""")
        except Exception as e:
            R["D8_FAILED"] = str(e)
        pg.keyboard.press("Escape")
        pg.wait_for_timeout(1000)


def main():
    res = {"batch": 762, "probe": "a", "rounds": []}
    with sync_playwright() as p:
        br = p.chromium.launch()
        pg = br.new_page(viewport={"width": 1440, "height": 1000})
        for _ in (1, 2):
            pg.goto(BASE, wait_until="networkidle")
            pg.wait_for_selector(".react-flow__node", timeout=25000)
            pg.wait_for_timeout(1200)
            pg.keyboard.press("Meta+0")     # fitView，把按钮带进视口
            pg.wait_for_timeout(900)
            R = {}
            run_round(pg, R)
            res["rounds"].append(R)
        br.close()

    def strip(o):
        if isinstance(o, str):
            import re
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
        print("FAIL:", r1["FAILED"])
    d = r1.get("D1_desk") or {}
    print("D1 dialog:", json.dumps({k: d.get(k) for k in
          ("open", "focusScope", "focusState", "focusReturn", "ariaModal",
           "zIndex", "position", "panelsCollapsed",
           "isTopmostAtCenter")}, ensure_ascii=False))
    print("D1 可聚焦:", json.dumps(r1.get("D1_focusable"), ensure_ascii=False))
    ao = (r1.get("D1_activeOnOpen") or {}).get("el") or {}
    print("D1 打开瞬间焦点:", json.dumps({k: ao.get(k) for k in
          ("tag", "ariaLabel", "text", "role")}, ensure_ascii=False),
          "| inDialog=", (r1.get("D1_activeOnOpen") or {}).get("inDialog"))
    for key in ("D2_tabForward", "D4_tabBackward"):
        w = r1.get(key) or {}
        print("%s: 按了 %s 次，逃出 dialog %s 次（步 %s），落在 body %s 次"
              % (key, w.get("steps"), w.get("escapedCount"),
                 w.get("escapedAt"), w.get("bodyHits")))
    e = r1.get("D6_afterEsc") or {}
    print("D6 Esc 之后 dialog 还开着:", (e.get("desk") or {}).get("open"),
          "| 焦点:", json.dumps((e.get("active") or {}).get("el"),
                                ensure_ascii=False)[:150])
    if "D7_focusAfterClose" in r1:
        print("D7 关掉后焦点:", json.dumps(r1["D7_focusAfterClose"],
                                           ensure_ascii=False)[:220])
        print("D7 focus-return 属性:", r1.get("D7_focusReturnAttr"))
    if r1.get("D8_collapse"):
        print("D8 折叠相关:", json.dumps(r1["D8_collapse"], ensure_ascii=False))
    for pn in (r1.get("D1_panels") or {}).get("panels", [])[:6]:
        print("   面板 %-8s label=%-10s inert=%-5s aria-hidden=%-6s w=%s h=%s"
              % (pn["tag"], pn["ariaLabel"], pn["inert"], pn["ariaHidden"],
                 pn["rect"]["w"], pn["rect"]["h"]))


if __name__ == "__main__":
    main()
