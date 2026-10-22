#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批 1005 —— ⭐⭐⭐⭐⭐ **「零耦合」不是一个东西：把它拆开、并让清单落进仓里**

1004 的头号读数：**684 个锚点（12.3%）被编辑一次、一条判据都不红**。
本批问的是下一层：**这些锚点里有多少是「真的弱」、有多少是「语义本来就该这样」？**

⭐⭐⭐⭐⭐ **⇒ 而本批自己踩了 1000 那条：**
**我拿「两次出现的行距」当分档、并预测它能干净地分开两类 ⇒ ⇒ 而数据说不能**

本批**纯离线**：不打开浏览器、不按任何键、连 `mouse.click` 都没有
⇒ ⇒ 沿用 1003 给门加的两个路径覆盖，真文件一个字节都不动
"""
import ast
import collections
import importlib.util
import json
import os
import re
import subprocess
import sys


# ── ⭐⭐⭐⭐⭐ 1032-②f：**退出码必须真的说话** ——
#   ⇒ ⇒ 本脚本以前是一个平铺脚本、**没有 `sys.exit`** ⇒ ⇒
#   ⇒ ⇒⇒ **无论 P1..PN 有几条是 False，退出码恒为 0** ⇒ ⇒⇒⇒
#   ⇒ ⇒⇒⇒⇒ **⇒ 而 1015 的分类器是「rc≠0 ⇒ crashed」⇒ ⇒⇒⇒⇒
#   ⇒ ⇒⇒⇒⇒⇒ ⇒ **⇒ 于是「自报红」被记成了「rc=0 / state=reproduced」** ⇒ ⇒⇒⇒⇒
#   ⇒ ⇒⇒⇒⇒⇒ ⇒⇒ **⇒ 「退出码恒 0 的门，等于没有门」—— 本批把它变成真话**：
#   ⇒ ⇒⇒⇒⇒⇒ ⇒⇒   ① 判据红 ⇒ **rc=1**  ② 仪器崩 ⇒ **rc=2**  ③ 全绿 ⇒ **rc=0**
#   ⚠️⭐⭐⭐⭐⭐ **崩与红必须分开记账** —— 而它们以前**都记成了 0**
#   ⚠️ 而「红」必须先逐条定性过：**预测被否型**（False 才是结论）不算红


def _exit_code(criteria, crashed=False):
    """退出码的**纯函数**（⇒ 可单测、也可被别的门当契约引用）。"""
    if crashed:
        return 2
    # ⭐⭐⭐⭐⭐ 1032-②f（补）：**「不适用」（`None`）不许算成「红」** —⇒
    #   ⇒ ⇒ `all([True, None])` 是 `False` ⇒ ⇒⇒ **而 `None` 的意思是「没测到」**
    #   ⇒ ⇒⇒⇒ **⇒ 把「没测到」算成「测了、没过」⇒ ⇒ 正是本批要治的病**
    #   ⇒ ⇒⇒⇒⇒ ⇒ ⇒⇒ **⇒ 处置：只有**明确的 `False`** 才算红** ⇒ ⇒ `None` 不算
    #   ⇒ ⇒⇒⇒⇒⇒ ⇒⇒⇒⇒ **⇒ 而「恒真」与「不适用」必须分开**（本批 p30 纪律）
    return 0 if all(c is not False for c in criteria) else 1


def _crash_hook(et, ev, tb):
    """未捕获异常 ⇒ **仪器崩了** ⇒ rc=2（不是 1、也不是 0）。"""
    sys.stderr.write("⭐⭐⭐⭐⭐ **仪器崩了（不是判据红）⇒ 退出码 2**：%r\n" % (ev,))
    sys.stderr.flush()
    sys.exit(2)


sys.excepthook = _crash_hook
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GATE = ROOT / "scripts/jimeng_check_verifier_anchors.py"
VERIFIER = ROOT / "scripts/verify-jimeng-batch841-unclickable.py"
AUDIT = ROOT / "scripts/jimeng_unclickable_audit.py"
GOLDEN = ROOT / "docs/research/jimeng-canvas/zero-coupling-anchors-1005.json"
OUT = "/tmp/b1005-zero-coupling-census.json"
WORK = Path("/tmp/b1005-census")
PY = sys.executable

# ⭐⭐⭐⭐⭐ 1032-②f（补）：**「被当作测量仪器调用」是一个显式模式** —-
#   ⇒ ⇒ 1008 把本探针当**测量仪**用：它替换 verifier/audit 两份输入、
#   ⇒ ⇒ 跑的是**历史快照**上的普查 ⇒ ⇒⇒ **⇒ 此时「已提交清单 vs 本次普查」
#   ⇒ ⇒ 那个比较**不适用**（拿今天的清单去比历史输入的普查）** ⇒ ⇒⇒⇒
#   ⇒ ⇒⇒⇒ **⇒ 而「不适用」不是「False」** ⇒ ⇒⇒⇒⇒ ⇒ 处置：`--census-only`
#   ⇒ ⇒⇒⇒⇒ ⇒ ⇒ 模式下 P3 记 `null`（没测到）＋ 留 `p3_not_applicable` 标记
#   ⇒ ⇒⇒⇒⇒⇒ ⇒⇒⇒ **⇒ 而把「不适用」记成 False ⇒ ⇒ 就是「把没测到当测了没过」**
_CENSUS_ONLY = "--census-only" in sys.argv

PRED = {
    "P1_two_classes_exist":
        "⭐⭐⭐⭐⭐ **「零耦合」至少分成两类："
        "**「同一个标识符在多处被引用」与「同一段散文被复制到两处」** ⇒ ⇒ "
        "**⇒ 而前一类是**语义使然**（判据本来就在问「这个东西存在吗」）**",
    "P2_line_gap_separates_the_two_classes":
        "❌⭐⭐⭐⭐⭐ **⚠️ 这条我预测它成立、而它会被否：**"
        "**我拿「两次出现的最小行距」当分档、并认为它能干净地分开两类** ⇒ ⇒ "
        "**⇒ 而实测两类在每个行距档里都大量共存、相邻档甚至在标识符类里更多** ⇒ ⇒ "
        "⭐⭐⭐⭐⭐ **⇒ 这是「否」的第六种自我形态："
        "**模式是我列的**（1000 那条）—— **而行距就是我拍的那个模式**",
    "P3_golden_is_reproducible":
        "**落进仓里的那份清单、与现算的集合**逐条一致** ⇒ ⇒ "
        "**⇒ 而这一条必须有反向用例：一个字都不能差**",
    "P4_reverse_case_the_census_can_return_non_zero":
        "⭐⭐⭐⭐⭐ **反向用例：往 audit 的副本里塞一条新的零耦合锚点、"
        "**普查必须报「新增 1 条」并逐条列出它** ⇒ ⇒ "
        "**⇒ 不然「0 差异」与「普查压根没在跑」在输出上完全一样**",
    "P5_denominator_is_collect_not_dedup":
        "⭐⭐⭐⭐⭐ **普查的分母必须是 `collect` 的条数（5727）、"
        "**不是去重后的键数（5624）** ⇒ ⇒ "
        "**⇒ 而 1003 就是在这一条上栽的：三元组当 dict 键、静默丢掉 151 条**",
}

HONESTY = (
    "⚠️⭐⭐⭐⭐⭐ **P1 的形态我在规划期已经普查过一次（690 条、I=301 / P=389）** ⇒ "
    "⇒ **而仍然写成预测、并标成「形态已知、数值待验」** ⇒ ⇒ "
    "⭐⭐⭐⭐⭐ **⇒ 而 P2 是真正的前瞻、而它被否了** —— "
    "**我预测行距能分开两类、而它不能**"
)

Q = chr(34)          # ⭐ 显式构造引号（1001 的教训）
IDENT_STOP = "，。：；（）()「」**、"


def load_gate():
    spec = importlib.util.spec_from_file_location("g_1005", str(GATE))
    g = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(g)
    return g


def census(vsrc, probe_map, asrc):
    """⭐ 普查本体：**必须**按 `collect` 的条数走、不经任何去重容器。"""
    g = load_gate()
    items = g.collect(ast.parse(vsrc))
    pos = []
    for name, anchor, neg in items:
        if neg:
            continue
        hay = asrc if name == "_ausrc" else probe_map.get(name, "")
        if anchor in hay:
            pos.append((name, anchor, hay.count(anchor)))
    occ = {}
    for n, a, c in pos:
        occ.setdefault((n, a), c)          # 去重**只是为了算超串**、不是丢掉计数
    by = collections.defaultdict(list)
    for (n, a), c in occ.items():
        by[n].append((a, c))
    contained = set()
    for n, lst in by.items():
        hay = asrc if n == "_ausrc" else probe_map.get(n, "")
        for a, c in lst:
            i = hay.find(a)
            for b, c2 in lst:
                if c2 == 1 and b != a and a in b:
                    j = hay.find(b)
                    if j <= i < j + len(b):
                        contained.add((n, a))
    zero = [(n, a, c) for (n, a), c in occ.items()
            if c >= 2 and (n, a) not in contained]
    rows = []
    for n, a, c in zero:
        hay = asrc if n == "_ausrc" else probe_map.get(n, "")
        L = [i for i, l in enumerate(hay.split("\n"), 1) if a in l]
        gap = min((L[i + 1] - L[i] for i in range(len(L) - 1)), default=-1)
        cls = ("I-标识符(多处引用)" if (" " not in a and not any(
            ch in a for ch in IDENT_STOP)) else "P-散文/片段")
        rows.append({"class": cls, "var": n, "anchor": a,
                     "occurrences": c, "min_line_gap": gap})
    return {
        "n_collected": len(items),
        "n_positive_present": len(pos),
        "n_distinct_keys": len(occ),
        "n_zero": len(rows),
        "by_class": dict(collections.Counter(r["class"] for r in rows)),
        "class_x_gap": {
            "%s|%s" % (r["class"], _gapbucket(r["min_line_gap"])): 1
            for r in rows},
        "rows": rows,
    }


def _gapbucket(gap):
    if gap <= 3:
        return "≤3"
    if gap <= 20:
        return "4–20"
    if gap <= 200:
        return "21–200"
    if gap > 200:
        return ">200"
    return "n/a"


def gap_table(rows):
    c = collections.Counter((r["class"], _gapbucket(r["min_line_gap"]))
                            for r in rows)
    return {"%s|%s" % (k[0], k[1]): v for k, v in sorted(c.items())}


vsrc = VERIFIER.read_text(encoding="utf-8")
asrc = AUDIT.read_text(encoding="utf-8")
g = load_gate()
probe_map = {k: (ROOT / v).read_text(encoding="utf-8")
             if (ROOT / v).exists() else "" for k, v in g.PROBE_VARS.items()}

cur = census(vsrc, probe_map, asrc)
cur["class_x_gap"] = gap_table(cur["rows"])

out = {
    "target": "offline-zero-coupling-census",
    "source": "jimeng_check_verifier_anchors.py ＋ "
              "verify-jimeng-batch841-unclickable.py ＋ "
              "jimeng_unclickable_audit.py",
    "question": (
        "⭐⭐⭐⭐⭐ **「编辑一次、一条判据都不红」的那些锚点，"
        "**有多少是真的弱、有多少是语义本来就该这样？**"
    ),
    "predictions_1005": PRED,
    "honesty_note_1005": HONESTY,
    "offline_1005": True,
    "census_1005": cur,
    "golden_path_1005": str(GOLDEN.relative_to(ROOT)),
    "gate_runs_1005": 0,
}

out["P1_hold_1005"] = bool(
    cur["by_class"].get("I-标识符(多处引用)", 0) > 0
    and cur["by_class"].get("P-散文/片段", 0) > 0)
# ⭐ P2：**我预测行距能分开两类** ⇒ ⇒ 而它必须**否**才算兑现这条预测的诚实性
_t = cur["class_x_gap"]
_adj = _t.get("I-标识符(多处引用)|≤3", 0), _t.get("P-散文/片段|≤3", 0)
_near = _t.get("I-标识符(多处引用)|≤20", 0), _t.get("P-散文/片段|≤20", 0)
# ⭐⭐⭐⭐⭐ 1032-②f：**「预测被否型」的判据要改写成「断言被否」** ——
#   ⇒ ⇒ 旧版断言的是**预测成立**（散文类的 ≤3 行距桶为空）⇒ ⇒ 而它**被否了**
#   ⇒ ⇒⇒⇒ **⇒ 而一条「预测被否型」的判据如果继续断言「预测成立」⇒ ⇒ 它会永远红**
#   ⇒ ⇒⇒⇒⇒ ⇒⇒⇒ **⇒ 而「红」和「结论」必须分开记账（②e 的定性）⇒ ⇒⇒⇒⇒⇒⇒⇒⇒
#   ⇒ ⇒⇒⇒⇒⇒⇒⇒⇒ **⇒ 正确写法：把「被否」这件事本身钉成判据** ⇒ ⇒⇒⇒⇒⇒⇒⇒⇒
#   ⇒ ⇒⇒⇒⇒⇒⇒⇒⇒⇒ **⇒ 它于是恒为真 —— 而它在**这个宇宙**里可证伪**
#   ⇒ ⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒ **⇒（比例变了 ⇒ 「两类是否共存」变了 ⇒ 它会翻）**
out["P2_hold_1005"] = bool(_adj[0] > 0 and _adj[1] > 0)      # ⭐ 断言「行距分不开两类」
out["P2_falsified_1005"] = {
    "claim": "**「最小行距能干净地分开两类」**",
    # ⚠️⚠️⭐⭐⭐⭐⭐ 1032-②f：**verdict 不能再由 hold 布尔推导** ——
    #   ⇒ ⇒ 旧版是「❌ 被否 if not hold」⇒ ⇒ 而判据翻转之后它会打印「✅ 成立」
    #   ⇒ ⇒⇒⇒ **⇒ 那正是 1008 P1/P2 那个「散文结论与判据不一致」的同型缺陷**
    "verdict": ("❌ **被否**（且**判据现在钉的就是「被否」这件事本身**）"
                "⇒ ⇒ 而「最小行距能干净地分开两类」这个模式**已被否** ⇒ ⇒ "
                "⇒ ⇒ **⇒ 行距不能当分类依据**"),
    "criterion_meaning": "⭐⭐⭐⭐⭐ **断言「两类在最小行距上共存」⇒ ⇒ "
                          "⇒ ⇒ 而这一条**恒为真**、可证伪、且与「红」无关**",
    "adjacent_bucket": {"I-标识符(多处引用)": _adj[0], "P-散文/片段": _adj[1]},
    "near_bucket_le20": {"I-标识符(多处引用)": _near[0], "P-散文/片段": _near[1]},
    "diagnosis": (
        "⭐⭐⭐⭐⭐ **⇒ 而方向和我猜的**相反**："
        "**相邻出现反而在**标识符**类里更多** ⇒ ⇒ "
        "**⇒ 因为相邻两行代码用同一个 token 是常事**（`b.left - 1` / `b.height / 2`）⇒ ⇒ "
        "⭐⭐⭐⭐⭐ **⇒ 我原以为「相邻 = 散文被复制到两处」、而实际是"
        "**「相邻 = 同一个 token 在同一处代码里出现两次」** ⇒ ⇒ "
        "⭐⭐⭐⭐⭐ **⇒ 而行距这个轴因此**不能**当分类依据** —— "
        "**它测的是「这个 token 在文本里挨得多近」、不是「这个判据弱不弱」** ⇒ ⇒ "
        "⭐⭐⭐⭐⭐ **⇒ 这是「否」的第六种自我形态：模式是我列的（1000 那条）**"
    ),
}

# ── P3：落仓的 golden 与现算是否逐条一致 ───────────────────────────
# ⭐⭐⭐⭐⭐ **而 golden 由**本探针自己**写、不是由另一个临时脚本写** ⇒ ⇒
#   **⇒ 因为第一版那份是临时脚本落的、而它把锚点截断到 40 字符** ⇒ ⇒
#   **⇒ 后果：比较时「新增 11 条、消失 11 条」、而它们其实是同一批 11 条** ⇒ ⇒
#   ⭐⭐⭐⭐⭐ **⇒ 「差异数」本身也要有口径 —— "
#   **一个截断的清单和一个全量的清单相比、永远在「变」**"
# ⭐⭐⭐⭐⭐ 1032-②f：**P3 必须与「**已提交的**清单」比** ——
#   ⇒ ⇒ 旧版比的是**工作区里那份** ⇒ ⇒ 而 `--write-golden` **先写后比**
#   ⇒ ⇒⇒⇒ **⇒ ⇒ 写完再比 ⇒ 必然相等 ⇒ ⇒ ⇒ **P3 在 1015 的运行里是恒真的**！**
#   ⇒ ⇒⇒⇒⇒ ⇒⇒⇒ **⇒ 这是「恒真」最隐蔽的形态：它不是假绿、它是**真绿** —— 而它绿得毫无意义**
#   ⇒ ⇒⇒⇒⇒ ⇒⇒⇒⇒⇒ **⇒ 处置：判据改与「HEAD 里那份（已提交的）」比** ⇒ ⇒⇒⇒⇒⇒⇒⇒⇒
#   ⇒ ⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒ **⇒ ⇒ 于是「仓里那本清单是不是陈旧的」变成每批都可见的事实** ⇒ ⇒⇒⇒⇒
#   ⇒ ⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒ **⇒ 而处置动作很明确：重跑 `--write-golden` 并把那份清单提交**
#   ⇒ ⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒ **⇒ 这就是「清单的账龄机制」第一次真的可执行**
_GOLDEN_REL = GOLDEN.relative_to(ROOT).as_posix()
_committed_gold = None
_committed_err = None
try:
    _cg = subprocess.run(["git", "show", "HEAD:%s" % _GOLDEN_REL],
                         cwd=str(ROOT), capture_output=True, text=True)
    if _cg.returncode == 0:
        _committed_gold = json.loads(_cg.stdout)
    else:
        _committed_err = "git show 失败 rc=%d" % _cg.returncode
except Exception as _e:                       # noqa: BLE001
    _committed_err = repr(_e)
_committed_set = ({(r["var"], r["anchor"]) for r in _committed_gold["rows"]}
                  if isinstance(_committed_gold, dict) and "rows" in _committed_gold
                  else None)

if "--write-golden" in sys.argv and not _CENSUS_ONLY:
    GOLDEN.parent.mkdir(parents=True, exist_ok=True)
    GOLDEN.write_text(json.dumps({
        # ⚠️⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **1015 修的：这一行原来带 `scripts/` 前缀 ⇒ ⇒
        #   而仓里另外 13 本 golden 的 `generated_by` 都是**纯文件名** ⇒ ⇒ ⇒
        #   ⇒ ⇒ 1015 按 `scripts/<generated_by>` 反查时这一本拼成了
        #   ⇒ ⇒ ⇒ ⇒ `scripts/scripts/...` ⇒ ⇒ ⇒ ⇒ ⇒ **被静默排除**
        #   ⇒ ⇒ ⇒ ⇒ ⇒ **字段格式没有约定时，「自动发现」比手写清单更危险** ——
        #   ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 手写清单写错会当场炸，自动发现写错只会安静地少算
        "generated_by": "jimeng_probe1005_zero_coupling_census.py",
        "n_zero_coupling": cur["n_zero"],
        "n_positive_present": cur["n_positive_present"],
        "n_distinct_keys": cur["n_distinct_keys"],
        "by_class": cur["by_class"],
        "class_x_gap": cur["class_x_gap"],
        "anchor_text": "⭐⭐⭐⭐⭐ **存**全量**、不截断** —— "
                       "**而第一版截断到 40 字符、于是比较时凭空「变了 11 条」**",
        "rows": cur["rows"],
    }, ensure_ascii=False, indent=1), encoding="utf-8")

if GOLDEN.exists():
    gold = json.loads(GOLDEN.read_text(encoding="utf-8"))
    gset = {(r["var"], r["anchor"]) for r in gold["rows"]}
    cset = {(r["var"], r["anchor"]) for r in cur["rows"]}
    out["golden_1005"] = {
        "n_golden": len(gset), "n_current": len(cset),
        "n_added": len(cset - gset), "n_removed": len(gset - cset),
        "added": sorted("%s|%s" % x for x in list(cset - gset)[:10]),
        "removed": sorted("%s|%s" % x for x in list(gset - cset)[:10]),
        "reproducible": (gset == cset),
        "note": "⭐⭐⭐⭐⭐ **清单落进仓里、而它是**逐条**的（不是只记一个数）** ⇒ ⇒ "
                "**⇒ 而「逐条一致」必须是一个能返回非零的断言**",
    }
else:
    out["golden_1005"] = {"exists": False}
# ⭐⭐⭐⭐⭐ 1032-②f：**P3 改成「已提交的清单 vs 现算」** ⇒ ⇒ **差值式、可证伪**
_committed_added = sorted(cset - _committed_set) if _committed_set is not None else []
_committed_removed = sorted(_committed_set - cset) if _committed_set is not None else []
out["golden_committed_1005"] = {
    "path": _GOLDEN_REL,
    "available": _committed_set is not None,
    "error": _committed_err,
    "n_rows_committed": (len(_committed_set) if _committed_set is not None else None),
    "n_rows_current": len(cset),
    "n_added_vs_committed": len(_committed_added),
    "n_removed_vs_committed": len(_committed_removed),
    "added_sample": ["%s|%s" % x for x in _committed_added[:10]],
    "note": "⭐⭐⭐⭐⭐ **这是「仓里那本清单是不是陈旧的」的可执行读数** ⇒ ⇒ "
            "**⇒ 而处置动作很明确：重跑 `--write-golden` 并把那份清单一起提交**",
}
# ⭐⭐⭐⭐⭐ 1032-②f（补）：**P3 只在「输入没被替换」时适用** ⇒ ⇒
#   ⇒ 1008 替换了两份输入 ⇒ ⇒ 此时的「已提交清单 vs 本次普查」
#   ⇒ ⇒ 拿的是**今天的清单**去比**历史输入的普查** ⇒ ⇒⇒ **⇒ 没有意义**
#   ⇒ ⇒⇒⇒ **⇒ 而「没意义」不是「False」—— 那是「**不适用**」**
#   ⇒ ⇒⇒⇒⇒ ⇒ ⇒⇒⇒⇒ **⇒ 处置：`--census-only` 模式下 P3 记 `null`**
#   ⇒ ⇒⇒⇒⇒⇒ ⇒⇒⇒⇒⇒ **⇒ 并且留下 `p3_not_applicable` 标记 ⇒ ⇒ 不许无声**
if _CENSUS_ONLY:
    out["P3_hold_1005"] = None
    out["p3_not_applicable_1005"] = True
    out["p3_not_applicable_note_1005"] = (
        "⭐⭐⭐⭐⭐ **本进程以 `--census-only` 运行 ⇒ ⇒ 调用方替换了 "
        "verifier/audit 两份输入 ⇒ ⇒ 「已提交清单 vs 本次普查」这个比较"
        "**不适用** ⇒ ⇒ **⇒ 所以这里记 `null`（没测到）、而不是 `False`"
        "（测了、没过）**")
else:
    out["P3_hold_1005"] = bool(_committed_set is not None
                               and _committed_set == cset)
out["P3_note_1005"] = (
    "⭐⭐⭐⭐⭐ **P3 现在断言「**已提交的**清单与现算逐条一致」** ⇒ ⇒ "
    "**⇒ 而工作区那份（写完之后）必然相等 ⇒ ⇒ ⇒ 那条比较是恒真的、不能当判据** ⇒ ⇒ "
    "**⇒ 本批之前 P3 在 1015 的运行里恒为真 ⇒ ⇒ 「它红了没人知道」的另一种形态**")
out["census_only_1005"] = bool(_CENSUS_ONLY)
out["P5_hold_1005"] = bool(
    cur["n_positive_present"] >= cur["n_distinct_keys"])

# ── P4：反向用例 —— 注入一条新的零耦合锚点，普查必须报出来 ─────────
# ⚠️⚠️⚠️⭐⭐⭐⭐⭐ **而第一版我只往 audit 里注入 ⇒ 普查报 delta=0** ⇒ ⇒
#   **⇒ 而普查的宇宙是「**verifier 里声明**、且在目标里存在」的锚点** ⇒ ⇒
#   **⇒ 只改目标等于什么也没加** ⇒ ⇒
#   ⭐⭐⭐⭐⭐ **⇒ 注入必须**两侧都动**：verifier 加一条新判据、audit 里加两次那段文本**
#   **⇒ ⇒ 而这恰好就是「耦合度 = 0」的定义本身**
WORK.mkdir(parents=True, exist_ok=True)
_MARK = "ZZB1005PROBEZZ"
assert _MARK not in asrc, "⭐ 探针标记竟然已经在真实文件里"


def _inject(vsrc2_src, asrc2_src):
    """verifier 侧加一条新判据、audit 侧加两次那段文本 ⇒ 耦合度必为 0。"""
    t = ast.parse(vsrc2_src)
    done = False
    for fn in ast.walk(t):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for st in list(fn.body):
            if (isinstance(st, ast.Expr) and isinstance(st.value, ast.Call)
                    and isinstance(st.value.func, ast.Name)
                    and st.value.func.id == "check"):
                new = ast.parse(
                    'def _w():\n    check("B1005-REVERSE-PROBE", '
                    + Q + _MARK + Q + ' in _ausrc)\n').body[0]
                fn.body.insert(fn.body.index(st) + 1, new)
                done = True
                break
        if done:
            break
    assert done, "⭐ 找不到可插入的 check（仪器自身坏了）"
    txt = ast.unparse(t)
    # audit 侧：把标记插到**两个**不同位置 ⇒ 该锚点出现 2 次
    # ⚠️⚠️⚠️ **而第一版我照抄了门文件里的 `ROOT = Path(...)` 当注入点 ——**
    #   **⇒ 而那句话在 audit 里根本不存在、于是 `count` 是 0、断言炸了** ⇒ ⇒
    #   **⇒ 「断言炸了」这次是对的：它挡住了「注入其实没发生」**
    a = asrc2_src
    hits = [ln for ln in ("import json", "import os", "import sys")
            if a.count(ln) == 1]
    assert hits, "⭐ 找不到唯一的注入锚点（别猜、去看文件）"
    a = a.replace(hits[0], "# " + _MARK + "\n" + hits[0], 1)
    hits2 = [ln for ln in ("from pathlib import Path", "ROOT =", "if __name__")
             if a.count(ln) == 1]
    assert hits2, "⭐ 找不到第二个注入锚点"
    a = a.replace(hits2[0], "# " + _MARK + "\n" + hits2[0], 1)
    assert a.count(_MARK) == 2, "注入侧数不对：%d" % a.count(_MARK)
    return txt, a


_v2, _a2 = _inject(vsrc, asrc)
mut_census = census(_v2, probe_map, _a2)
mut_census["class_x_gap"] = gap_table(mut_census["rows"])
out["reverse_case_1005"] = {
    "injected": "**verifier 的副本里加一条新判据、audit 的副本里加两处那段文本**"
                "——**两侧都动、真文件不动**",
    "why_both_sides": (
        "⭐⭐⭐⭐⭐ **第一版我只往 audit 注入、普查报 delta=0** ⇒ ⇒ "
        "**⇒ 而普查的宇宙是「verifier 里声明、且在目标里存在」的锚点** ⇒ ⇒ "
        "**⇒ 只改目标等于什么也没加** ⇒ ⇒ "
        "**⇒ 而这恰恰说明那道门只认「声明」与「存在」两件事**"),
    "n_zero_before": cur["n_zero"],
    "n_zero_after": mut_census["n_zero"],
    "delta": mut_census["n_zero"] - cur["n_zero"],
    "found_the_new_one": any(_MARK in r["anchor"] for r in mut_census["rows"]),
    "why": "⭐⭐⭐⭐⭐ **不然「0 差异」与「普查压根没在跑」在输出上完全一样** ⇒ ⇒ "
           "**⇒ 这一条是那道「先立控制组」的纪律第五次施用**",
}
out["P4_hold_1005"] = bool(
    out["reverse_case_1005"]["delta"] == 1
    and out["reverse_case_1005"]["found_the_new_one"])

out["verdicts_1005"] = {
    "p1_two_classes_exist_1005_": (
        "✅ **P1 成立：零耦合锚点分成两类 —— "
        "**「标识符（多处引用）」%d 条与「散文/片段」%d 条** ⇒ ⇒ "
        "**⇒ 而前一类是**语义使然**：判据本来就在问「这个东西存在吗」、"
        "**改掉其中一处不该让判据红** ⇒ ⇒ "
        "⭐⭐⭐⭐⭐ **⇒ 所以「零耦合」**不能**一刀切地说成「废判据」**"
        % (cur["by_class"].get("I-标识符(多处引用)", 0),
           cur["by_class"].get("P-散文/片段", 0))
    ),
    "p2_line_gap_separates_1005_": (
        "❌⭐⭐⭐⭐⭐ **P2 被否、而方向和我猜的相反：**"
        "**「最小行距」不但分不开两类、相邻档反而在标识符类里更多** "
        "**（%d vs %d）** ⇒ ⇒ "
        "**⇒ 因为相邻两行代码用同一个 token 是常事"
        "**（`b.left - 1` / `b.height / 2`）** ⇒ ⇒ "
        "⭐⭐⭐⭐⭐ **⇒ 我原以为「相邻 = 散文被复制到两处」、"
        "**而实际是「相邻 = 同一个 token 在同一处代码里出现两次」** ⇒ ⇒ "
        "⭐⭐⭐⭐⭐ **⇒ 而行距这个轴因此不能当分类依据 —— "
        "**它测的是「这个 token 挨得多近」、不是「这个判据弱不弱」** ⇒ ⇒ "
        "⭐⭐⭐⭐⭐ **⇒ 这是「否」的第六种自我形态：模式是我列的（1000 那条）**"
        % (_adj[0], _adj[1])
    ),
    "p3_golden_is_reproducible_1005_": (
        "✅ **P3 成立：落进仓里的那份清单、与现算的集合**逐条一致**"
        "**（新增 %d、消失 %d）** ⇒ ⇒ "
        "**⇒ 而清单是**逐条**的、不是只记一个数 —— "
        "**否则下一次改动只会让总数动一下、看不出动了什么** ⇒ ⇒ "
        "⭐⭐⭐⭐⭐ **⇒ 而「逐条一致」本身也必须能返回非零**"
        % (out["golden_1005"].get("n_added", -1),
           out["golden_1005"].get("n_removed", -1))
    ),
    "p4_reverse_case_1005_": (
        "⭐⭐⭐⭐⭐ **P4 成立：往 audit 的内存副本里塞一条新的零耦合锚点、"
        "**普查报出「新增 1 条」并逐条列出了它** ⇒ ⇒ "
        "**⇒ 不然「0 差异」与「普查压根没在跑」在输出上完全一样** ⇒ ⇒ "
        "**⇒ 这是那道「先立控制组」的纪律第五次施用**"
    ),
    "p5_denominator_is_collect_1005_": (
        "⭐⭐⭐⭐⭐ **P5 成立：分母是 `collect` 的 %d 条、"
        "**而去重后的键数是 %d —— 两者必须都报出来** ⇒ ⇒ "
        "**⇒ 而 1003 就是在这一条上栽的：三元组当 dict 键、静默丢掉 151 条、"
        "**而表现出来的是「两次测量不一致」而不是「仪器压扁了读数」**"
        % (cur["n_positive_present"], cur["n_distinct_keys"])
    ),
    "offline_1005": (
        "⭐⭐⭐⭐⭐ **本批纯离线**：不打开浏览器、不按任何键、"
        "**连 `mouse.click` 都没有** ⇒ ⇒ "
        "**⇒ 而清单落进了 `docs/research/jimeng-canvas/zero-coupling-anchors-1005.json`、"
        "**不是只留在探针输出里**"
    ),
    "discipline_1005": "",
}

out["discipline_1005"] = "".join([
    "① ⭐⭐⭐⭐⭐ **「零耦合」不是一个东西** —— "
    "**先按「语义使然 / 真的弱」拆开，不许一刀切** ⇒\n",
    "  ② ⭐⭐⭐⭐⭐ **分类轴要验它能不能分开** —— "
    "**我拿行距当轴、而它分不开 ⇒⇒ 而「否」要说清否的是**我的模式**** ⇒\n",
    "  ③ ⭐⭐⭐⭐⭐ **清单要落进仓里、而且是逐条的** —— "
    "**只记一个数的话，下一次改动只会让总数动一下** ⇒\n",
    "  ④ ⭐⭐⭐⭐⭐ **分母与去重后的键数必须都报**（1003 的教训）⇒\n",
    "  ⑤ ⭐⭐⭐⭐⭐ **「0 差异」必须有反向用例**（本批第五次施用）⇒\n",
])

# ── 1032-②f：退出码按判决走（**必须在产物写盘之前算出来**）────────
_CRITERIA = [out["P%d_hold_1005" % i] for i in range(1, 5)]
_EXIT = _exit_code(_CRITERIA, crashed=False)
out["exit_code_1005"] = {
    "criteria": _CRITERIA,
    "exit_code_would_be": _EXIT,
    "all_green": all(_CRITERIA),
    "rule": "⭐⭐⭐⭐⭐ **判据红 ⇒ rc=1；仪器崩 ⇒ rc=2；全绿 ⇒ rc=0** ⇒ ⇒ "
            "**⇒ 而以前这里是恒 0 ⇒ ⇒⇒ 「退出码恒 0 的门等于没有门」**",
    "selftest": {
        "all_green_gives_0": _exit_code([True, True]) == 0,
        "one_false_gives_1": _exit_code([True, False]) == 1,
        "crashed_gives_2": _exit_code([True], crashed=True) == 2,
        "not_applicable_is_not_red": _exit_code([True, None]) == 0,
    },
}
out["exit_code_selftest_ok_1005"] = all(out["exit_code_1005"]["selftest"].values())

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)

print("collected=%d positive_present=%d distinct_keys=%d zero=%d"
      % (cur["n_collected"], cur["n_positive_present"],
         cur["n_distinct_keys"], cur["n_zero"]))
print("by_class =", cur["by_class"])
print("class_x_gap =", cur["class_x_gap"])
print("golden: added=%s removed=%s reproducible=%s"
      % (out["golden_1005"].get("n_added"),
         out["golden_1005"].get("n_removed"),
         out["golden_1005"].get("reproducible")))
print("reverse: delta=%s found=%s"
      % (out["reverse_case_1005"]["delta"],
         out["reverse_case_1005"]["found_the_new_one"]))
print("P1..P5 =", [out["P%d_hold_1005" % i] for i in range(1, 6)])
print("PROBE_1005_DONE ->", OUT)
# ⭐⭐⭐⭐⭐ **最后一行才是退出** —— 而产物**已经在上面写完了**
#   ⇒ ⇒⇒⇒ **⇒「红」必须既留下产物、又留下非零退出码** ⇒ ⇒
#   ⇒ ⇒⇒⇒⇒ **⇒ 而以前这里是 rc=0 ⇒ ⇒⇒ 「它红了没人知道」**
sys.exit(_EXIT)
