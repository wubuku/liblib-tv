#!/usr/bin/env python3
"""batch 764 探针 b：导演台自己的 ⌘C / ⌘V（763 明确留下的空白）

763 验了 ⌘Z / ⌘⇧Z / ⌘Y / Delete / Backspace，**⌘C / ⌘V 没测** ——
理由是「要先造出可复制的选择」。本探针把那一步做出来，顺带回答四个
没人问过的问题：

① ⌘C / ⌘V 到底改不改历史、lastCommand 叫什么（源码里是
   `copyDirectorSelection` / `pasteDirectorClipboard`）
② **空剪贴板粘贴**会不会凭空造出对象（先按 ⌘V 再按 ⌘C 的顺序）
③ 连续两次 ⌘V 是不是每次都造一个新对象
④ 鼠标等价物（`DirectorObjectTree.tsx:384/394/404` 的
   `data-director-selection-action=copy/delete/clear`）与快捷键**行为是否一致**
   —— 不一致的话键盘和鼠标就是两套语义

外加一格交叉检查：**焦点在手势边界数值框里时按 ⌘C** 会怎样。
D1 那个边界（`useDirectorGestureBoundary.ts:92-108`）只对 Escape
preventDefault，其他键只 `begin()` 不拦 ⟹ 预期 ⌘C 仍然生效。
如果这里不生效，就是 D1 的第二个后果，必须记。
"""
import json
import pathlib
from playwright.sync_api import sync_playwright

BASE = "http://localhost:4317"
OUT = pathlib.Path(
    "/Users/yangjiefeng/Documents/wubuku/liblib-tv"
    "/docs/research/liblib-canvas-batch764-2026-10-01/raw/vb764b.json")

DESK = """()=>{const d=document.querySelector('[role="dialog"][aria-modal="true"]');
 if(!d) return {open:false};
 const t=d.querySelector('aside[aria-label="场景对象"]');
 const tb=d.querySelector('[data-director-selection-toolbar]');
 const rows=[];
 if(t) for(const e of t.querySelectorAll('[data-director-object-id]')){
   const r=e.getBoundingClientRect(); if(r.width<=0||r.height<=0) continue;
   rows.push({id:e.getAttribute('data-director-object-id'),
     kind:e.getAttribute('data-director-object-kind'),
     selected:e.getAttribute('data-director-object-selected'),
     text:(e.textContent||'').trim().slice(0,16)});}
 return {open:true, count:rows.length, rows:rows,
   selectedIds:rows.filter(r=>r["selected"]=="true").map(r=>r["id"]),
   toolbar:tb?{kind:tb.getAttribute('data-director-selection-kind'),
     actions:[...tb.querySelectorAll('[data-director-selection-action]')]
       .map(b=>b.getAttribute('data-director-selection-action')),
     visible:getComputedStyle(tb).display!=='none'}:null,
   historyPast:d.getAttribute('data-director-history-past'),
   historyFuture:d.getAttribute('data-director-history-future'),
   lastCommand:d.getAttribute('data-director-last-command')||'',
   activeGesture:d.getAttribute('data-director-active-gesture')||'',
   active:{tag:document.activeElement?document.activeElement.tagName:null,
     type:document.activeElement?document.activeElement.getAttribute('type'):null,
     tf:document.activeElement?document.activeElement
       .getAttribute('data-director-transform-field'):null,
     ta:document.activeElement?document.activeElement
       .getAttribute('data-director-transform-axis'):null}};}"""

OBJECTS = """()=>{const d=document.querySelector(
  '[role="dialog"][aria-modal="true"]');
 const t=d&&d.querySelector('aside[aria-label="场景对象"]');
 if(!t) return {err:'no tree'};
 const rows=[];
 for(const e of t.querySelectorAll('[data-director-object-id]')){
   const r=e.getBoundingClientRect(); if(r.width<=0||r.height<=0) continue;
   rows.push({id:e.getAttribute('data-director-object-id'),
     kind:e.getAttribute('data-director-object-kind'),
     selected:e.getAttribute('data-director-object-selected'),
     x:Math.round(r.x), y:Math.round(r.y),
     w:Math.round(r.width), h:Math.round(r.height)});}
 return rows;}"""

SCAN_CLICK = """(sel)=>{const el=document.querySelector(sel);
 if(!el) return {missing:true};
 const r=el.getBoundingClientRect();
 for(let f=0.08; f<=0.95; f+=0.07)
   for(let g=0.08; g<=0.95; g+=0.07){
     const x=Math.round(r.x+r.width*f), y=Math.round(r.y+r.height*g);
     if(x<2||y<2||x>innerWidth-2||y>innerHeight-2) continue;
     const e=document.elementFromPoint(x,y);
     if(e&&e.closest&&e.closest(sel)) return {pt:[x,y],
       rect:{x:Math.round(r.x),y:Math.round(r.y),
             w:Math.round(r.width),h:Math.round(r.height)}};}
 return {noHit:true, rect:{x:Math.round(r.x),y:Math.round(r.y),
   w:Math.round(r.width),h:Math.round(r.height)}};}"""

HIT = """(a)=>{const e=document.elementFromPoint(a[0],a[1]);
 if(!e) return {tag:null, ok:false};
 const t=e.closest(a[2]);
 return {tag:e.tagName, ok:!!t, aria:t?t.getAttribute('aria-label'):null};}"""


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
    pg.set_viewport_size({"width": 1440, "height": 1000})
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
    return {"opened": True}


def pick(pg, j):
    objs = pg.evaluate(OBJECTS)
    if not isinstance(objs, list) or len(objs) <= j:
        return {"err": "对象行不够", "count": len(objs) if
                isinstance(objs, list) else objs}
    o = objs[j]
    x, y = o["x"] + o["w"] // 2, o["y"] + o["h"] // 2
    hit = pg.evaluate(HIT, [x, y, "[data-director-object-id]"])
    pg.mouse.click(x, y)
    pg.wait_for_timeout(700)
    st = pg.evaluate(DESK)
    return {"picked": j, "target": o, "hit": hit,
            "selectedAfter": st.get("selectedIds"),
            "toolbar": st.get("toolbar")}


def key(pg, k, label, note=""):
    before = pg.evaluate(DESK)
    pg.keyboard.press(k)
    pg.wait_for_timeout(800)
    after = pg.evaluate(DESK)
    return {"key": label, "note": note,
            "count": [before.get("count"), after.get("count")],
            "selectedBefore": before.get("selectedIds"),
            "selectedAfter": after.get("selectedIds"),
            "past": [before.get("historyPast"), after.get("historyPast")],
            "future": [before.get("historyFuture"),
                       after.get("historyFuture")],
            "lastCommand": [before.get("lastCommand"),
                            after.get("lastCommand")],
            "activeGestureBefore": before.get("activeGesture"),
            "activeGestureAfter": after.get("activeGesture"),
            "countDelta": ((after.get("count") or 0)
                           - (before.get("count") or 0)),
            "historyDelta": (int(after.get("historyPast") or 0)
                             - int(before.get("historyPast") or 0))}


def click_action(pg, action):
    sel = '[data-director-selection-action="%s"]' % action
    s = pg.evaluate(SCAN_CLICK, sel)
    if not s.get("pt"):
        return {"FAILED": s, "sel": sel}
    before = pg.evaluate(DESK)
    pg.mouse.click(s["pt"][0], s["pt"][1])
    pg.wait_for_timeout(900)
    after = pg.evaluate(DESK)
    return {"action": action, "click": s,
            "count": [before.get("count"), after.get("count")],
            "past": [before.get("historyPast"), after.get("historyPast")],
            "lastCommand": [before.get("lastCommand"),
                            after.get("lastCommand")],
            "selectedAfter": after.get("selectedIds"),
            "countDelta": ((after.get("count") or 0)
                           - (before.get("count") or 0)),
            "toolbarAfter": after.get("toolbar")}


def run_round(pg, R):
    op = load_open(pg)
    R["open"] = op
    if op.get("FAILED_open"):
        return
    R["deskStart"] = pg.evaluate(DESK)
    R["pick0"] = pick(pg, 0)

    # ① 空剪贴板先按 ⌘V（会不会凭空造对象）
    R["C1_pasteWithEmptyClipboard"] = key(
        pg, "Meta+v", "Cmd+V（先不复制）", "空剪贴板粘贴")
    # ② 选中 → ⌘C
    R["C2_pick"] = pick(pg, 0)
    R["C2_copy"] = key(pg, "Meta+c", "Cmd+C", "有选中时复制")
    # ③ 换一行选中 → ⌘V
    R["C3_pickOther"] = pick(pg, 1)
    R["C3_paste"] = key(pg, "Meta+v", "Cmd+V", "复制后换行粘贴")
    # ④ 连按两次 ⌘V
    R["C4_pasteAgain"] = key(pg, "Meta+v", "Cmd+V（第二次）", "连续粘贴")
    # ⑤ 焦点在边界数值框里按 ⌘C（D1 会不会连 ⌘C 也拦掉）
    fld = pg.evaluate("""()=>{const d=document.querySelector(
      '[role="dialog"][aria-modal="true"]');
     const e=d&&d.querySelector('[data-director-transform-field]');
     if(!e) return {err:'no field'};
     e.focus();
     return {focused:document.activeElement===e,
       tf:e.getAttribute('data-director-transform-field'),
       ta:e.getAttribute('data-director-transform-axis')};}""")
    R["C5_focusBoundaryField"] = fld
    R["C5_copyFromField"] = key(pg, "Meta+c", "Cmd+C（焦点在数值框里）",
                                "边界只拦 Escape，预期 ⌘C 仍生效")
    # ⑥ 鼠标等价物
    R["C6_pick"] = pick(pg, 0)
    R["C6_copyButton"] = click_action(pg, "copy")
    R["C6_pickOther"] = pick(pg, 1)
    R["C6_clearButton"] = click_action(pg, "clear")
    R["C6_pickAgain"] = pick(pg, 0)
    R["C6_deleteButton"] = click_action(pg, "delete")
    R["deskEnd"] = pg.evaluate(DESK)

    kb = [R.get(k) for k in ("C1_pasteWithEmptyClipboard", "C2_copy",
                             "C3_paste", "C4_pasteAgain", "C5_copyFromField")]
    kb = [x for x in kb if x]
    R["keyboardSummary"] = {
        "steps": [{"key": x["key"], "countDelta": x["countDelta"],
                   "historyDelta": x["historyDelta"],
                   "lastAfter": x["lastCommand"][1]} for x in kb]}
    print("   键盘：", json.dumps(R["keyboardSummary"]["steps"],
                                ensure_ascii=False))


def main():
    res = {"batch": 764, "probe": "b",
           "question": "导演台的 ⌘C / ⌘V 到底做什么？鼠标等价物一致吗？",
           "rounds": []}
    with sync_playwright() as p:
        br = p.chromium.launch()
        pg = br.new_page(viewport={"width": 1440, "height": 1000})
        try:
            for _ in range(2):
                R = {}
                res["rounds"].append(R)
                print("round %d" % (len(res["rounds"])))
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
    for rd, R in enumerate(res["rounds"], 1):
        print("\n=== r%d ===" % rd)
        for k in ("C1_pasteWithEmptyClipboard", "C2_copy", "C3_paste",
                  "C4_pasteAgain", "C5_copyFromField"):
            x = R.get(k) or {}
            if not x:
                continue
            print("  %-22s 对象数 %s→%s (%+d) past %s→%s last=%s"
                  % (x["key"], x["count"][0], x["count"][1], x["countDelta"],
                     x["past"][0], x["past"][1], x["lastCommand"][1]))
        for k in ("C6_copyButton", "C6_clearButton", "C6_deleteButton"):
            x = R.get(k) or {}
            if "FAILED" in x:
                print("  鼠标 %-14s FAILED %s" % (k, json.dumps(x, ensure_ascii=False)[:120]))
                continue
            print("  鼠标 %-14s 对象数 %s→%s (%+d) past %s→%s last=%s toolbar=%s"
                  % (k, x["count"][0], x["count"][1], x["countDelta"],
                     x["past"][0], x["past"][1], x["lastCommand"][1],
                     json.dumps(x.get("toolbarAfter"), ensure_ascii=False)[:80]))
        print("  起始对象数 %s | 结束 %s" % ((R.get("deskStart") or {}).get("count"),
                                            (R.get("deskEnd") or {}).get("count")))
    print("wrote %s" % OUT)


if __name__ == "__main__":
    main()
