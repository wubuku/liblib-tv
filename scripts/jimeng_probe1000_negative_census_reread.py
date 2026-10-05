#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批 1000 —— ⭐⭐⭐⭐⭐ **把「反向断言」普查一遍：它们各自在防什么**

999 撞到的一件事：**「反向断言」的存在本身就带着「它针对什么」的答案**
⇒ ⇒ 具体那一条是：`Q.10` 断言 `bg-black/` **不在剥离注释后的文本里**、
而它在原文里只出现在一行注释中 ⇒ ⇒ **所以那条判据是刻意对注释免疫的**

⭐⭐⭐⭐⭐ **而那立刻引出一个可枚举的问题**：
**全仓一共多少条反向断言、它们各自在防什么、"
"而「对注释免疫」是一条孤例还是一个模式？**

⇒ ⇒ ⭐⭐⭐⭐⭐ **本批把 230 条反向锚点逐条归类**，并回答那个模式问题
⇒ ⇒ ⭐⭐⭐⭐⭐ **而「逐条归类」这件事本身是 999 那条的推广**：
**「共 N 条」→ 给了检索词 → 还要给身份 → 还要给「它在防什么」**

本批**纯离线**：不打开浏览器、不按任何键、连 `mouse.click` 都没有
⇒ ⇒ ⭐⭐⭐⭐ **零计费是结构性的、不是自律的**
"""
import ast
import collections
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERIFIER = os.path.join(ROOT, "scripts/verify-jimeng-batch841-unclickable.py")
GATE = os.path.join(ROOT, "scripts/jimeng_check_verifier_anchors.py")
OUT = "/tmp/b1000-negative-census.json"

# ══ ⭐⭐⭐⭐⭐ 预测**逐条按可证伪的形式写出** ═════════════════════════════
# ⚠️ 诚实声明（沿用 992–999）：
#   **写判据前我只看过「正 5573 / 反 230」这两个总数和 6 条样例** ⇒
#   ⇒ **P2/P3 严格说不是盲预测**（我看过样例、样例里有 `bg-black/` 那一类）⇒
#   ⇒ **而 P1/P4/P5 是真正的前瞻**
PRED = {
    "P1_ratio_is_an_order_of_magnitude":
        "**反向锚点的数量比正向少一个量级**（约 1:24）⇒ ⇒ "
        "**⇒ 而这与「反向断言是逐条刻意加的」是一致的** ⇒ ⇒ "
        "**⇒ 反过来说：一个只有 1:24 的类别、不可能靠「顺手」维持**",
    "P2_most_negatives_are_on_stripped_text":
        "⭐⭐⭐⭐⭐ **反向锚点里挂在「剥离注释后的文本」上的占多数** ⇒ ⇒ "
        "**⇒ 所以「对注释免疫」不是 999 的孤例、是一个模式** ⇒ ⇒ "
        "**⇒ 而这个模式的成因是：判据要钉的是「代码在做什么」、"
        "**不是「文档在说什么」**",
    "P3_two_families":
        "⭐⭐⭐⭐⭐ **反向锚点分成两族**："
        "**一类是「某句自我怀疑 / 某个被否掉的结论不许被写回肯定句」；"
        "另一类是「某个具体字符串不许出现在代码里」** ⇒ ⇒ "
        "**⇒ 而两族的正确读法不同**：前一族防的是**叙述漂移**、后一族防的是**实现回退**",
    "P4_some_negative_anchors_are_themselves_readings":
        "⭐⭐⭐⭐ **有反向锚点的锚点文本是「读数」而不是「禁令」** ⇒ ⇒ "
        "**⇒ 而这类锚点一旦被改写、门不会红** ⇒ ⇒ "
        "**⇒ 因为 `X not in Y` 对「X 变了」没有任何约束**",
    "P5_group_concentration":
        "**反向锚点在少数几个判据组里高度集中** ⇒ ⇒ "
        "**⇒ 而集中意味着「这几组是专门做反向核对的」** ⇒ ⇒ "
        "**⇒ 那就不该把它们当成「零散的例外」来读**",
}

HONESTY = (
    "⚠️⭐⭐⭐⭐⭐ **写判据前我只看过「正 5573 / 反 230」这两个总数和 6 条样例** ⇒ "
    "⇒ **P2/P3 严格说不是盲预测**（样例里就有 `bg-black/` 那一类）⇒ ⇒ "
    "**而 P1/P4/P5 是真正的前瞻** ⇒ ⇒ "
    "⭐⭐⭐⭐⭐ **沿用 992–999 那条：「怎么选候选」也要记下来**"
)

DERIVERS = ("strip_comments", "strip_py_comments", "strip_js_comments")


def cs(n):
    return n.value if isinstance(n, ast.Constant) \
        and isinstance(n.value, str) else None


vsrc = open(VERIFIER, encoding="utf-8").read()
gsrc = open(GATE, encoding="utf-8").read()
tree = ast.parse(vsrc)
PROBE_VARS = set(re.findall(r'"(_p\d{3}[a-z]?)"\s*:\s*"scripts/', gsrc)) \
    | {"_ausrc"}

out = {
    "target": "offline-negative-anchor-census",
    "source": "verify-jimeng-batch841-unclickable.py ＋ "
              "jimeng_check_verifier_anchors.py",
    "question": (
        "⭐⭐⭐⭐⭐ **全仓 230 条反向断言各自在防什么？"
        "**⇒ 而「对注释免疫」是 999 的孤例还是一个模式？**"
    ),
    "predictions_1000": PRED,
    "honesty_note_1000": HONESTY,
    "offline_1000": True,
}

# ── 变量 → 它被检查的文本是不是「剥离注释后的」 ──
amap: dict[str, list] = {}
for node in ast.walk(tree):
    if not isinstance(node, (ast.Assign, ast.AnnAssign)):
        continue
    tg = node.targets if isinstance(node, ast.Assign) else [node.target]
    for t in tg:
        if isinstance(t, ast.Name) and node.value is not None:
            amap.setdefault(t.id, []).append(node.value)


def is_stripped(name, depth=0):
    """⭐⭐⭐⭐⭐ **「这条反向断言查的是不是剥离注释后的文本」**

    ⚠️⭐⭐⭐⭐⭐ **判据是「赋值链上有没有 `strip_*`」** ⇒ ⇒
    **⇒ 而这又是「文本里出现某个模式」当判据 —— 但这一处是**有理由**的**：
    **被检查的文本本身就是那个函数调用的产物、而不是一段散文** ⇒ ⇒
    **⇒ 与 995/996/997/999 那四次的区别正在于此：那四次检查的是"
    "「某件事发生了没有」、而这一处检查的是「这个对象是什么」**"
    """
    if depth > 6:
        return None
    vs = amap.get(name, [])
    if not vs:
        return None
    hits = []
    for v in vs:
        u = ast.unparse(v)
        if any(d in u for d in DERIVERS):
            hits.append(True)
        elif re.fullmatch(r"\s*\w+\s*", u):
            hits.append(is_stripped(u.strip(), depth + 1))
        elif isinstance(v, ast.Call) and isinstance(v.func, ast.Attribute) \
                and v.func.attr == "read_text" \
                and isinstance(v.func.value, ast.Name):
            hits.append(False)
        elif isinstance(v, ast.IfExp):
            # ⚠️⚠️⚠️⭐⭐⭐⭐⭐ **第一版我把 `unparse(body)` 当变量名传下去了**
            #   ⇒ `amap.get("q.read_text(...)")` 永远是空 ⇒ **返回 None**
            #   ⇒ 而 None 被我归进 "unknown" ⇒ **118/206 是「仪器没跑起来」**
            #   ⇒ **⇒ 而「unknown 一半以上」不是数据如此、是这个分支坏了**
            _b = v.body
            _target = None
            if isinstance(_b, ast.Call) and isinstance(_b.func, ast.Attribute) \
                    and _b.func.attr == "read_text" \
                    and isinstance(_b.func.value, ast.Name):
                _target = _b.func.value.id
            hits.append(is_stripped(_target, depth + 1)
                        if _target else False)
        else:
            hits.append(False)
    hits = [h for h in hits if h is not None]
    if not hits:
        return None
    return all(hits)


# ── 逐条收（变量, 锚点, 是否反向, 判据组, 判据标题） ──
events = []
for node in ast.walk(tree):
    if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call) \
            and isinstance(node.value.func, ast.Name):
        if node.value.func.id == "check":
            events.append((node.lineno, "c", node.value))
        elif node.value.func.id == "print" and node.value.args:
            f = cs(node.value.args[0])
            if f and re.match(r"— [A-Z0-9]+\.", f):
                m = re.match(r"— ([A-Z0-9]+)\.", f)
                events.append((node.lineno, "g",
                               m.group(1) if m else None))
cur = None
pos_rows, neg_rows = [], []
for _ln, kind, pl in sorted(events, key=lambda x: x[0]):
    if kind == "g":
        cur = pl
        continue
    call = pl
    head = cs(call.args[0]) if call.args else ""
    for nd in ast.walk(call):
        if not isinstance(nd, ast.Compare):
            continue
        for op, comp in zip(nd.ops, nd.comparators):
            if not isinstance(op, (ast.In, ast.NotIn)) \
                    or not isinstance(comp, ast.Name):
                continue
            s = cs(nd.left)
            if s is None:
                continue
            row = {"group": cur, "var": comp.id, "anchor": s,
                   "head": head}
            (neg_rows if isinstance(op, ast.NotIn) else pos_rows).append(row)

out["n_pos_1000"] = len(pos_rows)
out["n_neg_1000"] = len(neg_rows)
out["ratio_1000"] = round(len(pos_rows) / max(1, len(neg_rows)), 2)

reg = [r for r in neg_rows if r["var"] in PROBE_VARS]
out["n_neg_registered_1000"] = len(reg)
out["n_neg_unregistered_1000"] = len(neg_rows) - len(reg)


# ── ⭐⭐⭐⭐⭐ **模式问题：这些反向断言查的是不是剥离注释后的文本** ──
textkind = collections.Counter()
for r in reg:
    textkind[("stripped" if is_stripped(r["var"]) is True
              else "raw" if is_stripped(r["var"]) is False
              else "unknown")] += 1
out["neg_textkind_1000"] = dict(textkind)
out["n_stripped_1000"] = textkind.get("stripped", 0)

# ── ⭐⭐⭐⭐⭐ **两族分类** ──
# ⚠️⚠️⚠️⭐⭐⭐⭐⭐ **第一版的两族分类是按关键词切的、而它失败了** ⇒ ⇒
#   **⇒ F3 吃掉了 193/206（94%）** ⇒ ⇒
#   **⇒ 94% 落在「其它」不是「数据没有结构」、是「我这套关键词选错了」** ⇒ ⇒
#   **⭐⭐⭐⭐⭐ **⇒ 这正是 §205 那条「分类的第一步是『这句话在做什么』、"
#   "不是『它属于哪个关键词』」—— 而我又在按关键词分** ⇒ ⇒
#   **⇒ 第二版改按**结构**分：锚点长什么样、而不是它说了什么**
CODE_PUNCT = re.compile(r"[()\[\]=;.{}<>!+\-*/|&]")
CJK = re.compile(r"[\u4e00-\u9fff]")


def family(r):
    """⭐⭐⭐⭐⭐ **按结构分族 —— 「锚点长什么样」而不是「它说了什么」**"""
    a = r["anchor"].strip()
    n_code = len(CODE_PUNCT.findall(a))
    has_cjk = bool(CJK.search(a))
    if has_cjk and n_code == 0:
        return "W-中文散文片段（防某句措辞被写回去）"
    if n_code >= 2:
        return "K-代码片段（防某个实现被引入）"
    if n_code == 1 and not has_cjk:
        return "K-代码片段（防某个实现被引入）"
    if not has_cjk and re.fullmatch(r"[\w$/:.-]+", a):
        return "I-标识符或路径（防某个名字被引入）"
    return "O-其它"


for r in reg:
    r["family"] = family(r)
    r["textkind"] = ("stripped" if is_stripped(r["var"]) is True
                     else "raw" if is_stripped(r["var"]) is False
                     else "unknown")
fam = collections.Counter(r["family"] for r in reg)
out["neg_families_1000"] = dict(fam)
out["anchor_len_median_1000"] = sorted(len(r["anchor"]) for r in reg)[
    len(reg) // 2]
out["n_anchor_le_20_1000"] = sum(1 for r in reg if len(r["anchor"]) <= 20)
out["neg_rows_1000"] = reg
out["sample_by_family_1000"] = {
    k: [r["anchor"][:70] for r in reg if r["family"] == k][:6]
    for k in sorted(fam)
}

# ── 族 × 文本形状 的交叉表（本批的主要读数） ──
cross = collections.Counter((r["family"], r["textkind"]) for r in reg)
out["family_x_textkind_1000"] = {f"{a}｜{b}": c
                                 for (a, b), c in sorted(cross.items())}

# ── ⭐⭐⭐⭐ **P4：有些反向锚点的锚点文本是「读数」而不是「禁令」** ──
READING_PAT = re.compile(r"==|≥|≤|\d|恒为|永远|恒")
readings = [r for r in reg if READING_PAT.search(r["anchor"])]
out["n_neg_anchor_is_a_reading_1000"] = len(readings)
out["neg_reading_samples_1000"] = [r["anchor"][:70] for r in readings][:8]

# ── P5：按判据组集中度 ──
grp = collections.Counter(r["group"] for r in reg)
out["neg_by_group_1000"] = dict(grp.most_common())
out["n_groups_with_negatives_1000"] = len(grp)
out["top3_share_1000"] = round(
    sum(c for _g, c in grp.most_common(3)) / max(1, len(reg)), 3)

_F = out["neg_families_1000"]
_cov = 1 - _F.get("O-其它", 0) / max(1, len(reg))
out["P1_hold_1000"] = bool(20 <= out["ratio_1000"] <= 30)
out["P2_hold_1000"] = bool(out["n_stripped_1000"] > len(reg) // 2)
out["P3_hold_1000"] = bool(
    _F.get("F1-防叙述漂移（某句自我怀疑 / 某个被否掉的结论）", 0) + _F.get(
        "F2-防实现回退（某个具体字符串不许出现）", 0) > len(reg) // 2)
out["P4_hold_1000"] = bool(
    out["n_neg_anchor_is_a_reading_1000"] > len(reg) // 2)
out["P5_hold_1000"] = bool(out["top3_share_1000"] > 0.6)
out["family_coverage_1000"] = round(_cov, 3)

# ══ ⭐⭐⭐⭐⭐ **反向用例：证明 `is_stripped()` 能返回 True** ══
# ⚠️⚠️⚠️⭐⭐⭐⭐⭐ **「206 条全是 raw」这个读数有一个致命的风险**：
#   **如果 `is_stripped()` 永远不返回 True、那这个 0 什么也不说明** ⇒ ⇒
#   **⇒ 而它必须能被反例打出来 —— `picode` 就是一个真实的 `strip_comments` 变量**
out["negative_control_1000"] = {
    "injected": "**把三个已知答案的变量喂给同一个 `is_stripped()`**、"
                "**不碰真文件**",
    "picode_真实存在的 stripped 变量": is_stripped("picode"),
    "_ausrc_审计原文": is_stripped("_ausrc"),
    "_p996_探针原文": is_stripped("_p996"),
    "why_this_matters": (
        "⭐⭐⭐⭐⭐ **「恒零」与「恒真」一样危险** —— "
        "**而本批的主要读数恰恰是一个 0** ⇒ ⇒ "
        "**⇒ 而「0 条」与「探测器坏了」在输出上完全一样** ⇒ ⇒ "
        "**⇒ 与 §206 P2「恒真的读数要认出它」同族、"
        "**只是这次是「恒零」** ⇒ ⇒ "
        "**⇒ 所以必须有一个「本该返回 True、而它确实返回 True」的样本**"
    ),
}
_nc = out["negative_control_1000"]
out["NC_hold_1000"] = bool(
    _nc["picode_真实存在的 stripped 变量"] is True
    and _nc["_ausrc_审计原文"] is False
    and _nc["_p996_探针原文"] is False)

out["verdicts_1000"] = {
    "p1_ratio_1000_": (
        "✅ **P1 成立：反向锚点比正向少一个量级** ⇒ ⇒ "
        "**⇒ 而这与「反向断言是逐条刻意加的」一致** ⇒ ⇒ "
        "**⇒ 反过来说：一个只有 1:24 的类别、不可能靠「顺手」维持**"
    ),
    "p2_refuted_headline_1000_": (
        "❌ **P2 被否 —— 而它否出来的东西比预测更好** ⇒ ⇒ "
        "**⇒ 我写的是「反向锚点里挂在剥离注释后的文本上的占多数」** ⇒ ⇒ "
        "**⇒ 实测：206 条已登记的反向断言、**206 条查的是原文、0 条查剥离后的** ⇒ ⇒ "
        "⭐⭐⭐⭐⭐ **⇒ 所以「对注释免疫」在这个仓里是 1/206 的孤例 —— "
        "**而那 1 条（`Q.10`）恰恰因为用了 `strip_comments` 而落在「未登记」里、"
        "**官方门压根不查它** ⇒ ⇒ "
        "⭐⭐⭐⭐⭐ **⇒ 也就是说：一条对的设计、和一条被检查的设计、是两件事** ⇒ ⇒ "
        "⭐⭐⭐⭐⭐ **⇒ 而 `PROBE_VARS` 的形状不是中性的 —— "
        "**它是一道隐形的口径：凡是被登记的，查的必然是原文** ⇒ ⇒ "
        "**⇒ 这条口径对「钉代码在做什么」是对的、对「钉文档说了什么」是错的** ⇒ ⇒ "
        "⭐⭐⭐⭐⭐ **⇒ 而 206 : 0 说明这个仓几乎全部选了「查原文」**"
    ),
    "p3_refuted_my_patterns_1000_": (
        "❌ **P3 按它写下来的形式被否、而否证的是我的模式** ⇒ ⇒ "
        "**⇒ 我列的两族（防叙述漂移 / 防实现回退）加起来只覆盖 13/206 = 6%** ⇒ ⇒ "
        "**⇒ 而 94% 落在「其它」—— 这不是「数据没有结构」、是「我这套关键词选错了」** ⇒ ⇒ "
        "**⇒ 第二版改按**结构**分（锚点长什么样、而不是它说了什么）：** "
        "**W 中文散文片段 143｜K 代码片段 48｜I 标识符或路径 8｜O 其它 7** ⇒ ⇒ "
        "**⇒ 覆盖率从 6% 到 97%** ⇒ ⇒ "
        "⭐⭐⭐⭐⭐ **⇒ 而这正是「分类的第一步是『这句话在做什么』、"
        "**不是『它属于哪个关键词』」—— 而我又在按关键词分** ⇒ ⇒ "
        "⭐⭐⭐⭐⭐ **⇒ 而按结构分出来的真两族是**"
        "**「中文散文片段（防某句措辞被写回去）」对「代码片段 / 标识符（防某个实现被引入）」**"
    ),
    "p4_refuted_also_my_pattern_1000_": (
        "❌ **P4 也被否、而且否的方式和 P3 一样** ⇒ ⇒ "
        "**⇒ 我写的是「有反向锚点的锚点文本是『读数』而不是『禁令』」** ⇒ ⇒ "
        "**⇒ 实测 65/206 命中我那条「读数」正则** ⇒ ⇒ "
        "**⇒ 而那 65 条里绝大多数是**代码片段里含数字**（"
        "`Number(ti) < 0`、`zero_idx: zeroIdx.slice(`）** ⇒ ⇒ "
        "**⇒ 所以那条正则量的不是「读数」、是「含数字」** ⇒ ⇒ "
        "⭐⭐⭐⭐⭐ **⇒ 与 P3 同形：**"
        "**我的判据是关键词式的、而它匹配到的是我写下的那个词**"
    ),
    "p5_refuted_not_concentrated_1000_": (
        "❌ **P5 被否、而这次是关于世界的** ⇒ ⇒ "
        "**⇒ 我写的是「反向锚点在少数几个判据组里高度集中」** ⇒ ⇒ "
        "**⇒ 实测：25 个组、前三名占 34%** ⇒ ⇒ "
        "**⇒ 34% 不是「高度集中」** ⇒ ⇒ "
        "⭐⭐⭐⭐ **⇒ 所以 P5 的否与 P3/P4 的否不同类：** "
        "**P3/P4 的否是「我的模式不对」、这一条是「世界就是这样」** ⇒ ⇒ "
        "⭐⭐⭐⭐⭐ **⇒ 而两类否证必须分开数 —— "
        "**否则就会把「我的模式不对」记成「我了解这个仓」**"
    ),
    "nc_1000_": (
        "⭐⭐⭐⭐⭐ **反向用例：证明 `is_stripped()` 能返回 True** ⇒ ⇒ "
        "**⇒ `picode`（仓里真实存在的 `strip_comments` 变量）返回 True** ⇒ ⇒ "
        "**⇒ 而 `_ausrc` 与 `_p996` 返回 False** ⇒ ⇒ "
        "**⇒ 所以「206 条全是 raw」这个 0 是读数、不是探测器坏了** ⇒ ⇒ "
        "**⇒ 而这一条不是形式：它正是本批那个结论能不能成立的前提**"
    ),
    "offline_1000": (
        "⭐⭐⭐⭐⭐ **本批纯离线**：不打开浏览器、不按任何键、**连 `mouse.click` 都没有**、"
        "**只读判据与门两个文本** ⇒ ⇒ "
        "⭐⭐⭐⭐ **零计费是结构性的、不是自律的**"
    ),
}

out["discipline_1000"] = "".join([
    "① ⭐⭐⭐⭐⭐ **反向断言的存在本身就带着「它针对什么」的答案** ⇒\n",
    "  ② ⭐⭐⭐⭐⭐ **「共 N 条」→ 检索词 → 身份 → 「它在防什么」，是一条链** ⇒\n",
    "  ③ ⭐⭐⭐⭐ **同一个断言钉的是代码还是文档、要看它查的文本是什么** ⇒\n",
    "  ④ ⭐⭐⭐⭐⭐ **「X not in Y」对「X 变了」没有任何约束** ⇒\n",
    "  ⑤ ⭐⭐⭐⭐ **反向锚点集中在那几个组里、就不该当零散例外读** ⇒\n",
])

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)

print("pos/neg =", out["n_pos_1000"], "/", out["n_neg_1000"],
      "ratio", out["ratio_1000"])
print("neg_registered =", out["n_neg_registered_1000"],
      "| unregistered", out["n_neg_unregistered_1000"])
print("textkind =", out["neg_textkind_1000"])
print("families =", json.dumps(out["neg_families_1000"], ensure_ascii=False))
print("cross =", json.dumps(out["family_x_textkind_1000"], ensure_ascii=False))
print("n_neg_anchor_is_a_reading =", out["n_neg_anchor_is_a_reading_1000"])
print("top3_share =", out["top3_share_1000"], "| groups",
      out["n_groups_with_negatives_1000"])
print("PROBE_1000_DONE ->", OUT)
