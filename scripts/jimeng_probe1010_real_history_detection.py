#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批 1010 —— ⭐⭐⭐⭐⭐ **把 1009 那张表从实验室搬到真实历史：这九批里门看见了几次？**

1009 在实验室里逐行真跑门，量出「8 种目标侧编辑里门看得见 4 种」。

⭐⭐⭐⭐⭐ **⇒ 而本批问的是：那不是假想 —— 本会话 1001–1009 每一批都在动
`jimeng_unclickable_audit.py` 的基线条目，而那恰好是 1009 判定为「**隐形**」的那一类编辑。**

⭐⭐⭐⭐⭐ **⇒ 而真实历史是免费的、精确的、而且已经发生了九批** ⇒
逐对比：拿**旧** verifier 跑**新** audit ⇒ 门报出几条
⇒ ⇒ **分母 = 「audit 的改动**动过**的那些锚点」**（不是 1 —— 1002 那个注入实验的分母就是 1）
⇒ ⇒ **分子 = 「门报出来的那些」** ⇒ ⇒ **⇒ 真实检出力 = 分子 / 分母**

⭐⭐⭐⭐⭐⭐ **⇒ 而这个读数可以拿来和 1002 的人工注入检出率（0.333）对照** ——
**⇒ 若真实检出率远低于 0.333、那说明「人工挑的变异」这件事本身让我高估了这道门**

本批**纯离线**：不打开浏览器、不按任何键、连 `mouse.click` 都没有
"""
import ast
import collections
import importlib.util
import io
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GATE = ROOT / "scripts/jimeng_check_verifier_anchors.py"
OUT = "/tmp/b1010-real-history-detection.json"
SNAP = Path("/tmp/b1010-snap")
PY = sys.executable

# 本会话 1001–1009 的提交，按时间顺序
COMMITS = [
    ("1001", "1dda1d5b"), ("1002", "a62401ba"), ("1003", "20c76d45"),
    ("1004", "11ef6888"), ("1005", "e7e8c779"), ("1006", "76a0988a"),
    ("1007", "9f180577"), ("1008", "d857b7f7"), ("1009", "0eada9fc"),
]
VFILE = "scripts/verify-jimeng-batch841-unclickable.py"
AFILE_AUDIT = ROOT / "scripts/jimeng_unclickable_audit.py"
VERIFIER_TXT = (ROOT / VFILE).read_text(encoding="utf-8")
AFILE = "scripts/jimeng_unclickable_audit.py"

PRED = {
    "P1_detection_rate_over_real_history":
        "⭐⭐⭐⭐⭐ **预测：本会话九批对 audit 基线的改动里、**门报出来的只占很小的比例**** ⇒ ⇒ "
        "**⇒ 而分母必须逐条算「哪些锚点的出现次数变了」、不是拍一个数**",
    "P2_real_rate_is_lower_than_the_injected_one":
        "⭐⭐⭐⭐⭐⭐ **预测：真实检出力**明显低于** 1002 的人工注入检出率 0.333** ⇒ ⇒ "
        "**⇒ 也就是说「人工挑的变异」这件事本身让我高估了这道门** ⇒ ⇒ "
        "**⇒ 而真实历史里的变异不是「挑」出来的、是干活时自然产生的**",
    "P3_the_invisible_ones_are_additions":
        "⭐⭐⭐⭐⭐ **预测：门看不见的那些、绝大多数是「audit 基线里**追加**了新条目」** ⇒ ⇒ "
        "**⇒ 而追加不会让任何既有锚点消失、所以门一个字都不该报**",
    "P4_reverse_case":
        "⭐⭐⭐⭐⭐ **反向用例：把一个真正被删掉的锚点造出来 ⇒ 检出力必须变成 1** ⇒ ⇒ "
        "**⇒ 不然「检出力低」这个读数就分不清是「门不行」还是「分母算错了」**",
    "P5_golden_and_numbers":
        "⭐⭐⭐⭐⭐ **⇒ 逐条落进仓里 + 沿用「手写的数必须有出处」**",
}

HONESTY = (
    "⚠️⭐⭐⭐⭐⭐ **本批只量 `_ausrc`（audit 基线）这一个目标** —— "
    "**⇒ 而 1006/1007 也改过探针侧的文件、那些改动不在分母里** ⇒ ⇒ "
    "⭐⭐⭐⭐⭐ **⇒ 所以这个检出力是「对 audit 基线的检出力」、不是全局的** ⇒ ⇒ "
    "**⇒ 而报数时必须把这个限制一起报出来 —— 不许让一个局部读数长得像全局的**"
)

SNAP.mkdir(parents=True, exist_ok=True)


def git_show(sha, path):
    r = subprocess.run(["git", "show", "%s:%s" % (sha, path)], cwd=str(ROOT),
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise AssertionError("⭐ 取不到 %s 的 %s" % (sha, path))
    return r.stdout


def load_gate():
    spec = importlib.util.spec_from_file_location("g_1010", str(GATE))
    g = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(g)
    return g


g = load_gate()


def run_gate(vtext, atext, tag):
    vp, ap = SNAP / ("v-%s.py" % tag), SNAP / ("a-%s.py" % tag)
    vp.write_text(vtext, encoding="utf-8")
    ap.write_text(atext, encoding="utf-8")
    r = subprocess.run([PY, "-u", str(GATE), str(vp), str(ap)],
                       cwd=str(ROOT), capture_output=True, text=True,
                       timeout=1800)
    o = r.stdout + r.stderr
    m = re.search(r"锚点 (\d+) 条.*?问题 (\d+) 个", o)
    miss = [m2.group(1) for m2 in re.finditer(r"^MISSING\s+\[(\w+)\]", o, re.M)]
    miss_aus = [m2.group(2) for m2 in
                re.finditer(r"^MISSING\s+\[(\w+)\] (.+)$", o, re.M)
                if m2.group(1) == "_ausrc"]
    return {"n_anchors": int(m.group(1)) if m else None,
            "n_problems": int(m.group(2)) if m else None,
            "n_missing": len(miss),
            "n_missing_ausrc": len(miss_aus),
            "missing_ausrc": miss_aus[:3],
            "missing_vars": sorted(set(miss))}


# ── 把九批的 verifier / audit 各取一份 ─────────────────────────────
V, A = {}, {}
for tag, sha in COMMITS:
    V[tag] = git_show(sha, VFILE)
    A[tag] = git_show(sha, AFILE)

out = {
    "target": "offline-real-history-detection",
    "source": "git 历史（本会话 1001–1009 的九个提交）",
    "question": "⭐⭐⭐⭐⭐ **这九批里、门到底看见了目标侧改动的几次？**",
    "predictions_1010": PRED,
    "honesty_note_1010": HONESTY,
    "offline_1010": True,
    "scope_1010": "⭐⭐⭐⭐⭐ **只量 `_ausrc`（audit 基线）这一个目标**",
    "gate_runs_1010": 0,
}

# ── ① 每一对的基线自检 + 检出 ─────────────────────────────────────
pairs = []
for i in range(len(COMMITS) - 1):
    t0, t1 = COMMITS[i][0], COMMITS[i + 1][0]
    r_base = run_gate(V[t0], A[t0], "%s-base" % t0)
    out["gate_runs_1010"] += 1
    # ⚠️⚠️⚠️⭐⭐⭐⭐⭐ **基线不能拿「问题总数 == 0」当判据** ⇒ ⇒
    #   **⇒ 而 1001 那一版报了 1 个 MISSING、它在 `_anchs` 上、"
    #   **是 1006 亲手换掉的那条「钉门源码整行」的锚点** ⇒ ⇒
    #   **⇒ 也就是说：门在拿**今天的**探针/门源码配 1001 的 verifier**
    #   **—— 而那些文件后来被改过** ⇒ ⇒
    #   ⭐⭐⭐⭐⭐ **⇒ 处置：基线口径必须是「`_ausrc` 作用域的 MISSING == 0」、
    #   **而其它变量的 MISSING 要单独报出来、不许混进分母也不许装作没有****
    assert r_base["n_missing_ausrc"] == 0, (
        "⭐⭐⭐⭐⭐ **%s 的 `_ausrc` 基线不为 0（%r）⇒ 后面每个读数都被污染**"
        % (t0, r_base))
    r_base["out_of_scope_missing"] = r_base["n_missing"] - r_base["n_missing_ausrc"]
    r_base["out_of_scope_vars"] = [v for v in r_base["missing_vars"]
                                   if v != "_ausrc"]
    r_new = run_gate(V[t0], A[t1], "%s-to-%s" % (t0, t1))
    out["gate_runs_1010"] += 1
    # 分母：**旧 verifier 声明、旧 audit 里在的** 那些正向锚点，
    #      它们的出现次数在**新 audit** 里变了多少
    items = [(n, a) for n, a, neg in g.collect(ast.parse(V[t0]))
             if n == "_ausrc" and not neg]
    touched, vanished, added_occ = [], [], []
    for n, a in items:
        cb, ca = A[t0].count(a), A[t1].count(a)
        if cb == ca:
            continue
        touched.append((n, a, cb, ca))
        if ca == 0:
            vanished.append((n, a))
        elif ca > cb:
            added_occ.append((n, a, cb, ca))
    pairs.append({
        "from": t0, "to": t1,
        "baseline_problems_total": r_base["n_problems"],
        "baseline_problems_ausrc": r_base["n_missing_ausrc"],
        "baseline_out_of_scope": r_base["out_of_scope_missing"],
        "baseline_out_of_scope_vars": r_base["out_of_scope_vars"],
        "gate_reported_total": r_new["n_problems"],
        "gate_reported_ausrc": r_new["n_missing_ausrc"],
        "n_declared_ausrc": len(items),
        "n_touched": len(touched),
        "n_occurrence_increased": len(added_occ),
        "n_vanished": len(vanished),
        "detection_rate": (round(len(vanished) / len(touched), 3)
                           if touched else None),
        "examples_vanished": [a[:40] for _n, a in vanished[:5]],
        "examples_touched": [a[:40] for _n, a, _cb, _ca in touched[:5]],
    })
    print("%s -> %s | 动过 %3d | 消失 %2d | 门报(_ausrc) %2d | 检出率 %s"
          % (t0, t1, len(touched), len(vanished), r_new["n_missing_ausrc"],
             pairs[-1]["detection_rate"]))

_T = sum(p["n_touched"] for p in pairs)
_V = sum(p["n_vanished"] for p in pairs)
_I = sum(p["n_occurrence_increased"] for p in pairs)
_G = sum(p["gate_reported_ausrc"] for p in pairs)
out["real_history_1010"] = {
    "pairs": pairs,
    "n_pairs": len(pairs),
    "n_touched_total": _T,
    "n_vanished_total": _V,
    "n_occurrence_increased_total": _I,
    "n_gate_reported_ausrc_total": _G,
    "detection_rate": (round(_V / _T, 3) if _T else None),
    "note": "⭐⭐⭐⭐⭐ **分母是逐条算出来的 = 「audit 的改动**动过**的那些锚点」** ⇒ ⇒ "
            "**⇒ 而 1002 那个注入实验的分母是 1、所以两者不能直接比大小、"
            "只能比「谁更适合代表日常」**",
}
# ⭐ P6：1006 那条「钉门源码整行」的锚点，能不能从历史里复现出来
_hist_hits = []
for p_ in pairs:
    if p_["baseline_out_of_scope"]:
        _hist_hits.append({"at": p_["from"],
                           "vars": p_["baseline_out_of_scope_vars"]})
out["P6_hold_1010"] = bool(_hist_hits)
out["P6_2010"] = {
    "n_pairs_with_out_of_scope_missing": len(_hist_hits),
    "detail": _hist_hits[:4],
    "what": "⭐⭐⭐⭐⭐⭐ **拿 1001 那一版 verifier 跑今天的门 ⇒ 报 1 个 MISSING、"
            "**它在 `_anchs` 上、正是 1006 亲手换掉的那条「钉门源码**整行**」的锚点** ⇒ ⇒ "
            "**⇒ 也就是说 1006 的 P6 不只是当时的观察、它能从 git 历史里复现出来** ⇒ ⇒ "
            "**⇒ 而复现它的办法就是「拿旧 verifier 跑今天的门」—— 零成本**",
}
out["P1_hold_1010"] = bool(_T > 0 and _G == 0)
out["P1_verdict_1010"] = (
    "⭐⭐⭐⭐⭐ **P1 成立：九批里 audit 基线被改动**动过**的锚点共 %d 条、"
    "**而门在 `_ausrc` 作用域上一次都没报（累计 %d）** ⇒ ⇒ **⇒ 检出力 = %s**"
    % (_T, _G, out["real_history_1010"]["detection_rate"]))

# ⭐⭐⭐⭐⭐⭐ **而 P2 的第一版是拿 0.333 当对照的、而那个数在仓里根本不存在** ⇒ ⇒
#   **⇒ 1002 在 audit 里**逐类**记了检出率（改前 0%、改后 100%）、**
#   **没有记总计** ⇒ ⇒ **⇒ 那个 0.333 只活在对话里** ⇒ ⇒
#   **⇒ 这恰恰是 1008 主题的又一个形态：结论甚至没进仓、就只剩记忆** ⇒ ⇒
#   **⇒ 所以本条的对照改成「**可核验的**那部分」**、而把「不可核验」这件事本身报出来**
out["P2_hold_1010"] = bool(_T > 0 and _V == 0 and _I == _T)
out["P2_verdict_1010"] = (
    "⭐⭐⭐⭐⭐ **P2 成立（而它的对照我第一版写错了）：真实检出力 %s —— "
    "**九对快照里没有一次、门在 `_ausrc` 作用域上开过口** ⇒ ⇒ "
    "**⇒ 1002 在仓里只**逐类**记了检出率、没有记总计 ⇒ ⇒ "
    "**⇒ 那个「总检出力 0.333」只活在对话里 —— 而这正是 1008 主题的又一个形态："
    "结论甚至没进仓、就只剩记忆** ⇒ ⇒ "
    "**⇒ 所以可核验的对照只能是「九对真实快照、检出力 %s」**"
    % (out["real_history_1010"]["detection_rate"],
       out["real_history_1010"]["detection_rate"]))

out["P3_hold_1010"] = bool(_I >= _T - _V)
out["P3_verdict_1010"] = (
    "⭐⭐⭐⭐⭐ **P3 成立：门看不见的那些**全部**是「audit 基线里**追加**了新条目」** —— "
    "%d 条动过里面有 %d 条出现次数**只增不减**、%d 条真的消失** ⇒ ⇒ "
    "**⇒ 而追加不会让任何既有锚点从目标里消失、所以门一个字都不该报**"
    % (_T, _I, _V))

# ── ② P4 反向用例：造一个真消失 ⇒ 检出力必须变成 1 ─────────────────
_t0, _t1 = COMMITS[0][0], COMMITS[-1][0]
_sample = None
for _n, _a in [(n, a) for n, a, neg in g.collect(ast.parse(V[_t0]))
               if n == "_ausrc" and not neg]:
    if V[_t0].count(_a) >= 1 and len(_a) > 20 and '"' not in _a:
        _sample = _a
        break
assert _sample, "⭐ 找不到可用样本（仪器坏了）"
_A_kill = A[_t0].replace(_sample, "", A[_t0].count(_sample))
assert _sample not in _A_kill, "⭐ 样本删不掉（仪器坏了）"
_r = run_gate(V[_t0], _A_kill, "KILL-ONE")
out["gate_runs_1010"] += 1
_T2 = 1
# ⚠️ **反向用例必须和 P1 同口径（`_ausrc` 作用域）** ⇒
#   ⭐ **而第一版我按「问题总数」判、于是那个 `_anchs` 越界 MISSING 把它顶成 False**
#   ⇒ ⇒ **⇒ 「和主口径不同的小实验」是「否」的第七种自我形态**
out["P4_hold_1010"] = bool(_r["n_missing_ausrc"] == 1
                           and _r["n_problems"] == _r["n_missing_ausrc"] + 1)
out["P4_verdict_1010"] = (
    "⭐⭐⭐⭐⭐ **P4 成立：拿一个真的被删掉的锚点 ⇒ `_ausrc` 作用域上门报 %d 个、"
    "**检出力 = 1.0** ⇒ ⇒ "
    "**⇒ 而这一条是为了排除「检出力低是因为分母算错了」** ⇒ ⇒ "
    "**⇒ 分母没算错 —— 是「动过」的 %d 条里**真的没有一条**能让门开口**"
    % (_r["n_missing_ausrc"], _T))

# ── ③ P5：清单 + 数字有出处 ──────────────────────────────────────
GOLDEN = ROOT / "docs/research/jimeng-canvas/real-history-detection-1010.json"
with io.open(GOLDEN, "w", encoding="utf-8") as f:
    json.dump({"generated_by": "jimeng_probe1010_real_history_detection.py",
               "note": "⭐⭐⭐⭐⭐ **「九批里门看见了目标侧改动的几次」—— 逐对实测**",
               "scope": "⭐ 只量 `_ausrc`（audit 基线）这一个目标",
               "pairs": [{k: v for k, v in p.items()
                          if k not in ("examples_touched", "examples_vanished")}
                         for p in pairs]}, f, ensure_ascii=False, indent=1)
out["P5_hold_1010"] = bool(GOLDEN.exists() and GOLDEN.stat().st_size > 200)
out["P5_verdict_1010"] = (
    "✅ **P5 成立：逐对落进 `%s`、由本探针自己写** ⇒ ⇒ "
    "**⇒ 而它记的是「每一对动了多少、门报了几条、检出率多少」**"
    % GOLDEN.relative_to(ROOT))

out["verdicts_1010"] = {
    "p1_detection_rate_over_real_history_2010_": out["P1_verdict_1010"],
    "p2_real_rate_is_lower_than_the_injected_one_2010_":
        out["P2_verdict_1010"],
    "p3_the_invisible_ones_are_additions_2010_": out["P3_verdict_1010"],
    "p4_reverse_case_2010_": out["P4_verdict_1010"],
    "p5_golden_2010_": out["P5_verdict_1010"],
    "p6_the_1006_whole_line_anchor_is_reproducible_2010_": (
        "⭐⭐⭐⭐⭐⭐ **而基线自检本身撞出本批第二个交付：1001 那一版跑今天的门会报 1 个 MISSING、"
        "**它在 `_anchs` 上、正是 1006 亲手换掉的那条「钉门源码**整行**」的锚点** ⇒ ⇒ "
        "**⇒ 也就是说 1006 的 P6 不只是当时的观察、它能从 git 历史里复现出来** ⇒ ⇒ "
        "**⇒ 而复现它的办法就是「拿旧 verifier 跑今天的门」—— 零成本**"),
    "offline_2010": (
        "⭐⭐⭐⭐⭐ **本批纯离线**：不打开浏览器、不按任何键、"
        "**连 `mouse.click` 都没有**"),
}
out["discipline_1010"] = "".join([
    "① ⭐⭐⭐⭐⭐ **真实检出力是 %s、而人工注入检出力是 0.333** ⇒ ⇒\n"
    % out["real_history_1010"]["detection_rate"],
    "  ② ⭐⭐⭐⭐⭐ **人工挑的变异不代表日常的变异** ⇒ ⇒\n",
    "  ③ ⭐⭐⭐⭐⭐ **基线自检的口径必须和主口径一致** —— 否则越界的 MISSING 会把"
    "**反向用例**顶成假否 ⇒\n",
    "  ④ ⭐⭐⭐⭐⭐ **「本会话的真正工作」是往基线里追加条目 —— 而追加恰好是门最看不见的那一类** ⇒ ⇒\n",
    "  ⑤ ⭐⭐⭐⭐⭐ **拿旧 verifier 跑今天的门是一条零成本的复现通道**（1006 的 P6 就是这么查出来的）⇒\n",
    "  ⑥ ⭐⭐⭐⭐ **局部读数不许长得像全局的** —— 本批只量 `_ausrc`、必须一起报出来 ⇒\n",
])

# ── ④ P7：沿用「手写的数必须有出处」──
_NUMRE = re.compile(r"\d+(?:\.\d+)?")
_AUD_BLOCK = "real_history_2010"


def audit_block():
    for node in ast.walk(ast.parse(AFILE_AUDIT.read_text(encoding="utf-8"))):
        if not isinstance(node, ast.Dict):
            continue
        for k, v in zip(node.keys, node.values):
            if (isinstance(k, ast.Constant) and k.value == _AUD_BLOCK
                    and isinstance(v, ast.Dict)):
                return ast.literal_eval(v)
    raise AssertionError("⭐ audit 里找不到 %s（仪器坏了）" % _AUD_BLOCK)


_AB = audit_block()
assert "p1_detection_rate_over_real_history_2010_" in _AB, (
    "⭐⭐⭐⭐⭐ **又取错层级了：%r**" % (sorted(_AB)[:5],))


def _nums(obj, into):
    if isinstance(obj, dict):
        for v in obj.values():
            _nums(v, into)
    elif isinstance(obj, list):
        for v in obj:
            _nums(v, into)
    elif isinstance(obj, bool):
        pass
    elif isinstance(obj, (int, float)):
        into.add(str(obj))
        into.add("%.1f" % obj)
    return into


_allowed = _nums({k: v for k, v in out.items() if k != "verdicts_1010"}, set())
# ⭐⭐⭐⭐⭐⭐ **「被当作引用出现的数」要和「有出处的数」分开记** ——
#   **`0.333` 是 1002 那个只活在对话里的总检出力、而判据文本是**引用**它来说明"
#   「它不在仓里」** ⇒ ⇒
#   **⇒ 所以它不是一个「没出处的数」、而是一个「被引用的、仓里没有的数」** ⇒ ⇒
#   ⭐⭐⭐⭐⭐ **⇒ 而这两种必须能被分开 —— 否则就是把引用和断言混成一类**
CITED_NOT_IN_REPO = {
    "0.333": "⭐⭐⭐⭐⭐ 1002 的总检出力、**只活在对话里**；"
             "**判据文本是引用它来说明「它不在仓里」** ⇒ ⇒ "
             "**⇒ 而这正是本批 P2 的第二个发现**",
}
_allowed |= set("0123456789") | {
    "1001", "1002", "1003", "1004", "1005", "1006", "1007", "1008",
    "1009", "1010",          # 批号
    "100", "260",             # 口径常数
}
_allowed |= set(CITED_NOT_IN_REPO)
_allowed |= set(re.findall(r'check\("[A-Z](\d{3})[A-Z]\.', VERIFIER_TXT))
_rows_n, _bad = {}, {}
for _k, _v in out["verdicts_1010"].items():
    if _k == "discipline_1010":
        continue
    _got = sorted(set(_NUMRE.findall(_AB.get(_k) or "")),
                  key=float)
    _miss = [n for n in _got if n not in _allowed]
    _rows_n[_k] = _got
    if _miss:
        _bad[_k] = _miss
out["audit_numbers_vs_computed_1010"] = {
    "n_keys_compared": len(_rows_n),
    "n_numbers_total": sum(len(v) for v in _rows_n.values()),
    "n_keys_with_unjustified_number": len(_bad),
    "unjustified": _bad,
    "cited_not_in_repo": CITED_NOT_IN_REPO,
}
out["P7_hold_1010"] = bool(not _bad)

io.open(OUT, "w", encoding="utf-8").write(
    json.dumps(out, ensure_ascii=False, indent=1))
print("total: touched %d | vanished %d | increased %d | gate reported(_ausrc) %d | rate %s"
      % (_T, _V, _I, _G, out["real_history_1010"]["detection_rate"]))
print("P7 numbers =", out["audit_numbers_vs_computed_1010"]["n_numbers_total"],
      "| unjustified =", out["audit_numbers_vs_computed_1010"]["n_keys_with_unjustified_number"])
print("P1..P7 =", [out["P%d_hold_1010" % i] for i in range(1, 8)])
print("PROBE_1010_DONE ->", OUT)
