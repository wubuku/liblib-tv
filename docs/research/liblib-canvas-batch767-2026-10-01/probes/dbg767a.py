#!/usr/bin/env python3
"""batch 767 探针 a：导演台 6 个 disclosure 浮层的「关闭契约」普查

765 只量了**一个**浮层（导出面板），查出 D4（Esc 关面板后焦点掉到 body）、
D5（没有外点关闭）、D6（disclosure 契约残缺）。但全仓带 `aria-expanded` 的
disclosure 一共 **6 个**，而且静态上就已经分成两派：

  有关闭 effect（外点 pointerdown + Esc，`:554-575` / `:578-599` / `:2734-2753`）
    · 创建运动轨迹菜单（`DirectorTimeline.tsx:1502`）
    · 预设运镜面板（`DirectorTimeline.tsx:1371`）
    · 模型库面板（`DirectorViewport.tsx:2734`）
  没有任何关闭 effect
    · 导出面板（`DirectorDesk.tsx:1351`）—— 765 已实测「点外面不关」
    · 虚拟相机面板（`DirectorViewport.tsx:3080`）
    · 添加群众阵列面板（`DirectorViewport.tsx:3084`）

静态只能证明「某条路径可达/不可达」（765 的 R64），**证明不了浏览器实际
怎么处理事件**。所以本批把同一套 5 个问题挨个问一遍，让读数定案：

  ① 打开瞬间焦点在哪（触发器上 / 浮层内 / 浮层背后）
  ② 点浮层外面会不会关
  ③ Esc 能不能关（**先测外点再测 Esc** —— 不被处理的 Esc 会顺着导演台的
     阶梯把**整个导演台关掉**，所以顺序反了会毁掉后面的读数）
  ④ 关掉之后焦点在哪（触发器上 / body / 浮层内残留）
  ⑤ aria 契约：`aria-expanded` / `aria-controls` / `aria-haspopup` /
     浮层根的 `role` / `aria-label` / 有没有可访问名

这批的用处不只是「又查出几个毛病」：**同一族里有做对了的样本**，可以当
D5/D6 修法的同仓先例 —— 到底是导出面板特殊，还是另外两个也漏了。

★ 破坏性：只点触发器与浮层外面，不点任何提交/生成按钮。虚拟相机面板连
  「连接」都不点。建运动轨迹用的仍是本地预设，不碰源站。
"""
import json
import pathlib
from playwright.sync_api import sync_playwright

BASE = "http://localhost:4317"
OUT = pathlib.Path(
    "/Users/yangjiefeng/Documents/wubuku/liblib-tv"
    "/docs/research/liblib-canvas-batch767-2026-10-01/raw/vb767a.json")
LS_KEY = "liblib-tv-director-project-v1"

# 六个 disclosure：触发器 / 浮层 / 打开前需要的上下文
DISCLOSURES = [
    {"id": "export", "name": "导出面板",
     "trigger": "[data-director-export-trigger]",
     "panel": "[data-director-export-panel]",
     "needs": "none", "src": "DirectorDesk.tsx"},
    {"id": "preset", "name": "预设运镜面板",
     "trigger": "[data-director-camera-preset-trigger]",
     "panel": "[data-director-camera-preset-panel]",
     "needs": "cameraTrack", "src": "DirectorTimeline.tsx"},
    {"id": "pathmenu", "name": "创建运动轨迹菜单",
     "trigger": '[data-director-track-draw-trail="director-track-camera-main"]',
     "panel": "[data-director-motion-path-menu]",
     "needs": "cameraTrack", "src": "DirectorTimeline.tsx"},
    {"id": "phonevcam", "name": "虚拟相机面板",
     "trigger": "[data-director-phone-vcam-trigger]",
     "panel": "[data-director-phone-vcam-panel]",
     "needs": "none", "src": "DirectorPhoneVcamPanel.tsx"},
    {"id": "crowd", "name": "添加群众阵列面板",
     "trigger": "[data-director-crowd-trigger]",
     "panel": "[data-director-crowd-panel]",
     "needs": "none", "src": "DirectorViewport.tsx"},
    {"id": "modellib", "name": "模型库面板",
     "trigger": "[data-director-model-library-trigger]",
     "panel": "[data-director-model-library-panel]",
     "needs": "none", "src": "DirectorViewport.tsx"},
]

DESK = """()=>{const d=document.querySelector('[role="dialog"][aria-modal="true"]');
 if(!d) return {open:false};
 const a=document.activeElement;
 return {open:true,
   activeTag:a?a.tagName:null,
   activeAria:a?a.getAttribute('aria-label'):null,
   activeText:a?(a.textContent||'').trim().slice(0,10):null,
   inDialog:d===a||d.contains(a),
   isBody:a===document.body};}"""

STATE = """(a)=>{const trig=a[0], panel=a[1];
 const d=document.querySelector('[role="dialog"][aria-modal="true"]');
 if(!d) return {open:false};
 const t=d.querySelector(trig);
 const p=d.querySelector(panel);
 const act=document.activeElement;
 const trigSeg=t?(t.outerHTML||''):'';
 return {deskOpen:true,
   triggerPresent:!!t,
   triggerAriaExpanded:t?t.getAttribute('aria-expanded'):null,
   triggerAriaControls:t?t.getAttribute('aria-controls'):null,
   triggerAriaHasPopup:t?t.getAttribute('aria-haspopup'):null,
   triggerAriaLabel:t?t.getAttribute('aria-label'):null,
   triggerTitle:t?t.getAttribute('title'):null,
   triggerHasControlsAttr:trigSeg.includes('aria-controls'),
   triggerHasHasPopupAttr:trigSeg.includes('aria-haspopup'),
   triggerId:t?(t.id||null):null,
   panelPresent:!!p,
   panelTag:p?p.tagName:null,
   panelRole:p?p.getAttribute('role'):null,
   panelAriaLabel:p?p.getAttribute('aria-label'):null,
   panelId:p?(p.id||null):null,
   panelHasHeading:!!(p&&p.querySelector('h1,h2,h3,h4')),
   panelHeading:p&&p.querySelector('h1,h2,h3,h4')
     ?(p.querySelector('h1,h2,h3,h4').textContent||'').trim().slice(0,10):null,
   panelFocusables:p?[...p.querySelectorAll(
     'a[href],button,input,select,textarea,[tabindex],'
     +'[contenteditable="true"]')].filter(e=>{
       if(e.disabled) return false;
       const t2=e.getAttribute('tabindex');
       if(t2!==null && Number(t2)<0) return false;
       const s=getComputedStyle(e);
       if(s.display==='none'||s.visibility==='hidden') return false;
       const r=e.getBoundingClientRect(); return r.width>0&&r.height>0;}).length:0,
   active:{tag:act?act.tagName:null,
     aria:act?act.getAttribute('aria-label'):null,
     text:act?(act.textContent||'').trim().slice(0,10):null,
     isTrigger:!!(act&&t&&act===t),
     inPanel:!!(act&&p&&p.contains(act)),
     inDialog:d===act||d.contains(act),
     isBody:act===document.body}};}"""

SCAN_CLICK = """(sel)=>{const el=document.querySelector(sel);
 if(!el) return {missing:true};
 if(el.disabled) return {disabled:true,
   title:el.getAttribute('title')||null};
 const r=el.getBoundingClientRect();
 for(let f=0.08; f<=0.95; f+=0.07)
   for(let g=0.08; g<=0.95; g+=0.07){
     const x=Math.round(r.x+r.width*f), y=Math.round(r.y+r.height*g);
     if(x<2||y<2||x>innerWidth-2||y>innerHeight-2) continue;
     const e=document.elementFromPoint(x,y);
     if(e&&e.closest&&e.closest(sel)===el) return {pt:[x,y]};}
 return {noHit:true, rect:{x:Math.round(r.x),y:Math.round(r.y),
   w:Math.round(r.width),h:Math.round(r.height)}};}"""

SCAN_PT = """(a)=>{const x=a[0], y=a[1];
 const e=document.elementFromPoint(x,y);
 if(!e) return {none:true};
 const d=document.querySelector('[role="dialog"][aria-modal="true"]');
 return {tag:e.tagName,
   text:(e.textContent||'').trim().slice(0,12),
   inDialog:!!(d&&(d===e||d.contains(e))),
   clickable:!!(e.closest&&e.closest('button,a,[role="button"],input'))};}"""

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


def click_outside(pg, panel_sel, tag):
    """找一个**确实在浮层外、又不是按钮**的点再点。"""
    pr = pg.evaluate("""(s)=>{const p=document.querySelector(s);
     if(!p) return null; const r=p.getBoundingClientRect();
     return {x:Math.round(r.x),y:Math.round(r.y),
       w:Math.round(r.width),h:Math.round(r.height)};}""", panel_sel)
    cands = []
    if pr:
        cands += [[max(2, pr["x"] // 2), 420],
                  [max(2, pr["x"] // 3), 700],
                  [max(2, (pr["x"] - 260) // 2), 500]]
    cands += [[420, 400], [300, 620], [700, 300]]
    tried = []
    for c in cands:
        if not (0 < c[0] < 1400 and 0 < c[1] < 990):
            continue
        s = pg.evaluate(SCAN_PT, c)
        tried.append({"pt": c, "hit": s})
        if s.get("none") or s.get("clickable"):
            continue
        pg.mouse.click(c[0], c[1])
        pg.wait_for_timeout(700)
        return {"clicked": c, "hit": s, "tried": tried}
    return {"skipped": "没找到可安全点的空白点", "tried": tried}


def probe_one(pg, d):
    R = {"id": d["id"], "name": d["name"], "src": d["src"]}
    ensure = ensure_desk(pg)
    R["ensureDesk"] = ensure
    if pg.evaluate(DESK).get("open") is not True:
        R["FAILED"] = "导演台没开"
        return R
    if d["needs"] == "cameraTrack":
        # 预设面板的触发器 disabled 条件是「选中轨道不是 camera」
        R["selCamera"] = pg.evaluate("""()=>{const d=document.querySelector(
          '[role="dialog"][aria-modal="true"]');
         const r=d&&d.querySelector(
           '[data-director-object-id="director-camera-main"]');
         if(!r) return {missing:true};
         const b=r.getBoundingClientRect();
         for(let f=0.1; f<=0.9; f+=0.08)
           for(let g=0.1; g<=0.9; g+=0.08){
             const x=Math.round(b.x+b.width*f), y=Math.round(b.y+b.height*g);
             if(x<2||y<2||x>innerWidth-2||y>innerHeight-2) continue;
             const e=document.elementFromPoint(x,y);
             if(e&&e.closest&&e.closest(
               '[data-director-object-id="director-camera-main"]')){
                 e.closest('[data-director-object-id="director-camera-main"]')
                   .click(); return {clicked:true, pt:[x,y]};}}
         return {noHit:true};}""")
        pg.wait_for_timeout(1100)
    R["before"] = pg.evaluate(STATE, [d["trigger"], d["panel"]])
    s = pg.evaluate(SCAN_CLICK, d["trigger"])
    R["triggerScan"] = s
    if not s.get("pt"):
        R["FAILED"] = "触发器扫不到（missing/disabled/noHit）"
        return R
    pg.mouse.click(s["pt"][0], s["pt"][1])
    pg.wait_for_timeout(800)
    R["afterOpen"] = pg.evaluate(STATE, [d["trigger"], d["panel"]])
    if not R["afterOpen"].get("panelPresent"):
        R["FAILED"] = "点了触发器但浮层没出现"
        R["deskAfterOpen"] = pg.evaluate(DESK)
        return R

    # ② 外点关闭（**先测** —— 不被处理的 Esc 会把整个导演台关掉）
    R["outside"] = click_outside(pg, d["panel"], d["id"])
    R["afterOutside"] = pg.evaluate(STATE, [d["trigger"], d["panel"]])

    # ③ Esc（浮层还开着才测）
    if R["afterOutside"].get("panelPresent"):
        pg.keyboard.press("Escape")
        pg.wait_for_timeout(700)
        R["afterEsc"] = pg.evaluate(STATE, [d["trigger"], d["panel"]])
    else:
        R["afterEsc"] = {"skipped": "外点那一下已经关掉了，Esc 无从测起"}
    R["deskEnd"] = pg.evaluate(DESK)
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
    R["results"] = []
    for d in DISCLOSURES:
        try:
            R["results"].append(probe_one(pg, d))
        except Exception as e:
            R["results"].append({"id": d["id"], "name": d["name"],
                                 "FAILED": "%s: %s" % (type(e).__name__,
                                                      str(e)[:160])})
        # 收尾：把导演台恢复到干净状态（Esc 可能把它关掉了）
        if pg.evaluate(DESK).get("open") is not True:
            R.setdefault("reopened", []).append(d["id"])
            open_desk(pg)


def summarize(R):
    rows = []
    for r in R.get("results") or []:
        if r.get("FAILED"):
            rows.append((r.get("id"), "FAILED: %s" % r["FAILED"][:60]))
            continue
        a = r.get("afterOpen") or {}
        ao = r.get("afterOutside") or {}
        ae = r.get("afterEsc") or {}
        rows.append((
            r["id"],
            "开=%s 焦点在触发器=%s 焦点进浮层=%s | 外点关=%s | Esc关=%s "
            "关后焦点=%s | controls=%s haspopup=%s role=%s"
            % (a.get("panelPresent"), a.get("active", {}).get("isTrigger"),
               a.get("active", {}).get("inPanel"),
               (not ao.get("panelPresent")) if ao.get("panelPresent") is not None
               else None,
               (not ae.get("panelPresent")) if "panelPresent" in ae else None,
               ((ae.get("active") or {}).get("tag")
                or (ao.get("active") or {}).get("tag")),
               a.get("triggerHasControlsAttr"), a.get("triggerHasHasPopupAttr"),
               a.get("panelRole"))))
    for x in rows:
        print("   %-11s %s" % x)


def main():
    res = {"batch": 767, "probe": "a",
           "question": "导演台 6 个带 aria-expanded 的 disclosure 浮层的关闭契约普查",
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
        print("\n=== r%d ===" % rd)
        print("  重开过导演台的 disclosure：%s"
              % json.dumps(R.get("reopened"), ensure_ascii=False))
        for r in R.get("results") or []:
            a = r.get("afterOpen") or {}
            print("  %-11s aria-expanded=%s controls=%s haspopup=%s | "
                  "panel role=%s aria-label=%s heading=%s 可聚焦=%s"
                  % (r.get("id"), a.get("triggerAriaExpanded"),
                     a.get("triggerHasControlsAttr"),
                     a.get("triggerHasHasPopupAttr"), a.get("panelRole"),
                     a.get("panelAriaLabel"), a.get("panelHeading"),
                     a.get("panelFocusables")))
    print("wrote %s" % OUT)


if __name__ == "__main__":
    main()
