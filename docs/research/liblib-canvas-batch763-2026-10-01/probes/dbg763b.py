#!/usr/bin/env python3
"""batch 763 探针 b：移动端抽屉的焦点围栏 + 导演台自己的快捷键

763a 把两块都验成「修好的 / 正确的」：
  - Batch 622 那个 1px 断点缝：896–901 六档 JS 与 CSS **零错位**
  - Esc 优先级阶梯四档全对（导出面板优先、可编辑控件内不关、离开后能关、无面板能关）

还剩三块没碰：

**① 移动端 focus scope（762 的「不声称」之一，完全没测）。**
`openMobilePanel("tree" | "inspector")`（`DirectorDesk.tsx:406-416`）
会把 `viewportPanelsCollapsed` 重置为 false 并记下 `mobilePanelReturnRef`。
入口是视口左上角两枚 `max-[899px]:flex` 的按钮
（`DirectorViewport.tsx:3366/3375`，`aria-label` 分别是
「打开场景对象」「打开属性面板」）。要量：
  - 抽屉打开后 `data-director-mobile-panel-state` 与 `data-director-focus-scope`
  - **焦点有没有进抽屉**
  - Tab 是否仍被围在 dialog 内
  - Esc 是否**只关抽屉**（`:482` 那一档）而不关整个导演台

**② 导演台自己的快捷键**（`DirectorDesk.tsx:487-545`）：
`⌘C` / `⌘V` / `⌘Z` / `⌘⇧Z` / `⌘Y` / `Delete` / `Backspace`。
读 `data-director-history-past` / `-future` / `data-director-last-command` 三个钩子。

**③ `workspaceBusy` 与 `capture-viewer` 两档会吞掉 Delete 与 Esc**（`:519/:551`）——
这两档不好主动制造，列为不声称。

== 本版相对初版改了什么，以及为什么 ==

初版在每轮里「1440 加载 → Meta+0 → resize 800 → Meta+0 → 点按钮」，
`click_real` 反复 FATAL，落在 `x=596`、0 命中、中心是 DIV。
查下来（探针 763c，4 档 delay × 2 轮 = 8 次 trial）：
  - 800 档期望落点 `x=276`、1440 档 `x=526`，而 FATAL 那个 596 **两者都不是**；
    按钮宽高与 800 档完全一致（zoom 0.2396），只有 x 偏了 320 = 1440/2 − 800/2。
  - 8 次 trial **全部**落在 276、zoom 正确、命中 169 点，0/8 复现。
⟹ 定性为一次性瞬态，不作为产品缺陷记账（不改判据，只改探针）。

探针侧三处加固：
1. **每格在自己的宽度上直接加载**（`set_viewport_size` → `goto`），不再
   「先在别的宽度加载再 resize」。`set_viewport_size` 是按 page 生效的，
   改完就长期留在那个宽度，第二轮的「resize 到 800」其实是空操作。
2. **`settle()` 等 fitView 落定**：连续 3 次读 store 视口不变才算稳。
3. **落空不再 SystemExit**：`click_real` 命中失败时把判别读数
   （vw / store 视口 / 中心元素栈 / 节点 rect / dialog 是否已开）**落盘**，
   重试一次后仍不中才记 FAILED。规矩不变：命中不了就是命中不了，如实记，
   但不许让一次瞬态把整轮读数一起带走。
"""
import json
import pathlib
import re
from playwright.sync_api import sync_playwright

BASE = "http://localhost:4317"
OUT = pathlib.Path(
    "/Users/yangjiefeng/Documents/wubuku/liblib-tv"
    "/docs/research/liblib-canvas-batch763-2026-10-01/raw/vb763b.json")

DESK = """()=>{const d=document.querySelector('[role="dialog"][aria-modal="true"]');
 if(!d) return {open:false};
 const tree=d.querySelector('aside[aria-label="场景对象"]');
 const insp=d.querySelector('aside[aria-label="属性"]');
 const p=(el)=>{if(!el) return null; const r=el.getBoundingClientRect();
   return {inert:!!el.inert, ariaHidden:el.getAttribute('aria-hidden'),
     state:el.getAttribute('data-director-mobile-panel-state'),
     focusScope:el.getAttribute('data-director-focus-scope'),
     rect:{x:Math.round(r.x),y:Math.round(r.y),
           w:Math.round(r.width),h:Math.round(r.height)}};};
 return {open:true, innerWidth:innerWidth,
   focusState:d.getAttribute('data-director-focus-state'),
   focusReturn:d.getAttribute('data-director-focus-return'),
   collapsed:d.getAttribute('data-director-panels-collapsed'),
   tree:p(tree), inspector:p(insp),
   historyPast:d.getAttribute('data-director-history-past'),
   historyFuture:d.getAttribute('data-director-history-future'),
   lastCommand:d.getAttribute('data-director-last-command')||'',
   lastDisposition:d.getAttribute('data-director-last-disposition')||'',
   activeGesture:d.getAttribute('data-director-active-gesture')||''};}"""

ACTIVE = """()=>{const d=document.querySelector('[role="dialog"][aria-modal="true"]');
 const a=document.activeElement;
 let scope=null;
 if(a){const h=a.closest('aside[aria-label="场景对象"]');
   const i=a.closest('aside[aria-label="属性"]');
   if(h) scope='tree'; else if(i) scope='inspector';}
 return {open:!!d, inDialog:d?(d===a||d.contains(a)):false,
   tag:a?a.tagName:null, ariaLabel:a?a.getAttribute('aria-label'):null,
   inPanel:scope, text:a?(a.textContent||'').trim().slice(0,18):null};}"""

HIT = """(a)=>{const x=a[0],y=a[1],sel=a[2];const e=document.elementFromPoint(x,y);
 if(!e) return {tag:null,ok:false};
 const t=e.closest(sel);
 return {tag:e.tagName, ok:!!t,
   ariaLabel:t?t.getAttribute('aria-label'):null};}"""

FOCUSABLE_IN_PANEL = """(sel)=>{const d=document.querySelector(
  '[role="dialog"][aria-modal="true"]');
 if(!d) return null;
 const p=d.querySelector(sel); if(!p) return {panelMissing:true};
 let n=0; for(const e of p.querySelectorAll('a[href],button,input,select,textarea,[tabindex]')){
   if(e.disabled) continue; const t=e.getAttribute('tabindex');
   if(t!==null && Number(t)<0) continue;
   const s=getComputedStyle(e);
   if(s.display==='none'||s.visibility==='hidden') continue;
   const r=e.getBoundingClientRect();
   if(r.width<=0||r.height<=0) continue;
   n++; }
 return {panelState:p.getAttribute('data-director-mobile-panel-state'),
   focusScope:p.getAttribute('data-director-focus-scope'),
   inert:!!p.inert, reachable:n};}"""

DIAG = """(sel)=>{
 const el=document.querySelector(sel);
 const d=document.querySelector('[role="dialog"][aria-modal="true"]');
 const st=window.__libtv_store?window.__libtv_store.getState():null;
 const vp=st&&st.getActiveCanvas?st.getActiveCanvas().viewport:null;
 if(!el) return {missing:true, vw:innerWidth, dialogOpen:!!d, storeViewport:vp};
 const r=el.getBoundingClientRect();
 const cx=Math.round(r.x+r.width/2), cy=Math.round(r.y+r.height/2);
 const node=el.closest?el.closest('.react-flow__node'):null;
 const nr=node?node.getBoundingClientRect():null;
 const inView=(cx>1&&cy>1&&cx<innerWidth-1&&cy<innerHeight-1);
 const stack=inView?document.elementsFromPoint(cx,cy).slice(0,5).map(n=>({
   tag:n.tagName,
   cls:(n.getAttribute('class')||'').split(' ').slice(0,2).join('.'),
   isSelf:n===el,
   closestSel:!!(n.closest&&n.closest(sel))})):null;
 return {vw:innerWidth, dialogOpen:!!d, storeViewport:vp,
   rect:{x:Math.round(r.x),y:Math.round(r.y),
         w:Math.round(r.width),h:Math.round(r.height)},
   centerInView:inView, centerStack:stack,
   nodeId:node?node.getAttribute('data-id'):null,
   nodeRect:nr?{x:Math.round(nr.x),y:Math.round(nr.y),
                w:Math.round(nr.width),h:Math.round(nr.height)}:null};}"""

# ★ 树里的**真对象行**（`DirectorObjectTree.tsx:459-464` 的
# `role="treeitem" data-director-object-id/-kind/-selected`）。
# 初版按 `cands[2]` 找，选中的是「解组」那个**动作按钮**，不是对象行，
# 于是「先选中一个对象」这步从一开始就不成立。
OBJECTS = """()=>{const d=document.querySelector(
  '[role="dialog"][aria-modal="true"]');
 const t=d&&d.querySelector('aside[aria-label="场景对象"]');
 if(!t) return {err:'no tree'};
 const out=[];
 for(const e of t.querySelectorAll('[data-director-object-id]')){
   const r=e.getBoundingClientRect();
   if(r.width<=0||r.height<=0) continue;
   const s=getComputedStyle(e);
   if(s.display==='none'||s.visibility==='hidden') continue;
   out.push({id:e.getAttribute('data-director-object-id'),
     kind:e.getAttribute('data-director-object-kind'),
     selected:e.getAttribute('data-director-object-selected'),
     role:e.getAttribute('role'),
     text:(e.textContent||'').trim().slice(0,18),
     x:Math.round(r.x), y:Math.round(r.y),
     w:Math.round(r.width), h:Math.round(r.height)});}
 return out;}"""


def settle(pg, tries=10, gap=250):
    """等 fitView 落定：连续 `tries` 次读 store 视口都相同才算稳。"""
    prev, same = None, 0
    for _ in range(40):
        cur = pg.evaluate("""()=>{const st=window.__libtv_store.getState();
          const v=st.getActiveCanvas().viewport;
          return [v.x,v.y,v.zoom].join('|');}""")
        same = same + 1 if cur == prev else 0
        prev = cur
        if same >= tries:
            return cur
        pg.wait_for_timeout(gap)
    return prev


def load(pg, width):
    """★ 在目标宽度上**直接加载**页面（不再先宽后窄再 fitView）。"""
    pg.set_viewport_size({"width": width, "height": 1000})
    pg.goto(BASE, wait_until="networkidle")
    pg.wait_for_selector(".react-flow__node", timeout=25000)
    pg.wait_for_timeout(1200)
    pg.keyboard.press("Meta+0")
    pg.wait_for_timeout(600)
    settle(pg)
    return {"width": width, "viewportAfterFit": settle(pg)}


def scan(pg, sel):
    return pg.evaluate("""(sel)=>{
      const el=document.querySelector(sel);
      if(!el) return {missing:true};
      const r=el.getBoundingClientRect();
      const hits=[];
      for(let f=0.08; f<=0.95; f+=0.07)
        for(let g=0.08; g<=0.95; g+=0.07){
          const x=Math.round(r.x+r.width*f), y=Math.round(r.y+r.height*g);
          if(x<2||y<2||x>innerWidth-2||y>innerHeight-2) continue;
          const e=document.elementFromPoint(x,y);
          if(e&&e.closest&&e.closest(sel)) hits.push([x,y]);
        }
      const cx=Math.round(r.x+r.width/2), cy=Math.round(r.y+r.height/2);
      const top=(cx>1&&cy>1&&cx<innerWidth-1&&cy<innerHeight-1)
        ?document.elementFromPoint(cx,cy):null;
      return {rect:{x:Math.round(r.x),y:Math.round(r.y),
                    w:Math.round(r.width),h:Math.round(r.height)},
              hitCount:hits.length, point:hits[0]||null,
              centerHit:!!(top&&top.closest&&top.closest(sel)),
              centerTag:top?top.tagName:null};}""", sel)


def click_real(pg, sel, why, tries=3):
    """★ 在目标 rect 内**扫网格找能命中的点**，不要只取中心。

    扫网格找不到任何命中点时**如实记 FAILED** —— 那才是真结论。
    但要把判别读数一起落盘（vw / store 视口 / 中心元素栈 / 节点 rect），
    否则「命中不了」就变成一句无法复查的空话。
    """
    attempts = []
    for _ in range(tries):
        pt = scan(pg, sel)
        attempts.append(pt)
        if pt.get("missing"):
            return {"FAILED": "找不到 %s" % sel, "attempts": attempts}
        if pt.get("point"):
            pg.mouse.click(pt["point"][0], pt["point"][1])
            pg.wait_for_timeout(1100)
            return {"point": pt["point"], "rect": pt["rect"],
                    "hitCount": pt["hitCount"],
                    "centerHit": pt["centerHit"],
                    "attempts": attempts}
        pg.wait_for_timeout(700)          # 让布局稳一稳再扫
    return {"FAILED": "扫网格 %d 次全部命不中" % tries,
            "attempts": attempts, "diag": pg.evaluate(DIAG, sel)}


def open_director(pg, why):
    r = click_real(pg, "[data-open-director]", why)
    if "FAILED" in r:
        # 落盘判别读数后重试一次；规矩不变——不中就是不中，不解释成不可点
        pg.keyboard.press("Meta+0")
        settle(pg)
        retry = click_real(pg, "[data-open-director]", why + "（重试）")
        r = {"FAILED": r["FAILED"], "firstAttempt": r,
             "retry": retry}
        if "FAILED" in retry:
            return r
        r = retry
    try:
        pg.wait_for_selector('[role="dialog"][aria-modal="true"]', timeout=25000)
    except Exception:
        return {"FAILED": "点了但 dialog 没出现", "click": r}
    pg.wait_for_timeout(2400)
    return r


def tab_walk(pg, n):
    seq = []
    for i in range(n):
        pg.keyboard.press("Tab")
        pg.wait_for_timeout(80)
        a = pg.evaluate(ACTIVE)
        seq.append({"after": i, "inDialog": a["inDialog"],
                    "inPanel": a["inPanel"], "tag": a["tag"]})
    esc = [s["after"] for s in seq if s["inDialog"] is False]
    return {"steps": n, "escapedCount": len(esc), "escapedAt": esc,
            "panelsSeen": sorted({s["inPanel"] for s in seq
                                  if s["inPanel"]})}


def run_round(pg, R):
    # ================= ① 移动端抽屉（窄视口）=================
    R["B1_load800"] = load(pg, 800)
    r = open_director(pg, "打开导演台（800）")
    if "FAILED" in r:
        R["FAILED_B1"] = r["FAILED"]
        R["FAILED_B1_detail"] = r
    else:
        R["B1_narrow_baseline"] = pg.evaluate(DESK)
        drawers = []
        for sel, name in (('button[aria-label="打开场景对象"]', "tree"),
                          ('button[aria-label="打开属性面板"]', "inspector")):
            hit = click_real(pg, sel, "打开%s抽屉" % name)
            if "FAILED" in hit:
                drawers.append({"panel": name, **hit})
                continue
            before = pg.evaluate(DESK)
            active = pg.evaluate(ACTIVE)
            panelSel = ('aside[aria-label="%s"]'
                        % ("场景对象" if name == "tree" else "属性"))
            foc = pg.evaluate(FOCUSABLE_IN_PANEL, panelSel)
            tab = tab_walk(pg, 12)
            after = pg.evaluate(DESK)
            pg.keyboard.press("Escape")
            pg.wait_for_timeout(1100)
            closed = pg.evaluate(DESK)
            drawers.append({
                "panel": name, "click": hit, "before": before,
                "focusOnOpen": active, "panelFocusable": foc, "tab": tab,
                "afterEsc": closed,
                "drawerClosedByEsc":
                    closed["open"] is True
                    and ((closed["tree"] or {}).get("state") == "closed"
                         or (closed["inspector"] or {}).get("state") == "closed"),
                "workspaceClosedByEsc": closed["open"] is False,
                "focusAfterEsc": pg.evaluate(ACTIVE)})
            pg.wait_for_timeout(500)
        R["B1_drawers"] = drawers

    # ================= ② 快捷键（桌面视口）=================
    R["B2_load1440"] = load(pg, 1440)
    r2 = open_director(pg, "打开导演台（1440）")
    if "FAILED" in r2:
        R["FAILED_B2"] = r2["FAILED"]
        R["FAILED_B2_detail"] = r2
        return
    R["B2_baseline"] = pg.evaluate(DESK)

    # 先造一个真实的历史条目：icon rail 的「add-camera」加一台机位
    addcam = click_real(pg, '[data-director-rail-entry="add-camera"]',
                        "rail 加机位")
    R["B2_addCamera"] = {"click": addcam, "after": pg.evaluate(DESK)}

    # ★ 快捷键阶梯：初版把 Cmd+Y 排在 Cmd+Shift+Z **之后**，那时 redo 栈本来就是空的，
    #   「没动」恰恰是正确行为 —— 格子是废的，不能拿它下结论。
    #   这版每一步都先造出**有东西可动**的状态。
    def step(keys, name, note):
        before = pg.evaluate(DESK)
        for k in keys:
            pg.keyboard.press(k)
            pg.wait_for_timeout(700)
        after = pg.evaluate(DESK)
        return {"key": name, "note": note,
                "past": [before["historyPast"], after["historyPast"]],
                "future": [before["historyFuture"], after["historyFuture"]],
                "lastCommand": [before["lastCommand"], after["lastCommand"]],
                "moved": (before["historyPast"] != after["historyPast"]
                          or before["historyFuture"] != after["historyFuture"])}

    kb = [
        step(("Meta+z",), "Cmd+Z", "撤销刚加的机位：past 1→0、future 0→1"),
        step(("Meta+y",), "Cmd+Y", "重做：此刻 future 非空，格子有效"),
        step(("Meta+z",), "Cmd+Z", "再造一个「有 future 可重做」的状态"),
        step(("Meta+Shift+z",), "Cmd+Shift+Z", "重做：此刻 future 非空，格子有效"),
    ]
    R["B2_undoRedo"] = kb

    # ★ Delete / Backspace：初版点的是动作按钮（不是对象行），
    #   而且 Backspace 排在 Delete 之后 —— 对象早被删光，「没动」也是正确的。
    #   这版点真对象行，且**每个键都在有新选中时**按。
    def objects():
        return pg.evaluate(OBJECTS)

    def pick_object(j):
        objs = objects()
        if isinstance(objs, dict):
            return {"err": objs}
        if len(objs) <= j:
            return {"err": "对象行不够", "count": len(objs)}
        o = objs[j]
        px, py = o["x"] + o["w"] // 2, o["y"] + o["h"] // 2
        hit = pg.evaluate(HIT, [px, py, "[data-director-object-id]"])
        pg.mouse.click(px, py)
        pg.wait_for_timeout(700)
        after = objects()
        sel = [x["id"] for x in after if x.get("selected") == "true"]
        return {"picked": j, "target": o, "hit": hit,
                "countBefore": len(objs), "countAfter": len(after),
                "selectedAfter": sel}

    objs0 = objects()
    R["B3_objectsSeed"] = objs0
    dels = []
    for key in ("Delete", "Backspace"):
        before = pg.evaluate(DESK)
        pick = pick_object(0)
        mid = pg.evaluate(DESK)
        if "err" in pick:
            # 没有对象行可点：先加一台机位再试
            add = click_real(pg, '[data-director-rail-entry="add-camera"]',
                             "补机位以产生对象行")
            pick = {"fallbackAdd": add, **pick_object(0)}
        pg.keyboard.press(key)
        pg.wait_for_timeout(800)
        after = pg.evaluate(DESK)
        objs_after = objects()
        n_before = len(objs0) if isinstance(objs0, list) else None
        n_after = len(objs_after) if isinstance(objs_after, list) else None
        dels.append({"key": key, "pick": pick,
                     "lastCommand": [before["lastCommand"],
                                     after["lastCommand"]],
                     "changed": before["lastCommand"] != after["lastCommand"],
                     "past": [mid["historyPast"], after["historyPast"]],
                     "future": [mid["historyFuture"], after["historyFuture"]],
                     "objectCount": [n_before, n_after],
                     "objectsAfter": objs_after,
                     "pickedRowNowExists": any(
                         x["id"] == pick.get("target", {}).get("id")
                         for x in objs_after)
                     if isinstance(objs_after, list) else None})
    R["B3_delete"] = dels
    R["B3_objectsAfterAll"] = objects()


def main():
    res = {"batch": 763, "probe": "b", "rounds": []}
    with sync_playwright() as p:
        br = p.chromium.launch()
        pg = br.new_page(viewport={"width": 1440, "height": 1000})
        for _ in range(2):
            R = {}
            run_round(pg, R)
            res["rounds"].append(R)
        br.close()

    def strip(o):
        if isinstance(o, str):
            return re.sub(r"-\d{10,}-[a-z0-9]{6}\b", "-<gen>", o)
        if isinstance(o, dict):
            return {k: strip(v) for k, v in o.items()}
        if isinstance(o, list):
            return [strip(v) for v in o]
        return o

    r1, r2 = res["rounds"][0], res["rounds"][1]
    diff = {k: {"round1": strip(r1.get(k)), "round2": strip(r2.get(k))}
            for k in set(r1) | set(r2) if strip(r1.get(k)) != strip(r2.get(k))}
    res["roundDiff"] = diff
    res["consistent"] = (len(diff) == 0)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")

    print("consistent =", res["consistent"], "| diff =", sorted(diff))
    for tag in ("FAILED_B1", "FAILED_B2"):
        if r1.get(tag):
            print(tag, ":", r1[tag])
    print("--- 移动端抽屉（vw=800）---")
    for d in r1.get("B1_drawers", []):
        if "FAILED" in d:
            print("  ✗", d["panel"], d["FAILED"])
            continue
        pf = d.get("panelFocusable") or {}
        print("  %-10s 打开后 state=%s focus-scope=%s | 焦点 inDialog=%s inPanel=%s"
              " | 面板内可达控件=%s | Tab %s 步逃出 %s | Esc 关抽屉=%s 关导演台=%s"
              % (d["panel"],
                 (d["afterEsc"]["tree"] or {}).get("state") if d["panel"] == "tree"
                 else (d["afterEsc"]["inspector"] or {}).get("state"),
                 pf.get("focusScope"), d["focusOnOpen"]["inDialog"],
                 d["focusOnOpen"]["inPanel"], pf.get("reachable"),
                 d["tab"]["steps"], d["tab"]["escapedCount"],
                 d["drawerClosedByEsc"], d["workspaceClosedByEsc"]))
        print("     Esc 后焦点:", json.dumps(d.get("focusAfterEsc"),
                                             ensure_ascii=False)[:150])
    print("--- 快捷键 ---")
    ac = (r1.get("B2_addCamera") or {}).get("after") or {}
    print("  加机位后 history past=%s future=%s last=%s"
          % (ac.get("historyPast"), ac.get("historyFuture"),
             ac.get("lastCommand")))
    for k in r1.get("B2_undoRedo", []):
        print("  %-14s past %s→%s future %s→%s 动了=%s last=%s"
              % (k["key"], k["past"][0], k["past"][1], k["future"][0],
                 k["future"][1], k["moved"], k["lastCommand"]))
    sp = r1.get("B3_selectProbe") or {}
    print("  选中目标:", json.dumps(sp, ensure_ascii=False)[:160])
    for d in r1.get("B3_delete", []):
        print("  %-10s last %s→%s 变了=%s"
              % (d["key"], d["lastCommand"][0], d["lastCommand"][1],
                 d["changed"]))


if __name__ == "__main__":
    main()
