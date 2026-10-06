#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐
batch 1025 —— 量「**判据的方向**」。

问题：verifier 里有 936 条 `check()`。其中一条（S.8）旁边写着本项目自己治过这个病的记录：
    「⚠️ 第一版这里断言 `== 4`，红了（实测 8）。**不是代码错了，是我把一个
      易变量写成了断言** …… 钉条数就是把易变量当契约。」
⇒ **那一条治过了。问题是：还剩多少条同类的？**

⇒ 本批只量，不改。口径：
    ① **锚点型** vs **活判据型** —— 前者只验「那段字还在」，后者验「那个性质还成立」
       （1018：`'<字面量>' in <源码>` 验的是「那段字还在」不是行为）
    ② 活判据里按形状分：**钉死等值 `== N`** / **下界 `>=`、`>`** / **归零 `not`、`is None`、`== 0`**
    ③ ⭐⭐⭐ 关键一步：钉死等值那一类，**被钉的那个量是不是「易变量」**
       —— **易变量 = 会随运行轮次/画布状态变的读数**（§83 的原话）
       —— 分法要机械：`X.count(...)`（数**源码里出现几次**）与 `len(实测表)`
          是两种东西，前者只在代码被改时变、后者逐轮都可能变

**只跑 AST 与正则，零安装、零网络、零浏览器；不改 verifier 一个字。**

⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **阳性对照**：本探针不许被告知「§83 那条在哪」，
必须**自己**找到那条已知为真的实例（易变量判据），并把它单独标出来。
"""
import ast
import collections
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
VER = ROOT / "scripts/verify-jimeng-batch841-unclickable.py"
GOLDEN = ROOT / "docs/research/jimeng-canvas/criterion-direction-1025.json"

SRC = VER.read_text(encoding="utf-8")
TREE = ast.parse(SRC)


def seg(node):
    try:
        return (ast.get_source_segment(SRC, node) or "").strip()
    except Exception:
        return ""


def is_lit(node):
    """这条条件是「活判据」还是「文本锚点」？判据要机械，不能靠「看起来像」。

    ⭐⭐⭐⭐⭐ **口径：把全部字符串字面量摘掉，看剩下什么形状**
      - 剩下 `Call` / `Subscript` / `Attribute` / **非字符串 `Constant`**
        ⇒ **活的**（真的会被求值、真的随运行变）
      - 只剩 `Name`（纯变量引用）⇒ **锚点**（`"字面量" in _p1024` 里 `_p1024`
        是**预读的源码文本**，它的真值不随这一轮探测变）

    ⚠️⚠️⚠️⚠️ **仪器 bug 2（第二版）：第一版用「子树里有没有 `Name`」判活**
      ⇒ `"x" in _p1024` 里有个 `Name(_p1024)` ⇒ **936 条全被判成活的、锚点型 0 条**
      ⇒⇒⇒⇒⇒ **那个结论是假的，而且假得「很整齐」—— 整齐本身就是该怀疑的信号**
      ⇒⇒⇒⇒⇒⇒⇒ `_pXXXX` / `_ausrc` 是**预读源码字符串**，
      **在它身上做 `in` 验的是「那段字还在」，不是行为**（1018 的原话）
    """
    for n in ast.walk(node):
        if isinstance(n, ast.Constant) and not isinstance(n.value, str):
            return True                      # 数字 / None / True… ⇒ 活的
        if isinstance(n, (ast.Call, ast.Subscript, ast.Attribute, ast.BinOp)):
            return True                      # 真的在算东西
    return False


# ── 形状识别 ────────────────────────────────────────────────────────────────
def shape_of(node):
    """给一条**活**条件打形状标签。返回 (kind, lhs, rhs, 整段原文)"""
    cmps = [n for n in ast.walk(node) if isinstance(n, ast.Compare)]
    for c in cmps:
        for op, comp in zip(c.ops, c.comparators):
            if isinstance(op, (ast.Eq, ast.GtE, ast.Gt)) and isinstance(comp, ast.Constant) \
                    and isinstance(comp.value, int):
                kind = {ast.Eq: "pinned_eq", ast.GtE: "floor", ast.Gt: "floor"}[type(op)]
                return kind, seg(c.left), comp.value, seg(c)
    for n in ast.walk(node):
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.Not):
            return "zero", seg(n.operand), None, seg(n)
        if isinstance(n, ast.Compare) and any(isinstance(o, (ast.Is, ast.Eq)) for o in n.ops):
            return "zero", seg(n.left), None, seg(n)
    # ⚠️⚠️ **仪器 bug 1（第一版）：末尾写的是 `seg(c)`，而 `c` 只在上面的
    #   `for c in cmps` 里绑定 ⇒ 走到这里就是 `UnboundLocalError`**
    #   ⇒⇒⇒⇒⇒⇒ 症状是「某个形状一个都没命中」，而形状明明存在 ⇒ **安静的失败形态**
    return "other", None, None, seg(node)


# ⭐⭐⭐⭐⭐ **易变量的机械分法** —— 不靠「我觉得它易变」
#   `X.count(...)` / `X.index(...)` / `X.find(...)`：**数的是源码里出现几次**
#   ⇒ 只有代码被改时才变 ⇒ 不是易变量
#   `len(...)` 且参数名像实测表（`probed`/`whys`/`_row`/`kb`…）或任何 `.get()`：
#   ⇒ 读的是**运行期采集的读数** ⇒ 易变量
SRC_TEXT_CALLS = re.compile(r"\.(count|index|find)\s*\(")
RUNTIME_HINT = re.compile(r"\.get\s*\(|^len\(|len\(")


def volatility(lhs):
    """返回 'source_text' / 'runtime_measured' / 'unknown' —— 口径写进产物

    ⚠️⚠️⚠️ **仪器 bug 3（第三版）：第一版有一句 `"(" in lhs.split(".")[0]`
       就判成运行期读数 ⇒ `sum(f"useArrowKeys({v}" in g2 + a2 for v in (...)) == 5`
       被误判 —— 而它数的是**源码里 `useArrowKeys(` 出现几次**，根本不是易变量**
       ⇒⇒⇒⇒⇒⇒ **处置：只认两种有把握的形状；认不出来的老实写 `unknown`**
       ⇒⇒⇒⇒⇒⇒⇒⭐⭐⭐⭐⭐ **「分类器把自己搞不清的归进危险那一类」是一个会自己
       制造结论的偏差** —— 它让读数看起来更严重，而**更严重的读数更容易被采信**
    """
    if not lhs:
        return "unknown"
    if SRC_TEXT_CALLS.search(lhs):
        return "source_text"
    if ".get(" in lhs or re.match(r"len\(\s*[A-Za-z_]\w*\s*\)$", lhs):
        return "runtime_measured"
    return "unknown"


# ── 逐条遍历 check() ────────────────────────────────────────────────────────
CHECKS = []
calls = [n for n in ast.walk(TREE)
         if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
         and n.func.id == "check"]
for c in calls:
    args = c.args
    if len(args) < 2:
        continue
    label = seg(args[0])
    conds = [a for a in args[1:] if not (isinstance(a, ast.Call) and
                                         isinstance(a.func, ast.Name) and a.func.id == "check")]
    live_args = [a for a in conds if is_lit(a)]
    rec = {
        "label_head": re.sub(r"\s+", " ", label)[:110],
        "lineno": c.lineno,
        "n_cond_args": len(conds),
        "n_live_cond_args": len(live_args),
        "kind": "live" if live_args else "anchor_only",
        "shapes": [],
    }
    for a in live_args:
        k, lhs, rhs, full = shape_of(a)
        rec["shapes"].append({
            "shape": k, "lhs": lhs, "rhs": rhs,
            "volatility": volatility(lhs) if k in ("pinned_eq", "floor") else "n/a",
            "text": re.sub(r"\s+", " ", full)[:130],
        })
    if rec["kind"] == "live":
        for s in rec["shapes"]:
            s["family"] = s["shape"]
        rec["family"] = rec["shapes"][0]["shape"] if rec["shapes"] else "other"
    CHECKS.append(rec)

N_ALL = len(CHECKS)
LIVE = [r for r in CHECKS if r["kind"] == "live"]
ANCHOR_ONLY = [r for r in CHECKS if r["kind"] == "anchor_only"]
PINNED_EQ = [r for r in LIVE if any(s["shape"] == "pinned_eq" for s in r["shapes"])]
FLOOR = [r for r in LIVE if any(s["shape"] == "floor" for s in r["shapes"])]
ZERO = [r for r in LIVE if any(s["shape"] == "zero" for s in r["shapes"])]

# ⭐ 危险交集：**钉死等值** ∩ **被钉的量是运行期读数**
PINNED_EQ_RUNTIME = [r for r in PINNED_EQ
                     if any(s["shape"] == "pinned_eq" and s["volatility"] == "runtime_measured"
                            for s in r["shapes"])]
PINNED_EQ_SOURCE = [r for r in PINNED_EQ
                    if any(s["shape"] == "pinned_eq" and s["volatility"] == "source_text"
                           for s in r["shapes"])]


# ── 阳性对照：不告知答案，得自己找到 §83 那条已知为真的「易变量判据」 ──────────
#   已知事实（写在 verifier 的注释里、可被独立核对）：S.8 旁边有一段
#   「把一个易变量写成了断言 …… 钉条数就是把易变量当契约」的记录。
KNOWN_TRUE_MARKER = "易变量写成了断言"
# ⭐ 判据形状：**底下有 floor、下界是 `len(<实测表>)`** —— 与 §83 记的形状一致
pc_hits = []
for r in CHECKS:
    flat = re.sub(r"\s+", " ", r["label_head"])
    for s in r["shapes"]:
        if s["shape"] == "floor" and s["lhs"] and s["lhs"].startswith("len(") \
                and re.match(r"[A-Za-z_]\w*$", s["lhs"][4:-1] or ""):
            pc_hits.append(r)
POSITIVE_CONTROL = bool(pc_hits)

# 反向自检：拿 verifier 里那段记录当**可核对的原文**，不许凭记忆断言它存在
marker_ctx = []
for i, l in enumerate(SRC.split("\n"), 1):
    if KNOWN_TRUE_MARKER in l or "钉条数就是把易变量当契约" in l:
        marker_ctx.append({"lineno": i, "text": l.strip()[:160]})
MARKER_IN_SRC = len(marker_ctx) > 0


# ── P 判定（只钉机制） ──────────────────────────────────────────────────────
P1 = N_ALL > 0 and len(LIVE) + len(ANCHOR_ONLY) == N_ALL
P2 = all(r["kind"] == "anchor_only" or r["n_live_cond_args"] >= 1 for r in CHECKS)
P3 = POSITIVE_CONTROL and MARKER_IN_SRC
P4 = all(s.get("volatility") for r in LIVE for s in r["shapes"] if s["shape"] in ("pinned_eq", "floor"))
P5 = len(PINNED_EQ_SOURCE) >= 1          # 分法不是「全都易变」——那等于没分
P6 = True
P7 = True

OUT = {
    "P1_every_check_is_classed_live_or_anchor_only_1025": P1,
    "P2_anchor_only_means_no_live_condition_1025": P2,
    "P3_positive_control_the_scan_finds_the_volatile_criterion_on_its_own_1025": P3,
    "P4_every_count_pinning_says_which_volatility_it_assumed_1025": P4,
    "P5_source_text_counting_is_distinguished_from_runtime_measuring_1025": P5,
    "P6_scope_declared_2025": P6,
    "P7_offline_2025": P7,
}

by_family = collections.Counter()
for r in LIVE:
    for s in r["shapes"]:
        by_family[s["shape"]] += 1
vol_count = collections.Counter()
for r in PINNED_EQ:
    for s in r["shapes"]:
        if s["shape"] == "pinned_eq":
            vol_count[s["volatility"]] += 1

GOLDEN.parent.mkdir(parents=True, exist_ok=True)
GOLDEN.write_text(json.dumps({
    "generated_by": "jimeng_probe1025_criterion_direction.py",
    "note": "⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ "
            "**量「判据的方向」** —— verifier 里有 936 条 `check()`，"
            "其中一条（S.8）旁边写着本项目自己治过这个病的记录。"
            "**⇒ 那一条治过了；问题是：还剩多少条同类的？**",
    "question_1025": "verifier 里那些把「一个数」写进判据的条款，有多少钉的是易变量？",
    "how": "⭐⭐⭐⭐⭐ **只跑 `ast` 与正则解析 verifier 本体**；"
           "**零安装、零网络、零浏览器**；**不改 verifier 一个字**",
    "axis_A_anchor_only_vs_live": {
        "what": "⭐⭐⭐⭐⭐ **锚点型 vs 活判据型** —— 判定口径是把条件里的"
                "**字符串字面量全部去掉之后还剩不剩东西**："
                "剩 ⇒ 活的（真的会被求值）；不剩 ⇒ 锚点（只验「那段字还在」）"
                "⇒⇒⇒⇒⇒ 这是 1018 那条纪律的机械化",
        "n_checks": N_ALL,
        "n_live": len(LIVE),
        "n_anchor_only": len(ANCHOR_ONLY),
        "note_about_anchor_only": "⭐⭐⭐⭐⭐ **`anchor_only` 少，不代表锚点少** —— "
                                  "绝大多数 `check()` 都同时含活条件与锚点，"
                                  "只有整条都只验文本的才归这一类 ⇒ "
                                  "**⇒ 「936 条判据」这个说法本身把两种东西混在了一起**",
        "all": [{"kind": r["kind"], "lineno": r["lineno"],
                 "label_head": r["label_head"]} for r in CHECKS],
    },
    "axis_B_shape_of_live_conditions": {
        "what": "⭐ 活判据按形状分：**钉死等值 `== N`** / **下界 `>=`、`>`** / **归零** / 其它",
        "counts_by_shape": dict(by_family),
        "n_checks_with_pinned_eq": len(PINNED_EQ),
        "n_checks_with_floor": len(FLOOR),
        "n_checks_with_zero": len(ZERO),
        "pinned_eq_cases": [
            {"lineno": r["lineno"], "label_head": r["label_head"],
             "shapes": [s for s in r["shapes"] if s["shape"] == "pinned_eq"]}
            for r in PINNED_EQ],
        "floor_cases": [
            {"lineno": r["lineno"], "label_head": r["label_head"],
             "shapes": [s for s in r["shapes"] if s["shape"] == "floor"]}
            for r in FLOOR],
    },
    "axis_C_which_volatility_is_pinned": {
        "what": "⭐⭐⭐⭐⭐⭐⭐ **关键一步：钉死等值那一类，被钉的那个量是不是「易变量」**"
                "（§83 的原话：「demo 画布每次加载都会动态插入节点」）"
                "⇒ 分法必须机械：`X.count(...)` 数的是**源码里出现几次**"
                "（只有代码被改时才变），`len(...)`/`.get()` 读的是**运行期采集的读数**"
                "（逐轮都可能变）",
        "counts_by_volatility": dict(vol_count),
        "n_pinned_eq_on_runtime_measured": len(PINNED_EQ_RUNTIME),
        "n_pinned_eq_on_source_text": len(PINNED_EQ_SOURCE),
        "dangerous_ones": [
            {"lineno": r["lineno"], "label_head": r["label_head"],
             "shapes": [s for s in r["shapes"] if s["shape"] == "pinned_eq"]}
            for r in PINNED_EQ_RUNTIME],
        "rule": "⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ "
                "**⇒ 「== N」这个形状本身不是缺口，缺口是「== N」且 N 是易变量** ⇒ "
                "**⇒⇒⇒⇒⇒⇒ 两类必须分开报：把 `X.count()==2` 当成和 `len(实测)==2` 同一种病，"
                "是**用形状代替语义**——而形状是机械可判的、语义不是**",
    },
    "positive_control": {
        "what": "⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ "
                "**不告知答案**：本探针必须**自己**找到一条「底界是 `len(实测表)`」的判据"
                "（§83 记录的那个形状）",
        "n_found": len(pc_hits),
        "found": [{"lineno": r["lineno"], "label_head": r["label_head"]} for r in pc_hits],
        "marker_in_source": {
            "marker": KNOWN_TRUE_MARKER,
            "n_lines": len(marker_ctx),
            "context": marker_ctx,
        },
        "rule": "⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ "
                "**阳性对照找不到已知答案 ⇒ 这张表就是空的**（1024 那条血的教训）",
    },
    "what_this_does_not_claim": (
        "⚠️⭐⭐⭐⭐⭐ 本批**只分类、不判决**。`pinned_eq` 落在 `source_text` 上，"
        "**不代表它对，只代表「它不会因为跑第二轮而变」** ⇒ "
        "**⇒⇒⇒⇒⇒⇒ 「不会漂」与「对」是两件事，机械分类只能证明前一件** ⇒ "
        "**⇒⇒⇒⇒⇒⇒⇒ 要判「对不对」得逐条读语义，那是人做的事**"
    ),
    "scope": "⚠️⭐⭐⭐⭐⭐ 量的是 **verifier 本体里 `check()` 调用的条件形状**；"
             "**不覆盖探针脚本内部的 `P1..Pn` 判据**（那是另一批的事）；"
             "**不覆盖 audit 散文**；**不改 verifier 一个字**",
    "offline": "**只 `ast.parse` 一个文件 + 正则**；零安装、零网络、零浏览器",
}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


print("verifier 里 `check()` 共 %d 条：活判据型 %d、整条只验文本 %d"
      % (N_ALL, len(LIVE), len(ANCHOR_ONLY)))
print()
print("活判据按形状：", dict(by_family))
print("  钉死等值 `== N` 的判据：%d 条" % len(PINNED_EQ))
print("    其中被钉的量是 **运行期读数**（易变量）：%d 条" % len(PINNED_EQ_RUNTIME))
print("    其中被钉的量是 **源码文本出现次数**（不会逐轮漂）：%d 条" % len(PINNED_EQ_SOURCE))
for r in PINNED_EQ_RUNTIME:
    for s in r["shapes"]:
        if s["shape"] == "pinned_eq":
            print("      ⚠️ :%d  %s  ‖  %s == %s" % (r["lineno"], r["label_head"][:46], s["lhs"], s["rhs"]))
print()
print("阳性对照：自己找到「底界是 len(实测表)」的判据 %d 条 = %s"
      % (len(pc_hits), POSITIVE_CONTROL))
for r in pc_hits[:4]:
    print("      :%d  %s" % (r["lineno"], r["label_head"][:70]))
print("  §83 那段「易变量写成了断言」的原文在源码里：", MARKER_IN_SRC, "（%d 行）" % len(marker_ctx))
for m in marker_ctx[:2]:
    print("      :%d %s" % (m["lineno"], m["text"][:96]))
print()
print("P1..P7 =", [OUT[k] for k in OUT])
print("PROBE_1025_DONE ->", GOLDEN)
sys.exit(0 if all(OUT.values()) else 1)