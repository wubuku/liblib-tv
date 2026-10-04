#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""batch 982 **源站**探针（**纯诊断 / 零插入零节点点击**）：
⭐⭐⭐⭐⭐ **给「一圈」这件事下一个正式定义** —— 并用它把 973/974 的核心结论
**从一个 17.8% 的小段补到 100%**。

── 981 逼出来的那个问题 ────────────────────────────────────────────

981 实测源站的**完整顺序环长 101 格**，于是「973–977 那个『走满一圈』」当场可疑。
而 982 一上手就查出一件更要紧的事 —— ⭐⭐⭐⭐⭐ **981 自己挂错了一个数**：

- 981 写：「左栏容器 `canvas-fixed-toolbar` **一圈里被命中约 2 次**
  （三个左栏按钮各自的 `closest_tid` 都是它）」
- 981 自己的读数：**240 步 = 2 圈 + 38 步，`closest_tid == canvas-fixed-toolbar`
  只在第 84、185 拍出现** ⇒ ⇒ **每圈 1 次**
- 而且第 85/86/87 拍的 `closest_tid` 分别是
  `canvas-pointer-tool-toggle` / `canvas-display-toggle-minimap` /
  `canvas-display-toggle-connections` ⇒ **三个左栏按钮的 `closest_tid`
  各不相同**

⇒ ⇒ ⚠️ 错在**跨圈计数漏了除以圈数**（980「切圈残段不许算进分母」的姊妹条）
⇒ 但**这个错误的方向是「说多了」**，而 981 据此下的结论是
「973–977 不是整圈」⇒ ⇒ **结论要换理由重述，不是撤回**（见下面「换理由」）。

── ⭐⭐⭐⭐⭐ 本批的正题：「圈」= **最小重复周期** ──────────────────────

973/974 报的 `arc`（19 / 18 格）**根本不是圈** —— 读 973 的源码可知，
它的 `arc` 是**「`out` 行里 k 连续的第一段」**（`jimeng_probe973_ringorder_ck.py:311`），
**与 `n_rail_stops` 那套切圈毫无关系**。

⇒ ⇒ 而 973 那句注释「走查不重试 ⇒ 一段 = 一圈」**在两侧的覆盖率差了一个量级**：

|        | 973 复刻 | 974 源站 |
|--------|----------|----------|
| 整圈长 | **26**   | **101**  |
| `arc`  | 19       | 18       |
| 覆盖率 | 73.1%    | **17.8%** |

⇒ ⇒ ⭐⭐⭐⭐⭐ **「环序 = 纯 DOM 序」这个核心结论，在源站侧只验了 17.8% 的圈。**

⇒ 所以本批给「圈」下一个**不依赖任何 testid、不依赖「左栏」这类站点标记**的
正式定义：

    圈长 p := 满足「∀i: seq[i] == seq[i % p]」的**最小** p

它是**不变量**（旋转不变、与步数无关），而且**不读任何名字**
⇒ ⇒ ⭐⭐⭐⭐⭐ 「同一个东西要比同一个口径」这条纪律（974 记的，已复发四次）
**从根上被绕开**：新定义里根本没有「名字」，也就没有「两种口径」。

── 换理由（981 那条结论的新说法） ────────────────────────────────

981 的结论「973–977 那个『走满一圈』不是整圈」**仍然成立**，但理由换成三条可查的：

1. 源站整圈 = **101 格**，而 973/974 报的 `arc` 是 19 / 18 格的**连续 out 段**；
2. ⭐ **974 根本没走完一圈** —— 它的读数 `n_rail_stops = 1`
   （`canvas-fixed-toolbar` 只命中 1 次就撞上了 `n_lead_cap = 140` 硬上限）
   ⇒ **140 步 = 1 个整圈 + 39 步残段**；
3. 973（复刻侧）`n_rail_stops = 2` ⇒ 它**确实**走完了，而复刻侧整圈 = **26 格**
   ⇒ 它的 19 格 `arc` = 圈的 73.1%。

── 本批的读数（只做计数，真伪由 verifier 判） ─────────────────────

- `min_period` / `n_full` / `rem` —— ⭐⭐⭐ **`rem` 必须读出来**
  （980 的纪律：切圈残段不许算进分母）
- `arc_len`（**973/974 的口径**，在整圈上重算）与 `arc_cover`（关系式）
- ⭐⭐⭐ `descents_on_full_lap`（**整圈上**的 `dom_rank` 下降次数）
  与 `descents_on_arc`（弧上的，**并排**读出、不二选一）
- ⭐ `rail_closest_hits` / `n_circles_by_marker` —— **每圈 1 次还是 2 次**

⚠️⭐⭐⭐ **`min_period` 有一条致命的坑**：`p == n` 时恒成立
（`seq[i % n] == seq[i]` 恒真）⇒ 它**永不失败** ⇒
① 空序列必须**显式**返回 `None`（否则 `all([])` 让 `p = 1` 恒成立）；
② 残段必须靠 `rem` 单独读出来，否则「1.5 个周期」会被当成「1 个周期」。

**本批零计费**：只按 `Tab`；⛔ 计费守卫拦在 `mouse.click` **之前**。
"""
from __future__ import annotations

import json
import os
import re

OUT = "/tmp/b982-ringlen.json"
REPS = 2
N_STEPS = 210        # ⭐ 101×2 = 202 ⇒ **2 个完整周期**，另留 8 步余量
WINDOW_MS = 140      # 与 981 同一道门①（≥ 979 实测的 `BODY` 停留 120ms）
MIN_VISIBLE_MS = 120
NODE_SEL = "[data-nodeid], .react-flow__node"   # ⭐ 与 974 **逐字同**
LAP_TID = "canvas-project-logo"                 # 981 用过的切圈标记
RAIL_TID = "canvas-fixed-toolbar"
LEFT_RAIL_SELF = ("canvas-pointer-tool-toggle",
                  "canvas-display-toggle-minimap",
                  "canvas-display-toggle-connections")
SRC_URL = ("https://jimeng.jianying.com/ai-tool/ai-canvas/"
           "64b58cd5-7b04-4312-890a-09f2d1d3399f"
           "?enter_from=project_list&from_page=create")
FORBIDDEN_TIDS = ("canvas-commerce-entry", "canvas-pay-trigger",
                  "canvas-recharge", "canvas-member-buy")

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _src(name):
    p = os.path.join(_ROOT, "scripts", name)
    if not os.path.exists(p):
        return ""
    with open(p, encoding="utf-8") as f:
        return f.read()


# ⚠️⭐⭐⭐ **`DOMRANK_JS` 的源头是 973**（974 已逐字搬过一次）
#   ⚠️⚠️ `DOMRANK_JS` 用**普通** `"""` 写的，`_grab` 的 `r?"""` 也匹配得上
# ⚠️⭐⭐⭐ **`POLL_JS` 的源头是 979**（980/981 都在用）⇒ 本批是第三个消费者
_p973 = _src("jimeng_probe973_ringorder_ck.py")
_p979 = _src("jimeng_probe979_dwell_src.py")
_p980 = _src("jimeng_probe980_rate_src.py")
_p981 = _src("jimeng_probe981_srcrate_src.py")


def _grab(name, src=None):
    m = re.search(r'^%s\s*=\s*r?"""(.*?)"""' % name, src or "", re.S | re.M)
    assert m, "抠不到 %s" % name
    _s = m.group(1)
    assert _s in (src or ""), "%s 不是逐字抠出来的" % name
    return _s


DOMRANK_JS = _grab("DOMRANK_JS", _p973)
POLL_JS = _grab("POLL_JS", _p979)

_ME = open(__file__, encoding="utf-8").read()

# ── ⭐⭐⭐ 分叉守卫：本批**不许自己定义**那两件继承来的仪器 ──────────
assert not re.search(r'^DOMRANK_JS\s*=\s*r?"""', _ME, re.M), \
    "本批自己定义了**继承来的** `DOMRANK_JS` ⇒ 尺子分叉了"
assert not re.search(r'^POLL_JS\s*=\s*r?"""', _ME, re.M), \
    "本批自己定义了**继承来的** `POLL_JS` ⇒ 尺子分叉了"
assert DOMRANK_JS in _p973, "DOMRANK_JS 不在 973 探针里 ⇒ 不是同一件仪器"
assert POLL_JS in _p979, "POLL_JS 不在 979 探针里 ⇒ 不是同一件仪器"
# ⭐⭐⭐⭐⭐ **981 的前提还在吗**（本批 981 那条结论要换理由重述）
assert "实验室的比率不等于源站的比率" in _p980, \
    "980 的 `skip_note` 变了 ⇒ 981 的前提要重新确认"
# ⭐⭐⭐⭐⭐ **本批要更正的那句话，在 README §191 里，不在 981 探针里**
#   ⚠️⚠️⚠️ 第一版这道门错在**锚点挑错文件**（我拿 README 的措辞去探针里找）
#   ⇒ ⇒ **门红先判「门错还是数据错」** —— 这次是门错
_README = _src("../docs/research/jimeng-canvas/README.md") or _src(
    "docs/research/jimeng-canvas/README.md")
assert "## §191" in _README, "README 没有 §191 ⇒ 本批要更正的对象变了"
assert "约 2 次" in _README, \
    "§191 里那句「约 2 次」不见了 ⇒ 撤销结论必须**原文保留**、只加改写横幅"
# ⭐⭐⭐⭐ **读数层的字段名不许悄悄改名**（981 那个错数是从它算出来的）
assert "rail_hits_container_kb" in _p981, \
    "981 探针里 `rail_hits_container_kb` 改名了 ⇒ 本批的更正要重写"
assert "canvas-fixed-toolbar" in _p981, "981 探针里没有左栏 testid ⇒ 对象变了"
assert WINDOW_MS >= MIN_VISIBLE_MS and N_STEPS >= 202, \
    "步数不够 2 个完整周期 ⇒ 圈长定不下来"


# ══ ⭐⭐⭐⭐⭐ 本批的新件：把「圈」定义成一个不变量 ═══════════════════

def min_period(seq):
    r"""圈长 := 使「∀i: seq[i] == seq[i % p]」成立的**最小** p。

    ⚠️⭐⭐⭐ **本函数永不失败** —— `p == len(seq)` 恒成立
    （`seq[i % n] == seq[i]` 恒真）⇒ 它判不出「不是周期序列」。

    ⇒ 因此**调用方必须另外读出两件事**：
      · 空序列 ⇒ 显式返回 `None`（否则 `p = 1` 靠 `all([])` 恒真）
      · `rem = n % p` ⇒ **残段不许算进分母**（980 的纪律）
    """
    n = len(seq)
    if n == 0:                    # ⭐⭐ `all([])` 是恒真 ⇒ 必须显式挡掉
        return None
    for p in range(1, n + 1):
        if all(seq[i] == seq[i % p] for i in range(n)):
            return p
    return None                   # 不可达；写出来是为了「不靠隐式回落」


def _arc_of(pairs):
    r"""⭐⭐⭐⭐⭐ **逐字复刻 973 的 `arc` 提取器**（`arc` = `out` 行里
    k 连续的第一段）⇒ 于是本批报出来的 `arc_len` **与 973/974 同口径**。
    `pairs` = [(k, rank), ...]（k 须是圈内相对下标 + 1）。
    """
    arc = []
    for (k, rk) in pairs:
        if arc and k != arc[-1][0] + 1:
            break
        arc.append((k, rk))
    return arc


def _descents(seq):
    """数**严格下降**的次数（973 的 `n_rank_descents` 口径）。

    ⚠️⚠️⭐⭐⭐ **`unknown` 数的是「元素」不是「相邻对」** ——
    第一版我按循环自然产物数**相邻对**，于是 `[1, None, 2]` 报出 `u = 2`
    （第 1 对含 `seq[1]`、第 2 对也含 `seq[1]`）⇒ 而 973 的
    `n_rank_unknown` 数的是**格数** ⇒ ⇒ **口径不同**。
    ⇒ ⇒ 与 973 对齐：**`unknown` = 序列里 `None` 的个数**。
    """
    d = 0
    for i in range(1, len(seq)):
        a, b = seq[i - 1], seq[i]
        if a is None or b is None:
            continue          # ⭐ `None` **不算下降**（避免「没量到」被当成有序）
        if b < a:
            d += 1
    return d, sum(1 for x in seq if x is None)


# ══ ⭐⭐⭐⭐⭐ 三个新件的自测 —— 期望值**按定义逐句推**，不是「跑出来是什么」══
_MP_CASES = (
    # (seq, 期望 p, 期望 n_full, 期望 rem, 逐句依据)
    ([], None, 0, 0,
     "空序列没有观测 ⇒ `p=1` 靠 `all([])` 恒真，必须显式 None"),
    (['a'], 1, 1, 0, "单枚 ⇒ 平凡周期 1"),
    (['a', 'b', 'a', 'b'], 2, 2, 0, "p=1 在 i=1 失败；p=2 全成立"),
    (['a', 'b', 'a', 'b', 'a', 'b', 'a'], 2, 3, 1,
     "p=2 全成立（seq[6]=='a'==seq[0]）⇒ 7 步 = 3 圈 + **1 步残段**"),
    (['a', 'b', 'a'], 2, 1, 1,
     "p=2 成立（seq[2]==seq[0]）⇒ 3 步 = 1 圈 + 1 步残段；**不是** p=3"),
    (['a', 'b', 'a', 'c'], 4, 1, 0,
     "p=1✗(i=1)、p=2✗(i=3: 'c'!='b')、p=3✗(i=3: 'c'!='a')、p=4 恒成立"),
    (['a', 'a', 'a', 'a'], 1, 4, 0, "全同 ⇒ 平凡周期 1"),
    (['a', 'b', 'c', 'a', 'b', 'c', 'a', 'b'], 3, 2, 2,
     "p=3 全成立 ⇒ 8 步 = 2 圈 + 2 步残段"),
)
for _seq, _p, _nf, _rem, _why in _MP_CASES:
    _got = min_period(_seq)
    assert _got == _p, "min_period 自测（p）失败：%r ⇒ 期望 %r 实际 %r（%s）" \
        % (_seq, _p, _got, _why)
    if _p is None:
        continue
    _n = len(_seq)
    assert (_n // _p, _n % _p) == (_nf, _rem), \
        "min_period 自测（n_full/rem）失败：%r ⇒ 期望 (%r,%r) 实际 (%r,%r)（%s）" \
        % (_seq, _nf, _rem, _n // _p, _n % _p, _why)
# ⭐⭐⭐ **成对**：钉住反向 —— 期望值推错时**必须仍红**
#   ⚠️⚠️⚠️ **写这条时我又把期望值推错了（那条纪律的第六次复发）**：
#   我先写「4 步序列的『最大周期』= 2」⇒ 判红 ⇒ 逐句重推才发现
#   **`p == n` 恒成立 ⇒ `max` 必是 `n`** ⇒ 4 步的答案是 **4**，不是 2。
#   ⇒ ⇒ 记下来：**`min` 与 `max` 的差别恰好就是「残段」这件事**。
def _min_period_longest(seq):
    n = len(seq)
    return max([p for p in range(1, n + 1)
                if all(seq[i] == seq[i % p] for i in range(n))] or [0])


assert _min_period_longest(['a', 'b', 'a', 'b']) == 4, \
    "反向门本身坏了（4 步序列的『最大周期』必是 n = 4）"
assert _min_period_longest(['a', 'b', 'a', 'b', 'a', 'b']) == 6, \
    "反向门失灵：把「最小」写成「最大」也能过 ⇒ 期望值钉不住"
assert min_period(['a', 'b', 'a', 'b', 'a', 'b']) == 2, \
    "「最小」那条对不上了"
# ⭐⭐⭐⭐⭐ **`min` 与 `max` 的差就是「残段」** ⇒ 这条同时钉住 `rem` 的意义
#   · 6 步整除：min = 2（3 圈）、max = 6（1 圈）⇒ **两者都 rem=0**
#   · 3 步（1.5 圈）：min = 2 ⇒ **rem = 1**；max = 3 ⇒ rem = 0
#   ⇒ ⇒ ⭐ **`max` 永远看不到残段**（它总是整除）⇒ **用它会把残段当整圈**
assert (min_period(['a', 'b', 'a', 'b', 'a', 'b']),
        _min_period_longest(['a', 'b', 'a', 'b', 'a', 'b'])) == (2, 6), \
    "min/max 这对钉子错位了"
assert (min_period(['a', 'b', 'a']),
        _min_period_longest(['a', 'b', 'a'])) == (2, 3), "min/max 错位"
assert 3 % min_period(['a', 'b', 'a']) == 1, "`min` 的残段读法不对"
assert 3 % _min_period_longest(['a', 'b', 'a']) == 0, "`max` 的残段读法不对"
# ⭐⭐⭐⭐⭐ **最致命的一条**：`p == n` 恒成立 ⇒ 「不是周期序列」这个返回值
#   **永远不会出现** ⇒ 必须有一条门把这件事钉住，否则后人会去信它
assert min_period(['x', 'y', 'z', 'w', 'v', 'q', 'r']) == 7, \
    "p == n 恒成立这条被改动了 ⇒ `n_full`/`rem` 的读法要重看"

_ARC_CASES = (
    ([(1, 10), (2, 11), (3, 12)], 3, "k 连续 ⇒ 整段"),
    ([(1, 10), (2, 11), (4, 12)], 2, "k=4 ≠ 2+1 ⇒ 在第 3 项 break"),
    ([(1, 10), (3, 12), (4, 13)], 1, "k=3 ≠ 1+1 ⇒ 只有第 1 项"),
    ([], 0, "空 ⇒ 0（且不许 IndexError）"),
)
for _pairs, _want, _why in _ARC_CASES:
    assert len(_arc_of(_pairs)) == _want, \
        "arc 自测失败：%r ⇒ 期望 %r 实际 %r（%s）" \
        % (_pairs, _want, len(_arc_of(_pairs)), _why)
# ⭐⭐ **成对**：`arc` 只取**第一段**，后面还有段也不能续上
assert len(_arc_of([(1, 1), (2, 2), (5, 5), (6, 6), (7, 7)])) == 2, \
    "arc 把断开的第二段也吃进来了 ⇒ 与 973 不同口径"

_D_CASES = (
    ([1, 2, 3], 0, 0, "单调 ⇒ 无下降"),
    ([3, 2, 1], 2, 0, "每一步都降"),
    ([1, None, 2], 0, 1, "**None 不算下降**，只记 unknown"),
    ([5, None, 1], 0, 1, "None 夹在中间 ⇒ 仍不算下降（避免「没量到」被当成有序）"),
    ([5, None, 1, 0], 1, 1, "None 之后的两格照常比"),
    ([], 0, 0, "空 ⇒ 0"),
)
for _seq, _d, _u, _why in _D_CASES:
    assert _descents(_seq) == (_d, _u), \
        "descents 自测失败：%r ⇒ 期望 (%r,%r) 实际 %r（%s）" \
        % (_seq, _d, _u, _descents(_seq), _why)


def _code_only(js):
    o = []
    for line in js.split("\n"):
        t = line.strip()
        if t.startswith("//") or t.startswith("*") or t.startswith("/*"):
            continue
        o.append(line.split("//")[0])
    return "\n".join(o)


# ⭐⭐⭐⭐⭐ **新件全是纯 python** ⇒ 门挂在「不许碰浏览器 API」上。
#   ⚠️ 不用正则去抠函数体（正则抠函数体本身就是个会静默失灵的仪器）
#   ⇒ 改成**划定一段明确的下标区间**再查
_NEW_PC_START = _ME.index("def min_period(seq):")
_NEW_PC_END = _ME.index("def ev(js, arg=None):")
_NEW_PC = _code_only(_ME[_NEW_PC_START:_NEW_PC_END])
for _f in ("min_period", "_arc_of", "_descents"):
    assert ("def %s(" % _f) in _NEW_PC, "新件 %s 不在受检区间里 ⇒ 这道门是空的" % _f
for _forbidden in ("focus(", "querySelector", "document.", "addEventListener",
                   "page.", "evaluate"):
    assert _forbidden not in _NEW_PC, \
        "新件里出现了浏览器 API %r" % _forbidden
# ⭐⭐ **成对**：钉住反向 —— 这道门**必须抓得住**真代码里的 `document.`
assert "document." in _code_only("var a = 1;\nvar b = document.title;\n"), \
    "纯读守卫失灵：`document.` 在真代码里都抓不住"
assert "document." not in _code_only("var a = 1;\n// 纪律：不许 document.\n"), \
    "注释剥离守卫失灵"
# ⭐⭐⭐⭐⭐ **纯读守卫**：`DOMRANK_JS` 逐字继承 973 的那件 ⇒ 它的只读性也继承
for _forbidden in ("focus(", "MutationObserver", "addEventListener",
                   "location.reload"):
    assert _forbidden not in _code_only(DOMRANK_JS), \
        "DOMRANK_JS 里出现了 %r" % _forbidden
    assert _forbidden not in _code_only(POLL_JS), \
        "POLL_JS 里出现了 %r" % _forbidden
# ⭐⭐⭐⭐ **同一个名字、两种口径的钉子**（974 记的纪律，已复发四次）：
#   本批把 `closest_tid`（容器口径）与 `landed`（元素自己口径）**并排**读出
assert "closest_tid" in _ME and "landed" in _ME, \
    "本批把两种口径二选一了 ⇒ 981 刚踩过"
assert "canvas-fixed-toolbar" in _p981, "981 探针里没有左栏 testid ⇒ 对象变了"
# ⭐⭐⭐⭐⭐ **981 那个错数的钉子**：三个左栏按钮**各自**的 `closest_tid`
#   —— 981 说「它们的 `closest_tid` 都是 `canvas-fixed-toolbar`」，
#   而本批要把**三列并排读出来**、让读数自己说话
for _t in LEFT_RAIL_SELF:
    assert _t in _ME, "左栏自查名单缺 %r" % _t
assert WINDOW_MS >= MIN_VISIBLE_MS and N_STEPS >= 202, \
    "步数不够 2 个完整周期 ⇒ 圈长定不下来"


def ev(js, arg=None):
    if arg is None:
        return page.evaluate(js)
    return page.evaluate(js, arg)


def dump(out):
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1, default=str)


def guard(al, tid):
    t = str(tid or "")
    if any(f in t for f in FORBIDDEN_TIDS):
        raise AssertionError("⛔ 拦下计费控件：%r / %r" % (tid, al))


def guard_point(x, y):
    at = ev("""([x, y]) => {
        const el = document.elementFromPoint(x, y);
        const host = el && el.closest('[data-testid]');
        return {tid: host ? host.getAttribute('data-testid') : null,
                al: (el.innerText || el.textContent || '').slice(0, 40)};
    }""", [x, y])
    guard((at or {}).get("al"), (at or {}).get("tid"))
    return at


out = {
    "target": "source", "url": SRC_URL, "reps": REPS, "n_steps": N_STEPS,
    "window_ms": WINDOW_MS, "min_visible_ms": MIN_VISIBLE_MS,
    "node_sel": NODE_SEL, "lap_tid": LAP_TID, "rail_tid": RAIL_TID,
    "question": "⭐⭐⭐⭐⭐ **「一圈」是什么？** ⇒ 把它定义成**最小重复周期**"
                "（不读任何 testid ⇒ 没有「两种口径」），"
                "并把 973/974 的核心结论**从一个 17.8% 的小段补到 100%**",
    "ruler": {
        "js_verbatim_from_973": ["DOMRANK_JS"],
        "js_verbatim_from_979": ["POLL_JS"],
        "new_pieces": ["min_period", "_arc_of", "_descents"],
        "definition_of_lap": "⭐⭐⭐⭐⭐ **圈长 p := 满足「∀i: seq[i] == seq[i%p]」"
                              "的最小 p** ⇒ **不变量**（旋转不变、与步数无关）"
                              "、**不读任何名字**（testid 一律不进定义）",
        "why_not_rail_marker": "⭐⭐⭐⭐⭐ **左栏标记当圈界是错的** —— 981 自己的读数里 "
                               "`closest_tid == canvas-fixed-toolbar` "
                               "**240 步只命中第 84、185 拍 ⇒ 每圈 1 次**"
                               "（981 写的「约 2 次」把 2 圈的总数当成了单圈）",
        "arc_is_not_lap": "⭐⭐⭐⭐⭐ **973 报的 `arc`（19/18 格）根本不是圈** —— 读它的"
                          "源码可知 `arc` = 「`out` 行里 k 连续的第一段」"
                          "（`jimeng_probe973_ringorder_ck.py:311`），"
                          "**与 `n_rail_stops` 那套切圈毫无关系**"
                          "⇒ 源站 18/101 = **17.8%**、复刻 19/26 = 73.1%",
        "min_period_never_fails": "⚠️⭐⭐⭐ **`min_period` 永不失败**（`p == n` 恒成立）"
                                  "⇒ ① 空序列显式 `None` ② **`rem` 必须读出来**"
                                  "（980 的纪律：切圈残段不许算进分母）",
        "two_calibers_side_by_side": "⭐⭐⭐⭐ **「二选一是最坏的选择」** ⇒ 本批把 "
                                     "`descents_on_full_lap`（整圈）与 "
                                     "`descents_on_arc`（弧上，974 的 1）"
                                     "**并排**读出，**不判谁对**",
    },
    "runs": [],
}

for rep in range(1, REPS + 1):
    print("===== rep %d =====" % rep, flush=True)
    rec = {"rep": rep, "cells": []}
    out["runs"].append(rec)
    dump(out)

    page.goto(SRC_URL, wait_until="domcontentloaded", timeout=90000)
    page.wait_for_timeout(10000)
    page.set_viewport_size({"width": 1512, "height": 1200})
    page.wait_for_timeout(3000)
    n = page.locator('button[aria-label="音频"]').count()
    if n == 0:
        page.wait_for_timeout(8000)
        n = page.locator('button[aria-label="音频"]').count()
    cell = {"rep": rep, "n_ready": n, "steps": []}
    rec["cells"].append(cell)
    dump(out)
    if n == 0:
        cell["skip_note"] = "左栏入口没出来 ⇒ 本格什么也没测"
        continue

    sp = ev("""() => {
        const x = Math.floor(window.innerWidth / 2);
        const y = Math.floor(window.innerHeight * 0.92);
        const el = document.elementFromPoint(x, y);
        return (el && el.id !== 'canvas-watermark') ? [x, y] : null;
    }""")
    cell["blank"] = sp
    if sp:
        guard_point(sp[0], sp[1])      # ⛔ 守卫在 `mouse.click` **之前**
        page.mouse.click(sp[0], sp[1])
        page.wait_for_timeout(900)

    for k in range(1, N_STEPS + 1):
        page.keyboard.press("Tab")
        r = ev(POLL_JS, [WINDOW_MS])
        seq = (r or {}).get("seq") or []
        # ⭐⭐⭐⭐⭐ **落点的全文档下标要逐拍留着** —— 979 的教训：
        #   「原始读数里答案一直在」⇒ 981 只留了第一枚键，
        #   于是**整圈上的 `dom_rank` 单调性在汇总层根本无从算起**
        #   ⇒ ⇒ ⭐⭐ **汇总层要用的字段，读数层就得留着**
        dr = ev(DOMRANK_JS, [NODE_SEL]) or {}
        # ⭐⭐⭐⭐ **两种口径并排**：元素自己 vs `closest('[data-testid]')` 容器
        #   ⚠️⚠️ 981 栽在这里：`own_tid` 与 `closest_tid` **同一个名字、两种口径**
        #   ⇒ 本批把**两列都留着**，谁也不替代谁
        ct = ev("""() => {
            const a = document.activeElement;
            const h = (a && a.closest) ? a.closest('[data-testid]') : null;
            return h ? h.getAttribute('data-testid') : null;
        }""")
        cell["steps"].append({
            "k": k, "key": "Tab",
            # ⭐⭐⭐⭐ **「元素自己」那口径** = `POLL_JS` 读的元素自身键
            #   （`seq[0]["key"]`）—— 与下面 `closest_tid` **并排**，谁也不替代谁
            "landed": (seq[0]["key"] if seq else None),
            # ⭐⭐⭐⭐ **「容器」那口径** = `closest('[data-testid]')`
            "closest_tid": ct,
            "dom_rank": dr.get("dom_rank"),
            "dom_path": dr.get("dom_path"),
            "kind": dr.get("kind"),
            "is_body": dr.get("is_body"),
            "t_ms": (seq[0]["t_ms"] if seq else None),
            "elapsed_ms": (r or {}).get("elapsed_ms"),
            "n_seq": len(seq),
        })
        if k % 40 == 0:
            dump(out)

    # ── 汇总：⭐⭐ 只做计数，不下结论 ──────────────────────────────
    steps = cell["steps"]
    keys = [s["landed"] for s in steps]
    ranks = [s["dom_rank"] for s in steps]
    cell["keys"] = keys
    cell["ranks"] = ranks

    # ⭐⭐⭐⭐⭐ **「圈」= 最小重复周期**
    p = min_period(keys)
    cell["min_period"] = p
    cell["n_steps_landed"] = len(keys)
    if p:
        cell["n_full"] = len(keys) // p
        cell["rem"] = len(keys) % p
        cell["laps_identical"] = all(
            keys[i] == keys[i % p] for i in range(len(keys)))

    # ⭐⭐⭐⭐⭐ **左栏标记：每圈几次？**（更正 981 的「约 2 次」）
    cell["rail_closest_hits"] = sum(
        1 for s in steps if s.get("closest_tid") == RAIL_TID)
    cell["rail_own_hits"] = sum(1 for s in keys if s == RAIL_TID)
    cell["marker_hits"] = sum(1 for k in keys if k == LAP_TID)
    cell["left_rail_closest_tids"] = [
        s["closest_tid"] for s in steps
        if s["landed"] in LEFT_RAIL_SELF]

    if p:
        one = steps[:p]              # ⭐ 第一圈 = 完整一圈
        cell["one_lap"] = [{"i": i + 1, "landed": s["landed"],
                            "closest_tid": s["closest_tid"],
                            "dom_rank": s["dom_rank"], "kind": s["kind"]}
                           for i, s in enumerate(one)]
        # ⭐⭐⭐⭐⭐ **在整圈上重算 `dom_rank` 下降次数**（974 只在 18 格弧上算过）
        d_full, u_full = _descents([s["dom_rank"] for s in one])
        cell["descents_on_full_lap"] = d_full
        cell["n_rank_unknown_on_full_lap"] = u_full
        # ⭐⭐⭐⭐ **973/974 的口径**：`out` 行里 k 连续的第一段
        pairs = [(i + 1, s["dom_rank"]) for i, s in enumerate(one)
                 if s["kind"] == "out"]
        arc = _arc_of(pairs)
        cell["n_out_in_lap"] = len(pairs)
        cell["arc_len"] = len(arc)
        cell["arc_names"] = [one[k - 1]["landed"] for k, _rk in arc]
        d_arc, u_arc = _descents([rk for _k, rk in arc])
        cell["descents_on_arc"] = d_arc
        cell["n_rank_unknown_on_arc"] = u_arc
        cell["arc_starts_at_in_lap"] = (arc[0][0] if arc else None)
        # ⭐⭐⭐⭐ **关系式**（不钉绝对值 ⇒ 源站 DOM 每轮在动也不影响）
        cell["arc_cover_num"] = len(arc)
        cell["arc_cover_den"] = p
        cell["arc_covers_whole_lap"] = (len(arc) == p)
        cell["body_i_in_lap"] = next(
            (i + 1 for i, s in enumerate(one) if s["is_body"]), None)
        cell["marker_i_in_lap"] = next(
            (i + 1 for i, s in enumerate(one) if s["landed"] == LAP_TID), None)
        cell["n_rank_unknown_total"] = sum(1 for r in ranks if r is None)
    dump(out)

dump(out)
print("PROBE_982_DONE", flush=True)
