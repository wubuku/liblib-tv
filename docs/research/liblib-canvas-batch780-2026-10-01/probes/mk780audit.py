#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 780 汇编器 —— **验 D1d 严重度的前提**，结果把 `:487` 的修法从「按类型分流」
变成一张**有证据的「键 × 类型」矩阵**

## 本批更正的是 777 的一句**没验过的场景描述**

777 记 D1d（中-高）时写：「刚在输入框里改完数、**顺手删个对象**是很自然的落点」。

★ 777 的探针**用的是鼠标点行删除按钮**（`[data-director-delete-object]`；
R119 就是为此立的：删除动作自己会移走焦点）。所以那句「顺手」**从来没被测过** ——
它是我为了让缺陷显得严重而写的一句场景描述。

而源码说：`Delete`/`Backspace` 的处理在 `DirectorDesk.tsx:517`，
**排在 `:487` 那道 `isEditable` 守卫之后** ⟹ 焦点停在 `<input>` 上时按 Delete
**什么都不会发生**。

## 实测：预测成立 ⟹ 「顺手」不成立

- **gesture 臂 8/8 次**（2 族 × 2 键 × 2 次按压）：`cap=1, win=1` ⟹ 事件
  **到达了 window**，而对象数 **5→5**、`past` 仍=0、`lastCommand` 停在
  `GESTURE_BEGIN` ⟹ **桌的 `:487` 守卫把它吞了，什么都没删**。
- ★ **对照臂 2/2 次**：非输入落点 ⟹ `:487` 不触发 ⟹ **5→4**、
  `past` 0→1、`lastCommand=DELETE_OBJECTS` ⟹ 测量**有鉴别力**。

⟹ 用户想「改完数顺手删个对象」必须：**键入 → 鼠标点树上的行删除按钮 →
再点回控件 → 按 `Cmd+Z`** ⟹ 四步**刻意**序列，而不是一次顺手。

## 顺带把 `:487` 的修法定成一张矩阵（778/779 都给不出来的）

`:487` 早退的**正当性**取决于「该键在该控件上有没有原生兜底」。三批的读数
正好铺满这张表：

| 键 | number（原生兜底） | range（无原生兜底） |
| --- | --- | --- |
| `Escape` | **无** ⟹ 779 测得 hook 吞，桌够不着 | **无** ⟹ 同 |
| `Cmd+Z` | **有**（文本撤销）⟹ 778 测得早退是**承重墙** | **无** ⟹ 778 的 D1f 死键 |
| `Delete`/`Backspace` | **有**（删字符）⟹ 本批测得早退 | **无** ⟹ **本批新记录** |

⟹ **放行判据不是「控件类型」，是「该键在该类型上有没有原生兜底」。**
两个「无兜底」的键（`Cmd+Z` 与 `Delete`）在 26 个 range 滑杆上同时是死键 ⟹
**D1f 与本批的新缺陷是同一个缺陷的两种键** ⟹ 合并记一条。

★ `Cmd+C`/`Cmd+V` 那一行**本批未测** ⟹ 不写进矩阵（774 只在**浮层落点**上
测过它们，没在 gesture 控件上测过）。
"""
import hashlib
import json
import pathlib
import re

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent.parent.parent.parent
BATCH = REPO / "docs/research/liblib-canvas-batch780-2026-10-01"
OUT = BATCH / "runtime-audit.json"
RAW = BATCH / "raw/vb780a.json"
RAW778 = REPO / "docs/research/liblib-canvas-batch778-2026-10-01/raw/vb778a.json"
AUDIT778 = REPO / "docs/research/liblib-canvas-batch778-2026-10-01/runtime-audit.json"
RAW779 = REPO / "docs/research/liblib-canvas-batch779-2026-10-01/raw/vb779a.json"
AUDIT779 = REPO / "docs/research/liblib-canvas-batch779-2026-10-01/runtime-audit.json"

CAM = "director-camera-main"
MUG = "director-prop-mug"
META = {"tries", "retried"}
GESTURE_RX = re.compile(r"director-gesture-\d+-(\d+)")
GESTURE_ARMS = ["numberDelete", "numberBackspace", "rangeDelete",
                "rangeBackspace"]
CONTROL_ARM = "controlDelete"
ARMS = GESTURE_ARMS + [CONTROL_ARM]
PRESSES = 2
#: 「没有原生兜底」的键 —— 它们在 range 滑杆上是死键（778 的 D1f + 本批）
NO_FALLBACK = ["Meta+z", "Delete", "Backspace"]


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
    """臂的**标签**不是读数。"""
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
print("（阶段一）%d 轮 × %d 臂 × %d 次按压 = %d 格，零 FAILED，两轮逐字段一致"
      % (len(rounds), len(ARMS), PRESSES, len(ARMS) * PRESSES))

# 每格自证：起点干净、按键真的送达
for k, rs in arms.items():
    c = rs[0]
    assert (c.get("focus") or {}).get("ok") is True, "%s 聚焦没落上" % k
    assert (c.get("stateBefore") or {}).get("past") == "0", \
        "%s 起始历史不干净（past=%r）" % (
            k, (c.get("stateBefore") or {}).get("past"))
    assert (c.get("objectsBefore") or 0) > 0, "%s 起点没有对象" % k
    for p in c["presses"]:
        assert (p["read"].get("cap") or 0) >= 1, (
            "★ %s 第%s次 cap=%r ⟹ 按键没送达浏览器 ⟹ "
            "「没删掉」这个读数没有鉴别力"
            % (k, p["n"], p["read"].get("cap")))

# ═══════════════ 2. 读数（从源码逐行推出的预测） ═══════════════
# ── 预测 A（对照臂 · 鉴别力）：非输入落点上 `Delete` **应该**真的删掉 ──
ctrl = arms[CONTROL_ARM][0]
ctrlPer = [{"n": p["n"], "cap": p["read"].get("cap"),
            "win": p["read"].get("win"),
            "objectsBefore": p.get("objectsBefore"),
            "objectsAfter": p.get("objectsAfter"),
            "objectsDropped": p.get("objectsDropped"),
            "oidStillThere": p.get("oidStillThere"),
            "past": (p.get("state") or {}).get("past"),
            "lastCommand": (p.get("state") or {}).get("lastCommand")}
           for p in ctrl["presses"]]
for e in ctrlPer:
    assert e["objectsDropped"] == 1, (
        "★ 对照臂第%s次对象数只少了 %r ⟹ `:517` 没跑到 ⟹ "
        "「gesture 臂删不掉」可能只是**探针删不动**，判别力为零"
        % (e["n"], e["objectsDropped"]))
    assert e["oidStillThere"] is False, "对照臂第%s次目标还在" % e["n"]
    assert e["lastCommand"] == "DELETE_OBJECTS", (
        "★ 对照臂第%s次 lastCommand=%r，而预测是 DELETE_OBJECTS"
        % (e["n"], e["lastCommand"]))
    assert e["past"] == "1", "对照臂第%s次 past=%r，而预测是 1" % (
        e["n"], e["past"])
nCtrl = len(ctrlPer)
print("（阶段二）对照臂 %d/%d 次真的删掉了对象（5→%s、DELETE_OBJECTS、past=1）"
      "⟹ 判别器有鉴别力" % (nCtrl, nCtrl, ctrlPer[0]["objectsAfter"]))

# ── 预测 B（★ 本批载荷）：gesture 臂上 Delete/Backspace **删不掉** ──
#   ⟸ 桌的 `Delete`/`Backspace` 处理在 `:517`，排在 `:487` **之后**
#   ⟹ 事件到达 window（hook 对非 Escape 键只 `begin()` 不 `stopPropagation`）
#      但桌在 `:487` 早退 ⟹ 什么都没发生
noDelete = {}
for arm in GESTURE_ARMS:
    c = arms[arm][0]
    per = []
    for p in c["presses"]:
        rd, s = p["read"], p["state"]
        per.append({"n": p["n"], "cap": rd.get("cap"), "win": rd.get("win"),
                    "objectsDropped": p.get("objectsDropped"),
                    "oidStillThere": p.get("oidStillThere"),
                    "past": s.get("past"), "lastCommand": s.get("lastCommand")})
        assert (rd.get("win") or 0) >= 1, (
            "★ %s 第%s次 win=%r ⟹ 事件**没到达** window ⟹ "
            "「`:487` 吞的」这个归因不成立，真因是 hook" % (arm, p["n"],
                                                        rd.get("win")))
        assert p.get("objectsDropped") == 0, (
            "★ %s 第%s次**真的删掉了** %r 个对象 ⟹ 「焦点在控件上时 "
            "Delete 删不掉」不成立 ⟹ 777 的「顺手」成立，D1d 严重度不动"
            % (arm, p["n"], p.get("objectsDropped")))
        assert p.get("oidStillThere") is True, \
            "%s 第%s次目标不见了，但对象数没变 ⟹ 读数自相矛盾" % (arm, p["n"])
        assert s.get("past") == "0", (
            "★ %s 第%s次 past=%r，而预测是 0（没进历史）"
            % (arm, p["n"], s.get("past")))
        assert s.get("lastCommand") == "GESTURE_BEGIN", (
            "★ %s 第%s次 lastCommand=%r，而预测是停在 GESTURE_BEGIN"
            "（桌的键处理根本没走到 `:517`）" % (arm, p["n"], s.get("lastCommand")))
    noDelete[arm] = per
nNoDelete = sum(len(v) for v in noDelete.values())
assert nNoDelete == len(GESTURE_ARMS) * PRESSES, (
    "「删不掉」只覆盖 %d/%d 次按压" % (nNoDelete, len(GESTURE_ARMS) * PRESSES))
print("（阶段二）gesture 臂 %d/%d 次按压：事件**到达了 window** 而对象数一个没少、"
      "`lastCommand` 停在 GESTURE_BEGIN ⟹ **桌的 `:487` 吞了 Delete/Backspace**"
      % (nNoDelete, len(GESTURE_ARMS) * PRESSES))

# ═══════════════ 3. 静态层 ═══════════════
dl = blank_comments(src_text("src/components/director/DirectorDesk.tsx")).split(
    "\n")


def all_in(lines, pat):
    rx = re.compile(pat)
    return [n for n, ln in enumerate(lines, 1) if rx.search(ln)]


def first_in(lines, pat, after=0):
    return next((n for n in all_in(lines, pat) if n > after), None)


guardLine = first_in(dl, r"if \(isEditable\) return;")
deleteLine = first_in(dl, r'event\.key === "Delete" \|\| event\.key === "Backspace"')
deleteCall = first_in(dl, r"deleteDirectorEntity\(", after=deleteLine or 0)
static = {
    "guardLine": guardLine, "deleteBranchLine": deleteLine,
    "deleteCallLine": deleteCall,
    # ★ 预测 B 的机制：`Delete` 分支排在守卫**之后**
    "deleteAfterGuard": bool(guardLine and deleteLine
                             and guardLine < deleteLine),
}
assert guardLine is not None, "`isEditable` 守卫找不到了"
assert deleteLine is not None, "Delete/Backspace 分支找不到了"
assert deleteCall is not None, "deleteDirectorEntity 调用点找不到了"
assert static["deleteAfterGuard"] is True, (
    "★ Delete/Backspace 分支排到了守卫**之前** ⟹ "
    "「焦点在控件上时删不掉」这条推理不成立，777 的「顺手」成立")
print("（阶段三）静态：守卫 :%s 早于 Delete 分支 :%s（调用点 :%s）⟹ "
      "焦点在 `<input>` 上时 `:517` 够不着" % (guardLine, deleteLine, deleteCall))

# ═══════════════ 4. 跨批矩阵（数字从 778/779 的**产物**取，并从 776 的 raw 交叉校验） ═══════════════
A778 = json.loads(AUDIT778.read_text(encoding="utf-8"))
A779 = json.loads(AUDIT779.read_text(encoding="utf-8"))
# ★ 族规模不手抄：从 **776 的 raw 普查重算**（跨上下文取 max，不是求和），
#   再与 778 产物里的数字对账 —— 两处不一致就说明有一边的去重规则变了。
RAW776 = REPO / "docs/research/liblib-canvas-batch776-2026-10-01/raw/vb776a.json"
c776 = json.loads(RAW776.read_text(encoding="utf-8"))["rounds"][0]["census"]
best776 = {}
for x in c776:
    if not x.get("selfJustified"):
        continue
    if x.get("id") not in best776 or (x.get("live") or 0) > (
            best776[x["id"]].get("live") or 0):
        best776[x["id"]] = x
for k, x in best776.items():
    assert (x.get("live") or 0) > 0, "★ 776 普查里 %s 族 live=0 ⟹ 规模读数无效" % k
fam776 = {}
for x in best776.values():
    fam776[x.get("wantType")] = fam776.get(x.get("wantType"), 0) + (
        x.get("live") or 0)
nRange = fam776.get("range")
nNumber = fam776.get("number")
assert (nNumber, nRange) == (A778["familySizes"]["number"]["count"],
                             A778["familySizes"]["range"]["count"]), (
    "★ 776 raw 重算得 %r，而 778 产物记的是 %r ⟹ 两批的去重规则不一致，"
    "跨批引用不能用了" % ((nNumber, nRange),
                           (A778["familySizes"]["number"]["count"],
                            A778["familySizes"]["range"]["count"])))
assert nNumber + nRange == 53, "两族合计 %d，而 776 README 自述 53" % (
    nNumber + nRange)
vacuumCtrl = A778["results"]["vacuumControls"]
d1dFamilies = A778["results"]["delBlockedFamilies"]
firstSwallow = A779["results"]["firstSwallowPresses"]
assert vacuumCtrl == nRange, "778 的真空控件数与 range 族规模不一致"
matrix = {
    "rows": [
        {"key": "Escape", "number": "**无原生兜底** ⟹ 779：hook 吞（%d/%d 次 "
                                     "`win=0`），桌够不着" % (firstSwallow, 6),
         "range": "**无原生兜底** ⟹ 同左", "passThrough": "**两族都该放行**"},
        {"key": "Meta+z", "number": "**有**（文本撤销）⟹ 778：早退是**承重墙**",
         "range": "**无** ⟹ 778 的 D1f：%d 个死键" % vacuumCtrl,
         "passThrough": "**只 range 放行**"},
        {"key": "Delete / Backspace",
         "number": "**有**（删字符）⟹ 本批：早退",
         "range": "**无** ⟹ **本批新记录**：%d 个死键" % nRange,
         "passThrough": "**只 range 放行**"},
        {"key": "Meta+c / Meta+v", "number": "★ **本批未测**（774 只在浮层落点上测过）",
         "range": "★ **本批未测**", "passThrough": "★ 待测，不写进判据"},
    ],
    "criterion": "★ **放行判据不是「控件类型」，是「该键在该类型上有没有原生"
                 "兜底」。** 两个「无兜底」的键（`Meta+z` 与 `Delete`）在 %d 个 "
                 "range 滑杆上同时是死键 ⟹ **D1f 与本批的新缺陷是同一个缺陷的"
                 "两种键** ⟹ 合并记一条。" % nRange,
    "counts": {"range": nRange, "number": nNumber,
               "vacuumControls": vacuumCtrl,
               "d1dFamilies": d1dFamilies},
    "notMeasured": ["Meta+c", "Meta+v"],
}
print("（阶段四）矩阵：range %d 个 / number %d 个（778 raw 现算）｜"
      "无兜底的键 = Escape、Meta+z、Delete/Backspace｜★ Meta+c/Meta+v 本批未测"
      % (nRange, nNumber))

# ═══════════════ 5. 可比性 ═══════════════
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
    "boundary": "★ **本批未改 `src/`，也没有任何注入。** 删除**只发生在对照臂**"
                "（用户目标允许有副作用的 CRUD），每格开头 `fresh()` 清 "
                "localStorage ⟹ 不留残留；**不点**提交/连接/新增机位/导入导出，"
                "不做付费或真实生图生视频。",
    "noDestructiveLeak": "★ gesture 臂**没有真的删除**（实测 8/8 次对象数不变）"
                         "⟹ 本批唯一的破坏性操作是对照臂那一次，且它测的正是"
                         "「删得掉」这个必要条件。",
}
assert comparability["allConsistent"] is True, "★ 两轮不一致"

# ═══════════════ 6. 结论 ═══════════════
judgments = [
    {"id": "J1",
     "text": "★ **777 的「顺手」不成立。** 焦点在 gesture 控件上时，"
             "`Delete`/`Backspace` **删不掉任何对象**（%d/%d 次按压：事件"
             "**到达了 window**，而对象数一个没少、`lastCommand` 停在 "
             "`GESTURE_BEGIN`）⟹ 用户想「改完数顺手删个对象」必须"
             "**键入 → 鼠标点树上的行删除按钮 → 再点回控件 → 按 `Cmd+Z`**，"
             "那是四步**刻意**序列。" % (nNoDelete, nNoDelete),
     "evidence": "阶段二 预测 B"},
    {"id": "J2",
     "text": "★ **判别力有对照**：非输入落点上的 `Delete` **真的删掉了**"
             "（%d/%d 次：5→%s、`DELETE_OBJECTS`、`past` 0→1）⟹ "
             "「gesture 臂删不掉」不是探针删不动。" % (
                 nCtrl, nCtrl, ctrlPer[0]["objectsAfter"]),
     "evidence": "阶段二 预测 A"},
    {"id": "J3",
     "text": "★ **D1d 的严重度要下调**（中-高 → 中）。缺陷**本身仍成立**"
             "（%d/%d 族、%d 个控件都不可撤销，778 已钉住），但**触发它需要"
             "一条刻意的四步序列**，而不是一次顺手 ⟹ 它的**发生频率**远低于"
             "777 写下的印象。" % (d1dFamilies, 2, nNumber + nRange),
     "evidence": "J1 + 778 的 J1"},
    {"id": "J4",
     "text": "★ **`:487` 的放行判据不是「控件类型」，是「该键在该类型上有没有"
             "原生兜底」。** 三批读数正好铺满矩阵：`Escape` 两族都无兜底 ⟹ "
             "**都该放行**（779）；`Meta+z` 与 `Delete/Backspace` 在 number 有"
             "兜底（778 的承重墙 / 原生删字符）、在 range 没有 ⟹ "
             "**只 range 该放行**。⟹ D1f（`Meta+z` 死键，778）与本批的新缺陷"
             "（`Delete` 死键）是**同一个缺陷的两种键**，合并记一条，"
             "落在同样那 %d 个滑杆上。" % nRange,
     "evidence": "阶段四 + 778 的 J3 + 779 的 J1"},
    {"id": "J5",
     "text": "★ **`Meta+c`/`Meta+v` 那一行本批未测** ⟹ 不写进矩阵也不写进判据。"
             "774 只在**浮层落点**上测过它们，没在 gesture 控件上测过 ⟹ "
             "「它们在 number 上有原生兜底」目前**只是推断**。",
     "evidence": "阶段四 notMeasured"},
]
corrections = [
    {"id": "C780-1",
     "targets": ["**777 的 D1d 描述**：「而『刚在输入框里改完数、顺手删个对象』"
                 "是很自然的落点」"],
     "was": "读作「删除与输入框焦点很容易同时发生」⟹ 缺陷被当成高频、中-高。",
     "now": "★ **那句『顺手』从来没被测过。** 777 的探针用的是**鼠标点行删除"
            "按钮**（`[data-director-delete-object]`，R119 就是为此立的）⟹ "
            "它测的是「**已经**删完之后焦点能不能撤销」，"
            "**没测「焦点在控件上时能不能删」**。"
            "本批实测：焦点在 gesture 控件上时 `Delete`/`Backspace` "
            "**%d/%d 次都删不掉**（事件到达 window 而桌在 `:487` 早退）⟹ "
            "真实序列是**键入 → 鼠标点删除按钮 → 点回控件 → `Cmd+Z`**，"
            "四步且刻意。⟹ **D1d 的严重度从「中-高」下调为「中」**"
            "（缺陷本身不撤销，仍是 %d 个控件、%d/%d 族成立）。"
            % (nNoDelete, nNoDelete, nNumber + nRange, d1dFamilies, 2),
     "evidence": "J1 + J2 + J3"},
    {"id": "C780-2",
     "targets": ["**778 的 D1f**（`Meta+z` 在 %d 个 range 滑杆上是死键）"
                 % vacuumCtrl],
     "was": "记作一个只关于 `Meta+z` 的缺陷。",
     "now": "★ **与本批的新缺陷合并**：同一个 `:487`、同样那 %d 个 range 滑杆、"
            "同样「零反馈」⟹ `Meta+z` 与 `Delete`/`Backspace` 是"
            "**同一个缺陷的两种键**。⟹ 记一条即可："
            "「**在没有原生兜底的键上，这 %d 个滑杆是死键**」。"
            % (nRange, nRange),
     "evidence": "J4"},
]
assert [c["id"] for c in corrections] == ["C780-1", "C780-2"]

probeLessons = [
    {"id": "R134", "text": "★ **缺陷描述里的「场景」也是要测的。** 我 777 写"
                            "「顺手删个对象」时，探针用的是**鼠标按钮** ⟹ "
                            "那句话是从**机制**想出来的，不是从**读数**出来的。"
                            "机制说 `Delete` 排在 `:487` 之后，"
                            "而我没去测 ⟹ 三批之后才发现它把 D1d 的严重度"
                            "高估了一档。"},
    {"id": "R135", "text": "★ **「什么都没发生」要配一个「真的发生了」的对照臂。**"
                            "若没有非输入落点那 %d/%d 次真删掉，"
                            "「gesture 臂删不掉」与「探针删不动」"
                            "在产物里长得一模一样（R113/R121 同族）。"},
    {"id": "R136", "text": "★ **承重的读数要按「这个键会不会被 hook 拦」来选。**"
                            "本批 `win` 对所有键都应为正（hook 只拦 Escape）⟹ "
                            "真正的读数是**「到达了 window 却什么也没发生」**。"},
    {"id": "R137", "text": "★ **没测的那一行要显式标出来，不要靠沉默。** "
                            "`Meta+c`/`Meta+v` 在 number 上「有原生兜底」"
                            "目前只是推断（774 只在浮层落点上测过）⟹ "
                            "矩阵里写成「本批未测」而不是留白或猜。"},
]
assert [x["id"] for x in probeLessons] == [
    "R134", "R135", "R136", "R137"]

defects = [
    {"id": "D1f", "severity": "中（★ 778 记为中，780 扩了键的种类）",
     "text": "★ **%d 个 range 族滑杆上，凡是没有原生兜底的键都是死键，且零反馈。**"
             "本批实测扩展了键的种类：`Meta+z`（778 的 D1f）与 "
             "`Delete`/`Backspace`（本批）在同样那 %d 个滑杆上"
             "**都是死键** —— 值/对象数、`past/future`、`lastCommand` 全部不动，"
             "而事件**确实到达了 window** ⟹ 桌在 `DirectorDesk.tsx:487` 的 "
             "`isEditable` 守卫早退。⟹ 同一个守卫、同一批控件、**两种键**，"
             "故合并记一条（见 C780-2）。" % (nRange, nRange),
     "evidence": "J4 + 778 的 J3"},
]
audit = {
    "batch": 780,
    "topic": "验 D1d 严重度的前提：「顺手删个对象」到底自不自然；顺带把 `:487` "
             "的放行判据定成一张「键 × 类型」矩阵",
    "generatedBy": "probes/mk780audit.py",
    "sources": {
        "vb780a.json": {"sha16": sha(RAW), "rounds": len(rounds),
                        "armsPerRound": len(ARMS), "pressesPerArm": PRESSES},
        "vb778a.json": {"sha16": sha(RAW778)},
        "vb779a.json": {"sha16": sha(RAW779)},
        "batch778/runtime-audit.json": {"sha16": sha(AUDIT778),
                                       "usedFor": "族规模与真空控件数"},
        "batch779/runtime-audit.json": {"sha16": sha(AUDIT779),
                                       "usedFor": "Escape 行的现算数字"},
        "vb776a.json": {"sha16": sha(RAW776), "usedFor": "★ 族规模重算并对账"},
    },
    "thePremise": {
        "claim777": "「刚在输入框里改完数、顺手删个对象是很自然的落点」",
        "how777MeasuredIt": "★ **用的是鼠标点行删除按钮**"
                            "（`[data-director-delete-object]`；R119 就是"
                            "为此立的）⟹ 测的是「已经删完之后能不能撤销」，"
                            "**没测「焦点在控件上时能不能删」**",
        "sourcePrediction": "`Delete`/`Backspace` 的处理在 `DirectorDesk.tsx:%s`，"
                            "**排在 `:487` 守卫之后** ⟹ 焦点停在 `<input>` "
                            "上时按 Delete 什么都不会发生。" % deleteLine,
        "verdict": "★ **预测成立** ⟹ 「顺手」不成立（%d/%d 次按压都删不掉）"
                   % (nNoDelete, nNoDelete),
    },
    "readings": {
        "R-control": "非输入落点上 `Delete` %d/%d 次**真的删掉**（5→%s、"
                     "`DELETE_OBJECTS`、`past` 0→1）⟹ 判别力成立" % (
                         nCtrl, nCtrl, ctrlPer[0]["objectsAfter"]),
        "R-gesture": "gesture 臂 %d/%d 次：事件**到达 window**（`win>=1`）"
                     "而对象数**一个没少**、`past` 仍=0、`lastCommand` 停在 "
                     "`GESTURE_BEGIN` ⟹ **桌的 `:487` 吞了 Delete/Backspace**" % (
                         nNoDelete, nNoDelete),
    },
    "matrix": matrix,
    "verdict": {
        "777的「顺手」": "**不成立** —— 焦点在控件上时 Delete/Backspace 删不掉",
        "D1d严重度": "**下调 中-高 → 中**（缺陷本身不撤销：%d 个控件、%d/%d 族）"
                     % (nNumber + nRange, d1dFamilies, 2),
        "`:487`放行判据": "★ **不是「控件类型」，是「该键在该类型上有没有原生兜底」**",
        "D1f范围": "**扩展** —— `Meta+z` 与 `Delete`/`Backspace` 是同一缺陷的"
                   "两种键，落在同样 %d 个滑杆上 ⟹ 合并" % nRange,
        "未测": "★ `Meta+c`/`Meta+v`（在 gesture 控件上）本批未测",
    },
    "comparability": comparability,
    "static": static,
    "noDelete": noDelete,
    "controlArm": ctrlPer,
    "results": {
        "noDeletePresses": nNoDelete,
        "noDeleteTotal": len(GESTURE_ARMS) * PRESSES,
        "controlDeletedPresses": nCtrl,
        "deleteAfterGuard": static["deleteAfterGuard"],
        "rangeControls": nRange, "numberControls": nNumber,
        "failedCells": 0,
    },
    "judgments": judgments,
    "corrections": corrections,
    "findings": {
        "F1": "★ **777 的「顺手」不成立** —— Delete/Backspace 在控件焦点下删不掉。",
        "F2": "★ **D1d 严重度下调为中**（缺陷仍在，但要一条刻意的四步序列）。",
        "F3": "★ **`:487` 的放行判据是「该键有无原生兜底」**，不是「控件类型」。",
        "F4": "★ **D1f 扩展并合并** —— `Meta+z` 与 `Delete` 是同一缺陷的两种键。",
        "F5": "★ `Meta+c`/`Meta+v` 在 gesture 控件上**本批未测** ⟹ 不进矩阵。",
    },
    "probeLessons": probeLessons,
    "defects": defects,
    "srcDiff": "**本批未改 `src/`**（工作区 `src/` 干净）；**没有任何注入**。",
    "rawSha": {"vb780a.json": sha(RAW), "vb778a.json": sha(RAW778),
               "vb779a.json": sha(RAW779)},
    "retryStats": comparability["retryStats"],
    "boundary": comparability["boundary"],
}
OUT.write_text(json.dumps(audit, ensure_ascii=False, indent=1), encoding="utf-8")
print("wrote %s" % OUT)
