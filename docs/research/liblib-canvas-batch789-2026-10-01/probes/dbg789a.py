#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 789 探针 —— 「`sIP` 主人 + `sIP` 主人**同时开着**」

## 前三批各测了一个格子，唯独这个没测

| 批 | 组合 | 测到 |
| --- | --- | --- |
| 783 批 | **bubble** + **bubble** | 两个都关（并发） |
| 784 批 | **`sIP`** + **bubble** | 一次 Escape **只关 `sIP` 那个** ⟹ 要按第二次（D1i） |
| 785 批 | （复用 782 raw）**`sIP`** + `sIP`，**纯鼠标** | 同上，纯鼠标路径 |
| ★ 789 批 | ★★ **`sIP`** + **`sIP`** | ★ **从来没测过** |

## 两个主人都长什么样

`src/components/director/DirectorViewport.tsx`：

| 主人 | 门 | effect | `sIP` | 注册 |
| --- | --- | --- | --- | --- |
| 运镜草稿 | `timeline.motionPathDraft` | `:2697` | `:2702` | `:2711` `window.addEventListener("keydown", handleKeyDown, **true**)` |
| 模型库 | `modelLibraryOpen` | `:2734` | `:2744` | `:2748` `window.addEventListener("keydown", closeOnEscape, **true**)` |

★ 两个都是 **window 捕获相位 + `sIP`** ⟹ 同一 target 同一相位下浏览器按
**注册顺序**依次调用 ⟹ **先注册的那个 `sIP` 会把后注册的整个截断**。

## ★★ 但「先注册」**不是**源码顺序 —— 这是本批真正的预测

★ 两个 effect 都是「**状态非空才注册**」（`:2698` 的
`if (!timeline.motionPathDraft) return;`、`:2734` 的
`if (!modelLibraryOpen) return;`）⟹

> **谁后被打开，谁的监听器就后注册、谁就赢。**

⟹ 于是有**两个**方向，各自可 falsify：

| 臂 | 打开顺序 | 预测：第 1 次 Escape 关掉谁 |
| --- | --- | --- |
| ★★ `draftThenLib` | 先造草稿、再开模型库 | ★ **模型库**（后开的赢），草稿**留着** |
| ★ `libThenDraft` | 先开模型库、再造草稿 | ★ 草稿（若可达）；**但可能结构上不可达**，见下 |

## ★ `libThenDraft` 预测**结构上不可达**，而理由来自 785

造草稿必须点时间轴上的 `[data-director-track-draw-trail]` / `…draw-tool` ——
那是**鼠标点击** ⟹ 产生 `pointerdown` ⟹ 模型库的
`document.addEventListener("pointerdown", closeOnOutsidePointerDown)`（`:2747`）
**先把模型库关掉** ⟹ 还没轮到造草稿，模型库已经没了。

★ 而这正是 **C785-2**（「4 个外点关闭**全是 pointer 类** ⟹ 键盘一律绕过」）
的直接推论。⟹ 本批把它当**预测**写下来，让探针去撞。

## 读数

| 读什么 | 怎么读 |
| --- | --- |
| 草稿活着？ | `[data-director-viewport-gizmo-disabled]`（788 已验证它就是 `motionPathDraft !== null`） |
| 模型库开着？ | `[data-director-model-library-trigger]` 的 `aria-expanded` |
| 阶梯跑到没有？ | `[data-director-export-panel]` 在不在（梯次第 2 档就是关它） |
| ★ **桌还在？** | `[role="dialog"][aria-modal="true"]` 存在与否 |

★ 最后一行是**加**上去的：草稿与模型库这两个读数在桌关闭后会一起变 `null`，
**单看它们只能「暗示」桌关了**。而 `aria-modal="true"` 全仓**只有**
`DirectorDesk.tsx:902` 一处（`grep -A2 'role="dialog"' | grep aria-modal`
只命中这一行）⟹ 它是桌的**唯一**锚点，不会被导出面板等冒充。
本批把「桌还在」从**推断**改成**直读**。

★ 阶梯**必须**有一档可关 ⟹ 所以三个臂**都**先把导出面板打开。

## 格数

4 臂 × **3 次按压** × 2 轮 = **24 个按压格**
（第二、三次是刻意的：测「要按几次才能全清」）
"""
import json
import pathlib
import sys
from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent /
                       "liblib-canvas-batch774-2026-10-01" / "probes"))
import dbg774a as A  # noqa: E402

OUT = pathlib.Path(
    "/Users/yangjiefeng/Documents/wubuku/liblib-tv/docs/research/"
    "liblib-canvas-batch789-2026-10-01/raw/vb789a.json")

DRAW = "[data-director-track-draw-trail]"
TOOL = '[data-director-motion-path-draw-tool="pencil"]'
LIB_TRIGGER = "[data-director-model-library-trigger]"
LIB_ADD = "[data-director-model-library-preview-add]"
EXPORT_TRIGGER = "[data-director-export-trigger]"
GIZMO = "[data-director-viewport-gizmo-disabled]"

ARMS = ["draftOnly", "libOnly", "draftThenLib", "libThenDraft"]
PRESSES = 3

READ = """(giz)=>{const g=document.querySelector(giz);
 const lt=document.querySelector('[data-director-model-library-trigger]');
 return {draft: g ? g.getAttribute('data-director-viewport-gizmo-disabled') : null,
   lib: lt ? lt.getAttribute('aria-expanded') : null,
   exportOpen: !!document.querySelector('[data-director-export-panel]'),
   deskOpen: !!document.querySelector('[role="dialog"][aria-modal="true"]')};}"""


def _click(pg, sel):
    s = pg.evaluate(A.SCAN_CLICK, sel)
    if not s.get("pt"):
        return False
    pg.mouse.click(s["pt"][0], s["pt"][1])
    A.settle(pg)
    return True


def make_draft(pg):
    if not _click(pg, DRAW):
        return False, "点不到 %s" % DRAW
    if not pg.evaluate(
            "()=>!!document.querySelector('[data-director-motion-path-menu]')"):
        return False, "路径菜单没开"
    if not _click(pg, TOOL):
        return False, "点不到 %s" % TOOL
    A.settle(pg)
    if pg.evaluate(READ, GIZMO)["draft"] != "true":
        return False, "点了工具但草稿没起来"
    return True, "ok"


def open_lib(pg):
    if not _click(pg, LIB_TRIGGER):
        return False, "点不到模型库触发器"
    if pg.evaluate(READ, GIZMO)["lib"] != "true":
        return False, "模型库没开"
    return True, "ok"


def run_cell(pg, arm):
    A.fresh(pg)
    if not pg.evaluate(
            "()=>!!document.querySelector('[role=\"dialog\"][aria-modal=\"true\"]')"):
        return {"arm": arm, "FAILED": "导演台没打开"}
    setup = []
    # ★ 三个臂**都**先开导出面板 ⟹ 阶梯有一档可关，「阶梯跑到没有」才可判
    if not _click(pg, EXPORT_TRIGGER):
        return {"arm": arm, "FAILED": "点不到导出触发器", "setup": setup}
    r = pg.evaluate(READ, GIZMO)
    setup.append({"phase": "exportOpen", "read": r})
    if not r["exportOpen"]:
        return {"arm": arm, "FAILED": "导出面板没开", "setup": setup}

    need_draft = arm in ("draftOnly", "draftThenLib", "libThenDraft")
    need_lib = arm in ("libOnly", "draftThenLib", "libThenDraft")
    if need_draft and need_lib and arm == "draftThenLib":
        ok, why = make_draft(pg)
        setup.append({"phase": "makeDraft", "ok": ok, "why": why})
        if not ok:
            return {"arm": arm, "FAILED": "造不出草稿", "setup": setup}
        ok, why = open_lib(pg)
        setup.append({"phase": "openLib", "ok": ok, "why": why})
        if not ok:
            return {"arm": arm, "FAILED": "开不了模型库", "setup": setup}
    elif need_draft and need_lib and arm == "libThenDraft":
        ok, why = open_lib(pg)
        setup.append({"phase": "openLib", "ok": ok, "why": why})
        if not ok:
            return {"arm": arm, "FAILED": "开不了模型库", "setup": setup}
        ok, why = make_draft(pg)
        # ★ 关键：预测「造草稿那一步会把模型库关掉」
        after = pg.evaluate(READ, GIZMO)
        setup.append({"phase": "makeDraft", "ok": ok, "why": why,
                      "libAfterAttempt": after["lib"],
                      "draftAfterAttempt": after["draft"]})
        if after["lib"] != "true":
            return {"arm": arm, "structurallyUnreachable": True,
                    "why": "★ 造草稿时模型库已被外点关闭关掉",
                    "setup": setup, "after": after}
    elif need_draft:
        ok, why = make_draft(pg)
        setup.append({"phase": "makeDraft", "ok": ok, "why": why})
        if not ok:
            return {"arm": arm, "FAILED": "造不出草稿", "setup": setup}
    elif need_lib:
        ok, why = open_lib(pg)
        setup.append({"phase": "openLib", "ok": ok, "why": why})
        if not ok:
            return {"arm": arm, "FAILED": "开不了模型库", "setup": setup}

    start = pg.evaluate(READ, GIZMO)
    setup.append({"phase": "start", "read": start})
    presses = []
    for k in range(1, PRESSES + 1):
        pg.keyboard.press("Escape")
        A.settle(pg)
        presses.append({"press": k, "read": pg.evaluate(READ, GIZMO)})
    return {"arm": arm, "setup": setup, "start": start, "presses": presses}


def main():
    with sync_playwright() as pw:
        b = pw.chromium.launch(headless=True)
        rounds = []
        for rd in range(2):
            rows = []
            for arm in ARMS:
                cell = None
                for t in range(3):
                    pg = b.new_page()
                    pg.set_default_timeout(15000)
                    try:
                        cell = run_cell(pg, arm)
                    except Exception as e:  # noqa: BLE001
                        cell = {"arm": arm,
                                "FAILED": "%s: %s" % (type(e).__name__, e)}
                    finally:
                        try:
                            pg.close()
                        except Exception:  # noqa: BLE001
                            pass
                    cell["tries"] = t + 1
                    if not cell.get("FAILED"):
                        break
                rows.append(cell)
                if cell.get("structurallyUnreachable"):
                    msg = "STRUCT-UNREACHABLE (%s)" % cell["why"]
                elif cell.get("FAILED"):
                    msg = "FAILED:%s" % cell["FAILED"]
                else:
                    msg = " | ".join(
                        "P%d d=%s l=%s e=%s %s"
                        % (p["press"], p["read"]["draft"], p["read"]["lib"],
                           "on" if p["read"]["exportOpen"] else "off",
                           "桌在" if p["read"].get("deskOpen") else "★桌关")
                        for p in cell["presses"])
                print("  round%d %-16s %s" % (rd + 1, arm, msg), flush=True)
            rounds.append({"round": rd + 1, "rows": rows})
        b.close()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"batch": 789, "arms": ARMS,
                               "presses": PRESSES, "rounds": rounds},
                              ensure_ascii=False, indent=1), encoding="utf-8")
    print("wrote %s" % OUT)


if __name__ == "__main__":
    main()
