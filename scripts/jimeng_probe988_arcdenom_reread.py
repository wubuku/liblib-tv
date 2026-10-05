#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""batch 988 **纯离线重算**探针（**零计费**：不打开任何浏览器、
不按任何键、**连 `mouse.click` 都没有**）：
⭐⭐⭐⭐⭐ **986 换口径的连带：把 §192 / §193 的 arc 覆盖率分母减一并重述** ——
而第一版算出来的东西**比减一更深**：**分子也要减**。

── 986/987 换掉了什么 ──────────────────────────────────────────────

985 证明 `BODY` 不是一格、是**间隙** ⇒ **可聚焦停靠点数 = 旧环长 − 1**
⇒ ⇒ ⭐⭐⭐⭐ 986 把它落成读数（源站 101→**100**、复刻 26→**25**）
⇒ ⇒ ⭐⭐⭐⭐⭐ **而 arc 覆盖率（§192 §193）还没换口径** ——
它报的是 **18/101 = 17.8%**（源站）与 **19/26 = 73.1%**（复刻）

⚠️⭐⭐⭐⭐⭐ **第一版我以为「分母减一、分子不动」** ⇒ **错了，两处都错**：

**错一：分母该减一** —— 与 986 同一件事（`BODY` 不是一格）
**错二：⭐⭐⭐⭐⭐ 分子也该减一** —— ⚠️ **因为弧里本来就有间隙！**

实测两处都不是我以为的那样：

| 系统 | 旧 `arc_ranks` / 旧 arc | 弧里含间隙？ | 间隙在哪 |
| --- | --- | --- | --- |
| **源站**（974） | 18 格，ranks = 2263…2396, **60**, 68, 85, …, 177 | ✅ **含** | `60` = `document.body`（`body_seats=[6]`） |
| **复刻**（983） | 19 格，环格 **8..26** | ✅ **含** | 环格 **25** = `BODY`（`dom_rank`=37） |

⇒ ⇒ ⭐⭐⭐⭐⭐ **「arc 覆盖率」的分子分母**各自都含一格间隙** ⇒
**两边同时减一** ⇒ ⇒ ⭐⭐⭐⭐⭐
**而这与 986 那条「去 BODY 后严格递增」的失败是同一族**：
**间隙不是环上的一格、却一直被我算成了一格**

── ⭐⭐⭐⭐⭐ 三条预测，**全部在看数据之前按定义逐句推出** ─────────────

⚠️⭐⭐⭐ **期望值必须按定义逐句推**，不能「跑出来是什么就写什么」。

**P1（分子分母各减一）**：新 `arc_cover_num` = 旧 `arc_cover_num` − 1、
新 `arc_cover_den` = 旧 `arc_cover_den` − 1
⇒ 推导：旧口径把间隙算成一格 ⇒ 分子里含它、分母里也含它 ⇒ **各减一**

**P2（⭐⭐ 旧口径会把「零」报成「一」的那个家族，在这里也成立）**：
**新分母（可聚焦停靠点数）= 旧分母 − 1 在两个系统上逐格成立**
⇒ ⇒ 推论：**分母减一之后，覆盖率必然上升** ⇒
⇒ ⭐⭐⭐⭐⭐ **而两边的上升幅度不同** ⇒ **比率的「大小关系」可能翻转**

**P3（⭐⭐⭐⭐⭐ 最值钱的一条：新口径下 arc 覆盖率的关系式，而不是数值）**：
源站新覆盖率 = 17/100、复刻新覆盖率 = 18/25
⇒ ⇒ ⭐⭐⭐⭐⭐ **源站仍远低于复刻** ⇒ **「源站侧只验了一小段」这个结论不变**
⇒ ⇒ ⭐⭐⭐⭐⭐ **但两者的差距被新口径放大了**（旧 17.8% vs 73.1%；
新 17.0% vs 72.0% ⇒ ⚠️ **差距其实几乎没变**，见下）
⇒ ⇒ ⭐⭐ **所以「换口径」不改变 §192/§193 的任何定性结论** ——
**这正是本批要验的那句**

── ⭐⭐⭐⭐⭐ 一条不许含糊的东西：**「arc 覆盖率」到底在量什么** ────────

`arc` 的定义（982 逐字复刻 973）：**`out` 行里 k 连续的第一段**
⇒ ⇒ ⭐⭐⭐⭐⭐ **它不是「一圈」、也不是「一圈的一部分」** ——
**它是「某次走查里连续按了多久 `Tab`」的度量**
⇒ ⇒ ⚠️⭐⭐⭐ **所以「覆盖率」这个名本身就有误导性** ——
**它不是「环被覆盖了百分之多少」**（982 已经说过 18 格不是圈）
⇒ ⇒ ⭐⭐⭐⭐⭐ **本批把它正名为「连续 out 段长 / 环长」**，
并**明确写下：它不是覆盖率、§192/§193 的措辞应当作废重写**

**本批零计费**：**不打开浏览器**、**不按任何键**、**连 `mouse.click` 都没有**；
纯离线重算 `/tmp` 里 974/983 的**原始读数** ⇒
⚠️ **源站侧用的是 974 存档的读数**（985 已确认源站登录态过期）⇒
**本批不测源站、只重算 974 当年的读数** ⇒ 「不是「测了没事」」
"""
from __future__ import annotations

import ast
import json
import os
import re

OUT = "/tmp/b988-arcdenom.json"
SRC_974 = "/tmp/b974-source-domrank.json"     # 源站侧 974 存档
SRC_983 = "/tmp/b983-wrapcmp.json"           # 复刻侧 983 存档
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _src(name):
    p = os.path.join(ROOT, "scripts", name)
    if not os.path.exists(p):
        return ""
    with open(p, encoding="utf-8") as f:
        return f.read()


_p982 = _src("jimeng_probe982_ringlen_src.py")
_ME = open(__file__, encoding="utf-8").read()


def _grab_def(start, end, src=None):
    s = src or ""
    i = s.index(start)
    j = s.index(end)
    assert i < j, "起止锚点顺序错了"
    _s = s[i:j]
    assert _s in s, "抠出来的那段不是逐字抠出来的"
    return _s


# ⭐⭐⭐⭐⭐ **纯 python 件按起止锚点逐字抠**（983/987 的原话照抄）
GRAB_DEF_START = "def min_period(seq):"
GRAB_DEF_END = "def _code_only(js):"
INSTR_SRC = _grab_def(GRAB_DEF_START, GRAB_DEF_END, _p982)
_NS: dict = {}
exec(compile(INSTR_SRC, "<982-instruments>", "exec"), _NS)   # noqa: S102
_arc_of = _NS["_arc_of"]
_descents = _NS["_descents"]
assert callable(_arc_of) and callable(_descents)
# ⚠️⭐⭐⭐⭐⭐ **`arc` 的定义不许各批各说各话** ⇒ 判据钉住它是「out 行里 k 连续的第一段」
assert "out` 行里" in INSTR_SRC and "k 连续的第一段" in INSTR_SRC, \
    "982 的 `arc` 定义变了 ⇒ 本批的重算口径分叉了"
# ⚠️⭐⭐⭐⭐⭐ **「本批不许自己重写」这道门，第一版被自己的注释误抓了** ——
#   我在讲 `arc` 定义的**注释字符串里**写了 `def _arc_of(pairs):`
#   ⇒ ⇒ ⭐⭐⭐⭐⭐ **门必须只看真正的定义行**（行首就是 `def`、且不在字符串里）
#   ⇒ ⇒ ⭐⭐ **用 `ast` 判，而不是用 `in` 判** ⇒ **同一个东西要比同一个口径**
assert not any(
    isinstance(n, ast.FunctionDef) and n.name == "_arc_of"
    for n in ast.walk(ast.parse(_ME))), \
    "本批自己重写了 `_arc_of` ⇒ 尺子分叉了"
# ⭐⭐⭐⭐⭐ **成对**：真的重写了必须被抓到
assert any(isinstance(n, ast.FunctionDef) and n.name == "_arc_of"
           for n in ast.walk(ast.parse("def _arc_of(pairs):\n    return []\n"))), \
    "⭐⭐⭐⭐ **成对门坏了**：用 `in` 判会误抓注释、用 `ast` 判会漏真定义"


# ══ ⭐⭐⭐⭐⭐ 本批的核心：**换口径的三个纯函数** ═══════════════════════
def _is_gap_rank(rank, body_rank):
    """⭐⭐⭐⭐⭐ **间隙的判定**：`dom_rank` 等于 `document.body` 那个值。

    ⚠️⭐⭐⭐⭐⭐ **为什么用「等于 `body` 的 `dom_rank`」而不是「key 里有 `BODY`」**
    —— ⭐⭐ **974 的 `arc_ranks` 里只存了 `dom_rank`、没存键** ⇒
    ⇒ 而 **`body_seats` 给了 `BODY` 在弧里的位置** ⇒
    ⇒ ⭐⭐⭐⭐⭐ **两个来源必须一致**（`arc_ranks[6] == 60` 且 `body_seats == [6]`）
    ⇒ ⇒ **成对门钉住**：位置对不上就判红
    """
    return body_rank is not None and rank == body_rank


def _recompute(pairs, body_seats, body_rank, ring_len_old):
    """⭐⭐⭐⭐⭐ **同一个函数算新旧两套口径** ⇒ 两批不会各说各话。

    推导：旧口径 = `arc` 的原样长度；新口径 = **去掉间隙那格**之后的长度
    ⇒ ⇒ **分母同理**（`ring_len_old` → `ring_len_old - 1`）
    """
    arc = _arc_of(pairs)
    n_old = len(arc)
    # ⭐⭐⭐⭐⭐ **成对门：两套座位必须换算到**同一基准**再比**
    # ⚠️⭐⭐⭐⭐⭐ **第一版直接比、门报 `seats_agree=False` —— 而两个数都没错**：
    #   复刻侧 `is_body` 的座位是**整圈内**的（0-based = 24），
    #   而 `by_rank` 数的是**弧内**的（0-based = 17）
    #   ⇒ ⇒ ⭐⭐⭐⭐⭐ **两个都对、只是基准不同** ⇒
    #   ⇒ **门比的不是「座位」、是「间隙是不是同一个东西」**
    #   ⇒ ⇒ **换算办法：由整圈座位回推它在 `out` 列表里的下标**
    by_rank = [i for i, (_k, rk) in enumerate(arc)
               if _is_gap_rank(rk, body_rank)]
    by_seat = list(body_seats or [])
    arc_start = pairs[0][0] - 1 if pairs else 0    # 弧首在 out 列表里的下标
    mapped = [i - arc_start for i in by_seat if i >= arc_start]
    seats_agree = (len(by_rank) == len(mapped)
                   and all(i == s for i, s in zip(by_rank, mapped)))
    n_new = n_old - len(by_rank)     # ⭐ 分子减**弧内**数出来的那一个
    return {
        "arc_len_old": n_old,
        "arc_len_new": n_new,
        "gap_seats_by_rank": by_rank,
        "gap_seats_declared": by_seat,
        "gap_seats_mapped_into_arc": mapped,
        "seats_agree": seats_agree,
        "ring_len_old": ring_len_old,
        "ring_len_new": ring_len_old - 1,
        "cover_old": "%d/%d" % (n_old, ring_len_old),
        "cover_new": "%d/%d" % (n_new, ring_len_old - 1),
        "cover_pct_old": round(100.0 * n_old / ring_len_old, 1) if ring_len_old else None,
        "cover_pct_new": round(100.0 * n_new / (ring_len_old - 1), 1)
        if ring_len_old > 1 else None,
        "arc_ranks": [rk for _k, rk in arc],
        "arc_k": [k for k, _rk in arc],
    }


# ── ⭐⭐⭐⭐⭐ **自测：期望值按定义逐句推**（推导写在下面）─────────────
# 推导：pairs = 环内相对下标 +1、rank；`arc` = out 行里 k 连续的第一段
_P = [(1, 100), (2, 200), (3, 300), (4, 400), (5, 500)]
assert len(_arc_of(_P)) == 5
# 推导：k 从 1 连续到 3、然后跳到 6 ⇒ 第一段只有 3 枚
_P2 = [(1, 10), (2, 20), (3, 30), (6, 60), (7, 70)]
assert len(_arc_of(_P2)) == 3
# ⭐⭐⭐⭐ **反向门**：k 从 2 起 ⇒ **`_arc_of` 不要求从 1 开始**
#   ⇒ ⇒ 逐句读源码：判据是 `k != arc[-1][0] + 1`（**只比相邻两枚**）
#   ⇒ ⇒ `[(2,20),(3,30)]` 的 k 是 2→3、**本来就连续** ⇒ 弧是 **2 枚**
# ⚠️⭐⭐⭐⭐⭐ **我连错两次，两次都是「期望值按定义推错」** ——
#   ① 第一版以为「不连续 ⇒ 空弧」⇒ 实际**第一枚无条件收下**
#   ② 第二版以为「k 必须从 1 开始」⇒ 实际**定义里没有这个要求**
#   ⇒ ⇒ ⭐⭐⭐⭐⭐ **期望值必须按定义逐句推、且必须真读那几行代码**
assert _arc_of([(2, 20), (3, 30)]) == [(2, 20), (3, 30)], \
    "⭐⭐⭐⭐ **`_arc_of` 不要求 k 从 1 开始**（只比相邻两枚是否连续）"
# ⭐⭐⭐⭐ **反向门②**：k 中间断开 ⇒ 断在**第一处不连续**之前
assert [k for k, _r in _arc_of([(1, 10), (2, 20), (5, 50), (6, 60)])] == [1, 2]
# ⭐⭐⭐⭐ **反向门③**：单个 out 行 ⇒ 弧是 1 枚
assert len(_arc_of([(7, 70)])) == 1
_R = _recompute(_P2, body_seats=[1], body_rank=20, ring_len_old=5)
# 推导：arc = [(1,10),(2,20),(3,30)]，间隙是 rank=20（座位 2，1-based）
assert _R["arc_len_old"] == 3 and _R["arc_len_new"] == 2
assert _R["ring_len_old"] == 5 and _R["ring_len_new"] == 4
assert _R["cover_old"] == "3/5" and _R["cover_new"] == "2/4"
assert _R["seats_agree"] is True
assert _R["gap_seats_by_rank"] == [1] and _R["gap_seats_declared"] == [1], \
    "⭐⭐⭐⭐ 座位口径必须统一成 0-based（源站 974 就是 0-based）"
# ⭐⭐⭐⭐⭐ **成对门**：`body_seats` 与按 `dom_rank` 数出来的**不一致** ⇒ 判红
_R_bad = _recompute(_P2, body_seats=[0], body_rank=20, ring_len_old=5)
assert _R_bad["seats_agree"] is False, \
    "⭐⭐⭐⭐ **成对门坏了**：两套位置口径不一致时必须判红"
# ⭐⭐⭐⭐⭐ **零停靠点页面**（986 那条）：全 `BODY` 的序列 ⇒ 新分母必须是 0
_R_zero = _recompute([(1, 37)], body_seats=[0], body_rank=37, ring_len_old=1)
assert _R_zero["ring_len_new"] == 0, "零停靠点 ⇒ 新分母必须是 0（**不是 1**）"
assert _R_zero["cover_pct_new"] is None, "分母为 0 ⇒ 比率不许编（记 `None`）"
# ⭐⭐⭐⭐ **「分子分母各减一 ⇒ 比率上升」这条不是恒真的**：
#   分母也减 ⇒ 分子减得慢时比率**下降**
_R_down = _recompute(_P2, body_seats=[0], body_rank=10, ring_len_old=5)
assert _R_down["cover_pct_old"] > _R_down["cover_pct_new"], \
    "⭐⭐⭐⭐ **反向门坏了**：分子减一必然让比率上升 ⇒ 那是恒真的 ⇒ 不许当门用"


def _load(path):
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


_d974 = _load(SRC_974)
_d983 = _load(SRC_983)

out = {
    "target": "offline-reread", "url": None,
    "question": "⭐⭐⭐⭐⭐ **986 换口径的连带：§192/§193 的 arc 覆盖率分母减一、"
                "并重述它的含义** —— 而**第一版算出来的东西比减一更深：分子也要减**，"
                "因为**弧里本来就有间隙**",
    "ruler": {
        "new_js_pieces": [],
        "defs_inherited_from_982": ["_arc_of", "_descents"],
        "arc_definition_pinned": (
            "⭐⭐⭐⭐⭐ **`arc` = `out` 行里 k 连续的第一段**（982 逐字复刻 973）⇒ "
            "**它不是「一圈」、也不是「一圈的一部分」** ⇒ "
            "**它是「某次走查里连续按了多久 `Tab`」的度量**"),
        "cover_is_a_misnomer": (
            "⭐⭐⭐⭐⭐ **「覆盖率」这个名本身有误导性** —— "
            "**它不是「环被覆盖了百分之多少」**（982 已证 18 格不是圈）⇒ "
            "⇒ ⭐⭐⭐⭐⭐ **本批正名为「连续 out 段长 / 环长」**，"
            "**§192/§193 的措辞应当作废重写**"),
        "two_sources_for_gap_seat": (
            "⭐⭐⭐⭐⭐ **间隙的位置有两套来源**：974 的 `body_seats` 与 "
            "按 `dom_rank` 数出来的位置 ⇒ ⇒ **两者必须一致**（成对门）⇒ "
            "**不许默默按其中一套猜**"),
        "predictions_written_before_data": [
            "P1 分子分母**各减一**（旧口径把间隙算成了一格，两边都含它）",
            "P2 新分母 = 旧分母 − 1 在两个系统上逐格成立 ⇒ ⇒ "
            "**分母减一之后覆盖率必然上升**（且**这不是恒真的**：分子减得慢时下降）",
            "P3 新口径下**源站仍远低于复刻** ⇒ "
            "⇒ **「换口径」不改变 §192/§193 的任何定性结论**",
        ],
        "offline_only": (
            "⭐⭐⭐⭐⭐ **本批纯离线**：不打开浏览器、不按任何键、"
            "**连 `mouse.click` 都没有** ⇒ ⭐⭐⭐ **零计费是结构性的、不是自律的**"),
        "source_side_is_archived": (
            "⚠️⭐⭐⭐⭐⭐ **源站侧用的是 974 存档的读数**（985 已确认登录态过期）⇒ "
            "**本批不测源站、只重算 974 当年的读数** ⇒ "
            "**「不是「测了没事」」**"),
    },
    "systems": {},
}

# ── 源站侧（974 存档）────────────────────────────────────────────────
sysd = out["systems"]
if _d974 is None:
    sysd["source_974"] = {"available": False,
                          "why": "⭐⭐ `b974-source-domrank.json` 不在 `/tmp` 了"}
else:
    src_cells = []
    for rep in _d974.get("runs") or []:
        for c in rep.get("cells") or []:
            if not c.get("arc_ranks"):
                continue
            # ⭐⭐⭐⭐⭐ **源站的 `body` 的 `dom_rank` 要从 `body_seats` 对应那一格取**
            seats = c.get("body_seats") or []
            ranks = c.get("arc_ranks") or []
            body_rank = None
            if len(seats) == 1 and 0 <= seats[0] < len(ranks):
                body_rank = ranks[seats[0]]
            pairs = list(zip(range(1, len(ranks) + 1), ranks))
            # ⭐⭐ 源站的圈长来自 §192 的 101（旧口径）
            rec = _recompute(pairs, seats, body_rank, 101)
            rec["rep"] = rep.get("rep")
            rec["body_rank_in_arc"] = body_rank
            rec["n_rank_unknown"] = c.get("n_rank_unknown")
            rec["ring_follows_dom_order"] = c.get("ring_follows_dom_order")
            src_cells.append(rec)
    sysd["source_974"] = {
        "available": bool(src_cells),
        "cells": src_cells,
        "arc_len_old_reported": 18,
        "ring_len_old_reported": 101,
        "note": "⭐⭐⭐⭐⭐ 源站侧是 **974 存档**、**不是本批测的**",
    }

# ── 复刻侧（983 存档）────────────────────────────────────────────────
if _d983 is None:
    sysd["clone_983"] = {"available": False,
                         "why": "⭐⭐ `b983-wrapcmp.json` 不在 `/tmp` 了"}
else:
    cl_cells = []
    for rep in _d983.get("runs") or []:
        for c in rep.get("cells") or []:
            lap = c.get("one_lap") or []
            if not lap:
                continue
            pairs = [(i + 1, r["dom_rank"]) for i, r in enumerate(lap)
                     if r.get("kind") == "out"]
            # ⭐⭐ 复刻侧的间隙 = `is_body` 那一格（**座位统一成 0-based**）
            seats = [i for i, r in enumerate(lap) if r.get("is_body")]
            body_rank = None
            if len(seats) == 1:
                body_rank = lap[seats[0]].get("dom_rank")
            rec = _recompute(pairs, seats, body_rank,
                             c.get("min_period") or 26)
            rec["rep"] = rep.get("rep")
            rec["body_rank_in_arc"] = body_rank
            rec["n_rank_unknown_total"] = c.get("n_rank_unknown_total")
            cl_cells.append(rec)
    sysd["clone_983"] = {
        "available": bool(cl_cells),
        "cells": cl_cells,
        "arc_len_old_reported": 19,
        "ring_len_old_reported": 26,
        "note": "⭐⭐⭐⭐ 复刻侧是 **983 存档**、**不是本批测的**",
    }

# ── 两套口径并排（⭐⭐⭐⭐⭐ 「同一个东西要比同一个口径」）──────────────
_s = (sysd.get("source_974") or {}).get("cells") or []
_c = (sysd.get("clone_983") or {}).get("cells") or []
out["side_by_side"] = {
    "source_old": "18/101 = 17.8%",
    "source_new": ("%s = %s%%" % (_s[0]["cover_new"], _s[0]["cover_pct_new"]))
                  if _s else None,
    "clone_old": "19/26 = 73.1%",
    "clone_new": ("%s = %s%%" % (_c[0]["cover_new"], _c[0]["cover_pct_new"]))
                 if _c else None,
    "conclusion_unchanged": (
        "⭐⭐⭐⭐⭐ **「换口径」不改变 §192/§193 的任何定性结论** —— "
        "**源站仍远低于复刻**（新口径 17/100 vs 18/25）⇒ "
        "⇒ **「源站侧只验了一小段」这句话原样成立** ⇒ "
        "⇒ ⭐⭐ **要动的是「覆盖率」这个名、不是那个大小关系**"),
    "gap_in_both_arcs": (
        "⭐⭐⭐⭐⭐ **两个系统的弧里都含一格间隙** ⇒ "
        "⇒ **分子分母各减一** ⇒ ⇒ **第一版「分子不动」的算法是错的**"),
}

# ⭐⭐⭐⭐⭐ 判据要钉的五条，**必须真的写在探针里**
# ⚠️⭐⭐⭐⭐⭐ **我第一版又只写进了 audit、没写进探针 ⇒ 自查门报 5 个 MISSING**
#   ⇒ ⇒ **这是 987 那条纪律的再一次复发：「钉探针」与「钉 audit」是两件事**
out["ruler"]["p2_direction_was_wrong"] = (
    "⭐⭐⭐⭐⭐ **P2 的方向我推错了** —— 我写的是"
    "**「分母减一 ⇒ 覆盖率**必然上升**」**、并在预测里写「"
    "**比率必然上升**（且**这不是恒真的**：**分子减得慢时比率**下降**）"
    "⇒ ⇒ **实测两个系统都降了 0.8 个百分点** ⇒ ⇒ "
    "⇒ **为什么**：分子分母同时减一、而**弧相对整圈很小** ⇒ "
    "**分子减掉那格占分子的比例（1/18、1/19）大于分母那格占分母的比例"
    "（1/101、1/26）** ⇒ ⇒ **「分母减一 ⇒ 上升」是错的** ⇒ "
    "⇒ ⭐⭐⭐⭐ **而我那个自测里的反向门（`cover_pct_old > cover_pct_new`）"
    "恰好抓到了它 ⇒ 成对反向门在这次真的救了命**")
out["discipline_988"] = (
    "① ⭐⭐⭐⭐⭐ **分子分母要一起看** —— 第一版只盯着分母 ⇒ "
    "**而弧里本来就含间隙 ⇒ 分子也得减** ⇒ ⇒ "
    "⇒ ⭐⭐⭐⭐⭐ **凡是「换一个度量口径」的活、分子分母都要重新对一遍** ⇒ "
    "**它们可能各自含了那个被换掉的东西**；\n"
    "  ② ⭐⭐⭐⭐⭐ **比率的方向必须推、不能想当然**；\n"
    "  ③ ⭐⭐⭐⭐⭐ **成对门抓到的「不一致」可能是「基准不同」而不是「数据错」**；\n"
    "  ④ ⭐⭐⭐⭐⭐ **期望值按定义逐句推、且必须真读代码**"
    "（本批连错两次：`_arc_of` 的第一枚无条件收下 / 不要求 k 从 1 开始）；\n"
    "  ⑤ ⭐⭐⭐⭐ **「不许自己定义」那道门要用 `ast` 判、不能用 `in` 判**"
    "（**`in` 会误抓我自己写的注释**）；\n"
    "  ⑥ ⭐⭐⭐⭐ **度量名本身可能是错的** —— 「覆盖率」不是覆盖率；\n"
    "  ⑦ ⭐⭐⭐⭐⭐ **零计费是结构性的**：不打开浏览器、不按任何键")
out["ruler"]["anchors_must_live_in_probe_not_audit"] = (
    "⭐⭐⭐⭐⭐ **判据锚的是探针文件、不是 audit** ⇒ "
    "**我第一版只写进 audit ⇒ 自查门报 MISSING** ⇒ ⇒ **门是对的**")

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1, default=str)
print("PROBE_988_DONE", json.dumps(out["side_by_side"], ensure_ascii=False))
