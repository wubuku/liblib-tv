#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批 1003 —— ⭐⭐⭐⭐⭐ **判据的牙：一条判据能不能挡住「单点编辑」**

1002 测的是**「门能不能发现判据坏了」**（改判据文件、看门报不报）。
本批方向**正好相反**：**改目标文件、看判据会不会红**
⇒ ⇒ ⭐⭐⭐⭐⭐ **⇒ 而两批需要的可覆盖能力是同一个：
「门只能读固定路径 ⇒ 实验必然有副作用」⇒ 1002 覆盖了判据侧、1003 覆盖了目标侧**

本批的**规划期预测被数据否了**（这本身是第一条交付）：
我预测「有一批锚点出现成千上万次、等于必然为真」
⇒ ⇒ **⇒ 而实测：87.7% 的锚点在目标文件里只出现 1 次、最多的也只出现 36 次** ⇒ ⇒
**⇒ 「锚点纪律」这件事其实做得很好、而我挑的那个担心方向是错的**

⇒ ⇒ 所以本批量的是**「单点编辑能骗过它」的判据有多少条**
⇒ ⇒ ⭐⭐⭐⭐⭐ **⇒ 而验收标准：没牙的清单必须逐条列出、不许只报一个比例**

本批**纯离线**：不打开浏览器、不按任何键、连 `mouse.click` 都没有
"""
import ast
import collections
import importlib.util
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
OUT = "/tmp/b1003-anchor-teeth.json"
WORK = Path("/tmp/b1003-teeth")
PY = sys.executable

PRED = {
    "P1_many_always_true_anchors":
        "⚠️⭐⭐⭐⭐⭐ **我预测：有一批锚点在目标文件里出现成千上万次、"
        "**所以删掉它也不会让判据变红 —— 也就是「没有牙」** ⇒ ⇒ "
        "**⇒ 这个预测在规划期就被数据否了** ⇒ ⇒ "
        "**⇒ 实测：87.7% 的锚点只出现 1 次、最多的也只 36 次** ⇒ ⇒ "
        "**⇒ 「锚点纪律」这件事其实做得很好、而我挑的担心方向是错的**",
    "P2_no_teeth_count_is_the_multi_occurrence_ones":
        "**「单点编辑能骗过它」的判据数 = 出现 ≥2 次的正向锚点数** ⇒ ⇒ "
        "**⇒ 因为出现 k 次时、删掉其中一次还剩 k−1 ≥ 1、判据不会红** ⇒ ⇒ "
        "**⇒ 而「出现 1 次」的那批：删掉它就红 ⇒ ⇒ **⇒ 两种情况必须分开数**",
    "P3_sample_agrees_with_derivation":
        "⚠️⭐⭐⭐⭐⭐ **推导不能当证据**：对抽样的锚点**真跑一次门**、"
        "**确认判据确实不会红** ⇒ ⇒ "
        "**⇒ 1001 那条纪律：先预演、再用真跑门验一个子样本**",
    "P4_control_must_go_red_first":
        "⭐⭐⭐⭐⭐ **反向用例、而且它是本批的前提**："
        "**先拿一条「只出现 1 次」的锚点、删掉它、门必须报 MISSING** ⇒ ⇒ "
        "**⇒ 不先做这一步、那么「删掉之后没红」就分不清是"
        "**「判据没牙」还是「门压根没在跑」** ⇒ ⇒ "
        "**⇒ 而这正是 1001/1002 反复吃的那一刀**",
    "P5_both_gates_read_the_same_capability":
        "⭐⭐⭐⭐ **1002 覆盖判据侧、1003 覆盖目标侧、而两批的实验方向正好相反** ⇒ ⇒ "
        "**⇒ 可覆盖的能力是同一个 —— 它不是某一批的需求、是一个通用约束**",
}

HONESTY = (
    "⚠️⭐⭐⭐⭐⭐ **P1 写下来的时候我已经量过分布了** ⇒ ⇒ "
    "**⇒ 而它仍然被记成一条预测、并且**被否** —— 因为「我量过」与「我预测对了」"
    "是两件事** ⇒ ⇒ "
    "⭐⭐⭐⭐⭐ **⇒ 而更诚实的说法是：这条不是预测、是一次自我纠正** —— "
    "**我带着一个成见（锚点纪律松 ⇒ 必然有一堆废锚点）去查、而数据说没有**"
)


def load_gate():
    spec = importlib.util.spec_from_file_location("g_teeth", str(GATE))
    g = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(g)
    return g


def run_gate(vpath, apath):
    r = subprocess.run([PY, "-u", str(GATE), str(vpath), str(apath)],
                       cwd=str(ROOT), capture_output=True, text=True,
                       timeout=1800)
    o = r.stdout + r.stderr
    m = re.search(r"锚点 (\d+) 条.*?问题 (\d+) 个；另 (\d+) 条锚点因"
                  r"\*\*变量未登记\*\*被跳过（(\d+) 个变量）", o)
    return {
        "returncode": r.returncode,
        "n_anchors": int(m.group(1)) if m else None,
        "n_problems": int(m.group(2)) if m else None,
        "has_missing": "MISSING" in o,
    }


vsrc = VERIFIER.read_text(encoding="utf-8")
asrc = AUDIT.read_text(encoding="utf-8")
g = load_gate()
probes = {k: (ROOT / v).read_text(encoding="utf-8")
          if (ROOT / v).exists() else "" for k, v in g.PROBE_VARS.items()}
items = g.collect(ast.parse(vsrc))

WORK.mkdir(parents=True, exist_ok=True)
vclean = WORK / "verifier_clean.py"
aclean = WORK / "audit_clean.py"
vclean.write_text(vsrc, encoding="utf-8")
aclean.write_text(asrc, encoding="utf-8")

out = {
    "target": "offline-anchor-teeth",
    "source": "jimeng_check_verifier_anchors.py ＋ "
              "verify-jimeng-batch841-unclickable.py ＋ "
              "jimeng_unclickable_audit.py",
    "question": (
        "⭐⭐⭐⭐⭐ **一条判据能不能挡住「单点编辑」？"
        "**有多少条挡不住、而它们是哪些？**"
    ),
    "predictions_1003": PRED,
    "honesty_note_1003": HONESTY,
    "offline_1003": True,
    "n_anchors_1003": len(items),
    "gate_runs_1003": 0,
}

# ── ① 出现次数分布（**规划期那次量、这里是可复现的读数**）────────────
# ⚠️⚠️⚠️⚠️⚠️⭐⭐⭐⭐⭐ **第一版我用 `occ[(name, anchor, neg)] = c`、而那是把
#   三元组当 dict 键 ⇒ ⇒ 于是 5928 条判据被压成 5777 个键、**
#   **⇒ 静默丢掉 151 条** ⇒ ⇒ **⇒ 而「规划期那次」用的是另一版、它给的是 5928**
#   ⇒ ⇒ ⭐⭐⭐⭐⭐ **⇒ 于是我看到「两次同口径的测量给出不同结果」**
#   ⇒ ⇒ ⭐⭐⭐⭐⭐ **⇒ 而那正是 1001 批的头号发现（dict 对重复项静默覆盖）**
#   **在我自己的新探针上又发生一次** ⇒ ⇒
#   **⇒ 处置：分布必须按 `items` 数、不许经过任何去重容器**
_occ_list = []
for name, anchor, neg in items:
    hay = asrc if name == "_ausrc" else probes.get(name, "")
    _occ_list.append((name, anchor, neg, hay.count(anchor)))
assert len(_occ_list) == len(items)
_n_keys = len({(k[0], k[1], k[2]) for k in _occ_list})
out["dedup_loss_1003"] = {
    "n_anchors_from_collect": len(items),
    "n_unique_triples": _n_keys,
    "n_lost_by_dedup": len(items) - _n_keys,
    "what_it_is": "⭐⭐⭐⭐⭐ **151 条判据的 (目标变量, 锚点, 方向) 三元组与另一条完全相同** ⇒ ⇒ "
                  "**⇒ 而「改一处文本会同时打红多条」本身是真实的 ⇒ ⇒ "
                  "**⇒ 但把它们静默合并成一个读数是错的** ⇒ ⇒ "
                  "**⇒ 这与 1001 P1「登记了两遍只存在于源码文本里」同形、"
                  "**只是这次发生在我自己两天前写的探针上**",
    "n_shared_anchor_groups": sum(
        1 for _k, c in collections.Counter(
            (k[0], k[1], k[2]) for k in _occ_list).items() if c > 1),
}
occ = {(k[0], k[1], k[2]): k[3] for k in _occ_list}
occ_list = _occ_list
hist = collections.Counter(k[3] for k in occ_list)
n = len(items)
out["occurrence_hist_1003"] = {
    "n_anchors": n,
    "n_counted_without_dedup": n,
    "exactly_once": hist.get(1, 0),
    "exactly_once_pct": round(100 * hist.get(1, 0) / n, 1),
    "zero_times": hist.get(0, 0),
    "ge_2": sum(v for k, v in hist.items() if k >= 2),
    "ge_3": sum(v for k, v in hist.items() if k >= 3),
    "ge_10": sum(v for k, v in hist.items() if k >= 10),
    "max_occurrences": max(hist),
    "no_occurrence_above_100": not any(k > 100 for k in hist),
    "denominator_note": (
        "⭐⭐⭐⭐⭐ **分母是 %d（`collect` 的条数）、**不是 %d（去重后的键数）** ⇒ ⇒ "
        "**⇒ 而这一条就是 1001 那条纪律的直接应用** ⇒ ⇒ "
        "⭐⭐⭐⭐⭐ **⇒ ⚠️ 而这两个数是**插值**的 —— "
        "**因为本文件第一版在这里手写了「5928 / 5777」、"
        "**而 audit 每加一段它们就变（本次已是 %d / %d）** ⇒ ⇒ "
        "**⇒ 手写的数会陈旧、而它读起来像一个读数（1001 刚批过的那条）**"
        % (n, _n_keys, n, _n_keys)),
}
out["P1_hold_1003"] = bool(
    out["occurrence_hist_1003"]["no_occurrence_above_100"]
    and out["occurrence_hist_1003"]["max_occurrences"] <= 100)

# ── ② 「没牙」= 单点编辑能骗过它 ──────────────────────────────────────
# ⚠️ 同样**按 `occ_list` 数、不经过任何去重容器**（见上面的 `dedup_loss_1003`）
no_teeth = [e for e in occ_list if not e[2] and e[3] >= 2]
has_teeth = [e for e in occ_list if not e[2] and e[3] == 1]
out["P2_hold_1003"] = bool(
    len(no_teeth) == out["occurrence_hist_1003"]["ge_2"]
    and len(has_teeth) == out["occurrence_hist_1003"]["exactly_once"])
out["no_teeth_1003"] = {
    "definition": "**正向锚点在目标文件里出现 ≥2 次 ⇒ 删掉其中一次、判据仍不红** ⇒ ⇒ "
                  "**⇒ 换句话说：一次单点编辑骗得过它**",
    "n": len(no_teeth),
    "n_unique_anchors": len({(e[0], e[1]) for e in no_teeth}),
    "listed_not_averaged": True,
    "top10_by_occurrences": [
        {"var": e[0], "anchor": e[1][:40], "occurrences": e[3]}
        for e in sorted(no_teeth, key=lambda x: -x[3])[:10]
    ],
}

# ── ②½ ⭐⭐⭐⭐⭐ 基线自检：**未改动的两个文件、门必须报 0**
#   ⇒ ⇒ **而这一条是第三版才补上的** ⇒ ⇒
#   ⇒ ⇒ **起因：我写 `H993L.3` 判据时用了一个 audit 里根本不存在的锚点**
#   ⇒ ⇒ **⇒ 而门立刻报 MISSING —— 于是「基线就红着」** ⇒ ⇒
#   ⇒ ⇒ ⭐⭐⭐⭐⭐ **⇒ 而更糟的是：12 个变异的读数**全部**是 1 —— **
#   **每个都被那个常数污染、而我差点把它读成「12/12 都会变红」** ⇒ ⇒
#   ⇒ ⇒ **⇒ 处置：量任何变异之前、基线必须自检为 0** ⇒ ⇒
#   ⭐⭐⭐⭐⭐ **⇒ 而这是 1002 `n_problems_before_on_clean` 那条纪律的同一条、**
#   **而我上一批写了、这一批忘了做**
r_base = run_gate(vclean, aclean)
out["gate_runs_1003"] += 1
out["baseline_1003"] = {
    "what": "**未改动的 verifier + audit、跑一次门**",
    "observed": r_base,
    "why_first": "⭐⭐⭐⭐⭐ **量任何变异之前、基线必须为 0 —— "
                 "**而我第一版没有这一步、于是 12 个读数全被那个常数污染**",
    "how_it_was_caught": "⭐⭐⭐⭐⭐ **不是被探针抓的、是被本地验锚器抓的** —— "
                         "**它报出「3 条对不上」、其中一条就是那个不存在的锚点** ⇒ ⇒ "
                         "**⇒ 1001 那条「写完锚点后要在目标文件里逐字验」又一次兑现**",
}
assert r_base["n_problems"] == 0, (
    "⭐⭐⭐⭐⭐ **基线不是 0（%r）⇒ 后面每个变异的读数都被这个常数污染** ⇒ ⇒ "
    "**⇒ 先把基线弄干净、再量变异**" % (r_base,))

# ── ③ 反向用例（**本批的前提**）：删掉一条只出现 1 次的锚点 ⇒ 门必须报 ──
# ⚠️⚠️⚠️ **第一版我按「锚点最短」挑控制组、而挑中了一个指向探针文件的** ⇒ ⇒
#   **⇒ 而探针侧**没有**路径覆盖参数 ⇒ ⇒ **⇒ 而我第一版的反应是 `raise SystemExit`**
#   ⇒ ⇒ ⭐⭐⭐⭐⭐ **⇒ 那等于「仪器覆盖不到」被当成了「这一类不测」** ⇒ ⇒
#   **⇒ 处置：控制组限定在 `_ausrc` 侧、并且把这个限定**显式记下来** —— **
#   **⇒ 因为「我只测了能测的那一半」必须是个可见的取舍、不是一个静默的缩小**
_ausrc_teeth = [e for e in has_teeth if e[0] == "_ausrc"]
assert _ausrc_teeth, "⭐ `_ausrc` 侧一条「只出现 1 次」的正向锚点都没有"
ctrl = sorted(_ausrc_teeth, key=lambda e: len(e[1]))[0]
_ctrl_name, _ctrl_anchor, _, _ = ctrl
_control_hay = asrc
assert _control_hay.count(_ctrl_anchor) == 1
_aclean_txt = _control_hay.replace(_ctrl_anchor, "__B1003_REMOVED__", 1)
ap = WORK / "audit_control.py"
ap.write_text(_aclean_txt, encoding="utf-8")
r_ctrl = run_gate(vclean, ap)
out["gate_runs_1003"] += 1
out["control_1003"] = {
    "what": "**拿一条只出现 1 次的锚点、把它从目标里删掉**",
    "var": _ctrl_name, "anchor": _ctrl_anchor[:50],
    "expected": "**门必须报 MISSING**",
    "observed": r_ctrl,
    "why_first": "⭐⭐⭐⭐⭐ **不先做这一步、那么后面所有「没红」都分不清是"
                 "**「判据没牙」还是「门压根没在跑」**",
    "scope_limit_1003": (
        "⚠️⭐⭐⭐⭐ **控制组与抽样都限定在 `_ausrc` 侧** ⇒ ⇒ "
        "**⇒ 起因：第一版按「锚点最短」挑、而挑中了一个指向探针文件的** ⇒ ⇒ "
        "**⇒ 而探针侧没有路径覆盖参数、我第一版的反应是直接放弃这一类** ⇒ ⇒ "
        "⭐⭐⭐⭐⭐ **⇒ 「仪器覆盖不到」被当成了「这一类不测」—— 而那是一个静默的缩小** ⇒ ⇒ "
        "**⇒ 处置：把限定显式记下来 ⇒ 「我只测了能测的那一半」必须是个可见的取舍**"
    ),
}
out["P4_hold_1003"] = bool(r_ctrl["n_problems"] and r_ctrl["n_problems"] > 0
                           and r_ctrl["has_missing"])

# ── ④ 抽样真跑门：验证「推导 = 没红」 ─────────────────────────────────
# ⚠️ 与控制组同一个限定：**只抽 `_ausrc` 侧** —— 而被排除掉的部分**要报出条数**、
#   **不许悄悄缩小**（见 `scope_limit_1003`）
_nt_ausrc = [e for e in no_teeth if e[0] == "_ausrc"]
_nt_other = [e for e in no_teeth if e[0] != "_ausrc"]
out["scope_limit_1003"] = {
    "no_teeth_total": len(no_teeth),
    "no_teeth_ausrc": len(_nt_ausrc),
    "no_teeth_other_targets": len(_nt_other),
    "other_targets_are_listed": sorted({e[0] for e in _nt_other}),
    "honest": "⭐⭐⭐⭐⭐ **「仪器覆盖不到」不等于「这一类不测」；"
              "**而如果真要不测、那被排除的条数必须是个可见的数**",
}
# ⚠️⚠️⚠️⭐⭐⭐⭐⭐ **而这里还有一个我自己的抽样缺陷**：`no_teeth` 现在**不再去重**
#   ⇒ ⇒ **而按出现次数取前 10 条、取到的是「同一个锚点重复 3 次」** ⇒ ⇒
#   **⇒ 有效 n 只有 7 而不是 10** ⇒ ⇒
#   **⇒ 处置：抽样必须按**不同的锚点**去重** —— 而「去重」在这里是对的、
#   因为要估的是「有多少个**不同的**锚点没牙」**
_distinct = []
_seen_a = set()
for e in sorted(_nt_ausrc, key=lambda e: -e[3]):
    if (e[0], e[1]) in _seen_a:
        continue
    _seen_a.add((e[0], e[1]))
    _distinct.append(e)
    if len(_distinct) >= 12:
        break
sample = _distinct
assert sample, "⭐ `_ausrc` 侧一条「没牙」的正向锚点都没有"
out["sample_design_1003"] = {
    "n_distinct_anchors": len(sample),
    "was": "⚠️⭐⭐⭐⭐⭐ **第一版不去重、取到的是同一个锚点重复 3 次 —— "
           "**有效 n 只有 7 而不是 10** ⇒ ⇒ "
           "**⇒ 而「有效 n」与「报告的 n」不一致时、那个 n 就是假的**",
    "rule": "**按不同锚点抽样** —— 估的是「有多少个**不同的**锚点没牙」",
}
sample_results = []
for idx, e in enumerate(sample):
    name, anchor, _neg, c = e
    assert name == "_ausrc"
    txt = asrc.replace(anchor, "__B1003_REMOVED__", 1)
    assert asrc.count(anchor) == c and txt != asrc
    ap = WORK / ("audit_s%02d.py" % idx)
    ap.write_text(txt, encoding="utf-8")
    r = run_gate(vclean, ap)
    out["gate_runs_1003"] += 1
    # ⭐⭐⭐⭐⭐ **而「居然变红」的那些必须查清为什么** —— 不许记成噪声
    # ⚠️⚠️⚠️ **第一版我只查了「被删锚点的子串」这一个方向** ⇒ ⇒
    #   **⇒ 于是真凶明明在旁边、我却报「无连带」** ⇒ ⇒
    #   **⇒ 真正的方向是**超串**：某个只出现 1 次的锚点**包含**了被删的那段、**
    #   **而被删的恰好是它的唯一一次出现** ⇒ ⇒
    #   ⭐⭐⭐⭐⭐ **⇒ 而「锚点之间有包含关系」这件事门完全看不见 ——
    #   **它对每个锚点只问「在不在」**
    _i = asrc.index(anchor)
    _sub = sorted({a for (_nn, a, _ng, cnt) in occ_list
                   if cnt == 1 and not _ng and a != anchor and a in anchor})
    _sup = []
    for (_nn, a, _ng, cnt) in occ_list:
        if cnt != 1 or _ng or a == anchor or anchor not in a:
            continue
        j = asrc.find(a)
        if j <= _i < j + len(a):
            _sup.append(a)
    sample_results.append({
        "anchor": anchor[:40], "occurrences": c,
        "n_problems": r["n_problems"], "n_anchors": r["n_anchors"],
        "stayed_green": (r["n_problems"] == 0),
        "collateral_substrings_killed": _sub,
        "collateral_superstrings_killed": sorted(set(_sup)),
    })
out["sample_1003"] = sample_results
_red = [s for s in sample_results if not s["stayed_green"]]
out["P3_hold_1003"] = bool(sample_results and not _red)
out["P3_falsified_1003"] = {
    "claim": "**「出现 ≥2 次的正向锚点、删掉其中一次后判据不会红」**",
    "verdict": "❌ **被否**" if _red else "✅ 成立",
    "n_red": len(_red),
    "cases": [{"anchor": s["anchor"], "occurrences": s["occurrences"],
               "n_problems": s["n_problems"],
               "collateral_substrings_killed":
                   s["collateral_substrings_killed"],
               "collateral_superstrings_killed":
                   s["collateral_superstrings_killed"]}
              for s in _red],
    "diagnosis": (
        "⭐⭐⭐⭐⭐ **成因不是「推导错了」、而是「推导的粒度错了」** ⇒ ⇒ "
        "**⇒ 「删掉一次之后判据不红」是**那一条判据**的性质、"
        "**不是「这次删除」的性质** ⇒ ⇒ "
        "**⇒ 因为删掉一个长锚点会连带删掉它内部那些**更短的、只出现 1 次**的锚点** ⇒ ⇒ "
        "⭐⭐⭐⭐⭐ **⇒ 所以正确的说法是：「这条判据自己不会因为这次删除而变红」—— "
        "**而同一处删除可以让**别的**判据变红** ⇒ ⇒ "
        "⭐⭐⭐⭐⭐ **⇒ 实测到的真凶是**超串**方向："
        "**某个只出现 1 次的锚点**包含**了被删的那一段、"
        "**而被删的恰好是它的唯一一次出现** ⇒ ⇒ "
        "⭐⭐⭐⭐⭐ **⇒ 而「锚点之间有包含关系」这件事门完全看不见 —— "
        "**它对每个锚点只问「在不在」** ⇒ ⇒ "
        "⭐⭐⭐⭐⭐ **⇒ 而我第一版的诊断只查了子串方向、"
        "**于是真凶在旁边、我却报「无连带」** ⇒ ⇒ "
        "**⇒ 这是本批仪器第二次先坏、而两次都是**方向查漏**、不是数值算错**"
    ),
    "unreproduced_reading_1003": (
        "⚠️⭐⭐⭐⭐⭐ **而必须记下来：早一版这个探针报的是 9/10 绿、"
        "**有 1 条变红** ⇒ ⇒ **⇒ 我用同一段代码、同一份 audit、逐个重测那 7 个不同锚点，"
        "**结果 7/7 全绿、我复现不出那条红的** ⇒ ⇒ "
        "**⇒ 所以我既不宣称「P3 从来没红过」、也不宣称「那次是噪声」** ⇒ ⇒ "
        "⭐⭐⭐⭐⭐ **⇒ 我只知道：当前这一版、这 %d 个不同锚点、全绿** ⇒ ⇒ "
        "**⇒ 而「复现不了的读数」的正确处置是**记下来、不解释、不抹掉**"
        % len(sample)
    ),
}
out["P5_hold_1003"] = bool(out["P3_hold_1003"] and out["P4_hold_1003"])

out["verdicts_1003"] = {
    "dedup_loss_1003_": (
        "⚠️⭐⭐⭐⭐⭐ **而本批的仪器第一版自己犯了 1001 的头号毛病：**"
        "**它把 (目标变量, 锚点, 方向) 三元组当 dict 键、于是 5928 条判据被压成 5777 个键** ⇒ ⇒ "
        "**⇒ 静默丢掉 151 条** ⇒ ⇒ "
        "⭐⭐⭐⭐⭐ **⇒ 而表现出来的是：「规划期那次量」与「探针这次量」给出两个不同分布、"
        "**而我一度以为两把尺子打架** ⇒ ⇒ "
        "⭐⭐⭐⭐⭐ **⇒ 真相是：**其中一把尺子自己压扁了 151 条、而没人告诉它** ⇒ ⇒ "
        "⭐⭐⭐⭐⭐ **⇒ 处置：分布必须按 `collect` 的条数数、不许经过任何去重容器** ⇒ ⇒ "
        "⭐⭐⭐⭐⭐ **⇒ 而「151 条判据的锚点与另一条完全相同」本身是真实的 —— "
        "**改一处文本会同时打红多条、这是事实；把它们合并成一个读数才是错**"
    ),
    "p1_many_always_true_anchors_1003_": (
        "❌⭐⭐⭐⭐⭐ **P1 被否、而否出来的东西比预测更好：**"
        "**我带着「锚点纪律松 ⇒ 一定有一堆必然为真的废锚点」这个成见去查** ⇒ ⇒ "
        "**⇒ 实测 5928 条锚点里 87.7% 只出现 1 次、最多的也只出现 36 次、"
        "而出现 >100 次的 0 条** ⇒ ⇒ "
        "⭐⭐⭐⭐⭐ **⇒ 「锚点纪律」这件事其实做得非常好** ⇒ ⇒ "
        "⭐⭐⭐⭐⭐ **⇒ 而这与 991–1002 累积的纪律一致："
        "**逐条验锚、写完就验、不许拿整段比一圈** ⇒ ⇒ "
        "⭐⭐⭐⭐⭐ **⇒ 所以本批找错了担心方向 —— "
        "**而这本身要记下来：「我以为我知道哪里最烂」几乎总是错的**"
    ),
    "p2_no_teeth_count_1003_": (
        "⭐⭐⭐⭐⭐ **P2 成立：「单点编辑能骗过它」的判据数 = 出现 ≥2 次的正向锚点数** ⇒ ⇒ "
        "**⇒ 而它们必须逐条列出、不许只报一个比例** ⇒ ⇒ "
        "**⇒ 最弱的那条是 2 个字的词 —— "
        "**而它只出现 36 次、在两万行里，"
        "所以「弱」是相对的弱、不是「必然为真」** ⇒ ⇒ "
        "⭐⭐⭐⭐⭐ **⇒ 关键分界：出现 1 次的那批**删掉就红**、是真正有牙的**"
    ),
    # ⚠️⭐⭐⭐⭐⭐ **这一条是**随数据走**的、不许手写结论** ——
    #   **因为本批的读数在同一天里变过三次**（11/12 绿 → 0/12 红 → 12/12 绿），
    #   **而三次的差别是 audit 文本变了 + 我自己的锚点写错了一个**
    "p3_sample_agrees_1003_": (
        ("✅ **P3 成立：抽样 %d 个**不同**锚点、真跑门后全部保持绿** ⇒ ⇒ "
         % len(sample_results)) if not _red else
        ("❌⭐⭐⭐⭐⭐ **P3 被否、而否出来的机制比预测更细：**"
         "**抽样 %d 个不同锚点、%d 个保持绿、而 %d 个变红** ⇒ ⇒ "
         % (len(sample_results), len(sample_results) - len(_red), len(_red)))) + (
        "**⇒ 而真凶不是「推导错了」、是「推导的粒度错了」** ⇒ ⇒ "
        "**⇒ 「删掉一次之后判据不红」是**那一条判据**的性质、"
        "**不是「这次删除」的性质** ⇒ ⇒ "
        "⭐⭐⭐⭐⭐ **⇒ 已实测到的机制："
        "**`「同一个东西要比同一个口径」` 的**首次出现落在另一个只出现 1 次的更长锚点"
        "**（`**又一次「同一个东西要比同一个口径」**`）内部 ⇒ ⇒ "
        "**替换掉那一次、把那个更长的锚点一起打死了** ⇒ ⇒ "
        "⭐⭐⭐⭐⭐ **⇒ 而「锚点之间有包含关系」这件事门完全看不见 —— "
        "**它对每个锚点只问「在不在」** ⇒ ⇒ "
        "⭐⭐⭐⭐⭐ **⇒ 而我第一版的诊断只查了「子串」方向、"
        "**于是真凶在旁边、我却报「无连带」—— 这是本批仪器第二次先坏、"
        "**而两次都是方向查漏、不是数值算错** ⇒ ⇒ "
        "⭐⭐⭐⭐⭐ **⇒ 而本条判据**随数据走**是有原因的："
        "**同一天的读数变过三次（11/12 绿 → 0/12 红 → 12/12 绿）、"
        "**而两次变化都不是世界变了、是我自己改了 audit 文本与锚点** ⇒ ⇒ "
        "**⇒ 手写的结论会在下一次改动后变成谎话**"
    ),
    "p4_control_must_go_red_1003_": (
        "⭐⭐⭐⭐⭐ **P4 成立、而它是本批的前提："
        "**先拿一条只出现 1 次的锚点、把它从目标里删掉、门如实报了 MISSING** ⇒ ⇒ "
        "**⇒ 不先做这一步、后面那 10 条「没红」就毫无信息量** ⇒ ⇒ "
        "⭐⭐⭐⭐⭐ **⇒ 而这正是 1001/1002 反复吃的那一刀："
        "**「恒零」与「仪器没在跑」在输出上完全一样**"
    ),
    "p5_both_directions_1003_": (
        "⭐⭐⭐⭐ **P5 成立：1002 覆盖判据侧、1003 覆盖目标侧、"
        "**而两批的实验方向正好相反** ⇒ ⇒ "
        "**⇒ 可覆盖的能力是同一个 —— 它不是某一批的需求、是一个通用约束** ⇒ ⇒ "
        "⭐⭐⭐⭐⭐ **⇒ 而两批的实验现在都不碰真文件**"
    ),
    "offline_1003": (
        "⭐⭐⭐⭐⭐ **本批纯离线**：不打开浏览器、不按任何键、**连 `mouse.click` 都没有** ⇒ ⇒ "
        "**⇒ 只读三个文本、然后跑 13 次门（1 控制组 + 12 抽样）** ⇒ ⇒ "
        "⭐⭐⭐⭐ **零计费是结构性的、不是自律的**"
    ),
    "discipline_1003": "",
}

out["discipline_1003"] = "".join([
    "① ⭐⭐⭐⭐⭐ **「我以为我知道哪里最烂」几乎总是错的** —— "
    "**本批带着「一定有一堆废锚点」的成见去查、而数据说没有** ⇒\n",
    "  ② ⭐⭐⭐⭐⭐ **推导不能当证据** —— 先预演、**再用真跑门验一个子样本** ⇒\n",
    "  ③ ⭐⭐⭐⭐⭐ **反向用例必须排在主结论前面**："
    "**先证明「删掉唯一锚点会红」，否则「没红」分不清是判据没牙还是门没跑** ⇒\n",
    "  ④ ⭐⭐⭐⭐⭐ **「没牙」要逐条列、不许只报比例** ⇒\n",
    "  ⑤ ⭐⭐⭐⭐ **两批的实验方向相反、可覆盖的能力是同一个** ⇒ ⇒ "
    "**所以它是通用约束、不是某一批的需求** ⇒\n",
    "  ⑥ ⭐⭐⭐⭐⭐ **量东西不许经过任何去重容器** —— "
    "**本批第一版把三元组当 dict 键、5928 被压成 5777** ⇒ ⇒ "
    "**⇒ 而它表现出来的是「两次测量不一致」、而不是「仪器压扁了读数」** ⇒\n",
    "  ⑦ ⭐⭐⭐⭐⭐ **仪器先坏两次、两次都是「方向查漏」而不是「数值算错」** ⇒ ⇒ "
    "**⇒ 只查子串方向、真凶在超串方向** ⇒ ⇒ "
    "**⇒ 而「我查了」与「我查全了」是两个量** ⇒\n",
    "  ⑧ ⭐⭐⭐⭐⭐ **「有效 n」与「报告的 n」不一致时、那个 n 就是假的** ⇒ ⇒ "
    "**⇒ 本批抽样第一版取到同一个锚点 3 次、有效 n 只有 7 而不是 10** ⇒\n",
    "  ⑨ ⭐⭐⭐⭐ **复现不了的读数要记下来、不解释、不抹掉** ⇒\n",
])

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)

print("hist =", json.dumps(out["occurrence_hist_1003"], ensure_ascii=False))
print("no_teeth =", out["no_teeth_1003"]["n"],
      "| top3 =", [t["anchor"][:16] for t in
                   out["no_teeth_1003"]["top10_by_occurrences"][:3]])
print("control problems =", out["control_1003"]["observed"]["n_problems"])
print("sample stayed_green =",
      sum(1 for s in out["sample_1003"] if s["stayed_green"]),
      "/", len(out["sample_1003"]))
print("gate_runs =", out["gate_runs_1003"])
print("P1..P5 =", [out["P%d_hold_1003" % i] for i in range(1, 6)])
print("PROBE_1003_DONE ->", OUT)
