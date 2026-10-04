#!/usr/bin/env python3
"""batch 766 探针 a：把「边界标记扫」换成「行为反推」，并把三类未验证控件逼出来

764 留了两条明确的不声称，本批正面处理：

① **路径锚点（`:825`）、路径变换（`:866`）、FOV（`:1579`）三类控件两轮一次都
   没渲染出来** ⟹ 763 那句「推测同样受影响」对这三类**仍然只是推测**。
   本批先把渲染条件查清（静态，见 README）再按条件把它们逼出来：
     - `MotionPathInspector` 的门是 `{selectedPath ? … : null}`（`:2749`），
       `selectedPath = selectedTrack?.motionPathId ? find(…) : undefined`
       （`:2165-2168`），而 `selectedTrack` 要求 **时间轴轨道选中 且 该轨道
       的 objectId 等于当前选中的对象**（`:2159-2164`）——
     - 路径变换 9 个数值框（3 组 × 3 轴）在 `MotionPathInspector` 里**无条件**
       渲染（`:1041/1056/1071`）⟹ 只要 `selectedPath` 有值就在；
     - 路径锚点的数值框还多一道门：`{selectedAnchor ? … : null}`（`:1134`），
       `selectedAnchor` 要 `timeline.selectedMotionPathAnchorId` 命中锚点
       （`:950-953`）⟹ **还必须点一下锚点选项**。764 就是停在这一步之前
       （它记的「+15 个控件」正好是 9 路径变换 + 6 锚点按钮/类型按钮，
       数值框一个都没渲染）。
     - FOV 的门只有 `{selected.camera ? <CameraFovField/> : null}`（`:2579-2591`）
       ⟹ 选中机位对象就该有。764 在「机位属性」档读到「可聚焦 7 / 边界 0」，
       而 FOV 滑杆**自身就带** `data-director-camera-fov`（`:1652`）且 spread
       了 gesture（`:1655`）⟹ 那个 0 本身就可疑。本批量。

② **边界检测是按 data-* 标记做的，标记挂在外层容器上的控件会漏检**（764 自己
   承认的）。本批换一种查法：**不看标记，只看行为** —— 焦点落在控件上时按
   Esc，读「事件有没有到达 window 冒泡」：
     - `reachedCapture=true` 且 `reachedBubble=false` ⟹ 有人在 React root
       那里 stopPropagation 了 ⟹ **边界候选（D1 的签名）**
     - `reachedBubble=true` 且 target 是可编辑元素 ⟹ 事件上来了，被
       `DirectorDesk.tsx:487` 的 `if (isEditable) return;` 挡在门外
     - `reachedBubble=true` 且 target 不可编辑 ⟹ 事件畅通
   然后把**行为分类**与**标记分类**交叉成一张表，**漏检/误判的格子就是 764
   那个漏洞的具体形状**。

★ 为什么要「冻结」导演台自己的 Esc 处理器：逐控件按 Esc 时，不可编辑控件会
  顺着阶梯把**整个导演台关掉**，后面几十格全变空（765 的 R63 同族）。
  所以页面一加载就往 window 上装探针（**注册在 React 的监听器之前**，因为导演台
  是后来才挂载的），并在冒泡阶段调 `stopImmediatePropagation()` 挡住导演台
  自己的处理器 —— 事件照样能到达 window（所以「到没到」照常可测），
  但导演台不会有任何反应。**这一格只测「到没到」，不测「做了什么」**；
  效果另在 unfrozen 的对照格里量。

★ 破坏性：建运动轨迹会改项目且导演台项目持久化在 localStorage（763 O1），
  所以**每轮开头先清** `liblib-tv-director-project-v1:*` 再 reload，
  否则第二轮起点就带着第一轮的路径。
"""
import json
import pathlib
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

BASE = "http://localhost:4317"
OUT = pathlib.Path(
    "/Users/yangjiefeng/Documents/wubuku/liblib-tv"
    "/docs/research/liblib-canvas-batch766-2026-10-01/raw/vb766a.json")
LS_KEY = "liblib-tv-director-project-v1"

# ★ 页面一加载就装：捕获 + 冒泡两个探针，冒泡那个带 freeze 开关
INSTALL = """()=>{
  if(window.__vb) return {installed:true, already:true};
  window.__vb={cap:0,bub:0,tgt:null,isEd:null,freeze:false};
  window.addEventListener('keydown',(e)=>{ if(e.key!=='Escape')return;
    window.__vb.cap++; }, true);
  window.addEventListener('keydown',(e)=>{ if(e.key!=='Escape')return;
    window.__vb.bub++;
    const t=e.target;
    window.__vb.tgt=t?(t.tagName+'/'+(t.getAttribute('type')||'')):null;
    window.__vb.isEd=!!(t&&t.isContentEditable) ||
      !!(t&&['INPUT','TEXTAREA','SELECT'].indexOf(t.tagName)>=0);
    if(window.__vb.freeze) e.stopImmediatePropagation(); }, false);
  return {installed:true};
}"""

READ = """()=>{const v=window.__vb;
  const out={reachedCapture:v.cap>0, reachedBubble:v.bub>0,
    targetAtWindow:v.tgt, targetIsEditable:v.isEd};
  window.__vb.cap=0; window.__vb.bub=0; window.__vb.tgt=null; window.__vb.isEd=null;
  return out;}"""

FREEZE = """(on)=>{window.__vb.freeze=!!on; return {freeze:!!on};}"""

CLEAR_LS = """(k)=>{const ks=[]; for(let i=0;i<localStorage.length;i++){
    const key=localStorage.key(i); if(key&&key.indexOf(k)===0){ks.push(key);}}
  ks.forEach(x=>localStorage.removeItem(x)); return {removed:ks};}"""

# 属性面板里「所有」可聚焦控件 —— **不按标记过滤**，这是本批的核心
SCAN_INSPECTOR = """()=>{const d=document.querySelector(
  '[role="dialog"][aria-modal="true"]');
 if(!d) return {err:'no dialog'};
 const insp=d.querySelector('aside[aria-label="属性"]') || d;
 const root=insp.querySelector('[data-director-inspector]') || insp;
 const MARK=/^data-director-/;
 const out=[]; let i=0;
 for(const e of root.querySelectorAll(
   'a[href],button,input,select,textarea,[tabindex],[contenteditable="true"]')){
   if(e.disabled) continue; const t=e.getAttribute('tabindex');
   if(t!==null && Number(t)<0) continue;
   const s=getComputedStyle(e);
   if(s.display==='none'||s.visibility==='hidden') continue;
   const r=e.getBoundingClientRect(); if(r.width<=0||r.height<=0) continue;
   // 自身标记
   const own=[]; for(const a of e.attributes)
     if(MARK.test(a.name)) own.push(a.name);
   // 祖先标记（≤4 层，够到字段容器）
   const anc=[]; let p=e.parentElement, depth=0;
   while(p && depth<4 && p!==root.parentElement){
     for(const a of p.attributes) if(MARK.test(a.name)) anc.push(a.name);
     p=p.parentElement; depth++;
   }
   out.push({i:i++, tag:e.tagName, type:e.getAttribute('type'),
     aria:e.getAttribute('aria-label'),
     text:(e.textContent||'').trim().slice(0,10),
     ownMarks:own, ancMarks:anc,
     inPathInspector:!!e.closest('[data-director-motion-path-inspector]'),
     inFovField:!!e.closest('[data-director-camera-fov-field]'),
     inFovSliderBox:!!e.closest('[data-director-camera-fov-slider]')});
 }
 return {count:out.length, controls:out};}"""

FOCUS_N = """(a)=>{const i=a[0];
 const d=document.querySelector('[role="dialog"][aria-modal="true"]');
 const insp=d&&d.querySelector('aside[aria-label="属性"]');
 const root=(insp&&insp.querySelector('[data-director-inspector]'))||insp;
 if(!root) return {err:'no inspector'};
 const els=[...root.querySelectorAll(
   'a[href],button,input,select,textarea,[tabindex],[contenteditable="true"]')]
  .filter(e=>{ if(e.disabled) return false;
    const t=e.getAttribute('tabindex');
    if(t!==null && Number(t)<0) return false;
    const s=getComputedStyle(e);
    if(s.display==='none'||s.visibility==='hidden') return false;
    const r=e.getBoundingClientRect(); return r.width>0&&r.height>0;});
 const e=els[i]; if(!e) return {err:'oob', n:els.length};
 e.focus();
 const a2=document.activeElement;
 return {focused:a2===e, tag:a2?a2.tagName:null,
   type:a2?a2.getAttribute('type'):null,
   text:a2?(a2.textContent||'').trim().slice(0,10):null};}"""

DESK = """()=>{const d=document.querySelector('[role="dialog"][aria-modal="true"]');
 if(!d) return {open:false};
 const a=document.activeElement;
 return {open:true, vw:innerWidth,
   activeTag:a?a.tagName:null,
   activeText:a?(a.textContent||'').trim().slice(0,10):null,
   activeGesture:d.getAttribute('data-director-active-gesture')};}"""

GESTURE = """()=>{const d=document.querySelector(
  '[role="dialog"][aria-modal="true"]');
 return d?d.getAttribute('data-director-active-gesture'):null;}"""

CLICK_SEL = """(sel)=>{const el=document.querySelector(sel);
 if(!el) return {missing:true};
 const r=el.getBoundingClientRect();
 for(let f=0.08; f<=0.95; f+=0.07)
   for(let g=0.08; g<=0.95; g+=0.07){
     const x=Math.round(r.x+r.width*f), y=Math.round(r.y+r.height*g);
     if(x<2||y<2||x>innerWidth-2||y>innerHeight-2) continue;
     const e=document.elementFromPoint(x,y);
     if(e&&e.closest&&e.closest(sel)) return {pt:[x,y]};}
 return {noHit:true, rect:{x:Math.round(r.x),y:Math.round(r.y),
   w:Math.round(r.width),h:Math.round(r.height)}};}"""

CLICK_IN = """(a)=>{const sel=a[0];
 const el=document.querySelector(sel); if(!el) return {missing:true};
 const r=el.getBoundingClientRect();
 for(let f=0.08; f<=0.95; f+=0.07)
   for(let g=0.08; g<=0.95; g+=0.07){
     const x=Math.round(r.x+r.width*f), y=Math.round(r.y+r.height*g);
     if(x<2||y<2||x>innerWidth-2||y>innerHeight-2) continue;
     const e=document.elementFromPoint(x,y);
     if(e&&e.closest&&e.closest(sel)){e.closest(sel).click();
       return {pt:[x,y], clicked:true};}}
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
    """清持久化 → reload → 装 window 探针 → 开导演台。"""
    pg.goto(BASE, wait_until="domcontentloaded")
    cleared = pg.evaluate(CLEAR_LS, LS_KEY)
    pg.set_viewport_size({"width": 1440, "height": 1000})
    pg.goto(BASE, wait_until="networkidle")
    installed = pg.evaluate(INSTALL)
    pg.wait_for_selector(".react-flow__node", timeout=25000)
    pg.wait_for_timeout(1200)
    pg.keyboard.press("Meta+0")
    pg.wait_for_timeout(600)
    settle(pg)
    s = pg.evaluate(CLICK_SEL, "[data-open-director]")
    if not s.get("pt"):
        return {"FAILED_open": s, "cleared": cleared, "installed": installed}
    pg.mouse.click(s["pt"][0], s["pt"][1])
    try:
        pg.wait_for_selector('[role="dialog"][aria-modal="true"]', timeout=25000)
    except Exception:
        return {"FAILED_open": "点了但没 dialog", "cleared": cleared}
    pg.wait_for_timeout(2200)
    return {"opened": True, "cleared": cleared, "installed": installed}


def click_text(pg, text, wait=800):
    """按可见文案找按钮并点它（先扫网格验命中，hit=false 不点 —— R 原则）。"""
    s = pg.evaluate("""(t)=>{
     const d=document.querySelector('[role="dialog"][aria-modal="true"]');
     if(!d) return {err:'no dialog'};
     const el=[...d.querySelectorAll('button,[role="button"]')].find(
       e=>(e.textContent||'').trim().indexOf(t)>=0 && !e.disabled);
     if(!el) return {missing:true};
     const r=el.getBoundingClientRect();
     for(let f=0.08; f<=0.95; f+=0.07)
       for(let g=0.08; g<=0.95; g+=0.07){
         const x=Math.round(r.x+r.width*f), y=Math.round(r.y+r.height*g);
         if(x<2||y<2||x>innerWidth-2||y>innerHeight-2) continue;
         const e=document.elementFromPoint(x,y);
         if(e&&e.closest&&e.closest('button,[role="button"]')===el)
           return {pt:[x,y], ariaExpanded:el.getAttribute('aria-expanded')};}
     return {noHit:true};}""", text)
    if not s.get("pt"):
        return {"FAILED": True, "scan": s, "text": text}
    pg.mouse.click(s["pt"][0], s["pt"][1])
    pg.wait_for_timeout(wait)
    return {"clicked": True, "text": text, "pt": s["pt"]}


def click_sel(pg, sel, wait=800):
    s = pg.evaluate(CLICK_SEL, sel)
    if not s.get("pt"):
        return {"FAILED": True, "scan": s, "sel": sel}
    pg.mouse.click(s["pt"][0], s["pt"][1])
    pg.wait_for_timeout(wait)
    return {"clicked": True, "sel": sel, "pt": s["pt"]}


def sweep(pg, label, expect_marks=None):
    """★ 无标记兜底扫：枚举属性面板所有可聚焦控件，逐个按 Esc 量「到没到 window」。

    冻结导演台自己的处理器，所以这一格只测传播，不测效果。
    """
    sc = pg.evaluate(SCAN_INSPECTOR)
    if sc.get("err") or not sc.get("controls"):
        return {"label": label, "FAILED": "扫不到控件", "scan": sc}
    ctrls = sc["controls"]
    rows = []
    for it in ctrls:
        if not (pg.evaluate(DESK).get("open")):
            return {"label": label, "FAILED": "扫到一半导演台没了",
                    "done": len(rows), "scan": sc}
        f = pg.evaluate(FOCUS_N, [it["i"]])
        if not f.get("focused"):
            # 焦点没上去就不能解释成「Esc 不管用」（R 原则）
            rows.append({"i": it["i"], "ctrl": it, "FAILED": "没获得焦点",
                         "focus": f})
            continue
        g_before = pg.evaluate(GESTURE)
        pg.evaluate(FREEZE, True)
        pg.keyboard.press("Escape")
        pg.wait_for_timeout(120)
        fl = pg.evaluate(READ)
        pg.evaluate(FREEZE, False)
        g_after = pg.evaluate(GESTURE)
        row = {"i": it["i"], "ctrl": it, "focus": f,
               "reachedCapture": fl["reachedCapture"],
               "reachedBubble": fl["reachedBubble"],
               "targetAtWindow": fl["targetAtWindow"],
               "targetIsEditable": fl["targetIsEditable"],
               "gestureBefore": g_before, "gestureAfter": g_after}
        # —— 行为分类（不看标记）
        if fl["reachedCapture"] and not fl["reachedBubble"]:
            row["behavior"] = "swallowed-below-window"
        elif fl["reachedBubble"] and fl["targetIsEditable"]:
            row["behavior"] = "reached-then-editable-guard"
        elif fl["reachedBubble"]:
            row["behavior"] = "reached-plain"
        else:
            row["behavior"] = "never-reached"
        # —— 标记分类（764 的查法）
        OWN_BOUNDARY = {
            "data-director-transform-field", "data-director-path-anchor-position",
            "data-director-path-anchor-handle", "data-director-path-transform-field",
            "data-director-pose-control", "data-director-camera-fov",
            "data-director-transform-axis", "data-director-path-transform-axis",
        }
        ANC_BOUNDARY = {
            "data-director-transform-field", "data-director-path-anchor-position",
            "data-director-path-anchor-handle", "data-director-path-transform-field",
            "data-director-pose-control", "data-director-camera-fov-slider",
            "data-director-camera-fov-field", "data-director-transform-axis",
            "data-director-path-transform-axis",
        }
        om = set(it["ownMarks"]); am = set(it["ancMarks"])
        row["markerOwnBoundary"] = sorted(om & OWN_BOUNDARY)
        row["markerAncBoundary"] = sorted(am & ANC_BOUNDARY)
        row["markerClass"] = ("boundary-own" if (om & OWN_BOUNDARY)
                              else "boundary-anc" if (am & ANC_BOUNDARY)
                              else "no-marker")
        rows.append(row)
    return {"label": label, "scanCount": sc["count"],
            "rows": rows, "expectMarks": expect_marks}


def unfrozen_effect(pg, label, pick):
    """对照格：**不冻结**，按一次真 Esc，看导演台/抽屉实际怎么变。"""
    if pick is None:
        return {"label": label, "skipped": "没挑到对照控件"}
    f = pg.evaluate(FOCUS_N, [pick])
    if not f.get("focused"):
        return {"label": label, "FAILED": "对照控件没获得焦点", "focus": f}
    before = pg.evaluate(DESK)
    pg.keyboard.press("Escape")
    pg.wait_for_timeout(700)
    after = pg.evaluate(DESK)
    return {"label": label, "i": pick, "focus": f,
            "beforeTag": (before.get("active") or {}).get("tag"),
            "deskOpenAfter": after.get("open") is True,
            "activeAfter": after.get("active")}


def select_object(pg, obj_id):
    return click_sel(pg, '[data-director-object-id="%s"]' % obj_id)


def guard(R, key, fn, *a, **kw):
    """单阶段异常保护：一处抛错只记下，不丢整轮。"""
    try:
        R[key] = fn(*a, **kw)
    except Exception as e:
        R[key] = {"FAILED": "%s: %s" % (type(e).__name__, str(e)[:180])}
    return R.get(key)


def run_round(pg, R):
    R["load"] = load_open(pg)
    if R["load"].get("FAILED_open"):
        R["verdict"] = "打开导演台失败"
        return
    R["desk0"] = pg.evaluate(DESK)
    if R["desk0"].get("open") is not True:
        R["verdict"] = "加载后导演台没开"
        return

    # ── 上下文 A：机位属性（FOV 应该就在这里）
    R["selCamera"] = select_object(pg, "director-camera-main")
    pg.wait_for_timeout(1200)
    R["ctxA_probe"] = pg.evaluate("""()=>{const d=document.querySelector(
      '[role="dialog"][aria-modal="true"]');
     const q=(s)=>{const e=d.querySelector(s); return e?{
       tag:e.tagName, type:e.getAttribute('type'),
       aria:e.getAttribute('aria-label'),
       text:(e.textContent||'').trim().slice(0,10)}:null;};
     const tabs=[...d.querySelectorAll('[data-director-camera-tab]')]
       .map(t=>({id:t.getAttribute('data-director-camera-tab'),
         text:(t.textContent||'').trim().slice(0,6),
         pressed:t.getAttribute('aria-pressed')}));
     return {tabs:tabs,
       fovField:!!d.querySelector('[data-director-camera-fov-field]'),
       fovSlider:!!d.querySelector('[data-director-camera-fov-slider]'),
       fovRange:q('[data-director-camera-fov]'),
       fovNumber:q('[data-director-camera-fov-number]'),
       pathTransformFields: d.querySelectorAll(
         '[data-director-path-transform-field]').length,
       pathAnchorInputs: d.querySelectorAll(
         '[data-director-path-anchor-position],'
         +'[data-director-path-anchor-handle]').length};}""")
    if not R["ctxA_probe"].get("fovRange"):
        # 属性档没有就逐个 tab 找一遍（tab 值运行时发现，不写死）
        R["ctxA_tabWalk"] = []
        for t in R["ctxA_probe"].get("tabs") or []:
            click_sel(pg, '[data-director-camera-tab="%s"]' % t["id"])
            pg.wait_for_timeout(700)
            R["ctxA_tabWalk"].append({
                "tab": t["id"],
                "fovRange": pg.evaluate("""()=>{const d=document.querySelector(
                  '[role="dialog"][aria-modal="true"]');
                 const e=d.querySelector('[data-director-camera-fov]');
                 return e?{tag:e.tagName, type:e.getAttribute('type'),
                   aria:e.getAttribute('aria-label')}:null;}""")})
    R["ctxA_sweep"] = sweep(pg, "camera-properties",
                            expect_marks=["data-director-camera-fov"])

    # ── 上下文 B：建运动轨迹 → 选中轨道 → 路径变换框
    # ★ 预设按钮在**折叠菜单**里，DOM 里根本没有（766a 首轮 `missing:true`）。
    #   入口是 `data-director-track-draw-trail`（`DirectorTimeline.tsx:1677`），
    #   它一次点击就 `selectTimelineTrack(cameraTrack.id)` + `togglePathMenu()`。
    #   找不到它再退回按文案找「创建运动轨迹」（`:1110-1125`，带 aria-expanded）。
    R["trackRows"] = pg.evaluate("""()=>[...document.querySelectorAll(
      '[role="dialog"][aria-modal="true"] [data-director-track-row]')]
      .map(r=>({id:r.getAttribute('data-director-track-row'),
        kind:r.getAttribute('data-director-track-row-kind'),
        selected:r.getAttribute('data-director-track-row-selected')}))""")
    R["drawTrailButtons"] = pg.evaluate("""()=>[...document.querySelectorAll(
      '[role="dialog"][aria-modal="true"] [data-director-track-draw-trail]')]
      .map(b=>({track:b.getAttribute('data-director-track-draw-trail'),
        aria:b.getAttribute('aria-label'),
        pressed:b.getAttribute('aria-pressed')}))""")
    R["openPathMenu"] = {"strategy": None, "result": None}
    if R["drawTrailButtons"]:
        R["openPathMenu"] = {
            "strategy": "data-director-track-draw-trail",
            "result": click_sel(
                pg, '[data-director-track-draw-trail="%s"]'
                % R["drawTrailButtons"][0]["track"], wait=900)}
    else:
        R["openPathMenu"] = {
            "strategy": "按文案找「创建运动轨迹」",
            "result": click_text(pg, "创建运动轨迹", wait=900)}
    R["presetsVisible"] = pg.evaluate("""()=>[...document.querySelectorAll(
      '[role="dialog"][aria-modal="true"] [data-director-motion-path-preset]')]
      .map(e=>({preset:e.getAttribute('data-director-motion-path-preset'),
        disabled:!!e.disabled}))""")
    R["createPath"] = click_sel(
        pg, '[data-director-motion-path-preset="line"]', wait=1600)
    R["ctxB_probe"] = pg.evaluate("""()=>{const d=document.querySelector(
      '[role="dialog"][aria-modal="true"]');
     return {motionPathInspector:!!d.querySelector(
       '[data-director-motion-path-inspector]'),
       pathTransformFields: d.querySelectorAll(
         '[data-director-path-transform-field]').length,
       pathTransformInputs: d.querySelectorAll(
         '[data-director-path-transform-axis]').length,
       pathAnchorOptions: d.querySelectorAll(
         '[data-director-anchor-option],'
         +'[data-director-path-anchor-option]').length,
       trackRows: d.querySelectorAll('[data-director-track-row]').length,
       selectedTrackRows: d.querySelectorAll(
         '[data-director-track-row-selected="true"]').length};}""")
    if not R["ctxB_probe"].get("motionPathInspector"):
        # 轨道没自动选中 ⟹ 逐个点轨道行（值运行时发现，不写死）
        R["ctxB_trackClick"] = []
        rows = pg.evaluate("""()=>[...document.querySelectorAll(
          '[role="dialog"][aria-modal="true"] [data-director-track-row]')]
          .map(r=>({id:r.getAttribute('data-director-track-row'),
            kind:r.getAttribute('data-director-track-row-kind'),
            selected:r.getAttribute('data-director-track-row-selected')}))""")
        for rr in rows or []:
            if rr.get("selected") == "true":
                continue
            c = click_sel(pg, '[data-director-track-row="%s"]' % rr["id"],
                          wait=800)
            has = pg.evaluate("""()=>{const d=document.querySelector(
              '[role="dialog"][aria-modal="true"]');
             return {insp:!!d.querySelector(
               '[data-director-motion-path-inspector]'),
               fields:d.querySelectorAll(
                 '[data-director-path-transform-field]').length};}""")
            R["ctxB_trackClick"].append({"track": rr["id"],
                                         "kind": rr.get("kind"),
                                         "click": c, "after": has,
                                         "drawTrail": pg.evaluate(
                                             """()=>[...document.querySelectorAll(
                                               '[data-director-track-draw-trail]')]
                                               .map(b=>({t:b.getAttribute(
                                                 'data-director-track-draw-trail'),
                                                 pressed:b.getAttribute(
                                                 'aria-pressed')}));""")})
            if has.get("insp"):
                break
    R["ctxB_probe2"] = pg.evaluate("""()=>{const d=document.querySelector(
      '[role="dialog"][aria-modal="true"]');
     return {motionPathInspector:!!d.querySelector(
       '[data-director-motion-path-inspector]'),
       pathTransformFields: d.querySelectorAll(
         '[data-director-path-transform-field]').length,
       pathTransformInputs: d.querySelectorAll(
         '[data-director-path-transform-axis]').length,
       pathAnchorInputs: d.querySelectorAll(
         '[data-director-path-anchor-position],'
         +'[data-director-path-anchor-handle]').length};}""")
    if R["ctxB_probe2"].get("motionPathInspector"):
        R["ctxB_sweep"] = sweep(pg, "path-transform",
                                expect_marks=["data-director-path-transform-field"])

    # ── 上下文 C：再点一个锚点 ⟹ 路径锚点数值框
    R["ctxC_anchor"] = {"clicked": None}
    opts = pg.evaluate("""()=>[...document.querySelectorAll(
      '[role="dialog"][aria-modal="true"] [data-director-path-anchor-option]')]
      .map(o=>({id:o.getAttribute('data-director-path-anchor-option'),
        text:(o.textContent||'').trim().slice(0,8),
        pressed:o.getAttribute('aria-pressed')}))""")
    R["ctxC_anchorOptions"] = opts
    for o in opts or []:
        c = click_sel(pg, '[data-director-path-anchor-option="%s"]' % o["id"],
                      wait=900)
        R["ctxC_anchor"] = {"option": o, "click": c}
        n = pg.evaluate("""()=>{const d=document.querySelector(
          '[role="dialog"][aria-modal="true"]');
         return d.querySelectorAll('[data-director-path-anchor-position],'
           +'[data-director-path-anchor-handle]').length;}""")
        R["ctxC_anchor"]["anchorInputsAfter"] = n
        if n > 0:
            break
    R["ctxC_sweep"] = sweep(pg, "path-anchor",
                            expect_marks=["data-director-path-anchor-position",
                                          "data-director-path-anchor-handle"])
    R["ctxC_anchorType"] = pg.evaluate("""()=>{const d=document.querySelector(
      '[role="dialog"][aria-modal="true"]');
     return [...d.querySelectorAll('[data-director-path-anchor-type-option]')]
       .map(b=>({type:b.getAttribute('data-director-path-anchor-type-option'),
         pressed:b.getAttribute('aria-pressed')}));
     }""")

    # ── 交叉表：行为分类 × 标记分类
    for key in ("ctxA_sweep", "ctxB_sweep", "ctxC_sweep"):
        s = R.get(key) or {}
        rows = s.get("rows") or []
        if not rows:
            R[key + "_xtab"] = {"FAILED": "没有行"}
            continue
        xt = {}
        for r in rows:
            if r.get("FAILED"):
                continue
            k = "%s | %s" % (r.get("markerClass"), r.get("behavior"))
            xt[k] = xt.get(k, 0) + 1
        R[key + "_xtab"] = {"cells": len(rows), "table": xt,
                            "failedRows": [r["i"] for r in rows
                                           if r.get("FAILED")]}


def print_round(R):
    a = R.get("ctxA_probe") or {}
    print("   A 机位属性：tabs=%s FOV范围=%s FOV数值=%s 路径变换字段=%s 锚点输入=%s"
          % ([t.get("id") for t in a.get("tabs") or []],
             bool(a.get("fovRange")), bool(a.get("fovNumber")),
             a.get("pathTransformFields"), a.get("pathAnchorInputs")))
    b = R.get("ctxB_probe2") or {}
    print("   B 路径变换：MotionPathInspector=%s 字段=%s 数值框=%s 锚点输入=%s"
          % (b.get("motionPathInspector"), b.get("pathTransformFields"),
             b.get("pathTransformInputs"), b.get("pathAnchorInputs")))
    c = R.get("ctxC_anchor") or {}
    print("   C 路径锚点：点=%s 之后锚点输入=%s"
          % (json.dumps(c.get("option"), ensure_ascii=False),
             c.get("anchorInputsAfter")))
    for key in ("ctxA_sweep", "ctxB_sweep", "ctxC_sweep"):
        s = R.get(key) or {}
        xt = R.get(key + "_xtab") or {}
        if s.get("FAILED") or not s.get("rows"):
            print("   %-14s FAILED: %s" % (key, s.get("FAILED")))
            continue
        beh = {}
        mk = {}
        for r in s["rows"]:
            if r.get("FAILED"):
                continue
            beh[r["behavior"]] = beh.get(r["behavior"], 0) + 1
            mk[r["markerClass"]] = mk.get(r["markerClass"], 0) + 1
        print("   %-14s %d 个控件 | 行为 %s | 标记 %s"
              % (key, s["scanCount"], json.dumps(beh, ensure_ascii=False),
                 json.dumps(mk, ensure_ascii=False)))


def main():
    res = {"batch": 766, "probe": "a",
           "question": "行为反推取代标记扫来识别手势边界控件；"
                       "把路径锚点/路径变换/FOV 三类未验证控件逼出来",
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
        for key in ("ctxA_sweep", "ctxB_sweep", "ctxC_sweep"):
            xt = R.get(key + "_xtab") or {}
            print("  %s 交叉表：%s" % (key, json.dumps(xt.get("table"),
                                                     ensure_ascii=False)))
    print("wrote %s" % OUT)


if __name__ == "__main__":
    main()
