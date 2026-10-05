#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 780 探针 A —— **验 D1d 严重度的前提**：「刚在输入框里改完数、顺手删个对象」
这个落点，**到底自不自然**？

## 本批要更正的是 777 的一句**没验过的场景描述**

777 记 D1d（中-高）时写：

> 删除进了历史但 `Cmd+Z` 被 `isEditable` 守卫吞掉……而「刚在输入框里改完数、
> **顺手删个对象**」是很自然的落点。

★ 777 的探针**用的是鼠标点行删除按钮**（`[data-director-delete-object]`，
777 的 R119 就是为此立的：删除动作自己会移走焦点）。所以那句「顺手」**从来没
被测过** —— 它是我为了让缺陷显得严重而写的一句场景描述。

而源码说：`Delete`/`Backspace` 的处理在 `DirectorDesk.tsx:517`，
**排在 `:487` 那道 `isEditable` 守卫之后** ⟹ 焦点停在 `<input>` 上时，
**按 Delete 键什么都不会发生**。

⟹ 若实测确认，则「顺手」不成立：用户必须先用**鼠标**点树上的行删除按钮，
再**点回**控件，再按 `Cmd+Z` ⟹ 那是一条**刻意**的操作序列 ⟹
**D1d 的严重度要下调**（而 D1d 正是驱动 D14 修法授权的那一条）。

## 判别器：沿用 779 的三读数

`window` 上晚注册 keydown 监听器 + **capture 相位**的 document 监听器：

- `cap` = 按键**真的送达了浏览器**（正向对照）
- `win` = 事件有没有到达 window 相位 ⟹ hook 对非 Escape 键只 `begin()`
  不 `stopPropagation`（`:99-107`）⟹ **任何键都该到达 window**

⟹ 所以本批的承重读数**不是** `win`（它对所有键都应为正），而是
**「到达了 window 却什么也没发生」** ⟹ 这正是 `:487` 的签名
（`:550` 的 `preventDefault` 在守卫之后 ⟹ 早退时不生效）。

## 臂

| 臂 | 按什么 | 焦点在哪 | 选中了 | 预测 |
| --- | --- | --- | --- | --- |
| `numberDelete` / `numberBackspace` | `Delete` / `Backspace` | 变换字段（number） | 相机 | **删不掉** |
| `rangeDelete` / `rangeBackspace` | `Delete` / `Backspace` | FOV 滑杆（range） | 相机 | **删不掉** |
| ★ `controlDelete` | `Delete` | 桌内非输入控件 | 道具 | **删得掉**（`:517` 跑） |

★ 对照臂必须**真的删掉一个对象** ⟹ 否则「删不掉」可能只是「探针删不动」。

## 每个臂按 2 次

`Delete` 连按两次是 2 个独立读数 ⟹ 「什么都没发生」不是一个单点观察。
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
    "liblib-canvas-batch780-2026-10-01/raw/vb780a.json")

CAM = A.CAM
MUG = "director-prop-mug"
TREE_BTN = "[data-director-panels-toggle]"
SETTLE = 450
PRESSES = 2
MAX_TRIES = 3

#: 臂 = (键, 焦点落点, 选中的对象)
ARMS = [
    {"id": "numberDelete", "key": "Delete", "sel":
     '[data-director-transform-field][data-director-transform-axis="x"]',
     "oid": CAM},
    {"id": "numberBackspace", "key": "Backspace", "sel":
     '[data-director-transform-field][data-director-transform-axis="x"]',
     "oid": CAM},
    {"id": "rangeDelete", "key": "Delete", "sel": "[data-director-camera-fov]",
     "oid": CAM},
    {"id": "rangeBackspace", "key": "Backspace",
     "sel": "[data-director-camera-fov]", "oid": CAM},
    # ★ 对照臂：非输入落点 ⟹ `:487` 不触发 ⟹ `:517` 应该真的删掉
    {"id": "controlDelete", "key": "Delete", "sel": TREE_BTN, "oid": MUG},
]
ARM_IDS = [a["id"] for a in ARMS]
CONTROL_ARM = "controlDelete"

LISTEN = """()=>{const w=window;
 if(!w.__b780){
   w.__b780={cap:0, win:0, keys:[]};
   document.addEventListener('keydown',(e)=>{w.__b780.cap++;
     w.__b780.keys.push({where:'capture', key:e.key,
       prevented:e.defaultPrevented,
       target:e.target?e.target.tagName:null,
       type:e.target?e.target.getAttribute('type'):null});},true);
   window.addEventListener('keydown',(e)=>{w.__b780.win++;
     w.__b780.keys.push({where:'window', key:e.key,
       prevented:e.defaultPrevented,
       target:e.target?e.target.tagName:null,
       type:e.target?e.target.getAttribute('type'):null});});
 }
 return {installed:true};}"""

READ = """()=>{const b=window.__b780; if(!b) return {err:'no listener'};
 const winKeys=b.keys.filter(k=>k.where==='window');
 const r={cap:b.cap, win:b.win, winEntryCount:winKeys.length,
   keys:b.keys.slice()};
 b.cap=0; b.win=0; b.keys=[]; return r;}"""

ST = """()=>{const q=(n)=>{const e=document.querySelector('['+n+']');
  return e?(e.getAttribute(n)||''):null;};
 const ae=document.activeElement;
 const t=document.querySelector('[data-director-tree]');
 const objs=t?[...t.querySelectorAll('[data-director-object-id]')]:[];
 return {gesture:q('data-director-active-gesture'),
   past:q('data-director-history-past'),
   future:q('data-director-history-future'),
   lastCommand:q('data-director-last-command'),
   lastDisp:q('data-director-last-disposition'),
   deskOpen:!!document.querySelector('[role="dialog"][aria-modal="true"]'),
   focusTag:ae?ae.tagName:null, focusType:ae?ae.getAttribute('type'):null,
   objectCount:objs.length,
   objectIds:objs.map(e=>e.getAttribute('data-director-object-id'))};}"""

FOCUS = """(s)=>{const e=document.querySelector(s);
 if(!e) return {err:'no el'};
 if(e.disabled) return {err:'disabled'};
 e.focus({preventScroll:true});
 return {ok:document.activeElement===e, value:e.value,
   type:e.getAttribute('type')};}"""


def run_cell(pg, arm):
    R = {"arm": arm["id"], "key": arm["key"], "selector": arm["sel"],
         "oid": arm["oid"], "presses": []}
    r = A.fresh(pg)
    if r.get("FAILED"):
        R["FAILED"] = "导演台没开"
        return R
    A.click_tree_row(pg, arm["oid"])
    A.settle(pg)
    sel = (pg.evaluate(A.TREE) or {}).get("selectedIds") or []
    if arm["oid"] not in sel:
        R["FAILED"] = "选中没落在 %s（实为 %r）" % (arm["oid"], sel)
        return R
    pg.evaluate(LISTEN)
    f = pg.evaluate(FOCUS, arm["sel"])
    A.settle(pg)
    R["focus"] = f
    if f.get("err") or not f.get("ok"):
        R["FAILED"] = "聚焦失败：%s" % (f.get("err") or "焦点未落上")
        return R
    before = pg.evaluate(ST)
    R["stateBefore"] = before
    if (before or {}).get("past") != "0":
        R["FAILED"] = ("★ 起始历史不干净（past=%r）—— 不是有效读数"
                       % (before or {}).get("past"))
        return R
    n0 = (before or {}).get("objectCount")
    R["objectsBefore"] = n0
    for i in range(PRESSES):
        pg.keyboard.press(arm["key"])
        pg.wait_for_timeout(SETTLE + 150)
        s = pg.evaluate(ST)
        R["presses"].append({
            "n": i + 1, "read": pg.evaluate(READ), "state": s,
            # ★ 直接算出来，比让汇编器反推更不容易搞错
            "objectsBefore": n0, "objectsAfter": s.get("objectCount"),
            "objectsDropped": (n0 - (s.get("objectCount") or 0)),
            "oidStillThere": arm["oid"] in (s.get("objectIds") or []),
        })
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
            print("   %-18s FAILED(试 %s): %s"
                  % (r["arm"], r.get("tries"), r["FAILED"][:50]))
            continue
        print("   %-18s 按=%-10s 焦点=%-7s 起始对象=%s 手势=%s"
              % (r["arm"], r["key"], r["focus"].get("type"),
                 r.get("objectsBefore"),
                 "有" if (r["stateBefore"] or {}).get("gesture") else "空"))
        for p in r["presses"]:
            rd, s = p["read"], p["state"]
            print("        第%d次 cap=%s win=%s ｜ 对象 %s→%s（少了 %s）｜ "
                  "%s 还在=%-5s ｜ past=%s lastCommand=%s"
                  % (p["n"], rd.get("cap"), rd.get("win"),
                     p.get("objectsBefore"), p.get("objectsAfter"),
                     p.get("objectsDropped"), r.get("oid"),
                     p.get("oidStillThere"), s.get("past"),
                     s.get("lastCommand")))


def main():
    res = {
        "batch": 780, "probe": "a",
        "question": "焦点在检查器 gesture 控件上时，Delete/Backspace **到底删不删得掉"
                    "对象**？——这决定 777 说的「顺手删个对象」是不是真的顺手",
        "whyItMatters": "★ 777 记 D1d（中-高）时写「刚在输入框里改完数、顺手删个"
                        "对象是很自然的落点」，但它的探针**用的是鼠标点行删除按钮**"
                        "（R119 就是为此立的）⟹ 那句「顺手」**从没被测过**。",
        "sourcePrediction": "`Delete`/`Backspace` 的处理在 `DirectorDesk.tsx:517`，"
                            "**排在 `:487` 的 `isEditable` 守卫之后** ⟹ 焦点停在 "
                            "`<input>` 上时按 Delete **什么都不会发生**。",
        "discriminator": "沿用 779 的三读数（capture 正向对照 + window 相位）。"
                         "★ 本批承重的**不是** `win`（hook 对非 Escape 键只 "
                         "`begin()` 不 `stopPropagation`（`:99-107`）⟹ 任何键都该"
                         "到达 window），而是**「到达了 window 却什么也没发生」**"
                         "⟹ 这正是 `:487` 的签名（`:550` 的 `preventDefault` 在"
                         "守卫之后 ⟹ 早退时不生效）。",
        "controlArm": "★ `controlDelete`：非输入落点 ⟹ `:487` 不触发 ⟹ `:517` "
                      "**必须真的删掉一个对象**。没有它，「删不掉」可能只是"
                      "「探针删不动」。",
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
