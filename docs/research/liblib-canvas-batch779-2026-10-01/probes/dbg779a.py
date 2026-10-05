#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 779 探针 A —— **776 授权修法 (a) 的依据本身**：「按两次」这个结论，
**机制归属对不对**？

## 要验的是 776 的 C776-1，不是产品

776 测到：焦点在 gesture 控件上时，第 1 次 Escape 清掉手势而面板与桌都没关，
**第 2、3 次毫无作用**。据此更正 C776-1：

> 「只改 (a) = 按两次；两处都改 = 按一次」

并授权修法 (a)：在 Escape 分支加 `if (!activeRef.current) return;`。

★ **但 776 从没问「第 2/3 次到底被谁吞掉」。** 而有**两个**候选：

| 候选 | 吞嘴 | 修法 (a) 碰得到吗 |
| --- | --- | --- |
| **(i)** | `useDirectorGestureBoundary.ts:92-98` 的无条件 `preventDefault` + `stopPropagation` | **碰得到**（(a) 就在这个分支里） |
| **(ii)** | `DirectorDesk.tsx:487` 的 `isEditable` 守卫 —— 第 2 次按压时**焦点仍在 `<input>` 上** | **碰不到** |

⟹ 若真因是 (ii)，修法 (a) 对**用户可见行为净为零**（只是把「被 hook 吞」换成
「被桌守卫吞」）⟹ **C776-1 本身是错的**，而它是当前最高优先拍板项的授权依据。

⭐ 而 778 刚好把这个疑点顶到了台面上：`delWhileFocused` 那一臂里，
**删除动作之后重新聚焦控件、`Cmd+Z` 依然被 `:487` 吞掉** —— 证明 `:487`
确实会在**焦点停在 `<input>` 上**时无条件吞掉修饰键。

## 判别器：三读数（不需要注入）

在 `window` 上**晚注册**一个 keydown 监听器（同一个 phase ⟹ 注册顺序决定谁先跑，
应用的 `:570` 先注册 ⟹ 我的后跑），再配一个 **capture 相位**的 document 监听器
（capture 从 document 往下 ⟹ **任何** `stopPropagation` 都拦不住它）：

| 读数 | 含义 |
| --- | --- |
| `captureSeen` | 这一次按键**真的送达了浏览器**（正向对照） |
| `winFired` | 有没有东西在到达 `window` 之前就把事件拦下了 |
| `defaultPrevented` | 事件到达 `window` 时**已被消费**没有 |

⟹ 三个组合把三个候选分开：

| 组合 | 结论 |
| --- | --- |
| `capture=1, win=0` | **(i)** gesture hook 吞的（`stopPropagation` 拦在 React root） |
| `capture=1, win=1, prevented=0` | **(ii)** 桌守卫 `:487` 吞的（`:550` 的 `preventDefault` 在它之后） |
| `capture=1, win=1, prevented=1` | **桌的阶梯真的跑了**（`:550` 已 preventDefault） |

★ 没有 `captureSeen` 的话，「`win=0`」与「按键压根没送达」长得一样（R113/R121 同族）。

## 对照臂：非输入控件

焦点在 `[data-director-panels-toggle]`（桌内**真的能聚焦、且不挂 gesture
handler** 的元素）⟹ 阶梯应该**真的跑起来**（先关导出面板、再关桌）。
没有这一臂，判别器可能整个是坏的 —— 而这正是 774 用过的对照形状。
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
    "liblib-canvas-batch779-2026-10-01/raw/vb779a.json")

CAM = A.CAM
EXPORT_TRIGGER = "[data-director-export-trigger]"
EXPORT_PANEL = "[data-director-export-panel]"
TREE_BTN = "[data-director-panels-toggle]"
SETTLE = 450
PRESSES = 3
MAX_TRIES = 3
FAMS = {
    "number": '[data-director-transform-field]'
              '[data-director-transform-axis="x"]',
    "range": "[data-director-camera-fov]",
}
# 臂 = 焦点落在哪一类元素上 + 按哪个键
ARMS = ["gestureNumber", "gestureRange", "controlNonInput",
        "modifierNonEscape"]
#: 第四臂按**非 Escape** 的修饰键 —— hook 的 `onKeyDown` 只对 Escape
#: 做 `stopPropagation`（`:92-98`），其余键只 `begin()`（`:99-107`）⟹
#: 事件**一定**到达 window ⟹ 若 `lastCommand` 仍不是 `UNDO`，
#: 那就**直接证明**第二道吞嘴是桌的 `:487` 守卫，而不是 hook。
KEYMAP = {
    "gestureNumber": "Escape", "gestureRange": "Escape",
    "controlNonInput": "Escape", "modifierNonEscape": "Meta+z",
}

# ★ 晚注册的 window 监听器（与应用同一个 phase ⟹ 后跑）+ capture 相位正向对照
LISTEN = """()=>{const w=window;
 if(!w.__b779){
   w.__b779={cap:0, win:0, prevented:0, keys:[]};
   document.addEventListener('keydown',(e)=>{
     const b=w.__b779; b.cap++;
     if(e.key==='Escape') b.keys.push({where:'capture', key:e.key,
       prevented:e.defaultPrevented, target:e.target?e.target.tagName:null,
       type:e.target?e.target.getAttribute('type'):null});
   },true);
   window.addEventListener('keydown',(e)=>{
     const b=w.__b779; b.win++;
     if(e.key==='Escape') b.keys.push({where:'window', key:e.key,
       prevented:e.defaultPrevented, target:e.target?e.target.tagName:null,
       type:e.target?e.target.getAttribute('type'):null});
     b.prevented = e.defaultPrevented ? 1 : 0;
   });
 }
 return {installed:true};}"""

# ★ `win=0` 时 `prevented` 必须是 **null** 而不是 0 ——
#   「监听器没跑」与「跑了但事件未被 preventDefault」在同一个 0 里长得一样
#   （R113/R121 同族）。null 让「这是个非读数」在产物里显形。
READ = """()=>{const b=window.__b779; if(!b) return {err:'no listener'};
 const winKeys=b.keys.filter(k=>k.where==='window');
 const r={cap:b.cap, win:b.win,
   prevented: b.win ? (winKeys.length ? (winKeys[0].prevented?1:0) : null) : null,
   winEntryCount: winKeys.length,
   keys:b.keys.slice()}; b.cap=0; b.win=0; b.prevented=0; b.keys=[];
 return r;}"""

ST = """()=>{const q=(n)=>{const e=document.querySelector('['+n+']');
  return e?(e.getAttribute(n)||''):null;};
 const ae=document.activeElement;
 return {gesture:q('data-director-active-gesture'),
   past:q('data-director-history-past'),
   future:q('data-director-history-future'),
   lastCommand:q('data-director-last-command'),
   lastDisp:q('data-director-last-disposition'),
   exportPanel:!!document.querySelector('[data-director-export-panel]'),
   deskOpen:!!document.querySelector('[role=\"dialog\"][aria-modal=\"true\"]'),
   focusTag:ae?ae.tagName:null, focusType:ae?ae.getAttribute('type'):null};}"""

FOCUS = """(s)=>{const e=document.querySelector(s);
 if(!e) return {err:'no el'};
 if(e.disabled) return {err:'disabled'};
 e.focus({preventScroll:true});
 return {ok:document.activeElement===e, value:e.value,
   type:e.getAttribute('type')};}"""


def _open_export(pg):
    s = pg.evaluate(A.SCAN_CLICK, EXPORT_TRIGGER)
    if not s.get("pt"):
        return False
    pg.mouse.click(s["pt"][0], s["pt"][1])
    A.settle(pg)
    return bool(pg.evaluate(ST).get("exportPanel"))


def run_cell(pg, arm):
    R = {"arm": arm, "presses": []}
    r = A.fresh(pg)
    if r.get("FAILED"):
        R["FAILED"] = "导演台没开"
        return R
    A.click_tree_row(pg, CAM)
    A.settle(pg)
    sel = (pg.evaluate(A.TREE) or {}).get("selectedIds") or []
    if CAM not in sel:
        R["FAILED"] = "选中没落在相机（实为 %r）" % (sel,)
        return R
    # ★ 导出面板开着 ⟹ 桌阶梯的 `:557` 那档有目标可关
    if not _open_export(pg):
        R["FAILED"] = "★ 导出面板没打开 ⟹ 这一格不是有效读数"
        return R
    sel_map = {"gestureNumber": FAMS["number"], "gestureRange": FAMS["range"],
               "controlNonInput": TREE_BTN,
               "modifierNonEscape": FAMS["number"]}
    target = sel_map[arm]
    R["selector"] = target
    pg.evaluate(LISTEN)
    f = pg.evaluate(FOCUS, target)
    A.settle(pg)
    R["focus"] = f
    if f.get("err") or not f.get("ok"):
        R["FAILED"] = "聚焦失败：%s" % (f.get("err") or "焦点未落上")
        return R
    R["stateOnFocus"] = pg.evaluate(ST)
    R["readOnFocus"] = pg.evaluate(READ)
    R["key"] = KEYMAP[arm]
    if arm in ("gestureNumber", "gestureRange") and \
            R["stateOnFocus"].get("gesture") in (None, ""):
        R["FAILED"] = "★ 聚焦后没有活动手势 ⟹ 这一格不是有效读数"
        return R
    if arm == "controlNonInput" and \
            R["stateOnFocus"].get("gesture") not in (None, ""):
        R["FAILED"] = "★ 对照臂居然起了手势 ⟹ 对照失效"
        return R
    for i in range(PRESSES):
        pg.keyboard.press(KEYMAP[arm])
        pg.wait_for_timeout(SETTLE + 120)
        R["presses"].append({
            "n": i + 1,
            "read": pg.evaluate(READ),
            "state": pg.evaluate(ST),
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
                r = {"arm": arm,
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
            print("   %-16s FAILED(试 %s): %s"
                  % (r["arm"], r.get("tries"), r["FAILED"][:52]))
            continue
        print("   %-18s 按=%-7s 焦点=%-7s 聚焦后 手势=%-4s 导出面板=%s"
              % (r["arm"], r.get("key"), r["focus"].get("type"),
                 "有" if r["stateOnFocus"].get("gesture") else "空",
                 r["stateOnFocus"].get("exportPanel")))
        for p in r["presses"]:
            rd = p["read"] or {}
            st = p["state"] or {}
            print("        第%d次  capture=%s win=%s win条目=%s prevented=%s ｜ "
                  "手势=%-4s 导出面板=%-5s 桌=%-5s lastCommand=%s"
                  % (p["n"], rd.get("cap"), rd.get("win"),
                     rd.get("winEntryCount"), rd.get("prevented"),
                     "有" if st.get("gesture") else "空",
                     st.get("exportPanel"), st.get("deskOpen"),
                     st.get("lastCommand")))


def main():
    res = {
        "batch": 779, "probe": "a",
        "question": "776 更正 C776-1「只改 (a) = 按两次」的**机制归属**对不对？"
                    "第 2/3 次 Escape 到底被 gesture hook 还是被桌的 isEditable "
                    "守卫吞掉？",
        "whyItMatters": "★ 776 授权修法 (a) 的**唯一依据**就是「2/3 次按压被 "
                        "hook 吞掉」。若真因是 `DirectorDesk.tsx:487` 的 "
                        "`isEditable` 守卫（第 2 次按压时焦点**仍在 `<input>` "
                        "上**），修法 (a) **碰不到它** ⟹ 对用户可见行为净为零 "
                        "⟹ **C776-1 本身错了**。",
        "twoCandidates": {
            "(i) gesture hook": "`useDirectorGestureBoundary.ts:92-98` 的无条件 "
                                "`preventDefault` + `stopPropagation` ⟹ **(a) 碰得到**",
            "(ii) 桌守卫": "`DirectorDesk.tsx:487` 排在 `:550` 的 `preventDefault` "
                           "**之前** ⟹ **(a) 碰不到**",
        },
        "discriminator": "★ 三读数：**capture 相位**的 document 监听器（任何 "
                         "`stopPropagation` 都拦不住 ⟹ 正向对照证明按键送达了）、"
                         "**晚注册**的 window 监听器是否被调用、事件到达 window 时"
                         "的 `defaultPrevented`。"
                         "⟹ `(1,0,*)`=hook 吞；`(1,1,0)`=桌守卫吞；"
                         "`(1,1,1)`=阶梯真跑了。",
        "controlArm": "焦点在 `[data-director-panels-toggle]`（桌内真的能聚焦、"
                      "且**不挂** gesture handler 的元素）⟹ 阶梯应该真跑起来。"
                      "★ 没有它，「win=0」可能只是判别器整个坏了。",
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
