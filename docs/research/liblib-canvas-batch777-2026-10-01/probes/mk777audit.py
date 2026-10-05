#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 777 汇编器 —— 把「删除破坏性且跨 reload 持久化，却无『未保存/重置』提示」
这句**捆在一起**的话，拆成四个独立读数再合议。

## 为什么必须拆

763 的原话把三件事捆成一句：破坏性 / 跨 reload 持久化 / 无提示。
捆着的后果是：**任何一件为真都会让另外两件显得已被处理**。
实测正是这样 —— 「`Cmd+Z` 确实能撤销」差点把「无提示」一起放过。

## 四个读数与它们的合议

| 读数 | 问题 | 实测 |
| --- | --- | --- |
| R-past | 删除进不进历史？ | 进（`past` 0→1） |
| R-undo | 撤销在**哪些落点**上可用？ | **非输入框落点 2/2 可用；输入框落点 0/1** |
| R-persist | 跨 reload 还在吗？ | **在**（4→4，且 `past` 归零） |
| R-affordance | 有没有撤销入口/确认/提示？ | **撤销类控件 0、确认对话框 0、反馈面板显示「无命令反馈」** |

⟹ 合议不是三桶也不是四桶，而是**两桶缺陷 + 两处订正**：

- **不是**「不可逆」（R-undo 在非输入框落点上成立）
- **是**「无入口」（R-affordance = 0，而出路是个**没有任何提示的快捷键**）
- **新缺陷**：输入框落点上撤销**不可用**（R-undo 的那个 0/1）
- **订正**：763 的「破坏性」应改成「无入口」；「无未保存/重置提示」应改成
  「零撤销入口 + 零确认 + 反馈面板显示『无命令反馈』」
"""
import hashlib
import json
import pathlib
import re

HERE = pathlib.Path(__file__).resolve().parent
#: HERE = <repo>/docs/research/<batch>/probes ⟹ 退 **4** 级到仓库根
REPO = HERE.parent.parent.parent.parent
BATCH = REPO / "docs/research/liblib-canvas-batch777-2026-10-01"
OUT = BATCH / "runtime-audit.json"
RAW = BATCH / "raw/vb777a.json"

MUG = "director-prop-mug"
META = {"tries", "retried"}
#: 四个落点。`tree` 是**预期失败**的（落点不可聚焦 ⟹ 与 body 臂重复），
#: 探针的自证会把它判 FAILED —— 汇编器必须**断言这个失败是预期的**，
#: 否则「少一格」与「多一格重复」会互相冒充。
LANDINGS = ["fovInput", "deskButton", "body", "tree"]
TREE_ARM_EXPECTED_FAIL = "落点不可聚焦"


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


def src_text(rel):
    p = REPO / rel
    if not p.exists():
        raise SystemExit("FATAL 缺源码 %s" % rel)
    return p.read_text(encoding="utf-8")


def blank_comments(s):
    """注释抹白而不删（行号不漂移）。★ 只抹注释，不抹字符串（775 的 R107）。"""
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


# ═══════════════ 1. 原始读数 ═══════════════
raw = json.loads(RAW.read_text(encoding="utf-8"))
rounds = raw["rounds"]
assert len(rounds) == 2, "轮数不是 2"


def strip(rows):
    """去掉 `tries`/`retried`。★ **入参既可能是 dict 也可能是 dict 列表** ——
    `census` 是单个 dict，而 `rows` 是列表；第一版只当列表处理，
    于是 `strip(census)` 把字符串当 dict 迭代 ⟹ `AttributeError`。"""
    if isinstance(rows, dict):
        return {k: v for k, v in rows.items() if k not in META}
    return [{k: v for k, v in r.items() if k not in META} for r in (rows or [])]


cells = {}
for rd in rounds:
    for r in strip(rd.get("rows")):
        cells.setdefault(r.get("landing"), []).append(r)
# ★ `census` 每轮是**一个 dict**（不是列表）⟹ 直接取，不要 `[0]`
census = [strip(rd.get("census")) for rd in rounds]
feedback = [rd.get("feedback") or {} for rd in rounds]
persist = [rd.get("persist") or {} for rd in rounds]
print("（阶段一）%d 轮，落点 %d 个：%s" % (len(rounds), len(cells),
                                         sorted(cells)))

assert set(cells) == set(LANDINGS), "落点集合不符：%r" % sorted(cells)
bad = [(k, v[0].get("FAILED")) for k, v in cells.items() if v[0].get("FAILED")]
allowed = [(k, f) for k, f in bad if k == "tree"
           and TREE_ARM_EXPECTED_FAIL in (f or "")]
assert len(allowed) == len(bad), (
    "★ 有非预期 FAILED：%r\n  （`tree` 臂**预期**失败：%s —— 它的落点不可聚焦，"
    "与 body 臂是同一格，探针的自证会判它无效）"
    % ([x for x in bad if x not in allowed], TREE_ARM_EXPECTED_FAIL))

# ── 四臂逐格自证 ──
for k, rs in cells.items():
    c = rs[0]
    if k == "tree":
        continue
    assert c.get("before", {}).get("past") == "0", \
        "%s 起始历史不干净（past=%r）" % (k, c.get("before", {}).get("past"))
    assert c.get("mugGone") is True, "%s 删除后道具还在 ⟹ 不是有效读数" % k
    assert c.get("selectionKept") is True, \
        "%s 按行删除改选了 ⟹ 「输入框留在屏上」的前提没了" % k
    assert c.get("afterDelete", {}).get("past") == "1", (
        "%s 删除后 past=%r，而预测是 1（删除进历史）"
        % (k, c.get("afterDelete", {}).get("past")))
    # ★ 只对**非 body 的两臂**断言「与 body 臂不重复」——
    #   `body` 臂按定义焦点就是 BODY，拿它去比自己是自指的。
    if k in ("tree", "deskButton"):
        assert c.get("landingIsDistinct") is True, (
            "%s 落点与 body 臂重复（focusTag=%r）⟹ 不能当成独立的一格"
            % (k, (c.get("atLanding") or {}).get("focusTag")))
assert cells["fovInput"][0].get("atLanding", {}).get("focusInInput") is True, \
    "fovInput 臂的焦点没落在输入框上 ⟹ 那一格测的不是「输入框焦点」"

# ═══════════════ 2. 预测（从源码逐行推出） ═══════════════
# 预测 1：删除**进历史**（store 的 deleteDirectorEntity 走快照 + past）
nPast1 = sum(1 for k in ("fovInput", "deskButton", "body")
             if cells[k][0].get("afterDelete", {}).get("past") == "1")
assert nPast1 == 3, "★ 只有 %d/3 格删除后 past=1 ⟹ 「删除进历史」不成立" % nPast1

# 预测 2：撤销在**非输入框**落点上可用
#   ⟸ 桌的 Cmd+Z 分支在 `isEditable` 守卫之后（DirectorDesk.tsx:506 vs :487），
#      焦点不在输入框 ⟹ 守卫不触发 ⟹ undoDirector() 被调用
nonInput = ["deskButton", "body"]
nUndoOK = sum(1 for k in nonInput if cells[k][0].get("mugBack") is True)
assert nUndoOK == len(nonInput), (
    "★ 非输入框落点只有 %d/%d 能撤销 ⟹ 「不可逆」的读法要重算"
    % (nUndoOK, len(nonInput)))
#   且历史结构要跟着走：past 1→0、future 0→1
for k in nonInput:
    u = cells[k][0].get("afterUndo") or {}
    assert u.get("past") == "0" and u.get("future") == "1", (
        "%s 撤销后 past=%r future=%r，而预测是 0/1"
        % (k, u.get("past"), u.get("future")))

# ★ 预测 3（本批的核心）：焦点在**输入框**上时撤销**不可用**
#   ⟸ `isEditable` 守卫（:487）排在 Cmd+Z 分支（:506）**之前** ⟹ 早退
f = cells["fovInput"][0]
assert f.get("mugBack") is False, (
    "★ 输入框落点**居然能撤销** ⟹ 「守卫早退」这条推理不成立，"
    "本批关于 D1d 的结论要重算")
assert (f.get("afterUndo") or {}).get("past") == "1", (
    "★ 输入框落点撤销后 past=%r，而预测是 1（命令被吞、历史没动）"
    % (f.get("afterUndo") or {}).get("past"))
assert (f.get("afterUndo") or {}).get("future") == "0", (
    "★ 输入框落点撤销后 future=%r，而预测是 0"
    % (f.get("afterUndo") or {}).get("future"))

# 预测 4：**零撤销入口**、零确认、反馈面板显示占位文案
c0 = census[0]
assert c0.get("deskOk") is True, "普查没证明桌在 ⟹ 「没找到提示」不算数"
assert c0.get("undoish") == [], (
    "★ 桌里出现了撤销类控件 %r ⟹ 「零撤销入口」这条要重算" % c0.get("undoish"))
assert c0.get("rowDelete", 0) > 0, "按行删除入口为 0 ⟹ 普查前提不成立"
fb = (feedback[0] or {}).get("after") or {}
assert fb.get("undoishCount") == 0, \
    "★ 删除后出现了撤销类控件 ⟹ 「零撤销入口」要重算"
hasNoFeedback = any("无命令反馈" in (t or "") for t in (fb.get("liveTexts") or []))
assert hasNoFeedback, (
    "★ 删除后的 live 区里**没有**「无命令反馈」⟹ "
    "「反馈面板显示占位文案」这条要重算；实测 %r" % (fb.get("liveTexts"),))

# 预测 5：跨 reload **持久化**，且历史**不**随之保留
p0, p1 = persist[0], persist[1]
assert not p0.get("FAILED") and p0.get("afterReload"), \
    "跨 reload 那一格没跑成：%s" % (p0.get("FAILED"),)
assert p0["beforeReload"]["mug"] is False, "删除前道具就不在 ⟹ 那一格无效"
assert p0["afterReload"]["mug"] is False, (
    "★ reload 后道具**回来了** ⟹ 「删除跨 reload 持久化」不成立")
assert p0["afterReload"]["n"] == p0["beforeReload"]["n"], \
    "reload 前后对象数变了（%d → %d）⟹ 有别的东西在动" % (
        p0["beforeReload"]["n"], p0["afterReload"]["n"])
assert p0["afterReload"]["state"].get("past") == "0", (
    "★ reload 后 past=%r，而预测是 0（历史不跨 reload 保留）"
    % p0["afterReload"]["state"].get("past"))

print("（阶段二）删除进历史 %d/3｜非输入框落点可撤销 %d/2｜"
      "输入框落点**不可撤销**｜撤销入口 %d 个｜跨 reload 持久化=%s，past 归零=%s"
      % (nPast1, nUndoOK, c0.get("undoish") and len(c0["undoish"]) or 0,
         p0["afterReload"]["mug"] is False,
         p0["afterReload"]["state"].get("past") == "0"))

# ═══════════════ 3. 静态层 ═══════════════
DD = blank_comments(src_text("src/components/director/DirectorDesk.tsx"))
dl = DD.split("\n")
FB_LIB = src_text("src/lib/directorCommandFeedback.ts")
TREE_SRC = blank_comments(src_text(
    "src/components/director/DirectorObjectTree.tsx"))


def first_in(lines, pat, after=0):
    rx = re.compile(pat)
    return next((n for n, ln in enumerate(lines, 1)
                 if n > after and rx.search(ln)), None)


static = {
    "guardLine": first_in(dl, r"if \(isEditable\) return;"),
    "undoLine": first_in(dl, r'key\.toLowerCase\(\) === "z"'),
    "historyAttrs": [n for n, ln in enumerate(dl, 1)
                     if "data-director-history-past" in ln
                     or "data-director-history-future" in ln],
    "feedbackPanelLine": first_in(dl, r"无命令反馈"),
    "committedReturnsNull": 'disposition === "COMMITTED") return null' in FB_LIB,
    "rowDeleteStopPropagation": bool(
        TREE_SRC.find("data-director-delete-object") is not None
        and "event.stopPropagation();" in TREE_SRC[
            (TREE_SRC.find("data-director-delete-object") or 0):][:400]),
    "undoishInSource": bool(re.search(r"撤销|还原|恢复|已删除", TREE_SRC)),
}
static["undoAfterGuard"] = bool(
    static["guardLine"] and static["undoLine"]
    and static["guardLine"] < static["undoLine"])
assert static["guardLine"] is not None, "守卫不见了"
assert static["undoLine"] is not None, "Cmd+Z 分支不见了"
assert static["undoAfterGuard"] is True, (
    "★ Cmd+Z 分支排到了守卫**之前** ⟹ 「守卫早退」这条推理不成立")
assert static["committedReturnsNull"] is True, (
    "★ `getDirectorCommandFeedback` 不再对 COMMITTED 返回 null ⟹ "
    "「删除后显示『无命令反馈』」的机制要重算")
assert static["historyAttrs"], "桌根不再暴露 history-past/future ⟹ 读数方法不成立"
print("（阶段三）静态：守卫 :%s 早于 Cmd+Z :%s｜COMMITTED→null=%s｜"
      "history 属性在 :%r"
      % (static["guardLine"], static["undoLine"],
         static["committedReturnsNull"], static["historyAttrs"]))

# ═══════════════ 4. 可比性 ═══════════════
r0 = strip(rounds[0].get("rows"))
r1 = strip(rounds[1].get("rows"))
tries = [r.get("tries", 1) for rd in rounds for r in (rd.get("rows") or [])]
comparability = {
    "rounds": len(rounds), "rowsPerRound": len(rounds[0].get("rows") or []),
    "allConsistent": r0 == r1,
    "retryPolicy": "每格最多试 3 次（含第一次），900×n 退避；`tries`/`retried` "
                   "记进 raw 但**排除在两轮一致性比较之外**。",
    "retryStats": {"cells": len(tries),
                   "retriedCells": sum(1 for t in tries if t > 1),
                   "maxTries": max(tries) if tries else None},
    "boundary": "★ **本批未改 `src/`，也没有任何注入。** "
                "删除**是破坏性操作且本批真的执行了**（用户目标明确允许"
                "「各种改变状态的有副作用 CRUD」），但：① 每格开头 "
                "`fresh()` 清 localStorage ⟹ 不留残留；② 跨 reload 那一格"
                "**故意不清库**（那正是它要测的东西）；③ **不点**提交/连接/"
                "新增机位/导入导出，不做付费或真实生图生视频。",
}
assert comparability["allConsistent"] is True, "★ 两轮不一致"

# ═══════════════ 5. 结论 ═══════════════
judgments = [
    {"id": "J1",
     "text": "★ **「不可逆」不成立**：非输入框落点 **%d/%d** 能撤销"
             "（道具回到对象树、`past` 1→0、`future` 0→1）。"
             "763 那句「删除破坏性」把「可撤销」与「有入口」混成了一件事。"
             % (nUndoOK, len(nonInput)),
     "evidence": "阶段二"},
    {"id": "J2",
     "text": "★ **「跨 reload 持久化」成立**：删除后 %d 个对象，"
             "普通 reload 并重开桌后**仍是 %d 个**、道具**不在**，"
             "而 `past` **归零** ⟹ 删除留下了，**撤销历史没留下**。"
             % (p0["beforeReload"]["n"], p0["afterReload"]["n"]),
     "evidence": "阶段二"},
    {"id": "J3",
     "text": "★ **「无提示」成立，而且比原话更具体**：桌内**撤销类控件 0 个**、"
             "确认对话框 0 个，而唯一的出路是一个**没有任何提示的快捷键**；"
             "更糟的是常驻的命令反馈面板在**成功删除之后显示占位文案"
             "「无命令反馈」**（`getDirectorCommandFeedback` 对 `COMMITTED` "
             "返回 `null`）⟹ 用户刚做完一件破坏性操作，界面告诉他「无命令反馈」。",
     "evidence": "阶段二 + 阶段三"},
    {"id": "J4",
     "text": "★ **新缺陷 D1d：焦点在检查器输入框上时，删除**不可撤销**。**"
             "删除明明进了历史（`past`=1），但 `Cmd+Z` 被 `isEditable` 守卫"
             "（`DirectorDesk.tsx:487`）吞掉 ⟹ 道具**没有**回来、"
             "`past` 仍=1、`future` 仍=0。而「刚在输入框里改完数、顺手删个对象」"
             "是很自然的落点。**这与 D14 是同一道守卫** ⟹ 修 D14 时会顺带修掉它。",
     "evidence": "阶段二 + 阶段三"},
    {"id": "J5",
     "text": "★ 撤��的**可用性完全由焦点落点决定**，而**没有任何东西告诉用户这件事**"
             "—— 既没有提示「当前落点撤销无效」，也没有撤销按钮可以绕开键盘。"
             "⟹ 同一个产品里，「能不能撤销」取决于一个用户看不见的状态。",
     "evidence": "J1 + J3 + J4"},
    {"id": "J6",
     "text": "★ 「对象树」臂的落点 `[data-director-tree]` **不可聚焦** ⟹ "
             "焦点掉到 `BODY` ⟹ 它与 body 臂**是同一格**。探针的**自证**"
             "把它判成无效（而不是照报成两格）⟹ 本批的「非输入框落点」"
             "是 **2 个独立格**（`deskButton` 焦点在 BUTTON、`body` 焦点在 BODY），"
             "不是 3 个。",
     "evidence": "阶段一 + 探针自证"},
]
corrections = [
    {"id": "C777-1",
     "targets": ["763 挂起的 D1 后半句：「导演台删除破坏性且跨 reload 持久化，"
                 "却无『未保存/重置』提示」"],
     "was": "读作「删除不可逆 + 没有任何提示」。",
     "now": "★ 据实拆成三个读数：① **不可逆不成立** —— 非输入框落点 "
            "**2/2** 能用 `Cmd+Z` 撤销；② **跨 reload 持久化成立**，"
            "且**撤销历史不随之保留**（`past` 归零）；③ **「无提示」成立**，"
            "但比原话更具体：不是「无未保存/重置提示」，而是"
            "**零撤销入口 + 零确认 + 反馈面板在成功删除后显示「无命令反馈」**。",
     "evidence": "J1 + J2 + J3"},
]
assert [c["id"] for c in corrections] == ["C777-1"]
probeLessons = [
    {"id": "R119", "text": "★ **落点必须设在「动作之后」。** 删除动作自己会移走焦点，"
                            "所以「删除前的落点」不是「删除后用户所在的地方」。"},
    {"id": "R120", "text": "★ **两格若实测落在同一元素上，它们就是同一格。** "
                            "「对象树」落点不可聚焦 ⟹ 与 body 臂重复 ⟹ "
                            "补一个真的能聚焦的非输入控件作独立臂，并**自证**不重复。"},
    {"id": "R121", "text": "★ **读属性别把选择器当属性名**（`getAttribute('[data-x]')` "
                            "永远返回 null ⟹ 空串看起来像「历史是空的」）；"
                            "且这些属性挂在 `role=\"dialog\"` **元素本身**上，"
                            "而 `d.querySelector()` 只搜后代。"},
    {"id": "R122", "text": "★ **「可撤销」与「有入口」是两种不同的缺陷**，捆在一句话里"
                            "会让其中一件为真时把另一件一起放过。"},
]
assert [x["id"] for x in probeLessons] == ["R119", "R120", "R121", "R122"]

defects = [
    {"id": "D1d", "severity": "中-高",
     "text": "★ **焦点在检查器输入框上时，删除不可撤销。** 删除进了历史"
             "（`past`=1）但 `Cmd+Z` 被 `isEditable` 守卫"
             "（`DirectorDesk.tsx:487`，排在 `:506` 的 undo 分支之前）吞掉 ⟹ "
             "道具没回来、`past` 仍=1、`future` 仍=0。"
             "**与 D14 同一道守卫** ⟹ 修 D14 时顺带修掉。",
     "evidence": "J4"},
    {"id": "D1e", "severity": "中",
     "text": "★ **删除的出路是一个没有任何提示的快捷键。** 桌内撤销类控件 **0** 个、"
             "确认对话框 **0** 个；而常驻反馈面板在成功删除后显示**「无命令反馈」**。"
             "⟹ 用户既看不到「已删除」，也看不到「可以撤销」。",
     "evidence": "J3 + J5"},
]
audit = {
    "batch": 777,
    "topic": "把「删除破坏性且跨 reload 持久化，却无未保存/重置提示」拆成四个读数",
    "generatedBy": "probes/mk777audit.py",
    "sources": {"vb777a.json": {"sha16": sha(RAW), "rounds": len(rounds),
                                "rowsPerRound": len(rounds[0].get("rows") or [])}},
    "fourReadings": {
        "R-past": "删除进不进历史 → 进（past 0→1，%d/3 格）" % nPast1,
        "R-undo": "撤销在哪些落点可用 → 非输入框 %d/%d 可用，**输入框 0/1**"
                  % (nUndoOK, len(nonInput)),
        "R-persist": "跨 reload 还在吗 → **在**（%d→%d，past 归零）"
                     % (p0["beforeReload"]["n"], p0["afterReload"]["n"]),
        "R-affordance": "有没有撤销入口/确认/提示 → **撤销类控件 0、确认 0、"
                        "反馈面板显示「无命令反馈」**",
    },
    "verdict": {
        "不可逆": "**不成立**（非输入框落点 2/2 能撤销）",
        "跨reload持久化": "**成立**（且撤销历史不保留）",
        "无提示": "**成立**，但比原话更具体：零入口 + 零确认 + 「无命令反馈」",
        "新缺陷": "**输入框落点上撤销不可用**（D1d）",
    },
    "comparability": comparability,
    "static": static,
    "census": census[0],
    "results": {
        "pastAfterDelete": nPast1, "undoOKNonInput": nUndoOK,
        "undoOKInput": 0 if f.get("mugBack") is False else 1,
        "undoishCount": len(c0.get("undoish") or []),
        "noFeedbackText": hasNoFeedback,
        "persistKept": p0["afterReload"]["mug"] is False,
        "persistPast": p0["afterReload"]["state"].get("past"),
        "treeArmExpectedFail": [k for k, v in cells.items()
                                if v[0].get("FAILED")],
    },
    "judgments": judgments,
    "corrections": corrections,
    "findings": {
        "F1": "★ **「不可逆」不成立** —— 出路存在，只是不在任何界面上。",
        "F2": "★ **「跨 reload 持久化」成立**，且撤销历史**不**随之保留 ⟹ "
              "reload 之后删除就真的没有退路了。",
        "F3": "★ **「无提示」成立且更具体**：零撤销入口 + 零确认 + "
              "反馈面板显示「无命令反馈」。",
        "F4": "★ **新缺陷 D1d**：输入框落点上撤销被 D14 的守卫吞掉（同一道守卫）。",
        "F5": "★ 撤��可用性**由用户看不见的焦点状态决定**，而界面不告知。",
    },
    "probeLessons": probeLessons,
    "defects": defects,
    "srcDiff": "**本批未改 `src/`**（工作区 `src/` 干净）；**没有任何注入**。"
               "★ 本批**真的执行了破坏性删除**（用户目标允许有副作用的 CRUD），"
               "但每格开头 `fresh()` 清 localStorage ⟹ 不留残留。",
    "rawSha": {"vb777a.json": sha(RAW)},
    "retryStats": comparability["retryStats"],
    "boundary": comparability["boundary"],
}
OUT.write_text(json.dumps(audit, ensure_ascii=False, indent=1), encoding="utf-8")
print("wrote %s" % OUT)
