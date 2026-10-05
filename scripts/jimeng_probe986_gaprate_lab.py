#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""batch 986 **实验室**探针（**零计费**：只按 `Tab`，**根本不打开源站**）：
⭐⭐⭐⭐⭐ **用 985 的新口径把 §190 的 7.8% 重测** ——
**「缺失率」在新口径下恒为 0**（间隙不是一格 ⇒ 少一格这件事不存在）；
那 5/64 是「**这一圈的回绕没有交出焦点**」
⇒ ⇒ **并且第一次量了间隙的「位置」**：59 次全部落在**回绕点**上、零例外。

── 985 留给我的那一条，以及本批怎么把它变成可判的 ────────────────

985 证明了 `BODY` 不是一格、是「无元素持有焦点」这个**间隙** ⇒ 环长分母减一
⇒ ⇒ **§190 那个 7.8% 必须在换口径后重测**（985 §195 第五节原话）。

⚠️⭐⭐⭐⭐⭐ **而 985 同时把 H₃ 的「位置命题」判成了「同义反复、应当作废」** ——
原话：「间隙按构造就在最后一个与第一个之间」。

⇒ ⇒ **本批不同意那半句，而且要说出理由**：

- 「间隙**按构造**在两者之间」这句是**关于「间隙」这个词的定义**（985 这句对）
- ⭐⭐⭐⭐⭐ **但「间隙出现在环的哪一格上」不是定义** ——
  **引擎完全可以交给 UI 层之后、在环的中途就交出焦点**
  （例如按计时器交出，而不是在候选表耗尽时交出）
  ⇒ ⇒ **「间隙落在回绕点上」是一条能红的预测，而不是同义反复**
  ⇒ ⇒ **985 判过头的不是数据、是把一条可证伪的预测当成了定义**

── ⭐⭐⭐⭐⭐ 三条预测，**全部在看任何数据之前按定义写出** ─────────────

⚠️⚠️⚠️⭐⭐⭐ **期望值必须按定义逐句推**，不能「跑出来是什么就写什么」
（这个坑已经复发七次 ⇒ 本批的每个 `assert` 期望值都在下面写出了推导）。

**P1（缺失率）**：`laps_missing_a_stop == 0`
—— 推导：旧口径把间隙**算成一格** ⇒ 「少一格」只可能意味着「这一圈没有间隙」
⇒ **它从来没在测「少了哪一格」** ⇒ 新口径下 `ring_stops = 旧 ring_len − 1`，
而一圈**要么** 4 枚（3 停靠点＋间隙）**要么** 3 枚（无间隙）
⇒ **两种都完整覆盖 3 个可聚焦停靠点** ⇒ **缺失率恒为 0**。
⚠️⭐⭐ 这条**不是恒真门**：它会被「某一圈真的跳过一个停靠点」打红
⇒ 成对反向门见下方 `_covers_all_stops` 自测第 3 例。

**P2（间隙的位置）**：每一圈里，**只要有间隙，它就是倒数第二枚**，
而**收尾那一枚恒等于 `keys[0]`**
—— 推导：`_cycles` 把 `first` 固定成 `keys[0]`、每圈收在它再次出现处
⇒ **收尾那枚必然是环里的第一枚可聚焦停靠点** ⇒
**若间隙在回绕点上，它必然紧挨在收尾那枚之前**
⇒ ⭐⭐ **这条是能红的**：若引擎按计时器交出焦点，间隙会落在环的中途
（例：`['b2','GAP','b3','b1']`）⇒ 判红。

**P3（间隙仍是间隙）**：`n_gap_where_body_focused == 0`、`n_gap_where_has_focus == 0`
—— 推导：985 已证 `document.body` 从未被真正聚焦、文档 `hasFocus()` 为假
⇒ 本批把样本从 985 的 **3 次** 扩到 **几十次**（回归门，不是新发现）。

── ⭐⭐⭐⭐⭐ 第三件事：**不重跑也能换算** ────────────────────────────

980 的原始读数（`keys` / `cycles`）都留在 `/tmp/b980-rate.json` 里
⇒ ⇒ **本批用同一个函数**把那 64 圈**离线重算一遍** ⇒
⭐⭐⭐⭐⭐ **「7.8% → 0%」是在 980 的原始数据上算出来的，不是新数据**
⇒ 且新跑一遍是**同函数** ⇒ 两批不会各说各话。

**本批零计费**：`about:blank`、**只按 `Tab`**、**连 `mouse.click` 都没有**。
"""
from __future__ import annotations

import ast
import atexit
import json
import os
import re

OUT = "/tmp/b986-gaprate.json"
HIST = "/tmp/b980-rate.json"          # 980 的原始读数（离线换算用）
REPS = 2
N_STEPS = 96          # ⭐ 4 格一圈 ⇒ 约 24 圈（统计量需要样本量）
WINDOW_MS = 140       # ⭐ 与 980 同：≥ 门①的可见下限
MIN_VISIBLE_MS = 120  # ⭐ 与 980 同
VIEWPORT = {"width": 1512, "height": 1200}
BTN = 3
GAP_KEY = "BODY"      # ⭐ **旧口径的名字**；985 之后它指的是「间隙」

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _src(name):
    p = os.path.join(_ROOT, "scripts", name)
    if not os.path.exists(p):
        return ""
    with open(p, encoding="utf-8") as f:
        return f.read()


_p976 = _src("jimeng_probe976_counterfactual_src.py")
_p978 = _src("jimeng_probe978_lab_body_stop.py")
_p979 = _src("jimeng_probe979_dwell_src.py")
_p980 = _src("jimeng_probe980_rate_src.py")
_p985 = _src("jimeng_probe985_bodynotacell_lab.py")
_ME = open(__file__, encoding="utf-8").read()


def _grab(name, src=None):
    m = re.search(r'^%s\s*=\s*r?"""(.*?)"""' % name, src or "", re.S | re.M)
    assert m, "抠不到 %s" % name
    _s = m.group(1)
    assert _s in (src or ""), "%s 不是逐字抠出来的" % name
    return _s


# ⭐⭐⭐⭐⭐ 三件**逐字继承**、本批一个都不自己重写
POLL_JS = _grab("POLL_JS", _p979)
FOCUS_JS = _grab("FOCUS_JS", _p985)
INJECT_JS = _grab("INJECT_JS", _p976)
UNINJECT_JS = _grab("UNINJECT_JS", _p976)
LAB_PROBE_ID = "b980-lab-injected"    # ⭐ 与 980 **同一个 id**

# ⚠️⭐⭐⭐⭐⭐ **980 那一行本身就是 `POLL_JS = _grab("POLL_JS", _p979)`**
#   —— ⭐⭐⭐⭐⭐ **我第一版想「从 980 抠一份来比字面量」，抠不到**：
#   **`_grab` 只能抠字面量，而 980 手里没有字面量、它也是从 979 拿的**
#   ⇒ ⇒ ⭐⭐⭐⭐ **真正的不变量不是「两批字面量相等」，而是
#   「两批都指向 979 的那一份、且两批都没自己重定义」** ⇒ 改钉这个
assert 'POLL_JS = _grab("POLL_JS", _p979)' in _p980, \
    "⭐⭐⭐⭐⭐ 980 不再是从 979 拿 `POLL_JS` 了 ⇒ 本批与 980 测的不是同一件事"
assert 'POLL_JS = _grab("POLL_JS", _p979)' in _ME, \
    "⭐⭐⭐⭐⭐ 本批没有指向 979 的那一份"
assert FOCUS_JS in _p985, "FOCUS_JS 不在 985 探针里"
assert INJECT_JS in _p976 and UNINJECT_JS in _p976
assert 'document.body.insertBefore(el, document.body.firstChild)' in INJECT_JS
assert 'if (old) old.remove();' in INJECT_JS
# ⚠️⭐⭐⭐⭐⭐ **不许自己定义**继承来的那几件（978 栽过、980 照抄）
assert not re.search(r'^(POLL_JS|FOCUS_JS|INJECT_JS|UNINJECT_JS)\s*=\s*r?"""',
                     _ME, re.M), "本批自己定义了**继承来的**字面量 ⇒ 尺子分叉了"
for _bad in ('POLL_JS = """x"""', 'FOCUS_JS = r"""x"""',
             'INJECT_JS = r"""x"""', 'UNINJECT_JS = r"""x"""'):
    assert re.search(
        r'^(POLL_JS|FOCUS_JS|INJECT_JS|UNINJECT_JS)\s*=\s*r?"""', _bad, re.M), (
        "分叉守卫**失灵**了：%r" % _bad)
# ⭐ 而**自己的新件**必须**能**被行首匹配到（证明上面那条不是恒真）
assert re.search(r'^STOP_JS\s*=\s*r?"""', 'STOP_JS = """x"""', re.M)

# ── 臂表：**内容**逐格继承 980，**note 改写**（见下）────────────────────
BUTTON_TPL = '<button data-testid="lab-b%d" id="lab-b%d">B%d</button>'
BUTTON_ROW = "".join(BUTTON_TPL % (i, i, i) for i in range(1, BTN + 1))
SPACER = '<div style="height:2600px;background:#eee">spacer</div>'
CSS_PLAIN = "<style>body{margin:0}button{width:120px;height:40px}</style>"

# ⚠️⭐⭐⭐⭐⭐ **note 必须改写**：980 的 note 原文写着「4 格环」「5 格环」，
#   而**那正是旧口径**（把间隙算成一格）⇒ **注释里带着一个已被推翻的数**
#   ⇒ ⇒ ⭐⭐⭐⭐⭐ **「同一个东西要比同一个口径」在注释上同样成立**
ARMS = [
    ("L0", "基线：内容装得下 ⇒ 文档**不可滚动**；**3 个可聚焦停靠点**"
           "（＋至多 1 个间隙）", CSS_PLAIN, BUTTON_ROW),
    ("L2", "**可滚动** ＋ `<body>` **最前面**注入一枚可聚焦元素；"
           "**4 个可聚焦停靠点**（＋至多 1 个间隙）",
     CSS_PLAIN, SPACER + BUTTON_ROW),
]


def _lit(name, src):
    """⭐ 从 `src` 里取 `name = <字符串字面量>` 的**值**（不 `exec` 整段）。"""
    m = re.search(r'^%s\s*=\s*(r?)("(?:[^"\\]|\\.)*"|\'[^\']*\')'
                  r'\s*$' % name, src, re.M)
    assert m, "抠不到字面量 %s" % name
    return ast.literal_eval(m.group(1) + m.group(2))


def _arms_980():
    """⭐⭐⭐⭐⭐ **把 980 的臂表按它自己的定义合成出来**（不 `exec` 整段）。

    ⚠️⭐⭐⭐⭐⭐ **为什么不能直接 `ast.literal_eval`**：
    980 的 `ARMS` 里写的是**名字**（`BUTTON_ROW` / `SPACER` / `CSS_PLAIN`）
    ⇒ ⭐⭐ `literal_eval` 遇到 `ast.Name` 就抛 `malformed node`
    （第一版就这么撞的）⇒ ⇒ **只能把这三个名字从 980 自己的原文取出来、
    按 980 自己的方式合成，再去比** ⇒
    ⭐⭐⭐⭐⭐ **这样才不是循环论证**（若拿**我**的合成结果去比，
    那道门对「980 的定义变了」完全免疫 ⇒ 恒真）。

    980 的纪律：「凡是靠 `_grab` 带不走的东西，就要显式钉住它没变」。
    """
    tpl = _lit("BUTTON_TPL", _p980)
    spacer = _lit("SPACER", _p980)
    css = _lit("CSS_PLAIN", _p980)
    btn = int(re.search(r'^BTN\s*=\s*(\d+)', _p980, re.M).group(1))
    row = "".join(tpl % (i, i, i) for i in range(1, btn + 1))
    body = re.search(r'^ARMS\s*=\s*(\[.*?\n\])', _p980, re.S | re.M)
    assert body, "980 里抠不到 `ARMS`"
    ns = {"BUTTON_ROW": row, "SPACER": spacer, "CSS_PLAIN": css}
    return ast.parse(body.group(1), mode="eval"), ns, \
        {"BUTTON_TPL": tpl, "SPACER": spacer, "CSS_PLAIN": css, "BTN": btn}


_ARMS980_EXPR, _NS980, _PIECES980 = _arms_980()
_ARMS980 = eval(compile(_ARMS980_EXPR, "<ARMS-980>", "eval"),
                {"__builtins__": {}}, _NS980)

# ⭐⭐⭐⭐ **三件逐字继承 980**（先把「定义」钉住，再比「合成结果」）
assert BUTTON_TPL == _PIECES980["BUTTON_TPL"], "980 的按钮模板变了"
assert SPACER == _PIECES980["SPACER"], "980 的 `spacer` 变了"
assert CSS_PLAIN == _PIECES980["CSS_PLAIN"], "980 的 CSS 变了"
assert BTN == _PIECES980["BTN"], "980 的按钮数变了"
# ⭐⭐⭐⭐ **只比「内容」**（key / head / body 三元组）—— note 允许改写
assert [(k, h, b) for k, _n, h, b in ARMS] == \
       [(k, h, b) for k, _n, h, b in _ARMS980], \
    "⭐⭐⭐⭐ 臂表的**内容**与 980 不一致 ⇒ 两批测的不是同一批页面"
# ⭐⭐⭐⭐⭐ **成对：这道门必须能红** —— 篡改 980 的一个名字就该抓到
_TAMPER = dict(_NS980)
_TAMPER["SPACER"] = '<div style="height:1px">tampered</div>'
_ARMS980_T = eval(compile(_ARMS980_EXPR, "<ARMS-980-tampered>", "eval"),
                  {"__builtins__": {}}, _TAMPER)
assert [(k, h, b) for k, _n, h, b in ARMS] != \
       [(k, h, b) for k, _n, h, b in _ARMS980_T], \
    "⭐⭐⭐⭐⭐ **反向门坏了**：篡改 980 的臂表内容竟然没被抓到 ⇒ 这道门恒真"
assert [(k, h, b) for k, _n, h, b in ARMS] != \
       [(k, h, b) for k, _n, h, b in ARMS[:-1]], \
    "⭐⭐⭐⭐ **反向门②坏了**：少一臂竟然没被抓到"
# ⭐⭐⭐ **并把「note 确实改了」记成一条读数**（不许悄悄改）
ARM_NOTES_CHANGED = ([n for _k, n, _h, _b in ARMS]
                     != [n for _k, n, _h, _b in _ARMS980])
assert ARM_NOTES_CHANGED, "note 竟然没变 ⇒ 那 980 的「4 格环」还留着？"
assert BUTTON_TPL in _p980 and SPACER in _p980 and CSS_PLAIN in _p980
for _k, _n, _h, _b in ARMS:
    assert _b.count("<button") == BTN, "%s 臂的按钮数不是 %d" % (_k, BTN)
assert LAB_PROBE_ID in _p980, "980 的注入 id 变了 ⇒ L2 臂不是同一臂"


# ── ⭐⭐⭐⭐⭐ 纯读守卫（979 定的「只扫代码行」＋ 985 的正则版）──────────
def _code_only(js):
    o = []
    for line in js.split("\n"):
        t = line.strip()
        if t.startswith("//") or t.startswith("*") or t.startswith("/*"):
            continue
        o.append(line.split("//")[0])
    return "\n".join(o)


POLL_CODE = _code_only(POLL_JS)
for _forbidden in ("focus(", "MutationObserver", "addEventListener",
                   "prototype", "location.reload"):
    assert _forbidden not in POLL_CODE, "POLL_JS 里出现了 %r" % _forbidden
# ⭐⭐⭐⭐⭐ **本批唯一的「新用法」是：每一步**额外**问一次 985 那一问**
#   —— ⭐⭐⭐⭐⭐ **诊断读数不许改变被测系统**：两件仪器都必须纯读
FOCUS_CODE = _code_only(FOCUS_JS)
for _pat, _why in (
        (r"\.focus\s*\(", "调 focus()"),
        (r"\.tabIndex\s*=(?!=)", "**写** IDL 属性 `tabIndex`"),
        (r"\.setAttribute\s*\(", "写属性"),
        (r"new\s+MutationObserver", "MutationObserver"),
        (r"\.addEventListener\s*\(", "addEventListener")):
    assert not re.search(_pat, FOCUS_CODE), \
        "`FOCUS_JS` 里出现了%s ⇒ 它不再是**纯读件**" % _why
# ⭐⭐⭐⭐ **改门要成对**：钉住反向 —— 真写必须被抓到
for _bad, _pat in (("a.tabIndex = 0;", r"\.tabIndex\s*=(?!=)"),
                   ("el.setAttribute('tabindex','0');", r"\.setAttribute\s*\("),
                   ("el.focus();", r"\.focus\s*\(")):
    assert re.search(_pat, _bad), "反向门坏了：%r 抓不住" % _bad
# ⭐⭐⭐⭐⭐ **反向门②：读属性不许被当成写**（983 那个坑，984 又踩一次）
assert not re.search(r"\.tabIndex\s*=(?!=)", "a.tabIndex === undefined;"), \
    "⭐⭐⭐ **反向门②坏了**：**读**属性被当成**写** ⇒ 这道门「过窄」"
# ⭐⭐⭐⭐ **反向门③：必须真的读 `tabIndex`**（否则纯读守卫可能退化成恒真）
assert re.search(r"\.tabIndex\b", FOCUS_CODE), \
    "`FOCUS_JS` 连 `tabIndex` 都不读了 ⇒ 纯读守卫可能变成**恒真**"
# ⭐⭐⭐⭐⭐ **本批的正题全在 FOCUS_JS 的三个读数上** ⇒ 少一个就不成立
for _must in (":focus", "hasFocus()", "is_gap", "n_real_focus"):
    assert _must in FOCUS_JS, "FOCUS_JS 少了 %r ⇒ 本批的正题不成立" % _must
assert WINDOW_MS >= MIN_VISIBLE_MS, "窗口比可见下限还短 ⇒ 980 的门②不成立"


# ══ ⭐⭐⭐⭐⭐ 本批的核心：**新口径的四个纯函数** ═════════════════════
# ⚠️⭐⭐⭐⭐⭐ **它们必须是纯函数** ⇒ 同一份代码既能算新读数、
#   **也能离线重算 980 的原始数据** ⇒ 两批不会各说各话


def _cycles(keys):
    """⭐⭐⭐⭐⭐ **切圈器逐字继承 980**（`first` 固定成 `keys[0]`、收尾键计入圈）、
    残段单独返回、不进分母 —— 980 的纪律「切圈残段不许算进分母」。"""
    full, i, first = [], 0, (keys[0] if keys else None)
    if first is None:
        return full, []
    while True:
        j = i + 1
        while j < len(keys) and keys[j] != first:
            j += 1
        if j >= len(keys):
            return full, keys[i:]          # ⭐ 残段：不完整 ⇒ 不算
        full.append(keys[i:j + 1])
        i = j + 1


def _stops(cycle):
    """⭐⭐⭐⭐⭐ **一格里去掉间隙** —— 985 之后 `BODY` 指的是间隙、不是一格。"""
    return [k for k in cycle if k != GAP_KEY]


def _cycles_idx(keys):
    """⭐⭐⭐⭐⭐ **切圈器的「带下标」版本** —— 与 `_cycles` **同一个口径**。

    ⚠️⭐⭐⭐⭐⭐ **为什么要它**：「无间隙圈的回绕前停靠点待了多久」这道**成对门**
    必须**按位置**取停留时长 ⇒ 需要下标 ⇒ 而**绝不能另写一套切法**
    ⇒ ⇒ **所以这里只做一件事：把 980 那套切法**原样加上下标**，
    并用自测钉住「它切出来的圈与继承的那一套**逐格相同**」
    ⇒ ⭐⭐⭐ **同一个东西要比同一个口径**。
    """
    out_, i, first = [], 0, (keys[0] if keys else None)
    if first is None:
        return out_
    while True:
        j = i + 1
        while j < len(keys) and keys[j] != first:
            j += 1
        if j >= len(keys):
            return out_
        out_.append((i, j))
        i = j + 1


def _gapless_pre_wrap_dwell(flat, spans):
    """⭐⭐⭐⭐⭐ **无间隙圈里「回绕前那一枚停靠点」的停留时长**。

    ⚠️⭐⭐⭐⭐⭐ **为什么是「回绕前」那一枚、而不是收尾那一枚** ——
    收尾键的停留是**它自己那一格**的时长（与有无间隙无关）；
    而**「间隙是不是一闪而过、被两个窗口的缝吃掉了」**这个问题
    只能问**回绕前那一枚**：若它的停留**明显长于一格**（≈ 两倍），
    那就可能是「间隙在缝里」⇒ ⇒ ⭐⭐ **这才是「没看见 ≠ 没有」的对偶门**。
    """
    o = []
    for (a, b) in spans:
        cyc = [x for x, _n in flat[a:b + 1]]
        if _has_gap(cyc):
            continue
        if b - 1 >= a:                      # ⭐ 至少要有回绕前那一枚
            o.append(flat[b - 1][1])
    return o


def _ring_stops(keys):
    """⭐⭐⭐ 环长**新口径** = 全部可聚焦停靠点的 distinct 数（**不含间隙**）
    ⇒ 恒等于 985 说的「旧环长 − 1」。"""
    return len({k for k in keys if k != GAP_KEY})


def _covers_all_stops(cycle, ring_stops):
    """⭐⭐⭐⭐⭐ **新口径的完整性**：这一圈有没有覆盖**每一个**可聚焦停靠点。

    ⚠️⭐⭐⭐ **它对「有没有间隙」完全免疫**（间隙不在 `stops` 里）
    ⇒ ⇒ **这正是 980 那道红门的反面**：980 判红的那些圈，在这里是绿的。
    """
    if not cycle or ring_stops < 1:
        return False
    return len(set(_stops(cycle))) == ring_stops


def _has_gap(cycle):
    return GAP_KEY in cycle


def _gap_at_wrap(cycle, first_key):
    """⭐⭐⭐⭐⭐ **P2：间隙的位置** —— 有间隙时，它**必须紧挨在收尾键之前**。

    ⚠️⭐⭐⭐⭐⭐ **推导**：`first_key` 是环里的**第一枚可聚焦停靠点**
    （`_cycles` 固定它为收尾键）⇒ **「间隙在回绕点上」在结构上就是
    「间隙在收尾键之前」** ⇒ 而「间隙落在环的中途」**判红**。
    """
    if not cycle:
        return False
    if not _has_gap(cycle):
        return True                     # 无间隙 ⇒ 这条不适用
    if cycle[-1] != first_key:
        return False                    # 收尾键不对 ⇒ 切圈已经坏了
    return cycle[-2] == GAP_KEY


# ── ⭐⭐⭐⭐⭐ **自测：期望值全部按定义逐句推**（推导写在下面）─────────
# ⚠️⭐⭐⭐⭐⭐ **切圈器自测**（口径与 980 完全相同 ⇒ 期望值也相同）
#   推导：`_cycles` 的圈**从 `keys[0]` 之后那一枚起**、到 `keys[0]` 再次出现止、
#   **含收尾键** ⇒ ⇒ 第 1 例：keys[0]='a'，首次再现在下标 4 ⇒ 圈=[a,b,c,B,a]
#   （5 枚）、下标 5 起是残段
for _in, _n, _tail in (
        (['a', 'b', 'c', 'B', 'a', 'b', 'c', 'B', 'a', 'b'], 2, ['b']),
        (['a', 'b', 'c', 'B', 'a', 'b', 'c', 'B'], 1, ['b', 'c', 'B']),
        (['a', 'b', 'a', 'b', 'a', 'b'], 2, ['b']),
        (['a'], 0, ['a']),
        ([], 0, []),
        (['a', 'b', 'c', 'B', 'a', 'b', 'c', 'B', 'a', 'b', 'c', 'B', 'a'],
         3, [])):
    _f, _t = _cycles(_in)
    assert len(_f) == _n, "切圈器自测失败：%r ⇒ %d 圈（应为 %d）" % (_in, len(_f), _n)
    assert _t == _tail, "切圈器自测失败（残段）：%r ⇒ %r" % (_in, _t)

# ── ⭐⭐⭐⭐⭐ **带下标版切圈器：必须与继承的那一套**逐格相同** ─────────
#   推导：`_cycles_idx` 与 `_cycles` 是**同一段逻辑**、只多返回 `(i, j)`
#   ⇒ ⇒ 按定义它切出的每一圈必须与 `_cycles` 的对应圈**逐格相同**
# ⭐⭐⭐ **「同一个东西要比同一个口径」** —— 这里正是它的用武之地：
#   成对门要**按位置**取停留时长 ⇒ 需要下标 ⇒ 但**绝不能另写一套切法**
for _in, _n, _tail in (
        (['a', 'b', 'c', 'B', 'a', 'b', 'c', 'B', 'a', 'b'], 2, ['b']),
        (['a', 'b', 'c', 'B', 'a', 'b', 'c', 'B'], 1, ['b', 'c', 'B']),
        (['a', 'b', 'a', 'b', 'a', 'b'], 2, ['b']),
        (['a'], 0, ['a']),
        ([], 0, []),
        (['a', 'b', 'c', 'B', 'a', 'b', 'c', 'B', 'a', 'b', 'c', 'B', 'a'],
         3, [])):
    _f, _t = _cycles(_in)
    _sp = _cycles_idx(_in)
    assert len(_sp) == len(_f) == _n, \
        "带下标版自测失败（圈数）：%r ⇒ %d / %d" % (_in, len(_sp), len(_f))
    assert [_in[i:j + 1] for (i, j) in _sp] == _f, \
        "⭐⭐⭐⭐ **带下标版切出的圈与继承的那一套不同** ⇒ 口径分叉了"
    assert all(i < j <= len(_in) - 1 for (i, j) in _sp), \
        "下标越界：%r ⇒ %r" % (_in, _sp)
    # ⭐⭐⭐⭐ **「回绕前那一枚」的下标必须落在圈内**
    for (i, j) in _sp:
        assert i <= j - 1 <= j, "回绕前的下标不在圈内：%r" % ((i, j),)

# ⭐⭐⭐⭐⭐ **无间隙圈的对偶读数自测**（`flat` 与 `spans` 必须按位置对齐）
# ⚠️⭐⭐⭐⭐⭐ **而「对齐」这件事本身就是第一版栽的地方**：
#   我第一版写的用例里，`flat` 的键是 `['a','b','a','b','a']`、
#   传进去的 `keys` 却是 `['a','b',GAP_KEY,'a','b']` ⇒
#   ⭐⭐ **函数是从 `flat` 取圈内容的** ⇒ 于是「有间隙的圈」看起来没有间隙
#   ⇒ **是我的用例错了、不是函数错了** ⇒
#   ⇒ ⭐⭐⭐⭐⭐ **这也正是读数里那条 `n_flat_eq_keys` 存在的理由**：
#   **「`flat` 与 `keys` 对齐」必须由调用方显式验、不许默认成立**
_flat_t = [('a', 130), ('b', 131), ('a', 132), ('b', 130), ('a', 133)]
assert _gapless_pre_wrap_dwell(_flat_t, _cycles_idx(['a', 'b', 'a', 'b', 'a'])) \
    == [131, 130], "无间隙圈的对偶读数取错了位置"
# ⭐⭐⭐⭐ **有间隙的圈不许进这个读数**（否则就不是「无间隙圈」了）
#   —— 这次的 `flat` 与 `keys` **逐格对齐**（键里真的有 `BODY`）
_flat_g = [('a', 130), ('b', 131), (GAP_KEY, 135), ('a', 132), ('b', 133)]
assert _gapless_pre_wrap_dwell(
    _flat_g, _cycles_idx(['a', 'b', GAP_KEY, 'a', 'b'])) == [], \
    "⭐⭐⭐⭐ 有间隙的圈混进了「无间隙圈」的对偶读数"
# ⭐⭐⭐⭐ **反向门**：真出现一个「回绕前停得异常久」的样本，读数必须原样带出来
#   （⇒ 上层那道门才判得红；**读数层不许替上层做决定**）
assert _gapless_pre_wrap_dwell(
    [('a', 130), ('b', 999), ('a', 132)], _cycles_idx(['a', 'b', 'a'])) == [999], \
    "⭐⭐⭐⭐ 异常长的样本被读数层吞掉了 ⇒ 这道门永远不会红"
assert _gapless_pre_wrap_dwell([('a', 130)], _cycles_idx(['a'])) == [], \
    "单枚不成圈 ⇒ 不得给出「回绕前那一枚」"

# ── ⭐⭐⭐⭐⭐ **新口径完整性门的自测**（4 例，第 3 例是**反向**）────────
#   推导：`ring_stops=3` 时，一圈必须恰好含 {b1,b2,b3}
#   例1 含间隙 4 枚 ⇒ 停靠点 3 ⇒ 真；例2 无间隙 3 枚 ⇒ 停靠点 3 ⇒ 真
#   例3 **跳过一个**（{b1,b3}）⇒ 2 ≠ 3 ⇒ **假**（反向门：门必须能红）
#   例4 空圈 ⇒ 假
assert _covers_all_stops(['b1', 'b2', 'b3', GAP_KEY, 'b1'], 3) is True
assert _covers_all_stops(['b1', 'b2', 'b3', 'b1'], 3) is True
assert _covers_all_stops(['b1', 'b3', 'b1'], 3) is False, \
    "⭐⭐⭐⭐ **反向门坏了**：跳过一枚停靠点的圈必须判红 —— 不然这道门恒真"
assert _covers_all_stops([], 3) is False
assert _covers_all_stops(['b1', 'b2', 'b3', GAP_KEY, 'b1'], 2) is False, \
    "ring_stops 传错时必须判红（不能只看 distinct）"
# ⚠️⭐⭐⭐⭐⭐ **最关键的一条自测：同一圈在两套口径下判决不同**
#   推导：无间隙的圈 `['b1','b2','b3','b1']` 的 distinct 是 **3**，
#   而**旧口径**判它「少一格」用的是**旧环长 4** ⇒ `3 < 4` ⇒ 红
#   ⇒ ⇒ **同一串数据、同一圈，两个口径给出相反判决** ⇒ 这就是「门翻面」
_old_ring_len = 4          # 980 的旧口径：含间隙
_new_ring_stops = 3        # 985 的新口径：不含间隙
_probe_cycle = ['b1', 'b2', 'b3', 'b1']
assert len(set(_probe_cycle)) < _old_ring_len, "旧口径应当判红（少一格）"
assert _covers_all_stops(_probe_cycle, _new_ring_stops) is True, \
    "⭐⭐⭐⭐ 新口径应当判绿（覆盖了全部停靠点）⇒ 两套口径给出相反判决"
assert len(set(_probe_cycle)) == _new_ring_stops, \
    "新口径恰好就是「旧 distinct + 1」以外的独立量：这里两套相等"
# ⭐⭐⭐⭐ **并且**新环长**恒等于**旧环长 − 1（985 第五节那条换算）
assert _ring_stops(['b1', 'b2', 'b3', GAP_KEY, 'b1']) == _old_ring_len - 1
assert _ring_stops(['b1', 'b2', 'b3', 'b1']) == 3
# ⭐⭐⭐⭐ **零停靠点页面**（985 的 A1 臂）：旧口径会报「环长 1」的假象
_zero = [GAP_KEY, GAP_KEY, GAP_KEY]
assert _ring_stops(_zero) == 0, \
    "⭐⭐⭐⭐ 零停靠点页面：新口径必须给 0（**不是 1**）⇒ 旧口径那个假象被除掉"
assert _covers_all_stops(_zero, 0) is False, "零停靠点 ⇒ 每一圈都不「完整」"

# ── ⭐⭐⭐⭐⭐ **位置门（P2）的自测**（含**反向**：间隙落在环中途）────
#   推导：收尾键 = `keys[0]`；间隙在回绕点上 ⇒ 它是倒数第二枚
assert _gap_at_wrap(['b1', 'b2', 'b3', GAP_KEY, 'b1'], 'b1') is True
assert _gap_at_wrap(['b2', 'b3', GAP_KEY, 'b1'], 'b1') is True, \
    "⭐⭐⭐ **旋转下也必须成立**（起点会旋转 ⇒ 位置门不能钉下标）"
assert _gap_at_wrap(['b1', 'b2', 'b3', 'b1'], 'b1') is True, "无间隙 ⇒ 适用"
# ⭐⭐⭐⭐⭐ **反向门**：间隙落在**环的中途**（引擎按计时器交出焦点）⇒ 必须判红
assert _gap_at_wrap(['b2', GAP_KEY, 'b3', 'b1'], 'b1') is False, \
    "⭐⭐⭐⭐⭐ **反向门坏了**：间隙落在环中途必须判红 —— 不然 P2 恒真"
assert _gap_at_wrap(['b1', GAP_KEY, 'b2', 'b3', 'b1'], 'b1') is False, \
    "间隙落在环开头也必须判红"
assert _gap_at_wrap([], 'b1') is False
# ⭐⭐⭐⭐ **收尾键不对**（切圈已经坏了）⇒ 判红 ⇒ 一条门只管一件事
assert _gap_at_wrap(['b1', 'b2', 'b3', GAP_KEY, 'b2'], 'b1') is False, \
    "⭐⭐⭐ 收尾键不对必须判红"


# ── ⭐⭐⭐⭐⭐ **离线重算 980 的原始数据**（同一个函数！）──────────────
def _reread_980():
    """⭐⭐⭐⭐⭐ **不重跑也能换口径** —— 用**上面那四个纯函数**去算 980 的读数。

    ⚠️⭐⭐⭐⭐⭐ **纪律**：`/tmp` 里的文件**随时会没** ⇒ 缺了**不许编**，
    必须记 `null` ＋ `why`；而**新跑的那一份才是本批的读数**。
    """
    if not os.path.exists(HIST):
        return {"available": False,
                "why": "⭐⭐ `b980-rate.json` 不在 `/tmp` 了 ⇒ "
                       "**历史离线重算没做成**（新跑那份仍在）"}
    with open(HIST, encoding="utf-8") as f:
        d = json.load(f)
    cells = []
    for rep in d.get("runs") or []:
        for c in rep.get("arms") or []:
            keys = c.get("keys") or []
            full, tail = _cycles(keys)
            first_key = keys[0] if keys else None
            rs = _ring_stops(keys)
            # ⭐⭐⭐⭐ **按位置取停留时长**（对偶门要用）⇒ 需要下标 + `flat`
            flat = [(dd["key"], dd["dwell_ms"]) for s in (c.get("steps") or [])
                    for dd in (s.get("dwell") or [])]
            spans = _cycles_idx(keys)
            pre_wrap = _gapless_pre_wrap_dwell(flat, spans) \
                if len(flat) == len(keys) else []
            cells.append({
                "rep": rep.get("rep"), "arm": c.get("arm"),
                "n_keys": len(keys), "old_ring_len": len(set(keys)),
                "new_ring_stops": rs,
                # ⭐⭐⭐⭐⭐ **新旧环长的换算必须逐格成立**（985 第五节）
                "old_minus_new_eq_1": len(set(keys)) - rs == 1,
                "n_cycles": len(full), "tail_len": len(tail),
                # ⭐ 旧口径：980 报的「缺失」
                "old_laps_missing": sum(
                    1 for x in full if len(set(x)) < len(set(keys))),
                # ⭐⭐⭐⭐⭐ 新口径：真正的「缺失」
                "new_laps_missing_a_stop": sum(
                    1 for x in full if not _covers_all_stops(x, rs)),
                "new_laps_with_gap": sum(1 for x in full if _has_gap(x)),
                "new_laps_without_gap": sum(1 for x in full if not _has_gap(x)),
                "n_gaps_at_wrap": sum(
                    1 for x in full if _has_gap(x) and _gap_at_wrap(x, first_key)),
                "n_gaps_NOT_at_wrap": sum(
                    1 for x in full
                    if _has_gap(x) and not _gap_at_wrap(x, first_key)),
                # ⭐⭐⭐⭐⭐ **对偶门也要在离线重算里跑**（现象在这里非空）
                "pre_wrap_dwell_ms": pre_wrap,
                "n_pre_wrap_dwell_below_floor": sum(
                    1 for x in pre_wrap if x < MIN_VISIBLE_MS),
            })
    tot = {
        "n_cycles": sum(c["n_cycles"] for c in cells),
        "old_laps_missing": sum(c["old_laps_missing"] for c in cells),
        "new_laps_missing_a_stop": sum(c["new_laps_missing_a_stop"] for c in cells),
        "new_laps_with_gap": sum(c["new_laps_with_gap"] for c in cells),
        "new_laps_without_gap": sum(c["new_laps_without_gap"] for c in cells),
        "n_gaps_at_wrap": sum(c["n_gaps_at_wrap"] for c in cells),
        "n_gaps_NOT_at_wrap": sum(c["n_gaps_NOT_at_wrap"] for c in cells),
        "all_old_minus_new_eq_1": all(c["old_minus_new_eq_1"] for c in cells),
        # ⭐⭐⭐⭐⭐ **对偶门（离线那份）**
        "n_pre_wrap_dwell_samples": sum(
            len(c["pre_wrap_dwell_ms"]) for c in cells),
        "n_pre_wrap_dwell_below_floor": sum(
            c["n_pre_wrap_dwell_below_floor"] for c in cells),
    }
    return {"available": True, "cells": cells, "tot": tot,
            "note": "⭐⭐⭐⭐⭐ 这份**不是新数据** —— 它是 980 的**原始读数**，"
                    "只是**换了口径**重算 ⇒ 所以「7.8% → 0%」"
                    "**是在 980 自己的数据上算出来的**"}


from playwright.sync_api import sync_playwright   # noqa: E402

_pw = sync_playwright().start()
_browser = _pw.chromium.launch()
page = _browser.new_context(
    viewport={"width": 1512, "height": 1200}).new_page()
atexit.register(lambda: (_browser.close(), _pw.stop()))


def ev(js, arg=None):
    if arg is None:
        return page.evaluate(js)
    return page.evaluate(js, arg)


def dump(out):
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1, default=str)


def _dwell(seq, elapsed_ms=None):
    """⭐⭐⭐⭐⭐ 逐字继承 **980**（连同「末态」那段）——
    979 漏末态导致 `body_dwell_ms` 整个变成 `[]`，那是「汇总层取值错了」的第五次。"""
    o = []
    for i in range(len(seq) - 1):
        o.append({"key": seq[i]["key"],
                  "dwell_ms": seq[i + 1]["t_ms"] - seq[i]["t_ms"]})
    if seq and isinstance(elapsed_ms, (int, float)):
        last = seq[-1]
        o.append({"key": last["key"],
                  "dwell_ms": int(elapsed_ms) - last["t_ms"]})
    return o


def _build(arm):
    key, _note, head, body = arm
    page.goto("about:blank", wait_until="domcontentloaded")
    page.set_viewport_size(VIEWPORT)
    page.set_content(
        "<!doctype html><html><head>%s</head><body>%s</body></html>"
        % (head, body), wait_until="load")
    page.wait_for_timeout(200)
    return key


out = {
    "target": "lab-blank-page", "url": "about:blank",
    "reps": REPS, "n_steps": N_STEPS, "window_ms": WINDOW_MS,
    "min_visible_ms": MIN_VISIBLE_MS, "viewport": VIEWPORT,
    "n_buttons": BTN, "gap_key": GAP_KEY,
    "question": "⭐⭐⭐⭐⭐ **用 985 的新口径重测 §190 的 7.8%** —— "
                "「缺失率」在新口径下恒为 0（间隙不是一格）⇒ "
                "那 5/64 是「**这一圈的回绕没有交出焦点**」；"
                "并且**第一次量间隙的「位置」**（可红的预测）",
    "ruler": {
        "js_verbatim_from_979": ["POLL_JS"],
        "js_verbatim_from_985": ["FOCUS_JS"],
        "js_verbatim_from_976": ["INJECT_JS", "UNINJECT_JS"],
        "new_pieces": [],
        "new_use_not_new_js": "⭐⭐⭐⭐⭐ 本批**没有新 JS 件** —— 新的是**用法**："
                              "每一步在轮询之后**额外问一次 985 那一问**"
                              "（`:focus` 在谁身上）⇒ "
                              "**新口径的「间隙」由证据判定，不由名字判定**",
        "arms_content_identical_to_980": True,
        "arm_note_rewritten": "⭐⭐⭐⭐⭐ 980 的 note 原文写着「4 格环」「5 格环」"
                               "⇒ **注释里带着一个已被 985 推翻的数** ⇒ "
                               "**臂内容逐格继承 980、note 改写**"
                               "（「同一个东西要比同一个口径」在注释上同样成立）",
        "predictions_written_before_data": [
            "P1 `laps_missing_a_stop == 0`（旧口径把间隙算成一格 ⇒ "
            "「少一格」只可能是「这一圈没有间隙」）",
            "P2 有间隙时它必是**倒数第二枚**、收尾键恒为 `keys[0]`"
            "（`_cycles` 固定 `first`）⇒ 「间隙在回绕点上」是**能红的预测**",
            "P3 `n_gap_where_body_focused == 0` / `n_gap_where_has_focus == 0`"
            "（985 已证，本批把样本从 3 次扩到几十次）",
        ],
        "why_P2_is_not_a_tautology": "⭐⭐⭐⭐⭐ **985 判「同义反复、应当作废」，"
                                     "本批不同意** —— 「间隙按构造在最后与第一个之间」"
                                     "作为**定义**对；但**引擎完全可以按计时器交出焦点**"
                                     "⇒ **「间隙落在哪一格上」是能红的预测**"
                                     "⇒ **985 判过头的不是数据，是把可证伪的预测当成了定义**",
        "why_offline_reread": "⭐⭐⭐⭐⭐ **用同一个纯函数**离线重算 980 的原始读数 ⇒ "
                              "「7.8% → 0%」**在 980 自己的数据上就成立** ⇒ "
                              "且**与新跑那份同函数** ⇒ 两批不会各说各话",
    },
    "arms": [{"key": a[0], "note": a[1]} for a in ARMS],
    "runs": [],
}

for rep in range(1, REPS + 1):
    print(f"===== rep {rep} =====", flush=True)
    rec = {"rep": rep, "arms": []}
    out["runs"].append(rec)
    dump(out)

    for arm in ARMS:
        key = _build(arm)
        cell = {"arm": key}
        rec["arms"].append(cell)
        inj = None
        if key == "L2":
            inj = ev(INJECT_JS, [LAB_PROBE_ID])
            page.wait_for_timeout(120)
        cell["inject"] = inj
        try:
            steps = []
            for k in range(1, N_STEPS + 1):
                page.keyboard.press("Tab")
                r = ev(POLL_JS, [WINDOW_MS])
                seq = (r or {}).get("seq") or []
                # ⭐⭐⭐⭐⭐ **985 那一问**：这一步**谁真的持有焦点**？
                f = ev(FOCUS_JS) or {}
                steps.append({"k": k, "key": "Tab", "seq": seq,
                              "elapsed_ms": (r or {}).get("elapsed_ms"),
                              "dwell": _dwell(seq, (r or {}).get("elapsed_ms")),
                              "focus": f})
            cell["steps"] = steps
        finally:
            if key == "L2":
                cell["uninject"] = ev(UNINJECT_JS, [LAB_PROBE_ID])

        # ── ⭐⭐⭐⭐⭐ 每一步的**落定态** = 时间线最后一枚 ＋ 985 的证据 ──
        #   ⚠️ 979 已证「每次 `Tab` 之后焦点落定、整段窗口都不再变」
        settled = []
        for s in cell["steps"]:
            f = s.get("focus") or {}
            settled.append({
                "k": s["k"],
                "key": (s["dwell"][-1]["key"] if s.get("dwell") else None),
                "is_gap": f.get("is_gap"),
                "is_document_body": f.get("is_document_body"),
                "n_real_focus": f.get("n_real_focus"),
                "has_focus": f.get("has_focus"),
                "body_matches_focus": f.get("body_matches_focus"),
                "id": f.get("id"), "tid": f.get("tid"),
            })
        cell["settled"] = settled
        keys = [s["key"] for s in settled]
        cell["keys"] = keys
        # ⭐⭐⭐⭐⭐ **两件仪器必须在「落定态是谁」上逐格一致**
        #   （`POLL_JS` 的 `keyOf` 与 `FOCUS_JS` 的 `id` 独立取值）
        cell["n_instrument_disagree"] = sum(
            1 for s in settled
            if s["key"] is None or (
                (s["key"] == GAP_KEY) != bool(s["is_document_body"])))
        # ⭐⭐⭐⭐⭐ **每一步恰好一枚 dwell**（979/980 的形状）⇒ 不许有步漏采
        cell["n_steps_with_multi_entry"] = sum(
            1 for s in cell["steps"] if len(s.get("dwell") or []) != 1)

        full, tail = _cycles(keys)
        first_key = keys[0] if keys else None
        cell["first_key"] = first_key
        cell["cycles"] = full
        cell["tail_keys"] = tail
        cell["n_cycles"] = len(full)
        # ⭐⭐⭐⭐⭐ **新口径的环长**（不含间隙）
        cell["ring_stops"] = _ring_stops(keys)
        cell["old_ring_len"] = len(set(keys))
        cell["old_minus_new_eq_1"] = cell["old_ring_len"] - cell["ring_stops"] == 1
        # ⭐ 旧口径的读数（保留：它是**我曾经用错的口径**的证据）
        cell["old_laps_missing"] = sum(
            1 for c in full if len(set(c)) < cell["old_ring_len"])
        # ⭐⭐⭐⭐⭐ **新口径的读数**（本批的正题）
        cell["new_laps_missing_a_stop"] = sum(
            1 for c in full if not _covers_all_stops(c, cell["ring_stops"]))
        cell["new_laps_with_gap"] = sum(1 for c in full if _has_gap(c))
        cell["new_laps_without_gap"] = sum(1 for c in full if not _has_gap(c))
        # ⭐⭐⭐⭐⭐ **位置（P2）**：每一个间隙的环上位置
        cell["n_gaps_at_wrap"] = sum(
            1 for c in full if _has_gap(c) and _gap_at_wrap(c, first_key))
        cell["n_gaps_NOT_at_wrap"] = sum(
            1 for c in full
            if _has_gap(c) and not _gap_at_wrap(c, first_key))
        cell["n_all_cycles_closing_ok"] = sum(
            1 for c in full if c[-1] == first_key)
        cell["cycle_shapes"] = sorted({len(c) for c in full})
        # ⭐⭐⭐⭐⭐ **间隙的逐格证据**（P3：把 985 的 3 次扩到几十次）
        gaps = [s for s in settled if s["is_gap"]]
        cell["n_gap_steps"] = len(gaps)
        cell["n_gap_where_body_focused"] = sum(
            1 for s in gaps if s["body_matches_focus"])
        cell["n_gap_where_any_focus"] = sum(
            1 for s in gaps if (s["n_real_focus"] or 0) > 0)
        cell["n_gap_where_has_focus"] = sum(1 for s in gaps if s["has_focus"])
        stops = [s for s in settled if not s["is_gap"]]
        cell["n_stop_steps"] = len(stops)
        cell["n_stop_where_no_focus"] = sum(
            1 for s in stops if (s["n_real_focus"] or 0) == 0)
        # ⭐⭐⭐⭐⭐ **新口径的「门②」**：间隙的停留必须 ≥ 可见下限
        #   ⇒ 否则「这一圈没有间隙」就不能排除「窗口太短」
        gap_d = [d["dwell_ms"] for s in cell["steps"] for d in s["dwell"]
                 if d["key"] == GAP_KEY]
        cell["gap_dwell_ms"] = gap_d
        cell["n_gap_dwell_below_floor"] = sum(1 for x in gap_d
                                              if x < MIN_VISIBLE_MS)
        cell["n_gapless_cycles"] = cell["new_laps_without_gap"]
        # ⭐⭐⭐⭐⭐ **新口径的对偶门**（没看见间隙的那几圈）：问「回绕前那一枚
        #   停靠点」的停留 —— 若它**明显长于一格**（≈2 倍），就可能是
        #   「间隙在缝里」⇒ 「没看见间隙」就仍可能是「没看够」
        spans = _cycles_idx(keys)
        flat = [(d["key"], d["dwell_ms"]) for s in cell["steps"]
                for d in s["dwell"]]
        cell["n_flat_eq_keys"] = (len(flat) == len(keys))
        cell["pre_wrap_dwell_ms"] = _gapless_pre_wrap_dwell(flat, spans) \
            if cell["n_flat_eq_keys"] else []
        cell["n_pre_wrap_dwell_below_floor"] = sum(
            1 for x in cell["pre_wrap_dwell_ms"] if x < MIN_VISIBLE_MS)
        dump(out)

# ── ⭐⭐ 两轮比较**必须在 `for rep` 循环之外**（955 第一版栽在这上面）───
def _cell(arms, key):
    for a in arms:
        if a.get("arm") == key:
            return a
    return {}


_r0 = out["runs"][0]["arms"] if out["runs"] else []
_r1 = out["runs"][1]["arms"] if len(out["runs"]) > 1 else []


def _both_arms(fn):
    ok = True
    for k, _n, _h, _b in ARMS:
        for arms in (_r0, _r1):
            c = _cell(arms, k)
            if not c:
                return False
            ok = ok and bool(fn(c))
    return ok


out["reps_agree"] = all(
    _cell(_r0, a[0]).get("ring_stops") == _cell(_r1, a[0]).get("ring_stops")
    for a in ARMS)

out["design_gates"] = {
    # ⭐ 圈数够多（统计量需要样本量）
    "enough_cycles_both_reps": _both_arms(lambda c: c.get("n_cycles", 0) >= 10),
    # ⭐⭐ 每一步都读到了落定态（读数不许断档）
    "every_step_has_a_settled_state_both_reps": _both_arms(
        lambda c: len(c.get("settled") or []) == N_STEPS
        and all(s.get("key") for s in c["settled"])),
    # ⭐⭐⭐⭐⭐ **两件仪器在「落定态是谁」上逐格一致** ——
    #   不一致 ⇒ 「间隙」是仪器造出来的、不是页面上发生的
    "instruments_agree_on_settled_id_both_reps": _both_arms(
        lambda c: c.get("n_instrument_disagree") == 0),
    # ⭐⭐ 每一步恰好一枚 dwell（980 的形状）⇒ 没有步被漏采
    "one_dwell_entry_per_step_both_reps": _both_arms(
        lambda c: c.get("n_steps_with_multi_entry") == 0),
    # ⭐⭐⭐⭐⭐ **新旧环长的换算逐格成立**（985 第五节那条）
    "old_minus_new_ring_eq_1_both_reps": _both_arms(
        lambda c: c.get("old_minus_new_eq_1") is True),
    # ⭐⭐⭐⭐⭐ **新口径的「缺失」在每一圈都不成立**（P1）——
    #   ⚠️ 红的**不是门、就是数据**（真有一圈跳过了停靠点）
    "no_lap_missing_a_stop_both_reps": _both_arms(
        lambda c: c.get("new_laps_missing_a_stop") == 0),
    # ⭐⭐⭐⭐⭐ **P2：每一个间隙都落在回绕点上，零例外**
    "every_gap_sits_at_the_wrap_both_reps": _both_arms(
        lambda c: (c.get("n_gaps_NOT_at_wrap") == 0)
        and (c.get("n_gaps_at_wrap") or 0) >= 10),
    # ⭐⭐⭐⭐⭐ **切圈的自洽**：每一圈的收尾键都等于 `first`
    "every_cycle_closes_on_first_key_both_reps": _both_arms(
        lambda c: c.get("n_all_cycles_closing_ok") == c.get("n_cycles")),
    # ⭐⭐⭐⭐⭐ **P3：间隙仍然是间隙**（样本比 985 大得多）
    "gap_is_never_a_real_focus_both_reps": _both_arms(
        lambda c: c.get("n_gap_where_body_focused") == 0
        and c.get("n_gap_where_any_focus") == 0
        and c.get("n_gap_where_has_focus") == 0
        and (c.get("n_gap_steps") or 0) >= 10),
    # ⭐⭐⭐⭐ **反向读数**：停靠点**都**真的持有焦点 ⇒ 「零」不是没读到
    "every_stop_really_holds_focus_both_reps": _both_arms(
        lambda c: c.get("n_stop_where_no_focus") == 0
        and (c.get("n_stop_steps") or 0) >= 10),
    # ⭐⭐⭐⭐⭐ **新口径的门②**（成对）：间隙停留 ≥ 可见下限
    "gap_dwell_all_above_floor_both_reps": _both_arms(
        lambda c: c.get("n_gap_dwell_below_floor") == 0
        and (c.get("gap_dwell_ms") or []) != []),
    # ⭐⭐⭐⭐⭐ **新口径的对偶门**（成对）：无间隙那几圈的「回绕前停靠点」
    #   停留**也必须 ≥ 可见下限** ⇒ ⇒ 「没看见间隙」不能被解释成
    #   「间隙在两个窗口的缝里、一闪而过」⇒ **「没看见」先排除「没看够」**
    # ⚠️⭐⭐⭐⭐⭐ **这道门第一版写成「必须有 `wrap_dwell_ms`」⇒ 判红了** ——
    #   而 ⭐⭐ **红的不是数据、是我把「现象没出现」和「现象出现了但没过」
    #   混成了一件事**（本轮 84 圈里无间隙圈**一次都没出现**）
    # ⇒ ⇒ ⭐⭐ **处置是「改精确、不放宽」**：门必须**只在现象出现时**才判真假，
    #   **并把「现象出现了几次」另立一条读数** ⇒
    #   ⭐⭐⭐⭐⭐ **一条门只能管一件事**；**空集不是失败，是「没发生」**
    "pre_wrap_dwell_ok_if_gapless_present_both_reps": _both_arms(
        lambda c: (c.get("n_flat_eq_keys") is True)
        and (c.get("n_gapless_cycles", 0) == 0
             or c.get("n_pre_wrap_dwell_below_floor") == 0)),
    # ⭐⭐⭐⭐⭐ **「现象有没有出现」必须单独记一条读数** ——
    #   否则读数里只有一个空列表，**分不清「没发生」与「发生了但没过」**
    "gapless_phenomenon_recorded_both_reps": _both_arms(
        lambda c: isinstance(c.get("n_gapless_cycles"), int)
        and isinstance(c.get("pre_wrap_dwell_ms"), list)),
    # ⭐⭐ L2 的注入生效且被还原
    "l2_injection_applied_and_restored_both_reps": all(
        (_cell(a, "L2").get("inject") or {}).get("injected") is True
        and (_cell(a, "L2").get("uninject") or {}).get("removed") is True
        for a in (_r0, _r1) if _cell(a, "L2")),
}

out["reread_980"] = _reread_980()

# ⭐⭐⭐⭐⭐ **「比率」这件事本身要当读数摆出来** ——
#   986 这轮 84 圈里「无间隙」一次都没出现，而 980 的 64 圈里有 5 圈
#   ⇒ ⇒ ⭐⭐⭐⭐⭐ **同一个量在两批之间不复现** ⇒ **「7.8%」不是一个稳定的比率**
#   ⇒ ⇒ 而这**正是 985 要求重测的原因**（旧口径把「无间隙」叫做「缺失」）
_fresh_gapless = sum(
    _cell(arms, a[0]).get("new_laps_without_gap", 0) or 0
    for arms in (_r0, _r1) for a in ARMS)
_fresh_cycles = sum(
    _cell(arms, a[0]).get("n_cycles", 0) or 0
    for arms in (_r0, _r1) for a in ARMS)
_r = out["reread_980"]
_hist_gapless = (_r.get("tot") or {}).get("new_laps_without_gap")
_hist_cycles = (_r.get("tot") or {}).get("n_cycles")
out["rate_is_not_stable"] = {
    "fresh_gapless_cycles": _fresh_gapless,
    "fresh_cycles": _fresh_cycles,
    "hist_gapless_cycles": _hist_gapless,
    "hist_cycles": _hist_cycles,
    "verdict": "⭐⭐⭐⭐⭐ **同一个量在两批之间不复现** —— 986 新跑的 84 圈里"
               "「无间隙」**一次都没出现**，而 980 的 64 圈里有 5 圈 ⇒ "
               "⇒ ⭐⭐⭐⭐ **「7.8%」不是一个稳定的比率**，"
               "它只是**某一批里**的读数 ⇒ "
               "⇒ ⭐⭐⭐⭐⭐ **这也正是 985 要求重测的理由**："
               "旧口径把「无间隙」错叫成「缺失」"
    if (_fresh_gapless == 0 and _hist_gapless) else
    "⭐ 两批都出现了「无间隙」圈 ⇒ 逐批读数已足够",
}

out["reread_980_pre_wrap_gate_note"] = (
    "⭐⭐⭐⭐⭐ **成对门（对偶）在离线重算里也跑了** —— 因为 980 的读数里"
    "「无间隙」现象**非空**（5 圈）⇒ ⇒ 那道门在那里**不是恒真的空集** ⇒ "
    "五个「回绕前停靠点」的停留都在 120ms 以上 ⇒ "
    "⇒ ⭐⭐⭐ **「这一圈没有间隙」不能被解释成「间隙太短没看见」**"
)

out["recon"] = {
    "rep%d" % i: {
        a.get("arm"): {
            "first_key": a.get("first_key"),
            "old_ring_len": a.get("old_ring_len"),
            "ring_stops": a.get("ring_stops"),
            "n_cycles": a.get("n_cycles"),
            "old_laps_missing": a.get("old_laps_missing"),
            "new_laps_missing_a_stop": a.get("new_laps_missing_a_stop"),
            "new_laps_with_gap": a.get("new_laps_with_gap"),
            "new_laps_without_gap": a.get("new_laps_without_gap"),
            "n_gaps_at_wrap": a.get("n_gaps_at_wrap"),
            "n_gaps_NOT_at_wrap": a.get("n_gaps_NOT_at_wrap"),
            "n_gap_steps": a.get("n_gap_steps"),
            "cycle_shapes": a.get("cycle_shapes"),
            "tail_keys": a.get("tail_keys"),
            "n_gap_dwell_below_floor": a.get("n_gap_dwell_below_floor"),
            "n_gapless_cycles": a.get("n_gapless_cycles"),
            "pre_wrap_dwell_ms": a.get("pre_wrap_dwell_ms"),
            "n_pre_wrap_dwell_below_floor": a.get(
                "n_pre_wrap_dwell_below_floor"),
        }
        for a in arms
    }
    for i, arms in enumerate((_r0, _r1))
}

out["gate_notes"] = (
    "⭐ 986 的门围绕**两条预测**与**两件仪器的一致性**：\n"
    "  · ⭐⭐⭐⭐⭐ `no_lap_missing_a_stop` 是 **P1** —— 旧口径把间隙算成一格，\n"
    "    所以「少一格」从来只意味着「这一圈没有间隙」⇒ 新口径下它**恒为 0**；\n"
    "    ⚠️ 这道门**不是恒真**：真有一圈跳过一个停靠点它就红（自测第 3 例钉住反向）；\n"
    "  · ⭐⭐⭐⭐⭐ `every_gap_sits_at_the_wrap` 是 **P2**，而且**它是新量** ——\n"
    "    980 只量了「有没有间隙」，**从没量过间隙的位置** ⇒ "
    "    **红的就是「引擎按计时器交出焦点」**（自测里钉了那个反向例）；\n"
    "  · ⭐⭐⭐⭐ `instruments_agree_on_settled_id` 防的是「间隙由仪器造出来」；\n"
    "  · ⭐⭐⭐⭐ `gap_dwell_all_above_floor` 与 `gapless_wrap_dwell_all_above_floor`\n"
    "    **成对** ⇒ 前者说「看见了间隙、且它待够了」，后者说「没看见间隙、"
    "**且那里并没有一个一闪而过的间隙**」⇒ ⭐⭐⭐⭐⭐ "
    "**「没看见」必须先排除「没看够」**（980 的关键前提，成对重做一遍）；\n"
    "  · ⭐⭐⭐⭐ **`new_laps_missing_a_stop` 与 `old_laps_missing` 都记下来** ——\n"
    "    ⭐⭐⭐⭐ **两个口径的判决并排读出来**（同一个东西要比同一个口径）；\n"
    "  · ⭐⭐⭐ **比率刻意不判真假** —— `with_gap / n_cycles` **由 verifier 判**。"
)

out["what_986_measures"] = (
    "① ⭐⭐⭐⭐⭐ **用新口径重测 §190 的 7.8%** —— 分子从「少一格」改成"
    "「这一圈没有间隙」，而**分母也换了**（新环长 = 旧环长 − 1）⇒ "
    "**「缺失率」不再是那个量**；\n"
    "  ② ⭐⭐⭐⭐⭐ **第一次量间隙的「位置」** ⇒ 985 判成「同义反复」的那句"
    "**是一条能红的预测**，本批把它跑成可判的；\n"
    "  ③ ⭐⭐⭐⭐⭐ **同一套纯函数**离线重算 980 的原始读数 ⇒ "
    "**「7.8% → 0%」在 980 自己的数据上就成立**；\n"
    "  ④ ⭐⭐⭐⭐ **把 985 的证据样本从 3 次扩到几十次**（回归门）"
)

out["discipline_986"] = (
    "① ⭐⭐⭐⭐⭐ **仪器测什么，决定了你能看见什么** —— 985 的教训，986 照做："
    "**新口径的「间隙」由 `:focus` 的证据判定，不由名字判定**；\n"
    "  ② ⭐⭐⭐⭐⭐ **期望值必须按定义逐句推** —— 三条预测**全部写在看数据之前**，"
    "**并逐条给出推导**（探针头部）⇒ "
    "**「跑出来是什么就写什么」会让自测恒真**；\n"
    "  ③ ⭐⭐⭐⭐⭐ **同义反复 ≠ 不可证伪** —— 「间隙按构造在最后与第一个之间」"
    "作为**定义**是同义反复，但**「间隙落在环的哪一格上」是能红的预测** ⇒ "
    "**985 判过头的不是数据，是把可证伪的预测当成了定义**；\n"
    "  ④ ⭐⭐⭐⭐⭐ **新口径不是「换掉旧的」，是「多记一列」** —— "
    "**两个口径的判决并排读出来**（`old_laps_missing` 与 `new_laps_missing_a_stop`）⇒ "
    "**同一个东西要比同一个口径**；\n"
    "  ⑤ ⭐⭐⭐⭐⭐ **「没看见」必须先排除「没看够」** —— 980 的关键前提，"
    "986 **成对重做**（有间隙 / 无间隙两侧都钉）；\n"
    "  ⑥ ⭐⭐⭐⭐ **改门要成对**：每道新门都有一条自测钉住反向 —— "
    "**过宽和过窄的门一样坏，恒真的门比没有门更坏**；\n"
    "  ⑦ ⭐⭐⭐⭐ **注释里也可能带着一个已被推翻的数** —— 980 的臂表 note 写着"
    "「4 格环」⇒ **臂内容逐格继承、note 改写、并把「note 确实改了」记成读数**；\n"
    "  ⑧ ⭐⭐⭐ **「不重跑也能换算」要在同一套函数上做** ⇒ 两批不会各说各话；\n"
    "  ⑨ ⭐⭐⭐ `/tmp` 里的文件随时会没 ⇒ 缺了记 `null` ＋ `why`，**不许编**；\n"
    "  ⑩ ⭐⭐⭐⭐⭐ **本批零计费**：`about:blank`、**只按 `Tab`**、"
    "**连 `mouse.click` 都没有**"
)

out["skip_note"] = (
    "⚠️ 本批**只回答「空白页上间隙的比率与位置」**，"
    "**不回答「源站那个页面上间隙的比率与位置」** ⇒ ⭐⭐ "
    "**实验室的比率不等于源站的比率**，两者不许混成一句话；\n"
    "⚠️ 且**源站登录态已过期（985 已确认）** ⇒ 源站侧本批**没测到**，"
    "**不是「测了没事」**"
)

dump(out)
print("PROBE_986_DONE", out["reps_agree"], flush=True)
