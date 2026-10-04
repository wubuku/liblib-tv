#!/usr/bin/env python3
"""batch 770 探针 a：6 个 disclosure 浮层里的 **Tab 围栏**

765 只量过**导出面板**与**对话框级**的焦点围栏；767 / 768 / 769 **连续三批**
都把「6 个浮层里的 Tab 围栏」列进不声称。本批补掉它。

先看机制（静态可查）：`useDirectorFocusContainment.ts:149-172` 在对话框 root 上
监听 Tab，**手算**一个 Tab 数组：

    const focusable = getDirectorFocusableElements(root);   // root = 整个对话框
    const nextIndex = shiftKey ? (index<=0 ? len-1 : index-1)
                              : (index<0 || index===len-1 ? 0 : index+1);
    event.preventDefault(); focusable[nextIndex]?.focus();

也就是说这条围栏的边界是**对话框**，不是浮层 —— 浮层的控件只是这条数组里的
一段。于是有一个可以量的预测：**浮层开着时 Tab 会从浮层里走出去**，
走到对话框的别处（甚至环绕到数组首尾），而不是在浮层内环绕。

本批只做一件事：**按 Tab / Shift+Tab，逐步记录焦点落在哪**。

  起点：浮层里第一个**非输入框**控件（沿用 769 的协议 v2 落点，可比）
  步数：12 步（面板 2–15 个可聚焦控件，12 步足够走到段末并看出环绕）

每一步都读三件事：**还在浮层内吗 / 还在对话框内吗 / 是哪个元素**。
另外顺带读「对话框级可聚焦控件总数」与「当前焦点在对话框数组里的下标」——
直接检验「浮层控件是不是这条数组的一段」。

★ 边界不变：只点 6 个 disclosure 触发器，不点提交/连接/添加。
★ 每格都从**重新加载页面**开始（768 的 R73）。
★ 769 已经证明**焦点类别会改变结论**（D3 早退），所以起点固定用非输入框控件。

--- 以下是 batch 769 探针 a 的文档字符串（逐字保留，供 provenance） ---
batch 769 探针 a：**协议 v2** —— 把焦点放在浮层里**非输入框**的控件上重测

768 把 6 个 disclosure 的焦点归还契约测了一遍，结论是 **0/6 实现了归还**，
但有 **2 个浮层根本没测到**（导出面板、添加群众阵列），原因写在自己的 J10 里：

    协议是「把焦点放进浮层的**第一个**可聚焦控件」，而这两个浮层的第一个
    可聚焦控件是 `INPUT[type=number]` ⟹ `DirectorDesk.tsx:487` 的
    `isEditable` 早退先把 Esc 吞掉、**浮层压根没关** ⟹ 焦点还在原地，
    焦点去向无从观察。注入也救不了（注入只在面板真关时才动手）。

本批把**探针目标元素**换掉：同一批浮层、同一套读数，只把「焦点放哪」这一个
变量改成**该浮层里第一个非输入框的可聚焦控件**：

  臂 A｜`editable`     —— 第一个**输入框**控件（768 落点所在的类别）
  臂 B｜`noneditable`  —— 第一个**非**输入框控件（本批新协议）

臂 A 顺带当**768 的可复现性对照**；臂 B 才是新数据，它要回答三件事：

  ① 导出面板在焦点离开输入框之后，Esc 关掉面板时焦点去哪
     —— 这是对 765 的 D4 的**独立重测**（同一缺陷、另一个协议）。
  ② 添加群众阵列在焦点离开输入框之后，Esc 会发生什么
     —— 768 只**推理**过「群众阵列此刻没丢工作区，靠的正是 `isEditable`
     早退把 Esc 吞了」；臂 B 把这句话从**推理变成读数**。
  ③ 其余 4 个浮层的结论**会不会因为换了焦点目标而变**
     —— 两臂的落点若本就是同一个元素，读数就该完全一样。

★ 与 768 相同的边界：只点触发器与浮层内的**非提交**控件，不点提交/连接/添加。
  虚拟相机面板的「连接」不点；导出面板的提交不点。
★ 每格都从**重新加载页面**开始（768 的 R73）。

--- 以下是 batch 768 探针 a 的文档字符串（逐字保留，供 provenance） ---
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
    "/docs/research/liblib-canvas-batch770-2026-10-01/raw/vb770a.json")
LS_KEY = "liblib-tv-director-project-v1"
STEPS = 12          # 面板 2–15 个可聚焦控件，12 步足够走到段末并看出环绕

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

# 每按一次 Tab / Shift+Tab 之后读一次：焦点在哪、还在不在浮层/对话框内
STEP = """(a)=>{const trig=a[0], panel=a[1];
 const d=document.querySelector('[role="dialog"][aria-modal="true"]');
 if(!d) return {err:'no dialog'};
 const t=d.querySelector(trig), p=d&&d.querySelector(panel);
 const act=document.activeElement;
 const foc=(root)=>[...root.querySelectorAll(
   'a[href],button,input,select,textarea,[tabindex],'
   +'[contenteditable="true"]')].filter(e=>{
   if(e.disabled) return false; const ti=e.getAttribute('tabindex');
   if(ti!==null && Number(ti)<0) return false;
   const s=getComputedStyle(e);
   if(s.display==='none'||s.visibility==='hidden') return false;
   const r=e.getBoundingClientRect(); return r.width>0&&r.height>0;});
 const dfoc=foc(d);
 const pfoc=p?foc(p):[];
 return {inPanel:!!(p&&act&&p.contains(act)),
   inDialog:!!(act&&(d===act||d.contains(act))),
   isTrigger:!!(t&&act===t), isBody:act===document.body,
   tag:act?act.tagName:null, type:act?act.getAttribute('type'):null,
   aria:act?act.getAttribute('aria-label'):null,
   text:act?(act.textContent||'').trim().slice(0,10):null,
   dialogFocusables:dfoc.length,
   panelFocusables:pfoc.length,
   idxInDialog:act?dfoc.indexOf(act):-1,
   idxInPanel:act&&p?pfoc.indexOf(act):-1};}"""

# ★ 本批的核心：把焦点放进浮层里**第一个指定类别**的可聚焦控件。
#   wantEditable=true  → 第一个 INPUT/SELECT/TEXTAREA/contenteditable
#   wantEditable=false → 第一个**非**上述类别的可聚焦控件
#   两类都没有时报 err 并如实报出各类计数 —— 不许悄悄退化成「取第一个」。
FOCUS_BY_KIND = """(a)=>{const sel=a[0], wantEditable=a[1];
 const d=document.querySelector('[role="dialog"][aria-modal="true"]');
 const p=d&&d.querySelector(sel); if(!p) return {err:'no panel'};
 const els=[...p.querySelectorAll('a[href],button,input,select,textarea,'
   +'[tabindex],[contenteditable="true"]')].filter(e=>{
   if(e.disabled) return false; const t=e.getAttribute('tabindex');
   if(t!==null && Number(t)<0) return false;
   const s=getComputedStyle(e);
   if(s.display==='none'||s.visibility==='hidden') return false;
   const r=e.getBoundingClientRect(); return r.width>0&&r.height>0;});
 const isEd=(e)=>e.tagName==='INPUT'||e.tagName==='SELECT'
   ||e.tagName==='TEXTAREA'||e.isContentEditable;
 const edEls=els.filter(isEd), nonEls=els.filter(e=>!isEd(e));
 const pool=wantEditable?edEls:nonEls;
 if(!pool.length) return {err:'no element of that kind', n:0,
   nEditable:edEls.length, nNonEditable:nonEls.length, total:els.length};
 const e=pool[0]; e.focus();
 const a2=document.activeElement;
 return {focused:a2===e, total:els.length,
   nEditable:edEls.length, nNonEditable:nonEls.length,
   pickedKind:wantEditable?'editable':'noneditable',
   pickedIndex:els.indexOf(e), pickedTag:e.tagName,
   tag:a2?a2.tagName:null, type:a2?a2.getAttribute('type'):null,
   text:a2?(a2.textContent||'').trim().slice(0,12):null};}"""

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
    """mode='fwd'：按 Tab；mode='back'：按 Shift+Tab。

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
    op = open_disclosure(pg, d)
    if op.get("FAILED") or op.get("alreadyOpen"):
        R["FAILED"] = op.get("FAILED") or "浮层已经是开着的，起点不干净"
        R["open"] = op
        return R
    # 起点固定用**非输入框**控件（769 的协议 v2 落点）
    f = pg.evaluate(FOCUS_BY_KIND, [d["panel"], False])
    R["focus"] = f
    if not f.get("focused"):
        R["FAILED"] = ("面板内没有非输入框可聚焦控件：%s"
                       % json.dumps({k: f.get(k) for k in
                                     ("err", "nEditable", "nNonEditable",
                                      "total")}, ensure_ascii=False))
        return R
    R["start"] = pg.evaluate(STEP, [d["trigger"], d["panel"]])
    if (R["start"] or {}).get("err"):
        R["FAILED"] = R["start"]["err"]
        return R
    key = "Tab" if mode == "fwd" else "Shift+Tab"
    R["steps"] = []
    for i in range(STEPS):
        pg.keyboard.press(key)
        pg.wait_for_timeout(90)
        s = pg.evaluate(STEP, [d["trigger"], d["panel"]])
        s["step"] = i + 1
        R["steps"].append(s)
    R["after"] = pg.evaluate(STATE, [d["trigger"], d["panel"]])
    R["desk"] = pg.evaluate(DESK)
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
        for mode in ("fwd", "back"):
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
        sts = r.get("steps") or []
        esc = next((s["step"] for s in sts if not s.get("inPanel")), None)
        if esc is None:
            verdict = "★ %d 步都没走出浮层" % len(sts)
        else:
            s0 = [s for s in sts if s["step"] == esc][0]
            verdict = ("第 %d 步走出浮层 → %s"
                       % (esc,
                          ("**出对话框**" if not s0.get("inDialog")
                           else "留在对话框（%s）"
                           % (s0.get("aria") or s0.get("text")
                              or s0.get("tag")))))
        st0 = r.get("start") or {}
        print("   %-10s %-5s 起点=%-6s 面板内 %s/%s 个控件、对话框共 %s 个 → %s"
              % (r["id"], r["mode"], st0.get("tag"),
                 st0.get("idxInPanel"), st0.get("panelFocusables"),
                 st0.get("dialogFocusables"), verdict))


def main():
    res = {"batch": 770, "probe": "a",
           "question": "6 个浮层里的 Tab 围栏：按 Tab / Shift+Tab 各 12 步，"
                       "焦点会不会走出浮层",
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
