#!/usr/bin/env python3
"""batch 763 探针 e：为什么 `<input type="number">` 里按 Esc 关不掉移动端抽屉？

763d 已定量（两轮完全一致）：
  树面板 20 个控件 → Esc **全部**能关抽屉（含那个 type=text 搜索框）
  属性面板 35 个控件 → **9 个**关不掉，全是 `type="number"`
                     （X/Y/Z 三轴 × 位移/旋转/缩放三组，紧跟 scrub 按钮后）
  读数 `dpAtDocBubble=true` ⟹ preventDefault 发生在 document 冒泡**之前**，
  而导演台的 handler 挂在 window 冒泡（`DirectorDesk.tsx:475`）——它来不及解释。

源码已排除应用 JS：`DirectorInspector.tsx` 里那 9 个数字框**没有 onKeyDown**
（该文件所有 onKeyDown 只处理 Enter），没有 stopPropagation。

本探针做两件事把归因钉死：

① **传播判决**：同一次 Esc 上挂三个监听
     - window 捕获（捕获阶段，任何 stopPropagation 都拦不掉）
     - document 冒泡
     - window 冒泡（与导演台同阶段）
   window 冒泡**没被触发** ⟹ 事件在 window 之下就被消费了，导演台那一档
   根本没机会跑 —— 这就排除了「handler 跑了但 activeMobilePanel 为空」。

② **注入对照**（同位置、同样式、同样 tabindex，只改 `type`）：
     往属性面板里现插一个 `type="text"` 和一个 `type="number"`，
     各按一次 Esc。text 能关、number 关不掉 ⟹ 差别来自 **`type` 本身**，
     与这些框的业务内容、位置、样式都无关。
"""
import json
import pathlib
from playwright.sync_api import sync_playwright

BASE = "http://localhost:4317"
OUT = pathlib.Path(
    "/Users/yangjiefeng/Documents/wubuku/liblib-tv"
    "/docs/research/liblib-canvas-batch763-2026-10-01/raw/vb763e.json")

# 三点埋点 + setTimeout 回读 defaultPrevented（规避 useEffect 重挂导致的顺序漂移）
ARM = """()=>{ if(window.__armed) return {armed:true, already:true};
  window.__esc=[];
  const snap=(e)=>({dp:e.defaultPrevented,
    targetTag:e.target&&e.target.tagName,
    targetType:e.target&&e.target.getAttribute?e.target.getAttribute('type'):null});
  window.addEventListener('keydown', e=>{
    if(e.key!=='Escape') return;
    const r=snap(e); r.stage='winCapture';
    setTimeout(()=>{ r.dpFinal=e.defaultPrevented;
      window.__esc.push(r); },0);
  }, true);
  document.addEventListener('keydown', e=>{
    if(e.key!=='Escape') return;
    const r=snap(e); r.stage='docBubble';
    setTimeout(()=>{ r.dpFinalDoc=e.defaultPrevented; },0);
  }, false);
  window.addEventListener('keydown', e=>{
    if(e.key!=='Escape') return;
    const r=snap(e); r.stage='winBubble';
    setTimeout(()=>{ r.dpFinalWin=e.defaultPrevented; },0);
  }, false);
  window.__armed=true; return {armed:true};}"""

TAKE = """()=>{const l=window.__esc||[]; window.__esc=[];
  return {events:l.map(e=>({stage:e.stage, dp:e.dp, dpFinal:e.dpFinal,
    targetTag:e.targetTag, targetType:e.targetType,
    reachedWinBubble:!!window.__reachedWinBubble})),
    reachedWinBubble:!!window.__reachedWinBubble,
    reachedWinCapture:!!window.__reachedWinCapture,
    dpAtDocBubble:null};}"""

DESK = """()=>{const d=document.querySelector('[role="dialog"][aria-modal="true"]');
 if(!d) return {open:false};
 const insp=d.querySelector('aside[aria-label="属性"]');
 const tree=d.querySelector('aside[aria-label="场景对象"]');
 const p=(el)=>{if(!el) return null; const r=el.getBoundingClientRect();
   return {state:el.getAttribute('data-director-mobile-panel-state'),
     focusScope:el.getAttribute('data-director-focus-scope'),
     inert:!!el.inert, x:Math.round(r.x)};};
 return {open:true, tree:p(tree), inspector:p(insp)};}"""

LIST = """(sel)=>{const d=document.querySelector(
    '[role="dialog"][aria-modal="true"]');
 const p=d.querySelector(sel); if(!p) return {err:'no panel'};
 const out=[]; let i=0;
 for(const e of p.querySelectorAll(
     'a[href],button,input,select,textarea,[tabindex]')){
   if(e.disabled) continue; const t=e.getAttribute('tabindex');
   if(t!==null && Number(t)<0) continue;
   const s=getComputedStyle(e);
   if(s.display==='none'||s.visibility==='hidden') continue;
   const r=e.getBoundingClientRect();
   if(r.width<=0||r.height<=0) continue;
   out.push({i:i++, tag:e.tagName, type:e.getAttribute('type'),
     ariaLabel:e.getAttribute('aria-label'),
     text:(e.textContent||'').trim().slice(0,12),
     dataTF:e.getAttribute('data-director-transform-field'),
     dataTA:e.getAttribute('data-director-transform-axis')});}
 return {panel:sel, count:out.length, items:out};}"""

FOCUS_N = """(a)=>{const sel=a[0], idx=a[1];
 const d=document.querySelector('[role="dialog"][aria-modal="true"]');
 const p=d.querySelector(sel); if(!p) return {err:'no panel'};
 const els=[...p.querySelectorAll(
   'a[href],button,input,select,textarea,[tabindex]')].filter(e=>{
   if(e.disabled) return false; const t=e.getAttribute('tabindex');
   if(t!==null && Number(t)<0) return false;
   const s=getComputedStyle(e);
   if(s.display==='none'||s.visibility==='hidden') return false;
   const r=e.getBoundingClientRect(); return r.width>0&&r.height>0;});
 const e=els[idx]; if(!e) return {err:'index oob'};
 e.focus();
 return {focused:document.activeElement===e, tag:e.tagName,
   type:e.getAttribute('type')};}"""

# 注入对照：同位置、同尺寸，只改 type
INJECT = """(types)=>{const d=document.querySelector(
    '[role="dialog"][aria-modal="true"]');
 const p=d.querySelector('aside[aria-label="属性"]');
 if(!p) return {err:'no panel'};
 const made=[];
 for(const t of types){
   const e=document.createElement('input');
   e.setAttribute('data-763-injected', t);
   e.setAttribute('type', t);
   e.style.cssText='display:block;width:120px;height:28px;margin:2px;'+
     'background:#222;color:#dedede;';
   e.value = (t==='number') ? '1' : 'abc';
   p.appendChild(e); made.push({type:t,
     w:Math.round(e.getBoundingClientRect().width),
     h:Math.round(e.getBoundingClientRect().height)});
 }
 return {made:made, count:made.length};}"""

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
    pg.evaluate(ARM)
    return {"opened": True}


def open_drawer(pg, sel, key):
    st = pg.evaluate(DESK)
    if (st.get(key) or {}).get("state") == "open":
        return {"alreadyOpen": True}
    s = pg.evaluate(SCAN_CLICK, sel)
    if not s.get("pt"):
        return {"FAILED": s}
    pg.mouse.click(s["pt"][0], s["pt"][1])
    pg.wait_for_timeout(900)
    return {"clicked": True, "desk": pg.evaluate(DESK)}


def esc_once(pg):
    """按一次 Esc，返回三点埋点读数 + 抽屉开合。"""
    pg.evaluate("""()=>{window.__reachedWinBubble=false;
      window.__reachedWinCapture=false;}""")
    pg.evaluate("""()=>{const w=window;
      if(!w.__capOnce){ w.__capOnce=true;
        w.addEventListener('keydown',e=>{ if(e.key==='Escape')
          w.__reachedWinCapture=true; },true);
        w.addEventListener('keydown',e=>{ if(e.key==='Escape')
          w.__reachedWinBubble=true; },false);} }""")
    pg.keyboard.press("Escape")
    pg.wait_for_timeout(420)
    log = pg.evaluate(TAKE)
    st = pg.evaluate(DESK)
    insp = st.get("inspector") or {}
    tree = st.get("tree") or {}
    log["inspectorState"] = insp.get("state")
    log["treeState"] = tree.get("state")
    log["deskOpen"] = st.get("open")
    log["focusScope"] = insp.get("focusScope") or tree.get("focusScope")
    return log


def sweep(pg, panel_sel, trigger_sel, key, label):
    lst = pg.evaluate(LIST, panel_sel)
    if "items" not in lst:
        return {"FAILED_list": lst}
    rows = []
    for it in lst["items"]:
        st0 = pg.evaluate(DESK)
        if st0.get("open") is False:
            rows.append({"i": it["i"], "item": it,
                         "skipped": "导演台已关，停止扫描"})
            break
        if (st0.get(key) or {}).get("state") != "open":
            op = open_drawer(pg, trigger_sel, key)
            if "FAILED" in op:
                rows.append({"i": it["i"], "item": it,
                             "skipped": "重开抽屉失败", "open": op})
                break
        f = pg.evaluate(FOCUS_N, [panel_sel, it["i"]])
        e = esc_once(pg)
        rows.append({"i": it["i"], "item": it, "focus": f,
                     "esc": e,
                     "drawerClosed": e.get(key + "State") != "open"})
    bad = [r for r in rows if r.get("drawerClosed") is False]
    return {"panel": label, "count": lst["count"],
            "notClosedIdx": [r["i"] for r in bad],
            "notClosedTypes": [r["item"].get("type") for r in bad],
            "closedTypes": sorted({str(r["item"].get("type")) for r in rows
                                   if r.get("drawerClosed")}),
            "rows": rows}


def injected_control(pg, typ):
    """注入一个同位置的 input[type=typ] 并按 Esc。"""
    inj = pg.evaluate(INJECT, [typ])
    st0 = pg.evaluate(DESK)
    if (st0.get("inspector") or {}).get("state") != "open":
        op = open_drawer(pg, 'button[aria-label="打开属性面板"]', "inspector")
        if "FAILED" in op:
            return {"FAILED": op}
    # 注入框在面板末尾，索引 = 现有控件数 + 已注入数
    n = pg.evaluate("""(sel)=>{const d=document.querySelector(
        '[role="dialog"][aria-modal="true"]');
      const p=d.querySelector(sel);
      let n=0; for(const e of p.querySelectorAll(
        'a[href],button,input,select,textarea,[tabindex]')){
        if(e.disabled) continue; const t=e.getAttribute('tabindex');
        if(t!==null && Number(t)<0) continue;
        const s=getComputedStyle(e);
        if(s.display==='none'||s.visibility==='hidden') continue;
        const r=e.getBoundingClientRect(); if(r.width<=0||r.height<=0) continue;
        n++;} return n;}""", 'aside[aria-label="属性"]')
    idx = n - 1     # 刚注入的是最后一个
    f = pg.evaluate("""(a)=>{const d=document.querySelector(
        '[role="dialog"][aria-modal="true"]');
      const p=d.querySelector('aside[aria-label="属性"]');
      const el=p.querySelector('[data-763-injected="'+a[1]+'"]');
      if(!el) return {err:'injected not found'};
      el.focus();
      return {focused:document.activeElement===el,
        type:el.getAttribute('type'), value:el.value};}""", [idx, typ])
    e = esc_once(pg)
    return {"type": typ, "inject": inj, "focus": f, "esc": e,
            "drawerClosed": e.get("inspectorState") != "open"}


def run_round(pg, R):
    op = load_open(pg)
    R["open"] = op
    if op.get("FAILED_open"):
        return
    R["tree_sweep"] = sweep(pg, 'aside[aria-label="场景对象"]',
                            'button[aria-label="打开场景对象"]', "tree", "tree")
    R["inspector_sweep"] = sweep(
        pg, 'aside[aria-label="属性"]',
        'button[aria-label="打开属性面板"]', "inspector", "inspector")
    R["injectedText"] = injected_control(pg, "text")
    R["injectedNumber"] = injected_control(pg, "number")
    R["deskEnd"] = pg.evaluate(DESK)


def main():
    res = {"batch": 763, "probe": "e",
           "question": "type=number 输入框里 Esc 为什么关不掉移动端抽屉？",
           "rounds": []}
    with sync_playwright() as p:
        br = p.chromium.launch()
        pg = br.new_page(viewport={"width": 800, "height": 1000})
        for _ in range(2):
            R = {}
            run_round(pg, R)
            res["rounds"].append(R)
        br.close()

    def strip(o):
        if isinstance(o, dict):
            return {k: strip(v) for k, v in o.items()}
        if isinstance(o, list):
            return [strip(v) for v in o]
        return o

    r1, r2 = res["rounds"]
    res["consistent"] = (strip(r1) == strip(r2))
    for rd, R in enumerate(res["rounds"], 1):
        t = R.get("tree_sweep") or {}
        i = R.get("inspector_sweep") or {}
        print("r%d 树 %s 个 → 关不掉 %s" % (rd, t.get("count"),
                                            t.get("notClosedIdx")))
        print("r%d 属性 %s 个 → 关不掉 %s（type=%s）；能关的 type=%s"
              % (rd, i.get("count"), i.get("notClosedIdx"),
                 i.get("notClosedTypes"), i.get("closedTypes")))
        for key in ("injectedText", "injectedNumber"):
            c = R.get(key) or {}
            print("r%d 注入 type=%-6s 焦点=%s → 关掉抽屉=%s winBubble=%s"
                  % (rd, key.replace("injected", ""),
                     (c.get("focus") or {}).get("focused"),
                     c.get("drawerClosed"),
                     (c.get("esc") or {}).get("reachedWinBubble")))
        # 首个关不掉的样本，把三点埋点打全
        rows = (i.get("rows") or [])
        for r in rows:
            if r.get("drawerClosed") is False:
                print("   样本 #%s type=%s → %s"
                      % (r["i"], r["item"].get("type"),
                         json.dumps(r["esc"], ensure_ascii=False)[:400]))
                break
        for r in rows:
            if r.get("drawerClosed") is True:
                print("   对照 #%s type=%s → %s"
                      % (r["i"], r["item"].get("type"),
                         json.dumps(r["esc"], ensure_ascii=False)[:400]))
                break
    print("两轮完全一致 =", res["consistent"])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    print("wrote %s" % OUT)


if __name__ == "__main__":
    main()
