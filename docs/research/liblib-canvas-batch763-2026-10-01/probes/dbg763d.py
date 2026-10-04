#!/usr/bin/env python3
"""batch 763 探针 d：移动端抽屉里，**逐个**可聚焦控件按 Esc 会发生什么？

起因（763b 两轮不一致，如实记）：
  - round 1 属性抽屉 Esc **没关上**（state 仍 open、inert=false、rect x=519），
    round 2 关上了（state=closed、x=800）；两轮 tree 抽屉都正常。
  - 同一序列两轮里属性面板可达控件 **35 vs 33**、打开后首焦点 BUTTON vs INPUT。

判决工具（源码给的）：
  `DirectorDesk.tsx:475` 把 `handleKeyDown` 挂在 **window 冒泡**阶段。
  ⟹ 任何后代控件对 Escape 调 `stopPropagation()`，关抽屉那一档
     （`:481 if (event.key==="Escape" && activeMobilePanel)`）**整段收不到**。
  另外该 listener 在 `useEffect` 依赖变化时会 remove+add，**注册顺序会漂**，
  所以不能在 document 上挂一个固定的冒泡监听去读 defaultPrevented
  ——它可能排在 desk 的前面。改用：document 冒泡里 `setTimeout(...,0)`
  回读 `event.defaultPrevented`（同一个任务里所有监听跑完后才执行，顺序无关）。

每格记录：落点控件（tag/aria-label/文案）、Esc 的 target、defaultPrevented、
抽屉开合、focus-scope。**命中不了就是命中不了，如实记。**
"""
import json
import pathlib
from playwright.sync_api import sync_playwright

BASE = "http://localhost:4317"
OUT = pathlib.Path(
    "/Users/yangjiefeng/Documents/wubuku/liblib-tv"
    "/docs/research/liblib-canvas-batch763-2026-10-01/raw/vb763d.json")

# 在 document 冒泡里抓 Esc；setTimeout 回读 defaultPrevented，规避注册顺序漂移
ARM = """()=>{ if(window.__escArmed) return {armed:true, already:true};
  window.__escLog=[];
  document.addEventListener('keydown', e=>{
    if(e.key!=='Escape') return;
    const t=e.target;
    const rec={dpAtDocBubble:e.defaultPrevented,
      targetTag:t&&t.tagName,
      targetAria:t&&t.getAttribute?t.getAttribute('aria-label'):null,
      targetText:t&&t.textContent?(t.textContent||'').trim().slice(0,14):null,
      activeTag:document.activeElement?document.activeElement.tagName:null,
      activeAria:document.activeElement&&document.activeElement.getAttribute
        ?document.activeElement.getAttribute('aria-label'):null};
    setTimeout(()=>{ rec.dpFinal=e.defaultPrevented;
      window.__escLog.push(rec); },0);
  }, false);
  window.__escArmed=true; return {armed:true};}"""

TAKE = """()=>{const l=window.__escLog||[]; window.__escLog=[]; return l;}"""

DESK = """()=>{const d=document.querySelector('[role="dialog"][aria-modal="true"]');
 if(!d) return {open:false};
 const tree=d.querySelector('aside[aria-label="场景对象"]');
 const insp=d.querySelector('aside[aria-label="属性"]');
 const p=(el)=>{if(!el) return null; const r=el.getBoundingClientRect();
   return {state:el.getAttribute('data-director-mobile-panel-state'),
     focusScope:el.getAttribute('data-director-focus-scope'),
     inert:!!el.inert, x:Math.round(r.x), w:Math.round(r.width)};};
 return {open:true, tree:p(tree), inspector:p(insp)};}"""

LIST = """(sel)=>{const d=document.querySelector(
    '[role="dialog"][aria-modal="true"]');
 if(!d) return {err:'no dialog'};
 const p=d.querySelector(sel);
 if(!p) return {err:'no panel ' + sel};
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
   const hiddenType=/^(input|select|textarea)$/i.test(e.tagName)&&
     (s.opacity==='0'||r.width<=2||r.height<=2);
   out.push({i:i++, tag:e.tagName, type:e.getAttribute('type'),
     ariaLabel:e.getAttribute('aria-label'),
     text:(e.textContent||'').trim().slice(0,14),
     w:Math.round(r.width), h:Math.round(r.height),
     x:Math.round(r.x), y:Math.round(r.y), hiddenType:hiddenType});
 }
 return {panel:sel, count:out.length, items:out};}"""

FOCUS_N = """(a)=>{const sel=a[0], idx=a[1];
 const d=document.querySelector('[role="dialog"][aria-modal="true"]');
 if(!d) return {err:'no dialog'};
 const p=d.querySelector(sel); if(!p) return {err:'no panel'};
 const els=[...p.querySelectorAll(
   'a[href],button,input,select,textarea,[tabindex]')].filter(e=>{
   if(e.disabled) return false; const t=e.getAttribute('tabindex');
   if(t!==null && Number(t)<0) return false;
   const s=getComputedStyle(e);
   if(s.display==='none'||s.visibility==='hidden') return false;
   const r=e.getBoundingClientRect(); return r.width>0&&r.height>0;});
 const e=els[idx]; if(!e) return {err:'index out of range'};
 e.focus();
 const a2=document.activeElement;
 return {focused:a2===e, tag:e.tagName,
   activeTag:a2?a2.tagName:null,
   activeAria:a2?a2.getAttribute('aria-label'):null};}"""

SCAN_CLICK = """(sel)=>{const el=document.querySelector(sel);
 if(!el) return {missing:true};
 const r=el.getBoundingClientRect();
 for(let f=0.1; f<=0.95; f+=0.07) for(let g=0.1; g<=0.95; g+=0.07){
   const x=Math.round(r.x+r.width*f), y=Math.round(r.y+r.height*g);
   if(x<2||y<2||x>innerWidth-2||y>innerHeight-2) continue;
   const e=document.elementFromPoint(x,y);
   if(e&&e.closest&&e.closest(sel)) return {pt:[x,y],
     rect:{x:Math.round(r.x),y:Math.round(r.y),
           w:Math.round(r.width),h:Math.round(r.height)}};}
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
    return {"opened": True, "desk": pg.evaluate(DESK)}


def ensure_open(pg, trigger_sel, panel_key):
    st = pg.evaluate(DESK)
    if st.get("open") is False:
        return {"needReload": True, "desk": st}
    cur = st.get(panel_key) or {}
    if cur.get("state") == "open":
        return {"alreadyOpen": True}
    s = pg.evaluate(SCAN_CLICK, trigger_sel)
    if not s.get("pt"):
        return {"FAILED_trigger": s, "desk": st}
    pg.mouse.click(s["pt"][0], s["pt"][1])
    pg.wait_for_timeout(900)
    return {"clicked": s, "desk": pg.evaluate(DESK)}


def sweep(pg, panel_sel, trigger_sel, panel_key, label):
    lst = pg.evaluate(LIST, panel_sel)
    if "items" not in lst:
        return {"FAILED_list": lst}
    rows = []
    for it in lst["items"]:
        st0 = pg.evaluate(DESK)
        need_reload = (st0.get("open") is False)
        if need_reload:
            rows.append({"i": it["i"], "skipped": "director 已关闭，跳过",
                         "item": it})
            break
        cur = st0.get(panel_key) or {}
        if cur.get("state") != "open":
            op = ensure_open(pg, trigger_sel, panel_key)
            if op.get("FAILED_trigger") or op.get("needReload"):
                rows.append({"i": it["i"], "skipped": "重开抽屉失败",
                             "item": it, "openResult": op})
                break
        f = pg.evaluate(FOCUS_N, [panel_sel, it["i"]])
        pg.evaluate(TAKE)                      # 清掉历史 Esc 记录
        pg.keyboard.press("Escape")
        pg.wait_for_timeout(420)
        log = pg.evaluate(TAKE)
        st1 = pg.evaluate(DESK)
        p1 = st1.get(panel_key) or {}
        rows.append({
            "i": it["i"], "item": it, "focus": f, "esc": log,
            "panelClosed": p1.get("state") != "open",
            "stateAfter": p1.get("state"),
            "focusScopeAfter": p1.get("focusScope"),
            "deskOpenAfter": st1.get("open"),
            "activeAfter": pg.evaluate("""()=>{const a=document.activeElement;
              return a?{tag:a.tagName,
                aria:a.getAttribute?a.getAttribute('aria-label'):null,
                text:(a.textContent||'').trim().slice(0,14)}:null;}""")})
    return {"panel": label, "count": lst["count"], "rows": rows,
            "notClosed": [r["i"] for r in rows
                          if r.get("panelClosed") is False],
            "noEscRecord": [r["i"] for r in rows if not r.get("esc")]}


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
    R["deskEnd"] = pg.evaluate(DESK)


def main():
    res = {"batch": 763, "probe": "d",
           "question": "移动端抽屉里逐个可聚焦控件按 Esc，抽屉会关吗？",
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
    res["treeCount"] = [r1["tree_sweep"].get("count"),
                        r2["tree_sweep"].get("count")]
    res["inspCount"] = [r1["inspector_sweep"].get("count"),
                        r2["inspector_sweep"].get("count")]
    res["treeNotClosed"] = [r1["tree_sweep"].get("notClosed"),
                            r2["tree_sweep"].get("notClosed")]
    res["inspNotClosed"] = [r1["inspector_sweep"].get("notClosed"),
                            r2["inspector_sweep"].get("notClosed")]
    res["consistent"] = (strip(r1) == strip(r2))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    print("tree  可达控件两轮 =", res["treeCount"],
          " 没关掉的序号 =", res["treeNotClosed"])
    print("insp  可达控件两轮 =", res["inspCount"],
          " 没关掉的序号 =", res["inspNotClosed"])
    print("两轮完全一致 =", res["consistent"])
    for rd, R in enumerate(res["rounds"], 1):
        for key in ("tree_sweep", "inspector_sweep"):
            s = R.get(key) or {}
            if "rows" not in s:
                print("r%d %s FAILED %s" % (rd, key, json.dumps(s,
                      ensure_ascii=False)[:160]))
                continue
            bad = [r for r in s["rows"] if r.get("panelClosed") is False]
            print("  r%d %s: %s 个控件，%s 个按 Esc 没关上"
                  % (rd, key, s["count"], len(bad)))
            for r in bad:
                print("     #%s %s %s esc=%s"
                      % (r["i"], r["item"]["tag"],
                         json.dumps(r["item"].get("ariaLabel")
                                    or r["item"].get("text"),
                                    ensure_ascii=False),
                         json.dumps(r.get("esc"), ensure_ascii=False)[:150]))


if __name__ == "__main__":
    main()
