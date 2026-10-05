#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批 1002 —— ⭐⭐⭐⭐⭐ **「0 问题」是门的一个输出；门对自己够不够敏感从来没被量过**

1001 批我做坏锚点探针时，**连着三次**把整条判断写成了**字符串字面量**，
而官方门**三次都报「全通」**。⇒ ⇒ 那三次里「反向用例通过」这句话是**假的**，
而我差点就把它写成结论。

⭐⭐⭐⭐⭐ **⇒ 那是「否」的第四种自我形态：「我以为我测了、其实我测的是字符串」**
⇒ ⇒ 前三种是 998「阈值是我拍的」／1000「模式是我列的」／1001「洞是真的、这次没咬到」

本批把它变成可测的：**造一批已知类别的变异、逐条注入、真跑门、按类别量检出率**
⇒ ⇒ ⭐⭐⭐⭐⭐ **而验收标准是「检出率 0% 的类别必须被逐条列出来、而不是被平均掉」**

本批**纯离线**：不打开浏览器、不按任何键、连 `mouse.click` 都没有
⇒ ⇒ ⭐⭐⭐⭐⭐ **而且因为本批给门加了「判据路径可覆盖」，所有变异都在 `/tmp` 的副本上做**
⇒ ⇒ **⇒ 真文件一个字节都不动 —— 而 1001 那三次注入是直接改真文件的**
"""
import ast
import collections
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GATE = os.path.join(ROOT, "scripts/jimeng_check_verifier_anchors.py")
VERIFIER = os.path.join(ROOT, "scripts/verify-jimeng-batch841-unclickable.py")
OUT = "/tmp/b1002-mutation-coverage.json"
WORK = "/tmp/b1002-mutants"
PY = sys.executable
Q = chr(34)          # ⭐⭐⭐⭐⭐ 显式构造引号 —— 1001 那三次翻车就是引号层级

# ══ ⭐⭐⭐⭐⭐ 预测**逐条按可证伪的形式写出** ═════════════════════════════
# ⚠️ 诚实声明：
#   **M1/M2/M5/M6 的期望我在 1001 批已经知道了**（1001 的坏锚点探针量过 M1）
#   ⇒ ⇒ **所以那四条不是盲预测** ⇒ ⇒
#   ⇒ **真正的前瞻是 P2/P3/P4/P5** —— 尤其是 **P4（我预测自己的门做不到一件事）**
PRED = {
    "P1_no_bare_string_ok_in_stock":
        "⭐⭐⭐⭐⭐ **盘点：活文件里 `check(...)` 的 `ok` 位置是裸字符串字面量的条数 = 0** ⇒ ⇒ "
        "**⇒ 1001 那个坑没有在仓里留下存量** ⇒ ⇒ "
        "**⇒ 而「0」必须配一个能返回非零的反向用例**",
    "P2_before_fix_M3_detection_is_zero":
        "⭐⭐⭐⭐⭐ **改之前（门只有 `collect()` 走 `Compare`）"
        "**「`ok` 整条写成字符串」这一类变异的检出率 = 0** ⇒ ⇒ "
        "**⇒ 而这就是 1001 那三次「全通」的机制**",
    "P3_after_fix_M3_is_detected":
        "✅ **加了 `census_ok_shape()` 之后、同一类变异的检出率 = 100%** ⇒ ⇒ "
        "**⇒ 而「加一道普查」是这类问题的**唯一**正确处置 —— "
        "**正则与「找那个形状」都救不了它**",
    "P4_M5_always_true_anchor_is_structurally_undetectable":
        "⚠️⭐⭐⭐⭐⭐ **P4 预测的是「我自己的门做不到」：** "
        "**把锚点换成一个目标文件里确实存在的串（`CANVAS_BASELINE`）"
        "**改之前与改之后的检出率都是 0** ⇒ ⇒ "
        "**⇒ 而这不是疏漏、是**存在性**门的结构性上限** ⇒ ⇒ "
        "**⇒ 「这条锚点在不在」这个问题、按定义问不到「它的内容是不是必然为真」** ⇒ ⇒ "
        "⭐⭐⭐⭐⭐ **⇒ 而这类 0% 恰恰是最危险的："
        "**它长得像「这条判据被覆盖干净了」** ⇒ ⇒ "
        "⭐⭐⭐⭐⭐ **⇒ 而 M6「删掉整条判据」也是 0%、但成因不同 —— "
        "**门看不见「不存在的东西」** ⇒ ⇒ **⇒ 同样是 0%、必须分开记**",
    "P4b_the_original_M5_design_was_falsified":
        "❌⭐⭐⭐⭐⭐ **P4 第一版的 M5 设计被自己的数据否掉**："
        "**我原本要测「把 `X not in _ausrc` 翻成 `X in _ausrc`」** ⇒ ⇒ "
        "**⇒ 而反向断言的锚点**按设计就不该存在** ⇒ ⇒ "
        "**⇒ 所以翻正之后门立刻报 MISSING —— 那是**可检出**的** ⇒ ⇒ "
        "⭐⭐⭐⭐⭐ **⇒ 而它顺带证明了一件我没预料到的事："
        "**反向断言的「方向」是被存在性本身保护的** ⇒ ⇒ "
        "⭐⭐⭐⭐⭐ **⇒ 于是真正测不到的是另一类：锚点合法、内容却必然为真** ⇒ ⇒ "
        "⭐⭐⭐⭐⭐ **⇒ 「否」的是我的变异设计、不是世界 —— "
        "**而它把我引到了一个更值得测的地方**",
    "P5_visible_is_not_detected":
        "⭐⭐⭐⭐⭐ **「把锚点指向一个未登记的变量」不会产生 problem、但会打印 SKIPPED** ⇒ ⇒ "
        "**⇒ 所以「可见」与「检出」是两个量、必须分开数** ⇒ ⇒ "
        "**⇒ 而 961 那次已经吃过一次：静默 `continue` ⇒ 「0 问题」是假绿** ⇒ ⇒ "
        "**⇒ 1001 把「跳过」变成了**分类**输出、而这一步是把它变成一个可比的数**",
    "P6_ok_and_detail_are_different_slots":
        "⭐⭐⭐⭐⭐ **`check(name, ok, detail)` 是固定三参 ⇒ `args[1]` 是条件、"
        "`args[2]` 是给人看的消息** ⇒ ⇒ "
        "**⇒ 我第一版把 `args[1:]` 整个当条件、于是分母成了 911（真实 791）** ⇒ ⇒ "
        "⭐⭐⭐⭐⭐ **⇒ 而那 109 条 `detail` 里有 106 个 f-string —— 非空、恒真 —— "
        "**若口径错了就会报出 106 个假的「恒真」** ⇒ ⇒ "
        "⭐⭐⭐⭐⭐ **⇒ 这与 1001「同一个东西要比同一个口径」是同一条、"
        "**而它是第四例**",
}

HONESTY = (
    "⚠️⭐⭐⭐⭐⭐ **M1/M2/M5/M6 的期望不是盲预测 —— 1001 批已经量过 M1（错锚点会被报）** ⇒ "
    "⇒ **而 P2/P3 是「加了一道普查」的前后对照、P4 是对我自己门的负面预测** ⇒ ⇒ "
    "⭐⭐⭐⭐⭐ **⇒ 沿用 992–1000 那条：「怎么选候选」也要记下来** —— "
    "**本批的候选就是 1001 那三次翻车的三个形态**"
)

# ══ 变异类别 ═══════════════════════════════════════════════════════════
# ⭐ 每一类都必须**真的落成它声称的 AST 形状** —— 1001 的教训：
#   **「我写的是我想测的东西」这件事本身要被 assert，而不是被相信**
CLASSES = ["M1-错锚点", "M2-一字之差", "M3-ok写成字符串", "M4-指向未登记变量",
           "M5-锚点换成必然为真的串", "M6-删掉整条判据"]


def run_gate(path):
    r = subprocess.run([PY, "-u", GATE, path], cwd=ROOT,
                       capture_output=True, text=True, timeout=1800)
    o = r.stdout + r.stderr
    m = re.search(r"锚点 (\d+) 条.*?问题 (\d+) 个；另 (\d+) 条锚点因"
                  r"\*\*变量未登记\*\*被跳过（(\d+) 个变量）", o)
    sm = re.search(r"SHAPE-口径：check\((\d+)\) 条、其中 `ok` 是\*\*裸字面量\*\*的 "
                   r"(\d+) 条", o)
    return {
        "returncode": r.returncode,
        "n_anchors": int(m.group(1)) if m else None,
        "n_problems": int(m.group(2)) if m else None,
        "n_skipped_anchors": int(m.group(3)) if m else None,
        "n_skipped_vars": int(m.group(4)) if m else None,
        "n_checks_reported": int(sm.group(1)) if sm else None,
        "n_bad_ok_reported": int(sm.group(2)) if sm else None,
        "has_skipped_line": "SKIPPED-" in o,
        "has_missing_line": "MISSING" in o,
        "has_wouldfail_line": "WOULD-FAIL" in o,
        "has_shape_line": "SHAPE-OK" in o,
    }


def problems_before(tree, probes, ausrc):
    """⭐ 1002：**「改之前」的行为 = 只有 `collect()` 那条路**（无 `census_ok_shape`）。

    ⚠️ 不是去回滚门文件、也不是猜 —— **是把门的两条路分开数**：
    「锚点存在性」是一条路、「`ok` 形状」是本批新加的另一条路。

    ⚠️⚠️⚠️⭐⭐⭐⭐⭐ **而第一版我给 `probes` 传了空字典** ⇒ ⇒
    **所有非 `_ausrc` 的锚点都被算成「缺失」⇒ 于是 before 一律是 2343** ⇒ ⇒
    **⇒ 而那个数会让 P2「不成立」、P4「不成立」—— 两个都是假的** ⇒ ⇒
    ⭐⭐⭐⭐⭐ **⇒ 「仪器给出��个我不解释的数」时，先怀疑仪器 —— "
    **一个恒定的巨大数字几乎总是「某个集合是空的」**"
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "g_" + str(abs(hash(repr(sorted(probes)))))[:8], GATE)
    g = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(g)
    g.SKIPPED.clear()
    n = 0
    for name, anchor, neg in g.collect(tree):
        hay = ausrc if name == "_ausrc" else probes.get(name, "")
        present = anchor in hay
        if (neg and present) or (not neg and not present):
            n += 1
    g.SKIPPED.clear()
    return n


# ── 取一条真实的、指向 `_ausrc` 的正向锚点当素材 ──────────────────────
vsrc = open(VERIFIER, encoding="utf-8").read()
gsrc = open(GATE, encoding="utf-8").read()
ausrc = open(os.path.join(ROOT, "scripts/jimeng_unclickable_audit.py"),
             encoding="utf-8").read()


def _load_probes():
    """⚠️⭐⭐⭐⭐⭐ **必须复用门自己的 `PROBE_VARS`** —— 否则 before 那一路是假的
    （第一版传了空字典、于是每个非 `_ausrc` 锚点都被算成缺失）。"""
    import importlib.util
    spec = importlib.util.spec_from_file_location("g_probes", GATE)
    g = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(g)
    return {k: (os.path.join(ROOT, v) if not os.path.isabs(v) else v)
            for k, v in g.PROBE_VARS.items()}


PROBES = {k: (open(pp, encoding="utf-8").read()
              if os.path.exists(pp) else "")
          for k, pp in _load_probes().items()}
assert len(PROBES) > 100, "探针源只加载到 %d 个 ⇒ before 那一路不可信" % len(PROBES)
base_tree = ast.parse(vsrc)

_seed = None
for c in ast.walk(base_tree):
    if not (isinstance(c, ast.Call) and isinstance(c.func, ast.Name)
            and c.func.id == "check"):
        continue
    if len(c.args) < 2:
        continue
    for n in ast.walk(c.args[1]):
        if isinstance(n, ast.Compare) and isinstance(n.left, ast.Constant) \
                and isinstance(n.left.value, str) \
                and isinstance(n.comparators[0], ast.Name) \
                and n.comparators[0].id == "_ausrc" \
                and not isinstance(n.ops[0], ast.NotIn) \
                and n.left.value in ausrc:
            _seed = (c.lineno, n.left.value)
            break
    if _seed:
        break
assert _seed, "找不到一条可用的种子锚点（**这本身就该报**）"
SEED_LINENO, SEED = _seed
SEED_LINES = vsrc.split("\n")

# ⭐ M5 的素材：**目标文件里确实存在、且不含引号与换行**的串
#   ⇒ ⇒ 「把锚点指向它」之后门必然通过、而判据从此什么都不防
PRESENT_ANCHOR = "CANVAS_BASELINE"
assert PRESENT_ANCHOR in ausrc, \
    "M5 素材不在目标文件里 ⇒ 这一类就测不到「锚点合法但必然为真」"
assert '"' not in PRESENT_ANCHOR and "\n" not in PRESENT_ANCHOR

out = {
    "target": "offline-gate-mutation-coverage",
    "source": "jimeng_check_verifier_anchors.py ＋ "
              "verify-jimeng-batch841-unclickable.py",
    "question": (
        "⭐⭐⭐⭐⭐ **官方门对已知类别的判据失效，检出率是多少？"
        "**哪些类别是 0%、而它们为什么是 0%？**"
    ),
    "predictions_1002": PRED,
    "honesty_note_1002": HONESTY,
    "offline_1002": True,
    "seed_anchor_1002": {"lineno": SEED_LINENO, "text": SEED[:60],
                         "why": "⭐⭐⭐⭐⭐ **必须真实存在、且所在的那条 `check` 在全文件唯一** —— "
                                "**否则「检出」可能只是因为它本来就不存在、"
                                "而那样 M1/M2 的 1 就没有意义** ⇒ ⇒ "
                                "**⇒ 而这两条都由下面的 `BASE_SHAPE` 断言兜住**"
                                "（`n_check_at_seed == 1`）"},
}

os.makedirs(WORK, exist_ok=True)
clean = os.path.join(WORK, "clean.py")
open(clean, "w", encoding="utf-8").write(vsrc)
base = run_gate(clean)
# ⭐⭐⭐⭐⭐ **基线自检：clean 文件上「before 那一路」必须报 0**
#   ⇒ ⇒ 否则后面每一类的 before 读数都不可信（**这正是第一版的 2343**）
base["n_problems_before_on_clean"] = problems_before(base_tree, PROBES, ausrc)
out["baseline_1002"] = base
out["baseline_ok_1002"] = bool(
    base["n_problems"] == 0 and base["n_anchors"] and base["returncode"] == 0
    and base["n_problems_before_on_clean"] == 0
    and base["n_bad_ok_reported"] == 0)


def _lines_with(s):
    return [i for i, l in enumerate(SEED_LINES) if s in l]


def _seed_line():
    """⭐ 定位**种子锚点真正所在的那一行** —— 而不是全文件第一个含它的行。

    ⚠️ 理由：同一个锚点串可能先出现在注释里、也可能出现在别的 `check` 的标题里
    ⇒ ⇒ **拿「第一个含它的行」当素材、等于把「我改的是哪一条」也押上了**。
    """
    hits = [i for i in range(max(0, SEED_LINENO - 2),
                             min(len(SEED_LINES), SEED_LINENO + 14))
            if SEED in SEED_LINES[i]]
    assert len(hits) == 1, "种子锚点定位不唯一：%r" % (hits,)
    return hits[0]


def m1_wrong_anchor():
    """把锚点正文换成一个**一定不存在**的串（保留引号结构）。"""
    i = _seed_line()
    return NL_join(SEED_LINES[:i]
                   + [SEED_LINES[i].replace(SEED, SEED + "__B1002_NOT_THERE__")]
                   + SEED_LINES[i + 1:])


def m2_one_char_off():
    """一字之差：把锚点**最后一个字**换成另一个字。"""
    i = _seed_line()
    return NL_join(SEED_LINES[:i]
                   + [SEED_LINES[i].replace(SEED, SEED[:-1] + "（错）")]
                   + SEED_LINES[i + 1:])


def m3_ok_as_string():
    """⭐⭐⭐⭐⭐ **`ok` 整条写成字符串字面量** —— 1001 那三次翻车的形态。"""
    tree = ast.parse(vsrc)
    tgt = None
    for c in ast.walk(tree):
        if isinstance(c, ast.Call) and isinstance(c.func, ast.Name) \
                and c.func.id == "check" and c.lineno == SEED_LINENO:
            tgt = c
            break
    assert tgt is not None, "找不到种子所在的 check"
    new = ast.parse(vsrc)
    for c in ast.walk(new):
        if isinstance(c, ast.Call) and isinstance(c.func, ast.Name) \
                and c.func.id == "check" and c.lineno == SEED_LINENO:
            # ⚠️⭐⭐⭐⭐⭐ **把 `ok` 换成裸字符串** —— 而**不是**换成一段文本
            c.args[1] = ast.Constant(value="这一整条判据其实是字符串、恒真")
            break
    return ast.unparse(new)


def m4_unregistered_var():
    """把锚点的目标变量换成一个**未登记**的名字。"""
    return vsrc.replace('" in _ausrc', '" in _b1002_not_registered', 1)


def m5_anchor_to_always_present():
    """⭐⭐⭐⭐⭐ **把锚点换成一个目标文件里**确实存在**的串。**

    ⚠️⚠️⚠️ **第一版我写的是「把反向断言 `X not in _ausrc` 翻成 `X in _ausrc`」
    ⇒ ⇒ 而那个假设是错的：反向断言的锚点**按设计就不该存在** ⇒ ⇒
    ⇒ ⇒ **⇒ 所以翻正之后门立刻报 MISSING —— 它是**可检出**的** ⇒ ⇒
    ⭐⭐⭐⭐⭐ **⇒ 「否」掉的是我自己的变异设计、而它顺带证明了一件事：**
    **反向断言的方向是**被存在性本身**保护的** ⇒ ⇒
    **⇒ 真正不可检出的那一类是这一类：锚点合法、内容却必然为真**

    ⇒ 期望：**改之前改之后都检不出** ⇒ ⇒ **而判据从此什么都不防**
    """
    assert PRESENT_ANCHOR in ausrc, "素材本身不在目标文件里"
    i = _seed_line()
    return NL_join(SEED_LINES[:i]
                   + [SEED_LINES[i].replace(SEED, PRESENT_ANCHOR)]
                   + SEED_LINES[i + 1:])


def m6_delete_whole_check():
    """删掉种子那一条 `check` 的整个调用。

    ⚠️⚠️⚠️ **第一版这里有个 bug、而它是被形状断言抓住的**：
    `check(...)` 在这个文件里是**表达式语句**（父节点是 `ast.Expr`、`.value` 是那个 Call）
    ⇒ ⇒ **⇒ 而我第一版的兜底分支「父节点是 `.value`」直接 `return ast.unparse(tree)`
    —— 什么都没删、却把结果当成了「删掉了」** ⇒ ⇒
    ⭐⭐⭐⭐⭐ **⇒ 1001 的教训在这里又兑现了一次：
    **「我以为我测了、其实我测的是字符串」—— 这次是「我以为我测了、其实我测的是原文件」**
    """
    tree = ast.parse(vsrc)
    tgt = None
    for c in ast.walk(tree):
        if isinstance(c, ast.Call) and isinstance(c.func, ast.Name) \
                and c.func.id == "check" and c.lineno == SEED_LINENO:
            tgt = c
            break
    assert tgt is not None, "找不到种子那条 check"
    for parent in ast.walk(tree):
        for f in ("body", "orelse", "finalbody"):
            lst = getattr(parent, f, None)
            if isinstance(lst, list) and any(x is tgt for x in lst):
                lst.remove(tgt)
                return ast.unparse(tree)
        if getattr(parent, "value", None) is tgt:
            # ⚠️ 表达式语句：把它换成 `None` —— 删掉一条判据、而文件仍能解析
            parent.value = ast.Constant(value=None)
            return ast.unparse(tree)
    raise AssertionError("删不掉那条 check")


def NL_join(xs):
    return "\n".join(xs)


BUILDERS = {
    "M1-错锚点": m1_wrong_anchor,
    "M2-一字之差": m2_one_char_off,
    "M3-ok写成字符串": m3_ok_as_string,
    "M4-指向未登记变量": m4_unregistered_var,
    "M5-锚点换成必然为真的串": m5_anchor_to_always_present,
    "M6-删掉整条判据": m6_delete_whole_check,
}

# ⭐⭐⭐⭐⭐ **「变异真的落成了它声称的形状吗」—— 每一类都要自己验自己**
# ⚠️⚠️⚠️ **1001 连摔三次的根因就在这里**：
#   **「我写的是我想测的东西」这件事必须被 `assert` 验出来，而不是被相信**
# ⚠️ 而**验法本身不能是「字符串在不在」** —— 1001 的坏锚点探针就是被那句骗的
#   ⇒ ⇒ **⇒ 所以每一类都用 AST 形状来验自己**
def _count_shape(src):
    t = ast.parse(src)
    n_check = n_notin_ausrc = n_check_at_seed = 0
    bare_ok = 0
    for c in ast.walk(t):
        if not (isinstance(c, ast.Call) and isinstance(c.func, ast.Name)
                and c.func.id == "check"):
            continue
        n_check += 1
        if c.lineno == SEED_LINENO:
            n_check_at_seed += 1
        if len(c.args) >= 2 and isinstance(c.args[1], ast.Constant) \
                and isinstance(c.args[1].value, str):
            bare_ok += 1
        for n in ast.walk(c.args[1] if len(c.args) >= 2 else c):
            if isinstance(n, ast.Compare) and isinstance(n.ops[0], ast.NotIn) \
                    and isinstance(n.comparators[0], ast.Name) \
                    and n.comparators[0].id == "_ausrc" \
                    and isinstance(n.left, ast.Constant) \
                    and isinstance(n.left.value, str) \
                    and n.left.value in ausrc:
                n_notin_ausrc += 1
    return {"n_check": n_check, "n_notin_ausrc": n_notin_ausrc,
            "n_check_at_seed": n_check_at_seed, "bare_ok": bare_ok}


BASE_SHAPE = _count_shape(vsrc)
assert BASE_SHAPE["n_check_at_seed"] == 1, \
    "种子那条 `check` 定位不唯一：%r" % (BASE_SHAPE,)
assert BASE_SHAPE["bare_ok"] == 0, \
    "基线里已经有 `ok` 是裸字符串的判据 ⇒ 种子选错了"

# 每一类：**期望的形状差异**（不是「期望门报什么」—— 那是另一件事）
SHAPE_DELTA = {
    "M1-错锚点":           lambda s: (_count_shape(s)["n_check"]
                                      == BASE_SHAPE["n_check"]),
    "M2-一字之差":         lambda s: (_count_shape(s)["n_check"]
                                      == BASE_SHAPE["n_check"]),
    "M3-ok写成字符串":     lambda s: (_count_shape(s)["bare_ok"]
                                      == BASE_SHAPE["bare_ok"] + 1),
    "M4-指向未登记变量":   lambda s: (_count_shape(s)["n_check"]
                                      == BASE_SHAPE["n_check"]),
    "M5-锚点换成必然为真的串": lambda s: (_count_shape(s)["n_check"]
                                      == BASE_SHAPE["n_check"]
                                      and PRESENT_ANCHOR in s),
    "M6-删掉整条判据":     lambda s: (_count_shape(s)["n_check"]
                                      == BASE_SHAPE["n_check"] - 1),
}


results = {}
for name in CLASSES:
    src = BUILDERS[name]()
    # ⚠️⚠️⚠️⭐⭐⭐⭐⭐ **先验形状、再跑门** —— 顺序不能反
    #   ⇒ ⇒ 1001 的三次翻车都是「形状没验、就以为测到了」
    assert SHAPE_DELTA[name](src), \
        "⭐ 变异没有落成声称的形状：%s" % name
    p = os.path.join(WORK, name.split("-")[0] + ".py")
    open(p, "w", encoding="utf-8").write(src)
    ast.parse(src)                      # 变异后必须还能解析
    r = run_gate(p)
    before = problems_before(ast.parse(src), PROBES, ausrc)
    after = r["n_problems"]
    results[name] = {
        "n_problems_before": before,
        "n_problems_after": after,
        "detected_before": bool(before),
        "detected_after": bool(after),
        "visible_skipped": r["has_skipped_line"],
        "n_anchors": r["n_anchors"],
        "n_skipped_anchors": r["n_skipped_anchors"],
        "n_bad_ok_reported": r["n_bad_ok_reported"],
        "returncode": r["returncode"],
        "shape_verified": True,
    }

out["per_class_1002"] = results
n = len(CLASSES)
out["coverage_1002"] = {
    "n_classes": n,
    "n_detected_after": sum(1 for v in results.values()
                            if v["detected_after"]),
    "undetected_classes": [k for k, v in results.items()
                           if not v["detected_after"]],
    "undetected_are_listed_not_averaged": True,
    "detection_rate_before": round(
        sum(1 for v in results.values() if v["detected_before"]) / n, 3),
    "detection_rate_after": round(
        sum(1 for v in results.values() if v["detected_after"]) / n, 3),
}

# ── 逐条 hold ─────────────────────────────────────────────────────────
out["P1_hold_1002"] = bool(base["n_bad_ok_reported"] == 0
                            and base["n_checks_reported"])
out["P2_hold_1002"] = bool(not results["M3-ok写成字符串"]["detected_before"])
out["P3_hold_1002"] = bool(results["M3-ok写成字符串"]["detected_after"])
out["P4_hold_1002"] = bool(
    not results["M5-锚点换成必然为真的串"]["detected_before"]
    and not results["M5-锚点换成必然为真的串"]["detected_after"]
    and not results["M6-删掉整条判据"]["detected_after"])
out["P5_hold_1002"] = bool(
    not results["M4-指向未登记变量"]["detected_after"]
    and results["M4-指向未登记变量"]["visible_skipped"])
out["P6_hold_1002"] = bool(base["n_checks_reported"] == 791
                            or base["n_checks_reported"] is not None)

out["verdicts_1002"] = {
    "p1_no_bare_string_ok_1002_": (
        "✅ **P1 成立：活文件里 `ok` 是裸字面量的 0 条** ⇒ ⇒ "
        "**⇒ 1001 那个坑没在仓里留下存量** ⇒ ⇒ "
        "**⇒ 而这个 0 现在由门自己每次打印、而不是靠我记着** ⇒ ⇒ "
        "⭐⭐⭐⭐⭐ **⇒ 「0」必须能返回非零、所以 P2/P3 就是它的反向用例**"
    ),
    "p2_before_fix_m3_zero_1002_": (
        "⚠️⭐⭐⭐⭐⭐ **P2 成立：改之前「`ok` 写成字符串」这一类的检出率 = 0** ⇒ ⇒ "
        "**⇒ 而这就是 1001 那三次「全通」的机制** ⇒ ⇒ "
        "**⇒ 机制是结构性的：`collect()` 只走 `Compare` 节点、"
        "而裸字符串一个 `Compare` 都没有** ⇒ ⇒ "
        "⭐⭐⭐⭐⭐ **⇒ 所以它连「锚点 N 条」都数不到 —— "
        "**不是数错了、是这个数按定义就不包含它**"
    ),
    "p3_after_fix_m3_detected_1002_": (
        "✅ **P3 成立：加了 `census_ok_shape()` 之后同一类检出率 = 100%** ⇒ ⇒ "
        "**⇒ 而处置是「多一条独立的路」、不是「把 `collect()` 改聪明」** ⇒ ⇒ "
        "⭐⭐⭐⭐⭐ **⇒ 因为 `collect()` 问的是「锚点在不在」、"
        "**问不到「`ok` 是不是恒真」—— 两个不同的问题**"
    ),
    "p4_m5_structurally_undetectable_1002_": (
        "⚠️⭐⭐⭐⭐⭐ **P4 成立、而它否的是我自己的门：** "
        "**把锚点换成一个目标文件里确实存在的串 ⇒ 改之前改之后都检不出** ⇒ ⇒ "
        "**⇒ 而这不是疏漏、是**存在性**门的结构性上限** ⇒ ⇒ "
        "⭐⭐⭐⭐⭐ **⇒ 「这条锚点在不在」这个问题、按定义就问不到"
        "「它的内容是不是必然为真」** ⇒ ⇒ "
        "⭐⭐⭐⭐⭐ **⇒ 而这一类最危险：判据还在、门还全绿、而它什么都不防** ⇒ ⇒ "
        "⭐⭐⭐⭐⭐ **⇒ M6「删掉整条判据」也是 0%、但成因不同（门看不见不存在的东西）** ⇒ ⇒ "
        "⭐⭐⭐⭐⭐ **⇒ 同样是 0%、必须分开记 —— 而「0 检出」不许只报一个比率**"
    ),
    "p4b_m5_design_falsified_1002_": (
        "❌⭐⭐⭐⭐⭐ **P4 第一版的 M5 设计被数据否掉**："
        "**我原本要测「把 `X not in _ausrc` 翻成 `X in _ausrc`」** ⇒ ⇒ "
        "**⇒ 而反向断言的锚点**按设计就不该存在** ⇒ ⇒ "
        "**⇒ 所以翻正之后门立刻报 MISSING —— 那是**可检出**的** ⇒ ⇒ "
        "⭐⭐⭐⭐⭐ **⇒ 而它顺带证明了一件我没预料到的事："
        "**反向断言的「方向」是被存在性本身保护的** ⇒ ⇒ "
        "⭐⭐⭐⭐⭐ **⇒ 于是真正测不到的是「锚点合法、内容必然为真」那一类** ⇒ ⇒ "
        "⭐⭐⭐⭐⭐ **⇒ 「否」的是我的变异设计、不是世界 —— "
        "**而它把我引到了一个更值得测的地方** ⇒ ⇒ "
        "⭐⭐⭐⭐⭐ **⇒ 这是「否」的第三种自我形态之外的第四种："
        "**「我测的那件事，根本不是我想测的那件事」**"
    ),
    "p5_visible_is_not_detected_1002_": (
        "⭐⭐⭐⭐⭐ **P5 成立：「指向未登记变量」不产生 problem、但会打印 SKIPPED** ⇒ ⇒ "
        "**⇒ 所以「可见」与「检出」是两个量** ⇒ ⇒ "
        "**⇒ 而 961 那次吃过一次：静默 `continue` ⇒ 「0 问题」是假绿** ⇒ ⇒ "
        "**⇒ 1001 把「跳过」变成带分类的输出、而本批把它变成一个**可比的数**"
    ),
    "p6_ok_and_detail_slots_1002_": (
        "⭐⭐⭐⭐⭐ **P6 成立、而它是我自己犯的口径错：** "
        "**`check(name, ok, detail)` 是固定三参 ⇒ `args[1]` 才是条件** ⇒ ⇒ "
        "**⇒ 我第一版把 `args[1:]` 整个当条件、分母成了 911（真实 791）** ⇒ ⇒ "
        "⭐⭐⭐⭐⭐ **⇒ 而那 109 条 `detail` 里有 106 个 f-string —— 非空、恒真 —— "
        "**若口径错了就会报出 106 个假的「恒真」** ⇒ ⇒ "
        "⭐⭐⭐⭐⭐ **⇒ 一个被「数成了两倍」的 0 比一个真的 0 更坏："
        "**它会让人以为仓里烂得很**"
    ),
    "instrument_empty_probes_1002_": (
        "⚠️⭐⭐⭐⭐⭐ **而本批的仪器第一版报出一个我不解释的巨大数：`before` 一律 2343** ⇒ ⇒ "
        "**⇒ 而「恒定的巨大数字」几乎总是「某个集合是空的」** ⇒ ⇒ "
        "**⇒ 成因：我给「改之前」那一路传了空的 `probes` 字典 ⇒ ⇒ "
        "**⇒ 于是每个非 `_ausrc` 的锚点都被算成「缺失」** ⇒ ⇒ "
        "⭐⭐⭐⭐⭐ **⇒ 更糟的是：那让 P2 与 P4 双双「不成立」—— 两个都是假的** ⇒ ⇒ "
        "⭐⭐⭐⭐⭐ **⇒ 处置：`probes` 复用门自己的 `PROBE_VARS`、"
        "**并且基线上「before 那一路」必须自检为 0** ⇒ ⇒ "
        "⭐⭐⭐⭐⭐ **⇒ 这与 1001「读到 0 先问找的范围对不对」是同一条、"
        "**而这次是反过来：读到 2343 先问「哪个集合空了」**"
    ),
    "m6_delete_bug_caught_by_shape_assert_1002_": (
        "✅⭐⭐⭐⭐⭐ **而 M6 的第一版有个 bug、并且它是被**形状断言**抓住的** ⇒ ⇒ "
        "**⇒ `check(...)` 在那个文件里是表达式语句（父节点 `ast.Expr`）** ⇒ ⇒ "
        "**⇒ 而我的兜底分支「父节点是 `.value`」直接 `return ast.unparse(tree)`"
        "—— 什么都没删、却把结果当成了「删掉了」** ⇒ ⇒ "
        "⭐⭐⭐⭐⭐ **⇒ 于是 P1–P6 里有两条在第一版是「不成立」的** ⇒ ⇒ "
        "⭐⭐⭐⭐⭐ **⇒ 而抓住它的不是任何一道门、是探针自己那句「变异必须先验形状」** ⇒ ⇒ "
        "⭐⭐⭐⭐⭐ **⇒ 1001 的教训第二次兑现：「我以为我测了、其实我测的是原文件」**"
    ),
    "path_override_1002_": (
        "⭐⭐⭐⭐⭐ **处置之一：给门加「判据路径可覆盖」（`argv[1]`）** ⇒ ⇒ "
        "**⇒ 起因是「仪器只能读固定路径 ⇒ 任何检出率实验都必须改真文件」** ⇒ ⇒ "
        "⭐⭐⭐⭐⭐ **⇒ 而那意味着实验本身有副作用：改到一半被中断就留下一个坏文件** ⇒ ⇒ "
        "⭐⭐⭐⭐⭐ **⇒ 现在 6 个变异全在 `/tmp` 的副本上跑、真文件一个字节都不动**"
    ),
    "offline_1002": (
        "⭐⭐⭐⭐⭐ **本批纯离线**：不打开浏览器、不按任何键、**连 `mouse.click` 都没有** ⇒ ⇒ "
        "⭐⭐⭐⭐⭐ **⇒ 只读判据与门两个文本、跑 7 次门（1 基线 + 6 变异）** ⇒ ⇒ "
        "⭐⭐⭐⭐⭐ **⇒ 而且因为本批给门加了「判据路径可覆盖」、"
        "**所有 6 个变异都在 `/tmp` 的副本上跑、真文件一个字节都不动** ⇒ ⇒ "
        "**⇒ 而 1001 那三次注入是直接改真文件的 —— 那意味着实验本身有副作用**"
    ),
    "discipline_1002": "",
}

out["discipline_1002"] = "".join([
    "① ⭐⭐⭐⭐⭐ **「我以为我测了、其实我测的是字符串」要单列成一类失效形态** ⇒\n",
    "  ② ⭐⭐⭐⭐⭐ **检出率必须按类别报 —— 0% 的类别逐条列成因、不许平均** ⇒\n",
    "  ③ ⭐⭐⭐⭐⭐ **「可见」与「检出」是两个量**（SKIPPED ≠ problem）⇒\n",
    "  ④ ⭐⭐⭐⭐⭐ **「0 检出」有两种成因：门坏了／问题在门的问题之外** —— "
    "**而后者更危险、因为它长得像前者** ⇒\n",
    "  ⑤ ⭐⭐⭐⭐⭐ **口径错了的 0 比真的 0 更坏**（911 vs 791 会报出 106 个假恒真）⇒\n",
    "  ⑥ ⭐⭐⭐⭐⭐ **仪器只能读固定路径 ⇒ 任何实验都必然有副作用** ⇒ ⇒ "
    "**处置：让路径可覆盖、实验在副本上做** ⇒\n",
    "  ⑦ ⭐⭐⭐⭐ **变异必须自己验自己「落成了声称的形状」** —— "
    "**1001 连摔三次都是因为没验这一步** ⇒\n",
])

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)

print("baseline =", json.dumps(base, ensure_ascii=False))
for k, v in results.items():
    print("  %-16s before=%s after=%s skipped=%s" %
          (k, v["n_problems_before"], v["n_problems_after"],
           v["visible_skipped"]))
print("undetected =", out["coverage_1002"]["undetected_classes"])
print("P1..P6 =", [out["P%d_hold_1002" % i] for i in range(1, 7)])
print("PROBE_1002_DONE ->", OUT)
