#!/usr/bin/env python3
"""batch 766 探针 b：把路径锚点的**控制柄**那 6 个框也逼出来（764 未验证清单的最后一项）

766a 已经把三类未验证控件里的两类验完了：
  - 路径变换 9 个数值框 → 全部吞 Esc（boundary-own ⟺ swallowed，22/22）
  - 路径锚点**位置** 3 个数值框 → 全部吞 Esc
  - FOV 滑杆（`data-director-camera-fov`，自身带 gesture）→ 吞 Esc

但 766a 里锚点类型默认是 `vertex`，而 `DirectorInspector.tsx:1189` 写的是
`{selectedAnchor.type !== "vertex" ? <PathTupleFields kind="handle" …/> × 2 : null}`
⟹ **入/出控制柄那 6 个数值框（2 组 × 3 轴）一次都没渲染**，仍然未验证。

本批只做一件事：点一下锚点类型里的「对称」/「非对称」（`data-director-path-anchor-type-option`），
让控制柄框出现，再用 766a 同一套**行为反推**扫法量它们的 Esc 影响面。

沿用 766a 的三条规矩：
1. 页面一加载就往 window 装传播探针（注册在 React 之前），按 Esc 时
   `stopImmediatePropagation()` 冻住导演台自己的处理器 ⟹ 只测「到没到 window」，
   不测「做了什么」，也就不会把导演台关掉。
2. 先验可点性再点（扫网格 + `elementFromPoint`），hit=false 不点。
3. 每轮开头清 `liblib-tv-director-project-v1:*` 再 reload —— 建轨迹是破坏性的，
   导演台项目会持久化（763 O1），不清的话第二轮起点就带着第一轮的路径。
"""
import json
import pathlib
from playwright.sync_api import sync_playwright

BASE = "http://localhost:4317"
OUT = pathlib.Path(
    "/Users/yangjiefeng/Documents/wubuku/liblib-tv"
    "/docs/research/liblib-canvas-batch766-2026-10-01/raw/vb766b.json")
LS_KEY = "liblib-tv-director-project-v1"

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

# 只扫 MotionPathInspector 里的可聚焦控件 —— 本批只关心锚点区
SCAN_PATH = """()=>{const d=document.querySelector(
  '[role="dialog"][aria-modal="true"]');
 const ins=d&&d.querySelector('[data-director-motion-path-inspector]');
 if(!ins) return {err:'no motion path inspector'};
 const MARK=/^data-director-/;
 const out=[]; let i=0;
 for(const e of ins.querySelectorAll(
   'a[href],button,input,select,textarea,[tabindex],[contenteditable="true"]')){
   if(e.disabled) continue; const t=e.getAttribute('tabindex');
   if(t!==null && Number(t)<0) continue;
   const s=getComputedStyle(e);
   if(s.display==='none'||s.visibility==='hidden') continue;
   const r=e.getBoundingClientRect(); if(r.width<=0||r.height<=0) continue;
   const own=[]; for(const a of e.attributes)
     if(MARK.test(a.name)) own.push(a.name);
   out.push({i:i++, tag:e.tagName, type:e.getAttribute('type'),
     aria:e.getAttribute('aria-label'),
     text:(e.textContent||'').trim().slice(0,10),
     ownMarks:own,
     isAnchorPosition:!!e.closest('[data-director-path-anchor-position]'),
     isAnchorHandle:!!e.closest('[data-director-path-anchor-handle]'),
     handleAxis:e.getAttribute('data-director-path-anchor-handle'),
     inLegend:!!e.closest('legend')});
 }
 return {count:out.length, controls:out};}"""

FOCUS_N = """(a)=>{const i=a[0];
 const d=document.querySelector('[role="dialog"][aria-modal="true"]');
 const ins=d&&d.querySelector('[data-director-motion-path-inspector]');
 if(!ins) return {err:'no inspector'};
 const els=[...ins.querySelectorAll(
   'a[href],button,input,select,textarea,[tabindex],[contenteditable="true"]')]
  .filter(e=>{ if(e.disabled) return false;
    const t=e.getAttribute('tabindex');
    if(t!==null && Number(t)<0) return false;
    const s=getComputedStyle(e);
    if(s.display==='none'||s.visibility==='hidden') return false;
    const r=e.getBoundingClientRect(); return r.width>0&&r.height>0;});
 const e=els[i]; if(!e) return {err:'oob', n:els.length};
 e.focus(); const a2=document.activeElement;
 return {focused:a2===e, tag:a2?a2.tagName:null,
   type:a2?a2.getAttribute('type'):null};}"""

DESK = """()=>{const d=document.querySelector('[role="dialog"][aria-modal="true"]');
 if(!d) return {open:false};
 const a=document.activeElement;
 return {open:true, activeTag:a?a.tagName:null};}"""

CLICK_SEL = """(sel)=>{const el=document.querySelector(sel);
 if(!el) return {missing:true};
 if(el.disabled) return {disabled:true};
 const r=el.getBoundingClientRect();
 for(let f=0.08; f<=0.95; f+=0.07)
   for(let g=0.08; g<=0.95; g+=0.07){
     const x=Math.round(r.x+r.width*f), y=Math.round(r.y+r.height*g);
     if(x<2||y<2||x>innerWidth-2||y>innerHeight-2) continue;
     const e=document.elementFromPoint(x,y);
     if(e&&e.closest&&e.closest(sel)===el) return {pt:[x,y]};}
 return {noHit:true, rect:{x:Math.round(r.x),y:Math.round(r.y),
   w:Math.round(r.width),h:Math.round(r.height)}};}"""


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


SCROLL_IN = """(sel)=>{const el=document.querySelector(sel);
 if(!el) return {missing:true};
 el.scrollIntoView({block:'center', inline:'nearest'});
 const r=el.getBoundingClientRect();
 return {x:Math.round(r.x), y:Math.round(r.y),
   w:Math.round(r.width), h:Math.round(r.height),
   inViewport:r.top>=0 && r.bottom<=innerHeight};}"""


def click(pg, sel, wait=900):
    s = pg.evaluate(CLICK_SEL, sel)
    scrolled = None
    if not s.get("pt"):
        # ★ 元素在视口之外（属性面板可滚动，锚点列表实测在 y≈1769）⟹ 先滚进视口
        scrolled = pg.evaluate(SCROLL_IN, sel)
        if scrolled.get("missing"):
            return {"FAILED": True, "scan": s, "scrolled": scrolled,
                    "sel": sel}
        pg.wait_for_timeout(350)
        s = pg.evaluate(CLICK_SEL, sel)
    if not s.get("pt"):
        return {"FAILED": True, "scan": s, "scrolled": scrolled, "sel": sel}
    pg.mouse.click(s["pt"][0], s["pt"][1])
    pg.wait_for_timeout(wait)
    return {"clicked": True, "sel": sel, "pt": s["pt"], "scrolled": scrolled}


def handle_count(pg):
    return pg.evaluate("""()=>{const d=document.querySelector(
      '[role="dialog"][aria-modal="true"]');
     if(!d) return 0;
     return d.querySelectorAll('[data-director-path-anchor-handle]').length;}""")


def anchor_type_state(pg):
    return pg.evaluate("""()=>{const d=document.querySelector(
      '[role="dialog"][aria-modal="true"]');
     if(!d) return [];
     return [...d.querySelectorAll('[data-director-path-anchor-type-option]')]
       .map(b=>({type:b.getAttribute('data-director-path-anchor-type-option'),
         pressed:b.getAttribute('aria-pressed')}));}""")


def sweep_handles(pg, label):
    """只扫锚点区，行为反推 + 标记分类。"""
    sc = pg.evaluate(SCAN_PATH)
    if sc.get("err") or not sc.get("controls"):
        return {"label": label, "FAILED": sc.get("err", "扫不到控件"),
                "scan": sc}
    rows = []
    for it in sc["controls"]:
        if not (pg.evaluate(DESK).get("open")):
            return {"label": label, "FAILED": "扫到一半导演台没了",
                    "done": len(rows)}
        f = pg.evaluate(FOCUS_N, [it["i"]])
        if not f.get("focused"):
            rows.append({"i": it["i"], "ctrl": it, "FAILED": "没获得焦点",
                         "focus": f})
            continue
        pg.evaluate(FREEZE, True)
        pg.keyboard.press("Escape")
        pg.wait_for_timeout(110)
        fl = pg.evaluate(READ)
        pg.evaluate(FREEZE, False)
        if fl["reachedCapture"] and not fl["reachedBubble"]:
            beh = "swallowed-below-window"
        elif fl["reachedBubble"] and fl["targetIsEditable"]:
            beh = "reached-then-editable-guard"
        elif fl["reachedBubble"]:
            beh = "reached-plain"
        else:
            beh = "never-reached"
        own = set(it["ownMarks"])
        if own & {"data-director-path-anchor-handle",
                  "data-director-path-anchor-position",
                  "data-director-path-transform-axis"}:
            mk = "boundary-own"
        else:
            mk = "no-marker"
        rows.append({"i": it["i"], "ctrl": it, "focus": f,
                     "reachedCapture": fl["reachedCapture"],
                     "reachedBubble": fl["reachedBubble"],
                     "targetAtWindow": fl["targetAtWindow"],
                     "targetIsEditable": fl["targetIsEditable"],
                     "behavior": beh, "markerClass": mk})
    return {"label": label, "scanCount": sc["count"], "rows": rows}


def run_round(pg, R):
    R["load"] = load_open(pg)
    if R["load"].get("FAILED_open"):
        R["verdict"] = "打开导演台失败"
        return
    if not pg.evaluate(DESK).get("open"):
        R["verdict"] = "加载后导演台没开"
        return
    R["selCamera"] = click(pg, '[data-director-object-id="director-camera-main"]',
                           wait=1300)
    R["openMenu"] = click(pg, '[data-director-track-draw-trail="%s"]' % "director-track-camera-main",
                          wait=900)
    R["createPath"] = click(pg, '[data-director-motion-path-preset="line"]',
                            wait=1600)
    R["hasInspector"] = pg.evaluate("""()=>{const d=document.querySelector(
      '[role="dialog"][aria-modal="true"]');
     return !!(d&&d.querySelector('[data-director-motion-path-inspector]'));}""")
    if not R["hasInspector"]:
        R["verdict"] = "MotionPathInspector 没渲染，后面的读数不作数"
        return
    # 选一个锚点
    opts = pg.evaluate("""()=>[...document.querySelectorAll(
      '[role="dialog"][aria-modal="true"] [data-director-path-anchor-option]')]
      .map(o=>({id:o.getAttribute('data-director-path-anchor-option'),
        text:(o.textContent||'').trim().slice(0,6)}));""")
    R["anchorOptions"] = opts
    R["selectAnchor"] = None
    for o in opts or []:
        c = click(pg, '[data-director-path-anchor-option="%s"]' % o["id"], 900)
        R["selectAnchor"] = {"option": o, "click": c}
        if handle_count(pg) >= 0 and pg.evaluate("""()=>{const d=document.querySelector(
          '[role="dialog"][aria-modal="true"]');
         return d.querySelectorAll('[data-director-path-anchor-position]').length>0;}"""):
            break
    R["typeBefore"] = anchor_type_state(pg)
    R["handleCountBeforeType"] = handle_count(pg)
    R["positionCountBeforeType"] = pg.evaluate("""()=>{const d=document.querySelector(
      '[role="dialog"][aria-modal="true"]');
     return d.querySelectorAll('[data-director-path-anchor-position]').length;}""")
    # ★ 关键一步：把锚点类型从 vertex 改成「对称」，让控制柄框渲染出来
    R["setTypeSymmetric"] = click(
        pg, '[data-director-path-anchor-type-option="symmetric"]', 1000)
    R["typeAfter"] = anchor_type_state(pg)
    R["handleCountAfterType"] = handle_count(pg)
    R["positionCountAfterType"] = pg.evaluate("""()=>{const d=document.querySelector(
      '[role="dialog"][aria-modal="true"]');
     return d.querySelectorAll('[data-director-path-anchor-position]').length;}""")
    R["legendTexts"] = pg.evaluate("""()=>{const d=document.querySelector(
      '[role="dialog"][aria-modal="true"]');
     const ins=d&&d.querySelector('[data-director-motion-path-inspector]');
     if(!ins) return [];
     return [...ins.querySelectorAll('legend')].map(l=>(l.textContent||'').trim());}""")
    R["sweep"] = sweep_handles(pg, "path-anchor-handles")
    rows = R["sweep"].get("rows") or []
    handle_rows = [r for r in rows
                   if not r.get("FAILED") and r["ctrl"].get("isAnchorHandle")]
    R["handleRows"] = len(handle_rows)
    R["handleSwallowed"] = sum(1 for r in handle_rows
                               if r["behavior"] == "swallowed-below-window")
    R["handleAllBoundaryOwn"] = all(r["markerClass"] == "boundary-own"
                                    for r in handle_rows)
    R["xtab"] = {}
    for r in rows:
        if r.get("FAILED"):
            continue
        k = "%s | %s" % (r["markerClass"], r["behavior"])
        R["xtab"][k] = R["xtab"].get(k, 0) + 1
    R["failedRows"] = [r["i"] for r in rows if r.get("FAILED")]


def print_round(R):
    print("   锚点选项=%s | 类型 %s→%s | 控制柄框 %s→%s | 位置框 %s→%s"
          % (json.dumps(R.get("anchorOptions"), ensure_ascii=False),
             json.dumps(R.get("typeBefore"), ensure_ascii=False),
             json.dumps(R.get("typeAfter"), ensure_ascii=False),
             R.get("handleCountBeforeType"), R.get("handleCountAfterType"),
             R.get("positionCountBeforeType"),
             R.get("positionCountAfterType")))
    print("   legend=%s" % json.dumps(R.get("legendTexts"),
                                      ensure_ascii=False))
    sw = R.get("sweep") or {}
    print("   扫 %s 个控件 | 控制柄格 %s 吞 Esc %s | 交叉表 %s | 失败行 %s"
          % (sw.get("scanCount"), R.get("handleRows"),
             R.get("handleSwallowed"), json.dumps(R.get("xtab"),
                                                  ensure_ascii=False),
             R.get("failedRows")))


def main():
    res = {"batch": 766, "probe": "b",
           "question": "把路径锚点的控制柄 6 个框逼出来并量 Esc 影响面",
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
        print("  handleRows=%s handleSwallowed=%s allBoundaryOwn=%s"
              % (R.get("handleRows"), R.get("handleSwallowed"),
                 R.get("handleAllBoundaryOwn")))
    print("wrote %s" % OUT)


if __name__ == "__main__":
    main()
