#!/usr/bin/env python3
"""batch 765 探针 b：把 765a 的两个「看起来像缺陷」的读数做成对照实验

765a 量出来两件事，都还只是读数，没判成缺陷：

① **时长数值框里的 Esc 关不掉面板**（1440 下面板不关、导演台不关；
   800px 下面板不关、只关了更早那一档的抽屉）。同一个症状在 batch 764
   已经出现过一次（D2：`DirectorDesk.tsx:481` 的 `if (isEditable) return;`
   让 ⌘C/⌘V 在任何可编辑控件里彻底失效）。**但不能就这么套上去** ——
   763 的 D1 当时看起来也是「数值框吞 Esc」，最后被注入对照否掉了，
   真凶是 `useDirectorGestureBoundary` 的 stopPropagation。
   这次必须**在这个位置**重新做注入对照，不能拿 763 的结论当证据。

   四个注入对照，都插在面板里时长框的旁边（同一父节点、同一时刻）：
     A `input[type=text]`   —— 若**也**关不掉 ⟹ 与 `type=number` 无关，
                              是「可编辑性」判定，不是 number 原生吞 Esc
     B `input[type=number]` —— 阳性对照：探针自己得能复现出「不关」
     C `div[contenteditable]`—— `:477` 的 `isContentEditable` 分支
     D `div[tabindex=0]`    —— 负向对照：不是 INPUT 这个标签本身的问题，
                              不可编辑的元素照关不误
   每次都记「Esc 有没有到达 window 冒泡」（window 上挂捕获+冒泡两个
   探针，见 763 的手法），把「事件根本没上来」和「上来了被代码 return 掉」
   分开。**读标志必须在清标志之前**（R58）。

② **Esc 关掉面板后焦点掉到 `body`、逃出导演台对话框**（两轮一致）。
   静态侧已经找到机制：`DirectorExportPanel.tsx:38` 的 `if (!open) return null`
   会把正在聚焦的元素整个卸载，而 `DirectorDesk.tsx:557-560` 的关闭分支
   只调了 `setExportPanelOpen(false)`、**没碰焦点**；围栏 hook
   `useDirectorFocusContainment.ts` 只在 `keydown` 里接管 Tab
   （`:149-172`）、**没有 focusin 监听**，所以也捞不回来。
   还差一格没量：这个「死路」有多死 —— 焦点掉到 body 之后，**按 Tab
   能不能回导演台里**？hook 的 Tab 接管挂在 root 上，事件目标在 body
   时根本冒泡不到 root。量 6 步看落点。

外加两格没人问过的：

③ **外点关闭**：`setExportPanelOpen` 全仓只有 3 处调用（`:294` 初始化、
   `:558` Esc、`:624` toggle），**没有任何 pointerdown/外点监听**。
   打开面板后点别处，面板会不会自己收起？（预期：不会 —— 于是 ① 那个
   「时长框里 Esc 关不掉」就有了第二条退路：面板可能卡在打开状态）

④ **反向 Tab**：面板在 DOM 序上位于触发器**之后**（`:1351` 挂在
   `:1338` 那个按钮后面），而围栏 hook 的 Tab 数组是 `querySelectorAll`
   的 DOM 序。焦点停在触发器、面板开着时按 Shift+Tab —— 进得去面板吗？
   （预期：进不去。`aria-expanded=true` 却没有 `aria-controls`/
   `aria-haspopup`，键盘用户只能正向 Tab 进。）

**不点提交按钮**（Batch 596 注释：可能启动真实导出，属付费/破坏性动作），
**不选文件**（会覆盖种子项目）。
"""
import json
import pathlib
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

BASE = "http://localhost:4317"
OUT = pathlib.Path(
    "/Users/yangjiefeng/Documents/wubuku/liblib-tv"
    "/docs/research/liblib-canvas-batch765-2026-10-01/raw/vb765b.json")

DESK = """()=>{const d=document.querySelector('[role="dialog"][aria-modal="true"]');
 if(!d) return {open:false};
 const panel=d.querySelector('[data-director-export-panel]');
 const trig=d.querySelector('[data-director-export-trigger]');
 const a=document.activeElement;
 return {open:true, vw:innerWidth,
   trigger:trig?{present:true,
     ariaExpanded:trig.getAttribute('aria-expanded'),
     ariaControls:trig.getAttribute('aria-controls'),
     ariaHasPopup:trig.getAttribute('aria-haspopup'),
     text:(trig.textContent||'').trim().slice(0,12)}:null,
   panel:panel?{present:true,
     status:panel.getAttribute('data-director-export-status'),
     tag:panel.tagName,
     role:panel.getAttribute('role'),
     ariaLabel:panel.getAttribute('aria-label'),
     id:panel.id||null,
     rect:{x:Math.round(panel.getBoundingClientRect().x),
           y:Math.round(panel.getBoundingClientRect().y),
           w:Math.round(panel.getBoundingClientRect().width),
           h:Math.round(panel.getBoundingClientRect().height)}}:null,
   active:{tag:a?a.tagName:null, type:a?a.getAttribute('type'):null,
     aria:a?a.getAttribute('aria-label'):null,
     inPanel:!!(a&&panel&&panel.contains(a)),
     inDialog:d===a||d.contains(a),
     isTrigger:!!(a&&trig&&trig===a),
     isBody:a===document.body,
     text:a?(a.textContent||'').trim().slice(0,12):null}};}"""

# window 上的 Esc 传播探针：记录「有没有到达 window 冒泡」。
# ★ 先读标志、再清标志（R58）：这里把标志留在 window 上，每格开一次、
#   读一次就清，不在同一格里既读又清。
FLAG = """()=>{window.__escReach={capture:0,bubble:0,
  lastTarget:null};
 window.addEventListener('keydown',(e)=>{if(e.key!=='Escape')return;
   window.__escReach.capture++;},true);
 window.addEventListener('keydown',(e)=>{if(e.key!=='Escape')return;
   window.__escReach.bubble++; window.__escReach.lastTarget=
   e.target?e.target.tagName+'/'+(e.target.getAttribute('type')||''):null;});
 return {armed:true};}"""

READ_FLAG = """()=>{const r=window.__escReach||{capture:0,bubble:0,lastTarget:null};
 window.__escReach={capture:0,bubble:0,lastTarget:null}; return r;}"""

# 在时长框旁边插一个元素并聚焦它。插完立刻可用，调用方负责移除。
INJECT = """(spec)=>{const d=document.querySelector(
  '[role="dialog"][aria-modal="true"]');
 const p=d&&d.querySelector('[data-director-export-panel]');
 if(!p) return {err:'no panel'};
 const dur=p.querySelector('[data-director-export-duration]');
 if(!dur) return {err:'no duration'};
 const host=dur.parentElement;
 let el;
 if(spec.kind==='contenteditable'){
   el=document.createElement('div');
   el.setAttribute('contenteditable','true');
   el.textContent='注入';
 } else if(spec.kind==='tabindex'){
   el=document.createElement('div');
   el.setAttribute('tabindex','0');
   el.textContent='注入';
 } else {
   el=document.createElement('input');
   el.type=spec.kind;
 }
 el.setAttribute('data-vb765b-inject',spec.kind);
 el.style.cssText='position:fixed;left:20px;top:20px;z-index:99999;'
   +'width:80px;height:24px;background:#000;color:#fff';
 host.appendChild(el);
 el.focus();
 const a=document.activeElement;
 return {injected:true, kind:spec.kind,
   focused:a===el, tag:a?a.tagName:null,
   type:a?a.getAttribute('type'):null,
   isContentEditable:!!(a&&a.isContentEditable),
   tabIndex:a?a.tabIndex:null,
   rect:{x:Math.round(el.getBoundingClientRect().x),
         y:Math.round(el.getBoundingClientRect().y)}};}"""

REMOVE = """()=>{const n=document.querySelectorAll('[data-vb765b-inject]');
 const c=n.length; n.forEach(e=>e.remove()); return {removed:c};}"""

# 面板外的一个空白点：先扫出那里到底是什么元素再点（R 原则：hit 必须先验）
SCAN_PT = """(a)=>{const x=a[0], y=a[1];
 const e=document.elementFromPoint(x,y);
 if(!e) return {none:true};
 const d=document.querySelector('[role="dialog"][aria-modal="true"]');
 const p=d&&d.querySelector('[data-director-export-panel]');
 return {tag:e.tagName, cls:(e.className&&e.className.baseVal===undefined
     ?String(e.className):String(e.className||'')).slice(0,60),
   text:(e.textContent||'').trim().slice(0,14),
   inDialog:!!(d&&(d===e||d.contains(e))),
   inPanel:!!(p&&(p===e||p.contains(e))),
   clickable:!!(e.closest&&e.closest('button,a,[role="button"],input'))};}"""


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


def load_open(pg, width=1440):
    pg.set_viewport_size({"width": width, "height": 1000})
    pg.goto(BASE, wait_until="networkidle")
    pg.wait_for_selector(".react-flow__node", timeout=25000)
    pg.wait_for_timeout(1200)
    pg.keyboard.press("Meta+0")
    pg.wait_for_timeout(600)
    settle(pg)
    s = pg.evaluate("""()=>{const el=document.querySelector('[data-open-director]');
     if(!el) return {missing:true};
     const r=el.getBoundingClientRect();
     for(let f=0.08; f<=0.95; f+=0.07)
       for(let g=0.08; g<=0.95; g+=0.07){
         const x=Math.round(r.x+r.width*f), y=Math.round(r.y+r.height*g);
         if(x<2||y<2||x>innerWidth-2||y>innerHeight-2) continue;
         const e=document.elementFromPoint(x,y);
         if(e&&e.closest&&e.closest('[data-open-director]'))
           return {pt:[x,y]};}
     return {noHit:true};}""")
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
    s = pg.evaluate("""()=>{const d=document.querySelector(
      '[role="dialog"][aria-modal="true"]');
     const t=d&&d.querySelector('[data-director-export-trigger]');
     if(!t) return {missing:true};
     const r=t.getBoundingClientRect();
     for(let f=0.08; f<=0.95; f+=0.07)
       for(let g=0.08; g<=0.95; g+=0.07){
         const x=Math.round(r.x+r.width*f), y=Math.round(r.y+r.height*g);
         if(x<2||y<2||x>innerWidth-2||y>innerHeight-2) continue;
         const e=document.elementFromPoint(x,y);
         if(e&&e.closest&&e.closest('[data-director-export-trigger]'))
           return {pt:[x,y]};}
     return {noHit:true};}""")
    if not s.get("pt"):
        return {"FAILED": s, "desk": st}
    pg.mouse.click(s["pt"][0], s["pt"][1])
    pg.wait_for_timeout(900)
    return {"clicked": True, "pt": s.get("pt")}


def esc_once(pg, label=""):
    """按一次 Esc，读标志 + 读状态。读标志在清标志之前（R58）。"""
    pg.evaluate(FLAG)
    pg.keyboard.press("Escape")
    pg.wait_for_timeout(650)
    reach = pg.evaluate(READ_FLAG)
    d = pg.evaluate(DESK)
    return {"label": label,
            "reachedWinCapture": reach.get("capture", 0) > 0,
            "reachedWinBubble": reach.get("bubble", 0) > 0,
            "escTargetAtWin": reach.get("lastTarget"),
            "panelClosed": not (d.get("panel") or {}).get("present"),
            "workspaceClosed": d.get("open") is False,
            "active": d.get("active")}


def inject_case(pg, R, key, kind, expect_closed):
    """注入对照：插一个元素 → 聚焦 → 按 Esc → 读标志与状态 → 移除。"""
    if not (pg.evaluate(DESK).get("panel") or {}).get("present"):
        op = open_panel(pg)
        if "FAILED" in op:
            R[key] = {"FAILED": "重开面板失败", "open": op}
            return
    inj = pg.evaluate(INJECT, {"kind": kind})
    if inj.get("err") or not inj.get("focused"):
        # 焦点没上去就说明位置不对，不能解释成「Esc 不管用」（R 原则）
        pg.evaluate(REMOVE)
        R[key] = {"FAILED": "注入元素没获得焦点", "inject": inj}
        return
    st = pg.evaluate(DESK)
    res = esc_once(pg, kind)
    res["inject"] = inj
    res["focusInPanelBefore"] = (st.get("active") or {}).get("inPanel")
    res["injectedStillInDom"] = pg.evaluate(
        """()=>!!document.querySelector('[data-vb765b-inject]')""")
    res["removed"] = pg.evaluate(REMOVE)
    res["expectPanelClosed"] = expect_closed
    res["matchesExpectation"] = res["panelClosed"] == expect_closed
    R[key] = res


def run_round(pg, R):
    R["load"] = load_open(pg)
    if R["load"].get("FAILED_open"):
        R["verdict"] = "打开导演台失败"
        return
    R["state0"] = pg.evaluate(DESK)
    R["openPanel"] = open_panel(pg)
    R["state1"] = pg.evaluate(DESK)
    if not (R["state1"].get("panel") or {}).get("present"):
        R["verdict"] = "面板没打开"
        return

    # ── ① 注入对照：时长框旁边的四个元素，各自按一次 Esc ─────────────
    inject_case(pg, R, "inj_text", "text", False)
    inject_case(pg, R, "inj_number", "number", False)
    inject_case(pg, R, "inj_ce", "contenteditable", False)
    inject_case(pg, R, "inj_tabindex", "tabindex", True)

    # ── ③ 外点关闭：点面板外的空白（点之前先验那里是什么元素）────────
    if not (pg.evaluate(DESK).get("panel") or {}).get("present"):
        open_panel(pg)
    pt = pg.evaluate(SCAN_PT, [320, 300])
    R["outsideScan"] = pt
    # 若那儿是画布背景/非可点元素才点；点到按钮就换坐标重扫
    x, y = 320, 300
    tries = 0
    while pt.get("clickable") and tries < 6:
        tries += 1
        x, y = 320 + tries * 90, 300 + tries * 40
        pt = pg.evaluate(SCAN_PT, [x, y])
        R["outsideScan"] = pt
    R["outsideClick"] = {"pt": [x, y], "hit": pt}
    if pt.get("none") or pt.get("clickable"):
        R["outsideClick"]["skipped"] = "没找到可安全点的空白点，未点"
    else:
        pg.mouse.click(x, y)
        pg.wait_for_timeout(700)
        d = pg.evaluate(DESK)
        R["outsideClick"].update({
            "panelStillOpen": (d.get("panel") or {}).get("present"),
            "panelClosed": not (d.get("panel") or {}).get("present"),
            "workspaceClosed": d.get("open") is False,
            "active": d.get("active")})

    # ── ② 焦点死路：Esc 关掉面板 → 焦点在 body → 连按 6 次 Tab ───────
    if not (pg.evaluate(DESK).get("panel") or {}).get("present"):
        open_panel(pg)
    # 先把焦点放进面板里的一个非可编辑控件（画幅按钮），关面板才有「聚焦元素被卸载」这回事
    pg.evaluate("""()=>{const d=document.querySelector(
      '[role="dialog"][aria-modal="true"]');
     const b=d&&d.querySelector('[data-director-export-aspect]');
     if(b) b.focus();
     return {focused:document.activeElement===b};}""")
    st_before = pg.evaluate(DESK)
    R["focaloss_before"] = st_before.get("active")
    R["focaloss_esc"] = esc_once(pg, "close-panel-by-esc")
    seq = []
    for _ in range(6):
        pg.keyboard.press("Tab")
        pg.wait_for_timeout(160)
        a = pg.evaluate(DESK).get("active") or {}
        seq.append({"tag": a.get("tag"), "aria": a.get("ariaLabel"),
                    "text": a.get("text"), "inDialog": a.get("inDialog"),
                    "isBody": a.get("isBody")})
    R["focaloss_tab6"] = {
        "steps": 6,
        "reachedDialogCount": sum(1 for x in seq if x["inDialog"] is True),
        "onBodyCount": sum(1 for x in seq if x["isBody"] is True),
        "seq": seq}

    # ── ④ 反向 Tab：焦点在触发器、面板开着，Shift+Tab 12 步 ──────────
    if not (pg.evaluate(DESK).get("panel") or {}).get("present"):
        open_panel(pg)
    f = pg.evaluate("""()=>{const d=document.querySelector(
      '[role="dialog"][aria-modal="true"]');
     const t=d&&d.querySelector('[data-director-export-trigger]');
     if(!t) return {err:'no trigger'};
     t.focus(); return {focused:document.activeElement===t,
       panelOpen:!!d.querySelector('[data-director-export-panel]')};}""")
    R["shift_focusTrigger"] = f
    seq2 = []
    for _ in range(12):
        pg.keyboard.press("Shift+Tab")
        pg.wait_for_timeout(110)
        a = pg.evaluate(DESK).get("active") or {}
        seq2.append({"tag": a.get("tag"), "aria": a.get("ariaLabel"),
                     "text": a.get("text"), "inPanel": a.get("inPanel"),
                     "inDialog": a.get("inDialog"),
                     "isTrigger": a.get("isTrigger")})
    R["shift_tab12"] = {
        "steps": 12,
        "inPanelCount": sum(1 for x in seq2 if x["inPanel"] is True),
        "escapedDialogCount": sum(1 for x in seq2
                                  if x["inDialog"] is False),
        "seq": seq2}


def print_round(R):
    print("   注入对照（预期 panelClosed）:")
    for k, exp in (("inj_text", False), ("inj_number", False),
                   ("inj_ce", False), ("inj_tabindex", True)):
        v = R.get(k) or {}
        if v.get("FAILED"):
            print("        %-14s FAILED: %s" % (k, v["FAILED"]))
            continue
        print("        %-14s 关面板=%-5s 达window冒泡=%-5s target=%-16s "
              "符合预期=%s" % (k, v["panelClosed"], v["reachedWinBubble"],
                               v.get("escTargetAtWin"), v["matchesExpectation"]))
    oc = R.get("outsideClick") or {}
    print("   外点关闭：%s 面板仍开=%s" % (oc.get("skipped") or "点了",
                                          oc.get("panelStillOpen")))
    fl = R.get("focaloss_esc") or {}
    print("   Esc 关面板后焦点=%s inDialog=%s | 之后 Tab 6 步回 dialog %s 次"
          % ((fl.get("active") or {}).get("tag"),
             (fl.get("active") or {}).get("inDialog"),
             (R.get("focaloss_tab6") or {}).get("reachedDialogCount")))
    st = R.get("shift_tab12") or {}
    print("   焦点在触发器 Shift+Tab 12 步：进面板 %s 次 | 逃出 dialog %s 次"
          % (st.get("inPanelCount"), st.get("escapedDialogCount")))


def main():
    res = {"batch": 765, "probe": "b",
           "question": "注入对照定位时长框 Esc 关不掉面板的机制、"
                       "外点关闭、Esc 关面板后焦点死路、反向 Tab 进不进面板",
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
                print_round(R)
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
        t = (R.get("state1") or {}).get("trigger") or {}
        p1 = (R.get("state1") or {}).get("panel") or {}
        print("  触发器 aria-expanded=%s aria-controls=%s aria-haspopup=%s"
              % (t.get("ariaExpanded"), t.get("ariaControls"),
                 t.get("ariaHasPopup")))
        print("  面板 tag=%s role=%s aria-label=%s id=%s"
              % (p1.get("tag"), p1.get("role"), p1.get("ariaLabel"),
                 p1.get("id")))
        print("  外点扫描 =", json.dumps(R.get("outsideScan"),
                                         ensure_ascii=False))
        print("  Tab6 落点 =", json.dumps(
            (R.get("focaloss_tab6") or {}).get("seq"),
            ensure_ascii=False)[:600])
    print("wrote %s" % OUT)


if __name__ == "__main__":
    main()
