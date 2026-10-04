#!/usr/bin/env python3
"""batch 764 探针 a：D1（手势边界吞 Esc）的真实影响面

763 已经把因果链钉死：`useDirectorGestureBoundary.ts:92-98` 在 Escape 上
preventDefault + stopPropagation ⟹ 事件永远到不了 `DirectorDesk.tsx:475`
挂在 window 冒泡上的 Esc 阶梯。属性面板当前渲染态里 9 个
`input[type=number][data-director-transform-field]` 关不掉移动端抽屉（两轮一致）。

763 留的最大一条「不声称」是：**另外 8 个同一边界 hook 的控件当时不在渲染态，
只写了「推测同样受影响 —— 推测不是读数」**。本探针把它变成读数。

同一个 hook 的 5 处调用（`grep useDirectorGestureBoundary({`）：
  :117 TransformField      → `[data-director-transform-field/-axis]`  input[type=number]
  :807 PathAnchor         → `[data-director-path-anchor-position]`、`[-handle/-axis]`
  :866 PathTransform      → `[data-director-path-transform-field/-axis]`
  :1331 PoseControl       → `[data-director-pose-control]`             input[type=range]
  :1579 CameraFov         → `[data-director-camera-fov-slider]`        input[type=range]

★ 特别要验的是**滑杆**（姿势/FOV 是 type=range，不是 number）。
  763 的结论「全是 type=number」只覆盖当时那 9 个；如果 range 也吞，
  影响面比 763 记的更宽。

判决工具沿用 763e 的三点埋点：window 捕获 / window 冒泡 + document 冒泡，
`reachedWinBubble=false` 即「事件在 window 之下被消费」。
每个上下文还扫 1 个**非边界**控件当阴性对照，证明同一上下文里 Esc 本来是通的。

上下文按 tab 逐个走（tab 取值**运行时发现**，不写死）：
默认 / 每个 `[data-director-camera-tab]` / 每个 `[data-director-character-tab]` /
能建出运动路径时再加路径上下文（时间轴 `[data-director-motion-path-preset]`）。
"""
import json
import pathlib
from playwright.sync_api import sync_playwright

BASE = "http://localhost:4317"
OUT = pathlib.Path(
    "/Users/yangjiefeng/Documents/wubuku/liblib-tv"
    "/docs/research/liblib-canvas-batch764-2026-10-01/raw/vb764a.json")

BOUNDARY_SEL = ",".join([
    "[data-director-transform-field]",
    "[data-director-path-anchor-position]",
    "[data-director-path-anchor-handle]",
    "[data-director-path-transform-field]",
    "[data-director-pose-control]",
    "[data-director-camera-fov-slider]",
])

ARM = """()=>{ if(window.__armed) return {armed:true};
  window.__esc=[];
  window.addEventListener('keydown', e=>{
    if(e.key!=='Escape') return;
    const r={stage:'winCapture', dp:e.defaultPrevented,
      targetTag:e.target&&e.target.tagName,
      targetType:e.target&&e.target.getAttribute
        ?e.target.getAttribute('type'):null};
    setTimeout(()=>{ r.dpFinal=e.defaultPrevented;
      window.__esc.push(r); },0);
  }, true);
  window.addEventListener('keydown', e=>{
    if(e.key!=='Escape') return;
    const r={stage:'winBubble', dp:e.defaultPrevented};
    setTimeout(()=>{ r.dpFinalWin=e.defaultPrevented;
      window.__esc.push(r); },0);
  }, false);
  window.__armed=true; return {armed:true};}"""

# ★ 读标志必须在 TAKE **之前**：TAKE 会把两个标志清成 false。
#   初版顺序反了，27+3 个控件全被算成「吞了 Esc」。
PEEK = """()=>({reachedWinCapture:!!window.__reachedWinCapture,
  reachedWinBubble:!!window.__reachedWinBubble,
  armed:!!window.__once})"""
TAKE = """()=>{const l=window.__esc||[]; window.__esc=[];
  window.__reachedWinBubble=false; window.__reachedWinCapture=false;
  return l;}"""

DESK = """()=>{const d=document.querySelector('[role="dialog"][aria-modal="true"]');
 if(!d) return {open:false};
 const insp=d.querySelector('aside[aria-label="属性"]');
 const tree=d.querySelector('aside[aria-label="场景对象"]');
 const p=(el)=>{if(!el) return null; const r=el.getBoundingClientRect();
   return {state:el.getAttribute('data-director-mobile-panel-state'),
     focusScope:el.getAttribute('data-director-focus-scope'),
     inert:!!el.inert, x:Math.round(r.x)};};
 return {open:true, tree:p(tree), inspector:p(insp),
   historyPast:d.getAttribute('data-director-history-past'),
   historyFuture:d.getAttribute('data-director-history-future'),
   lastCommand:d.getAttribute('data-director-last-command')||'',
   activeGesture:d.getAttribute('data-director-active-gesture')||'',
   kind:d.getAttribute('data-director-inspector-kind')||null};}"""

# 属性面板里所有可聚焦控件（带序号），并标出哪些带边界标记
LIST = """(a)=>{const bsel=a[0];
 const d=document.querySelector('[role="dialog"][aria-modal="true"]');
 if(!d) return {err:'no dialog'};
 const p=d.querySelector('aside[aria-label="属性"]');
 if(!p) return {err:'no panel'};
 const items=[]; let i=0;
 for(const e of p.querySelectorAll(
     'a[href],button,input,select,textarea,[tabindex]')){
   if(e.disabled) continue; const t=e.getAttribute('tabindex');
   if(t!==null && Number(t)<0) continue;
   const s=getComputedStyle(e);
   if(s.display==='none'||s.visibility==='hidden') continue;
   const r=e.getBoundingClientRect();
   if(r.width<=0||r.height<=0) continue;
   const mark=[];
   for(const m of bsel.split(',')){
     if(!m) continue;
     try{ if(e.matches(m)) mark.push(m); }catch(err){ mark.push('BAD:'+m); }}
   items.push({i:i++, tag:e.tagName, type:e.getAttribute('type'),
     boundary:mark.length>0, marks:mark,
     tf:e.getAttribute('data-director-transform-field'),
     ta:e.getAttribute('data-director-transform-axis'),
     pap:e.getAttribute('data-director-path-anchor-position'),
     pah:e.getAttribute('data-director-path-anchor-handle'),
     pax:e.getAttribute('data-director-path-anchor-handle-axis'),
     ptf:e.getAttribute('data-director-path-transform-field'),
     pta:e.getAttribute('data-director-path-transform-axis'),
     pose:e.getAttribute('data-director-pose-control'),
     fov:e.getAttribute('data-director-camera-fov-slider'),
     aria:e.getAttribute('aria-label'),
     text:(e.textContent||'').trim().slice(0,12),
     x:Math.round(r.x), y:Math.round(r.y),
     w:Math.round(r.width), h:Math.round(r.height)});}
 return {count:items.length, items:items,
   boundaryCount:items.filter(x=>x.boundary).length,
   boundaryTypes:sorted_set(items.filter(x=>x.boundary).map(x=>String(x.type)))};}

function sorted_set(a){return Array.from(new Set(a)).sort();}"""

FOCUS_N = """(a)=>{const idx=a[0];
 const d=document.querySelector('[role="dialog"][aria-modal="true"]');
 const p=d&&d.querySelector('aside[aria-label="属性"]');
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
   type:e.getAttribute('type')};}"""

TABS = """(attr)=>{const d=document.querySelector(
  '[role="dialog"][aria-modal="true"]');
 if(!d) return [];
 return [...d.querySelectorAll('['+attr+']')].map(e=>({
   value:e.getAttribute(attr),
   pressed:e.getAttribute('aria-pressed'),
   text:(e.textContent||'').trim().slice(0,8)}));}"""

PATH_MENU = """()=>{const d=document.querySelector(
  '[role="dialog"][aria-modal="true"]');
 if(!d) return {err:'no dialog'};
 const presets=[...d.querySelectorAll('[data-director-motion-path-preset]')]
   .map(e=>({preset:e.getAttribute('data-director-motion-path-preset'),
     disabled:!!e.disabled,
     x:Math.round(e.getBoundingClientRect().x),
     y:Math.round(e.getBoundingClientRect().y),
     w:Math.round(e.getBoundingClientRect().width),
     h:Math.round(e.getBoundingClientRect().height)}));
 const triggers=[...d.querySelectorAll('button')].filter(e=>{
   const a=Array.from(e.attributes||[]).map(x=>x.name+'='+x.value).join(' ');
   return /path|轨迹/i.test(a) || /轨迹/.test(e.textContent||'');
 }).map(e=>({data:Array.from(e.attributes||[]).filter(x=>
     x.name.startsWith('data-')).map(x=>x.name+'='+x.value).join(','),
   aria:e.getAttribute('aria-label'),
   text:(e.textContent||'').trim().slice(0,10),
   x:Math.round(e.getBoundingClientRect().x),
   y:Math.round(e.getBoundingClientRect().y),
   w:Math.round(e.getBoundingClientRect().width),
   h:Math.round(e.getBoundingClientRect().height),
   visible:getComputedStyle(e).display!=='none'}));
 return {presets:presets, triggers:triggers};}"""

SCAN_CLICK = """(sel)=>{const el=document.querySelector(sel);
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

SCAN_CLICK_XY = """(a)=>{const x=a[0],y=a[1];
 const e=document.elementFromPoint(x,y);
 return {tag:e?e.tagName:null};}"""


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


def click_at(pg, x, y):
    hit = pg.evaluate(SCAN_CLICK_XY, [x, y])
    pg.mouse.click(x, y)
    return hit


def esc_once(pg):
    pg.evaluate("""()=>{window.__reachedWinBubble=false;
      window.__reachedWinCapture=false;
      if(!window.__once){window.__once=true;
        window.addEventListener('keydown',e=>{ if(e.key==='Escape')
          window.__reachedWinCapture=true; },true);
        window.addEventListener('keydown',e=>{ if(e.key==='Escape')
          window.__reachedWinBubble=true; },false);} }""")
    pg.keyboard.press("Escape")
    pg.wait_for_timeout(400)
    peek = pg.evaluate(PEEK)
    log = {"events": pg.evaluate(TAKE)}      # TAKE 返回的是列表
    st = pg.evaluate(DESK)
    insp = st.get("inspector") or {}
    log["reachedWinCapture"] = peek["reachedWinCapture"]
    log["reachedWinBubble"] = peek["reachedWinBubble"]
    log["listenersArmed"] = peek["armed"]
    log["inspectorState"] = insp.get("state")
    log["deskOpen"] = st.get("open")
    log["drawerClosed"] = (st.get("open") is True
                           and insp.get("state") != "open")
    log["workspaceClosed"] = (st.get("open") is False)
    return log


def close_other_drawer(pg, keep):
    """★ 两个移动端抽屉互斥，而且**开着的那一个会盖住另一个的触发按钮**：
       树 aside 占 x=0..220 / y=88..，属性抽屉触发按钮 rect 在 (48,100,32,32)，
       `elementFromPoint` 命中的是 aside ⟹ noHit。
       所以开任一抽屉之前，先把另一个关掉（Esc 关移动抽屉，
       见 DirectorDesk.tsx:481-485）。"""
    st = pg.evaluate(DESK)
    other = "inspector" if keep == "tree" else "tree"
    if (st.get(other) or {}).get("state") == "open":
        pg.keyboard.press("Escape")
        pg.wait_for_timeout(700)
        st2 = pg.evaluate(DESK)
        return {"closedOther": other, "stillOpen":
                (st2.get(other) or {}).get("state") == "open"}
    return {"nothingToClose": other}


def open_tree(pg):
    """★ 对象行在**树抽屉**里。树抽屉关着时 aside 在 x=-220，行坐标全在视口外
       （实测 x=-212），点不到 —— 必须先开树抽屉。"""
    pre = close_other_drawer(pg, "tree")
    st = pg.evaluate(DESK)
    if (st.get("tree") or {}).get("state") == "open":
        return {"alreadyOpen": True, "pre": pre}
    s = pg.evaluate(SCAN_CLICK, 'button[aria-label="打开场景对象"]')
    if not s.get("pt"):
        return {"FAILED": s}
    pg.mouse.click(s["pt"][0], s["pt"][1])
    pg.wait_for_timeout(800)
    return {"clicked": True, "desk": pg.evaluate(DESK)}


def open_drawer(pg):
    st = pg.evaluate(DESK)
    if (st.get("inspector") or {}).get("state") == "open":
        return {"alreadyOpen": True}
    pre = close_other_drawer(pg, "inspector")
    st = pg.evaluate(DESK)
    if (st.get("inspector") or {}).get("state") == "open":
        return {"alreadyOpen": True, "pre": pre}
    s = pg.evaluate(SCAN_CLICK, 'button[aria-label="打开属性面板"]')
    if not s.get("pt"):
        return {"FAILED": s, "pre": pre,
                "desk": pg.evaluate(DESK)}
    pg.mouse.click(s["pt"][0], s["pt"][1])
    pg.wait_for_timeout(800)
    return {"clicked": True, "pre": pre}


def sweep(pg, label, max_boundary=None, need_control=True):
    """扫当前上下文：全部边界控件 + 1 个非边界控件（阴性对照）。"""
    lst = pg.evaluate(LIST, [BOUNDARY_SEL])
    if "items" not in lst:
        return {"FAILED_list": lst, "label": label}
    bset = [x for x in lst["items"] if x["boundary"]]
    nset = [x for x in lst["items"] if not x["boundary"]]
    if max_boundary:
        bset = bset[:max_boundary]
    picks = list(bset) + (nset[:1] if need_control and nset else [])
    rows = []
    for it in picks:
        st0 = pg.evaluate(DESK)
        if st0.get("open") is False:
            rows.append({"i": it["i"], "item": it,
                         "skipped": "导演台已关"})
            break
        if (st0.get("inspector") or {}).get("state") != "open":
            op = open_drawer(pg)
            if "FAILED" in op:
                rows.append({"i": it["i"], "item": it,
                             "skipped": "重开抽屉失败", "open": op})
                break
        f = pg.evaluate(FOCUS_N, [it["i"]])
        e = esc_once(pg)
        rows.append({"i": it["i"], "item": it, "focus": f, "esc": e,
                     "swallowed": (e.get("reachedWinBubble") is False),
                     "drawerClosed": e.get("drawerClosed")})
    st0 = pg.evaluate(DESK)
    return {"label": label, "inspectorKind": st0.get("kind"),
            "focusScope": (st0.get("inspector") or {}).get("focusScope"),
            "totalFocusable": lst["count"],
            "boundaryCount": lst["boundaryCount"],
            "boundaryTypes": lst["boundaryTypes"],
            "sweptBoundary": len(bset),
            "sweptNonBoundary": 1 if need_control and nset else 0,
            "swallowedIdx": [r["i"] for r in rows if r.get("swallowed")],
            "boundarySwallowed": [r["i"] for r in rows
                                  if r.get("swallowed") and r["item"]["boundary"]],
            "nonBoundarySwallowed": [r["i"] for r in rows
                                     if r.get("swallowed")
                                     and not r["item"]["boundary"]],
            "rows": rows}


OBJECTS = """()=>{const d=document.querySelector(
  '[role="dialog"][aria-modal="true"]');
 const t=d&&d.querySelector('aside[aria-label="场景对象"]');
 if(!t) return {err:'no tree'};
 const rows=[];
 for(const e of t.querySelectorAll('[data-director-object-id]')){
   const r=e.getBoundingClientRect();
   if(r.width<=0||r.height<=0) continue;
   rows.push({id:e.getAttribute('data-director-object-id'),
     kind:e.getAttribute('data-director-object-kind'),
     selected:e.getAttribute('data-director-object-selected'),
     x:Math.round(r.x), y:Math.round(r.y),
     w:Math.round(r.width), h:Math.round(r.height)});}
 return rows;}"""


def select_object(pg, kind):
    """在树里点第一个该 kind 的对象行（树抽屉必须已打开，行才在屏内可点）。"""
    ot = open_tree(pg)
    objs = pg.evaluate(OBJECTS)
    if not isinstance(objs, list):
        return {"err": objs, "openTree": ot}
    hit = [o for o in objs if o["kind"] == kind]
    if not hit:
        return {"err": "没有 %s 对象" % kind, "kinds":
                sorted({o["kind"] for o in objs}), "openTree": ot}
    o = hit[0]
    x, y = o["x"] + o["w"] // 2, o["y"] + o["h"] // 2
    if x < 2 or x > 798 or y < 2 or y > 998:
        return {"err": "对象行在视口外（树抽屉没开？）", "target": o,
                "openTree": ot}
    tag = pg.evaluate(SCAN_CLICK_XY, [x, y])
    pg.mouse.click(x, y)
    pg.wait_for_timeout(900)
    return {"picked": o, "hitTag": tag, "openTree": ot,
            "selectedAfter": [q["id"] for q in (pg.evaluate(OBJECTS) or [])
                              if q.get("selected") == "true"]}


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
    pg.evaluate(ARM)
    return {"opened": True}


def visit_tab(pg, sel, value):
    q = '[%s="%s"]' % (sel[1:-1], value)      # sel 形如 [data-...-tab]
    s = pg.evaluate(SCAN_CLICK, q)
    if not s.get("pt"):
        return {"FAILED": s, "q": q}
    pg.mouse.click(s["pt"][0], s["pt"][1])
    pg.wait_for_timeout(800)
    tabs = pg.evaluate(TABS, sel[1:-1])
    pressed = [t for t in tabs if t.get("value") == value]
    return {"clicked": s, "pressed": bool(pressed and
                                           pressed[0].get("pressed") == "true"),
            "pressedAttr": (pressed[0].get("pressed") if pressed else None)}


def run_round(pg, R):
    op = load_open(pg)
    R["open"] = op
    if op.get("FAILED_open"):
        return
    R["deskStart"] = pg.evaluate(DESK)
    R["objectsSeed"] = pg.evaluate(OBJECTS)
    contexts = []

    def sweep_ctx(label):
        # ★ 抽屉关着时 tab 按钮在视口外（实测 x=817 > 800），点不到。
        #   所以顺序固定为：开抽屉 → 点 tab → 再扫。
        o = open_drawer(pg)
        sc = sweep(pg, label)
        sc["drawerOpen"] = o
        contexts.append(sc)
        return sc

    # ① 默认上下文（树里的默认选中）
    sweep_ctx("default")

    # ② 角色 tab（发现到的取值逐个走）
    for sel, tagname in (("[data-director-character-tab]", "character"),):
        open_drawer(pg)
        tabs = pg.evaluate(TABS, sel[1:-1])
        R["tabs_%s" % tagname] = tabs
        for t in tabs:
            v = t.get("value")
            if not v:
                continue
            o = open_drawer(pg)
            res = visit_tab(pg, sel, v)
            sc = sweep_ctx("%s:%s" % (tagname, v))
            sc["tabVisit"] = res

    # ③ 切到机位再走机位 tab（相机 tab 只在选中机位时渲染）
    sel_cam = select_object(pg, "camera")
    R["selectCamera"] = sel_cam
    if "err" not in sel_cam:
        open_drawer(pg)
        tabs = pg.evaluate(TABS, "data-director-camera-tab")
        R["tabs_camera"] = tabs
        for t in tabs:
            v = t.get("value")
            if not v:
                continue
            open_drawer(pg)
            res = visit_tab(pg, "[data-director-camera-tab]", v)
            sc = sweep_ctx("camera:%s" % v)
            sc["tabVisit"] = res
        # ④ 建一条运动路径，再走一遍机位 tab（路径锚点/路径变换只在这里渲染）
        pm = pg.evaluate(PATH_MENU)
        if not pm.get("presets"):
            trig = pg.evaluate("""()=>{const d=document.querySelector(
              '[role="dialog"][aria-modal="true"]');
             const e=d&&d.querySelector('[data-director-create-motion-path]');
             if(!e) return null; const r=e.getBoundingClientRect();
             return {x:Math.round(r.x),y:Math.round(r.y),
               w:Math.round(r.width),h:Math.round(r.height),
               text:(e.textContent||'').trim().slice(0,10)};}""")
            R["pathTrigger"] = trig
            if trig and trig["w"] > 0:
                # 这个按钮在时间轴上，抽屉关着时被 inert/移出视口，先开抽屉
                open_drawer(pg)
                click_at(pg, trig["x"] + trig["w"] // 2,
                         trig["y"] + trig["h"] // 2)
                pg.wait_for_timeout(700)
                pm = pg.evaluate(PATH_MENU)
        if pm.get("presets"):
            pr = pm["presets"][0]
            hit = click_at(pg, pr["x"] + pr["w"] // 2, pr["y"] + pr["h"] // 2)
            pg.wait_for_timeout(1200)
            R["pathCreated"] = {"preset": pr.get("preset"), "hit": hit,
                                "lastCommand":
                                    pg.evaluate(DESK).get("lastCommand")}
            for t in R.get("tabs_camera") or []:
                v = t.get("value")
                if not v:
                    continue
                open_drawer(pg)
                visit_tab(pg, "[data-director-camera-tab]", v)
                sc = sweep_ctx("path+camera:%s" % v)
                sc["afterPathCreated"] = True
        else:
            R["pathNotReachable"] = (
                "时间轴里找不到 [data-director-motion-path-preset]；"
                "触发器=%s" % json.dumps(R.get("pathTrigger"),
                                         ensure_ascii=False))
    else:
        R["cameraNotSelectable"] = sel_cam

    R["contexts"] = contexts
    tot_b = sum(c.get("boundaryCount") or 0 for c in contexts)
    sw_b = sum(len(c.get("boundarySwallowed") or []) for c in contexts)
    sw_n = sum(len(c.get("nonBoundarySwallowed") or []) for c in contexts)
    R["summary"] = {
        "contexts": len(contexts),
        "boundaryControlsSeen": tot_b,
        "boundarySwallowed": sw_b,
        "boundaryNotSwallowed": tot_b - sw_b,
        "nonBoundaryControlsTested": sum(c.get("sweptNonBoundary") or 0
                                         for c in contexts),
        "nonBoundarySwallowed": sw_n,
        "boundaryTypesSeen": sorted({str(t) for c in contexts
                                     for t in (c.get("boundaryTypes") or [])}),
        "pathReachable": bool(R.get("pathCreated")),
    }
    print("   上下文 %s | 边界 %s（吞 %s / 未吞 %s）| 非边界对照 %s（吞 %s）| 路径可达=%s"
          % (R["summary"]["contexts"], tot_b, sw_b, tot_b - sw_b,
             R["summary"]["nonBoundaryControlsTested"], sw_n,
             R["summary"]["pathReachable"]))


def main():
    res = {"batch": 764, "probe": "a",
           "question": "D1（手势边界吞 Esc）的真实影响面有多大？",
           "boundarySelector": BOUNDARY_SEL, "rounds": []}
    with sync_playwright() as p:
        br = p.chromium.launch()
        pg = br.new_page(viewport={"width": 800, "height": 1000})
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
    a, b = res["rounds"]
    print("\n汇总 r1:", json.dumps(a.get("summary"), ensure_ascii=False))
    print("汇总 r2:", json.dumps(b.get("summary"), ensure_ascii=False))
    for rd, R in enumerate(res["rounds"], 1):
        for c in R.get("contexts") or []:
            if "rows" not in c:
                print("  r%d %-22s FAILED %s" % (rd, c.get("label"),
                                                 json.dumps(c, ensure_ascii=False)[:110]))
                continue
            print("  r%d %-22s 可聚焦 %-3s 边界 %-3s(%s) 吞Esc: 边界 %s / 非边界 %s"
                  % (rd, c.get("label"), c.get("totalFocusable"),
                     c.get("boundaryCount"),
                     ",".join(str(t) for t in c.get("boundaryTypes") or []),
                     c.get("boundarySwallowed"),
                     c.get("nonBoundarySwallowed")))
    print("路径:", json.dumps(a.get("pathMenu"), ensure_ascii=False)[:200])
    print("wrote %s" % OUT)


if __name__ == "__main__":
    main()
