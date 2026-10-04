#!/usr/bin/env python3
"""batch 765 探针 a：导入/导出面板内的焦点围栏（763 明确留下的第三块）

763a 在 1440 桌面下量过 Esc 优先级阶梯（导出面板开着时第一次只关面板、
第二次才关导演台、焦点在可编辑控件里时不关），但那是**焦点在触发按钮上**、
且**只有 1440**。本批补三块：

① **面板内逐控件 Esc**：`DirectorExportPanel.tsx` 一共 5 个可聚焦控件
   （1 个时长 `input[type=number]` `:60`、3 枚画幅按钮 `:81`、
   1 枚提交按钮 `:132`）。面板源码里**没有 onKeyDown、没有 stopPropagation、
   也没有手势边界**，所以预期 Esc 处处能关面板 —— 预期不是读数，逐个量。
   （提交按钮**只读不点**：Batch 596 的注释写明点它可能启动真实导出，
   属付费/破坏性动作，未授权。）

② **面板是不是焦点陷阱**：面板是 `absolute z-50` 贴在时间轴上的一个
   popover，**不是 modal**。Tab 会不会走到它背后的其他控件上？
   762 量的是 dialog 级别的围栏，没有量过这个 popover。

③ **800px 移动端形态下的 Esc 优先级**：移动端还有「关抽屉」那一档
   （`DirectorDesk.tsx:481-485`，排在 isEditable 早退之前）。
   面板 + 抽屉 + 导演台三档同时存在时，Esc 先关哪个？

外加一格没人问过的：**导入按钮到底会不会真的弹文件选择器**。
`data-director-project-import`（`DirectorDesk.tsx:1128`）背后是一个
隐藏 file input（`:1110`，762 记过它**没有 aria-label**）。
用 Playwright 的 `expect_file_chooser` 量：点了到底弹不弹。
"""
import json
import pathlib
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

BASE = "http://localhost:4317"
OUT = pathlib.Path(
    "/Users/yangjiefeng/Documents/wubuku/liblib-tv"
    "/docs/research/liblib-canvas-batch765-2026-10-01/raw/vb765a.json")

DESK = """()=>{const d=document.querySelector('[role="dialog"][aria-modal="true"]');
 if(!d) return {open:false};
 const panel=d.querySelector('[data-director-export-panel]');
 const trig=d.querySelector('[data-director-export-trigger]');
 const tree=d.querySelector('aside[aria-label="场景对象"]');
 const insp=d.querySelector('aside[aria-label="属性"]');
 const p=(el)=>{if(!el) return null; const r=el.getBoundingClientRect();
   return {state:el.getAttribute('data-director-mobile-panel-state'),
     focusScope:el.getAttribute('data-director-focus-scope'),
     inert:!!el.inert, x:Math.round(r.x), w:Math.round(r.width)};};
 const a=document.activeElement;
 return {open:true, vw:innerWidth,
   tree:p(tree), inspector:p(insp),
   trigger:trig?{present:true,
     ariaExpanded:trig.getAttribute('aria-expanded'),
     text:(trig.textContent||'').trim().slice(0,12),
     x:Math.round(trig.getBoundingClientRect().x),
     y:Math.round(trig.getBoundingClientRect().y),
     w:Math.round(trig.getBoundingClientRect().width),
     h:Math.round(trig.getBoundingClientRect().height)}:null,
   panel:panel?{present:true,
     status:panel.getAttribute('data-director-export-status'),
     progress:panel.getAttribute('data-director-export-progress'),
     rect:{x:Math.round(panel.getBoundingClientRect().x),
           y:Math.round(panel.getBoundingClientRect().y),
           w:Math.round(panel.getBoundingClientRect().width),
           h:Math.round(panel.getBoundingClientRect().height)},
     duration:(()=>{const i=panel.querySelector(
       '[data-director-export-duration]');
       return i?{value:i.value, disabled:!!i.disabled,
                 min:i.getAttribute('min'), max:i.getAttribute('max'),
                 step:i.getAttribute('step'),
                 aria:i.getAttribute('aria-label')}:null;})(),
     aspect:(()=>{return [...panel.querySelectorAll(
       '[data-director-export-aspect]')].map(b=>({
         ratio:b.getAttribute('data-director-export-aspect'),
         pressed:b.getAttribute('aria-pressed'),
         disabled:!!b.disabled,
         text:(b.textContent||'').trim().slice(0,6)}));})(),
     submit:(()=>{const s=panel.querySelector(
       '[data-director-export-submit]');
       return s?{present:true, text:(s.textContent||'').trim().slice(0,12),
                 disabled:!!s.disabled, type:s.getAttribute('type')}:null;})(),
     focusables:(()=>{const out=[]; let i=0;
       for(const e of panel.querySelectorAll(
         'a[href],button,input,select,textarea,[tabindex]')){
         if(e.disabled) continue; const t=e.getAttribute('tabindex');
         if(t!==null && Number(t)<0) continue;
         const s=getComputedStyle(e);
         if(s.display==='none'||s.visibility==='hidden') continue;
         const r=e.getBoundingClientRect();
         if(r.width<=0||r.height<=0) continue;
         out.push({i:i++, tag:e.tagName, type:e.getAttribute('type'),
           marker:(e.getAttribute('data-director-export-duration')!==null
             ?'duration':(e.getAttribute('data-director-export-aspect')||'')),
           submit:(e.getAttribute('data-director-export-submit')!==null),
           text:(e.textContent||'').trim().slice(0,8)});}
       return out;})()} : {present:false},
   active:{tag:a?a.tagName:null, type:a?a.getAttribute('type'):null,
     aria:a?a.getAttribute('aria-label'):null,
     inPanel:!!(a&&panel&&panel.contains(a)),
     inDialog:d===a||d.contains(a),
     isTrigger:!!(a&&trig&&trig===a),
     text:a?(a.textContent||'').trim().slice(0,12):null}};}"""

FOCUS_N = """(a)=>{const idx=a[0];
 const d=document.querySelector('[role="dialog"][aria-modal="true"]');
 const p=d&&d.querySelector('[data-director-export-panel]');
 if(!p) return {err:'no panel'};
 const els=[...p.querySelectorAll(
   'a[href],button,input,select,textarea,[tabindex]')].filter(e=>{
   if(e.disabled) return false; const t=e.getAttribute('tabindex');
   if(t!==null && Number(t)<0) return false;
   const s=getComputedStyle(e);
   if(s.display==='none'||s.visibility==='hidden') return false;
   const r=e.getBoundingClientRect(); return r.width>0&&r.height>0;});
 const e=els[idx]; if(!e) return {err:'oob'};
 e.focus();
 return {focused:document.activeElement===e, tag:e.tagName,
   type:e.getAttribute('type'),
   marker:(e.getAttribute('data-director-export-duration')!==null
     ?'duration':(e.getAttribute('data-director-export-aspect')||'')),
   submit:(e.getAttribute('data-director-export-submit')!==null)};}"""

SCAN_CLICK = """(sel)=>{const el=document.querySelector(sel);
 if(!el) return {missing:true};
 const r=el.getBoundingClientRect();
 for(let f=0.08; f<=0.95; f+=0.07)
   for(let g=0.08; g<=0.95; g+=0.07){
     const x=Math.round(r.x+r.width*f), y=Math.round(r.y+r.height*g);
     if(x<2||y<2||x>innerWidth-2||y>innerHeight-2) continue;
     const e=document.elementFromPoint(x,y);
     if(e&&e.closest&&e.closest(sel)) return {pt:[x,y],
       rect:{x:Math.round(r.x),y:Math.round(r.y),
             w:Math.round(r.width),h:Math.round(r.height)}};}
 return {noHit:true, rect:{x:Math.round(r.x),y:Math.round(r.y),
   w:Math.round(r.width),h:Math.round(r.height)}};}"""

IMPORT_PROBE = """()=>{const d=document.querySelector(
  '[role="dialog"][aria-modal="true"]');
 if(!d) return {err:'no dialog'};
 const btn=d.querySelector('[data-director-project-import]');
 const inp=d.querySelector('[data-director-project-import-input]');
 const b=btn?btn.getBoundingClientRect():null;
 const i=inp?inp.getBoundingClientRect():null;
 return {btn:btn?{tag:btn.tagName, type:btn.getAttribute('type'),
     ariaLabel:btn.getAttribute('aria-label'),
     title:btn.getAttribute('title'),
     text:(btn.textContent||'').trim().slice(0,10),
     disabled:!!btn.disabled,
     rect:b?{x:Math.round(b.x),y:Math.round(b.y),
             w:Math.round(b.width),h:Math.round(b.height)}:null}:null,
   input:inp?{tag:inp.tagName, type:inp.getAttribute('type'),
     accept:inp.getAttribute('accept'),
     ariaLabel:inp.getAttribute('aria-label'),
     id:inp.id||null,
     display:getComputedStyle(inp).display,
     visibility:getComputedStyle(inp).visibility,
     rect:i?{x:Math.round(i.x),y:Math.round(i.y),
             w:Math.round(i.width),h:Math.round(i.height)}:null}:null,
   inputFocusable:(()=>{if(!inp) return null;
     const s=getComputedStyle(inp); const r=inp.getBoundingClientRect();
     return {tabIndex:inp.tabIndex, display:s.display,
       visibility:s.visibility, w:Math.round(r.width),
       h:Math.round(r.height)};})(),
   btnWiredToInput:(()=>{if(!btn||!inp) return null;
     const id=inp.id;
     return {inputHasId:!!id,
       labelFor:(!!id && !!d.querySelector('label[for="'+id+'"]'))};})()};}"""


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


def load_open(pg, width):
    pg.set_viewport_size({"width": width, "height": 1000})
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
    return {"opened": True, "width": width}


def open_panel(pg):
    st = pg.evaluate(DESK)
    if (st.get("panel") or {}).get("present"):
        return {"alreadyOpen": True}
    s = pg.evaluate(SCAN_CLICK, "[data-director-export-trigger]")
    if not s.get("pt"):
        return {"FAILED": s, "desk": st}
    pg.mouse.click(s["pt"][0], s["pt"][1])
    pg.wait_for_timeout(900)
    return {"clicked": True, "rect": s.get("rect"),
            "desk": pg.evaluate(DESK)}


def esc(pg):
    pg.keyboard.press("Escape")
    pg.wait_for_timeout(600)
    return pg.evaluate(DESK)


def sweep_panel_esc(pg, label):
    """面板开着时，逐个控件聚焦后按 Esc，看面板关不关。"""
    st = pg.evaluate(DESK)
    p = st.get("panel") or {}
    if not p.get("present"):
        return {"FAILED": "面板没开", "desk": st}
    items = p.get("focusables") or []
    rows = []
    for it in items:
        st0 = pg.evaluate(DESK)
        if not (st0.get("panel") or {}).get("present"):
            op = open_panel(pg)
            if "FAILED" in op:
                rows.append({"i": it["i"], "item": it,
                             "skipped": "重开面板失败", "open": op})
                break
        f = pg.evaluate(FOCUS_N, [it["i"]])
        before = pg.evaluate(DESK)
        after = esc(pg)
        rows.append({"i": it["i"], "item": it, "focus": f,
                     "focusedInPanel": (before.get("active") or {}
                                        ).get("inPanel"),
                     "panelClosed": not (after.get("panel") or {}
                                         ).get("present"),
                     "workspaceClosed": after.get("open") is False,
                     "drawerStateAfter": (after.get("inspector") or {}
                                          ).get("state")})
    return {"label": label, "panelFocusables": len(items),
            "rows": rows,
            "allClosed": all(r.get("panelClosed") for r in rows
                             if "panelClosed" in r) and bool(rows),
            "anyWorkspaceClosed": any(r.get("workspaceClosed") for r in rows)}


def tab_walk(pg, n):
    seq = []
    for _ in range(n):
        pg.keyboard.press("Tab")
        pg.wait_for_timeout(90)
        a = pg.evaluate(DESK).get("active") or {}
        seq.append({"tag": a.get("tag"), "aria": a.get("ariaLabel"),
                    "text": a.get("text"), "inPanel": a.get("inPanel"),
                    "inDialog": a.get("inDialog"),
                    "isTrigger": a.get("isTrigger")})
    in_dialog = [x for x in seq if x["inDialog"] is False]
    return {"steps": n, "escapedCount": len(in_dialog),
            "escapedAt": [i for i, x in enumerate(seq)
                          if x["inDialog"] is False],
            "inPanelCount": sum(1 for x in seq if x["inPanel"]),
            "onTriggerCount": sum(1 for x in seq if x["isTrigger"]),
            "seq": seq}


def mobile_case(pg, R):
    """800px：先开属性抽屉，再开导出面板，量「面板 / 抽屉 / 导演台」三档 Esc 优先级。

    ★ 初版这里无脑 `press("Escape")` 想「关掉可能开着的抽屉」，结果那时并没有
      抽屉开着，Esc 顺着阶梯把**整个导演台关掉了** —— 后面三格读数全是空的
      （`desk.open=false`、`m_openPanel.missing=true`）。
      规矩：**按 Esc 之前先读状态**，只在该关的时候关；按完还要**断言**目标
      真的变了自己要的样子，否则这一格记 FAILED，不留空读数。
    """
    R["m_load"] = load_open(pg, 800)
    if R["m_load"].get("FAILED_open"):
        R["m_verdict"] = "打开导演台失败"
        return
    st0 = pg.evaluate(DESK)
    R["m_afterLoad"] = {"open": st0.get("open"),
                        "inspector": (st0.get("inspector") or {}).get("state"),
                        "tree": (st0.get("tree") or {}).get("state")}
    if st0.get("open") is not True:
        R["m_verdict"] = "加载后导演台没开"
        return
    # 只在抽屉确实开着时才按 Esc 去关它
    if ((st0.get("inspector") or {}).get("state") == "open"
            or (st0.get("tree") or {}).get("state") == "open"):
        pg.keyboard.press("Escape")
        pg.wait_for_timeout(600)
        st1 = pg.evaluate(DESK)
        R["m_closedStaleDrawer"] = {
            "inspector": (st1.get("inspector") or {}).get("state"),
            "tree": (st1.get("tree") or {}).get("state"),
            "open": st1.get("open")}
        if st1.get("open") is not True:
            R["m_verdict"] = "为了关抽屉那一下 Esc 把导演台关掉了（探针顺序错）"
            return
    # 开属性抽屉
    s = pg.evaluate(SCAN_CLICK, 'button[aria-label="打开属性面板"]')
    R["m_drawerScan"] = s
    if s.get("pt"):
        pg.mouse.click(s["pt"][0], s["pt"][1])
        pg.wait_for_timeout(900)
    R["m_drawer"] = pg.evaluate(DESK)
    if (R["m_drawer"].get("inspector") or {}).get("state") != "open":
        R["m_verdict"] = "属性抽屉没开成功，后面的 Esc 阶梯不作数"
        return
    R["m_openPanel"] = open_panel(pg)
    R["m_state"] = pg.evaluate(DESK)
    if not (R["m_state"].get("panel") or {}).get("present"):
        R["m_verdict"] = "800px 下导出面板没打开（触发器 %s）" % json.dumps(
            R["m_openPanel"], ensure_ascii=False)[:200]
        return
    R["m_panelFocusables"] = (R["m_state"].get("panel") or {}).get(
        "focusables")

    # ① 焦点在时长数值框里按 Esc（预期：被 isEditable 吃掉，参考 1440 的读数）
    R["m_focusFirst"] = pg.evaluate(FOCUS_N, [0])
    R["m_escFromDuration"] = _esc_state(pg)
    # ② 焦点在画幅按钮上按 Esc（预期：关面板）
    if not (R["m_escFromDuration"].get("panelClosed")
            or R["m_escFromDuration"].get("workspaceClosed")):
        pg.evaluate(FOCUS_N, [1])
        R["m_escFromAspect"] = _esc_state(pg)
    # ③ 继续按，直到抽屉关、导演台关
    R["m_escNext"] = _esc_state(pg)
    R["m_escNext2"] = _esc_state(pg)
    R["m_after"] = pg.evaluate(DESK)


def _esc_state(pg):
    pg.keyboard.press("Escape")
    pg.wait_for_timeout(650)
    d = pg.evaluate(DESK)
    return {"panelClosed": not (d.get("panel") or {}).get("present"),
            "drawerState": (d.get("inspector") or {}).get("state"),
            "treeState": (d.get("tree") or {}).get("state"),
            "workspaceClosed": d.get("open") is False,
            "active": d.get("active")}


def desktop_case(pg, R):
    R["d_load"] = load_open(pg, 1440)
    if R["d_load"].get("FAILED_open"):
        return
    R["d_before"] = pg.evaluate(DESK)
    R["d_openPanel"] = open_panel(pg)
    R["d_state"] = pg.evaluate(DESK)
    st = pg.evaluate(DESK)
    R["d_focusOnOpen"] = st.get("active")
    R["d_sweep"] = sweep_panel_esc(pg, "desktop")
    R["d_reopen"] = open_panel(pg)
    # 焦点先落进第一个控件再 Tab：会不会跑到面板背后去？
    pg.evaluate(FOCUS_N, [0])
    R["d_tabFromPanel"] = tab_walk(pg, 12)
    # 面板开着但焦点在触发按钮上时 Tab（763a 的那条路径，补齐读数）
    op = pg.evaluate("""()=>{const d=document.querySelector(
      '[role="dialog"][aria-modal="true"]');
     const t=d&&d.querySelector('[data-director-export-trigger]');
     if(!t) return {err:'no trigger'};
     t.focus(); return {focused:document.activeElement===t};}""")
    R["d_focusTrigger"] = op
    R["d_tabFromTrigger"] = tab_walk(pg, 12)


def import_case(pg, R):
    R["i_probe"] = pg.evaluate(IMPORT_PROBE)
    btn = pg.evaluate(SCAN_CLICK, "[data-director-project-import]")
    R["i_clickScan"] = btn
    if not btn.get("pt"):
        R["i_verdict"] = "按钮扫网格 0 命中，未点"
        return
    fired = {"fired": False, "multiple": None, "suggested": None}
    try:
        with pg.expect_file_chooser(timeout=2500) as fc:
            pg.mouse.click(btn["pt"][0], btn["pt"][1])
        info = fc.value
        fired = {"fired": True,
                 "multiple": info.page is not None,
                 "suggested": getattr(info, "element", None) is not None}
    except PWTimeout:
        fired = {"fired": False}
    except Exception as e:
        fired = {"fired": False, "err": str(e)[:120]}
    R["i_fileChooser"] = fired
    R["i_after"] = pg.evaluate(DESK)
    # 导入按钮键盘可达吗
    kb = pg.evaluate("""()=>{const d=document.querySelector(
      '[role="dialog"][aria-modal="true"]');
     const b=d&&d.querySelector('[data-director-project-import]');
     if(!b) return {err:'no button'};
     b.focus();
     return {focused:document.activeElement===b,
       tag:b.tagName, type:b.getAttribute('type'),
       aria:b.getAttribute('aria-label')};}""")
    R["i_focus"] = kb
    # 隐藏 file input 有没有可访问名（762 记过它没有 aria-label）
    R["i_inputName"] = pg.evaluate("""()=>{const d=document.querySelector(
      '[role="dialog"][aria-modal="true"]');
     const i=d&&d.querySelector('[data-director-project-import-input]');
     if(!i) return {err:'no input'};
     const id=i.id;
     const lab=id?d.querySelector('label[for="'+id+'"]'):null;
     return {ariaLabel:i.getAttribute('aria-label'),
       title:i.getAttribute('title'),
       id:id||null,
       labelForText:lab?(lab.textContent||'').trim().slice(0,10):null,
       hasLabelFor:!!lab,
       tabIndex:i.tabIndex,
       accessibleNameGuess:((i.getAttribute('aria-label')
         || i.getAttribute('title')
         || (lab?(lab.textContent||'').trim():'') || '') || null)};}""")


def run_round(pg, R):
    desktop_case(pg, R)
    import_case(pg, R)
    mobile_case(pg, R)
    sweep = R.get("d_sweep") or {}
    print("   1440：面板可聚焦 %s 个 | 逐个 Esc 全关=%s | Tab 从面板出 Dialog %s 次"
          % (sweep.get("panelFocusables"), sweep.get("allClosed"),
             (R.get("d_tabFromPanel") or {}).get("escapedCount")))
    print("   800：%s" % (R.get("m_verdict") or "流程走完"))
    for k in ("m_escFromDuration", "m_escFromAspect", "m_escNext",
              "m_escNext2"):
        if R.get(k):
            print("        %-20s 关面板=%-5s 抽屉=%-7s 关导演台=%s"
                  % (k, R[k]["panelClosed"], R[k]["drawerState"],
                     R[k]["workspaceClosed"]))
    print("   导入：filechooser=%s | 隐藏 input 可访问名=%s"
          % ((R.get("i_fileChooser") or {}).get("fired"),
             json.dumps((R.get("i_inputName") or {}).get("accessibleNameGuess"),
                        ensure_ascii=False)))


def main():
    res = {"batch": 765, "probe": "a",
           "question": "导入/导出面板内的焦点围栏、逐控件 Esc、"
                       "800px 三档 Esc 优先级、导入按钮会不会弹文件选择器",
           "rounds": []}
    with sync_playwright() as p:
        br = p.chromium.launch()
        ctx = br.new_context(viewport={"width": 1440, "height": 1000})
        pg = ctx.new_page()
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
            print("（已落盘）")
    for rd, R in enumerate(res["rounds"], 1):
        print("\n=== r%d ===" % rd)
        st = R.get("d_state") or {}
        print("  面板 status=%s 时长=%s 画幅=%s 提交=%s"
              % ((st.get("panel") or {}).get("status"),
                 json.dumps((st.get("panel") or {}).get("duration"),
                            ensure_ascii=False),
                 json.dumps((st.get("panel") or {}).get("aspect"),
                            ensure_ascii=False)[:150],
                 json.dumps((st.get("panel") or {}).get("submit"),
                            ensure_ascii=False)))
        print("  打开瞬间焦点 =", json.dumps(R.get("d_focusOnOpen"),
                                            ensure_ascii=False))
        print("  触发器 aria-expanded =",
              (st.get("trigger") or {}).get("ariaExpanded"))
    print("wrote %s" % OUT)


if __name__ == "__main__":
    main()
