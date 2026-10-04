#!/usr/bin/env python3
"""batch 764 探针 c：焦点在边界数值框里按 ⌘C，剪贴板到底有没有被换掉？

764b 读到一格反常：焦点停在 `[data-director-transform-field]` 里按 ⌘C，
`lastCommand` 是 **GESTURE_BEGIN** 而不是 COPY_SELECTION。
但 `directorStore.ts:3888-3944` 的 `copyDirectorSelection` **每条分支都会写
lastCommandResult**（COMMITTED / NOOP / REJECTED / STALE 都写 COPY_SELECTION），
所以「读到 GESTURE_BEGIN」有两种解释：

  甲：⌘C 根本没到 `DirectorDesk.tsx:487` 的 window handler（复制没发生）
  乙：到了，但边界 hook 的 `begin()` **异步**落库，把 COPY_SELECTION 又盖回
     GESTURE_BEGIN（复制其实发生了，只是读数被后写覆盖）

读源码判不了（`beginDirectorGesture` 是否异步要看实现细节），**用读数判**：
先复制 A → 在数值框里 ⌘C 复制 B → 粘贴 → 看新对象到底是 **A 的副本还是 B 的副本**。
对象名不会因为复制而改变，所以这一步能把甲/乙分开。

顺带把「空剪贴板粘贴也 stamp PASTE_CLIPBOARD」查清楚：
`data-director-last-disposition` 那个钩子是不是如实写了 NOOP ——
如果写了，那只是「命令标签照写、disposition 如实」，不是缺陷。
"""
import json
import pathlib
from playwright.sync_api import sync_playwright

BASE = "http://localhost:4317"
OUT = pathlib.Path(
    "/Users/yangjiefeng/Documents/wubuku/liblib-tv"
    "/docs/research/liblib-canvas-batch764-2026-10-01/raw/vb764c.json")

DESK = """()=>{const d=document.querySelector('[role="dialog"][aria-modal="true"]');
 if(!d) return {open:false};
 const t=d.querySelector('aside[aria-label="场景对象"]');
 const rows=[];
 if(t) for(const e of t.querySelectorAll('[data-director-object-id]')){
   const r=e.getBoundingClientRect(); if(r.width<=0||r.height<=0) continue;
   rows.push({id:e.getAttribute('data-director-object-id'),
     kind:e.getAttribute('data-director-object-kind'),
     selected:e.getAttribute('data-director-object-selected'),
     text:(e.textContent||'').trim().slice(0,14),
     x:Math.round(r.x), y:Math.round(r.y),
     w:Math.round(r.width), h:Math.round(r.height)});}
 return {open:true, count:rows.length, rows:rows,
   selectedIds:rows.filter(r=>r["selected"]=="true").map(r=>r["id"]),
   historyPast:d.getAttribute('data-director-history-past'),
   lastCommand:d.getAttribute('data-director-last-command')||'',
   lastDisposition:d.getAttribute('data-director-last-disposition')||'',
   activeGesture:d.getAttribute('data-director-active-gesture')||'',
   active:{tag:document.activeElement?document.activeElement.tagName:null,
     tf:document.activeElement?document.activeElement
       .getAttribute('data-director-transform-field'):null,
     ta:document.activeElement?document.activeElement
       .getAttribute('data-director-transform-axis'):null}};}"""

OBJECTS = DESK

FOCUS_FIELD = """()=>{const d=document.querySelector(
  '[role="dialog"][aria-modal="true"]');
 const e=d&&d.querySelector('[data-director-transform-field]');
 if(!e) return {err:'no field'};
 e.focus();
 return {focused:document.activeElement===e,
   tf:e.getAttribute('data-director-transform-field'),
   ta:e.getAttribute('data-director-transform-axis'),
   value:e.value};}"""

SCAN_CLICK = """(sel)=>{const el=document.querySelector(sel);
 if(!el) return {missing:true};
 const r=el.getBoundingClientRect();
 for(let f=0.08; f<=0.95; f+=0.07)
   for(let g=0.08; g<=0.95; g+=0.07){
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
        return {"err": "行不够", "n": len(objs) if isinstance(objs, list)
                else objs}
    o = objs[j]
    x, y = o["x"] + o["w"] // 2, o["y"] + o["h"] // 2
    pg.mouse.click(x, y)
    pg.wait_for_timeout(700)
    st = pg.evaluate(DESK)
    return {"j": j, "target": o, "selectedAfter": st.get("selectedIds")}


def press(pg, k, label):
    before = pg.evaluate(DESK)
    pg.keyboard.press(k)
    pg.wait_for_timeout(900)
    after = pg.evaluate(DESK)
    return {"key": label,
            "count": [before.get("count"), after.get("count")],
            "past": [before.get("historyPast"), after.get("historyPast")],
            "lastCommand": [before.get("lastCommand"),
                            after.get("lastCommand")],
            "lastDisposition": [before.get("lastDisposition"),
                                after.get("lastDisposition")],
            "activeGestureBefore": before.get("activeGesture"),
            "activeGestureAfter": after.get("activeGesture"),
            "active": after.get("active")}


def run_round(pg, R):
    op = load_open(pg)
    R["open"] = op
    if op.get("FAILED_open"):
        return
    R["deskStart"] = pg.evaluate(DESK)
    seed = R["deskStart"]["rows"]
    R["seedNames"] = [{"i": i, "kind": o["kind"], "text": o["text"]}
                      for i, o in enumerate(seed)]

    # ① 空剪贴板先粘贴：disposition 是不是如实写 NOOP
    R["A_emptyPaste"] = press(pg, "Meta+v", "Cmd+V（空剪贴板）")

    # ② 选中第 0 行，从**树**按 ⌘C（对照：这条一定成功，764b 已证）
    R["B_pickA"] = pick(pg, 0)
    R["B_copyFromTree"] = press(pg, "Meta+c", "Cmd+C（焦点在树）")
    R["B_pickA2"] = pick(pg, 0)

    # ③ 选中第 1 行，把焦点挪进边界数值框，再按 ⌘C
    R["C_pickB"] = pick(pg, 1)
    R["C_focusField"] = pg.evaluate(FOCUS_FIELD)
    R["C_copyFromField"] = press(pg, "Meta+c", "Cmd+C（焦点在数值框）")
    # 失焦，让 gesture 收尾
    R["C_pickB2"] = pick(pg, 1)

    # ④ 选中第 2 行，粘贴 —— 新对象是 A 的副本还是 B 的副本？
    R["D_pickC"] = pick(pg, 2)
    R["D_paste"] = press(pg, "Meta+v", "Cmd+V")
    after = pg.evaluate(DESK)
    R["D_rowsAfterPaste"] = after.get("rows")

    # 判决：粘贴出来的新对象名/类型 == A 还是 == B
    seedKinds = [(o["kind"], o["text"]) for o in seed]
    pasted = None
    for row in (after.get("rows") or []):
        if all(row["id"] != s["id"] for s in seed) and row["id"] not in (
                [p["id"] for p in (R["D_pickC"].get("target") and [])]):
            pass
    known = {o["id"] for o in seed}
    newrows = [r for r in (after.get("rows") or [])
               if r["id"] not in known]
    R["D_newRows"] = newrows
    if newrows:
        pasted = (newrows[-1]["kind"], newrows[-1]["text"])
    a_sig = (seed[0]["kind"], seed[0]["text"]) if len(seed) > 0 else None
    b_sig = (seed[1]["kind"], seed[1]["text"]) if len(seed) > 1 else None
    R["D_verdict"] = {
        "pastedSig": pasted,
        "seedA": a_sig, "seedB": b_sig,
        "pastedIsA": pasted == a_sig,
        "pastedIsB": pasted == b_sig,
        "newRowCount": len(newrows),
    }
    print("   粘贴出来的是 %s | A=%s B=%s → 是A=%s 是B=%s"
          % (json.dumps(pasted, ensure_ascii=False),
             json.dumps(a_sig, ensure_ascii=False),
             json.dumps(b_sig, ensure_ascii=False),
             R["D_verdict"]["pastedIsA"], R["D_verdict"]["pastedIsB"]))
    print("   树里 ⌘C → last=%s/%s | 数值框里 ⌘C → last=%s/%s"
          % (R["B_copyFromTree"]["lastCommand"][1],
             R["B_copyFromTree"]["lastDisposition"][1],
             R["C_copyFromField"]["lastCommand"][1],
             R["C_copyFromField"]["lastDisposition"][1]))
    print("   空剪贴板粘贴 → last=%s/%s"
          % (R["A_emptyPaste"]["lastCommand"][1],
             R["A_emptyPaste"]["lastDisposition"][1]))


def main():
    res = {"batch": 764, "probe": "c",
           "question": "焦点在边界数值框里按 ⌘C，剪贴板有没有被换掉？",
           "rounds": []}
    with sync_playwright() as p:
        br = p.chromium.launch()
        pg = br.new_page(viewport={"width": 1440, "height": 1000})
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
    print("\n两轮判决一致 =",
          a.get("D_verdict") == b.get("D_verdict"))
    print("wrote %s" % OUT)


if __name__ == "__main__":
    main()
