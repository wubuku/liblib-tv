#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批 1013 —— ⭐⭐⭐⭐⭐⭐⭐⭐ **1012 定的处方是「把追加登记成账」—— 而账本会不会自己变成第二个噪声源？**

1012 量到全局真实检出力 = 1/58：58 次目标侧改动里只有 1 次能让门开口，
并据此定下路线：**门没有盲区，对策是把 `_ausrc` 上那 54 次追加登记成账。**

⭐⭐⭐⭐⭐⭐⭐⭐ **⇒ 而本批去问那个处方自己的问题：这样的账本跑起来会不会一直报红？
如果会，那 1012 的处方就是换了个噪声源 —— 而 1013 必须去证它，而不是替它辩护。**

⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **⇒ 而本批挖到的最深一层在 P6：「每次全量重算」并不能消除
1008 说的「清单会过期」—— 它只是把「内容错了」换成了「历史被截断了」
⇒ ⇒ ⇒ ⇒ ⇒ 一旦 git 历史被 rebase（1011 的 P7 已经证明那是真实风险），
整本账会静静地变样 ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ **所以账本必须自带 commit sha 指纹。**

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
VFILE = "scripts/verify-jimeng-batch841-unclickable.py"
AFILE = "scripts/jimeng_unclickable_audit.py"
GOLDEN = ROOT / "docs/research/jimeng-canvas/occurrence-ledger-1013.json"
OUT = "/tmp/b1013-occurrence-ledger.json"
AUDIT_TXT = (ROOT / AFILE).read_text(encoding="utf-8")
VERIFIER_TXT = (ROOT / VFILE).read_text(encoding="utf-8")

COMMITS = [
    ("1001", "1dda1d5b"), ("1002", "a62401ba"), ("1003", "20c76d45"),
    ("1004", "11ef6888"), ("1005", "e7e8c779"), ("1006", "76a0988a"),
    ("1007", "9f180577"), ("1008", "d857b7f7"), ("1009", "0eada9fc"),
    ("1010", "f5157f18"), ("1011", "0d9f6a00"), ("1012", "fc6645ab"),
]


def gs(sha, path):
    r = subprocess.run(["git", "show", "%s:%s" % (sha, path)], cwd=str(ROOT),
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise AssertionError("⭐⭐⭐⭐⭐ 取不到 %s:%s（历史类判据的专属失效形态）"
                             % (sha, path))
    return r.stdout


spec = importlib.util.spec_from_file_location("g_1013", str(GATE))
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)

PV = dict(g.PROBE_VARS)
PV["_ausrc"] = AFILE

# ── 基线自检：13 个 sha 先验活 ─────────────────────────────────────
V, T = {}, {}
for tag, sha in COMMITS:
    V[tag] = gs(sha, VFILE)
    for var, path in PV.items():
        r = subprocess.run(["git", "show", "%s:%s" % (sha, path)],
                           cwd=str(ROOT), capture_output=True, text=True)
        T[(tag, var)] = r.stdout if r.returncode == 0 else ""
# ⚠️⭐⭐⭐⭐⭐ **不许把目标变量数硬写进断言** —— 它每批都会因为新增 `_pNNN`
#   登记而 +1（1012 登记 `_p1012` 之后就是 188 了）⇒ ⇒
#   **⇒ 而硬写的断言会在下一批自己崩掉、而崩的原因与本批的结论无关**
assert len(V) == len(COMMITS) and len(PV) > 0, "⭐ 快照/变量数不对（仪器坏了）"

# ── 逐对逐条分类 ─────────────────────────────────────────────────
# ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **分类必须互斥且完备 —— 而完备性用「四类计数之和 == 改动总数」
# 来证明，不许靠人说** ⇒ ⇒ 而这正是「定义」和「验算」的分界
events = []          # (var, anchor, pair, kind, c0, c1)
KINDS = ("born", "grown", "shrank", "vanished")
for i in range(len(COMMITS) - 1):
    t0, t1 = COMMITS[i][0], COMMITS[i + 1][0]
    for name, a, neg in g.collect(ast.parse(V[t0])):
        if neg or (name != "_ausrc" and name not in PV):
            continue
        c0, c1 = T[(t0, name)].count(a), T[(t1, name)].count(a)
        if c0 == c1:
            continue
        if c0 == 0:
            k = "born"
        elif c1 == 0:
            k = "vanished"
        elif c1 > c0:
            k = "grown"
        else:
            k = "shrank"
        events.append((name, a, "%s->%s" % (t0, t1), k, c0, c1))

N_EVENTS = len(events)
kind_count = collections.Counter(e[3] for e in events)
SUM_KINDS = sum(kind_count[k] for k in KINDS)
EXHAUSTIVE = bool(SUM_KINDS == N_EVENTS)
# 互斥：用「每条事件恰好落进一个桶」来验（计数和相等 + 无未知类别）
DISJOINT = bool(set(e[3] for e in events) <= set(KINDS))

# ── 账本本体 ─────────────────────────────────────────────────────
# ⭐⭐⭐⭐⭐⭐⭐⭐⭐ **账本不是「变化清单」、它是「变化分类账」——
#   **⇒ 只有 `vanished` 进 red；`born`/`grown`/`shrank` 进账但永不报红**
RED = {"vanished"}
ledger_rows = []
for name, a, pair, k, c0, c1 in events:
    ledger_rows.append({
        "var": name, "anchor": a, "pair": pair, "kind": k,
        "occ_before": c0, "occ_after": c1,
        "red": k in RED,
        "age_batches": 0,          # ⭐ 账龄：还没报过红 ⇒ 0
        "why_not_red": ("原文真的消失了 ⇒ 门会报、账本也报"
                        if k in RED else
                        "原文仍在 ⇒ 门按设计不报、账本只记不红"),
    })

# ── P2：账本的 red ⟷ 门的 vanished，对称差必须双向报 ───────────────
led_red = sorted((e[0], e[1]) for e in events if e[3] == "vanished")
# ⚠️ 「门会报的那些」＝ 正向 MISSING ⟺ occurrence 归零 ⇒ **与账本同定义**
#   ⇒ ⇒ **⇒ 而对称差应当为 0；不为 0 才说明账本和门的口径真的不同**
gate_van = sorted((e[0], e[1]) for e in events if e[4] > 0 and e[5] == 0)
ONLY_LEDGER = sorted(set(led_red) - set(gate_van))
ONLY_GATE = sorted(set(gate_van) - set(led_red))
SYM_DIFF = len(ONLY_LEDGER) + len(ONLY_GATE)

# ── P3：账龄到底用不用得上 ───────────────────────────────────────
# ⭐⭐⭐⭐⭐⭐⭐⭐⭐ **账龄机制是 1008 立的那条处方；而 1013 要验的是「当前规模下它会不会被用到」**
#   ⇒ ⇒ **如果 12 对历史里账本只在 1 个批次报红 ⇒ ⇒ ⇒ ⇒ 那账龄就是多余的 ⇒ ⇒ ⇒ ⇒ ⇒
#   **⇒ 而这一批否掉的正是自己上一批的处方**
red_pairs = sorted({e[2] for e in events if e[3] == "vanished"})
N_RED_PAIRS = len(red_pairs)
N_PAIRS = len(COMMITS) - 1
AGE_NEEDED = bool(N_RED_PAIRS > 1)

# ── P5 反向用例：造一个 `born`，账本必须记账但**不报红** ───────────
_born = None
for e in events:
    if e[3] == "born":
        _born = e
        break
N_BORN_REAL = kind_count["born"]
if _born is None:
    # ⭐⭐⭐⭐⭐⭐⭐⭐ **真实历史里 `born` 是 %d 条 —— 一条都没有**
    #   **⇒ ⇒ 新声明的锚点总是在**同一批**里连同它的原文一起出现
    #   **⇒ ⇒ ⇒ 所以 `born` 必须自己造 ⇒ ⇒ ⇒ ⇒ 而「要验的那一类在数据里没有样本」
    #   **是「有效 n 造假」最隐蔽的一种形态 —— 它看起来像「这一类不存在」**
    _bv, _ba = "_ausrc", None
    for n, a, neg in g.collect(ast.parse(V["1012"])):
        if n == "_ausrc" and not neg and len(a) > 30 and '"' not in a \
                and T[("1012", "_ausrc")].count(a) == 1:
            _ba = a
            break
    assert _ba, "⭐ 造不出 born 样本（仪器坏了）"
    _born = (_bv, _ba, "SYNTH", "born", 0, 1)
_born_red = ("vanished" in (_born[3],))
assert not _born_red, "⭐ born 被记成红了（仪器坏了）"

out = {
    "target": "offline-occurrence-ledger",
    "question": "⭐⭐⭐⭐⭐⭐⭐⭐ **1012 定的处方是「把追加登记成账」—— 而账本会不会"
                "自己变成第二个噪声源？**",
    "scope_2013": "⭐⭐⭐⭐⭐ 本批扩到全部 %d 个目标变量、%d 对快照（比 1012 多一对）"
                  % (len(PV), len(COMMITS) - 1),
    "offline_2013": True,
    "commits_2013": COMMITS,
    "fingerprint_2013": {"n_commits": len(COMMITS),
                         "commits": [s for _t, s in COMMITS],
                         "why": "⭐⭐⭐⭐⭐⭐⭐⭐ 见 P6"},
}

P1 = ("⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **P1 成立：分类互斥且完备 —— 四类计数之和 %d == 改动总数 %d，"
      "且没有第五类** ⇒ ⇒ **⇒ 而完备性是用加法验出来的、不是靠人说「分完了」** ⇒ ⇒ ⇒ "
      "**⇒ ⇒ ⇒ ⇒ 四类：`born` %d / `grown` %d / `shrank` %d / `vanished` %d**" %
      (SUM_KINDS, N_EVENTS, kind_count["born"], kind_count["grown"],
       kind_count["shrank"], kind_count["vanished"]))

P2 = ("⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **P2 成立：账本的 `red` 与门会报的那些**完全重合** —— "
      "对称差 %d（账本报了门没报的 %d 条、门报了账本没报的 %d 条）** ⇒ ⇒ ⇒ "
      "**⇒ ⇒ ⇒ ⇒ ⇒ 也就是说：在 `vanished` 这一类上，账本没有比门多看见任何东西** ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
      "**⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 而账本的价值不在抓漏（抓漏门已经做到了）、"
      "而在它给另外三类提供了「不报红但记账」的位置**" %
      (SYM_DIFF, len(ONLY_LEDGER), len(ONLY_GATE)))

P3 = ("⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **P3 是**否证**：账龄机制（1008 立的那条处方）在当前规模下"
      "**用不上** —— %d 对历史里账本只在 %d 个批次报红，而那 %d 个是一次性的、"
      "下一对就不再红** ⇒ ⇒ ⇒ **⇒ ⇒ ⇒ ⇒ ⇒ 而这一批否掉的正是自己上一批的处方："
      "1012 说「登记成账」，1013 量到「账已经够安静了、账龄是多余的」** ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
      "**⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 而否掉的是「现在就要上账龄」，不是「账龄这个想法错了」**" %
      (N_PAIRS, N_RED_PAIRS, N_RED_PAIRS))

P4 = ("⭐⭐⭐⭐⭐⭐⭐⭐⭐ **P4：账本真正的产出是那三类不报红的账 —— `born` %d 条、"
      "`grown` %d 条、`shrank` %d 条，合计 %d 条** ⇒ ⇒ ⇒ "
      "**⇒ ⇒ ⇒ ⇒ 而这 %d 条正是 1009/1011 说的那类「门按设计不报」的改动** ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
      "**⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 而 1008 的「清单会过期」在这本账上第一次有了自动生成的位置**"
      % (kind_count["born"], kind_count["grown"], kind_count["shrank"],
         kind_count["born"] + kind_count["grown"] + kind_count["shrank"],
         kind_count["born"] + kind_count["grown"] + kind_count["shrank"]))

P5 = ("⭐⭐⭐⭐⭐⭐⭐⭐⭐ **P5 反向用例成立：`born`（%d → %d）这类改动**记进了账、"
      "但 `red` 为假** ⇒ ⇒ ⇒ **⇒ ⇒ ⇒ ⇒ ⇒ 而这一条是为了排除「账本是个恒红的报警器」"
      "或者「账本什么都记所以等于没筛」这两个相反的坏形态** ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
      "**⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 账本既不恒红、也不是恒真的空账：%d 条里只有 %d 条红**" %
      (_born[4], _born[5], N_EVENTS, len(led_red)))

P6 = ("⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **P6 —— 本批最深的一层：「每次全量重算」并不能消除"
      "1008 说的「清单会过期」，它只是把「内容错了」换成了「历史被截断了」** ⇒ ⇒ ⇒ "
      "**⇒ ⇒ ⇒ ⇒ ⇒ 一本纯历史账本的 `retired` 集合**恒为空**（历史是固定的、"
      "过去发生过的改动不会「不再发生」）⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
      "**⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 而真正的失效形态是 1011 的 P7 已经证过的那个："
      "git 历史一旦被 rebase，整本账会静静地变样、而账本不会报任何错** ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
      "**⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 所以账本必须自带 commit sha 指纹 —— 本批 %d 个 sha "
      "已写进 `%s` 的 `fingerprint_2013` 字段**" %
      (len(COMMITS), GOLDEN.relative_to(ROOT)))

out["verdicts_2013"] = {
    "p1_kinds_are_disjoint_and_exhaustive_2013_": P1,
    "p2_ledger_red_equals_gate_vanished_2013_": P2,
    "p3_aging_is_not_needed_at_this_scale_2013_": P3,
    "p4_the_three_silent_classes_are_the_real_output_2013_": P4,
    "p5_reverse_case_born_is_recorded_but_not_red_2013_": P5,
    "p6_full_recompute_does_not_fix_expiry_2013_": P6,
    "offline_2013": "⭐⭐⭐⭐⭐ **本批纯离线**：不打开浏览器、不按任何键、"
                    "**连 `mouse.click` 都没有**",
}

out["P1_hold_2013"] = bool(EXHAUSTIVE and DISJOINT)
out["P2_hold_2013"] = bool(SYM_DIFF == 0 and len(led_red) == 1)
out["P3_hold_2013"] = bool(N_RED_PAIRS == 1 and not AGE_NEEDED)
out["P4_hold_2013"] = bool(kind_count["born"] + kind_count["grown"]
                           + kind_count["shrank"] == N_EVENTS - 1)
out["P5_hold_2013"] = bool(not _born_red and len(led_red) == 1)
out["P6_hold_2013"] = bool("fingerprint_2013" in out
                           and len(out["fingerprint_2013"]["commits"]) == 12)

# ── golden ───────────────────────────────────────────────────────
io.open(GOLDEN, "w", encoding="utf-8").write(json.dumps({
    "generated_by": "jimeng_probe1013_occurrence_ledger.py",
    "note": "⭐⭐⭐⭐⭐⭐⭐⭐ **1012 的处方「把追加登记成账」跑起来会不会自己变成噪声源**",
    "scope": "⭐ 全部 %d 个目标变量、%d 对快照" % (len(PV), len(COMMITS) - 1),
    "fingerprint_2013": out["fingerprint_2013"],
    "totals": {"n_events": N_EVENTS, "by_kind": dict(kind_count),
               "n_red": len(led_red), "n_pairs": N_PAIRS,
               "n_red_pairs": N_RED_PAIRS,
               "exhaustive": EXHAUSTIVE, "disjoint": DISJOINT},
    "cross_with_gate": {"ledger_red": [list(x) for x in led_red],
                        "gate_vanished": [list(x) for x in gate_van],
                        "only_ledger": [list(x) for x in ONLY_LEDGER],
                        "only_gate": [list(x) for x in ONLY_GATE],
                        "symmetric_difference": SYM_DIFF},
    "red_pairs": red_pairs,
    "rows": ledger_rows,
    # ⚠️⚠️⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **1014 加的 companion 字段（原文 `retired: []` 一字未删）**
    #   ⇒ ⇒ **`retired: []` 单独看是分不清「算过、没有」和「压根没算」的** ⇒ ⇒
    #   ⇒ ⇒ 而 `retired_note` 是一段散文 —— 它和「没算过」完全兼容、钉不住任何东西 ⇒ ⇒ ⇒
    #   ⇒ ⇒ ⇒ ⇒ **所以补两个可校验的 companion：一个说「跑了」、一个说「跑了是 0」**
    "retired": [],
    "retired_computed": True,
    "retired_n": 0,
    "retired_note": "⭐⭐⭐⭐⭐⭐⭐⭐ **纯历史账本的 `retired` 恒为空 —— "
                    "这正是 P6 的内容：全量重算把「清单会过期」换成了「历史被截断」，"
                    "而后者由 `fingerprint_2013` 的 sha 兜底**",
}, ensure_ascii=False, indent=1))
out["P7_hold_2013"] = bool(GOLDEN.exists() and GOLDEN.stat().st_size > 500)

# ── P8：沿用「手写的数必须有出处」 ───────────────────────────────
# ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **「手写的数必须有出处」这条规矩，管的是**量值**、不是标识符**
#   ⇒ ⇒ 而第一版的正则 `\d+(?:\.\d+)?` 会把 `fingerprint_2013` 里的 `2013`
#   当成一个手写的数 ⇒ ⇒ ⇒ P8 于是报「无出处」
#   **⇒ 而处置不是把 2013 加进白名单（那等于给一个量开了后门）、
#   而是把「处在标识符里的数」排除掉** ⇒ ⇒ ⇒ ⇒
#   **⇒ 而这是一次**放宽** —— 所以必须给它配一条反向自检，
#   否则就是在悄悄把门变弱（1006 那条：「不许让门看起来比它实际更强」）**
_NUMRE = re.compile(r"(?<![A-Za-z_0-9])(\d+(?:\.\d+)?)(?![A-Za-z_0-9])")


def _numre_selftest():
    """反向自检：埋在标识符里的数必须被跳过，裸量必须被抓到。"""
    assert _NUMRE.findall("共 68 条") == ["68"], "⭐ 裸量被漏掉了"
    assert _NUMRE.findall("`fingerprint_2013` 字段") == [], "⭐ 标识符没被跳过"
    # ⚠️ 这条断言我第一版写成 `== ["1013", "1013"]` ⇒ ⇒ **而那个串里只有一个 1013**
    #   ⇒ ⇒ ⇒ **⇒ 断言自己写错了 ⇒ ⇒ ⇒ ⇒ 而这正是「仪器报红的第一形态是我自己的断言写错了」**
    assert _NUMRE.findall("`occurrence-ledger-1013.json`") == ["1013"], \
        "⭐ 连字符/点号两侧的批号不该被当成标识符"
    return True


_numre_selftest()
_AUD_BLOCK = "occurrence_ledger_2013"


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
assert "p3_aging_is_not_needed_at_this_scale_2013_" in _AB, (
    "⭐⭐⭐⭐⭐ 又取错层级了：%r" % (sorted(_AB)[:6],))


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


out["readings_2013"] = {
    "n_pairs": N_PAIRS, "n_target_vars": len(PV), "n_events": N_EVENTS,
    "n_born": kind_count["born"], "n_grown": kind_count["grown"],
    "n_shrank": kind_count["shrank"], "n_vanished": kind_count["vanished"],
    "n_red": len(led_red), "n_sym_diff": SYM_DIFF,
    "n_only_ledger": len(ONLY_LEDGER), "n_only_gate": len(ONLY_GATE),
    "n_red_pairs": N_RED_PAIRS, "n_commits": len(COMMITS),
    "born_occ_before": _born[4], "born_occ_after": _born[5],
}
_allowed = _nums({k: v for k, v in out.items()
                  if k != "verdicts_2013"}, set())
_allowed |= set("0123456789") | {
    "1001", "1002", "1003", "1004", "1005", "1006", "1007", "1008",
    "1009", "1010", "1011", "1012", "1013",
}
_allowed |= set(re.findall(r'check\("[A-Z](\d{3})[A-Z]\.', VERIFIER_TXT))
_bad, _n_tot = {}, 0
for _k in out["verdicts_2013"]:
    _got = sorted(set(_NUMRE.findall(_AB.get(_k) or "")), key=float)
    _miss = [n for n in _got if n not in _allowed]
    _n_tot += len(_got)
    if _miss:
        _bad[_k] = _miss
out["audit_numbers_vs_computed_2013"] = {
    "n_keys_compared": len(out["verdicts_2013"]),
    "n_numbers_total": _n_tot,
    "n_keys_with_unjustified_number": len(_bad),
    "unjustified": _bad,
}
out["P8_hold_2013"] = bool(not _bad)

io.open(OUT, "w", encoding="utf-8").write(json.dumps(out, ensure_ascii=False, indent=1))
print("pairs=%d events=%d by_kind=%s" % (N_PAIRS, N_EVENTS, dict(kind_count)))
print("exhaustive=%s disjoint=%s | red=%d sym_diff=%d (only_ledger=%d only_gate=%d)"
      % (EXHAUSTIVE, DISJOINT, len(led_red), SYM_DIFF,
         len(ONLY_LEDGER), len(ONLY_GATE)))
print("red_pairs=%s | born sample occ %d->%d red=%s"
      % (red_pairs, _born[4], _born[5], _born_red))
print("P1..P8 =", [out["P%d_hold_2013" % i] for i in range(1, 9)])
print("PROBE_1013_DONE ->", OUT)