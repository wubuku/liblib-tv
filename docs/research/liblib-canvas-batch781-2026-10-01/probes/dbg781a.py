#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 781 探针 A —— **补上 780 矩阵的最后一行**（`Meta+c` / `Meta+v`），
并回答一个更要紧的问题：**按 780 的判据放行，会不会引入新伤害？**

## 780 留下的洞

780 建立的放行判据是「**该键在该类型上有没有原生兜底**」，
矩阵铺了 `Escape` / `Meta+z` / `Delete` / `Backspace` 四行，
而 `Meta+c` / `Meta+v` 那一行被**显式标注为「本批未测」** ⟹
它是矩阵里唯一没有读数支撑的一行，而判据却已经按它推过一轮。

★ 所以 781 有两件事：
① 把那一行**测出来**；
② 更要紧 —— **验证「放行」这个动作本身安不安全**。

## ② 为什么这是个真问题

780 说「range 上 `Meta+c` 无原生兜底 ⟹ 该放行」。但放行之后，
桌的 `Cmd+C` 分支（`DirectorDesk.tsx:491`）会调 `copyDirectorSelection()`。
如果它写的是**系统剪贴板**，那用户按 `Cmd+C` 就会把系统剪贴板内容
换成导演台内部数据 ⟹ **「修复」变成了新的伤害**，方向正好相反。

★ 查源码得到的答案让这个问题落地：`copyDirectorSelection`
（`src/store/directorStore.ts:3888-3946`）只写**内部**的
`clipboard: DirectorClipboardPacketV1`，
而**整个 director store 里没有任何 `navigator.clipboard` 调用**
（`writeText`/`readText` 一次都没有）⟹ 导演台的复制/粘贴是**完全内部**的。
⟹ **放行不会碰系统剪贴板** ⟹ 判据可以安全地覆盖全部 5 个键。

## ① 预测（从源码逐行推出）

- gesture 臂（number / range × `Meta+c` / `Meta+v`）：事件**到达 window**
  （hook 只拦 Escape）而 `lastCommand` **不出现** `COPY_SELECTION` /
  `PASTE_CLIPBOARD` ⟹ `:487` 吞了 ⟹ **死键且零反馈**
  （`getDirectorCommandFeedback` 只对**非** `COMMITTED` 返回文案 ⟹
  早退时连「被拒绝」都看不到）
- ★ 对照臂（非输入落点）：`Meta+c` 应出现 `COPY_SELECTION`；
  `Meta+v` 在**内部剪贴板为空**时应出现 `PASTE_CLIPBOARD` + **非 COMMITTED**
  ⟹ 而**那恰好是桌自己的反馈路径** ⟹ 差异不是「有没有功能」，
  而是「**静默的死键** vs **有反馈的拒绝**」

## 臂

| 臂 | 按什么 | 焦点在哪 |
| --- | --- | --- |
| `numberCopy` / `numberPaste` | `Meta+c` / `Meta+v` | 变换字段（number） |
| `rangeCopy` / `rangePaste` | `Meta+c` / `Meta+v` | FOV 滑杆（range） |
| ★ `controlCopy` / `controlPaste` | 同上 | 桌内非输入控件 |
"""
import json
import pathlib
import sys
from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent.parent /
                       "liblib-canvas-batch774-2026-10-01" / "probes"))
import dbg774a as A  # noqa: E402

OUT = pathlib.Path(
    "/Users/yangjiefeng/Documents/wubuku/liblib-tv/docs/research/"
    "liblib-canvas-batch781-2026-10-01/raw/vb781a.json")

CAM = A.CAM
TREE_BTN = "[data-director-panels-toggle]"
SETTLE = 450
PRESSES = 2
MAX_TRIES = 3
COPY_CMD = "COPY_SELECTION"
PASTE_CMD = "PASTE_CLIPBOARD"
COPY_KEY = "Meta+c"
PASTE_KEY = "Meta+v"

#: 臂 = (键, 焦点落点)
ARMS = [
    {"id": "numberCopy", "key": COPY_KEY,
     "sel": '[data-director-transform-field]'
            '[data-director-transform-axis="x"]'},
    {"id": "numberPaste", "key": PASTE_KEY,
     "sel": '[data-director-transform-field]'
            '[data-director-transform-axis="x"]'},
    {"id": "rangeCopy", "key": COPY_KEY, "sel": "[data-director-camera-fov]"},
    {"id": "rangePaste", "key": PASTE_KEY, "sel": "[data-director-camera-fov]"},
    {"id": "controlCopy", "key": COPY_KEY, "sel": TREE_BTN},
    {"id": "controlPaste", "key": PASTE_KEY, "sel": TREE_BTN},
]
ARM_IDS = [a["id"] for a in ARMS]
GESTURE_ARMS = [a["id"] for a in ARMS if a["id"].startswith(("number", "range"))]
CONTROL_ARMS = ["controlCopy", "controlPaste"]

LISTEN = """()=>{const w=window;
 if(!w.__b781){
   w.__b781={cap:0, win:0, keys:[]};
   document.addEventListener('keydown',(e)=>{w.__b781.cap++;
     w.__b781.keys.push({where:'capture', key:e.key,
       prevented:e.defaultPrevented,
       target:e.target?e.target.tagName:null,
       type:e.target?e.target.getAttribute('type'):null});},true);
   window.addEventListener('keydown',(e)=>{w.__b781.win++;
     w.__b781.keys.push({where:'window', key:e.key,
       prevented:e.defaultPrevented,
       target:e.target?e.target.tagName:null,
       type:e.target?e.target.getAttribute('type'):null});});
 }
 return {installed:true};}"""

READ = """()=>{const b=window.__b781; if(!b) return {err:'no listener'};
 const winKeys=b.keys.filter(k=>k.where==='window');
 const r={cap:b.cap, win:b.win, winEntryCount:winKeys.length,
   keys:b.keys.slice()}; b.cap=0; b.win=0; b.keys=[]; return r;}"""

ST = """()=>{const q=(n)=>{const e=document.querySelector('['+n+']');
  return e?(e.getAttribute(n)||''):null;};
 const ae=document.activeElement;
 const d=document.querySelector('[role="dialog"][aria-modal="true"]');
 const live=[...(d?d.querySelectorAll('[role="status"],[role="alert"],[aria-live]'):[])];
 const t=document.querySelector('[data-director-tree]');
 const objs=t?[...t.querySelectorAll('[data-director-object-id]')]:[];
 return {gesture:q('data-director-active-gesture'),
   past:q('data-director-history-past'),
   future:q('data-director-history-future'),
   lastCommand:q('data-director-last-command'),
   lastDisp:q('data-director-last-disposition'),
   deskOpen:!!d,
   focusTag:ae?ae.tagName:null, focusType:ae?ae.getAttribute('type'):null,
   objectCount:objs.length,
   liveTexts:live.map(e=>(e.textContent||'').trim()).filter(Boolean)};}"""

FOCUS = """(s)=>{const e=document.querySelector(s);
 if(!e) return {err:'no el'};
 if(e.disabled) return {err:'disabled'};
 e.focus({preventScroll:true});
 return {ok:document.activeElement===e, value:e.value,
   type:e.getAttribute('type')};}"""


def run_cell(pg, arm):
    R = {"arm": arm["id"], "key": arm["key"], "selector": arm["sel"],
         "presses": []}
    r = A.fresh(pg)
    if r.get("FAILED"):
        R["FAILED"] = "导演台没开"
        return R
    A.click_tree_row(pg, CAM)
    A.settle(pg)
    sel = (pg.evaluate(A.TREE) or {}).get("selectedIds") or []
    if CAM not in sel:
        # 对照臂的 Cmd+C 需要一个**非空选中**才不会是 NOOP
        R["selectionAtStart"] = sel
    pg.evaluate(LISTEN)
    f = pg.evaluate(FOCUS, arm["sel"])
    A.settle(pg)
    R["focus"] = f
    if f.get("err") or not f.get("ok"):
        R["FAILED"] = "聚焦失败：%s" % (f.get("err") or "焦点未落上")
        return R
    R["stateBefore"] = pg.evaluate(ST)
    if not (R["stateBefore"] or {}).get("deskOpen"):
        R["FAILED"] = "桌没开"
        return R
    for i in range(PRESSES):
        pg.keyboard.press(arm["key"])
        pg.wait_for_timeout(SETTLE + 150)
        R["presses"].append({"n": i + 1, "read": pg.evaluate(READ),
                             "state": pg.evaluate(ST)})
    return R


def run_round(pg, R):
    R["rows"] = []
    for arm in ARMS:
        r, tries = None, 0
        while tries < MAX_TRIES:
            tries += 1
            try:
                r = run_cell(pg, arm)
            except Exception as e:  # noqa: BLE001
                r = {"arm": arm["id"],
                     "FAILED": "%s: %s" % (type(e).__name__, str(e)[:150])}
            if not r.get("FAILED"):
                break
            pg.wait_for_timeout(900 * tries)
        r["tries"] = tries
        if tries > 1:
            r["retried"] = True
        R["rows"].append(r)


def summarize(R):
    for r in R.get("rows") or []:
        if r.get("FAILED"):
            print("   %-14s FAILED(试 %s): %s"
                  % (r["arm"], r.get("tries"), r["FAILED"][:50]))
            continue
        print("   %-14s 按=%-8s 焦点=%-7s 起始 lastCommand=%s"
              % (r["arm"], r["key"], r["focus"].get("type"),
                 (r["stateBefore"] or {}).get("lastCommand") or "(空)"))
        for p in r["presses"]:
            rd, s = p["read"], p["state"]
            print("        第%d次 cap=%s win=%s ｜ lastCommand=%-16s disp=%-9s "
                  "对象=%s live=%r"
                  % (p["n"], rd.get("cap"), rd.get("win"),
                     s.get("lastCommand") or "(空)", s.get("lastDisp") or "(空)",
                     s.get("objectCount"), (s.get("liveTexts") or [])[:1]))


def main():
    res = {
        "batch": 781, "probe": "a",
        "question": "780 矩阵最后一行（`Meta+c`/`Meta+v`）在 gesture 控件上到底"
                    "发不发生？以及按 780 的判据**放行**会不会引入新伤害？",
        "whyItMatters": "★ 780 的判据是「该键有无原生兜底 ⟹ 该放行」，而 "
                        "`Meta+c`/`Meta+v` 那一行被**显式标注为未测** ⟹ "
                        "它是矩阵里唯一没有读数支撑的一行，判据却已按它推过一轮。",
        "theSafetyQuestion": "★ 更要紧：放行之后桌的 `Cmd+C` 分支（`:491`）会调 "
                             "`copyDirectorSelection()`。若它写**系统剪贴板** ⟹ "
                             "用户按 `Cmd+C` 会把系统剪贴板内容换成导演台内部数据 "
                             "⟹ **「修复」变成新的伤害**。",
        "sourceAnswer": "`copyDirectorSelection`（`src/store/directorStore.ts:"
                        "3888-3946`）只写**内部**的 `clipboard: "
                        "DirectorClipboardPacketV1`；★ **整个 director store 里"
                        "没有任何 `navigator.clipboard` 调用**（`writeText`/"
                        "`readText` 一次都没有）⟹ 导演台的复制/粘贴**完全内部** ⟹ "
                        "**放行不会碰系统剪贴板** ⟹ 判据可安全覆盖全部 5 个键。",
        "prediction": "gesture 臂（4 臂 × 2 次）事件**到达 window** 而 "
                      "`lastCommand` **不出现** `COPY_SELECTION`/"
                      "`PASTE_CLIPBOARD` ⟹ `:487` 吞了 ⟹ **死键且零反馈**；"
                      "★ 对照臂 `Meta+c` 应出现 `COPY_SELECTION`、`Meta+v` 在"
                      "内部剪贴板为空时应出现 `PASTE_CLIPBOARD` + **非 COMMITTED** "
                      "⟹ 那正是桌自己的反馈路径 ⟹ 差异是「静默死键」"
                      "vs「**有反馈的拒绝**」。",
        "rounds": [],
    }
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
            except Exception:  # noqa: BLE001
                pass
            OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1),
                           encoding="utf-8")
            print("（已落盘）")
    print("wrote %s" % OUT)


if __name__ == "__main__":
    main()
