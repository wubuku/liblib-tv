#!/usr/bin/env python3
"""batch 763 探针 f：`useDirectorGestureBoundary` 吞掉 Esc 的完整后果

763e 已定位（两轮一致）：属性面板 9 个 `type=number` 输入框里按 Esc 关不掉抽屉，
`reachedWinBubble=false` ⟹ 事件没到 window 冒泡 ⟹ `DirectorDesk.tsx:475`
那个 Esc 阶梯**根本没跑**。注入同位置的 `type=number` 却能关 ⟹ 不是 type 本身。

源码根因 `useDirectorGestureBoundary.ts:92-98`：
    onKeyDown: (event) => { if (event.key === "Escape") {
        event.preventDefault(); event.stopPropagation(); cancel(); return; } ... }
经 `DirectorInspector.tsx:182` 的 `{...(isAxisDisabled(index) ? {} : gesture)}`
spread 到那 9 个框上。

本探针补齐「吞掉之后到底怎样」这四件事，逐格如实读：
  A 只聚焦那个框（不按任何键）→ `data-director-active-gesture` 是不是已经有了？
     （`:79 onFocus: begin` 意味着**光聚焦就开一个 gesture**）
     historyPast 有没有因为聚焦而多一条？
  B 按一次 Esc → 抽屉关不关？gesture 消没消？historyPast 有没有被 cancel 写脏？
  C 再按一次 Esc → 仍然关不掉？（结构性结论：焦点不出这个框，Esc 就一直无效）
  D Tab 走到别的控件再按 Esc → 抽屉能不能关（这才是逃生门）
  E 聚焦后按一个真编辑键（ArrowUp）→ 是否 begin 出 gesture、historyPast 是否 +1
"""
import json
import pathlib
from playwright.sync_api import sync_playwright

BASE = "http://localhost:4317"
OUT = pathlib.Path(
    "/Users/yangjiefeng/Documents/wubuku/liblib-tv"
    "/docs/research/liblib-canvas-batch763-2026-10-01/raw/vb763f.json")

DESK = """()=>{const d=document.querySelector('[role="dialog"][aria-modal="true"]');
 if(!d) return {open:false};
 const insp=d.querySelector('aside[aria-label="属性"]');
 const tree=d.querySelector('aside[aria-label="场景对象"]');
 const p=(el)=>{if(!el) return null; const r=el.getBoundingClientRect();
   return {state:el.getAttribute('data-director-mobile-panel-state'),
     focusScope:el.getAttribute('data-director-focus-scope'),
     inert:!!el.inert, x:Math.round(r.x)};};
 const a=document.activeElement;
 return {open:true, inspector:p(insp), tree:p(tree),
   historyPast:d.getAttribute('data-director-history-past'),
   historyFuture:d.getAttribute('data-director-history-future'),
   lastCommand:d.getAttribute('data-director-last-command')||'',
   activeGesture:d.getAttribute('data-director-active-gesture')||'',
   active:{tag:a?a.tagName:null, type:a?a.getAttribute('type'):null,
     aria:a?a.getAttribute('aria-label'):null,
     tf:a?a.getAttribute('data-director-transform-field'):null,
     ta:a?a.getAttribute('data-director-transform-axis'):null}};}"""

# 找出属性面板里带 data-director-transform-axis 的数字框（即 gesture 边界那批）
TARGETS = """()=>{const d=document.querySelector(
    '[role="dialog"][aria-modal="true"]');
 const p=d&&d.querySelector('aside[aria-label="属性"]');
 if(!p) return {err:'no panel'};
 const out=[];
 let i=0;
 for(const e of p.querySelectorAll(
     'a[href],button,input,select,textarea,[tabindex]')){
   if(e.disabled) continue; const t=e.getAttribute('tabindex');
   if(t!==null && Number(t)<0) continue;
   const s=getComputedStyle(e);
   if(s.display==='none'||s.visibility==='hidden') continue;
   const r=e.getBoundingClientRect();
   if(r.width<=0||r.height<=0) continue;
   out.push({i:i++, tag:e.tagName, type:e.getAttribute('type'),
     tf:e.getAttribute('data-director-transform-field'),
     ta:e.getAttribute('data-director-transform-axis'),
     aria:e.getAttribute('aria-label'),
     text:(e.textContent||'').trim().slice(0,10)});}
 return {count:out.length,
   gestureBoundaryIdx:out.filter(x=>x.tf&&x.ta).map(x=>x.i),
   items:out};}"""

FOCUS_N = """(a)=>{const d=document.querySelector(
    '[role="dialog"][aria-modal="true"]');
 const p=d.querySelector('aside[aria-label="属性"]');
 const els=[...p.querySelectorAll(
   'a[href],button,input,select,textarea,[tabindex]')].filter(e=>{
   if(e.disabled) return false; const t=e.getAttribute('tabindex');
   if(t!==null && Number(t)<0) return false;
   const s=getComputedStyle(e);
   if(s.display==='none'||s.visibility==='hidden') return false;
   const r=e.getBoundingClientRect(); return r.width>0&&r.height>0;});
 const e=els[a[0]]; if(!e) return {err:'oob'};
 e.focus();
 return {focused:document.activeElement===e, tag:e.tagName,
   type:e.getAttribute('type'),
   tf:e.getAttribute('data-director-transform-field'),
   ta:e.getAttribute('data-director-transform-axis')};}"""

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


def load_open(pg):
    pg.set_viewport_size({"width": 800, "height": 1000})
    pg.goto(BASE, wait_until="networkidle")
    pg.wait_for_selector(".react-flow__node", timeout=25000)
    pg.wait_for_timeout(1200)
    pg.keyboard.press("Meta+0")
    pg.wait_for_timeout(600)
    settle(pg)
    s = pg.evaluate(SCAN_CLICK, "[data-open-director]")
    if not s.get("pt"):
        return {"FAILED_open": s}
    pg.mouse.click(s["pt"][0], s["pt"][1])
    try:
        pg.wait_for_selector('[role="dialog"][aria-modal="true"]', timeout=25000)
    except Exception:
        return {"FAILED_open": "点了但没 dialog"}
    pg.wait_for_timeout(2200)
    return {"opened": True}


def open_drawer(pg):
    st = pg.evaluate(DESK)
    if (st.get("inspector") or {}).get("state") == "open":
        return {"alreadyOpen": True}
    s = pg.evaluate(SCAN_CLICK, 'button[aria-label="打开属性面板"]')
    if not s.get("pt"):
        return {"FAILED": s}
    pg.mouse.click(s["pt"][0], s["pt"][1])
    pg.wait_for_timeout(900)
    return {"clicked": True}


def drawer_state(desk):
    """★ 抽屉关掉 与 整个导演台关掉 是两件事，绝不能混。
    早先一版只写 `inspectorState != "open"` 就叫「关掉抽屉」，
    结果连整个导演台被 Esc 关掉的那一格也被记成了成功。"""
    insp = (desk or {}).get("inspector") or {}
    tree = (desk or {}).get("tree") or {}
    open_ = (desk or {}).get("open")
    return {"deskOpen": open_,
            "inspectorState": insp.get("state"),
            "treeState": tree.get("state"),
            "drawerClosed": (open_ is True
                             and insp.get("state") != "open"),
            "workspaceClosed": (open_ is False)}


def run_cell(pg, cell):
    """每格自带一次「在 800 宽度加载 + 打开导演台 + 打开属性抽屉」，
    格与格之间互不污染 —— 上一格把关导演台关掉不会连累下一格。"""
    op = load_open(pg)
    cell["open"] = op
    if op.get("FAILED_open"):
        return cell
    d = open_drawer(pg)
    cell["openDrawer"] = d
    st = pg.evaluate(DESK)
    if not st.get("open") or (st.get("inspector") or {}).get("state") != "open":
        cell["FAILED_openDrawer"] = drawer_state(st)
        return cell
    tg = pg.evaluate(TARGETS)
    cell["boundaryIdx"] = tg.get("gestureBoundaryIdx") or []
    if not cell["boundaryIdx"]:
        cell["FAILED_noBoundary"] = "属性面板里没找到 gesture 边界控件"
        return cell
    cell["targetIndex"] = cell["boundaryIdx"][0]
    cell["targetItem"] = tg["items"][cell["targetIndex"]]
    return cell


def run_round(pg, R):
    cells = {}
    for name in ("A_focusOnly", "B_esc1", "C_esc2", "D_escapeHatch",
                 "E_editKey"):
        cells[name] = {}
    R["cells"] = cells

    # ── A 只聚焦那个框，不按任何键
    c = run_cell(pg, cells["A_focusOnly"])
    if "targetIndex" in c:
        pre = pg.evaluate(DESK)
        f = pg.evaluate(FOCUS_N, [c["targetIndex"]])
        pg.wait_for_timeout(500)
        post = pg.evaluate(DESK)
        c["focus"] = f
        c["before"] = pre
        c["afterFocus"] = post
        c["gestureOpenedByFocusOnly"] = (not pre.get("activeGesture")
                                         and bool(post.get("activeGesture")))
        c["historyPastOnFocus"] = [pre.get("historyPast"),
                                   post.get("historyPast")]
    print("A 只聚焦 →", json.dumps(
        {k: cells["A_focusOnly"].get(k) for k in
         ("targetItem", "focus", "gestureOpenedByFocusOnly",
          "historyPastOnFocus")}, ensure_ascii=False)[:300])

    # ── B 聚焦后按一次 Esc
    c = run_cell(pg, cells["B_esc1"])
    if "targetIndex" in c:
        pre = pg.evaluate(DESK)
        pg.evaluate(FOCUS_N, [c["targetIndex"]])
        pg.wait_for_timeout(450)
        post = pg.evaluate(DESK)
        pg.keyboard.press("Escape")
        pg.wait_for_timeout(650)
        after = pg.evaluate(DESK)
        c["beforeEsc"] = post
        c["afterEsc"] = after
        c["result"] = drawer_state(after)
        c["gestureClearedByEsc"] = (not after.get("activeGesture"))
        c["historyPastDelta"] = [post.get("historyPast"),
                                 after.get("historyPast")]
    print("B Esc#1 →", json.dumps(
        {k: cells["B_esc1"].get(k) for k in
         ("result", "gestureClearedByEsc", "historyPastDelta")},
        ensure_ascii=False)[:300])

    # ── C 再按一次 Esc（焦点仍在框里）
    c = run_cell(pg, cells["C_esc2"])
    if "targetIndex" in c:
        pg.evaluate(FOCUS_N, [c["targetIndex"]])
        pg.wait_for_timeout(450)
        pg.keyboard.press("Escape")
        pg.wait_for_timeout(600)
        first = pg.evaluate(DESK)
        pg.keyboard.press("Escape")
        pg.wait_for_timeout(700)
        second = pg.evaluate(DESK)
        c["afterEsc1"] = drawer_state(first)
        c["afterEsc2"] = drawer_state(second)
        c["focusStillInBoundary"] = bool(
            (second.get("active") or {}).get("tf"))
    print("C Esc#2 →", json.dumps(
        {k: cells["C_esc2"].get(k) for k in
         ("afterEsc1", "afterEsc2", "focusStillInBoundary")},
        ensure_ascii=False)[:300])

    # ── D Tab 离开边界再按 Esc（逃生门）
    c = run_cell(pg, cells["D_escapeHatch"])
    if "targetIndex" in c:
        pg.evaluate(FOCUS_N, [c["targetIndex"]])
        pg.wait_for_timeout(450)
        pg.keyboard.press("Tab")
        pg.wait_for_timeout(500)
        afterTab = pg.evaluate(DESK)
        pg.keyboard.press("Escape")
        pg.wait_for_timeout(800)
        after = pg.evaluate(DESK)
        c["afterTab"] = after
        c["afterTabEsc"] = after
        c["leftBoundaryOnTab"] = not bool((afterTab.get("active") or {}).get("tf"))
        c["tabLandedOn"] = afterTab.get("active")
        c["result"] = drawer_state(after)
    print("D Tab 后 Esc →", json.dumps(
        {k: cells["D_escapeHatch"].get(k) for k in
         ("leftBoundaryOnTab", "tabLandedOn", "result")},
        ensure_ascii=False)[:340])

    # ── E 聚焦 → ArrowUp → Tab（真编辑一次，看 gesture 与 history）
    c = run_cell(pg, cells["E_editKey"])
    if "targetIndex" in c:
        pre = pg.evaluate(DESK)
        pg.evaluate(FOCUS_N, [c["targetIndex"]])
        pg.wait_for_timeout(450)
        afterFocus = pg.evaluate(DESK)
        pg.keyboard.press("ArrowUp")
        pg.wait_for_timeout(700)
        afterEdit = pg.evaluate(DESK)
        pg.keyboard.press("Tab")
        pg.wait_for_timeout(700)
        afterBlur = pg.evaluate(DESK)
        c["before"] = pre
        c["afterFocus"] = afterFocus
        c["afterEdit"] = afterEdit
        c["afterBlur"] = afterBlur
        c["gestureOpenedByFocusOnly"] = (not pre.get("activeGesture")
                                         and bool(afterFocus.get("activeGesture")))
        c["historyPastDelta"] = [pre.get("historyPast"),
                                 afterEdit.get("historyPast")]
        c["gestureOnBlur"] = [afterEdit.get("activeGesture"),
                              afterBlur.get("activeGesture")]
        c["valueOnBlur"] = (afterBlur.get("active") or {}).get("type")
    print("E 编辑键 →", json.dumps(
        {k: cells["E_editKey"].get(k) for k in
         ("gestureOpenedByFocusOnly", "historyPastDelta", "gestureOnBlur")},
        ensure_ascii=False)[:300])


def main():
    res = {"batch": 763, "probe": "f",
           "question": "useDirectorGestureBoundary 吞掉 Esc 之后的完整后果",
           "rounds": []}
    with sync_playwright() as p:
        br = p.chromium.launch()
        pg = br.new_page(viewport={"width": 800, "height": 1000})
        try:
            for _ in range(2):
                R = {}
                res["rounds"].append(R)
                run_round(pg, R)
        finally:
            OUT.parent.mkdir(parents=True, exist_ok=True)
            try:
                br.close()
            except Exception:
                pass
            OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1),
                           encoding="utf-8")
            print("\n（已先落盘，异常也不丢读数）")

    if len(res["rounds"]) < 2:
        print("只跑完 %d 轮" % len(res["rounds"]))
        return

    def strip(o):
        if isinstance(o, dict):
            return {k: strip(v) for k, v in o.items()}
        if isinstance(o, list):
            return [strip(v) for v in o]
        return o

    r1, r2 = res["rounds"]
    res["consistent"] = (strip(r1) == strip(r2))
    print("两轮完全一致 =", res["consistent"])
    print("wrote %s" % OUT)


if __name__ == "__main__":
    main()
