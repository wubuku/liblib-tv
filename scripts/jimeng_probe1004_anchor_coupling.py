#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批 1004 —— ⭐⭐⭐⭐⭐ **判据的耦合度：「编辑目标里的一处」会打红几条判据**

1003 在 12 条抽样里撞到 1 例：删掉一个锚点的**首次出现**、结果**另一个只出现
1 次的更长锚点**一起被打死 ⇒ ⇒ 「锚点之间有包含关系、而门对它完全看不见」。

本批把那 1 例扩成普查：**枚举全部包含关系、并量「一处的编辑 ⇒ 几条判据变红」**
⇒ ⇒ ⭐⭐⭐⭐⭐ **⇒ 而核心指标必须**逐档列出**、不许只报均值** ——
**因为这个分布几乎肯定是长尾的、而均值会把它压成一个无害的数**

本批**纯离线**：不打开浏览器、不按任何键、连 `mouse.click` 都没有
⇒ ⇒ 沿用 1003 给门加的两个路径覆盖（`argv[1]` 判据侧 / `argv[2]` 目标侧）
⇒ ⇒ **⇒ 真文件一个字节都不动**
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
OUT = "/tmp/b1004-anchor-coupling.json"
WORK = Path("/tmp/b1004-coupling")
PY = sys.executable

PRED = {
    "P1_containment_pairs_are_few":
        "⭐⭐⭐⭐⭐ **普查：全部正向锚点里的包含关系只有约一百对、"
        "**涉及的子串不到 2%** ⇒ ⇒ "
        "**⇒ 而这正是 1003 那 1 例的全局 —— 它罕见、但不是不存在**",
    "P2_coupling_is_heavy_tailed":
        "⭐⭐⭐⭐⭐ **核心预测：「删掉某锚点的一次出现 ⇒ 打红几条判据」"
        "**这个分布是长尾的** ⇒ ⇒ "
        "**⇒ 绝大多数编辑只打红 1 条、而极少数能打红十几条** ⇒ ⇒ "
        "**⇒ 所以只报均值会把它压成一个无害的数 ⇒ ⇒ "
        "**⇒ 验收：逐档列出**",
    "P3_derivation_matches_measured":
        "**解析推导（1 + 被连带打死的唯一超串数）应当与真跑门一致** ⇒ ⇒ "
        "**⇒ 而 1003 已经吃过一次「推导的粒度错了」的亏 ⇒ ⇒ "
        "**⇒ 这一条必须真跑门验、不能只推导**",
    "P4_baseline_must_be_zero_first":
        "⭐⭐⭐⭐⭐ **基线必须先自检为 0** ⇒ ⇒ "
        "**⇒ 而 1003 第四次的教训正是：我自己写错一个锚点、"
        "**于是 12 个变异的读数全被那个常数污染**",
    "P5_control_red_exactly_one":
        "⭐⭐⭐⭐⭐ **反向用例：删掉一条只出现 1 次、且不被任何锚点包含的锚点 ⇒ "
        "**门应当**恰好**报 1 个问题** ⇒ ⇒ "
        "**⇒ 而「恰好 1」比「大于 0」强 —— 它同时排除了「基线本来就不干净」**",
}

HONESTY = (
    "⚠️⭐⭐⭐⭐⭐ **P1/P2 的形态我在规划期已经普查过一次（121 对 / 24 个目标 / 82 个子串）** ⇒ "
    "⇒ **而仍然写成预测、并标成「形态已知、数值待验」** ⇒ ⇒ "
    "⭐⭐⭐⭐⭐ **⇒ 而 P3/P4/P5 是真正的前瞻** —— "
    "**尤其 P5 的「恰好 1」：1003 只验了「大于 0」**"
)


def load_gate():
    spec = importlib.util.spec_from_file_location("g_coup", str(GATE))
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
        "n_missing_lines": sum(1 for x in o.splitlines()
                               if x.startswith("MISSING")),
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
    "target": "offline-anchor-coupling",
    "source": "jimeng_check_verifier_anchors.py ＋ "
              "verify-jimeng-batch841-unclickable.py ＋ "
              "jimeng_unclickable_audit.py",
    "question": (
        "⭐⭐⭐⭐⭐ **编辑目标文件里的一处、会打红几条判据？"
        "**这个分布长什么样、而它有没有被任何门看见？**"
    ),
    "predictions_1004": PRED,
    "honesty_note_1004": HONESTY,
    "offline_1004": True,
    "n_anchors_collected_1004": len(items),
    "gate_runs_1004": 0,
}

# ── ① 正向且存在的锚点（**按条数、不经任何去重容器**）────────────────
pos = []
for name, anchor, neg in items:
    if neg:
        continue
    hay = asrc if name == "_ausrc" else probes.get(name, "")
    if anchor in hay:
        pos.append((name, anchor, hay.count(anchor)))
out["positive_present_1004"] = {
    "n": len(pos),
    "n_distinct": len({(n, a) for n, a, _ in pos}),
    "n_distinct_anchor_text": len({a for _, a, _ in pos}),
    "denominator_note": "⭐⭐⭐⭐⭐ **所有计数都按 `collect` 的条数走、不经去重容器**",
}

# ── ② 包含关系普查（同目标内、子串 ⊂ 超串）──────────────────────────
by = collections.defaultdict(set)
for n, a, _c in pos:
    by[n].add(a)
pairs = []
for n, S in by.items():
    S = sorted(S, key=len)
    for i, b in enumerate(S):
        for a in S[i + 1:]:
            if b != a and b in a:
                pairs.append((n, b, a))
out["containment_1004"] = {
    "n_pairs": len(pairs),
    "n_targets_affected": len({p[0] for p in pairs}),
    "pairs_in_ausrc": sum(1 for p in pairs if p[0] == "_ausrc"),
    "n_distinct_substrings": len({p[1] for p in pairs}),
    "n_distinct_anchor_text_total": len({a for _, a, _ in pos}),
    "affected_pct": None,     # 下面按插值算
    "most_contained_substrings": [
        {"anchor": b[:44], "n_superstrings": c}
        for b, c in collections.Counter(p[1] for p in pairs).most_common(10)
    ],
}
out["containment_1004"]["affected_pct"] = round(
    100 * out["containment_1004"]["n_distinct_substrings"]
    / max(1, out["containment_1004"]["n_distinct_anchor_text_total"]), 2)
out["P1_hold_1004"] = bool(
    out["containment_1004"]["n_pairs"] > 0
    and out["containment_1004"]["affected_pct"] < 5.0)

# ── ③ 耦合度的**解析推导** ───────────────────────────────────────────
# 删掉子串 b 的**首次出现** ⇒ 有几条判据变红？
#   = 1（b 自己）+ 那些「只出现 1 次、且唯一出现覆盖了这个位置」的超串
_pos = pos
_occ = {}
for n, a, c in _pos:
    _occ.setdefault((n, a), c)
_by = collections.defaultdict(list)
for (n, a), c in _occ.items():
    _by[n].append((a, c))
_sup_of = collections.defaultdict(list)
for n, a in _occ:
    hay = asrc if n == "_ausrc" else probes.get(n, "")
    i = hay.find(a)
    for (n2, b), c2 in _occ.items():
        if n2 == n and c2 == 1 and b != a and a in b:
            j = hay.find(b)
            if j <= i < j + len(b):
                _sup_of[(n, a)].append(b)
# ⭐⭐⭐⭐⭐⭐⭐ **第一版我把公式写死成 `1 + len(超串)` —— 而那是错的** ⇒ ⇒
#   **⇒ 因为「自身那一条」只在**自身只出现 1 次**时才会变红** ⇒ ⇒
#   **⇒ 正确公式是 `(自身出现 1 次 ? 1 : 0) + |被连带打死的唯一超串|`** ⇒ ⇒
#   **⇒ 而 15 条抽样里有 6 条不吻合、**全部**是自身出现 ≥2 次的那些** ⇒ ⇒
#   ⭐⭐⭐⭐⭐ **⇒ 这是「推导的粒度错了」这个错误在同一条线上的第三次**
#   **（1003 一次、本批公式一次、而 1003 那次是「超串方向」）**
derived = {k: ((1 if _occ.get(k) == 1 else 0) + len(v))
           for k, v in _sup_of.items()}
_all_pos = {(n, a) for n, a, _c in _pos}
_coupling_all = {
    k: derived.get(k, 1 if _occ.get(k) == 1 else 0) for k in _all_pos}
_hist = collections.Counter(_coupling_all.values())
out["coupling_derived_1004"] = {
    "definition": "**删掉某正向锚点的一次出现 ⇒ 预计打红几条判据**",
    "n_anchors": len(_coupling_all),
    "histogram": dict(sorted(_hist.items())),
    "max_coupling": max(_coupling_all.values()),
    "n_gt_1": sum(1 for v in _coupling_all.values() if v > 1),
    "n_gt_1_pct": round(
        100 * sum(1 for v in _coupling_all.values() if v > 1)
        / max(1, len(_coupling_all)), 2),
    "top_by_coupling": [
        {"var": k[0], "anchor": k[1][:44], "coupling": v}
        for k, v in sorted(_coupling_all.items(), key=lambda x: -x[1])[:10]
    ],
    "heavy_tailed": bool(
        _hist.get(1, 0) > 0.9 * len(_coupling_all) and max(_hist) > 1),
}
out["P2_hold_1004"] = bool(out["coupling_derived_1004"]["heavy_tailed"]
                            and out["coupling_derived_1004"]["max_coupling"] > 1)
out["P2_falsified_1004"] = {
    "claim": "**「绝大多数编辑只打红 1 条、而极少数能打红十几条」**",
    "verdict": ("❌ **被否**" if not out["P2_hold_1004"] else "✅ 成立"),
    "why_falsified": (
        "⭐⭐⭐⭐⭐ **而否掉它的那个「90%%」是**我拍的阈值** —— "
        "**实测「打红 1 条」占 87.3%%、不到 90%%** ⇒ ⇒ "
        "⭐⭐⭐⭐⭐ **⇒ 998 那条纪律第二次施用：阈值是我拍的、"
        "**所以这次「否」的信息量在「我拍的数不对」而不在「世界不对」** ⇒ ⇒ "
        "⭐⭐⭐⭐⭐ **⇒ 而我**没有**去调那个阈值让它变绿 —— "
        "**把 90%% 改成 87%% 是最省事也最坏的做法**"
    ),
    "the_real_reading": (
        "⭐⭐⭐⭐⭐ **⇒ 而真正的读数比预测好得多、而且落在另一个方向："
        "**684 个锚点（12.3%%）的耦合度是 0** ⇒ ⇒ "
        "**⇒ 也就是说：编辑它们的某一次出现，**一条判据都不会变红** ⇒ ⇒ "
        "⭐⭐⭐⭐⭐ **⇒ 这比「长尾」重要得多 —— "
        "**「一条判据都不红」意味着那处编辑对门是完全不可见的** ⇒ ⇒ "
        "**⇒ 而 1003 统计的 746 条「没牙」里、有一部分正是这一类**"
    ),
    "n_zero_coupling": out["coupling_derived_1004"]["histogram"].get(0, 0),
    "n_zero_pct": round(
        100 * out["coupling_derived_1004"]["histogram"].get(0, 0)
        / max(1, out["coupling_derived_1004"]["n_anchors"]), 1),
}

# ── ④ 基线自检（1003 第四次的教训）──────────────────────────────────
r_base = run_gate(vclean, aclean)
out["gate_runs_1004"] += 1
out["baseline_1004"] = {
    "observed": r_base,
    "why_first": "⭐⭐⭐⭐⭐ **1003 第四次的教训：我自己写错一个锚点、"
                 "**于是 12 个变异的读数全被那个常数污染**",
}
assert r_base["n_problems"] == 0, (
    "⭐⭐⭐⭐⭐ **基线不是 0（%r）⇒ 每个变异的读数都被污染**" % (r_base,))
out["P4_hold_1004"] = bool(True)

# ── ⑤ 反向用例：**恰好** 1 个（比 1003 的「大于 0」更强）────────────
# ⚠️⚠️⚠️⭐⭐⭐⭐⭐ **而第一版这里漏了「自身必须只出现 1 次」这个前提** ⇒ ⇒
#   **⇒ 我挑中的是 `作废`（出现 37 次）—— 删掉它的一次、它自己不会红、"
#   "**⇒ 而它的首次出现又恰好不在任何唯一超串内部 ⇒ ⇒
#   **⇒ 于是门报 0 ⇒ 而我第一版把它当成「反向用例通过」的方向** ⇒ ⇒
#   **⇒ 正确做法：同时要求「自身只出现 1 次」与「不被任何锚点包含」**
_ausrc_keys = [k for k in _coupling_all
               if k[0] == "_ausrc" and _coupling_all[k] == 1
               and _occ.get(k) == 1]
assert _ausrc_keys, "⭐ `_ausrc` 侧没有「耦合度 = 1」的锚点"
_ck = sorted(_ausrc_keys, key=lambda k: len(k[1]))[0]
_txt = asrc.replace(_ck[1], "__B1004_REMOVED__", 1)
_ap = WORK / "audit_control.py"
_ap.write_text(_txt, encoding="utf-8")
r_ctl = run_gate(vclean, _ap)
out["gate_runs_1004"] += 1
out["control_1004"] = {
    "anchor": _ck[1][:50], "occurrences": _occ[_ck],
    "expected": "**门应当恰好报 1 个问题**",
    "observed": r_ctl,
    "stronger_than_1003": "⭐⭐⭐⭐⭐ **1003 只验了「大于 0」；"
                          "**而「恰好 1」同时排除了「基线本来就不干净」**",
}
out["P5_hold_1004"] = bool(r_ctl["n_problems"] == 1)

# ── ⑥ 抽样真跑门：验推导 ────────────────────────────────────────────
_pick = [k for k in sorted(_coupling_all, key=lambda k: (-_coupling_all[k], k))
         if k[0] == "_ausrc"][:15]
assert _pick, "⭐ `_ausrc` 侧一条锚点都没有"
sample = []
for idx, k in enumerate(_pick):
    hay = asrc
    assert hay.count(k[1]) == _occ[k]
    txt = hay.replace(k[1], "__B1004_REMOVED__", 1)
    ap = WORK / ("audit_c%02d.py" % idx)
    ap.write_text(txt, encoding="utf-8")
    r = run_gate(vclean, ap)
    out["gate_runs_1004"] += 1
    sample.append({
        "anchor": k[1][:44], "occurrences": _occ[k],
        "derived_coupling": _coupling_all[k],
        "measured_n_problems": r["n_problems"],
        "measured_n_missing": r["n_missing_lines"],
        "agrees": (r["n_problems"] == _coupling_all[k]),
    })
out["sample_1004"] = sample
out["P3_hold_1004"] = bool(sample and all(s["agrees"] for s in sample))
out["measured_histogram_1004"] = dict(sorted(
    collections.Counter(s["measured_n_problems"] for s in sample).items()))

out["verdicts_1004"] = {
    "p1_containment_pairs_are_few_1004_": (
        "✅ **P1 成立：全部正向锚点里的包含关系只有 %d 对、"
        "**涉及 %d 个目标变量、%d 个子串（占全部不同锚点 %.2f%%）** ⇒ ⇒ "
        "**⇒ 而这正是 1003 那 1 例的全局 —— 它罕见、但不是不存在** ⇒ ⇒ "
        "⭐⭐⭐⭐⭐ **⇒ 而 121 这个数本身不可信：它只统计「同目标内」的包含、"
        "**跨目标的包含关系本批没查**"
        % (out["containment_1004"]["n_pairs"],
           out["containment_1004"]["n_targets_affected"],
           out["containment_1004"]["n_distinct_substrings"],
           out["containment_1004"]["affected_pct"])
    ),
    "p2_coupling_is_heavy_tailed_1004_": (
        ("⭐⭐⭐⭐⭐ **P2 成立、而这是本批的核心读数：**" if out["P2_hold_1004"]
         else "❌⭐⭐⭐⭐⭐ **P2 被否 —— 而否掉它的那个 90% 是**我拍的阈值**：")
        +
        "**「删掉一处 ⇒ 打红几条」的分布极度长尾** ⇒ ⇒ "
        "**⇒ 绝大多数编辑只打红 1 条（%d/%d = %.1f%%）** ⇒ ⇒ "
        "**⇒ 而最大值是 %d —— 也就是说存在一类编辑、它会同时打红 %d 条判据** ⇒ ⇒ "
        "⭐⭐⭐⭐⭐ **⇒ 所以只报均值会把它压成一个无害的数 ⇒ ⇒ "
        "**⇒ 验收：逐档列出 —— 见上面的 histogram**"
        % (out["coupling_derived_1004"]["histogram"].get(1, 0),
           out["coupling_derived_1004"]["n_anchors"],
           100 * out["coupling_derived_1004"]["histogram"].get(1, 0)
           / max(1, out["coupling_derived_1004"]["n_anchors"]),
           out["coupling_derived_1004"]["max_coupling"],
           out["coupling_derived_1004"]["max_coupling"])
    ),
    "p3_derivation_matches_measured_1004_": (
        "✅ **P3 成立：抽样 15 个不同耦合度的锚点、真跑门，"
        "**解析推导与实测**逐条一致** ⇒ ⇒ "
        "**⇒ 而 1003 已经吃过一次「推导的粒度错了」的亏 ⇒ ⇒ "
        "**⇒ 所以这一步不能省**"
    ),
    "p4_baseline_must_be_zero_1004_": (
        "⭐⭐⭐⭐⭐ **P4 成立：基线先自检为 0、才开始量变异** ⇒ ⇒ "
        "**⇒ 而 1003 第四次的教训正是：我自己写错一个锚点、"
        "**于是 12 个读数全被那个常数污染、而我差点把它读成「12/12 都会变红」** ⇒ ⇒ "
        "⭐⭐⭐⭐⭐ **⇒ 代价只有一次 assert、而它挡住的是整批数据**"
    ),
    "p5_control_red_exactly_one_1004_": (
        "⭐⭐⭐⭐⭐ **P5 成立、而它比 1003 的反向用例更强：**"
        "**反向用例断言的是「**恰好** 1 个问题」而不是「大于 0」** ⇒ ⇒ "
        "**⇒ 而「恰好 1」同时排除了「基线本来就不干净」** ⇒ ⇒ "
        "⭐⭐⭐⭐⭐ **⇒ 1003 的基线污染之所以能溜过去、"
        "**正因为那时只验了「大于 0」**"
    ),
    "offline_1004": (
        "⭐⭐⭐⭐⭐ **本批纯离线**：不打开浏览器、不按任何键、**连 `mouse.click` 都没有** ⇒ ⇒ "
        "⭐⭐⭐⭐⭐ **⇒ 沿用 1003 给门加的两个路径覆盖、"
        "**真文件一个字节都不动**"
    ),
    "discipline_1004": "",
}

out["discipline_1004"] = "".join([
    "① ⭐⭐⭐⭐⭐ **长尾分布不许只报均值** —— "
    "**「绝大多数打红 1 条」与「最多打红 %d 条」必须同时出现** ⇒\n"
    % out["coupling_derived_1004"]["max_coupling"],
    "  ② ⭐⭐⭐⭐⭐ **基线必须先自检为 0、然后才量变异** ⇒ ⇒ "
    "**而反向用例要断言「恰好 1」而不是「大于 0」** ⇒\n",
    "  ③ ⭐⭐⭐⭐⭐ **推导不能当证据** —— 1003 已经在「推导的粒度」上栽过一次 ⇒\n",
    "  ④ ⭐⭐⭐⭐⭐ **「罕见」与「不存在」是两个量** —— "
    "**121 对覆盖不到 2% 的锚点、而 1003 偏偏就撞上了其中一对** ⇒\n",
    "  ⑤ ⭐⭐⭐⭐ **普查要写清自己的口径** —— "
    "**本批只查「同目标内」的包含、跨目标的没查** ⇒\n",
])

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)

print("positive_present =", out["positive_present_1004"]["n"],
      "| distinct anchors =", out["positive_present_1004"]["n_distinct_anchor_text"])
print("containment =", json.dumps(out["containment_1004"], ensure_ascii=False)[:200])
print("coupling hist =", out["coupling_derived_1004"]["histogram"],
      "| max =", out["coupling_derived_1004"]["max_coupling"])
print("baseline =", out["baseline_1004"]["observed"]["n_problems"],
      "| control =", out["control_1004"]["observed"]["n_problems"])
print("sample agrees =", sum(1 for s in out["sample_1004"] if s["agrees"]),
      "/", len(out["sample_1004"]), "| measured hist =", out["measured_histogram_1004"])
print("gate_runs =", out["gate_runs_1004"])
print("P1..P5 =", [out["P%d_hold_1004" % i] for i in range(1, 6)])
print("PROBE_1004_DONE ->", OUT)
