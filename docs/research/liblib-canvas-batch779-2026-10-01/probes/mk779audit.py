#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 779 汇编器 —— **验 776 授权修法 (a) 的依据本身**，结果把「两处」变成「三个问题」

## 本批验的不是产品，是一条**授权依据**

776 测到：焦点在 gesture 控件上时，第 1 次 Escape 清掉手势而面板与桌都没关，
第 2、3 次毫无作用。据此更正 C776-1 为「**只改 (a) = 按两次；两处都改 = 按一次**」，
并授权修法 (a) = 在 `useDirectorGestureBoundary.ts:93` 加
`if (!activeRef.current) return;`。

★ **776 从没问「第 2/3 次到底被谁吞掉」。** 我 779 规划时的假设是：
第 2 次按压时**焦点仍在 `<input>` 上** ⟹ `DirectorDesk.tsx:487` 的 `isEditable`
守卫**也会**吞掉它 ⟹ 若真因是守卫，则修法 (a) **碰不到** ⟹ 对用户可见行为净为零。

## 判别器：三个读数（不需要注入）

`window` 上**晚注册**一个 keydown 监听器 + 一个 **capture 相位**的 document 监听器：

| 读数 | 含义 |
| --- | --- |
| `cap` | 按键**真的送达了浏览器**（capture 相位任何 `stopPropagation` 都拦不住） |
| `win` | 有没有东西在到达 `window` 之前就把事件拦下了 |
| `winEntryCount` | `keys` 里 `where==='window'` 的条目数（`win>0` 但它是 0 ⟹ 键不是 Escape） |

## 三个臂，三个机制

| 臂 | 按什么 | 焦点在哪 | 测什么 |
| --- | --- | --- | --- |
| `gestureNumber` / `gestureRange` | `Escape` | gesture 控件（number/range） | **第一道吞嘴**：hook 的 `:94-95` |
| `controlNonInput` | `Escape` | 桌内非输入控件 | **鉴别力对照**：阶梯该跑起来 |
| ★ `modifierNonEscape` | `Meta+z` | gesture 控件 | **第二道吞嘴**：hook 对非 Escape **不** `stopPropagation` ⟹ 事件一定到 window ⟹ 若 undo 仍不发生，那就是 `:487` |

## 结论：**两处**不够，是**三个问题**

实测把「两处」拆成三样，而且**最要紧的那一样不是缺陷、是产品决定**：

1. **第一道吞嘴** = hook `:94-95` 的无条件 `preventDefault` + `stopPropagation`
   （6/6 次按压 `win=0` ⟹ 从没到达 window）⟹ **776 的机制归属是对的**。
2. **第二道吞嘴** = 桌 `:487` 的 `isEditable` 守卫
   （`Meta+z` 臂 `win=2` 到达了 window，而 `lastCommand` 仍不是 `UNDO`）
   ⟹ **修法 (a) 单独做对用户可见行为净为零** ⟹ **776 的「(a) 可单独做」不成立**。
3. ★ **第三样 = 桌的阶梯 `:553` 自己就有一档 `activeGesture`** ⟹
   即使前两道都让路，第 1 次按压**仍然只会取消手势**、不会关掉导出面板 ⟹
   **「按一次就关掉面板」不是任何 (a)+(b) 组合能达成的**，它需要先决定
   「有活动手势时 Escape 要不要也关层」。**这是产品决定，不是机械修法。**

## 与 778 独立汇合

778 从另一条路得到同一结论：`:487` 在 number 族上是**承重墙**、不能整体去掉
⟹ 修法必须**按控件类型分流**，先例 = `useDirectorGestureBoundary.ts:82-90`。
779 则给出分流之所以**必要**的机制理由。
"""
import hashlib
import json
import pathlib
import re

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent.parent.parent.parent
BATCH = REPO / "docs/research/liblib-canvas-batch779-2026-10-01"
OUT = BATCH / "runtime-audit.json"
RAW = BATCH / "raw/vb779a.json"
RAW778 = REPO / "docs/research/liblib-canvas-batch778-2026-10-01/raw/vb778a.json"

CAM = "director-camera-main"
META = {"tries", "retried"}
GESTURE_RX = re.compile(r"director-gesture-\d+-(\d+)")
ESC_ARMS = ["gestureNumber", "gestureRange"]
CONTROL_ARM = "controlNonInput"
MOD_ARM = "modifierNonEscape"
ARMS = ESC_ARMS + [CONTROL_ARM, MOD_ARM]
PRESSES = 3


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


def src_text(rel):
    p = REPO / rel
    if not p.exists():
        raise SystemExit("FATAL 缺源码 %s" % rel)
    return p.read_text(encoding="utf-8")


def blank_comments(s):
    """注释抹白而不删（行号不漂移）。★ 只抹注释，不抹字符串（R107）。"""
    out = list(s)
    i, n, state = 0, len(s), None
    while i < n:
        c = s[i]
        nxt = s[i + 1] if i + 1 < n else ""
        if state is None:
            if c == "/" and nxt == "/":
                state = "line"
                out[i] = out[i + 1] = " "
                i += 2
                continue
            if c == "/" and nxt == "*":
                state = "block"
                out[i] = out[i + 1] = " "
                i += 2
                continue
        elif state == "line":
            if c == "\n":
                state = None
            else:
                out[i] = " "
        else:
            if c == "*" and nxt == "/":
                out[i] = out[i + 1] = " "
                state = None
                i += 2
                continue
            if c != "\n":
                out[i] = " "
        i += 1
    return "".join(out)


def norm(x):
    if isinstance(x, dict):
        return {k: norm(v) for k, v in x.items()}
    if isinstance(x, list):
        return [norm(v) for v in x]
    if isinstance(x, str):
        return GESTURE_RX.sub(r"director-gesture-<TS>-\1", x)
    return x


def strip(rows):
    if isinstance(rows, dict):
        return {k: v for k, v in rows.items() if k not in META}
    return [{k: v for k, v in r.items() if k not in META} for r in (rows or [])]


def reading(row):
    """臂的**标签**不是读数，同格/同臂比较时必须剔掉。"""
    r = {k: v for k, v in row.items() if k not in META}
    r.pop("arm", None)
    return r


# ═══════════════ 1. 原始读数 ═══════════════
raw = json.loads(RAW.read_text(encoding="utf-8"))
rounds = raw["rounds"]
assert len(rounds) == 2, "轮数不是 2"

arms = {}
for rd in rounds:
    for r in strip(rd.get("rows")):
        arms.setdefault(r.get("arm"), []).append(norm(r))
assert set(arms) == set(ARMS), "臂集合不符：%r" % sorted(arms)
bad = [(k, v[0].get("FAILED")) for k, v in arms.items() if v[0].get("FAILED")]
assert not bad, "★ 有 FAILED：%r" % bad
for k, rs in arms.items():
    assert len(rs) == 2, "%s 只跑了 %d 轮" % (k, len(rs))
    assert reading(rs[0]) == reading(rs[1]), "%s 两轮不一致" % k
nPresses = len(arms) * PRESSES
print("（阶段一）%d 轮 × %d 臂 × %d 次按压 = %d 格，零 FAILED，两轮逐字段一致"
      % (len(rounds), len(ARMS), PRESSES, nPresses))

# 每格自证：按键真的送达了（正向对照）
for k, rs in arms.items():
    c = rs[0]
    assert (c.get("focus") or {}).get("ok") is True, "%s 聚焦没落上" % k
    assert (c.get("readOnFocus") or {}).get("cap") == 0, \
        "%s 聚焦后 capture 计数不为 0 ⟹ 上一格的按键还残留" % k
    assert (c.get("stateOnFocus") or {}).get("exportPanel") is True, \
        "★ %s 导出面板没开 ⟹ 阶梯的 :557 那档没有目标，不是有效读数" % k
    for p in c.get("presses") or []:
        rd = p.get("read") or {}
        assert (rd.get("cap") or 0) >= 1, (
            "★ %s 第 %s 次 capture=%r ⟹ 按键压根没送达浏览器 ⟹ "
            "「没到达 window」这个读数没有鉴别力"
            % (k, p.get("n"), rd.get("cap")))

# ═══════════════ 2. 读数（从源码逐行推出的预测） ═══════════════
# ── 预测 A（第一道吞嘴）：Escape 打在 gesture 控件上，hook 的 `:94-95`
#    无条件 `preventDefault` + `stopPropagation` ⟹ **事件从没到达 window**。
firstSwallow = {}
for arm in ESC_ARMS:
    c = arms[arm][0]
    per = []
    for p in c["presses"]:
        rd, st = p["read"], p["state"]
        per.append({
            "n": p["n"], "cap": rd.get("cap"), "win": rd.get("win"),
            "winEntryCount": rd.get("winEntryCount"),
            "prevented": rd.get("prevented"),
            "gesture": st.get("gesture"), "deskOpen": st.get("deskOpen"),
            "exportPanel": st.get("exportPanel"),
            "lastCommand": st.get("lastCommand"),
        })
    firstSwallow[arm] = per
    for e in per:
        assert e["cap"] >= 1, "%s 第%d次 capture 不为正" % (arm, e["n"])
        assert e["win"] == 0, (
            "★ %s 第%d次 win=%r ⟹ 事件**到达了** window ⟹ "
            "「第一道吞嘴是 hook 的 stopPropagation」这条推理不成立，"
            "真因另有其人" % (arm, e["n"], e["win"]))
nFirst = sum(1 for arm in ESC_ARMS for e in firstSwallow[arm]
             if e["win"] == 0)
assert nFirst == len(ESC_ARMS) * PRESSES, \
    "第一道吞嘴只覆盖 %d/%d 次按压" % (nFirst, len(ESC_ARMS) * PRESSES)
# ⟹ **776 的机制归属是对的**：第 2/3 次确实是被 hook 吞的。
#    但这只说明「第一道是谁」，**不能**推出「去掉它之后桌就接得住」。

# ── 预测 B（鉴别力对照）：非输入控件上 Escape **应该**跑完整个阶梯 ──
ctrl = arms[CONTROL_ARM][0]
ctrlPer = [{"n": p["n"], "cap": p["read"].get("cap"),
            "win": p["read"].get("win"),
            "winEntryCount": p["read"].get("winEntryCount"),
            "prevented": p["read"].get("prevented"),
            "exportPanel": p["state"].get("exportPanel"),
            "deskOpen": p["state"].get("deskOpen"),
            "lastCommand": p["state"].get("lastCommand")}
           for p in ctrl["presses"]]
for e in ctrlPer:
    assert e["cap"] >= 1, "对照臂第%d次 capture 不为正" % e["n"]
    assert (e["win"] or 0) >= 1, (
        "★ 对照臂第%d次 win=%r ⟹ 事件也没到达 window ⟹ "
        "判别器对「到不到 window」**没有鉴别力**，"
        "上面「第一道吞嘴是 hook」那条就是空的" % (e["n"], e["win"]))
# 阶梯跑起来的可观察后果：第 1 次关导出面板、第 2 次关桌
assert ctrlPer[0]["exportPanel"] is False, (
    "★ 对照臂第 1 次按压后导出面板仍开着 ⟹ 阶梯的 :557 那档没跑到")
assert ctrlPer[1]["deskOpen"] is False, (
    "★ 对照臂第 2 次按压后桌仍开着 ⟹ 阶梯的 :568 那档没跑到")
ladderRan = True
print("（阶段二）第一道吞嘴（hook 的 stopPropagation）：%d/%d 次按压 win=0"
      " ⟹ 776 的机制归属正确｜对照臂 %d/%d 次 win>0 且阶梯跑完"
      "（导出面板→桌）⟹ 判别器有鉴别力"
      % (nFirst, len(ESC_ARMS) * PRESSES,
         sum(1 for e in ctrlPer if (e["win"] or 0) >= 1), len(ctrlPer)))

# ── 预测 C（★ 本批载荷 · 第二道吞嘴）：`Meta+z` 打在 gesture 控件上 ──
#   ⟸ hook 的 `onKeyDown` 只对 Escape 做 `stopPropagation`（`:93-98`），
#      其余键只 `begin()`（`:99-107`）⟹ **事件一定到达 window**；
#   ⟸ 而桌的 `Cmd+Z` 分支（`:506`）排在 `isEditable` 守卫（`:487`）**之后**
#      ⟹ 焦点仍在 `<input>` 上 ⟹ **undo 到不了**。
mod = arms[MOD_ARM][0]
modPer = [{"n": p["n"], "cap": p["read"].get("cap"),
           "win": p["read"].get("win"),
           "winEntryCount": p["read"].get("winEntryCount"),
           "prevented": p["read"].get("prevented"),
           "gesture": p["state"].get("gesture"),
           "lastCommand": p["state"].get("lastCommand"),
           "past": p["state"].get("past"),
           "deskOpen": p["state"].get("deskOpen")}
          for p in mod["presses"]]
for e in modPer:
    assert (e["cap"] or 0) >= 1, "Meta+z 臂第%d次 capture 不为正" % e["n"]
    assert (e["win"] or 0) >= 1, (
        "★ Meta+z 臂第%d次 win=%r ⟹ 事件**没有**到达 window ⟹ "
        "「第二道吞嘴是桌的 :487」这条推理不成立，"
        "真因是 hook 对非 Escape 也拦了（那 :99-107 就得重读）"
        % (e["n"], e["win"]))
    assert e["lastCommand"] != "UNDO", (
        "★ Meta+z 臂第%d次 lastCommand=%r ⟹ 桌的 undo **真的执行了** ⟹ "
        "`:487` 守卫没有拦住，本批的核心结论要重算"
        % (e["n"], e["lastCommand"]))
    assert e["gesture"] not in (None, ""), (
        "Meta+z 臂第%d次手势没了 ⟹ 那一格测的不是「按键没生效」" % e["n"])
secondSwallow = {"reachedWindow": True, "undoRan": False}
print("（阶段二）第二道吞嘴（桌的 :487）：Meta+z %d/%d 次 **到达了 window**"
      " 而 lastCommand 始终不是 UNDO ⟹ 守卫确实把它吞了"
      % (sum(1 for e in modPer if (e["win"] or 0) >= 1), len(modPer)))

# ═══════════════ 3. 静态层 ═══════════════
DD = blank_comments(src_text("src/components/director/DirectorDesk.tsx"))
dl = DD.split("\n")
gb = blank_comments(src_text(
    "src/components/director/useDirectorGestureBoundary.ts")).split("\n")


def all_in(lines, pat):
    rx = re.compile(pat)
    return [n for n, ln in enumerate(lines, 1) if rx.search(ln)]


def first_in(lines, pat, after=0):
    return next((n for n in all_in(lines, pat) if n > after), None)


def last_in(lines, pat):
    """★ 取**末次**出现：同名形状常在别处也有一份（R128②）。"""
    return max(all_in(lines, pat), default=None)


# S1：hook 的 Escape 分支无条件 preventDefault + stopPropagation ⟹ 第一道吞嘴
kdStart = last_in(gb, r"onKeyDown: \(event\) => \{")
kdEnd = next((n for n in all_in(gb, r"^\s*\};?\s*$") if n > (kdStart or 0)),
             len(gb) + 1)
kd = "\n".join(gb[(kdStart or 1) - 1:(kdEnd or 1) - 1])
escStart = first_in(kd.split("\n"), r'event\.key === "Escape"')
escEnd = first_in(kd.split("\n"), r"return;") or 0
escBody = "\n".join(kd.split("\n")[:escEnd]) if escStart else ""
# S2：★ 整个 `onKeyDown` 里 `stopPropagation` **只**出现在 Escape 分支 ⟹
#     非 Escape 键**不会**被拦 ⟹ 预测 C 的前提
kdStopCount = kd.count("stopPropagation")
nonEsc = kd.split("\n")[escEnd:] if escStart else []
nonEscStop = "\n".join(nonEsc).count("stopPropagation")
# S3：桌只挂在 window 的**冒泡**相位 ⟹ 判别器成立（capture 版永远拦不住）
winReg = all_in(dl, r'window\.addEventListener\("keydown"')
winRegCapture = all_in(dl, r'addEventListener\("keydown"[^)]*capture:\s*true')
# S4：`:487` 守卫 早于 `:549` 阶梯闸门 ⟹ 第二道吞嘴在第一道**下游**
guardLine = first_in(dl, r"if \(isEditable\) return;")
ladderGate = first_in(dl, r'if \(event\.key !== "Escape"\) return;')
ladderPrevent = first_in(dl, r"^      event\.preventDefault\(\);",
                         after=ladderGate or 0)
# S5：★ 阶梯的档位顺序：手势 → 导出面板 → 退出跟随 → 关桌
rung = {
    "gesture": first_in(dl, r"history\.activeGesture\) \{", after=ladderGate or 0),
    "export": first_in(dl, r"if \(exportPanelOpen\) \{", after=ladderGate or 0),
    "follow": first_in(dl, r"if \(followTargetId\) \{", after=ladderGate or 0),
    "close": first_in(dl, r"^      closeWorkspace\(\);", after=ladderGate or 0),
}
order = [rung["gesture"], rung["export"], rung["follow"], rung["close"]]
# S6：★ 移动抽屉的 Escape 分支排在守卫**之前**（775 的 C775-2 同仓先例）
mobileDrawer = first_in(dl, r'event\.key === "Escape" && activeMobilePanel')

static = {
    "hookOnKeyDownLine": kdStart,
    "hookEscapeBranchHasPrevent": "preventDefault" in escBody,
    "hookEscapeBranchHasStop": "stopPropagation" in escBody,
    "hookOnKeyDownStopCount": kdStopCount,
    "hookNonEscapeStopCount": nonEscStop,
    "deskWindowKeydownRegs": winReg,
    "deskWindowKeydownCaptureRegs": winRegCapture,
    "guardLine": guardLine, "ladderGate": ladderGate,
    "ladderPreventLine": ladderPrevent,
    "guardBeforeLadder": bool(guardLine and ladderGate
                              and guardLine < ladderGate),
    "ladderRungs": rung, "ladderOrder": order,
    "ladderOrdered": bool(all(order) and order == sorted(order)),
    "mobileDrawerLine": mobileDrawer,
    "mobileDrawerBeforeGuard": bool(mobileDrawer and guardLine
                                    and mobileDrawer < guardLine),
}
assert kdStart is not None, "hook 的 onKeyDown 找不到了"
assert static["hookEscapeBranchHasPrevent"] is True, (
    "★ hook 的 Escape 分支不再 `preventDefault` ⟹ 「第一道吞嘴」要重算")
assert static["hookEscapeBranchHasStop"] is True, (
    "★ hook 的 Escape 分支不再 `stopPropagation` ⟹ 「第一道吞嘴」要重算")
assert kdStopCount == 1 and nonEscStop == 0, (
    "★ `onKeyDown` 里 `stopPropagation` 出现了 %d 次（非 Escape 分支 %d 次）"
    "⟹ 「非 Escape 键会到达 window」这个前提要重算"
    % (kdStopCount, nonEscStop))
assert winReg and not winRegCapture, (
    "★ 桌的 keydown 监听不是「只在 window 冒泡相位」⟹ 判别器的依据要重算"
    "（挂载行 %r，capture 行 %r）" % (winReg, winRegCapture))
assert guardLine is not None and ladderGate is not None, \
    "守卫或阶梯闸门找不到了"
assert static["guardBeforeLadder"] is True, (
    "★ 阶梯闸门排到了守卫**之前** ⟹ 「第二道吞嘴在第一道下游」要重算")
assert all(order), "阶梯档位找不全：%r" % rung
assert static["ladderOrdered"] is True, (
    "★ 阶梯档位顺序变了：%r（手势→导出面板→退出跟随→关桌）" % order)
assert static["mobileDrawerBeforeGuard"] is True, (
    "★ 移动抽屉的 Escape 分支不再排在守卫之前 ⟹ C775-2 的同仓先例断了")
print("（阶段三）静态：hook Escape 分支 prevent+stop=%s（整个 onKeyDown 只 %d 次 "
      "stopPropagation，非 Escape 分支 %d 次）｜桌只挂 window 冒泡 %r｜"
      "守卫 :%s 早于阶梯 :%s｜阶梯档位 %r 有序=%s｜移动抽屉 :%s 在守卫前=%s"
      % (static["hookEscapeBranchHasStop"], kdStopCount, nonEscStop, winReg,
         guardLine, ladderGate, order, static["ladderOrdered"],
         mobileDrawer, static["mobileDrawerBeforeGuard"]))

# ═══════════════ 4. 可比性 ═══════════════
r0 = norm(strip(rounds[0].get("rows")))
r1 = norm(strip(rounds[1].get("rows")))
tries = [r.get("tries", 1) for rd in rounds for r in (rd.get("rows") or [])]
comparability = {
    "rounds": len(rounds), "armsPerRound": len(ARMS),
    "pressesPerArm": PRESSES,
    "allConsistent": [reading(x) for x in r0] == [reading(x) for x in r1],
    "retryPolicy": "每格最多试 3 次（含第一次），900×n 退避；`tries`/`retried` "
                   "记进 raw 但**排除在两轮一致性比较之外**。",
    "retryStats": {"cells": len(tries),
                   "retriedCells": sum(1 for t in tries if t > 1),
                   "maxTries": max(tries) if tries else None},
    "orderIndependence": "★ 承重的读数是 `win`（到达 window 的监听器有没有被调用）"
                         "与 `cap`（按键有没有送达）——**两者都与监听器相对次序无关**。"
                         "而 `prevented` **依赖次序**：应用在状态变化时会重挂 window "
                         "监听器（`:570` 的 effect 依赖 `exportPanelOpen`），新监听器"
                         "被追加到末尾 ⟹ 我的监听器与桌的监听器**相对次序会翻转**。"
                         "实测：对照臂第 1 次 `prevented=1`、第 2 次 `prevented=0` "
                         "**而桌确实关了** ⟹ 那一列不可信，故**不参与任何结论**，"
                         "且 `win=0` 时它是 `null` 而不是 `0`（R113/R121 同族）。",
    "boundary": "★ **本批未改 `src/`，也没有任何注入。** 删除**不涉及**（本批只按 "
                "Escape 与 `Meta+z`）；导出面板由探针点开并由阶梯关掉 ⟹ 不留残留；"
                "**不点**提交/连接/新增机位/导入导出，不做付费或真实生图生视频。",
}
assert comparability["allConsistent"] is True, "★ 两轮不一致"

# ═══════════════ 5. 结论 ═══════════════
judgments = [
    {"id": "J1",
     "text": "★ **776 的机制归属是对的，但它的推论是错的。** 实测 %d/%d 次按压 "
             "`win=0`（事件**从没到达 window**）⟹ 第 2/3 次确实是被 hook 的 "
             "`stopPropagation`（`:95`）吞的，不是桌守卫。"
             "**但「被 hook 吞」推不出「去掉 hook 之后桌就接得住」。**",
     "evidence": "阶段二 预测 A"},
    {"id": "J2",
     "text": "★ **第二道吞嘴直接测到了**：`Meta+z` 打在 gesture 控件上，"
             "hook 对非 Escape 键**只** `begin()`、**不** `stopPropagation`"
             "（`:99-107`）⟹ 事件**到达了 window**（`win>=1`），"
             "而 `lastCommand` **始终不是 `UNDO`**、`past` 不动 ⟹ "
             "**桌的 `:487` 守卫把它吞了。** ⟹ 修法 (a) 单独做：第 2 次按压从"
             "「被 hook 吞」变成「被 `:487` 吞」⟹ **对用户可见行为净为零**。",
     "evidence": "阶段二 预测 C + 阶段三 S1/S2/S4"},
    {"id": "J3",
     "text": "★ **「两处」不够，是三个问题。** 桌的 Escape 阶梯 `:553` "
             "**自己就有一档 `activeGesture`** ⟹ 即使前两道吞嘴都让路，"
             "第 1 次按压**仍然只会取消手势**、不会关掉导出面板。"
             "⟹ **「按一次就关掉面板」不是任何 (a)+(b) 组合能达成的**，"
             "它要先回答一个**产品问题**：「有活动手势时 Escape 要不要也关层」。"
             "**这一样不是缺陷，是决定。**",
     "evidence": "阶段三 S5 + 阶段二 预测 A/B"},
    {"id": "J4",
     "text": "★ **与 778 独立汇合。** 778 从另一条路得到同一结论：`:487` 在 "
             "number 族上是**承重墙**、不能整体去掉 ⟹ 修法必须**按控件类型分流**"
             "（先例 `useDirectorGestureBoundary.ts:82-90`）。779 则给出"
             "「分流之所以必要」的机制理由：不分流的话，**Escape 与 `Cmd+Z` "
             "会被同一道 `:487` 一起拦掉**，而这两件事要的是**相反**的行为。",
     "evidence": "J2 + 778 的 C778-1"},
    {"id": "J5",
     "text": "★ **对照臂证明判别器有鉴别力**：非输入控件上 `%d/%d` 次按压 "
             "`win>=1`，且阶梯**真的跑完**——第 1 次关掉导出面板（`:557`）、"
             "第 2 次关掉桌（`:568`）⟹ 「`win=0`」不是判别器坏了，"
             "而是事件真的没到 window。" % (
                 sum(1 for e in ctrlPer if (e["win"] or 0) >= 1), len(ctrlPer)),
     "evidence": "阶段二 预测 B"},
]
corrections = [
    {"id": "C779-1",
     "targets": ["**776 的 C776-1**：「只改 (a) = 按两次；两处都改 = 按一次」",
                 "**据此授权的修法 (a)**：`useDirectorGestureBoundary.ts:93` "
                 "加 `if (!activeRef.current) return;`（挂起项里被标成「可以单独做」）"],
     "was": "读作「第 2/3 次按压被 hook 吞掉 ⟹ (a) 让 hook 让路 ⟹ 桌就接得住 ⟹ "
            "(a) 单独可做、净效果是「按两次」。",
     "now": "★ **机制归属对，推论错。** 吞掉按压的是**两道**串联的守卫，"
            "不是一道："
            "① hook `:94-95`（实测 %d/%d 次 `win=0`）；"
            "② 桌 `:487`（实测 `Meta+z` 到达 window 而 undo 仍不发生）。"
            "修法 (a) 只动 ① ⟹ **(a) 单独做对用户可见行为净为零**。"
            "⟹ **(a) 不能单独做**，它必须与「`:487` 的分流」一起做；"
            "而 778 已证明 `:487` 不能整体去掉（number 族的原生撤销靠它）"
            "⟹ **两处都要按控件类型分流**，先例 `useDirectorGestureBoundary.ts:82-90`。"
            % (nFirst, len(ESC_ARMS) * PRESSES),
     "evidence": "J1 + J2 + J4"},
    {"id": "C779-2",
     "targets": ["**776 的「两处」这个计数本身**"],
     "was": "读作「Escape 阶梯有两处需要改（hook + 守卫）」。",
     "now": "★ **是三个问题，不是两处。** 桌的阶梯 `:553` **自己就有一档 "
            "`activeGesture`** ⟹ 前两处都改完，第 1 次按压**仍然只取消手势**。"
            "⟹ 「按一次就关掉导出面板」需要**第三个决定**："
            "「有活动手势时 Escape 要不要也关层」。"
            "★ 这一样**不是缺陷而是产品决定** ⟹ 不能和前两样一起当成"
            "「修完这两处就好了」。",
     "evidence": "J3 + 阶段三 S5"},
]
assert [c["id"] for c in corrections] == ["C779-1", "C779-2"]

probeLessons = [
    {"id": "R129", "text": "★ **「第一道是谁」与「去掉它之后会怎样」是两个读数。** "
                            "我 779 规划时把 776 的机制归属当成了充分条件，"
                            "结果预测被否掉：实测证明第 2/3 次**确实**被 hook 吞，"
                            "而这**推不出** (a) 有效——因为**后面还有第二道**。"
                            "⟹ 授权一条修法时，「当前的吞嘴在哪」与"
                            "「修完之后下一个吞嘴会不会接手」必须分别测。"},
    {"id": "R130", "text": "★ **换一个不被拦的键，就能测到后面那道吞嘴。** "
                            "hook 只对 `Escape` 做 `stopPropagation`（`:93-98`），"
                            "其余键只 `begin()`（`:99-107`）⟹ 按 `Meta+z` "
                            "**一定**能穿过 hook 到达 window ⟹ 再看 `lastCommand` "
                            "有没有变成 `UNDO`，就知道**桌**那一侧拦不拦。"
                            "★ 同一个键（Escape）永远只能测到**最前面**那道。"},
    {"id": "R131", "text": "★ **「没触发」与「触发了但没被消费」不能共用一个 0。** "
                            "第一版把 `prevented` 记成 0，而 `win=0` 时它压根没被写过 "
                            "⟹ 「非读数」长得像「未被 preventDefault」。"
                            "改成 `win=0` 时记 **null**。这是 R113/R121 的同族错误。"},
    {"id": "R132", "text": "★ **「晚注册的监听器」不保证每次都最后跑。** "
                            "应用在状态变化时会重挂 window 监听器"
                            "（`DirectorDesk.tsx:570` 的 effect 依赖 "
                            "`exportPanelOpen`），新监听器被**追加到末尾** ⟹ "
                            "我与桌的监听器**相对次序会翻转**。"
                            "实测：对照臂第 1 次 `prevented=1`、第 2 次 "
                            "`prevented=0` **而桌确实关了**。"
                            "⟹ **`defaultPrevented` 那一列不可信**；"
                            "承重的只能是与次序无关的 `cap` / `win`。"},
    {"id": "R133", "text": "★ **按一次 `Meta+z` 会产生 2 个 keydown**"
                            "（`Meta` 与 `z` 各一个）⟹ 计数类读数要按「≥1」判，"
                            "不能按「==1」判；且 `keys` 只记 `Escape` ⟹ "
                            "`win=2` 而 `winEntryCount=0` 是**正常**的，"
                            "不是「读数矛盾」。"},
]
assert [x["id"] for x in probeLessons] == [
    "R129", "R130", "R131", "R132", "R133"]

defects = [
    {"id": "D1g", "severity": "中-高（本批记录 · 授权依据缺陷）",
     "text": "★ **Escape 在 53 个 gesture 控件上被「两道」串联的守卫吞掉，"
             "而修法 (a) 只动其中一道。** 第一道 = "
             "`useDirectorGestureBoundary.ts:94-95` 无条件 `preventDefault` + "
             "`stopPropagation`（实测 %d/%d 次 `win=0`）；第二道 = "
             "`DirectorDesk.tsx:487` 的 `isEditable` 守卫（实测 `Meta+z` "
             "到达 window 而 `lastCommand` 仍非 `UNDO`）。"
             "⟹ 现有授权（(a) 可单独做）**依据不成立**；"
             "且即使两处都改，阶梯 `:553` 的 `activeGesture` 档仍会吃掉第 1 次按压。"
             % (nFirst, len(ESC_ARMS) * PRESSES),
     "evidence": "J1 + J2 + J3"},
]
audit = {
    "batch": 779,
    "topic": "验 776 授权修法 (a) 的依据本身：第 2/3 次按压到底被谁吞掉",
    "generatedBy": "probes/mk779audit.py",
    "sources": {
        "vb779a.json": {"sha16": sha(RAW), "rounds": len(rounds),
                        "armsPerRound": len(ARMS), "pressesPerArm": PRESSES},
        "vb778a.json": {"sha16": sha(RAW778), "usedFor": "交叉引用 778 的 C778-1"},
    },
    "discriminator": {
        "how": "window 上晚注册一个 keydown 监听器 + 一个 **capture 相位**的 "
               "document 监听器。capture 相位任何 `stopPropagation` 都拦不住 ⟹ "
               "`cap` 是「按键真的送达了」的正向对照。",
        "readings": {
            "cap": "按键送达浏览器的次数（正向对照）",
            "win": "到达了 window 相位的监听器次数（承重）",
            "winEntryCount": "`keys` 里 `where=='window'` 的条目数"
                             "（`win>0` 而它是 0 ⟹ 这次按的不是 Escape）",
            "prevented": "★ **不可信**（依赖监听器相对次序），且 `win=0` 时为 null",
        },
        "table": [
            ["cap=1, win=0", "**第一道**：gesture hook 的 `stopPropagation`"],
            ["cap>=1, win>=1, lastCommand≠UNDO",
             "**第二道**：事件到了 window，但被桌的 `:487` 守卫拦下"],
            ["cap=1, win>=1, prevented=1", "桌的阶梯**真的跑了**（对照臂）"],
        ],
        "whyTrustworthy": "★ 承重的 `cap`/`win` **与监听器相对次序无关**；"
                          "`prevented` 依赖次序，已被实测证伪（R132）故不参与结论。",
    },
    "readings": {
        "R-firstSwallow": "Escape 打在 gesture 控件上，%d/%d 次 `win=0`"
                          " ⟹ **776 的机制归属正确**" % (
                              nFirst, len(ESC_ARMS) * PRESSES),
        "R-secondSwallow": "`Meta+z` 打在 gesture 控件上，%d/%d 次 "
                           "**到达 window** 而 `lastCommand` 始终非 `UNDO` "
                           "⟹ **桌的 `:487` 守卫是第二道吞嘴**" % (
                               sum(1 for e in modPer if (e["win"] or 0) >= 1),
                               len(modPer)),
        "R-control": "非输入控件上 %d/%d 次 `win>=1`，阶梯跑完"
                     "（第 1 次关导出面板、第 2 次关桌）⟹ 判别器有鉴别力" % (
                         sum(1 for e in ctrlPer if (e["win"] or 0) >= 1),
                         len(ctrlPer)),
        "R-order": "静态确认阶梯档位有序：手势 :%s → 导出面板 :%s → 退出跟随 :%s "
                   "→ 关桌 :%s" % (rung["gesture"], rung["export"],
                                   rung["follow"], rung["close"]),
    },
    "verdict": {
        "776的机制归属": "**对**（第 2/3 次确实被 hook 的 stopPropagation 吞）",
        "776的推论": "**错** —— 后面还有第二道吞嘴，(a) 单独做净效果为零",
        "「按一次就关掉面板」": "**不是两处改动能做到的** —— 阶梯 `:553` 自己"
                               "有一档 `activeGesture`，需要第三个**产品决定**",
        "与778的汇合": "两批独立得到同一结论：修法必须**按控件类型分流**",
    },
    "comparability": comparability,
    "static": static,
    "firstSwallow": firstSwallow,
    "secondSwallow": secondSwallow,
    "controlArm": ctrlPer,
    "modifierArm": modPer,
    "results": {
        "firstSwallowPresses": nFirst,
        "firstSwallowTotal": len(ESC_ARMS) * PRESSES,
        "secondSwallowReachedWindow": True,
        "secondSwallowUndoRan": False,
        "controlReachedWindow": sum(1 for e in ctrlPer
                                    if (e["win"] or 0) >= 1),
        "controlTotal": len(ctrlPer),
        "ladderOrdered": static["ladderOrdered"],
        "ladderRungs": rung,
        "failedCells": 0,
    },
    "judgments": judgments,
    "corrections": corrections,
    "findings": {
        "F1": "★ 776 的机制归属对、推论错：吞嘴是**两道**串联的。",
        "F2": "★ 第二道吞嘴（桌 `:487`）已直接测到 ⟹ **(a) 不能单独做**。",
        "F3": "★ **「两处」是三个问题**：阶梯 `:553` 自己的 `activeGesture` 档"
              "会吃掉第 1 次按压 ⟹ 「按一次关面板」需要产品决定。",
        "F4": "★ 与 778 独立汇合：修法必须按控件类型分流。",
        "F5": "★ 判别器有鉴别力（对照臂阶梯跑完），且承重读数与次序无关。",
    },
    "probeLessons": probeLessons,
    "defects": defects,
    "srcDiff": "**本批未改 `src/`**（工作区 `src/` 干净）；**没有任何注入**。",
    "rawSha": {"vb779a.json": sha(RAW), "vb778a.json": sha(RAW778)},
    "retryStats": comparability["retryStats"],
    "boundary": comparability["boundary"],
}
OUT.write_text(json.dumps(audit, ensure_ascii=False, indent=1), encoding="utf-8")
print("wrote %s" % OUT)
