#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 776 汇编器 —— 把 `dbg776a.py` 的原始读数汇编成 `runtime-audit.json`。

## 汇编器只做三件事

1. **重算**：所有数字从 raw 现算，不采信探针写下的任何派生字段。
2. **断言**：把「从源码逐行推出的预测」写成会失败的断言。
   断言炸了是**机制读错了**，是要查的发现，不是要改的断言。
3. **下结论**：结论**分四桶**而不是三桶 —— 「无效」「更差」「更好」
   「本来就不是这个原因」是四种不同的东西，合并会让授权范围失真。

## ★ 结论里最要紧的一句

拍板项 763 写的是「两处必须一起改」。本批把它拆成两条可独立否证的推论：

- **推论一**「(a) Escape 加 `activeRef` 守卫单独改是空操作」——
  **被否证**。第 1 次 Escape 之后的状态（焦点仍在控件上、手势已空）
  正是 (a) 会**放行**的状态，而该状态**可达** ⟹ (a) 单独改会把
  「按 N 次都不生效的死键」变成「按第 2 次生效」。
- **推论二**「(b) `onFocus` 不再 `begin` 单独改是空操作」——
  **成立**，而且是**直接观测**而非推理：第 2、第 3 次按压所处的世界
  （永远没有活动手势）**就是 (b) 单独改之后的世界**，而它什么都没做。

⟹ 准确的说法不是「两处必须一起改」，而是
**「只改 (a)：死键变成按两次；两处都改：按一次」**。
这是**授权范围的缩小**，不是修法的推翻。
"""
import hashlib
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
#: HERE = <repo>/docs/research/<batch>/probes ⟹ 要退 **4** 级才到仓库根。
#: 少退一级会得到 <repo>/docs，那正是本文件第一版的错（`docs/docs/...`）。
REPO = HERE.parent.parent.parent.parent
BATCH = REPO / "docs/research/liblib-canvas-batch776-2026-10-01"
OUT = BATCH / "runtime-audit.json"
RAW = BATCH / "raw/vb776a.json"

IDS = ["xf", "panchor", "ptransform", "pose", "fov"]
PRESSES = 3
NEUTRAL = "F2"
META = {"tries", "retried"}


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


def src_text(rel):
    p = REPO / rel
    if not p.exists():
        raise SystemExit("FATAL 缺源码 %s" % rel)
    return p.read_text(encoding="utf-8")


def blank_comments(s):
    """注释**抹白而不删** —— 行号不漂移（775 的 R102）。

    ★ **只抹注释，不抹字符串字面量**（775 的 R107）：抹过头得到的
      不是零结果而是**假零**。
    """
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
A_p = RAW
raw = json.loads(A_p.read_text(encoding="utf-8"))
rounds = raw["rounds"]
assert len(rounds) == 2, "轮数不是 2"


#: 手势 id 的**易变部分**。`DirectorDesk.tsx:889` 暴露的是
#: `history.activeGesture?.gestureId`，而 store 生成的 id 形如
#: `director-gesture-<毫秒时间戳>-<序号>`（`directorStore.ts` 的 GESTURE_BEGIN 段）。
GESTURE_ID_RE = re.compile(r"director-gesture-\d+-\d+")


def norm(o):
    """把**易变**的手势 id 归一化成 `director-gesture-<id>`，递归。

    ★ 为什么必须归一化而不是**排除该字段**：
      「排除」会让人以为那一格没被比较过；「归一化」保留了
      **「有没有手势」这个机制相关的全部信息**，只扔掉时间戳。
      而且这件事必须**写进产物**（`comparability.normalized`），
      否则下一个人会以为两轮是逐字节相同的。
    """
    if isinstance(o, dict):
        return {k: norm(v) for k, v in o.items() if k not in META}
    if isinstance(o, list):
        return [norm(x) for x in o]
    if isinstance(o, str):
        return GESTURE_ID_RE.sub("director-gesture-<id>", o)
    return o


def strip_meta(rows):
    """`tries`/`retried` 是**基础设施元数据**，必须排除在两轮一致性之外
    （775 的教训：抖过一次和没抖过，机制读数应当相同）；手势 id 的
    时间戳按 `norm()` 归一化。"""
    return norm(rows or [])


def uniq(key, field):
    """两轮读数必须一致，不一致就**报出来**而不是取其一。"""
    vals = {json.dumps(c.get(field), ensure_ascii=False)
            for c in rows_by_key.get(key, [])}
    if len(vals) > 1:
        raise AssertionError("★ %s 的 %s 两轮不一致：%r" % (key, field, vals))
    if not vals:
        return None
    return json.loads(next(iter(vals)))


rows_by_key = {}
census_by_ctx = {}
for rd in rounds:
    for r in strip_meta(rd.get("rows")):
        rows_by_key.setdefault((r.get("ctx"), r.get("family"),
                                r.get("nth"), bool(r.get("isControl"))),
                               []).append(r)
    for c in strip_meta(rd.get("census")):
        census_by_ctx.setdefault((c.get("ctx"), c.get("id"),
                                  c.get("precondition")), []).append(c)

print("（阶段一）%d 轮，测量格 key %d 个，普查 key %d 个"
      % (len(rounds), len(rows_by_key), len(census_by_ctx)))

# ── 普查：五族在**前置到位**后的规模 ──
census = {}
censusFailed = []
for (ctx, fam, pre), rs in sorted(census_by_ctx.items()):
    c0 = rs[0]
    if c0.get("FAILED"):
        censusFailed.append("%s/%s: %s" % (ctx, fam, c0["FAILED"]))
        continue
    census[(ctx, fam)] = {"ctx": ctx, "id": fam, "precondition": pre,
                          "total": c0.get("total"), "live": c0.get("live"),
                          "type": c0.get("type"),
                          "wantType": c0.get("wantType"),
                          "hasRect": c0.get("hasRect"),
                          "selfJustified": c0.get("selfJustified")}
    assert c0.get("selfJustified") is True, \
        "%s/%s 普查行不自证（要么族不存在、要么有面积且类型与源码一致）：%r" % (
            ctx, fam, c0)
# ★ 自证覆盖：五族都必须至少在一个上下文里**真的出现**
#   ——「全部 0」看起来像「这个族不存在」，所以每族都要有非空的一次
for fam in IDS:
    hits = [v for v in census.values() if v["id"] == fam and v["live"]]
    assert hits, ("★ 族 %r 在**所有**上下文里都是 0 个 —— "
                  "要么真不存在，要么前置没做到位；两者必须分开记" % fam)
    for h in hits:
        assert h["type"] == h["wantType"], (
            "★ %s/%s 的 input type=%r 与源码标注的 %r 不符"
            % (h["ctx"], fam, h["type"], h["wantType"]))
print("（阶段一b）五族全部至少在一个上下文里非空：%s"
      % {f: max(v["live"] for v in census.values() if v["id"] == f)
         for f in IDS})

# ── 测量格 ──
g = {k: v[0] for k, v in rows_by_key.items()}
exp = {k: (c.get("exportOpenBefore"), c.get("gestureBeforeFocus"),
           c.get("gestureAfterFocus"), c.get("isGestureElement"),
           json.dumps(c.get("presses"), ensure_ascii=False))
       for k, c in g.items()}

gestureKeys = [k for k in g if not k[3]]
controlKeys = [k for k in g if k[3]]
assert gestureKeys, "没有实验格"
assert len(controlKeys) == 1, "对照格应恰有 1 个，实为 %d" % len(controlKeys)
bad = [k for k, c in g.items() if c.get("FAILED")]
assert not bad, "★ 有 %d 格 FAILED：%r" % (len(bad), bad[:3])

# 聚焦前手势必须为空（干净起点），否则这一格不是有效读数
for k, c in g.items():
    assert c.get("gestureBeforeFocus") == "", \
        "%s 起始手势非空（%r）—— 不是干净起点" % (k, c.get("gestureBeforeFocus"))
    assert (c.get("focus") or {}).get("ok") is True, \
        "%s 焦点没落在目标元素上" % (k,)
    assert c.get("exportOpenBefore") is True, "%s 导出面板没开" % (k,)
    assert len(c.get("presses") or []) == PRESSES, \
        "%s 按压次数 %d ≠ %d" % (k, len(c.get("presses") or []), PRESSES)

# ═══════════════ 2. 预测（从源码逐行推出） ═══════════════
# 预测 1：聚焦 gesture 控件 ⟹ onFocus: begin ⟹ beginDirectorGesture 返回
#         COMMITTED ⟹ activeGesture 非空（directorStore.ts:3580-3592）
nFocusBegan = sum(1 for k in gestureKeys if g[k].get("isGestureElement") is True)
assert nFocusBegan == len(gestureKeys), (
    "★ 只有 %d/%d 格在聚焦后起了手势 ⟹ 「onFocus 不起手势」成立，"
    "本批关于 (a) 的推理要重算" % (nFocusBegan, len(gestureKeys)))

# 预测 2：第 1 次 Escape ⟹ cancel() 清掉手势（useDirectorGestureBoundary.ts:96），
#         但 preventDefault+stopPropagation 无条件执行（:94-95）⟹
#         桌的 window 阶梯看不到它 ⟹ 导出面板仍开、桌仍开
p1 = [k for k in gestureKeys
      if (g[k]["presses"][0]["gesture"] == ""
          and g[k]["presses"][0]["exportPresent"] is True
          and g[k]["presses"][0]["deskOpen"] is True)]
assert len(p1) == len(gestureKeys), (
    "★ 只有 %d/%d 格符合「第 1 次 Escape：手势清空但面板/桌都没关」"
    % (len(p1), len(gestureKeys)))

# 预测 3：第 2、3 次 Escape ⟹ 仍然什么都没发生。
# ★ 这两次按压所处的世界（焦点在控件上、**无活动手势**）就是
#   「方向 (b) 单独改」之后的世界 ⟹ 观测到「什么都没做」即证 (b) 单独是空操作。
later = [g[k]["presses"][1:] for k in gestureKeys]
nLaterInert = sum(1 for ps in later
                  for p in ps if p["gesture"] == ""
                  and p["exportPresent"] is True and p["deskOpen"] is True)
nLaterTotal = sum(len(ps) for ps in later)
assert nLaterInert == nLaterTotal, (
    "★ 第 2/3 次按压里有 %d/%d 次**起了作用** ⟹ 「(b) 单独改是空操作」被否证，"
    "本批结论要重算" % (nLaterTotal - nLaterInert, nLaterTotal))

# 预测 4：焦点始终留在控件上（Escape 不移焦）
nStay = sum(1 for k in gestureKeys for p in g[k]["presses"]
            if p["focusStill"] is True)
assert nStay == len(gestureKeys) * PRESSES, (
    "★ 有焦点在按压后离开控件的情况（%d/%d）"
    % (len(gestureKeys) * PRESSES - nStay, len(gestureKeys) * PRESSES))

# ── 对照臂 ──
ck = controlKeys[0]
c = g[ck]
assert c.get("isGestureElement") is False, (
    "★ 对照臂聚焦后**起了手势** ⟹ 它根本不是非 gesture 控件，对照不成立")
assert c["presses"][0]["exportPresent"] is False, (
    "★ 对照臂第 1 次 Escape 没关掉导出面板 ⟹ 测量没有鉴别力"
    "（分不清「缺陷」与「面板本来就关不掉」）")
assert c["presses"][1]["deskOpen"] is False, (
    "★ 对照臂第 2 次 Escape 没关掉桌 ⟹ 桌的 Escape 阶梯本身有问题")
# ★ 对照臂第 1 次就把桌关掉的话，第 2 次就没有阶梯可走 —— 两种都接受，
#   但必须**如实记下是哪一种**，不能默认它关的是面板
ctrlFirstClosed = ("export" if c["presses"][0]["exportPresent"] is False
                   else ("desk" if c["presses"][0]["deskOpen"] is False
                         else "nothing"))
print("（阶段二）实验格 %d：第 1 次 Escape 手势清空且毫无作用 %d/%d；"
      "第 2/3 次仍毫无作用 %d/%d"
      % (len(gestureKeys), len(p1), len(gestureKeys),
         nLaterInert, nLaterTotal))
print("（阶段二）对照臂：第 1 次 Escape 关掉了 %s" % ctrlFirstClosed)

# ═══════════════ 3. 静态层 ═══════════════
GB = blank_comments(src_text("src/components/director/useDirectorGestureBoundary.ts"))
gl = GB.split("\n")


def first(pat, lines=None, after=0):
    """首个匹配行的**绝对**行号（1 起）。

    ★ `after` 是**必须的**：本文件第一版的 `block()` 找结束标记时从**文件头**开始，
      匹配到了起点**之前**第 90 行的另一个 `},` ⟹ 判定 `e < s` ⟹ 返回空串 ⟹
      「Escape 分支里没有 preventDefault」——**一个假零**，而且方向恰好是
      「我们的机制不存在」。这与 775 的 R110、775 的 R107 同族：
      **搜索必须有作用域，否则「找不到」会被读成「不存在」。**
    """
    rx = re.compile(pat)
    return next((n for n, ln in enumerate(lines or gl, 1)
                 if n > after and rx.search(ln)), None)


def block(start_pat, end_pat):
    """取 `start_pat` 到其后**首个** `end_pat`（含）之间的源码块，行号保持真实。"""
    s = first(start_pat)
    if not s:
        return ""
    e = first(end_pat, after=s)
    if not e:
        return ""
    return "\n".join(gl[s - 1:e])


esc = block(r'if \(event\.key === "Escape"\)', r"^\s*\},\s*$")
escStart = first(r'if \(event\.key === "Escape"\)')
onFocusLine = first(r"onFocus: begin,")
onPointerUpLine = first(r"onPointerUp: \(event\) => \{")
numEarly = first(r'event\.currentTarget\.type === "number"')

INSP = blank_comments(src_text(
    "src/components/director/DirectorInspector.tsx")).split("\n")
DESK = blank_comments(src_text(
    "src/components/director/DirectorDesk.tsx")).split("\n")
STORE = blank_comments(src_text("src/store/directorStore.ts")).split("\n")


def first_in(lines, pat):
    rx = re.compile(pat)
    return next((n for n, ln in enumerate(lines, 1) if rx.search(ln)), None)


static = {
    "escapeBranchLine": escStart,
    "escapeBranchText": " ".join(esc.split()),
    # ★ 修法 (a) 的判据**尚未出现** —— 断言它「现在还没有」，
    #   所以 D1 一旦落地，本批静态层立刻变红（775 沿用的做法）
    "escapeHasActiveRefGuard": bool(
        esc and "activeRef" in esc),
    "escapeHasPreventDefault": bool(esc and "preventDefault" in esc),
    "escapeHasStopPropagation": bool(esc and "stopPropagation" in esc),
    "escapeCallsCancel": bool(esc and "cancel()" in esc),
    "onFocusIsBegin": bool(onFocusLine),
    "onFocusLine": onFocusLine,
    "onPointerUpLine": onPointerUpLine,
    "pointerUpEarlyReturnForNumber": bool(numEarly),
    "numberEarlyReturnLine": numEarly,
    "gestureSpreadSites": [n for n, ln in enumerate(INSP, 1)
                           if "{...(disabled ? {} : gesture)}" in ln
                           or "{...(isAxisDisabled(index) ? {} : gesture)}" in ln],
    "deskExposesActiveGestureAttr": bool(
        first_in(DESK, r"data-director-active-gesture=")),
    "beginReturnsCommitted": bool(
        first_in(STORE, r'commandKind: "GESTURE_BEGIN"')),
}
assert static["escapeBranchLine"] is not None, "Escape 分支不见了"
assert static["escapeHasActiveRefGuard"] is False, (
    "★ Escape 分支里已经出现 `activeRef` 守卫了 —— **修法 (a) 可能已经被实现**，"
    "本批整批关于 (a) 的结论要重算")
assert static["escapeHasPreventDefault"] is True, \
    "Escape 分支不再 preventDefault ⟹ 本批的吞键推理要重算"
assert static["escapeHasStopPropagation"] is True, \
    "Escape 分支不再 stopPropagation ⟹ 桌的阶梯会看到它，推理要重算"
assert static["escapeCallsCancel"] is True, \
    "Escape 分支不再 cancel() ⟹ 第 1 次按压不会清手势，本批推理要重算"
assert static["onFocusIsBegin"] is True, (
    "★ `onFocus: begin` 已经不在了 —— **修法 (b) 可能已经被实现**，"
    "本批整批结论要重算")
assert static["pointerUpEarlyReturnForNumber"] is True, \
    "onPointerUp 对 number 的提前 return 不在了 ⟹ 775 批的 R103 推理要重算"
assert len(static["gestureSpreadSites"]) == 5, (
    "★ `{...gesture}` 展开处 %d 处，与源码现读的 5 处不符"
    % len(static["gestureSpreadSites"]))
assert static["deskExposesActiveGestureAttr"] is True, \
    "桌根不再暴露 data-director-active-gesture ⟹ 本批的读数方法不成立"
print("（阶段三）静态：Escape 分支在第 %d 行、无 activeRef 守卫、"
      "onFocus: begin 在第 %d 行、gesture 展开 %d 处"
      % (static["escapeBranchLine"], static["onFocusLine"],
         len(static["gestureSpreadSites"])))

# ═══════════════ 4. 可比性 / 重试 ═══════════════
r0 = strip_meta(rounds[0].get("rows"))
r1 = strip_meta(rounds[1].get("rows"))
c0 = strip_meta(rounds[0].get("census"))
c1 = strip_meta(rounds[1].get("census"))
tries = [r.get("tries", 1) for rd in rounds for r in (rd.get("rows") or [])]
retried = [{"ctx": r.get("ctx"), "family": r.get("family"),
            "nth": r.get("nth"), "tries": r.get("tries")}
           for rd in rounds for r in (rd.get("rows") or [])
           if (r.get("tries") or 1) > 1]
comparability = {
    "rounds": len(rounds), "rowsPerRound": len(rounds[0].get("rows") or []),
    "censusRowsPerRound": len(rounds[0].get("census") or []),
    "gestureCells": len(gestureKeys), "controlCells": len(controlKeys),
    "allConsistent": r0 == r1, "allConsistentCensus": c0 == c1,
    # ★ 归一化这件事必须**写进产物**：否则「两轮一致」会被读成逐字节相同
    "normalized": "两轮比较前做了两处归一化：① 去掉 `tries`/`retried`"
                  "（基础设施元数据）；② 把 `director-gesture-<时间戳>-<序号>` "
                  "归一化成 `director-gesture-<id>`（store 生成的手势 id 内嵌"
                  "毫秒时间戳，逐字节比较**永远不可能相等**）。"
                  "★ 归一化保留了「有没有手势」这个机制相关的全部信息，"
                  "只扔掉时间戳 —— 不是把该字段整个排除掉。",
    "rawRoundsByteIdentical": (
        json.dumps(rounds[0].get("rows"), ensure_ascii=False, sort_keys=True)
        == json.dumps(rounds[1].get("rows"), ensure_ascii=False,
                      sort_keys=True)),
    "retryPolicy": "每格最多试 3 次（含第一次），失败后按 900×n 毫秒退避；"
                   "4317 是多人共用的 dev server。★ 重试次数记进 raw 的 `tries`，"
                   "但 `tries`/`retried` **排除在两轮一致性比较之外**。",
    "retried": retried,
    "retryStats": {"cells": len(tries), "retriedCells": len(retried),
                   "maxTries": max(tries) if tries else None},
    "boundary": "★ **本批未改 `src/`，也没有任何注入。** 只点对象树的行、"
                "6 个 disclosure 触发器、**选中**相机/角色/道具、"
                "**切标签页**、**点预设路径造一条路径**、**选中锚点并切锚点类型**、"
                "以及**读属性**；**不点**提交/连接/添加，不做付费或真实生图生视频；"
                "导出面板的 `data-director-export-submit` **只读不点**。"
                "★ 造路径是在本地项目里**建数据**（`createMotionPath`），"
                "而 `fresh()` 每格开头清 localStorage ⟹ 不留残留。",
}
assert comparability["allConsistent"] is True, "★ 两轮测量不一致"
assert comparability["allConsistentCensus"] is True, "★ 两轮普查不一致"

# ═══════════════ 5. 结论 ═══════════════
q = {
    "Q0": "「聚焦 gesture 控件会不会起手势」？（推论一的前提）",
    "Q1": "第 1 次 Escape 之后，导出面板与桌各自发生了什么？",
    "Q2": "★ 第 2、3 次 Escape 呢？——**那正是「(b) 单独改」的世界**",
    "Q3": "非 gesture 的桌内控件作对照：第 1 次 Escape 能不能关掉导出面板？"
          "（测量有没有鉴别力）",
}
famMax = {f: max(v["live"] for v in census.values() if v["id"] == f)
          for f in IDS}
totalCtl = sum(famMax.values())
famsCovered = sorted(famMax)
judgments = [
    {"id": "J1",
     "text": "★ **推论一被否证**：%d/%d 格实测「聚焦即起手势」；而第 1 次 Escape "
             "之后状态变成「手势空、焦点仍在控件上」——**这正是修法 (a) 会放行的"
             "状态**，且它**可达** ⟹ **(a) 单独改不是空操作**。"
             % (nFocusBegan, len(gestureKeys)),
     "evidence": "阶段二 + J2"},
    {"id": "J2",
     "text": "★ **推论二成立，且是直接观测**：第 2、3 次按压共 %d/%d 次"
             "**什么都没发生**（手势空、面板开、桌开、焦点不动）。"
             "而那两次按压所处的世界（**永远没有活动手势**）"
             "**就是「(b) 单独改」之后的世界** ⟹ (b) 单独改是空操作。"
             % (nLaterInert, nLaterTotal),
     "evidence": "阶段二"},
    {"id": "J3",
     "text": "★ **「两处必须一起改」作为授权依据不成立**。准确的说法是："
             "**只改 (a)** ⟹ 死键变成「按第 2 次生效」；"
             "**两处都改** ⟹ 按 1 次生效。**这是授权范围的缩小，不是修法的推翻。**",
     "evidence": "J1 + J2"},
    {"id": "J4",
     "text": "★ **缺陷是跨全部 gesture 控件的**：普查在**前置到位**后共找到 "
             "**%d 个**可用控件，覆盖 **%d/%d 族**（%s）；"
             "每族取首末各一格 = **%d 个实验格**，**%d/%d** 格三按全无作用。"
             "← 5 个 `{...gesture}` 展开处（3 个 number + 2 个 range）同构。"
             % (totalCtl, len(famsCovered), len(IDS),
                "、".join("%s×%d" % (f, famMax[f]) for f in famsCovered),
                len(gestureKeys), len(gestureKeys), len(gestureKeys)),
     "evidence": "阶段一 + 阶段三"},
    {"id": "J5",
     "text": "★ 对照臂证明**测量有鉴别力**：非 gesture 的桌内控件上，"
             "第 1 次 Escape 关掉了 %s。⟹ 实验臂的「什么都没发生」"
             "**不是**「面板本来就关不掉」。" % ctrlFirstClosed,
     "evidence": "阶段二"},
    {"id": "J6",
     "text": "★ **用户可见的严重度比「死键」还高一层**：手势在第 1 次 Escape "
             "就被清掉了，却**没有任何反馈**（面板没关、桌没关、也没有别的提示）"
             "⟹ 用户既关不掉东西，也看不出发生了什么。",
     "evidence": "J2 + 阶段二读数"},
]
EVIDENCE_INDEX = {j["id"]: j["evidence"] for j in judgments}

probeLessons = [
    {"id": "R111", "text": "★ **同步的 `.focus()` 之后必须等 React 重渲染再读 "
                            "DOM 属性**。第一版同一次 `evaluate` 里读完就读 ⟹ "
                            "「onFocus 不起手势」—— 差一步就把 D1 的**理由**否了。"
                            "「看起来是机制发现」的第一嫌疑是自己的测量时序。"},
    {"id": "R112", "text": "★ **「少测」与「不存在」在产物里长得一模一样**"
                            "（775 的 R104 在本批复现）。姿态族与两族路径控件原本"
                            "全记成 0，真实原因是它们分别卡在 "
                            "`characterTab === \"pose\"`（:2339）、`paths.map`"
                            "（:1041）、`selectedAnchor.type !== \"vertex\"`"
                            "（:1189）后面。补上前置后是 **25 / 9 / 6** 个 ——"
                            "**代价是 31 个差点被记成「不存在」的控件。**"},
    {"id": "R113", "text": "★ **「点不动」是没有鉴别力的失败信息**。本批连踩三次："
                            "① 拿菜单**面板**的选择器当**触发器**；"
                            "② `SCAN_CLICK` **不滚动** ⟹ 折叠区外点不到；"
                            "③ 锚点类型取值**猜**成 `smooth`，源码里是 "
                            "`vertex`/`symmetric`/`asymmetric`。三次同一句话、"
                            "三个不同原因。"},
    {"id": "R114", "text": "★ **`if not x != \"true\"` 是优先级陷阱**：比较先于 "
                            "`not` ⟹ 解析成 `(not x) != \"true\"` ⟹ "
                            "**成功反而报错**。可怕之处是「手动复现成功、"
                            "函数却报失败」—— 两者不一致时**先怀疑判据**。"},
    {"id": "R115", "text": "★ **前置链要一层一层拆到底，不能停在「点不到」。** "
                            "本批的锚点族过了三道门（造路径 → 选中锚点 → "
                            "切锚点类型），每道门的失败信息**长得一模一样**。"},
    {"id": "R116", "text": "★ **内嵌时间戳的 id 会让「两轮逐字节一致」永远不可能**，"
                            "而它长得像「机制不一致」。手势 id 形如 "
                            "`director-gesture-<毫秒>-<序号>` ⟹ 11/11 格都「不同」。"
                            "正确做法是**归一化**（只扔时间戳、保留「有没有手势」）"
                            "**并把归一化写进产物** —— 不是把该字段**整个排除**，"
                            "那样会让人以为那一格没被比较过。"},
    {"id": "R117", "text": "★ **静态扫描里「找结束标记」必须带作用域**。"
                            "`block()` 找 `},` 时从文件头开始 ⟹ 匹配到起点**之前**"
                            "第 90 行的另一个 `},` ⟹ 判定 `e < s` ⟹ 返回空串 ⟹ "
                            "读成「Escape 分支里没有 `preventDefault`」—— "
                            "**一个假零，且方向恰好是「我们的机制不存在」。**"
                            "与 R107、R110 同族：**搜索没作用域 ⟹「找不到」"
                            "被读成「不存在」。**"},
    {"id": "R118", "text": "★ **阴性对照的 `kw` 必须取自判据标签里的字面量**，"
                            "不能取自判据的「意图」。本文件第一版写 "
                            "`kw=\"测量有鉴别力\"` —— 那句话只出现在 `why` 里、"
                            "标签里根本没有 ⟹ 翻红列表一条都匹配不上 ⟹ "
                            "被读成「判据不灵」。**775 也踩过一次同一个坑："
                            "这是复发性陷阱，不是手滑。**"},
]
assert [x["id"] for x in probeLessons] == ["R111", "R112", "R113", "R114",
                                            "R115", "R116", "R117", "R118"]

corrections = [
    {"id": "C776-1",
     "targets": ["763 挂起的 D1 修法：「两处必须一起改」"],
     "was": "「`useDirectorGestureBoundary` 的 Escape 分支加 "
            "`if (!activeRef.current) return;` + `onFocus` 不再 `begin()`"
            "（**两处必须一起改**）」—— 读作「(a) 单独改是空操作」。",
     "now": "★ 据实订正：**(a) 单独改不是空操作**。第 1 次 Escape 之后"
            "（`cancel()` 清了手势、焦点不动）就落在「`activeRef` 为假」的状态，"
            "而它**可达** ⟹ (a) 单独改会把死键变成「按第 2 次生效」。"
            "**(b) 单独改仍是空操作**（第 2/3 次按压**直接观测**了那个世界："
            "什么都没发生）。所以「必须一起」应当改写成"
            "**「只改 (a) = 按两次；两处都改 = 按一次」** —— "
            "**这是授权范围的缩小**：(a) 是可以单独做的。",
     "evidence": "J1 + J2 + J3"},
]
assert [c["id"] for c in corrections] == ["C776-1"]

defects = [
    {"id": "D1c", "severity": "中", "count": "%d/%d 格" % (len(gestureKeys),
                                                         len(gestureKeys)),
     "text": "★ **焦点在任意 gesture 控件上时，Escape 是死键**："
             "打开导出面板后连按 3 次 Escape，导出面板与桌**一次都没关**"
             "（而同一个会话里对照臂 1 次就关掉了）。"
             "根因是 `useDirectorGestureBoundary.ts:92-98` 的 Escape 分支"
             "**无条件** `preventDefault()` + `stopPropagation()`，"
             "把桌挂在 window 上的 Escape 阶梯整段挡掉。"
             "★ 且**没有任何反馈**（手势在第 1 次就被 cancel 掉了，"
             "但用户看不到任何变化）。",
     "evidence": "J2 + J4 + J5 + J6"},
]
audit = {
    "batch": 776,
    "topic": "验「D1 的两处必须一起改」这个断言本身 —— 拍板项里唯一一句"
             "从来没有证据的授权依据",
    "generatedBy": "probes/mk776audit.py",
    "sources": {"vb776a.json": {"sha16": sha(A_p), "rounds": len(rounds),
                                "rowsPerRound": len(rounds[0].get("rows") or [])}},
    "questions": q,
    "comparability": comparability,
    "static": static,
    "census": {("%s/%s" % (v["ctx"], v["id"])): v for v in census.values()},
    "censusFailed": censusFailed,
    "results": {
        "gestureCells": len(gestureKeys),
        "focusBeganGesture": nFocusBegan,
        "press1Inert": len(p1),
        "laterPresses": nLaterTotal,
        "laterPressesInert": nLaterInert,
        "controlFirstClosed": ctrlFirstClosed,
    },
    "evidenceIndex": EVIDENCE_INDEX,
    "judgments": judgments,
    "findings": {
        "F1": "★ **推论一被否证 ⟹ (a) 单独改可行**（把死键变成按两次）。",
        "F2": "★ **推论二成立 ⟹ (b) 单独改是空操作**（直接观测，非推理）。",
        "F3": "★ **「两处必须一起改」作为授权依据不成立**；准确说法是"
              "「只改 (a) = 按两次；两处都改 = 按一次」。**这是缩小授权范围。**",
        "F4": "★ 缺陷覆盖**全部** gesture 控件（5 个展开处同构，3 number + 2 range）。",
        "F5": "★ 静态层证明**两处都还没实现**（Escape 分支无 `activeRef` 守卫、"
              "`onFocus: begin` 仍在）⟹ D1 一旦落地，本批静态层立刻变红。",
    },
    "probeLessons": probeLessons,
    "corrections": corrections,
    "defects": defects,
    "srcDiff": "**本批未改 `src/`**（工作区 `src/` 干净；`git log 29d5ff1c..HEAD "
               "-- src/` 为空）；本批**没有任何注入**",
    "rawSha": {"vb776a.json": sha(A_p)},
    "retryStats": comparability["retryStats"],
    "boundary": comparability["boundary"],
}
OUT.write_text(json.dumps(audit, ensure_ascii=False, indent=1), encoding="utf-8")
print("wrote %s" % OUT)
