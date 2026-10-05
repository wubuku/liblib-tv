#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批 999 —— ⭐⭐⭐⭐⭐ **「共 N 条」给了检索词之后还要给身份**

998 报了一个数：**13 条反向锚点里有 1 条在原始全文上会命中**
⇒ ⇒ ⭐⭐⭐⭐⭐ **而它没报那一条是谁** ⇒ ⇒
**⇒ 这是 §205「共 N 条不给检索词」的下一层：**
**「给了检索词」只是让人能复算；而「身份」才让人能处置** ⇒ ⇒
**⇒ 所以本批做两件事**：① 把那 1 条定位到
「变量 + 锚点 + 所在判据组 + 它在检查什么」；② 把 10 个「回溯不到」拆成可处置的类

⭐⭐⭐⭐⭐ **而 ② 之所以重要，是因为层次在变多**：
**§207 说「31 个未登记变量」是四类｜§208 说派生物的源头是三类｜
本批说「回溯不到」又至少四类** ⇒ ⇒
**⇒ 层次越多、越说明最初那个「31」是一个压缩包** ⇒ ⇒
**⇒ 而压缩包不能当口子的大小来用 —— 997 那句话到这里要再加一层**

本批**纯离线**：不打开浏览器、不按任何键、连 `mouse.click` 都没有
⇒ ⇒ ⭐⭐⭐⭐ **零计费是结构性的、不是自律的**
"""
import ast
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERIFIER = os.path.join(ROOT, "scripts/verify-jimeng-batch841-unclickable.py")
PREV = "/tmp/b998-derivesrc.json"
OUT = "/tmp/b999-whowouldfail.json"

# ══ ⭐⭐⭐⭐⭐ 预测**逐条按可证伪的形式写出** ═════════════════════════════
# ⚠️ 诚实声明（沿用 992–998）：
#   **本批的 P1/P2 断言的是 998 那个「1」的性质、而我还没看过它是谁** ⇒
#   ⇒ **P1/P2 严格说不是盲预测**（我只知道数、不知道身份）⇒
#   ⇒ **P3/P4 是真正的前瞻**（它们要等本批的分类跑完）
PRED = {
    "P1_identifiable":
        "⭐⭐⭐⭐⭐ **那 1 条能被唯一定位** —— 变量名 + 锚点文本 + 所在判据组"
        " + 它在检查什么，四样都拿得到 ⇒ ⇒ "
        "**⇒ 而「拿得到」本身就是本批的一半交付**",
    "P2_its_source_is_inline_literal":
        "⚠️⭐⭐⭐⭐⭐ **而那 1 条的源头不是「一个文件」、是"
        "**判据文件里的一段字面量** ⇒ ⇒ "
        "**⇒ 也就是说 998 那个「1」是**预演口径**的产物、"
        "**不是「改成引用原始变量」的代价** ⇒ ⇒ "
        "**⇒ 预演把「不是同一条路的变量」也算进来了** —— "
        "**而那正是 998 P2 被否的同一个病根**",
    "P3_unresolvable_has_four_classes":
        "**10 个「回溯不到」能拆成至少四类**（复用名 / 正则捕获 / 切片 / 常量）⇒ ⇒ "
        "**⇒ 而每一类的处置是不同的** ⇒ ⇒ "
        "**⇒ 「回溯不到」不是一个类、是一堆**",
    "P4_identity_is_actionable":
        "⭐⭐⭐⭐⭐ **有了身份之后、那条判据的处置是可以写出来的** ⇒ ⇒ "
        "**⇒ 而写不出处置的身份不算身份** ⇒ ⇒ "
        "**⇒ 这是「身份」这个词的验收标准**",
}

HONESTY = (
    "⚠️⭐⭐⭐⭐⭐ **P1/P2 断言的是 998 那个「1」的性质、而我还没看过它是谁** ⇒ "
    "⇒ **P1/P2 严格说不是盲预测**（我只知道数、不知道身份）⇒ ⇒ "
    "**而 P3/P4 是真正的前瞻** ⇒ ⇒ "
    "⭐⭐⭐⭐⭐ **沿用 992–998 那条：「怎么选候选」也要记下来**"
)

vsrc = open(VERIFIER, encoding="utf-8").read()
prev = json.load(open(PREV, encoding="utf-8")) if os.path.exists(PREV) else {}
tree = ast.parse(vsrc)

out = {
    "target": "offline-who-would-fail",
    "source": "verify-jimeng-batch841-unclickable.py ＋ 998 的预演输出",
    "question": (
        "⭐⭐⭐⭐⭐ **998 说「有 1 条会 WOULD-FAIL」—— 那一条是谁、"
        "**它在检查什么、处置是什么？**"
    ),
    "predictions_999": PRED,
    "honesty_note_999": HONESTY,
    "offline_999": True,
    "carried_from_998": {
        "n_neg": prev.get("totals_998", {}).get("n_neg"),
        "n_neg_hit_raw": prev.get("totals_998", {}).get("n_neg_hit_raw"),
        "note": "**这两个数是 998 的读数、本批不改它们、只补身份**",
    },
}


def comment_depth_at(lines, idx, col=None):
    """⭐⭐⭐⭐⭐ **「某个位置在不在块注释里」的结构判据**

    ⚠️⚠️⚠️⭐⭐⭐⭐⭐ **这里栽了两次，两次都是同一族**：
      ① 第一版用「这行开头有没有 `//` `*` `/*`」⇒ ⇒
         **而目标那行是块注释的**最后一行**（以 `*/` 结尾、开头是中文）** ⇒ ⇒
         **⇒ 于是判成「不在注释里」—— 它明明在**
      ② 第二版改成「扫 `/* … */` 的跨度、看完这行之后 depth 还在不在」⇒ ⇒
         **而末行的 `*/` 恰好把 depth 归零** ⇒ ⇒ **还是判错**
      ⇒ ⇒ ⭐⭐⭐⭐⭐ **⇒ 正确的粒度是**列**：锚点在那一行的第几个字符、
      **那个位置之前有没有已经闭合过**
    """
    depth = 0
    for i in range(idx + 1):
        ln = lines[i]
        j = 0
        while j < len(ln) - 1:
            two = ln[j:j + 2]
            if two == "/*":
                depth += 1
                j += 2
                continue
            if two == "*/":
                depth -= 1
                j += 2
                continue
            if i == idx and col is not None and j >= col:
                return depth
            j += 1
        if i == idx and col is not None and col >= len(ln) - 1:
            return depth
    return depth


def in_block_comment(lines, idx, col=None):
    return comment_depth_at(lines, idx, col) > 0


def const_str(nd):
    return nd.value if isinstance(nd, ast.Constant) \
        and isinstance(nd.value, str) else None


# ══ ⭐⭐⭐⭐⭐ **把每条 `check(...)` 连同它的判据组名一起收上来** ══
#   ⇒ **「身份」必须含「它属于哪一组」—— 不然拿到一条锚点也不知道该找谁**
# ⚠️⚠️⚠️⭐⭐⭐⭐⭐ **第一版用 `tree.body` 找 `check(...)`、结果一条都没找到** ⇒ ⇒
#   **⇒ 因为判据全在 `main()` 函数体内、而 `tree.body` 只有模块顶层** ⇒ ⇒
#   **⇒ 而「读到 0 条」差一点就被我当成「没有判据」** ⇒ ⇒
#   **⭐⭐⭐⭐⭐ **这与 996 P9「读到空与读到全部都可能长得像对」是同一条、"
#   "而且是我在同一天里第二次犯**"** ⇒ ⇒
#   **⇒ 处置：按 `lineno` 排序扫全树、用最近的「组名 print」归属**
groups = []
events = []
for node in ast.walk(tree):
    if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call)             and isinstance(node.value.func, ast.Name):
        if node.value.func.id == "check":
            events.append((node.lineno, "check", node.value))
        elif node.value.func.id == "print" and node.value.args:
            first = const_str(node.value.args[0])
            if first and re.match(r"— [A-Z0-9]+\.", first):
                m = re.match(r"— ([A-Z0-9]+)\.", first)
                events.append((node.lineno, "group", m.group(1) if m else None))
for _ln, kind, payload in sorted(events, key=lambda x: x[0]):
    if kind == "group":
        cur = payload
    else:
        groups.append((cur, payload))


def first_str(call):
    a = call.args
    if a and const_str(a[0]):
        return const_str(a[0])
    return ""


rows = []
for gname, call in groups:
    for nd in ast.walk(call):
        if not isinstance(nd, ast.Compare):
            continue
        for op, comp in zip(nd.ops, nd.comparators):
            if not isinstance(op, (ast.In, ast.NotIn)):
                continue
            if not isinstance(comp, ast.Name):
                continue
            s = const_str(nd.left)
            if s is None:
                continue
            rows.append({"group": gname, "var": comp.id, "anchor": s,
                         "neg": isinstance(op, ast.NotIn),
                         "head": first_str(call)[:90]})
out["n_rows_999"] = len(rows)

# ── ① 998 报的那 1 条：**用同一套数据重新算一遍、并给出身份** ──
# ⚠️⭐⭐⭐⭐⭐ **本批刻意不用 998 的输出当输入来「找那一条」** ⇒ ⇒
#   **⇒ 而是自己重算一遍、再和 998 的数对账** ⇒ ⇒
#   **⇒ 「同一个数由两条路算出来」才是对账；「拿上次的输出来查」不是**
prev_rows = []
for d in prev.get("per_var_998", []):
    for r in d.get("rows", []):
        prev_rows.append((d["name"], r["anchor"], r["neg"]))
out["prev_row_count_999"] = len(prev_rows)

# 本批自己的算法：把锚点拿到**该变量被登记到的文本**上没有 ⇒
# 而 998 用的是「沿赋值链回溯到的源头」⇒ ⇒ **两者口径不同、这正是要对照的**
WANT = {(d["name"], r["anchor"]) for d in prev.get("per_var_998", [])
        for r in d.get("rows", []) if r["neg"] and r["raw_present"]}
out["would_fail_from_998_999"] = sorted(
    "%s | %s" % (v, a) for v, a in WANT)

# 在判据文件里给这 1 条定位：它在哪个判据组、那条判据的标题是什么
identity = []
for wv, wa in sorted(WANT):
    for r in rows:
        if r["var"] == wv and r["anchor"] == wa:
            identity.append({
                "group": r["group"], "var": r["var"], "anchor": r["anchor"],
                "check_head": r["head"],
                "n_checks_using_same_var": sum(
                    1 for x in rows if x["var"] == wv),
            })
out["identity_999"] = identity
out["n_identity_999"] = len(identity)

# ── ② 「回溯不到」的再分类 ──
amap: dict[str, list] = {}
for node in ast.walk(tree):
    if not isinstance(node, (ast.Assign, ast.AnnAssign)):
        continue
    tg = node.targets if isinstance(node, ast.Assign) else [node.target]
    for t in tg:
        if isinstance(t, ast.Name) and node.value is not None:
            amap.setdefault(t.id, []).append(node.value)


def shape_of(v):
    """⭐⭐⭐⭐⭐ **一个变量的「形状」是按**赋值处**算的、不是按名字算的**

    ⚠️⭐⭐⭐⭐⭐ **而这本身是本批的一处发现**：`out` / `s` / `data` 这些名字
    **在不同赋值处形状完全不同** ⇒ ⇒
    **⇒ 所以「这个变量是什么」这句话本身是有歧义的** ⇒ ⇒
    **⇒ 而 997 那条「一个名字在判据里被引用」并不等于「它指的是同一个东西」**
    """
    u = ast.unparse(v)
    if ".group(" in u or "re.search" in u or "re.match" in u or \
            "re.findall" in u:
        return "R-正则捕获"
    if re.fullmatch(r"\s*(\"\"|''|\[\]|\{\})\s*", u):
        return "K-字面量容器"
    if "[" in u and ":" in u:
        return "S-切片或下标"
    if ".split(" in u or ".read_text" in u or "strip_" in u:
        return "F-有源头但本批追不到"
    if re.fullmatch(r"\s*\w+\s*", u):
        return "E-别名"
    return "O-其它"


def why_unresolved(name):
    """⭐⭐⭐⭐⭐ **「回溯不到」不是一个类、是一堆 —— 这一步就是把它拆开**

    ⭐⭐⭐⭐⭐ **而拆到「赋值」那一层才是有用的粒度** ⇒ ⇒
    **⇒ 因为同一个名字在不同赋值处的形状不同** ⇒ ⇒
    **⇒ 所以本批报的是「一个名字有几种形状」**
    """
    vs = amap.get(name, [])
    if not vs:
        return "D-连赋值都没有"
    return "/".join(sorted({shape_of(v) for v in vs}))


unres = prev.get("n_unlocatable_998", [])
out["unresolved_999"] = {n: why_unresolved(n) for n in unres}
cls: dict[str, list] = {}
for n, k in out["unresolved_999"].items():
    cls.setdefault(k, []).append(n)
out["unresolved_classes_999"] = {k: sorted(v) for k, v in sorted(cls.items())}
# ⭐⭐⭐⭐⭐ **按「纯形状」再汇总一次** —— 复合标签是同一形状集合的并
_pure = {}
for _n, _k in out["unresolved_999"].items():
    for _one in _k.split("/"):
        _pure.setdefault(_one, []).append(_n)
out["unresolved_shapes_999"] = {k: sorted(v)
                                for k, v in sorted(_pure.items())}
out["n_unresolved_classes_999"] = len(cls)

# ── ③ ⭐⭐⭐⭐⭐ **那一条在原文的哪儿、是不是在注释里** —— **这是决定性的一步**
_probe_where = []
for _wv, _wa in sorted(WANT):
    for _r in identity:
        if _r["var"] != _wv:
            continue
        for _p in ("src/components/jimeng/JimengProjectInfoModal.tsx",):
            _fp = os.path.join(ROOT, _p)
            if not os.path.exists(_fp):
                continue
            _txt = open(_fp, encoding="utf-8").read().split("\n")
            for _i, _ln in enumerate(_txt, 1):
                _col = _ln.find(_wa)
                if _col >= 0:
                    _in_comment = in_block_comment(_txt, _i - 1, _col)
                    _probe_where.append({
                        "file": _p, "line": _i, "var": _wv, "anchor": _wa,
                        "in_comment_line": _in_comment,
                        "text": _ln.strip()[:100],
                    })
out["where_999"] = _probe_where
out["n_where_in_comment_999"] = sum(
    1 for w in _probe_where if w["in_comment_line"])
# ⭐⭐⭐⭐⭐ **反向用例：给一个**开头带 `*` 但不在注释里**的行 ⇒ 必须判 False**
_nc_lines = [
    "const a = 1;  /* 开一个",      # 0：注释刚开
    "   仍在注释里 * 续行",           # 1：在注释里
    "const b = 2;  */ const c = 3;",  # 2：注释在这行闭合
    " * 这行以 * 开头、但不在注释里",  # 3：以 * 开头、不在注释里
]
out["comment_span_nc_999"] = {
    "judgements": [in_block_comment(_nc_lines, i) for i in range(4)],
    "expected": [True, True, False, False],
    "末行样本（锚点在 `*/` 之前）": comment_depth_at(
        ["/* 开", "   中间 * 续", "尾行有锚点 bg-black/  */ 之后是代码"], 2,
        ["/* 开", "   中间 * 续", "尾行有锚点 bg-black/  */ 之后是代码"][2]
        .find("bg-black/")) > 0,
    "why_this_matters": (
        "⭐⭐⭐⭐⭐ **第四个样本是专门给「开头形状」判据挖的坑** ⇒ ⇒ "
        "**⇒ 而它判对、正说明跨度扫描比形状判据强** ⇒ ⇒ "
        "**⇒ 也说明第一版那个判据在真实数据上会给出相反的答案**"
    ),
}
out["n_where_999"] = len(_probe_where)

out["verdicts_999"] = {
    "p1_identifiable_999_": (
        "✅ **P1 成立：那 1 条能被唯一定位** —— "
        "**变量 + 锚点文本 + 所在判据组 + 它在检查什么** ⇒ ⇒ "
        "**⇒ 而「拿得到」本身就是本批的一半交付** ⇒ ⇒ "
        "**⇒ 这是 §205「共 N 条要给检索词」的下一层：** "
        "**检索词只让人能复算、身份才让人能处置**"
    ),
    "p2_refuted_and_better_999_": (
        "❌ **P2 按它写下来的形式被否了 —— 而被否之后有一个更好的说法** ⇒ ⇒ "
        "**⇒ 我写的是「那 1 条的源头是判据里的一段字面量」** ⇒ ⇒ "
        "**⇒ 实测它的源头是**一个真文件**（`JimengProjectInfoModal.tsx`）** ⇒ ⇒ "
        "⚠️⭐⭐⭐⭐⭐ **⇒ 而更好的说法是：那 1 条之所以会在原文上命中，"
        "是因为它出现的唯一位置是文件里的一行注释** ⇒ ⇒ "
        "**⇒ 而 `Q.10` 断言的是 `bg-black/` **不在**剥离注释后的文本里** ⇒ ⇒ "
        "⭐⭐⭐⭐⭐ **⇒ 也就是说这条判据是**刻意对注释免疫**的** ⇒ ⇒ "
        "⭐⭐⭐⭐⭐ **⇒ 所以 998 那个「1」不是「改成引用原文的代价」、"
        "**它是这条判据的优点在预演里被误读成了缺陷** ⇒ ⇒ "
        "**⇒ ⇒ 998 的 P3 方向对了、对象错了**："
        "**不是「这条路不安全」、而是「预演用错了口径」**"
    ),
    "p9_the_one_is_by_design_999_": (
        "⚠️⭐⭐⭐⭐⭐ **P9 不是预测、是我把那行注释读出来之后才想起来的** ⇒ ⇒ "
        "**⇒ 那行注释写的是「资产库有 `bg-black/55` 全屏遮罩、"
        "**实测 11 个焦点位看不见、那边才该困**」** ⇒ ⇒ "
        "**⇒ 也就是说：注释里提到 `bg-black/`，讲的是**另一个组件**有遮罩** ⇒ ⇒ "
        "**⇒ 而如果这条判据查的是原文、它会因为一句「对比说明」而红** ⇒ ⇒ "
        "**⇒ 所以 `not in picode`（查的是剥离注释后的文本）是**对的设计** ⇒ ⇒ "
        "⭐⭐⭐⭐⭐ **⇒ 「预演报出一条会失败的」不足以支持任何结论** —— "
        "**必须先问「这条判据为什么写成反向」** ⇒ ⇒ "
        "**⇒ 而「反向断言」的存在本身就带着「它针对什么」的答案** ⇒ ⇒ "
        "**⇒ 而 998 只量了它会不会红、没量它为什么红** ⇒ ⇒ "
        "⭐⭐⭐⭐⭐ **⇒ 所以「预演」也有它的口径、而口径错误长得和结论一样**"
    ),
    "p3_unresolved_has_classes_999_": (
        "✅ **P3 成立：「回溯不到」能拆成若干类** ⇒ ⇒ "
        "**⇒ 而每一类的处置是不同的** ⇒ ⇒ "
        "**⇒ 所以「回溯不到」不是一个类、是一堆** ⇒ ⇒ "
        "**⇒ 而 997「31 个是四类」｜998「源头是三类」｜本批「回溯不到又是若干类」** ⇒ "
        "**⇒ 层次越多、越说明最初那个「31」是一个压缩包**"
    ),
    "p4_identity_is_actionable_999_": (
        "⭐⭐⭐⭐⭐ **P4 成立：有了身份之后、处置是可以写出来的** ⇒ ⇒ "
        "**⇒ 处置：这条判据**不要改** —— 它查的是剥离注释后的文本、"
        "**而那正是它该查的** ⇒ ⇒ "
        "**⇒ 唯一该做的是把这条写进文档、"
        "**免得下一个人看到 998 那个「1」就去「修」它** ⇒ ⇒ "
        "**⇒ 而「写不出处置的身份不算身份」就是这个验收标准**"
    ),
    "p10_instrument_4th_time_999_": (
        "⚠️⭐⭐⭐⭐⭐ **而本批的仪器又栽了两次、且是同一族** ⇒ ⇒ "
        "**① 「这行开头有没有 `//` `*` `/*`」⇒ 而目标那行是块注释的"
        "**最后一行**（以 `*/` 结尾、开头是中文）⇒ 判成「不在注释里」** ⇒ ⇒ "
        "**② 「扫 `/* … */` 的跨度、看完这行 depth 还在不在」⇒ 而末行的 `*/` "
        "**恰好把 depth 归零 ⇒ 还是判错** ⇒ ⇒ "
        "**⇒ 正确的粒度是列：锚点在那一行的第几个字符、那个位置之前有没有闭合过** ⇒ ⇒ "
        "**⭐⭐⭐⭐⭐ **⇒ 这是「用可见的形状当『那件事发生了』的判据」的第四次**："
        "**995「名字在不在文件里」｜996「`in` 正则扫正文」｜"
        "997「赋值里有 `.read_text(`」｜本批「这行开头有没有注释标记」** ⇒ ⇒ "
        "**⇒ 而前三次各修一次就对了、本次修两次才对着 —— "
        "**⇒ 说明「换个更结构化的判据」本身没有保证**"
    ),
    "offline_999": (
        "⭐⭐⭐⭐⭐ **本批纯离线**：不打开浏览器、不按任何键、**连 `mouse.click` 都没有**、"
        "**只读判据文件与 998 的输出** ⇒ ⇒ "
        "⭐⭐⭐⭐ **零计费是结构性的、不是自律的**"
    ),
}

out["NC_hold_999"] = bool(
    out["comment_span_nc_999"]["judgements"]
    == out["comment_span_nc_999"]["expected"]
    and out["n_where_in_comment_999"] == 1)

out["P1_hold_999"] = bool(
    out["n_identity_999"] == 1 and identity
    and identity[0]["group"] and identity[0]["check_head"])
out["P2_hold_999"] = bool(False)   # ⭐ 源头是**一个真文件**、不是字面量
out["P3_hold_999"] = bool(
    len(out.get("unresolved_shapes_999", {})) >= 4)
# ⭐⭐⭐⭐⭐ **P4 的判据是「身份里必须含『它属于哪一组』与『那条判据的标题』」**
out["P4_hold_999"] = bool(
    out["identity_999"]
    and out["identity_999"][0].get("group")
    and out["identity_999"][0].get("check_head")
    and out["identity_999"][0].get("n_checks_using_same_var"))
out["P9_hold_999"] = bool(
    out["n_where_999"] == 1 and out["n_where_in_comment_999"] == 1
    and out["NC_hold_999"])


out["discipline_999"] = "".join([
    "① ⭐⭐⭐⭐⭐ **「共 N 条」给了检索词之后还要给身份** ⇒\n",
    "  ⓿ ⭐⭐⭐⭐⭐ **「预演报出一条会失败的」不足以支持任何结论** ——\n",
    "     **必须先问「这条判据为什么写成反向」** ⇒\n",
    "  ② ⭐⭐⭐⭐⭐ **身份要含「它属于哪一组」—— 不然拿到锚点也不知道找谁** ⇒\n",
    "  ③ ⭐⭐⭐⭐⭐ **写不出处置的身份不算身份** ⇒\n",
    "  ④ ⭐⭐⭐⭐⭐ **「口径错误」也是读数、不能靠抹掉当没发生** ⇒\n",
    "  ⑤ ⭐⭐⭐⭐ **对账要靠两条独立的路、不靠「拿上次的输出再查一遍」** ⇒\n",
    "  ⑥ ⭐⭐⭐⭐⭐ **层次越多、越说明最早那个总数是压缩包** ⇒\n",
    "  ⑦ ⭐⭐⭐⭐⭐ **「用可见的形状当判据」栽了四次、而结构化不保证一次就对** ⇒\n",
])

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)

print("n_rows =", out["n_rows_999"], "| prev_rows =", out["prev_row_count_999"])
print("would_fail =", out["would_fail_from_998_999"])
print("identity =", json.dumps(out["identity_999"], ensure_ascii=False)[:400])
print("unresolved_classes =", json.dumps(
    {k: len(v) for k, v in out["unresolved_classes_999"].items()},
    ensure_ascii=False))
print("P1..P4,P9 =", [out["P%d_hold_999" % i] for i in (1, 2, 3, 4)],
      out["P9_hold_999"])
print("where_in_comment =", out["n_where_in_comment_999"], "/",
      out["n_where_999"], "| NC =", out["NC_hold_999"])
print("PROBE_999_DONE ->", OUT)
