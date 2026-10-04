#!/usr/bin/env python3
"""batch 768 探针 b：a 的**注入对照** —— 注入「关闭后把焦点 focus() 回触发器」

a 已经量到：浮层关掉后，焦点要么掉到 `body`、要么**本来就在触发器上所以
没动**。这两种读数必须分开，靠的就是本探针：

  · 注入前（= a 的读数）：phonevcam/inside、modellib/inside 焦点掉 `body`
  · 注入后：这两格若焦点回到触发器 ⟹ 证明 ①「掉到 body」是**可避免的**，
    是缺陷不是必然；②「焦点在触发器」那三格在 a 里的 `✓` 是 **no-op**
    —— 注入**不改变**它们的读数，所以那一格不是「归还做对了」，
    只是「焦点从来没离开过触发器」。

★ 注入挂在 **window 捕获**阶段、150ms 后才动作：
  - 必须捕获阶段：`DirectorPhoneVcamPanel.tsx:286-296` 在 window 捕获里
    `stopImmediatePropagation()`，任何冒泡阶段的监听都收不到它的 keydown。
  - 捕获阶段 DOM 还没变，正好记下「按 Esc 前哪个 panel 开着」；
    150ms 后（React flush 之后）再判断 panel 是否已从 DOM 消失。
  - 只在**面板确实关了、且触发器还在 DOM 里**时才 focus ⟹
    不制造「焦点逃出仍开着的浮层」的假象（export/crowd 的 inside 格
    本来就没关，属于 D3/D2，注入不该改它们的结论）。

--- 以下是原批 a 的文档字符串（逐字保留，供 provenance） ---
batch 768 探针 a：把 767 的 J9 补干净 —— 6 个 disclosure 的焦点归还契约

767 的顺序是「先点浮层外面测外点关闭、浮层还开着才测 Esc」，结果**点空白
本身就把焦点挪到了对话框根** ⟹ 「关闭时是否把焦点归还触发器」这一问
6 格全废（J9）。README 里已经承诺要重跑一版干净的。

本批**不点外点**，改成两个变体，每个变体都从**新开的一次浮层**开始：

  变体 A｜焦点在浮层**内部**（聚焦面板里第一个可聚焦控件）
    ⟹ 问的是「关闭会不会把正在聚焦的元素卸载掉，焦点掉到哪」
    （这正是 765 对导出面板量到的 D4 场景：`if (!open) return null`
      把聚焦元素整个卸载 ⟹ 掉到 `body`）

  变体 B｜焦点留在**触发器**上（打开后不碰浮层内部）
    ⟹ 问的是经典 disclosure 契约：「关掉之后焦点回不回触发器」

两个变体必须**各开一次干净的浮层**，不能串在同一条时间线上（767 的 R73）。

★ 与 767 相同的边界：只点触发器与浮层内的**非提交**控件，不点提交/连接/添加。
  虚拟相机面板的「连接」不点；导出面板的提交不点。
"""
import json
import pathlib
from playwright.sync_api import sync_playwright

BASE = "http://localhost:4317"
OUT = pathlib.Path(
    "/Users/yangjiefeng/Documents/wubuku/liblib-tv"
    "/docs/research/liblib-canvas-batch768-2026-10-01/raw/vb768b.json")
LS_KEY = "liblib-tv-director-project-v1"

DISCLOSURES = [
    {"id": "export", "name": "导出面板",
     "trigger": "[data-director-export-trigger]",
     "panel": "[data-director-export-panel]", "needs": "none"},
    {"id": "preset", "name": "预设运镜面板",
     "trigger": "[data-director-camera-preset-trigger]",
     "panel": "[data-director-camera-preset-panel]", "needs": "cameraTrack"},
    {"id": "pathmenu", "name": "创建运动轨迹菜单",
     "trigger": '[data-director-track-draw-trail="director-track-camera-main"]',
     "panel": "[data-director-motion-path-menu]", "needs": "cameraTrack"},
    {"id": "phonevcam", "name": "虚拟相机面板",
     "trigger": "[data-director-phone-vcam-trigger]",
     "panel": "[data-director-phone-vcam-panel]", "needs": "none"},
    {"id": "crowd", "name": "添加群众阵列面板",
     "trigger": "[data-director-crowd-trigger]",
     "panel": "[data-director-crowd-panel]", "needs": "none"},
    {"id": "modellib", "name": "模型库面板",
     "trigger": "[data-director-model-library-trigger]",
     "panel": "[data-director-model-library-panel]", "needs": "none"},
]

INJ_SEL = [{"trigger": d["trigger"], "panel": d["panel"]} for d in DISCLOSURES]

DESK = """()=>{const d=document.querySelector('[role="dialog"][aria-modal="true"]');
 if(!d) return {open:false};
 const a=document.activeElement;
 return {open:true, activeTag:a?a.tagName:null,
   activeAria:a?a.getAttribute('aria-label'):null,
   activeText:a?(a.textContent||'').trim().slice(0,10):null,
   isBody:a===document.body, inDialog:d===a||d.contains(a)};}"""

STATE = """(a)=>{const trig=a[0], panel=a[1];
 const d=document.querySelector('[role="dialog"][aria-modal="true"]');
 if(!d) return {open:false};
 const t=d.querySelector(trig); const p=d.querySelector(panel);
 const act=document.activeElement;
 return {deskOpen:true,
   triggerPresent:!!t, panelPresent:!!p,
   triggerAriaExpanded:t?t.getAttribute('aria-expanded'):null,
   active:{tag:act?act.tagName:null,
     aria:act?act.getAttribute('aria-label'):null,
     text:act?(act.textContent||'').trim().slice(0,10):null,
     type:act?act.getAttribute('type'):null,
     isTrigger:!!(act&&t&&act===t),
     inPanel:!!(act&&p&&p.contains(act)),
     inDialog:d===act||d.contains(act),
     isBody:act===document.body}};}"""

# 把焦点放进面板里的第 idx 个可聚焦控件（只读不点，不会触发任何动作）
FOCUS_IN = """(a)=>{const sel=a[0], idx=a[1];
 const d=document.querySelector('[role="dialog"][aria-modal="true"]');
 const p=d&&d.querySelector(sel); if(!p) return {err:'no panel'};
 const els=[...p.querySelectorAll('a[href],button,input,select,textarea,'
   +'[tabindex],[contenteditable="true"]')].filter(e=>{
   if(e.disabled) return false; const t=e.getAttribute('tabindex');
   if(t!==null && Number(t)<0) return false;
   const s=getComputedStyle(e);
   if(s.display==='none'||s.visibility==='hidden') return false;
   const r=e.getBoundingClientRect(); return r.width>0&&r.height>0;});
 if(!els.length) return {err:'no focusable', n:0};
 const e=els[Math.min(idx, els.length-1)];
 e.focus();
 const a2=document.activeElement;
 return {focused:a2===e, total:els.length, tag:a2?a2.tagName:null,
   type:a2?a2.getAttribute('type'):null,
   text:a2?(a2.textContent||'').trim().slice(0,10):null};}"""

FOCUS_TRIGGER = """(a)=>{const d=document.querySelector(
  '[role="dialog"][aria-modal="true"]');
 const t=d&&d.querySelector(a[0]); if(!t) return {err:'no trigger'};
 t.focus(); return {focused:document.activeElement===t,
   tag:t.tagName, text:(t.textContent||'').trim().slice(0,10),
   aria:t.getAttribute('aria-label')};}"""

SCAN_CLICK = """(sel)=>{const el=document.querySelector(sel);
 if(!el) return {missing:true};
 if(el.disabled) return {disabled:true};
 const r=el.getBoundingClientRect();
 for(let f=0.08; f<=0.95; f+=0.07)
   for(let g=0.08; g<=0.95; g+=0.07){
     const x=Math.round(r.x+r.width*f), y=Math.round(r.y+r.height*g);
     if(x<2||y<2||x>innerWidth-2||y>innerHeight-2) continue;
     const e=document.elementFromPoint(x,y);
     if(e&&e.closest&&e.closest(sel)===el) return {pt:[x,y]};}
 return {noHit:true};}"""

# 注入对照：在「浮层确实关掉之后」把焦点 focus() 回触发器。
# 挂在 window 捕获阶段是因为手机相机面板的 Esc 监听在捕获里
# stopImmediatePropagation，冒泡阶段收不到。
INJECT = """(sel)=>{ if(window.__injOn) return {already:1};
 window.__injOn=1; window.__inj=[];
 window.addEventListener('keydown',(e)=>{
   if(e.key!=='Escape') return;
   const open=[]; sel.forEach(s=>{ if(document.querySelector(s.panel)) open.push(s); });
   if(!open.length) return;
   setTimeout(()=>{ open.forEach(s=>{
     const p=document.querySelector(s.panel), t=document.querySelector(s.trigger);
     const rec={panelGone:!p, trigThere:!!t};
     if(!p && t){ t.focus(); rec.focused=(document.activeElement===t); }
     window.__inj.push(rec); }); },150);
 },true);
 return {installed:true, n:sel.length};}"""

READ_INJ = """()=>{const v=window.__inj||[]; window.__inj=[]; return v;}"""

CLEAR_LS = """(k)=>{const ks=[]; for(let i=0;i<localStorage.length;i++){
    const key=localStorage.key(i); if(key&&key.indexOf(k)===0){ks.push(key);}}
  ks.forEach(x=>localStorage.removeItem(x)); return {removed:ks};}"""


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


def open_desk(pg):
    s = pg.evaluate(SCAN_CLICK, "[data-open-director]")
    if not s.get("pt"):
        return {"FAILED": s}
    pg.mouse.click(s["pt"][0], s["pt"][1])
    try:
        pg.wait_for_selector('[role="dialog"][aria-modal="true"]', timeout=25000)
    except Exception:
        return {"FAILED": "点了但没 dialog"}
    pg.wait_for_timeout(2000)
    return {"opened": True}


def ensure_desk(pg):
    if pg.evaluate(DESK).get("open") is True:
        return {"alreadyOpen": True}
    return open_desk(pg)


def ensure_context(pg, d):
    ensure_desk(pg)
    if pg.evaluate(DESK).get("open") is not True:
        return {"FAILED": "导演台没开"}
    if d["needs"] == "cameraTrack":
        pg.evaluate("""()=>{const d=document.querySelector(
          '[role="dialog"][aria-modal="true"]');
         const r=d&&d.querySelector(
           '[data-director-object-id="director-camera-main"]');
         if(!r) return;
         const b=r.getBoundingClientRect();
         for(let f=0.1; f<=0.9; f+=0.08)
           for(let g=0.1; g<=0.9; g+=0.08){
             const x=Math.round(b.x+b.width*f), y=Math.round(b.y+b.height*g);
             if(x<2||y<2||x>innerWidth-2||y>innerHeight-2) continue;
             const e=document.elementFromPoint(x,y);
             if(e&&e.closest&&e.closest('[data-director-object-id='
               +'"director-camera-main"]')){
               e.closest('[data-director-object-id="director-camera-main"]')
                 .click(); return;}}}""")
        pg.wait_for_timeout(1000)
    return {"ok": True}


def open_disclosure(pg, d):
    """确保浮层是**开着**的（如果已经开着就当作失败 —— 起点必须干净）。"""
    st = pg.evaluate(STATE, [d["trigger"], d["panel"]])
    if st.get("panelPresent"):
        return {"alreadyOpen": True, "state": st}
    s = pg.evaluate(SCAN_CLICK, d["trigger"])
    if not s.get("pt"):
        return {"FAILED": "触发器点不动", "scan": s}
    pg.mouse.click(s["pt"][0], s["pt"][1])
    pg.wait_for_timeout(800)
    st2 = pg.evaluate(STATE, [d["trigger"], d["panel"]])
    if not st2.get("panelPresent"):
        return {"FAILED": "点了但浮层没出现", "state": st2}
    return {"opened": True, "state": st2}


def variant(pg, d, mode):
    """mode='inside'：焦点进浮层；mode='trigger'：焦点留触发器。

    ★ 每个变体都**从重新加载页面开始**。初版沿用同一页连着跑 12 格，
      结果上一格没关掉浮层时下一格就撞上「起点不干净」（export/crowd 的
      变体 B 因此没读数）。重载是唯一能保证起点干净的办法 ——
      「先试着关掉再继续」不行，因为「怎么关」本身就是被测的东西（R73）。
    """
    R = {"mode": mode}
    pg.goto(BASE, wait_until="domcontentloaded")
    pg.evaluate(CLEAR_LS, LS_KEY)
    pg.set_viewport_size({"width": 1440, "height": 1000})
    pg.goto(BASE, wait_until="networkidle")
    pg.wait_for_selector(".react-flow__node", timeout=25000)
    pg.wait_for_timeout(1100)
    pg.keyboard.press("Meta+0")
    pg.wait_for_timeout(500)
    settle(pg, tries=5, gap=180)
    R["fresh"] = open_desk(pg)
    ctx = ensure_context(pg, d)
    if ctx.get("FAILED"):
        R["FAILED"] = ctx["FAILED"]
        return R
    R["injSetup"] = pg.evaluate(INJECT, INJ_SEL)
    op = open_disclosure(pg, d)
    if op.get("FAILED") or op.get("alreadyOpen"):
        R["FAILED"] = op.get("FAILED") or "浮层已经是开着的，起点不干净"
        R["open"] = op
        return R
    if mode == "inside":
        f = pg.evaluate(FOCUS_IN, [d["panel"], 0])
        R["focus"] = f
        if not f.get("focused"):
            R["FAILED"] = "面板内没有可聚焦控件（或聚焦失败）"
            return R
    else:
        # ★ FOCUS_TRIGGER 的形参是 `a`、内部取 `a[0]` ⟹ 必须传**数组**。
        #   传裸字符串的话 `a[0]` 是它的第一个字符，于是
        #   `querySelector("[")` 抛 `SyntaxError: Failed to execute`。
        f = pg.evaluate(FOCUS_TRIGGER, [d["trigger"]])
        R["focus"] = f
        if not f.get("focused"):
            R["FAILED"] = "触发器没获得焦点"
            return R
    R["before"] = pg.evaluate(STATE, [d["trigger"], d["panel"]])
    pg.keyboard.press("Escape")
    pg.wait_for_timeout(750)
    R["after"] = pg.evaluate(STATE, [d["trigger"], d["panel"]])
    R["desk"] = pg.evaluate(DESK)
    pg.wait_for_timeout(250)
    R["inj"] = pg.evaluate(READ_INJ)
    R["after2"] = pg.evaluate(STATE, [d["trigger"], d["panel"]])
    return R


def run_round(pg, R):
    pg.goto(BASE, wait_until="domcontentloaded")
    R["cleared"] = pg.evaluate(CLEAR_LS, LS_KEY)
    pg.set_viewport_size({"width": 1440, "height": 1000})
    pg.goto(BASE, wait_until="networkidle")
    pg.wait_for_selector(".react-flow__node", timeout=25000)
    pg.wait_for_timeout(1200)
    pg.keyboard.press("Meta+0")
    pg.wait_for_timeout(600)
    settle(pg)
    R["load"] = open_desk(pg)
    R["rows"] = []
    for d in DISCLOSURES:
        for mode in ("inside", "trigger"):
            try:
                r = variant(pg, d, mode)
            except Exception as e:
                r = {"mode": mode,
                     "FAILED": "%s: %s" % (type(e).__name__, str(e)[:150])}
            r["id"] = d["id"]
            r["name"] = d["name"]
            R["rows"].append(r)
            # 每格都重载 ⟹ 不需要额外收尾；只如实记「这一格之后导演台还在吗」
            if pg.evaluate(DESK).get("open") is not True:
                R.setdefault("deskGoneAfter", []).append(d["id"] + "/" + mode)


def summarize(R):
    for r in R.get("rows") or []:
        if r.get("FAILED"):
            print("   %-11s %-8s FAILED: %s" % (r["id"], r["mode"],
                                               str(r["FAILED"])[:52]))
            continue
        a = r.get("after") or {}
        b = r.get("before") or {}
        act = a.get("active") or {}
        if a.get("open") is False:
            verdict = "★ 导演台被关掉了"
        elif a.get("panelPresent") is False:
            verdict = ("焦点回触发器 ✓" if act.get("isTrigger")
                       else "掉到 body" if act.get("isBody")
                       else "落在 %s" % (act.get("aria") or act.get("tag")))
        else:
            verdict = "浮层没关（焦点还在 %s）" % (act.get("tag"))
        print("   %-11s %-8s 关前焦点在浮层内=%-5s → %s"
              % (r["id"], r["mode"],
                 (b.get("active") or {}).get("inPanel"), verdict))
        inj = r.get("inj") or []
        a2 = (r.get("after2") or {}).get("active") or {}
        if inj:
            print("        注入 %s ｜ 注入后焦点=%s"
                  % (json.dumps(inj, ensure_ascii=False),
                     ("触发器" if a2.get("isTrigger")
                      else "BODY" if a2.get("isBody")
                      else str(a2.get("aria") or a2.get("tag")))))


def main():
    res = {"batch": 768, "probe": "b",
           "question": "同 a，但注入「关闭后把焦点 focus() 回触发器」"
                       "—— 把「掉到 body」与「本来就在触发器上所以没动」分开",
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
                summarize(R)
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
        print("\n=== r%d ===  重开过导演台：%s"
              % (rd, json.dumps(R.get("reopened"), ensure_ascii=False)))
    print("wrote %s" % OUT)


if __name__ == "__main__":
    main()
