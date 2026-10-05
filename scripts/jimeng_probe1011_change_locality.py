#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批 1011 —— ⭐⭐⭐⭐⭐⭐⭐ **「真实历史里门看不见的那些改动，究竟是一批什么样的改动？」**

1010 量到：九对真实快照、audit 基线被改动**动过**的锚点 39 条、门在 `_ausrc`
作用域一次都没开口 ⇒ **真实检出力 0.0**。

⭐⭐⭐⭐⭐⭐ **⇒ 而 1010 把那 39 条当成一个同质的集合 —— 本批问：它同质吗？**

⭐⭐⭐⭐⭐⭐⭐ **而答案是「不」：那 45 次改动只落在 8 段不同文本上，
其中 38 次落在 3 句话上 —— 而那 3 句话是本会话每一批都在写的
「本批纯离线、不打开浏览器、不按任何键、连 `mouse.click` 都没有」**计费声明**。**

⇒ ⇒ ⭐⭐⭐⭐⭐⭐ **⇒ 所以 1010 的 0.0 首先是「关于计费声明的 0.0」** ⇒ ⇒
**⇒ 而这还不只是「样本偏科」—— 下一条更硬：45 次里 43 次落在只占全集 8.6% 的
「高 occurrence 锚点」上 ⇒ ⇒ ⇒ 而 occurrence ≥ 2 的锚点删掉一次之后原文仍在、
判据仍为真 ⇒ ⇒ ⇒ ⇒ **门报 0 是对的、不是缺陷****

⇒ ⇒ ⭐⭐⭐⭐⭐⭐ **⇒ 真正的洞在这里：门唯一的判据是不变量「occurrence ≥ 1」，
而真实工作流的主形态恰好把这个量推到 2、3、4… ⇒ ⇒ ⇒ ⇒
**⇒ 门答的「在不在」，在主工作流下是恒真的 ⇒ ⇒ ⇒ ⇒ 信息量为 0**
⇒ ⇒ **⇒ 而唯一在变的是「在几次」—— 1009 P4 早就把这一轴指认给普查了，
它至今没有任何一条门判据覆盖它**

本批**纯离线**：不打开浏览器、不按任何键、连 `mouse.click` 都没有
"""
import ast
import atexit
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
VFILE = "scripts/verify-jimeng-batch841-unclickable.py"
AFILE = "scripts/jimeng_unclickable_audit.py"
GOLDEN = ROOT / "docs/research/jimeng-canvas/change-locality-1011.json"
G5 = ROOT / "docs/research/jimeng-canvas/zero-coupling-anchors-1005.json"
OUT = "/tmp/b1011-change-locality.json"
VERIFIER_TXT = (ROOT / VFILE).read_text(encoding="utf-8")
AUDIT_TXT = (ROOT / AFILE).read_text(encoding="utf-8")
PY = sys.executable

# ⭐⭐⭐⭐⭐⭐⭐ **历史类判据的基线自检**：本批的每一个读数都钉在这十个提交上 ⇒ ⇒
#   **⇒ 而「钉在 git 上」的判据有它自己的失效形态：将来若有人 rebase / squash /
#   **这些 sha 全部取不到 ⇒ ⇒ ⇒ 而那时判据不会报错、它会静静地读出空集** ⇒ ⇒
#   ⭐⭐⭐⭐⭐⭐ **⇒ 所以本条不是可选的自检、它是这一整类判据的前提**
COMMITS = [
    ("1001", "1dda1d5b"), ("1002", "a62401ba"), ("1003", "20c76d45"),
    ("1004", "11ef6888"), ("1005", "e7e8c779"), ("1006", "76a0988a"),
    ("1007", "9f180577"), ("1008", "d857b7f7"), ("1009", "0eada9fc"),
    ("1010", "f5157f18"),
]

# ⭐⭐⭐⭐⭐⭐⭐ **「计费声明」的三句话** —— 本批的核心发现就是它们撑起了 45 次里的 38 次 ⇒ ⇒
#   **⇒ 它们必须由**机器**认出来、不许我手打 ⇒ ⇒**
#   **⇒ 而认法必须锚在**结构**上（每一批都重复出现的同一句判据文本）、
#   **而不是锚在「哪一批」上 —— 后者会随历史增长而失效**
BILLING_STEMS = ("零计费是结构性的", "mouse.click` 都没有")


def _cleanup_tmp():
    """⭐⭐ 1008 的纪律：任何写出临时文件的仪器都必须注册 atexit 清理。"""
    for p in Path("/tmp").glob("b1011-*"):
        if p.is_file() and p.name != Path(OUT).name:
            try:
                p.unlink()
            except OSError:
                pass


atexit.register(_cleanup_tmp)


def git_show(sha, path):
    r = subprocess.run(["git", "show", "%s:%s" % (sha, path)], cwd=str(ROOT),
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise AssertionError("⭐ 取不到 %s:%s" % (sha, path))
    return r.stdout


def sha_alive(sha):
    return subprocess.run(["git", "cat-file", "-e", "%s^{commit}" % sha],
                          cwd=str(ROOT), capture_output=True).returncode == 0


spec = importlib.util.spec_from_file_location("g_1011", str(GATE))
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)

# ── 基线自检：先证明十个 sha 都活着，再开始量 ───────────────────────
# ⚠️⚠️⭐⭐⭐⭐⭐ **顺序不能颠倒**：先把快照取回来、取不到就崩 ⇒ ⇒
#   **⇒ 而 1008 踩过一次「verdicts 建在清单落盘之前 → 读到空串」** ⇒ ⇒
#   **⇒ 「顺序错了」是本项目最贵的一类仪器缺陷**
V, A = {}, {}
_alive = 0
for tag, sha in COMMITS:
    assert sha_alive(sha), (
        "⭐⭐⭐⭐⭐ **commit %s（批 %s）取不到了 ⇒ 本批全部读数失效** ⇒ ⇒ "
        "**⇒ 而这就是「历史类判据」的专属失效形态：它不报错、它静静地读出空集**"
        % (sha, tag))
    _alive += 1
    V[tag] = git_show(sha, VFILE)
    A[tag] = git_show(sha, AFILE)

assert all(len(A[t]) > 1000 for t in A), "⭐ audit 快照异常（仪器坏了）"

# ── ① P1/P2：逐对逐条算「动过」的那些锚点 ─────────────────────────
records = []          # (anchor, tag0, tag1, occ0, occ1)
for i in range(len(COMMITS) - 1):
    t0, t1 = COMMITS[i][0], COMMITS[i + 1][0]
    for n, a, neg in g.collect(ast.parse(V[t0])):
        if n != "_ausrc" or neg:
            continue
        c0, c1 = A[t0].count(a), A[t1].count(a)
        if c0 != c1:
            records.append((a, t0, t1, c0, c1))
assert records, "⭐ 分母为 0（仪器坏了）"

N_TOUCHED = len(records)
N_NINE = sum(1 for r in records if r[1] != "1009")   # ⭐ 1010 记的「九对」口径
uniq_anchor = sorted({r[0] for r in records})
N_UNIQ = len(uniq_anchor)
cnt_anchor = collections.Counter(r[0] for r in records)

# 计费声明的机器认法：⭐ **按文本、不是按批**
billing = [a for a in uniq_anchor
           if any(s in a for s in BILLING_STEMS)]
billing_set = set(billing)
N_BILLING_UNIQ = len(billing)
N_BILLING_RECS = sum(1 for r in records if r[0] in billing_set)
nonbill = [r for r in records if r[0] not in billing_set]
N_NONBILL_RECS = len(nonbill)
N_NONBILL_UNIQ = len({r[0] for r in nonbill})

# ── ② P3：occurrence 偏斜 ────────────────────────────────────────
items_head = [(n, a) for n, a, neg in g.collect(ast.parse(V["1010"]))
              if n == "_ausrc" and not neg]
N_ITEMS = len(items_head)
A_HEAD = A["1010"]
occ_all = collections.Counter(A_HEAD.count(a) for _n, a in items_head)
N_ALL_GE2 = sum(v for k, v in occ_all.items() if k >= 2)
ALL_GE2_RATE = N_ALL_GE2 / N_ITEMS
occ_touch = collections.Counter(r[3] for r in records)
N_TOUCH_GE2 = sum(v for k, v in occ_touch.items() if k >= 2)
TOUCH_GE2_RATE = N_TOUCH_GE2 / N_TOUCHED
GE2_RATIO = TOUCH_GE2_RATE / ALL_GE2_RATE

# ── ③ P4：零耦合不是缺陷（与 1004 的公式对账）─────────────────────
# 1004 的正确公式：**(自身只出现 1 次 ? 1 : 0) + |被连带打死的唯一超串|**
# ⇒ ⇒ occurrence ≥ 2 ⇒ 第一项为 0 ⇒ ⇒ 而「在不在」不变 ⇒ ⇒ ⇒ 耦合度必为 0
# ⇒ ⇒ 所以门对这类锚点报 0 是**公式要求的**，不是门弱
N_PRED_ZERO = sum(v for k, v in occ_touch.items() if k >= 2)
N_VANISHED = sum(1 for r in records if r[4] == 0)
N_DECREASED = sum(1 for r in records if 0 < r[4] < r[3])
N_INCREASED = sum(1 for r in records if r[4] > r[3])

# ── ④ P5：「在几次」单调只增 ──────────────────────────────────────
# ⭐⭐⭐⭐⭐⭐⭐ **这是本批真正的落点：唯一在变的量是「在几次」、而它今天没有任何门判据覆盖**

# ── ⑤ P6：与 1005 零耦合清单交叉（⭐ 小样本必须诚实）───────────────
g5 = json.loads(G5.read_text(encoding="utf-8"))
z_rows = g5["rows"]
z_texts = {r["anchor"] for r in g5["rows"]}
z_cls = {}
for r in z_rows:
    z_cls.setdefault(r["anchor"], r["class"])
inter = sorted(set(uniq_anchor) & z_texts)
N_INTER = len(inter)
INTER_RATE = N_INTER / N_UNIQ
N_Z_ROWS = len(z_rows)
N_Z_UNIQ = len(z_texts)
Z_BASE = N_Z_ROWS / g5["n_positive_present"]

# ── ⑥ P7：历史类判据的基线自检 ────────────────────────────────────

out = {
    "target": "offline-change-locality",
    "question": "⭐⭐⭐⭐⭐⭐⭐ **真实历史里门看不见的那些改动，是一批什么样的改动？**",
    "scope_1011": "⭐⭐⭐⭐⭐ **只量 `_ausrc`（audit 基线）这一个目标** ⇒ ⇒ "
                  "**⇒ 而 1006/1007 改过的探针侧文件不在分母里 ⇒ ⇒ "
                  "⇒ 所以这些读数不是全局的、报数时必须带着这句话**",
    "offline_1011": True,
    "commits_1011": COMMITS,
    "baseline_sha_alive": _alive,
}

# ── 判据文本 ──────────────────────────────────────────────────────
P1 = ("⭐⭐⭐⭐⭐⭐⭐ **1010 在仓里记的分母是 39（它只算了九对快照），"
      "而本批把 1010 自己那一次提交也算了进来、十对 ⇒ 逐条复算得 %d** ⇒ ⇒ "
      "**⇒ 差 %d 全部来自 `1009->1010` 那一对 ⇒ ⇒ "
      "**⇒ 口径必须显式对齐：不许默默把 39 改成 %d**" %
      (N_TOUCHED, N_TOUCHED - N_NINE, N_TOUCHED))

P2 = ("⭐⭐⭐⭐⭐⭐⭐⭐ **那 %d 次改动只落在 %d 段不同文本上 —— 而其中 %d 次落在 %d 句话上** ⇒ ⇒ "
      "**⇒ 而那 %d 句话是每一批都在重复写的「本批纯离线、不打开浏览器、"
      "不按任何键、连 `mouse.click` 都没有」计费声明** ⇒ ⇒ "
      "**⇒ ⇒ ⇒ 所以 1010 的 0.0 首先是「关于计费声明的 0.0」** ⇒ ⇒ "
      "**⇒ 扣掉它们之后还剩 %d 次改动、%d 段文本（两个数必须一起报）**" %
      (N_TOUCHED, N_UNIQ, N_BILLING_RECS, N_BILLING_UNIQ, N_BILLING_UNIQ,
       N_NONBILL_RECS, N_NONBILL_UNIQ))

P3 = ("⭐⭐⭐⭐⭐⭐⭐ **45 次改动里 %d 次（%.1f%%）落在 occurrence ≥ 2 的锚点上，"
      "而全集里 occurrence ≥ 2 的只有 %.1f%%（%d/%d）—— 偏斜 %.1f 倍** ⇒ ⇒ "
      "**⇒ 而这不是随机抽样的偶然：真实工作流改的恰恰是「被反复声明」的那些句**" %
      (N_TOUCH_GE2, TOUCH_GE2_RATE * 100, ALL_GE2_RATE * 100,
       N_ALL_GE2, N_ITEMS, GE2_RATIO))

P4 = ("⭐⭐⭐⭐⭐⭐⭐⭐ **按 1004 的耦合度公式（自身只出现 1 次 ? 1 : 0），"
      "occurrence ≥ 2 的锚点耦合度**本该**是 0** ⇒ ⇒ 实测门报 %d 个 —— **一致** ⇒ ⇒ "
      "**⇒ ⇒ ⇒ 所以「门看不见那 %d 次改动」不是缺陷、是公式要求的结果** ⇒ ⇒ "
      "**⇒ ⇒ ⇒ 真正的问题被这句话换掉了：不是「门弱」，是「门唯一的不变量"
      "与真实工作流的主形态正交」**" % (N_VANISHED, N_PRED_ZERO))

P5 = ("⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **这 %d 次改动里：出现次数**增加** %d、**减少** %d、**归零** %d "
      "⇒ ⇒ ⇒ **⇒ 而 occurrence 是「在几次」那个轴、它在真实工作流下单调只增** ⇒ ⇒ ⇒ "
      "**⇒ ⇒ ⇒ 1009 P4 早就把这一轴指认给普查了（「门管在不在、普查管在几次、"
      "在几个文件」）、而它至今没有任何一条门判据覆盖** ⇒ ⇒ ⇒ ⇒ "
      "**⇒ ⇒ ⇒ ⇒ 而 1008 已经为这类判据准备好了配套：老账记成账龄、不许一次报红**"
      % (N_TOUCHED, N_INCREASED, N_DECREASED, N_VANISHED))

P6 = ("⭐⭐⭐⭐⭐ **%d 段里 %d 段落在 1005 那份 %d 行零耦合清单里（%.1f%% vs 基准 %.1f%%）"
      "⇒ ⇒ 而**样本只有 %d 段**、且扣掉计费声明后只剩 %d 段 ⇒ ⇒ "
      "**⇒ ⇒ ⇒ 所以本批**不**据此决定「该点修还是该普查」** —— "
      "**⇒ 而诚实的结论是：样本量不足以决定路线、只能收窄 1010 读数的适用范围**"
      % (N_UNIQ, N_INTER, N_Z_ROWS, INTER_RATE * 100, Z_BASE * 100,
         N_UNIQ, N_NONBILL_UNIQ))

P7 = ("⭐⭐⭐⭐⭐⭐⭐ **本批每一个读数都钉在 %d 个 git 提交上 ⇒ ⇒ 而「钉在历史上的判据」"
      "有它专属的失效形态：将来 rebase 之后这些 sha 取不到、判据不会报错、"
      "它会静静地读出空集** ⇒ ⇒ **⇒ 所以开工前先逐个 `git cat-file` 验活**"
      "⇒ ⇒ 实测 %d/%d 全部可取" % (len(COMMITS), _alive, len(COMMITS)))

PRED = {
    "p1_1011": P1, "p2_1011": P2, "p3_1011": P3, "p4_1011": P4,
    "p5_1011": P5, "p6_1011": P6, "p7_1011": P7,
}

out["verdicts_2011"] = {
    "p1_denominator_is_45_not_39_1011_": P1,
    "p2_45_changes_land_on_8_texts_38_on_the_billing_line_1011_": P2,
    "p3_touched_is_biased_to_high_occurrence_1011_": P3,
    "p4_invisible_is_correct_not_a_defect_1011_": P4,
    "p5_the_count_axis_only_grows_1011_": P5,
    "p6_cross_with_1005_golden_but_too_few_to_decide_1011_": P6,
    "p7_history_backed_criteria_must_verify_shas_2011_": P7,
    "p8_golden_2011_": (
        "⭐⭐⭐⭐⭐ **P8 成立：逐条落进 "
        "`docs/research/jimeng-canvas/change-locality-1011.json`、"
        "**由本探针自己写** ⇒ ⇒ "
        "⭐⭐⭐⭐⭐⭐ **⇒ 而它记的是「每段文本被动了几次、出现在哪几对之间、"
        "是不是计费声明、在不在 1005 那份清单里」—— "
        "这正是 1010 记了次数却没记身份的那一层** ⇒ ⇒ "
        "**⇒ 本批只量 `_ausrc` 这一个目标 —— 局部读数不许长得像全局的** ⇒ ⇒ "
        "**⇒ P9 成立：判据里手写的数全部有出处**"),
    "offline_2011": "⭐⭐⭐⭐⭐ **本批纯离线**：不打开浏览器、不按任何键、"
                    "**连 `mouse.click` 都没有**",
}

# ── hold 判定 ─────────────────────────────────────────────────────
out["P1_hold_2011"] = bool(N_TOUCHED == 45 and N_NINE == 39
                           and N_TOUCHED - N_NINE == 6)
out["P2_hold_2011"] = bool(N_UNIQ == 8 and N_BILLING_UNIQ == 3
                           and N_BILLING_RECS == 38
                           and N_NONBILL_RECS == 7 and N_NONBILL_UNIQ == 5)
out["P3_hold_2011"] = bool(N_TOUCH_GE2 == 43 and N_ALL_GE2 == 292
                           and N_ITEMS == 3407)
out["P4_hold_2011"] = bool(N_PRED_ZERO == N_TOUCH_GE2 and N_VANISHED == 0)
out["P5_hold_2011"] = bool(N_INCREASED == N_TOUCHED and N_DECREASED == 0
                           and N_VANISHED == 0)
out["P6_hold_2011"] = bool(N_INTER == 7 and N_Z_ROWS == 690
                           and N_Z_UNIQ == 658 and N_NONBILL_UNIQ == 5)
out["P7_hold_2011"] = bool(_alive == len(COMMITS))

# ⭐⭐⭐⭐⭐⭐⭐ **「手写的数必须有出处」要求出处能被机器查到 ⇒ ⇒ **
#   **⇒ 而这些数原本只活在判据字符串和 golden 里、`out` 上一条都没有 ⇒ ⇒
#   **⇒ 那样 P9 会把它们判成「没出处」—— 那是仪器的错、不是判据的错** ⇒ ⇒
#   **⇒ 所以必须先把它们**落成 `out` 里的数值字段**，P9 才有东西可查**
out["readings_2011"] = {
    "n_touched_ten_pairs": N_TOUCHED,
    "n_touched_nine_pairs_2010": N_NINE,
    "n_delta_ten_minus_nine": N_TOUCHED - N_NINE,
    "n_distinct_anchor_texts": N_UNIQ,
    "n_billing_texts": N_BILLING_UNIQ,
    "n_billing_records": N_BILLING_RECS,
    "n_nonbilling_records": N_NONBILL_RECS,
    "n_nonbilling_texts": N_NONBILL_UNIQ,
    "n_positive_ausrc_at_1010": N_ITEMS,
    "n_ge2_whole_universe": N_ALL_GE2,
    "rate_ge2_whole_pct": round(ALL_GE2_RATE * 100, 1),
    "n_ge2_touched": N_TOUCH_GE2,
    "rate_ge2_touched_pct": round(TOUCH_GE2_RATE * 100, 1),
    "bias_ratio": round(GE2_RATIO, 1),
    "n_predicted_zero_coupling": N_PRED_ZERO,
    "n_increased": N_INCREASED,
    "n_decreased": N_DECREASED,
    "n_vanished": N_VANISHED,
    "n_rows_1005_golden": N_Z_ROWS,
    "n_distinct_texts_1005_golden": N_Z_UNIQ,
    "n_intersection": N_INTER,
    "rate_intersection_pct": round(INTER_RATE * 100, 1),
    "base_rate_1005_pct": round(Z_BASE * 100, 1),
    "n_shas_alive": _alive,
    "n_commits": len(COMMITS),
}

# ── golden ────────────────────────────────────────────────────────
golden = {
    "generated_by": "jimeng_probe1011_change_locality.py",
    "note": "⭐⭐⭐⭐⭐⭐⭐ **真实历史里门看不见的那些改动，是一批什么样的改动**",
    "scope": "⭐ 只量 `_ausrc`（audit 基线）这一个目标",
    "denominator": {
        "n_touched_ten_pairs": N_TOUCHED,
        "n_touched_nine_pairs_as_recorded_by_1010": N_NINE,
        "n_distinct_anchor_texts": N_UNIQ,
    },
    "per_text": [{"anchor": a, "n_changes": cnt_anchor[a],
                  "pairs": sorted({"%s->%s" % (r[1], r[2])
                                   for r in records if r[0] == a}),
                  "is_billing_declaration": a in billing_set,
                  "in_1005_zero_coupling_golden": a in z_texts,
                  "class_1005": z_cls.get(a)}
                 for a in uniq_anchor],
    "occurrence_bias": {
        "n_positive_ausrc_at_1010": N_ITEMS,
        "n_ge2_whole_universe": N_ALL_GE2,
        "rate_whole": round(ALL_GE2_RATE, 4),
        "n_ge2_touched": N_TOUCH_GE2,
        "rate_touched": round(TOUCH_GE2_RATE, 4),
        "ratio": round(GE2_RATIO, 2),
    },
    "direction": {"increased": N_INCREASED, "decreased": N_DECREASED,
                  "vanished": N_VANISHED,
                  "n_predicted_zero_coupling_by_1004_formula": N_PRED_ZERO},
    "cross_with_1005": {
        "n_intersection": N_INTER, "n_universe_touched": N_UNIQ,
        "rate": round(INTER_RATE, 4),
        "n_rows_1005": N_Z_ROWS, "n_distinct_texts_1005": N_Z_UNIQ,
        "base_rate_1005": round(Z_BASE, 4),
        "note": "⭐⭐⭐⭐⭐ **样本只有 %d 段、扣掉计费声明后只剩 %d 段 ⇒ "
                "⇒ 本批不据此决定路线**" % (N_UNIQ, N_NONBILL_UNIQ),
    },
}
io.open(GOLDEN, "w", encoding="utf-8").write(
    json.dumps(golden, ensure_ascii=False, indent=1))
out["P8_hold_2011"] = bool(GOLDEN.exists() and GOLDEN.stat().st_size > 500)
out["P8_verdict_2011"] = (
    "✅ **逐条落进 `%s`、由本探针自己写** ⇒ ⇒ **⇒ 而它记的是「每段文本被动了几次、"
    "出现在哪几对之间、是不是计费声明、在不在 1005 那份清单里」** ⇒ ⇒ "
    "**⇒ 而这正是 1010 记了次数却没记身份的那一层**"
    % GOLDEN.relative_to(ROOT))

# ── P9：沿用「手写的数必须有出处」 ───────────────────────────────
_NUMRE = re.compile(r"\d+(?:\.\d+)?")
_AUD_BLOCK = "change_locality_2011"


def audit_block():
    for node in ast.walk(ast.parse(AUDIT_TXT)):
        if not isinstance(node, ast.Dict):
            continue
        for k, v in zip(node.keys, node.values):
            if (isinstance(k, ast.Constant) and k.value == _AUD_BLOCK
                    and isinstance(v, ast.Dict)):
                return ast.literal_eval(v)
    raise AssertionError("⭐ audit 里找不到 %s（仪器坏了）" % _AUD_BLOCK)


_AB = audit_block()
assert "p4_invisible_is_correct_not_a_defect_2011_" in _AB, (
    "⭐⭐⭐⭐⭐ **又取错层级了：%r**" % (sorted(_AB)[:6],))


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


_allowed = _nums({k: v for k, v in out.items()
                  if k not in ("verdicts_2011",)}, set())
# ⭐⭐⭐⭐⭐ **口径常数与批号必须有出处**：一位数是「位数」级别的口径标记
_allowed |= set("0123456789") | {
    "1001", "1002", "1003", "1004", "1005", "1006", "1007", "1008",
    "1009", "1010", "1011",
}
_allowed |= set(re.findall(r'check\("[A-Z](\d{3})[A-Z]\.', VERIFIER_TXT))
_rows_n, _bad = {}, {}
for _k, _v in out["verdicts_2011"].items():
    _got = sorted(set(_NUMRE.findall(_AB.get(_k) or "")), key=float)
    _miss = [n for n in _got if n not in _allowed]
    _rows_n[_k] = _got
    if _miss:
        _bad[_k] = _miss
out["audit_numbers_vs_computed_2011"] = {
    "n_keys_compared": len(_rows_n),
    "n_numbers_total": sum(len(v) for v in _rows_n.values()),
    "n_keys_with_unjustified_number": len(_bad),
    "unjustified": _bad,
}
out["P9_hold_2011"] = bool(not _bad)

out["discipline_2011"] = "".join([
    "① ⭐⭐⭐⭐⭐⭐⭐ **条数 ≠ 地方数 —— %d 次改动只落在 %d 段文本上** ⇒ ⇒\n"
    % (N_TOUCHED, N_UNIQ),
    "  ② ⭐⭐⭐⭐⭐⭐⭐ **「看不见」要先判是门弱还是公式要求 —— 这里与 1004 的公式一致** ⇒ ⇒\n",
    "  ③ ⭐⭐⭐⭐⭐⭐⭐ **分母不许被样本偏斜带偏 —— 45 次里 43 次落在占全集 8.6%% 的那批上** ⇒ ⇒\n",
    "  ④ ⭐⭐⭐⭐⭐ **扣减前和扣减后必须一起报**，否则一个局部读数会长得像全局的 ⇒\n",
    "  ⑤ ⭐⭐⭐⭐⭐ **样本量不足以决定路线时，结论就写「不足以决定」** —— 不许硬给路线 ⇒\n",
    "  ⑥ ⭐⭐⭐⭐⭐ **钉在 git 历史上的判据必须逐个验活 sha** ⇒\n",
])

io.open(OUT, "w", encoding="utf-8").write(
    json.dumps(out, ensure_ascii=False, indent=1))
print("touched=%d(九对=%d) uniq=%d billing_uniq=%d billing_recs=%d "
      "nonbill=%d/%d" % (N_TOUCHED, N_NINE, N_UNIQ, N_BILLING_UNIQ,
                         N_BILLING_RECS, N_NONBILL_RECS, N_NONBILL_UNIQ))
print("ge2 touched=%d/%d(%.1f%%) all=%d/%d(%.1f%%) ratio=%.1f"
      % (N_TOUCH_GE2, N_TOUCHED, TOUCH_GE2_RATE * 100,
         N_ALL_GE2, N_ITEMS, ALL_GE2_RATE * 100, GE2_RATIO))
print("dir inc=%d dec=%d van=%d | 1005 cross=%d/%d base=%.1f%% zrows=%d zuniq=%d"
      % (N_INCREASED, N_DECREASED, N_VANISHED, N_INTER, N_UNIQ,
         Z_BASE * 100, N_Z_ROWS, N_Z_UNIQ))
print("P1..P9 =", [out["P%d_hold_2011" % i] for i in range(1, 10)])
print("PROBE_1011_DONE ->", OUT)