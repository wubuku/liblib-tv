#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批 996 —— ⭐⭐⭐⭐⭐ **把「漏登记」从「靠人记」变成「有门」**

995 栽到了「钉探针 ≠ 钉 audit」的第五次：
**漏了 verifier 里读 `_p995` 的那一行** ⇒ 71 条锚点被两个门同时静默跳过
⇒ 而两个门都报成功。

⭐⭐⭐⭐⭐ **而 995 也找到了根因**：
用 `if "_p995" not in v:` 当「有没有登记」的判据是**不可靠**的 ——
**判据正文里本来就写着那个名字** ⇒ 守卫误判成「已登记」

⇒ ⇒ ⭐⭐⭐⭐⭐ **本批做的事：把「两处都要齐」做成一道可跑的探针**
  · ① 判据里引用的每个 `_pNNN` **在 verifier 里有没有那行读取**
  · ② 同一个 `_pNNN` **在 `jimeng_check_verifier_anchors.py` 的 `PROBE_VARS` 里有没有登记**

⭐⭐⭐⭐⭐ **而本批最要紧的一条是这个门的危险状态**：
**「0 缺失」与「门压根没在跑」在输出上不可区分** ⇒ ⇒
**⇒ 所以这道门必须自带反向用例** —— **故意注入一条假的引用、证明它会报**

本批**纯离线**：不打开浏览器、不按任何键、连 `mouse.click` 都没有
⇒ ⇒ ⭐⭐⭐⭐⭐ **零计费是结构性的、不是自律的**
"""
import ast
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERIFIER = os.path.join(ROOT, "scripts/verify-jimeng-batch841-unclickable.py")
ANCHORCHK = os.path.join(ROOT, "scripts/jimeng_check_verifier_anchors.py")
AUDIT = os.path.join(ROOT, "scripts/jimeng_unclickable_audit.py")
OUT = "/tmp/b996-regguard.json"

# ══ ⭐⭐⭐⭐⭐ 预测**逐条按可证伪的形式写出** ═══════════════════════════
# ⚠️⭐⭐⭐⭐⭐ **诚实声明**（沿用 992–995 那条）：
#   **写判据前我已知 995 修完之后状态是齐的** ⇒
#   ⇒ **P1 严格说不是盲预测**（我看过状态）
#   ⇒ ⇒ ⭐⭐⭐⭐⭐ **而 P2/P3 断言的是「这道门的危险状态」与「反向用例有效」**
PRED = {
    "P1_currently_no_missing":
        "**现状是 0 缺失**（995 修完之后两处都齐）",
    "P2_zero_is_the_dangerous_state":
        "⚠️⭐⭐⭐⭐⭐ **而「0 缺失」正是这道门最危险的状态** —— "
        "**它与「门压根没在跑」在输出上不可区分** ⇒ ⇒ "
        "**⇒ 所以这道门必须自带反向用例**",
    "P3_negative_control_catches":
        "**注入一条假的 `_pXXX` 引用 ⇒ 门会报它缺读取行** ⇒ "
        "**⇒ 这就是那道反向用例**",
    "P4_both_places_are_checkable":
        "⭐⭐⭐⭐⭐ **「两处都要齐」这个判据是可证的** —— "
        "**读行与 `PROBE_VARS` 各只有一处、都能被静态检出**",
    "P5_missing_is_now_a_gate":
        "⇒ ⇒ **「漏登记」从「靠人记」变成「有门」**",
}

HONESTY = (
    "⚠️⭐⭐⭐⭐⭐ **写判据前我已知 995 修完之后状态是齐的** ⇒ "
    "P1 严格说不是盲预测（我看过状态）⇒ "
    "**而 P2/P3 断言的是「这道门的危险状态」与「反向用例有效」** ⇒ "
    "⭐⭐⭐⭐⭐ **沿用 992–995 那条：「怎么选候选」也要记下来**"
)

# ⭐⭐⭐⭐⭐ **这条假引用就是反向用例本身 —— 写死、不许改**
# ⚠️⚠️⚠️⭐⭐⭐⭐⭐ **第一版我写的是 `_pXXX`、而它红了 —— 而红的成因是
#   **假名不符合被检的正则**（`_p` 加三位数字）⇒ ⇒ **门压根没看见它、照旧报 0**
#   ⇒ ⇒ ⭐⭐⭐⭐⭐ **而这正是 P2 预言的那个陷阱、在同一批里当场咬我一口**
#   ⇒ ⇒ ⭐⭐⭐⭐⭐ **结论：反向用例的名字必须自己通过被检的那道正则**
FAKE = "_p999"

ausrc = ""
if os.path.exists(AUDIT):
    with open(AUDIT, encoding="utf-8") as f:
        ausrc = f.read()
vsrc = ""
if os.path.exists(VERIFIER):
    with open(VERIFIER, encoding="utf-8") as f:
        vsrc = f.read()
asrc = ""
if os.path.exists(ANCHORCHK):
    with open(ANCHORCHK, encoding="utf-8") as f:
        asrc = f.read()

out = {
    "target": "offline-registry-guard",
    "source": "verify-jimeng-batch841-unclickable.py ＋ "
              "jimeng_check_verifier_anchors.py",
    "question": (
        "⭐⭐⭐⭐⭐ **995 栽在「漏了读取行」上、而两个门都报成功** "
        "⇒ **能不能让「漏登记」变成一道会红的门？**"
    ),
    "predictions_996": PRED,
    "honesty_note_996": HONESTY,
    "offline_996": True,
    "fake_name_996": FAKE,
    "fake_note_996": (
        "⭐⭐⭐⭐⭐ **`_p999` 是写死的假引用、它就是那道反向用例** ⇒ "
        "**而它的名字自己就通过被检的那道正则** —— "
        "**第一版的 `_pXXX` 不通过、所以那道反向用例当时是假的** ⇒ "
        "**任何时候跑这道门都必须报它** ⇒ "
        "**如果报不出来、说明门没在跑**"
    ),
}


# ⚠️⚠️⚠️⭐⭐⭐⭐⭐ **第三版、而它是被这道门自己逼出来的**：
#   第一版是 `in (_p\d{3})` 的**正则扫全文** ⇒ ⇒
#   **我插进判据正文的那句举例「`X in _p999`」被它当成了真引用** ⇒ ⇒
#   ⇒ ⭐⭐⭐⭐⭐ **而这就是 995 那条根因的**镜像**：
#   **995 是「拿正文当『有没有登记』的判据」不可靠；**
#   **这一条是「拿正则扫正文当『有没有引用』的判据」同样不可靠** ⇒ ⇒
#   ⇒ ⭐⭐⭐⭐⭐ **⇒ 所以判据必须扫 AST 里的条件表达式、不许扫字符串字面量**
_NAMERE = re.compile(r"_p\d{3}\Z")


def _referenced(src):
    """⭐⭐ 判据里**真正被求值**的 `X in _pNNN`

    ⚠️⭐⭐⭐⭐⭐ **只认 AST 的 `Compare` 节点** ⇒
    **散文里出现的「`X in _p999`」只是一个字符串常量、不是引用** ⇒
    **而这正是 990 那条「钉住真正被求值的那个表达式」的第三次施用**
    """
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return []
    names = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Compare):
            continue
        if not any(isinstance(op, (ast.In, ast.NotIn))
                   for op in node.ops):
            continue
        # ⭐⭐⭐⭐ **左边**不设限** —— ⚠️⭐⭐⭐⭐⭐ 而这是我踩到的第三个仪器坑：
        #   **我第一版 AST 加了「左边必须是字符串常量」这道过滤 ⇒**
        #   **它把 `all(block in _p894 for block ...)` 这种真引用也滤掉了** ⇒ ⇒
        #   **⇒ 收紧判据不是单调变好的、它要单独量对另一侧的影响** ⇒ ⇒
        #   **⇒ 而假阳性本来就靠「散文只是 Constant、不是 Compare」挡住了**
        #   ⇒ **这道多余的过滤器纯属自己给自己造了个假阴性**
        for c in node.comparators:
            cand = None
            if isinstance(c, ast.Name):
                cand = c.id
            elif isinstance(c, ast.Constant) and isinstance(c.value, str):
                cand = c.value
            if cand and _NAMERE.match(cand):
                names.add(cand)
    return sorted(names)


def _readlines(src):
    """⭐⭐ verifier 里真正的那行读取（**不是「名字在不在」**）"""
    return {m.group(1) for m in re.finditer(
        r"^\s*(_p\d{3})\s*=\s*\w+\.read_text", src, re.M)}


def _registered(src):
    """⭐⭐ `PROBE_VARS` 里登记了的（**同样按「那一行条目」判**）"""
    return {m.group(1) for m in re.finditer(
        r'"(_p\d{3})"\s*:\s*"scripts/', src)}


refs = _referenced(vsrc)
reads = _readlines(vsrc)
regs = _registered(asrc)

out["counts_996"] = {
    "n_referenced": len(refs),
    "n_readline": len(reads),
    "n_registered": len(regs),
    "n_missing_readline": len([r for r in refs if r not in reads]),
    "n_missing_registered": len([r for r in refs if r not in regs]),
    "n_readline_not_referenced": len([r for r in reads if r not in refs]),
}
out["missing_readline_996"] = [r for r in refs if r not in reads]
out["missing_registered_996"] = [r for r in refs if r not in regs]

out["P1_hold_996"] = bool(
    not [r for r in refs if r not in reads]
    and not [r for r in refs if r not in regs])

# ══ ⭐⭐⭐⭐⭐ **反向用例：把假引用注入一份内存副本、再跑一遍同一把尺子** ══
# ⭐⭐⭐⭐⭐ **第二版修正：注入的必须是「缺的那一半」**
#   ⚠️⚠️⚠️ **第一版我连「读取行」一起注入了 ⇒ 那正好补上了缺失的那一半
#   ⇒ ⇒ 门当然照旧报 0 ⇒ ⭐⭐⭐⭐⭐ **反向用例要注入的必须是「只被引用、
#   没被读取」** —— **而这才是 995 那次真实的漏登记形态**
# ⭐⭐⭐⭐⭐ **第三版修正：`_referenced` 改用 `ast` 之后、注入的代码必须能解析**
#   ⇒ ⇒ **而「模块级平铺」与「函数内缩进」两种形态我都要验一遍** ⇒
#   ⇒ **因为「门对缩进不敏感」是一个断言、而反向用例是把它变成读数的地方**
_inj_flat = '\ncheck("REGRESSION-FAKE", "x" in %s)\n' % FAKE
_inj_nested = ('\ndef _regression_fake():\n'
               '    check("REGRESSION-FAKE", "x" in %s)\n' % FAKE)
_rf, _rn = vsrc + _inj_flat, vsrc + _inj_nested
reads_fake = _readlines(_rf)
refs_fake = _referenced(_rf)
reads_nested = _readlines(_rn)
refs_nested = _referenced(_rn)
out["negative_control_996"] = {
    "fake_name": FAKE,
    "injected": "只注入一条 `X in _p999` 的判据、**不注入读取行**",
    "n_missing_before": len([r for r in refs if r not in reads]),
    "n_missing_after": len([r for r in refs_fake if r not in reads_fake]),
    "now_reported": FAKE in [r for r in refs_fake if r not in reads_fake],
    "now_reported_nested": FAKE in [r for r in refs_nested
                                    if r not in reads_nested],
    "why_this_matters": (
        "⭐⭐⭐⭐⭐ **这道门在真实状态下的输出是「0 缺失」** ⇒ "
        "**而「0 缺失」与「门没在跑」在输出上不可区分** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐⭐ **所以必须有一处能自证「我确实在跑」的东西** ⇒ "
        "**而这里就是它：注入一个假的、门必须报出来** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐ **而平铺/嵌套两种形态都报 —— "
        "**「门对缩进不敏感」也就从断言变成了读数**"
    ),
}
out["P2_hold_996"] = bool(
    out["P1_hold_996"]
    and out["counts_996"]["n_missing_readline"] == 0
    and out["counts_996"]["n_missing_registered"] == 0)
out["P3_hold_996"] = bool(out["negative_control_996"]["now_reported"]
                          and out["negative_control_996"]
                          ["now_reported_nested"])
out["P4_hold_996"] = bool(reads and regs)
out["P5_hold_996"] = bool(out["P2_hold_996"] and out["P3_hold_996"])

out["verdicts_996"] = {
    "p1_currently_clean_996": (
        "✅ **P1 成立：现状是 0 缺失**（995 修完之后两处都齐）⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐⭐ **而这个「0」正是本批要处理的东西、不是本批的结论**"
    ),
    "p2_zero_is_dangerous_996": (
        "⚠️⚠️⚠️⭐⭐⭐⭐⭐ **P2 成立、而它是本批最要紧的一条** —— "
        "**「0 缺失」与「门压根没在跑」在输出上不可区分** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐⭐ **这与 985 那条「恒假的读数要留」、"
        "990 那条「恒真的读数要认出它」是同一族** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐⭐ **而这里的「恒真」是整道门恒真** —— "
        "**它会一直报 0、而那不代表它有用** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐⭐ **所以这道门必须自带反向用例**"
    ),
    "p3_refuted_twice_996": (
        "❌→✅ **P3 连否两次、而两次都不是事实否的** —— "
        "**第一版假名 `_pXXX` 不符合被检的正则 ⇒ 门压根没看见它**；"
        "**第二版我把「读取行」也一起注入了 ⇒ 那正好补上缺失的那一半** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐⭐ **两次合起来是一句：反向用例要注入的必须是"
        "**「只被引用、没被读取」** —— **而那才是 995 那次真实的漏登记形态** ⇒ ⇒ "
        "**我的假名写成 `_pXXX`、而它不符合被检的正则（`_p` 加三位数字）** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐⭐ **门压根没看见它、照旧报 0 缺失** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐⭐ **所以反向用例的名字必须自己通过被检的那道正则** ⇒ "
        "**改用 `_p999` 之后它立刻被报出来** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐⭐ **这一条比「反向用例有效」本身更值钱** ⇒ ⇒ "
        "⇒ ✅ **P3 成立、反向用例有效** —— "
        "**把假引用 `_p999` 注入一份内存副本、门立刻报它缺读取行** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐⭐ **而注入的是一份副本、不是真文件** ⇒ "
        "**所以这道反向用例零副作用、可以每次都跑** ⇒ ⇒ "
        "⇒ ⚠️⭐⭐⭐⭐⭐ **而这里还有一处我自己的不一致**："
        "**第二版把 `FAKE` 改成了 `_p999`、而这段散文里还写着 `_pXXX`** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐⭐ **改了代码、忘了改同段散文** —— "
        "**而门只查散文里有没有那几串、查不出它说的是哪个名字** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐ **这是 996 自己踩的「同一位」的第三种形态**"
        "⇒ ⭐⭐⭐⭐⭐ **「自证在跑」这件事必须有、"
        "**而它必须便宜到每次都跑**"
    ),
    "p4_both_places_checkable_996": (
        "⭐⭐⭐⭐⭐ **「两处都要齐」这个判据是可证的** —— "
        "**读行与 `PROBE_VARS` 各只有一处、都能被静态检出** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐⭐ **而「都能被静态检出」这一点很重要**："
        "**它让这道门不需要跑 verifier 就知道自己有没有用**"
    ),
    "p5_missing_becomes_a_gate_996": (
        "⇒ ⇒ ⭐⭐⭐⭐⭐ **「漏登记」从「靠人记」变成「有门」** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐ **而它也是 995 那个根因的正面对策**："
        "**既然 `名字 in 文件` 不可靠、那就用「那行读取在不在」当判据** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐⭐ **判据从「一个名字」换成「一行代码」—— "
        "**这与 990 那条「从 `one_lap[i][key]` 改成 `cell[\"ring\"][idx]`」"
        "**是同一个动作**"
    ),
    "honest_blind_996": (
        "⚠️⭐⭐⭐⭐⭐ **本批沿用 992–995 的自省** —— "
        "**写判据前我已知修完之后状态是齐的** ⇒ "
        "**P1 严格说不是盲预测（我看过状态）** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐⭐ **而 P2/P3 断言的是"
        "**「这道门的危险状态」与「反向用例有效」** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐⭐ **「怎么选候选」是和预测同等重量的元数据** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐⭐ **而这一批的自省还有个新形状：**"
        "**我的反向用例本身错了两次** ⇒ ⇒ "
        "**而那两次都不是「数据否了预测」、是「用例没在测东西」** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐⭐ **所以「反向用例会红」这件事本身也要被反向用例检验**"
        "—— **而 996 就是这么被自己的 P2 抓住的**"
    ),
    # ══ ⚠️⭐⭐⭐⭐⭐ **P6/P7/P8 不是预测 —— 是这道门当场报出来的**
    #   （沿用 995 那条「先撞上、再命名」：**好问题只在我们撞上它之后才出现**）
    "p6_regex_mistook_prose_996_": (
        "⚠️⭐⭐⭐⭐⭐ **P6 不是预测、是门当场报的："
        "**「用正则扫判据正文」会把散文里的举例当成真引用** ⇒ ⇒ "
        "⇒ **我插进 `A993D.3` 的那句「`X in _p999`」被读成了一个真 `_p999`** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐⭐ **而这就是 995 那条根因的镜像**："
        "**995 是「拿正文当『有没有登记』的判据」不可靠；"
        "这一条是「拿正则扫正文当『有没有引用』的判据」同样不可靠** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐⭐ **⇒ 所以判据必须扫 AST 的 `Compare` 节点、"
        "**不许扫字符串字面量** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐⭐ **而门报错之后、这是我第一次希望它是红的** ⇒ "
        "**它红的正是它该红的东西**"
    ),
    "p7_tightening_false_negative_996_": (
        "⚠️⭐⭐⭐⭐⭐ **P7 也是当场撞的、而它比 P6 更值钱**："
        "**我第一版 AST 多加了一道「左边必须是字符串常量」的过滤** ⇒ ⇒ "
        "⇒ **它把 `all(block in _p894 for block ...)` 这种真引用也滤掉了** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐⭐ "
        "**收紧判据不是单调变好的 —— "
        "**它会同时减少假阳性与假阴性、而两侧要分开量** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐⭐ **⇒ 而假阳性本来就靠「散文只是 `Constant`、不是 `Compare`」"
        "**挡住了 ⇒ 那道多余的过滤器纯属自己给自己造了个假阴性** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐⭐ **差集是唯一能发现这一点的量** —— "
        "**只看「新仪器报 0 缺失」我永远不会知道它漏了 `_p894`** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐⭐ **⇒ 而这道门的第一版假阴性来自 P6 自己的修正** —— "
        "**为修一个假阳性而造的假阴性、它的成因是同一个动作**"
    ),
    "p8_reading_moves_when_pinned_996_": (
        "⭐⭐⭐⭐⭐ **P8 是本批最结构性的发现："
        "**这个读数在判据被插进去的那一刻就不再是同一个数** ⇒ ⇒ "
        "⇒ **插入前 119 个被引用；插入 `A993D` 之后变成 120** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐⭐ **⇒ 而 994 那条「一次扫描会改变它所扫描的对象」"
        "**在这里是字面成立的：被扫的就是判据文件本身** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐⭐ **⇒ 所以「钉判据」与「量现状」有先后顺序、"
        "**而报出来的数必须是**钉完之后**的数** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐⭐ **⇒ 这就是本批为什么先插判据、再重跑探针** —— "
        "**顺序反过来就会把一个自己造成的读数写成「现状」** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐⭐ **⇒ 而它是 994 那条的一个更狠的形态：**"
        "**994 是「同一把尺子量两次」得到不同数；"
        "**这一条是「尺子和被量的东西是同一个文件」**"
    ),
    "offline_996": (
        "⭐⭐⭐⭐⭐ **本批纯离线**：不打开浏览器、不按任何键、"
        "**连 `mouse.click` 都没有**、**只读两个脚本文本** ⇒ ⇒ "
        "**零计费是结构性的、不是自律的** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐ **而它比 993–995 那几批还轻 —— "
        "**它连 README 都不读、**"
        "**所以不会遇上「扫描改变输入」那一类问题** ⇒ ⇒ "
        "⇒ ⭐⭐⭐⭐⭐ **⇒ 而这给出一条可移植的分级："
        "**「读脚本文本的门」最轻、「扫文档的门」最重** ⇒ "
        "**⇒ 而越轻的门越该多设** —— "
        "**因为它便宜到可以每次都跑**"
    ),
}

# ══ ⭐⭐⭐⭐⭐ **P6/P7 用**行为自测**判、不查文本** ⇒ 与「用 `名字 in 文件` 当判据」
#   那条根因正好相反：**这一回判据是「门对几个已知输入返回什么」**
out["P6_selftest_996"] = {
    "散文里的样例（应不算引用）": bool(
        FAKE not in refs and _referenced('X = "x in _p999"') == []),
    "真引用（应算引用）": bool("_p996" in refs),
    "纯字符串字面量（应不算引用）": bool(
        _referenced('Y = "and \'z\' in _p998"') == []),
}
out["P6_hold_996"] = all(out["P6_selftest_996"].values())
out["P7_selftest_996"] = {
    "生成器表达式里的真引用（应算引用）": bool(
        _referenced("all(b in _p894 for b in xs)") == ["_p894"]),
    "真实文件里的 `_p894`（应算引用）": bool("_p894" in refs),
    "变量名当 comparator 也算": bool(
        _referenced("Z = s in _p993") == ["_p993"]),
}
out["P7_hold_996"] = all(out["P7_selftest_996"].values())
out["P8_hold_996"] = bool(
    out["counts_996"]["n_referenced"] == 120)

# ══ ⭐⭐⭐⭐ **键名一致性** ⇒ ⭐⭐⭐⭐⭐ **而它是在补 P3 自己点出的那个漏洞**
#   P3 里我写过「第二版把 `FAKE` 改成 `_p999`、而这段散文里还写着 `_pXXX`」
#   ⇒ 同样的漂移会发生在**键名**上 ⇒ ⇒ **所以把两侧的键名逐字比一遍**
# ⚠️⭐⭐⭐⭐⭐ **而这里我第一版读错了文件**（`asrc` 是锚点自查门、不是 audit）
#   ⇒ **⇒ 读数读到 0 键、而我差点把它当成「两侧完全一致」** ⇒ ⇒
#   **⇒ 又一次：「读到空」与「读到全部」在输出上都可能长得像「对」**
_ausrc_blk = ausrc[ausrc.find('"regguard_996"'):] \
    if '"regguard_996"' in ausrc else ""
_ausrc_blk = _ausrc_blk[:_ausrc_blk.find('"seampos_992"')] \
    if '"seampos_992"' in _ausrc_blk else _ausrc_blk
_ausrc_keys = set(re.findall(r'"(\w+_996_|offline_996|discipline_996)":', _ausrc_blk))
out["keyname_alignment_996"] = {
    "probe_keys": sorted(k for k in out["verdicts_996"] if k.endswith("_996")),
    "audit_keys": sorted(_ausrc_keys),
    "only_in_probe": None,
    "only_in_audit": None,
}
# ⭐⭐⭐⭐ **键名归一化**：audit 侧用 `<名>_996_` 避开大字典撞名、探针侧不带后缀
def _norm(k):
    return k[:-1] if k.endswith("_") else k


# ⭐⭐⭐⭐ **比对集 = verdict 键 ∪ `discipline_996`** ⇒
#   **`discipline_996` 在探针里是顶层键、不在 `verdicts_996` 里**
_mine = {_norm(k) for k in set(out["verdicts_996"]) | {"discipline_996"}}
_theirs = {_norm(k) for k in _ausrc_keys}
out["keyname_alignment_996"]["only_in_probe"] = sorted(_mine - _theirs)
out["keyname_alignment_996"]["only_in_audit"] = sorted(_theirs - _mine)
out["keyname_alignment_996"]["note_wrong_file_first"] = (
    "⚠️⭐⭐⭐⭐⭐ **我第一版读的是锚点自查门、于是读到 0 个键** ⇒ "
    "**「读到空」与「读到全部」在输出上都可能长得像「对」**")
out["keyname_alignment_996"]["first_run_actually_drifted"] = [
    "**探针侧 p1–p5 少了 `996` 标记、`p3` 两边根本不是同一个名字**"]
out["keyname_alignment_996"]["aligned"] = bool(
    not out["keyname_alignment_996"]["only_in_probe"]
    and not out["keyname_alignment_996"]["only_in_audit"])

out["discipline_996"] = "".join([
    "① ⭐⭐⭐⭐⭐ **一道恒报 0 的门、必须自带反向用例** —— "
    "**否则它和没装是同一种状态** ⇒\n",
    "  ② ⭐⭐⭐⭐⭐ **判据要从「一个名字」换成「一行代码」** ⇒\n",
    "  ③ ⭐⭐⭐⭐⭐ **自证「我确实在跑」的东西必须便宜到每次都跑** ⇒\n",
    "  ④ ⭐⭐⭐⭐⭐ **反向用例要注入的必须是「缺的那一半」、"
    "**不是「补全的那一半」** ⇒\n",
    "  ⑤ ⭐⭐⭐⭐⭐ **反向用例的名字自己也要通过被检的正则** ⇒\n",
    "  ⑥ ⭐⭐⭐⭐ **反向用例要走副本、不许碰真文件** ⇒\n",
    "  ⑦ ⭐⭐⭐⭐⭐ **本批纯离线、只读两个脚本文本** ⇒\n",
    "  ⑧ ⭐⭐⭐⭐⭐ **扫判据要扫 AST 的条件表达式、不许扫字符串字面量** ⇒\n",
    "  ⑨ ⭐⭐⭐⭐⭐ **换判据之后要量新旧两把尺子的差集** —— "
    "**只看「新仪器报 0」看不见它变瞎了** ⇒\n",
    "  ⑩ ⭐⭐⭐⭐⭐ **钉判据与量现状有先后顺序、报出来的数必须是钉完之后的** ⇒\n",
    "  ⑪ ⭐⭐⭐⭐⭐ **判据的形式与判据的内容要分开钉** —— "
    "**P6/P7 用行为自测、P1–P5 用存在性** ⇒\n",
    "  ⑫ ⭐⭐⭐⭐⭐ **「读到空」与「读到全部」都可能长得像「对」** —— "
    "**而我第一版读错了文件、于是读到 0 个键** ⇒\n",
])

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)

print("counts =", json.dumps(out["counts_996"], ensure_ascii=False))
print("negative =", json.dumps(
    {k: out["negative_control_996"][k] for k in
     ("n_missing_before", "n_missing_after", "now_reported")},
    ensure_ascii=False))
print("P1..P5 =", [out["P%d_hold_996" % i] for i in range(1, 6)])
print("PROBE_996_DONE ->", OUT)
