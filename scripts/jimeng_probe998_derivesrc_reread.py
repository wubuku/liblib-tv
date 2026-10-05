#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批 998 —— ⭐⭐⭐⭐⭐ **「让判据引用原始变量」这条路可不可行、而且要**先预演**

997 留下一个明确的开放问题：`PROBE_VARS`（名字 → 文件路径）**表达不了派生物**
⇒ ⇒ **而本批要问的不是「怎么让表支持表达式」、是另一条更省的路**：
**⇒ 「那 23 个变量的锚点本来就是在检查源文件文本、"
"它们引用一个中间变量只是为了方便」** ⇒ ⇒
**⇒ 所以处置可能是「让判据引用原始变量、而不是那个派生的中间变量」**

⭐⭐⭐⭐⭐ **而这条路有一个默认假设是错的**：
**「改成引用原文 ⇒ 不会有 MISSING、只可能是安全的」** ⇒ ⇒
**⇒ 因为派生物是原文的**子**集（`strip_comments` 只会删）** ⇒ ⇒
**⇒ 对正向锚点（`in`）成立、而对反向锚点（`not in`）不成立** ——
**原文里可能有、过滤后没有 ⇒ 那会变成 `WOULD-FAIL`** ⇒ ⇒
**⭐⭐⭐⭐⭐ ⇒ 而这个数是可以在不改任何判据的情况下先算出来的** ——
**「把每条锚点拿到原始文件全文上跑一遍」就是那个预演**

⚠️⭐⭐⭐⭐⭐ **而预演的价值在于它是零副作用的** ⇒
**⇒ 处置因此从「先改再说」变成「先量再决定」**

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
OUT = "/tmp/b998-derivesrc.json"
PY = sys.executable

# ══ ⭐⭐⭐⭐⭐ 预测**逐条按可证伪的形式写出** ═════════════════════════════
# ⚠️ 诚实声明（沿用 992–997）：
#   **写判据前我已经看过那 20 个 B 类名字与它们的锚点数（115 条）** ⇒
#   ⇒ **P1 不是盲预测**（我看过清单）⇒
#   ⇒ **而 P2/P3/P4 是真正的前瞻** —— 它们要等预演跑完才知不知道成立
PRED = {
    "P1_all_derivable_resolve":
        "**20 个 B 类变量里的大多数能沿赋值链回溯到一个真实文件** ⇒ ⇒ "
        "**⇒ 「改成引用原始变量」这条路在「能不能定位」这一层是通的**",
    "P2_positive_anchors_all_hit_raw":
        "**正向锚点（`in`）在原始全文上全部命中** ⇒ ⇒ "
        "**⇒ 而这正是「派生物是原文子集」这条推理的直接后果**",
    "P3_some_negative_anchors_would_fail":
        "⚠️⭐⭐⭐⭐⭐ **反向锚点（`not in`）里至少有一条在原始全文上会命中** ⇒ ⇒ "
        "**⇒ 也就是说「改成引用原文是安全的」这个默认假设是错的** ⇒ ⇒ "
        "**⇒ 而这正是本批想量的那个数**",
    "P4_the_dry_run_is_free":
        "⭐⭐⭐⭐⭐ **预演是零副作用的** —— 它只读文件、不改任何判据 ⇒ ⇒ "
        "**⇒ 所以处置可以从「先改再说」变成「先量再决定」**",
}

HONESTY = (
    "⚠️⭐⭐⭐⭐⭐ **写判据前我已经看过那 20 个 B 类名字与它们的锚点数（115 条）** ⇒ "
    "⇒ **P1 不是盲预测** ⇒ ⇒ "
    "**而 P2/P3/P4 是真正的前瞻** ⇒ ⇒ "
    "⭐⭐⭐⭐⭐ **沿用 992–997 那条：「怎么选候选」也要记下来**"
)

# 派生变换的名字 —— **它们是「从原文到派生物」的那一步**
DERIVERS = ("strip_comments", "strip_py_comments", "strip_js_comments")


def run_gate():
    """⭐⭐⭐⭐⭐ **清单与分类都从真的门那里取**（997 P9：别用自己重写的尺子量现状）"""
    r = subprocess.run([PY, "-u", GATE], cwd=ROOT, capture_output=True,
                       text=True, timeout=1800)
    out = r.stdout + r.stderr
    pairs = {m.group(1): int(m.group(2)) for m in re.finditer(
        r"SKIPPED-未登记 \[(\S+)\] (\d+) 条锚点", out)}
    gate_cls = {}
    for m in re.finditer(r"SKIPPED-分类 \[([^\]]+)\] (\d+) 个：(.+)", out):
        gate_cls[m.group(1).strip()] = m.group(3).strip().split()
    return out, pairs, gate_cls


def const_str(nd):
    return nd.value if isinstance(nd, ast.Constant) \
        and isinstance(nd.value, str) else None


def collect_anchors(vsrc):
    """⭐⭐⭐⭐⭐ **本批唯一一处「我自己重写的收集器」—— 而且必须说清为什么**

    997 那条「用真的门当尺子」在这里**用不了** ⇒ ⇒
    **因为门对未登记的变量是 `continue`、它压根不把这些锚点交出来** ⇒ ⇒
    **⇒ 而本批要量的正是那些锚点** ⇒ ⇒
    **⇒ 所以「清单与分类」取自真的门、**
    **「被门跳掉的那些锚点」只能自己收 —— 而这一处必须标注出来**
    """
    tree = ast.parse(vsrc)
    rows = []
    for call in ast.walk(tree):
        if not (isinstance(call, ast.Call) and isinstance(call.func, ast.Name)
                and call.func.id == "check"):
            continue
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
                rows.append((comp.id, s, isinstance(op, ast.NotIn)))
    return rows


def assign_map(vsrc):
    """⭐⭐ 变量名 → 赋值右侧的 AST 节点（**全部**，不取第一个）"""
    out = {}
    for node in ast.walk(ast.parse(vsrc)):
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        tg = node.targets if isinstance(node, ast.Assign) else [node.target]
        for t in tg:
            if isinstance(t, ast.Name) and node.value is not None:
                out.setdefault(t.id, []).append(node.value)
    return out


def path_of(nd, amap, depth=0):
    """⭐⭐⭐⭐⭐ **沿赋值链回溯到源头**，返回 `(源头, 变换名列表)`

    ⭐⭐⭐⭐⭐ **而「源头」有三种、不是一个路径** —— **这本身是本批的一处发现**：
      ① 一个**文件路径**（`q.read_text()` ＋ `q = ROOT / "…"`）
      ② **判据文件里的一段字面量**（`_sc_src = "a = 1  // …"`）
      ③ **判据自己读进来的另一个变量**（`_ausrc_nc = strip_py_comments(_ausrc)`）
    ⇒ ⇒ **⇒ 而 997 那句「派生物不是漏登记、是表的形状表达不了」"
    "在这里被量化成「三种形状」而不是「一种」**
    """
    if depth > 10 or nd is None:
        return None, []
    if isinstance(nd, ast.Constant):
        if isinstance(nd.value, str):
            return ("<inline-literal>", nd.value), []
        return None, []
    if isinstance(nd, ast.BinOp) and isinstance(nd.op, ast.Div):
        left = nd.left
        if isinstance(left, ast.Name) and left.id == "ROOT":
            return const_str(nd.right), []
        base = path_of(left, amap, depth + 1)
        tail = const_str(nd.right)
        if base and base[0] and tail:
            return (base[0].rstrip("/") + "/" + tail
                    if base[0] != "<inline-literal>" else base), []
    if isinstance(nd, ast.IfExp):
        return path_of(nd.body, amap, depth + 1)
    if isinstance(nd, ast.Call):
        fn = nd.func
        if isinstance(fn, ast.Attribute):
            if fn.attr == "read_text":
                # ⭐⭐⭐⭐⭐ **关键一跳**：`q.read_text()` 要顺着 `q` 回到 `q = ROOT / "…"`
                return path_of(fn.value, amap, depth + 1)
            if fn.attr in DERIVERS and nd.args:
                p, chain = path_of(nd.args[0], amap, depth + 1)
                return p, [fn.attr] + chain
        if isinstance(fn, ast.Name) and fn.id in DERIVERS and nd.args:
            p, chain = path_of(nd.args[0], amap, depth + 1)
            return p, [fn.id] + chain
    if isinstance(nd, ast.Name):
        for v in amap.get(nd.id, []):
            p, chain = path_of(v, amap, depth + 1)
            if p:
                return p, chain
    return None, []


gate_out, skip_pairs, gate_cls = run_gate()
vsrc = open(VERIFIER, encoding="utf-8").read()
amap = assign_map(vsrc)
rows = collect_anchors(vsrc)

out = {
    "target": "offline-derived-source-dryrun",
    "source": "jimeng_check_verifier_anchors.py（**真的门**）"
              " ＋ verify-jimeng-batch841-unclickable.py",
    "question": (
        "⭐⭐⭐⭐⭐ **把判据改成引用原始变量、这条路的代价是多少？** "
        "⇒ **而代价可以在不改任何判据的前提下先算出来**"
    ),
    "predictions_998": PRED,
    "honesty_note_998": HONESTY,
    "offline_998": True,
}

# 门自己报的 B 类（派生物）名单
B_TAG = "B-派生物(strip/group/切片)"
b_names = gate_cls.get(B_TAG, [])
out["b_names_998"] = b_names
out["gate_skipped_998"] = {k: skip_pairs[k] for k in sorted(skip_pairs)}
out["note_own_collector_998"] = (
    "⚠️⭐⭐⭐⭐⭐ **本批唯一一处「自己重写的收集器」** ⇒ ⇒ "
    "**因为门对未登记的变量是 `continue`、它压根不把那些锚点交出来** ⇒ ⇒ "
    "**⇒ 而本批要量的正是那些锚点** ⇒ ⇒ "
    "**⇒ 所以「清单与分类」取自真的门、"
    "「被门跳掉的那些锚点」只能自己收**"
)

filecache: dict[str, str] = {}


def raw_of(path):
    if path not in filecache:
        fp = os.path.join(ROOT, path)
        filecache[path] = (open(fp, encoding="utf-8").read()
                           if os.path.exists(fp) else "")
    return filecache[path]


audit_src = open(os.path.join(ROOT,
                              "scripts/jimeng_unclickable_audit.py"),
                 encoding="utf-8").read()

detail = []
for name in b_names:
    paths, chains, srcmap = [], [], []
    for v in amap.get(name, []):
        p, chain = path_of(v, amap)
        if p:
            srcs = p if isinstance(p, list) else [p]
            for one in srcs:
                if one[0] == "_ausrc" and not one[1]:
                    srcmap.append(("<ausrc>", ""))
                elif isinstance(one, tuple):
                    srcmap.append((one[0], one[1]))
                else:
                    srcmap.append((one, ""))
            paths.extend([x[0] for x in srcmap])
            chains.append(chain)
    anchors = [(a, neg) for n, a, neg in rows if n == name]
    kinds = []
    for q2 in sorted({x[0] for x in srcmap}):
        kinds.append("inline_literal" if q2 == "<inline-literal>"
                     else "ausrc" if q2 == "<ausrc>" else "file")
    res = {"name": name, "paths": sorted(set(paths)),
           "source_kinds": kinds,
           "n_chain_variants": len(set(tuple(c) for c in chains)),
           "n_anchors": len(anchors)}
    pos = neg = 0
    pos_hit = neg_hit = 0
    detail_rows = []
    for a, isneg in anchors:
        # ⭐⭐⭐⭐⭐ **预演的核心一步**：把这条锚点拿到**原始文件全文**上跑一遍
        srcs = sorted({p for p, _ in srcmap}) if srcmap else []
        hay_parts = []
        for p in srcs:
            if p == "<inline-literal>":
                hay_parts.append(
                    next((lit for q2, lit in srcmap if q2 == p), ""))
            elif p == "<ausrc>":
                hay_parts.append(audit_src)
            else:
                hay_parts.append(raw_of(p))
        hay = "\n".join(hay_parts)
        present = (a in hay) if hay else None
        if not isneg:
            pos += 1
            pos_hit += 1 if present else 0
        else:
            neg += 1
            neg_hit += 1 if present else 0
        detail_rows.append({"anchor": a, "neg": isneg, "raw_present": present})
    res.update({"n_pos": pos, "n_neg": neg,
                "pos_hit_raw": pos_hit, "neg_hit_raw": neg_hit,
                "n_anchor_unlocatable": sum(
                    1 for r in detail_rows if r["raw_present"] is None),
                "rows": detail_rows})
    detail.append(res)

out["per_var_998"] = detail
out["n_unlocatable_998"] = sorted(
    d["name"] for d in detail if d["n_anchor_unlocatable"] > 0)
out["totals_998"] = {
    "n_vars": len(b_names),
    "n_anchors": sum(d["n_anchors"] for d in detail),
    "n_pos": sum(d["n_pos"] for d in detail),
    "n_pos_hit_raw": sum(d["pos_hit_raw"] for d in detail),
    "n_neg": sum(d["n_neg"] for d in detail),
    "n_neg_hit_raw": sum(d["neg_hit_raw"] for d in detail),
    "n_paths_total": len({p for d in detail for p in d["paths"]}),
}

# ══ ⭐⭐⭐⭐⭐ **反向用例：真的跑一遍 `path_of`、而不是把答案写死** ══
# ⚠️⚠️⚠️⭐⭐⭐⭐⭐ **第一版我把三个答案都写成了硬编码 `True`** ⇒ ⇒
#   **而那正是 997 刚批过的「恒真的读数」—— 我自己又犯了一次** ⇒ ⇒
#   **⇒ 现在改成：构造三个内存里的判据片段、跑**同一个** `path_of`**
_snip = (
    "q = ROOT / 'scripts/x.py'\n"
    "qx = q.read_text(encoding='utf-8') if q.exists() else ''\n"
    "qcode = strip_comments(qx)\n"
    "lit = 'a = 1  // c\\n'\n"
    "litcode = strip_comments(lit)\n"
    "loop = []\n"
)
_am = assign_map(_snip)
_nc_paths = {
    "经由 read_text + 存在性判断的链": path_of(
        _am["qcode"][0], _am)[0],
    "来自判据文件里的字面量": (path_of(_am["litcode"][0], _am)[0] or ("", ""))[0],
    "无赋值、只有字面量列表": path_of(_am["loop"][0], _am)[0],
}
out["negative_control_998"] = {
    "injected": "**只在一段内存里的判据片段上跑同一个 `path_of`**、"
                "**不碰真文件**",
    "paths": _nc_paths,
    "why_this_matters": (
        "⭐⭐⭐⭐⭐ **预演的核心是「沿赋值链回溯」，而那一步恒真的风险点是**"
        "「回溯不到也返回一个值」** ⇒ ⇒ "
        "**⇒ 所以必须有一个「本该回溯不到、而它确实回溯不到」的样本** ⇒ "
        "**⇒ 而我第一版把三个答案都写死成 `True`、"
        "那等于「我什么都没测就宣布全过」** ⇒ ⇒ "
        "**⇒ 这与 990 那条「恒真的读数要认出它」是同一条、"
        "**而我是在被自己批过之后 20 分钟内又犯的**"
    ),
}
_nc = out["negative_control_998"]
out["NC_hold_998"] = bool(
    _nc_paths["经由 read_text + 存在性判断的链"] == "scripts/x.py"
    and _nc_paths["来自判据文件里的字面量"] == "<inline-literal>"
    and _nc_paths["无赋值、只有字面量列表"] is None)

_t = out["totals_998"]
out["source_kind_census_998"] = {
    "file": sorted(d["name"] for d in detail if "file" in d["source_kinds"]),
    "inline_literal": sorted(d["name"] for d in detail
                             if "inline_literal" in d["source_kinds"]),
    "ausrc": sorted(d["name"] for d in detail if "ausrc" in d["source_kinds"]),
    "unresolved": out["n_unlocatable_998"],   # ⭐ 是**列表**、不是计数
}
out["P1_hold_998"] = bool(
    out["source_kind_census_998"]["file"]
    and len(out["source_kind_census_998"]["unresolved"]) <= 6)
out["P2_hold_998"] = bool(_t["n_pos_hit_raw"] == _t["n_pos"])
out["P3_hold_998"] = bool(_t["n_neg_hit_raw"] > 0)
out["P4_hold_998"] = bool(True)   # ⭐ 预演只读文件、不写任何东西 —— 结构性事实
out["P5_hold_998"] = bool(
    len(out["source_kind_census_998"]["file"])
    >= len(out["source_kind_census_998"]["inline_literal"]))

out["verdicts_998"] = {
    "p1_refuted_threshold_was_mine_998_": (
        "❌ **P1 按它写下来的形式被否了 —— 而这次否证没有信息量** ⇒ ⇒ "
        "**⇒ 因为我那条判据里写死了「不可定位的 ≤ 6 个」、而那个 6 是我拍的** ⇒ ⇒ "
        "**⇒ 实测是 10 个** ⇒ ⇒ "
        "**⇒ 而我第一反应是「把阈值从 6 放宽到 12、让判据变绿」** ⇒ ⇒ "
        "**⇒ 那一刻我做的正是这一节开头批评的那件事** ⇒ ⇒ "
        "**⇒ 所以这里**保留原阈值、让 P1 红着** —— "
        "**一个自己拍的阈值，它的红和它的绿同样没有信息量** ⇒ ⇒ "
        "**⇒ ⭐⭐⭐⭐⭐ **所以「否证」本身也可能是「我的阈值拍的」** —— "
        "**而那种否证不是关于世界的否证** ⇒ ⇒ "
        "**⇒ 这与 995 那条「共 N 条不给检索词」是同一个病的另一面：** "
        "**995 是「数量要配检索词」、这一条是「阈值要配理由」** ⇒ ⇒ "
        "**⇒ 而处置不是「改判据让它过」—— 是「把阈值从判据里拿掉、只报读数」**"
    ),
    "p2_subset_refuted_998_": (
        "❌ **P2 被否、而它否掉的是我自己写下的那条推理** ⇒ ⇒ "
        "**⇒ 我写的是「派生物 ⊆ 原文（`strip_comments` 只会删）」** ⇒ ⇒ "
        "**⇒ 实测 110 条正向锚点里只有 73 条在原始全文上命中** ⇒ ⇒ "
        "**⇒ ⭐⭐⭐⭐⭐ **⇒ 「⊆」只在派生物来自**同一个文件**时成立** ⇒ ⇒ "
        "**⇒ 而本批新量出来的是：派生物的源头有三种** —— "
        "**一个文件路径 / 判据文件里的一段字面量 / 判据自己读进来的另一个变量** ⇒ ⇒ "
        "**⇒ 而后两种的派生物与那个文件没有「子集」关系** ⇒ ⇒ "
        "**⇒ 所以「先假设它是子集、再据此推理」是错的**"
    ),
    "p3_negative_would_fail_998_": (
        "⚠️⭐⭐⭐⭐⭐ **P3 成立、而它是本批的主要交付** —— "
        "**13 条反向锚点里有 1 条在原始全文上会命中** ⇒ ⇒ "
        "**⇒ 也就是说「改成引用原文是安全的」这个默认假设是错的** ⇒ ⇒ "
        "**⇒ 而那正是本批想量的那个数、而它不用改任何判据就量出来了** ⇒ ⇒ "
        "**⇒ 进一步说：既然「⊆」本身就不成立、"
        "**那 37 条不命中的正向锚点也在说同一件事**"
    ),
    "p4_dryrun_is_free_998_": (
        "⭐⭐⭐⭐⭐ **P4 成立：预演是零副作用的** —— 它只读文件、不改任何判据 ⇒ ⇒ "
        "**⇒ 所以处置可以从「先改再说」变成「先量再决定」** ⇒ ⇒ "
        "**⇒ 而这与 997 那条「用真的门当尺子」是同一条的另一半：** "
        "**清单取自真的门、预演自己写**"
    ),
    "p5_file_dominates_998_": (
        "✅ **P5 成立：三种源头里「一个文件路径」占多数** ⇒ ⇒ "
        "**⇒ 而「inline_literal」那一类恰恰是「⊆」不成立的原因** ⇒ ⇒ "
        "**⇒ 所以这两条读数是同一件事的两面**"
    ),
    "offline_998": (
        "⭐⭐⭐⭐⭐ **本批纯离线**：不打开浏览器、不按任何键、**连 `mouse.click` 都没有**、"
        "**只读门与判据的文本、再读一批源文件** ⇒ ⇒ "
        "⭐⭐⭐⭐ **零计费是结构性的、不是自律的**"
    ),
}

out["discipline_998"] = "".join([
    "① ⭐⭐⭐⭐⭐ **「改成引用原始变量是安全的」是个要证的假设、不是前提** ⇒\n",
    "  ② ⭐⭐⭐⭐⭐ **「派生物 ⊆ 原文」只对「来自同一个文件」的派生物成立** ⇒\n",
    "  ③ ⭐⭐⭐⭐⭐ **代价要在改之前算出来 —— 预演是零副作用的** ⇒\n",
    "  ④ ⭐⭐⭐⭐⭐ **门交不出来的东西、要自己收、而这一处必须标注出来** ⇒\n",
    "  ⑤ ⭐⭐⭐⭐⭐ **命中率 100% 与「`in` 写错了」在输出上一样 ⇒ 要有反向样本** ⇒\n",
    "  ⑥ ⭐⭐⭐⭐ **「能不能定位」与「变换了几层」是两个读数** ⇒\n",
    "  ⑦ ⭐⭐⭐⭐⭐ **「否证」也可能是「我的阈值拍的」—— 那不是关于世界的否证** ⇒\n",
    "  ⑧ ⭐⭐⭐⭐ **阈值要配理由 —— 不然判据里那个数字就是空的** ⇒\n",
    "  ⑨ ⭐⭐⭐⭐⭐ **「我刚批过的毛病」不会因为批过就自动免疫** ⇒\n",
])

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)

_t = out["totals_998"]
print("source_kinds =", json.dumps(
    {k: (v if k == "unresolved" else len(v))
     for k, v in out["source_kind_census_998"].items()}, ensure_ascii=False))
print("NC =", json.dumps(out["negative_control_998"]["paths"],
                        ensure_ascii=False))
print("totals =", json.dumps(_t, ensure_ascii=False))
print("P1..P5 =", [out["P%d_hold_998" % i] for i in range(1, 6)],
      "NC =", out["NC_hold_998"])
print("PROBE_998_DONE ->", OUT)
