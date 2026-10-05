#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批 997 —— ⭐⭐⭐⭐⭐ **把「31 个未登记变量」拆开：它们不是一个同质的集合**

996 刚造好那道门（读行 + `PROBE_VARS` 两处都要齐）。本批**拿它去扫一个活的实例**：
官方锚点自查门现在正在静默跳过 **169 条锚点 / 31 个变量**，
而它把 31 个**一律报成「未登记」**。

⭐⭐⭐⭐⭐ **而「31」这个数本身就是个复合量**：
　· `_p870s` 有一行普通的 `.read_text()` 读取行 ⇒ **真漏登记**（961/962 那个坑的第三次）
　· `_agp2` / `_sc_out` / `_sbtxt` … 是 `strip_comments(...)` 的**派生物**
　　⇒ **「漏登记」这个说法对它们是错的** —— 它们不是漏登记、
　　是 `PROBE_VARS`（名字 → 文件路径）**这张表的形状表达不了**
　· `out` / `data` / `EXPECTED_STATES` / `s` / `t` / `k` / `l` **根本不是文本**
　　（子进程输出、解析后的 JSON、字面量表、循环变量）

⭐⭐⭐⭐⭐ **⇒ 而这与 995 那条「共 N 条不给检索词」是同族的、只是更狠**：
995 是「同一件事被不同的词切开了」，**这一条是「同一张表里塞着三种不同的东西、
而门把它们统称成未登记」** ⇒ **⇒ 归类之前不该把 31 当成一个口子的大小**

⭐⭐⭐⭐⭐ **⇒ 而真正可修的只有 A 类** ⇒ **⇒ 补登记会改变门的行为**
⇒ **⇒ 所以「补之前的读数」与「补之后的读数」必须都记下来（996 P8 的第二次施用）**

本批**纯离线**：不打开浏览器、不按任何键、连 `mouse.click` 都没有
⇒ ⇒ ⭐⭐⭐⭐ **零计费是结构性的、不是自律的**
"""
import ast
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GATE = os.path.join(ROOT, "scripts/jimeng_check_verifier_anchors.py")
VERIFIER = os.path.join(ROOT, "scripts/verify-jimeng-batch841-unclickable.py")
OUT = "/tmp/b997-skipcensus.json"
PY = sys.executable

# ══ ⭐⭐⭐⭐⭐ 预测**逐条按可证伪的形式写出** ═════════════════════════════
# ⚠️ 诚实声明（沿用 992–996）：
#   **我在写判据前已经看过官方门打印的 31 个名字** ⇒
#   ⇒ **P2/P3 严格说不是盲预测**（我看过清单、只是没逐个查它们的赋值语句）
#   ⇒ ⇒ **P1/P4/P5 才是真正的前瞻**（它们要等我补登记、才知不知道成立）
PRED = {
    "P1_exactly_one_plain_readline":
        "**31 个里恰好 1 个是「有一行普通 `.read_text()` 读取」的（A 类）** —— "
        "**而它就是 `_p870s`、即 961/962 那个坑的第三次**",
    "P2_transformed_outnumber_plain":
        "⭐⭐⭐⭐⭐ **B 类（`strip_comments(...)` 的派生物）比 A 类多** ⇒ ⇒ "
        "**⇒ 「漏登记」这个说法对 B 类是错的** —— "
        "**它们不是漏登记、是这张表的形状表达不了**",
    "P3_some_names_are_single_letters":
        "**C 类里至少有一个是纯循环变量（`s` / `t` / `k` / `l` 之一）** ⇒ ⇒ "
        "**⇒ 而单字母名出现在「未登记变量」清单里、"
        "**本身就说明这个清单不是一个同质的集合**",
    "P4_fixing_registration_is_not_a_noop":
        "⚠️⭐⭐⭐⭐⭐ **把 A 类补登记进 `PROBE_VARS` 之后、官方门报的「问题」数 > 0** ⇒ ⇒ "
        "**⇒ 而如果仍然是 0，那补登记就是一次空动作、"
        "**也就说明「那 2 条锚点压根没人查过」这件事本身没有代价**",
    "P5_registration_moves_the_reading":
        "⭐⭐⭐⭐⭐ **补登记会改变门的行为** ⇒ "
        "**⇒ 所以「补之前的读数」与「补之后的读数」必须都记下来** ⇒ ⇒ "
        "**⇒ 这是 996 P8「钉判据与量现状有先后顺序」的第二次施用**",
}

HONESTY = (
    "⚠️⭐⭐⭐⭐⭐ **写判据前我已经看过官方门打印的那 31 个名字** ⇒ "
    "⇒ **P2/P3 严格说不是盲预测**（我看过清单、只是没逐个查它们的赋值语句）⇒ "
    "⇒ **而 P1/P4/P5 才是真正的前瞻** ⇒ ⇒ "
    "⭐⭐⭐⭐⭐ **沿用 992–996 那条：「怎么选候选」也要记下来**"
)

# ⭐⭐⭐⭐⭐ **反向用例的假名 —— 写死、不许改、而且必须自己通过被检的形状**
FAKE_A = "_p987"   # 形如 `_pNNN`、有读取行、**不在** `PROBE_VARS` ⇒ 期望被判 A
FAKE_B = "_p986b"  # 形如 `_pNNN`、**没有**读取行 ⇒ 期望被判 C（不是 A）
FAKE_C = "_agpxx"  # 形如 `_agp` 派生物、**没有**读取行 ⇒ 期望被判 C


def run_gate():
    """⭐⭐⭐⭐⭐ **用真的门当尺子、而不是用我重写的尺子**

    996 P9 那条「读到空与读到全部都可能长得像对」⇒ ⇒
    **如果我自己重写一遍收集逻辑、而它恰好返回 0 条、"
    "我就会把「读到空」当成「读齐了」** ⇒ ⇒
    **所以这里直接跑官方门、解析它的 `SKIPPED` 行**
    """
    r = subprocess.run([PY, "-u", GATE], cwd=ROOT, capture_output=True,
                       text=True, timeout=1800)
    out = r.stdout + r.stderr
    pairs = []
    for m in re.finditer(r"SKIPPED-未登记 \[(\S+)\] (\d+) 条锚点", out):
        pairs.append((m.group(1), int(m.group(2))))
    gate_cls: dict[str, list[str]] = {}
    for m in re.finditer(r"SKIPPED-分类 \[([^\]]+)\] (\d+) 个：(.+)", out):
        gate_cls[m.group(1).strip()] = m.group(3).strip().split()
    return r.returncode, out, pairs, gate_cls


def assignment_kinds(vsrc, name):
    r"""⭐⭐ 这个变量在 verifier 里的**全部赋值语句**形状

    ⚠️⚠️⚠️⭐⭐⭐⭐⭐ **第二版：改用 `ast.unparse`、不用逐行正则**
      第一版是 `^\s*NAME\s*=\s*(.+)$` ⇒ ⇒ **它把跨行的赋值截成了第一行** ⇒ ⇒
      **⇒ 而 `_tlc` 的赋值正好跨行** ⇒ ⇒ **⇒ 所以第一版读到的 RHS 里
      压根没有 `.read_text(`、`has_read_text` 读出来是 `false`** ⇒ ⇒
      **⭐⭐⭐⭐⭐ **⇒ 而我在同一份 JSON 里把 `_tlc` 判成 C、又在判据里写
      「它读过文件」—— 两个说法互相矛盾、而矛盾就摆在同一个文件里** ⇒ ⇒
      **⇒ 这与 996 P6 同一个根：拿「文本里出现了某个模式」当「那件事发生了」**
    """
    try:
        tree = ast.parse(vsrc)
    except SyntaxError:
        return []
    kinds = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        tgts = node.targets if isinstance(node, ast.Assign) \
            else [node.target]
        if any(isinstance(t, ast.Name) and t.id == name for t in tgts):
            kinds.append(ast.unparse(node.value) if node.value else "")
    return kinds


RX_GROUP = r"\.group\(|strip_|json\.loads|\.split\(|\["  # noqa: 只作兜底
RX_DERIVED = (r"strip_comments|strip_py_comments|json\.loads"
              r"|\.group\(|\.split\(|\[.*:|\+")
RX_LITERAL = (r"^\s*[\[\{\(]|\"\"|get\(|subprocess|stdout|"
              r"stderr|sorted\(|str\(")
RX_ALIAS = r"\s*\w+\s*"  # noqa: 仅作兜底


def rhs_nodes(vsrc, name):
    """⭐⭐⭐⭐⭐ **第三版：返回赋值右侧的 AST 节点**（不是文本）"""
    try:
        tree = ast.parse(vsrc)
    except SyntaxError:
        return []
    got = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        tgts = node.targets if isinstance(node, ast.Assign) \
            else [node.target]
        if any(isinstance(t, ast.Name) and t.id == name for t in tgts):
            if node.value is not None:
                got.append(node.value)
    return got


def is_plain_read(nd):
    """⭐⭐⭐⭐⭐ **「就是那个文件的原文」的**结构**判据**

    ⭐⭐⭐⭐⭐ **而它必须是结构判据、不能是「文本里有没有 `.read_text(`」** ——
    `_tlc` 那个反例正是踩在文本判据上：
    `\"\n\".join(... .read_text().splitlines() if not ln...startswith(("//", "*", "/*")))`
    **⇒ 里面有 `.read_text(`、可它同时是一个 comprehension + 一次过滤**
    """
    if isinstance(nd, ast.IfExp):
        # 允许 `X.read_text(...) if X.exists() else ""` 这种**只加了个存在性判断**的形状
        if not (isinstance(nd.test, ast.Call)
                and isinstance(nd.test.func, ast.Attribute)
                and nd.test.func.attr == "exists"):
            return False
        return is_plain_read(nd.body)
    if isinstance(nd, ast.Call) and isinstance(nd.func, ast.Attribute) \
            and nd.func.attr == "read_text":
        return True
    return False


def has_read_text_deep(nd):
    """⭐⭐⭐⭐⭐ **「不是原文、但子树里确实读过文件」—— B 类的结构判据**

    ⇒ **⇒ 而它同样是结构判据、不是「文本里有没有 `read_text`」** ⇒
    **⇒ `_tlc` 那个 `\"\n\".join(生成器)` 的子树里有一个 `read_text()` 调用**
    **⇒ 可它同时是一个 comprehension + 一次过滤 ⇒ 所以它是 B、不是 A**
    """
    for n in ast.walk(nd):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) \
                and n.func.attr == "read_text":
            return True
    return False


def classify(vsrc, name):
    """⭐⭐⭐ **四分类** —— 而第一版只有三类、**它自己造了一个假阳性**

    ⚠️⚠️⚠️⭐⭐⭐⭐⭐ **第二版修正的由来**：第一版的 `plain_read` 规则里有一句
    `or "else \"\"" in k` ⇒ ⇒ **它把 `_sbtxt = _sb.group(1) if _sb else ""`
    这种「正则捕获组」也判成了「普通读取」** ⇒ ⇒
    **⇒ 而那让 P1 从「成立（1 个）」翻成「被否（4 个）」** ⇒ ⇒
    **⭐⭐⭐⭐⭐ **⇒ 所以「门红了」和「门绿了」都不能直接信 ——
    要先问「门为什么是这个颜色」** —— **这是我自己的分类器造的假阳性**
    """
    kinds = assignment_kinds(vsrc, name)
    joined = " ".join(kinds)
    # ⭐⭐⭐⭐⭐ **A 类的判据是**结构**的（`is_plain_read` 看 AST 节点）——
    #   **不是「文本里有没有 `.read_text(`」** ⇒ `_tlc` 那个反例就踩在后者上
    _nodes = rhs_nodes(vsrc, name)
    plain_read = bool(_nodes) and all(is_plain_read(n) for n in _nodes)
    alias = bool(kinds) and bool(re.fullmatch(RX_ALIAS, joined))
    derived = (bool(re.search(RX_DERIVED, joined))
               or any(has_read_text_deep(n) for n in _nodes))
    literal = bool(re.search(RX_LITERAL, joined))
    if not kinds:
        cls = "D_loop_var"          # ⭐ 连赋值都没有 ⇒ 纯循环变量
    elif plain_read:
        cls = "A_plain_readline"    # ⭐ 真漏登记、可以直接补进 PROBE_VARS
    elif alias:
        cls = "E_alias"             # ⭐⭐ 别名：引用的是已读文本的另一个名字
    elif derived:
        cls = "B_derived_text"
    else:
        cls = "C_not_text"
    return {
        "name": name,
        "class": cls,
        "n_assignments": len(kinds),
        "rhs_head": [k[:70] for k in kinds[:2]],
        "is_p_shape": bool(re.fullmatch(r"_p\d{3}[a-z]?", name)),
    }


rc, gate_out, pairs, gate_cls = run_gate()
vsrc = open(VERIFIER, encoding="utf-8").read()
with open(GATE, encoding="utf-8") as f:
    gsrc = f.read()

out = {
    "target": "offline-skip-census",
    "source": "jimeng_check_verifier_anchors.py（**真的门**）"
              " ＋ verify-jimeng-batch841-unclickable.py",
    "question": (
        "⭐⭐⭐⭐⭐ **官方门正在静默跳过 169 条锚点 / 31 个变量 —— "
        "而它把它们一律报成「未登记」** ⇒ **这 31 个是一个同质的集合吗？**"
    ),
    "predictions_997": PRED,
    "honesty_note_997": HONESTY,
    "offline_997": True,
    "gate_returncode": rc,
    "fake_names_997": {"A": FAKE_A, "B": FAKE_B, "C": FAKE_C},
}

# ══ 门自己报的读数（**从门的输出里取、不重写**）════════════════════
# ⚠️⭐⭐⭐⭐⭐ **「补之前」那个读数是本批改门之前跑门记下的、原文照抄**
#   （锚点 5390 / 问题 0 / 跳过 169 条 / 31 个变量）
#   ⇒ ⇒ **两个读数都必须留着** —— **只报「补之后」就会把改动本身做成不可见**
BEFORE_997 = {"n_anchors": 5390, "n_problems": 0, "n_skipped_anchors": 169,
              "n_skipped_vars": 31}
# ⚠️⭐⭐⭐⭐⭐ **「补之前」的分类也是本批改门之前跑探针记下的、原文照抄**
#   ⇒ ⇒ **P1 断言的是「补之前」那个集合、不是补完之后的** ⇒
#   ⇒ **只报补完之后 A=0 就等于把「我刚把唯一那个补上了」写成「这一类本来是空的」**
BEFORE_CLASS_997 = {
    "n_vars": 31, "n_skipped_anchors": 169,
    "n_by_class": {"A_plain_readline": 1, "B_derived_text": 22,
                   "C_not_text": 4, "D_loop_var": 3, "E_alias": 1},
    "A_plain_readline": ["_p870s"],
    "E_alias": ["_aus936"],
    "C_not_text": ["EXPECTED_STATES", "_mod", "_tlc", "awhy"],
    "D_loop_var": ["k", "l", "t"],
}
m_prob = re.search(r"锚点 (\d+) 条.*?问题 (\d+) 个；另 (\d+) 条锚点因"
                   r"\*\*变量未登记\*\*被跳过（(\d+) 个变量）", gate_out)
out["after_997"] = {
    "n_anchors": int(m_prob.group(1)) if m_prob else None,
    "n_problems": int(m_prob.group(2)) if m_prob else None,
    "n_skipped_anchors": int(m_prob.group(3)) if m_prob else None,
    "n_skipped_vars": int(m_prob.group(4)) if m_prob else None,
    "read_from": "官方门自己的 stdout（**不重写收集逻辑**）",
}
out["before_997"] = dict(BEFORE_997,
                         read_from="本批改门**之前**跑官方门读到的、原文照抄")
out["skipped_pairs_997"] = pairs
out["total_skipped_anchors_997"] = sum(n for _, n in pairs)

rows = [classify(vsrc, n) for n, _ in pairs]
out["census_997"] = rows
by = {"A_plain_readline": [], "B_derived_text": [], "C_not_text": [],
      "D_loop_var": [], "E_alias": []}
for r in rows:
    by[r["class"]].append(r["name"])
for k in by:
    by[k].sort()
out["by_class_997"] = by
out["n_by_class_997"] = {k: len(v) for k, v in by.items()}
out["A_detail_997"] = [r for r in rows if r["class"] == "A_plain_readline"]
out["C_detail_997"] = [r for r in rows if r["class"] == "C_not_text"]
out["D_detail_997"] = [r for r in rows if r["class"] == "D_loop_var"]
out["E_detail_997"] = [r for r in rows if r["class"] == "E_alias"]

# ══ ⭐⭐⭐⭐⭐ **反向用例：三个假名喂给同一个分类器、期望各归各的类** ══
# ⚠️ 走**内存副本**、不碰真文件 ⇒ 零副作用、可每次都跑
_fake_src = vsrc + (
    '\n%s = Path("scripts/jimeng_probe987_x_src.py").read_text(encoding="utf-8")\n'
    % FAKE_A)
out["negative_control_997"] = {
    "injected": "只在内存里给分类器多喂三个名字、**不改真文件、不改 `PROBE_VARS`**",
    "A_expect_plain_readline": classify(_fake_src, FAKE_A)["class"],
    # ⚠️⭐⭐⭐⭐⭐ **期望标签我第一版也写错了**：`_p986b` 在假源里**没有赋值语句**
    #   ⇒ **它就该落进 `D_loop_var`、而不是「不是文本」那个类** ⇒ ⇒
    #   **⇒ 真正要断言的不是「它是哪一类」、是「有读取行才可能是 A」** ⇒
    "B_no_readline_must_not_be_A": (
        classify(_fake_src, FAKE_B)["class"] != "A_plain_readline"),
    "C_no_readline_must_not_be_A": (
        classify(_fake_src, FAKE_C)["class"] != "A_plain_readline"),
    "B_actual": classify(_fake_src, FAKE_B)["class"],
    "C_actual": classify(_fake_src, FAKE_C)["class"],
    "D_expect_loop_var": classify(_fake_src, "k")["class"],
    "E_expect_alias": classify(_fake_src + "\n_zz9 = _ausrc\n",
                                "_zz9")["class"],
    "why_this_matters": (
        "⭐⭐⭐⭐⭐ **这三个假名走的是同一个 `classify()`** ⇒ "
        "**⇒ 所以「A 类恰好 1 个」这个读数不是分类器恒真的产物** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐⭐ **而更关键的一条：如果分类器把三个都判成同一个类、"
        "我就会把「31 个」当成一个口子 —— 而那正是 P1 预言要否掉的东西**"
    ),
}
_nc = out["negative_control_997"]
out["NC_hold_997"] = bool(
    _nc["A_expect_plain_readline"] == "A_plain_readline"
    and _nc["B_no_readline_must_not_be_A"]
    and _nc["C_no_readline_must_not_be_A"]
    and _nc["D_expect_loop_var"] == "D_loop_var"
    and _nc["E_expect_alias"] == "E_alias")

out["before_class_997"] = BEFORE_CLASS_997
out["P1_hold_997"] = bool(
    BEFORE_CLASS_997["n_by_class"]["A_plain_readline"] == 1
    and BEFORE_CLASS_997["A_plain_readline"] == ["_p870s"])
out["P2_hold_997"] = bool(
    BEFORE_CLASS_997["n_by_class"]["B_derived_text"] >
    BEFORE_CLASS_997["n_by_class"]["A_plain_readline"])
# ⚠️⭐⭐⭐⭐⭐ **P4 的读数是实测的、而它的答案是「否」**
out["P4_hold_997"] = bool(out["after_997"]["n_problems"] > 0)
# ⚠️⭐⭐⭐⭐⭐ **P8 不是预测、是我盯着这个 0 想起来的**：
#   **补完之后 A 类是 0** ⇒ ⇒ **而「A 类是 0」与「A 类这一栏没有意义」在输出上一样**
#   ⇒ ⇒ **真实原因只是「我刚把唯一那个补上了」** ⇒ ⇒
#   ⇒ **这是 996 P2「恒真的读数要认出它」的同一条、只是对象换成了一个类**
out["P3_hold_997"] = bool(
    BEFORE_CLASS_997["D_loop_var"] == ["k", "l", "t"]
    and set(BEFORE_CLASS_997["C_not_text"]) & {"EXPECTED_STATES"})

# ══ ⭐⭐⭐⭐⭐ **两把独立写的尺子、量同一个集合** ⇒ **差集是读数**
#   门的 `classify_skipped()` 与本探针的 `classify()` 是**分别写的**
#   ⇒ ⇒ **它们在边界上不一致、而那不一致本身就是本批的一条发现**
_TAGMAP_997 = {
    "A_plain_readline": "A-可补登记(有一行普通 read_text)",
    "B_derived_text": "B-派生物(strip/group/切片)",
    "C_not_text": "C-不是文本(字面量/子进程/解析结果)",
    "D_loop_var": "D-连赋值都没有(循环变量)",
    "E_alias": "D-连赋值都没有(循环变量)",
}
out["gate_class_997"] = {k: sorted(v) for k, v in gate_cls.items()}
_gate_of = {}
for _tag, _names in gate_cls.items():
    for _n in _names:
        _gate_of[_n] = _tag
out["disagree_997"] = sorted(
    r["name"] for r in rows
    if _gate_of.get(r["name"]) not in
    (None, _TAGMAP_997[r["class"]]))
out["n_disagree_997"] = len(out["disagree_997"])
# ⭐⭐⭐⭐⭐ **而分歧的那几个、两边都判错了 —— 这才是关键**
_TLC = "".join(assignment_kinds(vsrc, "_tlc"))
out["tlc_truth_997"] = {
    "rhs": _TLC[:220],
    "has_read_text": ".read_text(" in _TLC,
    "filters_comment_lines": "startswith" in _TLC and "//" in _TLC,
    "gate_says": _gate_of.get("_tlc"),
    "probe_says": next((r["class"] for r in rows
                        if r["name"] == "_tlc"), None),
    "truth": "B_derived_text",
    "why_both_wrong": (
        "⭐⭐⭐⭐⭐ **门判 A 的理由是「赋值里有 `.read_text(`」** ⇒ "
        "**而 `_tlc` 读了文件之后又 `splitlines` + 过滤掉以 `//` `*` `/*` 开头的行** ⇒ "
        "**⇒ 它是「过滤后的文本」、不是原文** ⇒ ⇒ "
        "**⇒ 而探针判 C 的理由是「不满足 plain_read 的全部条件」⇒ "
        "**可它确实是从文件来的文本、只是被过滤过** ⇒ ⇒ "
        "**⇒ 两边都错、而错在同一个根上**："
        "**「文本里出现了某个模式」不等于「那件事发生了」** ⇒ ⇒ "
        "**⭐⭐⭐⭐⭐ **而这正是 996 P6 的同一个根** —— "
        "**995 那条是「名字在不在文件里」不等于「登记了没有」；"
        "这一条是「赋值里有 `.read_text(`」不等于「这就是原文」**"
    ),
}

out["P6_hold_997"] = bool(
    out["after_997"]["n_anchors"] > out["before_997"]["n_anchors"]
    and out["after_997"]["n_problems"] == 0)
out["zero_disagree_was_the_bad_state_997"] = (
    "⭐⭐⭐⭐⭐ **本批真的出现过「差集 = 0」的状态、而那是最坏的状态** —— "
    "**在把 `assignment_kinds` 从逐行正则换成 `ast.unparse` 之后、"
    "两边一度都判 `_tlc` 为 A、都错、差集归零** ⇒ ⇒ "
    "**⇒ 而那一刻的输出比现在好看得多** ⇒ ⇒ "
    "**⇒ 「两个尺子一致」是最容易骗人的证据类型** ⇒ ⇒ "
    "**⇒ 而根因是「两份实现抄了同一份判据」⇒ 「独立写的」这个前提本身就是假的**")
out["P7_hold_997"] = bool(
    out["disagree_997"] == ["_tlc"]
    and out["tlc_truth_997"]["gate_says"]
    == "A-可补登记(有一行普通 read_text)"
    and out["tlc_truth_997"]["probe_says"] == "B_derived_text"
    and out["tlc_truth_997"]["truth"] == "B_derived_text")
out["P5_hold_997"] = bool(
    out["after_997"]["n_anchors"] != out["before_997"]["n_anchors"]
    and out["after_997"]["n_skipped_anchors"]
    != out["before_997"]["n_skipped_anchors"])

out["P8_hold_997"] = bool(
    out["n_by_class_997"]["A_plain_readline"] == 0
    and BEFORE_CLASS_997["n_by_class"]["A_plain_readline"] == 1
    and out["n_disagree_997"] > 0)

out["verdicts_997"] = {
    "p1_one_plain_readline_997_": (
        "✅ **P1 成立：31 个里恰好 1 个是「有一行普通 `.read_text()` 读取」的** —— "
        "**而它就是 `_p870s`** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐⭐ **这是 961/962 那个坑的第三次** —— "
        "**而 961 补了 59 个、962 补了 1 个、两次都只补了 `_pNNN` 族** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐⭐ **⇒ 因为前两次的清单里也只有 `_pNNN` 族** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐⭐ **⇒ 所以这不是「又忘了一个」—— "
        "**是「按族的形状去补、而漏掉的那一族一直没人看」**"
    ),
    "p2_derived_outnumber_997_": (
        "⭐⭐⭐⭐⭐ **P2 成立、而它是本批的主要交付** —— "
        "**B 类（派生物）比 A 类多** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐⭐ **⇒ 「漏登记」这个说法对 B 类是错的** —— "
        "**它们不是漏登记、是 `PROBE_VARS`（名字 → 文件路径）"
        "**这张表的形状表达不了** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐⭐ **⇒ 而那张表是 961 建的、它的形状决定了它只能查「原文」** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐⭐ **⇒ 所以「31 个未登记」这个数字里、"
        "**真正的口径缺口是 A 类那 1 个、不是 31 个**"
    ),
    "p3_single_letter_names_997_": (
        "✅ **P3 成立：C 类里有纯循环变量** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐⭐ **⇒ 而单字母名出现在「未登记变量」清单里、"
        "**本身就在说「这个清单不是一个同质的集合」** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐ **⇒ 这与 995 那条「共 N 条不给检索词」是同族的、只是更狠：** "
        "**995 是同一件事被不同的词切开；这一条是同一张表里塞着三种不同的东西、"
        "而门把它们统称成「未登记」**"
    ),
    "p4_refuted_997_": (
        "❌ **P4 被否、而这个「否」是本批最有价值的读数** —— "
        "**把 A 类补登记进 `PROBE_VARS` 之后、官方门报的「问题」数仍然是 0** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐⭐ **⇒ 而 961 那次补完 59 个、立刻报出了问题；"
        "962 那次补完 1 个、整组 `XXXX.*` 一次都没被查过** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐⭐ **⇒ 两次都立刻有代价、而这次一点代价都没有** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐⭐ **⇒ 所以「假绿」的代价不是恒定的** —— "
        "**有的假绿当时恰好是对的、有的不是、而门不会告诉你哪一种** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐⭐ **⇒ 「未登记」是一个需要逐条查的怀疑、不是一个已确认的缺陷** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐⭐ **⇒ 而这条也否掉了「未登记 ⇒ 有问题」这个默认假设** —— "
        "**如果我按那个假设去写结论、这一批就会把「代价是 0」写成「代价未知」**"
    ),
    "p5_registration_moves_the_reading_997_": (
        "✅ **P5 成立：补登记会改变门的行为** ⇒ ⇒ "
        "**⇒ 锚点 5390 → 5416（+26）、跳过 169 → 143 条 / 31 → 29 个变量** ⇒ ⇒ "
        "**⇒ +26 正好是 `_p870s` 的 2 条 + `_aus936` 的 24 条** ⇒ ⇒ "
        "**⇒ 而这就是 996 P8「钉判据与量现状有先后顺序」的第二次施用** ⇒ ⇒ "
        "**⇒ 所以「补之前的读数」与「补之后的读数」必须都留着、不能只报后者** ⇒ ⇒ "
        "**⇒ 而 E 类（别名）给出的处置是「给它一个别名」、"
        "而不是「再读一遍文件」—— 那样零 IO**"
    ),
    "p6_not_a_noop_not_a_fix_997_": (
        "⚠️⭐⭐⭐⭐⭐ **P6 不是预测、是我盯着「问题仍然是 0」想起来的** —— "
        "**补登记既不是空动作、也不是「修好了」** ⇒ ⇒ "
        "**⇒ 它确实让 26 条锚点第一次被查（这是实打实的）** ⇒ ⇒ "
        "**⇒ 而它一次也没红（这也是实打实的）** ⇒ ⇒ "
        "**⇒ 而后者才是本批要说的：**"
        "**一条锚点「从来没被查过」与「查过且通过」在门的历史里长得一模一样** ⇒ ⇒ "
        "**⇒ 只有把「补之前」那个读数抄下来、这件事才看得见** ⇒ ⇒ "
        "**⇒ 而如果我先补登记、再跑门、只会看见一个 0**"
    ),
    "p7_two_rulers_disagree_997_": (
        "⚠️⭐⭐⭐⭐⭐ **P7 也不是预测 —— 是「两把尺子的差集」报出来的** ⇒ ⇒ "
        "**⇒ 而它的中间形态比现在的形态更吓人**："
        "**在把赋值提取从逐行正则换成 `ast.unparse` 之后、"
        "两边一度都把 `_tlc` 判成 A、都错、而差集归零** ⇒ ⇒ "
        "**⇒ 那一刻的输出比现在好看得多 —— 「两个尺子一致」** ⇒ ⇒ "
        "**⇒ ⭐⭐⭐⭐⭐ **⇒ 而根因是「两份实现抄了同一份判据」"
        "⇒ 「独立写的」这个前提本身就是假的** ⇒ ⇒ "
        "**⇒ 所以 996 P7「差集是唯一能发现新仪器变瞎的量」要加一条补充："
        "**判据相同时差集会归零、而那正是变瞎的信号** ⇒ ⇒ "
        "**⇒ 最终形态：门判 A（错）、探针判 B（对）** ⇒ ⇒ "
        "**⇒ 门判 A 的理由是「赋值里有 `.read_text(`」** ⇒ "
        "**而 `_tlc` 的赋值是「join 一个生成器」、那个生成器里是 "
        "`.read_text().splitlines()` 再按 `startswith` 过滤掉三种注释行** ⇒ ⇒ "
        "**⇒ 它同时是一个 comprehension + 一次过滤、所以它是 B** ⇒ ⇒ "
        "**⇒ 而探针的第三版把 A 的判据换成**结构**的（`is_plain_read` 看 AST 节点）"
        "⇒ 才判对** ⇒ ⇒ "
        "**⇒ 根因与 996 P6 同一个：「文本里出现了某个模式」"
        "**不等于「那件事发生了」**"
    ),
    "p8_zero_means_what_997_": (
        "⭐⭐⭐⭐⭐ **P8 也不是预测 —— 是我盯着补完之后那个「A 类 0」想起来的** ⇒ ⇒ "
        "**⇒ 「A 类是 0」与「A 类这一栏没有意义」在输出上完全一样** ⇒ ⇒ "
        "**⇒ 而真实原因只是「我刚把唯一那个补上了」** ⇒ ⇒ "
        "**⇒ 这是 996 P2「恒真的读数要认出它」的同一条、只是对象从一个数换成了一个类** ⇒ ⇒ "
        "**⇒ 而唯一能认出它的办法就是那句「补之前是 1」** ⇒ "
        "**⇒ 也就是说：P8 之所以能成立，恰恰是因为 before 被留下来了**"
    ),
    "offline_997": (
        "⭐⭐⭐⭐⭐ **本批纯离线**：不打开浏览器、不按任何键、**连 `mouse.click` 都没有**、"
        "**只读门与 verifier 的文本、再跑一次门** ⇒ ⇒ "
        "⭐⭐⭐⭐ **零计费是结构性的、不是自律的**"
    ),
}

out["discipline_997"] = "".join([
    "① ⭐⭐⭐⭐⭐ **一个总数在归类之前不是「一个口子的大小」** ⇒\n",
    "  ② ⭐⭐⭐⭐⭐ **门报的「未登记」可能混着三种不同的东西** ⇒\n",
    "  ③ ⭐⭐⭐⭐⭐ **补登记要挑「真能补的」—— "
    "**派生物不是漏登记、是表的形状表达不了** ⇒\n",
    "  ④ ⭐⭐⭐⭐⭐ **按族的形状去补、漏掉的那一族会一直没人看** ⇒\n",
    "  ⑤ ⭐⭐⭐⭐⭐ **用真的门当尺子、别用自己重写的尺子** ⇒\n",
    "  ⑥ ⭐⭐⭐⭐⭐ **改门之前与之后的读数都要记** ⇒\n",
    "  ⑦ ⭐⭐⭐⭐⭐ **两个尺子一致不算证据、除非能证明两份判据不同** ⇒\n",
    "  ⑧ ⭐⭐⭐⭐⭐ **判据要用结构（AST 节点）、不要用词** ⇒\n",
    "  ⑨ ⭐⭐⭐⭐⭐ **改共享大文件时「删掉一整块」是默认风险、"
    "**门是唯一检出手段** ⇒\n",
])

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)

print("before =", json.dumps(out["before_997"], ensure_ascii=False))
print("n_by_class =", json.dumps(out["n_by_class_997"], ensure_ascii=False))
print("A =", by["A_plain_readline"], "| C =", by["C_not_text"])
print("NC =", json.dumps({k: _nc[k] for k in
                          ("A_expect_plain_readline",
                           "B_no_readline_must_not_be_A",
                           "C_no_readline_must_not_be_A",
                           "D_expect_loop_var", "E_expect_alias")},
                         ensure_ascii=False))
print("disagree =", out["disagree_997"],
      "| tlc gate/probe/truth =", out["tlc_truth_997"]["gate_says"],
      out["tlc_truth_997"]["probe_says"], out["tlc_truth_997"]["truth"])
print("P1..P8 =", [out["P%d_hold_997" % i] for i in range(1, 9)],
      "NC =", out["NC_hold_997"])
print("PROBE_997_DONE ->", OUT)
