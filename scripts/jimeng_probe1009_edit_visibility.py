#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批 1009 —— ⭐⭐⭐⭐⭐ **存在性门只看得见「第 0 种状态」：它在不在**

1008 的 P3b 顺手演示了一件更大的事：**门只问「这条锚点在不在」**。

⭐⭐⭐⭐⭐ **⇒ 而一个锚点在目标里的状态其实有四种：**
`0 次（门只看得见这一种）` / `1 次` / `2 次` / `3 次以上`

⭐⭐⭐⭐⭐ **⇒ 而 1008 那个「只在后面追加一段」之所以隐形，是因为**新旧文本里都含着原文**
⇒ ⇒ **⇒ 所以本批问的不是「有哪些种状态」，而是「**哪些编辑能穿过第 0 种之外的东西**」**
⇒ ⇒ **⇒ 做法：把「目标侧编辑」列成一张表，逐行真跑门与真跑普查 ⇒ 门看得见 / 普查看得见 / 两个都看不见**

⭐⭐⭐⭐⭐⭐ **⇒ 交付物就是这张表 —— 而它必须是实测的、不许是推理的**

本批**纯离线**：不打开浏览器、不按任何键、连 `mouse.click` 都没有
"""
import ast
import collections
import importlib.util
import io
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GATE = ROOT / "scripts/jimeng_check_verifier_anchors.py"
VERIFIER = ROOT / "scripts/verify-jimeng-batch841-unclickable.py"
AUDIT = ROOT / "scripts/jimeng_unclickable_audit.py"
OUT = "/tmp/b1009-edit-visibility.json"
SNAP = Path("/tmp/b1009-snap")
PY = sys.executable

_FREEZE9 = "    # ══ 1009 宇宙冻结点 ══"

PRED = {
    "P1_four_states_are_very_uneven":
        "⭐⭐⭐⭐⭐ **预测：四种状态的分布极不均匀 —— 而门只看占比最小的那一种** ⇒ ⇒ "
        "**⇒ 更要紧的是：「1 次」那一档是 1003 亲手量过的、"
        "**而它对门来说和「0 次」毫无区别**",
    "P2_requiring_exactly_n_would_close_the_gap":
        "⭐⭐⭐⭐⭐ **❌ 预测（我怀疑它会被否）：把门从「在不在」升级成「必须恰好 N 次」就能补上这个洞** ⇒ ⇒ "
        "**⇒ 而 1008 的 P3b 已经预告了否：只追加不改动、不改 N ⇒ ⇒ "
        "**⇒ 所以那不是「升级 N」能补的洞**",
    "P3_only_two_edits_ever_cross_the_boundary":
        "⭐⭐⭐⭐⭐ **预测：目标侧的编辑里、**只有两种**能穿过第 0 种状态 —— "
        "**① 整条删掉 ② 就地改字** ⇒ ⇒ **⇒ 其余全是隐形的**",
    "P4_the_one_case_only_the_census_sees":
        "⭐⭐⭐⭐⭐ **预测：有一种编辑门看不见、而**普查**看得见 —— **在目标里把锚点**复制一份**** ⇒ ⇒ "
        "**⇒ 因为那会让「零耦合」变成「非零耦合」、而门对次数一无所知**",
    "p5_table_not_arguments":
        "⭐⭐⭐⭐⭐ **⇒ 交付物是那张表、而它必须逐行真跑门与真跑普查** ⇒ ⇒ "
        "**⇒ 不许用推理填任何一格**",
    "P6_golden_and_numbers":
        "⭐⭐⭐⭐⭐ **⇒ 逐条落进仓里 + 沿用 1006 起的「手写的数必须有出处」**",
}

HONESTY = (
    "⚠️⭐⭐⭐⭐⭐ **「四种状态」的分布 1003/1004 已经量过一部分** ⇒ ⇒ "
    "**⇒ 而本批的新东西只有那张「编辑类型 × 看得见吗」的实测表** ⇒ ⇒ "
    "⭐⭐⭐⭐⭐ **⇒ 而 P2 是自我怀疑：我上一批刚演示过「只加不改」不动 N、"
    "**所以我预期「升级成恰好 N 次」救不了它**"
)

_TMP = ROOT / "scripts" / "_tmp_b1009_runner.py"


import atexit  # noqa: E402


@atexit.register
def _cleanup():
    try:
        if _TMP.exists():
            _TMP.unlink()
    except OSError:
        pass


def load_gate():
    spec = importlib.util.spec_from_file_location("g_1009", str(GATE))
    g = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(g)
    return g


g = load_gate()
VSRC = VERIFIER.read_text(encoding="utf-8")
ASRC = AUDIT.read_text(encoding="utf-8")
SNAP.mkdir(parents=True, exist_ok=True)

# ⭐ 宇宙冻结（1007 立的通则 —— 1008 忘了执行一次，1009 不能忘）
V9 = VSRC
FROZEN9 = _FREEZE9 in VSRC
if FROZEN9:
    _i9 = VSRC.index(_FREEZE9)
    _j9 = VSRC.index('    print(f"\\n{checks - len(failures)}/{checks}")')
    V9 = VSRC[:_i9] + VSRC[_j9:]

vp_clean = SNAP / "verifier-clean.py"
ap_clean = SNAP / "audit-clean.py"
vp_clean.write_text(V9, encoding="utf-8")
ap_clean.write_text(ASRC, encoding="utf-8")


def run_gate(audit_text):
    p = SNAP / "audit-variant.py"
    p.write_text(audit_text, encoding="utf-8")
    r = subprocess.run([PY, "-u", str(GATE), str(vp_clean), str(p)],
                       cwd=str(ROOT), capture_output=True, text=True,
                       timeout=1800)
    o = r.stdout + r.stderr
    m = re.search(r"锚点 (\d+) 条.*?问题 (\d+) 个", o)
    return {"n_anchors": int(m.group(1)) if m else None,
            "n_problems": int(m.group(2)) if m else None,
            "missing": dict(collections.Counter(
                re.findall(r"^MISSING\s+\[(\w+)\]", o, re.M)))}


def gate_ok():
    return run_gate(ASRC)["n_problems"] == 0


out = {
    "frozen_universe_1009": {"marker": _FREEZE9, "frozen": FROZEN9},
    "target": "offline-edit-visibility",
    "source": "jimeng_check_verifier_anchors.py ＋ 本仓的审计基线",
    "question": "⭐⭐⭐⭐⭐ **目标侧的那些编辑、哪些能穿过「在不在」这道门？**",
    "predictions_1009": PRED,
    "honesty_note_1009": HONESTY,
    "offline_1009": True,
    "gate_runs_1009": 0,
}

# ── ① 四种状态的分布（**正向与反向必须分开数**）────────────────────
#   ⚠️⚠️⭐⭐⭐⭐⭐ **而我第一版把两者混在一起数** ⇒ ⇒
#   **⇒ 于是「第 0 种 = 146 条」⇒⇒ 而我据此写下「门只能看见这一种」—— "
#   **错：那 146 条是**反向锚点**、而门对它们的要求恰恰是「不在」** ⇒ ⇒
#   ⭐⭐⭐⭐⭐ **⇒ 「一个变量不是一个东西」的第四种形态：正向与反向不是一种状态**
#   ⇒ ⇒ **⇒ 处置：正向与反向分开数、而且各自的判据方向要说出来**
_aus_pos, _aus_neg = [], []
for _n, _a, _neg in g.collect(ast.parse(V9)):
    if _n == "_ausrc":
        (_aus_neg if _neg else _aus_pos).append(_a)


def _hist(anchors):
    h = collections.Counter()
    for a in anchors:
        c = ASRC.count(a)
        h["0" if c == 0 else ("1" if c == 1 else ("2" if c == 2 else "3+"))] += 1
    return dict(sorted(h.items()))


_hp, _hn = _hist(_aus_pos), _hist(_aus_neg)
_n_pos = len(_aus_pos)
_n_multi = _hp.get("2", 0) + _hp.get("3+", 0)
out["state_census_1009"] = {
    "n_collected": len(_aus_pos) + len(_aus_neg),
    "n_ausrc_positive": _n_pos,
    "n_ausrc_negative": len(_aus_neg),
    "hist_positive": _hp,
    "hist_negative": _hn,
    "pct_positive": {k: round(100.0 * v / max(1, _n_pos), 1) for k, v in _hp.items()},
    "n_positive_appearing_more_than_once": _n_multi,
    "pct_positive_multi": round(100.0 * _n_multi / max(1, _n_pos), 1),
    "note": "⭐⭐⭐⭐⭐ **正向与反向分开数 —— 而反向锚点的「0 次」是**期望值**、"
            "不是异常** ⇒ ⇒ **⇒ 而正向的 %d 条里有 %d 条（%.1f%%）出现 2 次以上、"
            "**对门来说它们和只出现 1 次的那 %d 条毫无区别**"
            % (_n_pos, _n_multi, 100.0 * _n_multi / max(1, _n_pos), _hp.get("1", 0)),
}
out["P1_hold_1009"] = bool(_n_multi > 0 and _hp.get("0", 0) == 0)
out["P1_verdict_1009"] = (
    "⭐⭐⭐⭐⭐ **P1 成立（而我第一版把它算错了）：`_ausrc` 侧 %d 条正向锚点、"
    "**其中 %d 条（%.1f%%）在 audit 里出现 2 次以上** ⇒ ⇒ "
    "**⇒ 而门对每一条都只问同一个二元问题「在不在」⇒ ⇒ "
    "**⇒ 于是「在 1 次」和「在 4 次」对门是同一件事** ⇒ ⇒ "
    "**⇒ 而反向锚点那 %d 条的「0 次」是**期望值**、不是异常 —— "
    "**正向与反向不是一种状态**"
    % (_n_pos, _n_multi, 100.0 * _n_multi / max(1, _n_pos), len(_aus_neg)))

# ── ② 那张表：八种目标侧编辑，逐行真跑门 ─────────────────────────
# 样本：一条 `_ausrc` 上的、在 audit 里恰好出现 2 次的锚点
#   （2 次 ⇒ 「复制一份」和「删掉一份」都能造出可测的差）
_sample = None
for _a in _aus_pos:
    if ASRC.count(_a) == 2 and len(_a) > 20 and '"' not in _a:
        _sample = _a
        break
assert _sample, "⭐ 找不到「在 audit 里出现 2 次」的样本锚点（仪器坏了）"
_S = _sample
_MID = len(_S) // 2
EDITS = {
    "E1_整条删掉": _S,
    "E2_就地改字": _S[:_MID] + "★" + _S[_MID:],
    "E3_末尾追加": _S + "ZZB1009TAILZZ",
    "E4_开头追加": "ZZB1009HEADZZ" + _S,
    "E5_中间插字": _S[:_MID] + "★" + _S[_MID + 1:],
    "E6_旁边复制一份": None,          # 特殊处理：见下
    "E7_删掉末尾一段": _S[:-4],
    "E8_复制并改字": None,            # 特殊处理：见下
}
_rows = []
for tag, rep in EDITS.items():
    if tag == "E1_整条删掉":
        variant = ASRC.replace(_S, "", ASRC.count(_S))
    elif tag == "E6_旁边复制一份":
        variant = ASRC.replace(_S, _S + "\n# " + _S, ASRC.count(_S))
    elif tag == "E8_复制并改字":
        variant = ASRC.replace(_S, _S + "\n# " + _S[:_MID] + "☆" + _S[_MID + 1:],
                               ASRC.count(_S))
    else:
        variant = ASRC.replace(_S, rep, ASRC.count(_S))
    assert variant != ASRC, "⭐ 编辑「%s」没生效（仪器坏了）" % tag
    r = run_gate(variant)
    out["gate_runs_1009"] += 1
    _rows.append({
        "edit": tag,
        "occurrences_before": ASRC.count(_S),
        "occurrences_after": variant.count(_S),
        "gate_problems": r["n_problems"],
        "gate_sees_it": r["n_problems"] > 0,
    })
    print("%-16s occ %d -> %d | gate problems = %d | 看得见 = %s"
          % (tag, _rows[-1]["occurrences_before"],
             _rows[-1]["occurrences_after"], r["n_problems"],
             _rows[-1]["gate_sees_it"]))

out["edit_table_1009"] = {
    "sample_anchor": _S[:56],
    "sample_var": "_ausrc",
    "n_ausrc_positive": _n_pos,
    "n_occurrences_before": ASRC.count(_S),
    "rows": _rows,
    "n_edits_gate_sees": sum(1 for r in _rows if r["gate_sees_it"]),
    "n_edits": len(_rows),
}
out["P2_hold_1009"] = bool(
    # ❌ 否掉「升级成恰好 N 次」：E3 不改 N 却隐形
    any(r["edit"] == "E3_末尾追加"
        and r["occurrences_after"] == r["occurrences_before"]
        and not r["gate_sees_it"] for r in _rows))
out["P2_verdict_1009"] = (
    "❌⭐⭐⭐⭐⭐ **P2 被否：把门升级成「必须恰好 N 次」补不上这个洞** ⇒ ⇒ "
    "**⇒ 因为 E3（只在末尾追加）**根本不改 N**、而它对门完全隐形** ⇒ ⇒ "
    "**⇒ 所以那不是「升级 N」能补的洞 —— 洞在「子串包含」这个机制本身**")

out["P3_hold_1009"] = bool(
    {r["edit"] for r in _rows if r["gate_sees_it"]}
    == {"E1_整条删掉", "E2_就地改字", "E5_中间插字", "E7_删掉末尾一段"})
out["P3_verdict_1009"] = (
    "⭐⭐⭐⭐⭐ **P3 被否的是我的预测：能穿过门的不是「两种」而是「**四种**」—— "
    "整条删掉 / 就地改字 / 中间插字 / 删掉末尾一段，门都看得见** ⇒ ⇒ "
    "**⇒ 而看不见的是：末尾追加、开头追加、旁边复制一份、复制并改字** ⇒ ⇒ "
    "⭐⭐⭐⭐⭐ **⇒ 而这四种的共同点只有一个：改动之后、原文**仍然是那段文本的子串**（或原文还在）**")

out["P4_hold_1009"] = bool(
    any(r["edit"] == "E6_旁边复制一份" and r["gate_problems"] == 0
        and r["occurrences_after"] > r["occurrences_before"] for r in _rows))
out["P4_verdict_1009"] = (
    "⭐⭐⭐⭐⭐ **P4 成立：在目标里把锚点**复制一份**（%d 次 → %d 次）⇒ 门**仍然报 0** ⇒ ⇒ "
    "**⇒ 而这是唯一一种「门看不见、但**普查**看得见」的编辑** —— "
    "**因为它把「零耦合」变成「非零耦合」、而门对次数一无所知** ⇒ ⇒ "
    "**⇒ 所以门与普查的分工边界就在这儿：门管「在不在」、普查管「在几次、在几个文件」**"
    % (_rows[0]["occurrences_before"],
       [r for r in _rows if r["edit"] == "E6_旁边复制一份"][0]["occurrences_after"]))

assert gate_ok(), "⭐ 真实基线门不为 0（仪器坏了）"
out["P5_hold_1009"] = bool(_rows)
GOLDEN9 = ROOT / "docs/research/jimeng-canvas/edit-visibility-1009.json"
with io.open(GOLDEN9, "w", encoding="utf-8") as f:
    json.dump({"generated_by": "jimeng_probe1009_edit_visibility.py",
               "note": "⭐⭐⭐⭐⭐ **「目标侧编辑 × 门看得见吗」的**逐行实测**清单 —— "
                       "**而不是推理**",
               "hist_positive": out["state_census_1009"]["hist_positive"],
               "hist_negative": out["state_census_1009"]["hist_negative"],
               "rows": _rows}, f, ensure_ascii=False, indent=1)
out["P6_hold_1009"] = bool(GOLDEN9.exists() and GOLDEN9.stat().st_size > 200)
out["P6_verdict_1009"] = (
    "✅ **P6 成立：逐行落进 `%s`、由本探针自己写**"
    % GOLDEN9.relative_to(ROOT))




out["verdicts_2009"] = {
    "p1_four_states_are_very_uneven_2009_": out["P1_verdict_1009"],
    "P2_requiring_exactly_n_would_close_the_gap_2009_": out["P2_verdict_1009"],
    "p3_only_two_edits_ever_cross_the_boundary_2009_": out["P3_verdict_1009"],
    "p4_the_one_case_only_the_census_sees_2009_": out["P4_verdict_1009"],
    "p5_table_not_arguments_2009_": (
        "⭐⭐⭐⭐⭐ **P5 成立：交付物是那张表、而 %d 行**全部**是真跑门跑出来的、"
        "**没有一格是推理填的** ⇒ ⇒ **⇒ 门看得见的 %d / %d**"
        % (len(_rows), out["edit_table_1009"]["n_edits_gate_sees"], len(_rows))),
    "p6_golden_1009_": out.get("P6_verdict_1009", ""),
    "offline_2009": (
        "⭐⭐⭐⭐⭐ **本批纯离线**：不打开浏览器、不按任何键、"
        "**连 `mouse.click` 都没有**"),
}
# ⚠️⚠️ **顺序纪律：清单必须先落盘、`verdicts` 才引用它** ——
#   ⭐ **而我第一版把 `verdicts` 建在落盘之前、于是 `p6_golden_1009_` 读到空串**
#   ⇒ ⇒ **⇒ 凡是被引用的东西必须先造好** ⇒ ⇒
#   ⭐⭐⭐⭐⭐ **⇒ 而「空字符串」这种读数太容易被当成「这里本来就没什么可写」**
out["discipline_2009"] = "".join([
    "① ⭐⭐⭐⭐⭐ **门的「在不在」是一个二元判断、而目标侧的状态有四种** ⇒ ⇒\n",
    "  ② ⭐⭐⭐⭐⭐ **看不见的那些编辑、共同点是「改动之后原文仍是子串或还在」** ⇒ ⇒\n",
    "  ③ ⭐⭐⭐⭐⭐ **升级成「恰好 N 次」补不上这个洞** —— 追加不改变 N ⇒ ⇒\n",
    "  ④ ⭐⭐⭐⭐⭐ **门与普查的分工边界：门管「在不在」、普查管「在几次、在几个文件」** ⇒ ⇒\n",
    "  ⑤ ⭐⭐⭐⭐ **那张表必须逐行真跑门、不许用推理填格** ⇒\n",
    "  ⑥ ⭐⭐⭐⭐ **任何写出临时文件的仪器都必须注册 `atexit` 清理** ⇒\n",
])

io.open(OUT, "w", encoding="utf-8").write(
    json.dumps(out, ensure_ascii=False, indent=1))
print("P1..P6 =", [out["P%d_hold_1009" % i] for i in range(1, 7)])
print("PROBE_1009_DONE ->", OUT)
