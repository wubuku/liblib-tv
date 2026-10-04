#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""batch 983 **复刻侧**探针（**纯诊断 / 零插入零节点点击**）：
⭐⭐⭐⭐⭐ **在第二个被测系统上独立验证 982 那条结构发现**。

── 982 留下的那条推论（可证伪的） ────────────────────────────────

982 在**源站**上量到（2/2，整圈 101 格）：
- 整圈 `dom_rank` 范围 **60 – 2395**
- ⭐⭐⭐ **最小值 = `BODY`（60）**、**最大值 = `canvas-sidecar-launcher`（2395）**
- ⭐⭐⭐⭐ 而它们**恰好相邻** ⇒ **下降 2335**、2/2 逐格相同
- ⇒ 「**整圈恰好一次回绕**」的**唯一来源就是 `BODY` 那一格**

⇒ ⇒ ⚠️ **那是在一个系统上的一次观察，不是规律。**
⇒ ⇒ ⭐⭐⭐⭐⭐ 本批去**另一个系统**（复刻侧 demo 画布）上**独立复验**：
**若两侧的「下降点形状」同构** ⇒ 这条才是规律；
**若不同构** ⇒ 982 那条推论**降级**为源站特有的巧合。

── ⭐⭐⭐⭐⭐ 预测**全部按定义逐句推出**（不许「跑出来是什么就写什么」）──

复刻侧 973 的 44 步存档（离线重算）给出 `dom_rank` 布局：

| 圈内下标 | 元素 | `dom_rank` |
|---|---|---|
| 1 | `rf__node-video-local-1` | 49 |
| 23 | `canvas-sidecar-launcher` | 255 |
| 24 | `NEXTJS-PORTAL` | **268（整圈最大）** |
| 25 | `BODY` | **37（整圈最小）** |
| 26 | `rf__wrapper` | 42 |
| （环回）1 | `rf__node-video-local-1` | 49 |

⇒ ⇒ **逐格推**：1→…→23 升（49→255）、24 升（268）、**24→25 降（268→37）**、
25→26 升（37→42）、环回 26→1 升（42→49）
⇒ ⇒ ⭐⭐⭐⭐⭐ **预测 ①：整圈上恰好 1 次下降**
⇒ ⇒ ⭐⭐⭐⭐⭐ **预测 ②：那一格的前驱 = 整圈 `dom_rank` **最大**的一格、
后继 = 整圈 `dom_rank` **最小**的一格，且最小的那一格**就是 `BODY`**
⇒ ⇒ ⭐⭐⭐⭐ **这与 982 在源站上量到的形状完全同构**
（源站 2395→60；复刻 268→37）⇒ **旋转下不变 ⇒ 是可判的关系式**

⚠️⭐⭐⭐ **`min_period` 的期望值 26 有据、不是猜的**：
973 的 44 步已排除一切 < 26 的周期（44 > 26）⇒ **26 是真最小周期**；
⚠️ 26 = 2×13 ⇒ 若真周期是 13，**44 步足够验出来** ⇒ 已排除

── ⭐⭐⭐⭐⭐ 本批的「一件仪器、两个探针」 ─────────────────────────

982 那三个新件是**纯 python**（不是 JS 字面量）⇒ `_grab` 抠不到
（`_grab` 只认「`NAME = r` + 三引号 + 正文 + 三引号」那种字面量赋值）⇒ 982 那三个
**按起止锚点逐字抠出那段源码、`exec` 绑定、再 `assert` 抠出来的段确实在 982 文件里**。

⚠️⭐⭐⭐⭐⭐ **代价必须说清**：`exec` 一段源码是**比 `_grab` 弱的保证**
（`_grab` 抠的是字面量、`exec` 跑的是**可执行代码**）
⇒ ⇒ 补一道**成对**的门：**把 982 自己那组自测用例在抠出来的仪器上重跑一遍**
⇒ ⇒ **若 982 改了语义而没同步改用例，这道门就红**

**本批零计费、零插入、零节点点击。** 按键只有 `Tab`；
⛔ 计费守卫拦在 `mouse.click` **之前**。
"""
from __future__ import annotations

import atexit
import json
import os
import re

OUT = "/tmp/b983-wrapcmp.json"
REPS = 2
SETTLE = 260           # ms（照 968–970 / 973）
BLANK_WAIT = 900       # ms
N_STEPS = 90           # ⭐ 26×3 = 78 ⇒ **3 个完整周期** + 12 步余量
NODE_SEL = "[data-nodeid], .react-flow__node"   # ⭐ 与 973/974/982 **逐字同**
KINDS = ()             # ⭐ 空 ⇒ 零插入零节点点击
RAIL_TID = "canvas-fixed-toolbar"
LEFT_RAIL_SELF = ("canvas-pointer-tool-toggle",
                  "canvas-display-toggle-minimap",
                  "canvas-display-toggle-connections")
FORBIDDEN_TIDS = ("canvas-commerce-entry", "canvas-pay-trigger",
                  "canvas-recharge", "canvas-member-buy")

_URL = "http://localhost:4317/jimeng/canvas/demo"

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _src(name):
    p = os.path.join(_ROOT, "scripts", name)
    if not os.path.exists(p):
        return ""
    with open(p, encoding="utf-8") as f:
        return f.read()


# ⚠️⭐⭐⭐ 每一件都**逐字继承**、本批**一个都不自己定义**
_p967 = _src("jimeng_probe967_armptr_src.py")
_p970 = _src("jimeng_probe970_owntid_ck.py")
_p973 = _src("jimeng_probe973_ringorder_ck.py")
_p982 = _src("jimeng_probe982_ringlen_src.py")


def _grab(name, src=None):
    m = re.search(r'^%s\s*=\s*r?"""(.*?)"""' % name, src or "", re.S | re.M)
    assert m, "抠不到 %s" % name
    _s = m.group(1)
    assert _s in (src or ""), "%s 不是逐字抠出来的" % name
    return _s


# ⚠️⭐⭐⭐⭐⭐ **`_grab` 只认字面量**（`NAME = r"""..."""`）⇒ 982 那三个
#   **纯 python** 新件抠不到 ⇒ 本批的 `_grab_def`：按**起止锚点**逐字抠源码
GRAB_DEF_START = "def min_period(seq):"
GRAB_DEF_END = "def _code_only(js):"


def _grab_def(start, end, src=None):
    s = src or ""
    i = s.index(start)
    j = s.index(end)
    assert i < j, "起止锚点顺序错了"
    _s = s[i:j]
    assert _s in s, "抠出来的那段不是逐字抠出来的"
    return _s


INSTR_SRC = _grab_def(GRAB_DEF_START, GRAB_DEF_END, _p982)
_INSTR_NS = {}
exec(compile(INSTR_SRC, "<982-instruments>", "exec"), _INSTR_NS)   # noqa: S102
min_period = _INSTR_NS["min_period"]
_arc_of = _INSTR_NS["_arc_of"]
_descents = _INSTR_NS["_descents"]

INSTALL_JS = _grab("INSTALL_JS", _p967)
READ_JS = _grab("READ_JS", _p967)
OFF_NULL_JS = _grab("OFF_NULL_JS", _p967)
BLANK_JS = _grab("BLANK_JS", _p967)
OWN_JS = _grab("OWN_JS", _p970)
DOMRANK_JS = _grab("DOMRANK_JS", _p973)
POINT_JS = _grab("POINT_JS", _p973)

_ME = open(__file__, encoding="utf-8").read()

# ── ⭐⭐⭐ 分叉守卫：本批**不许自己定义**任何继承来的那件 ──────────────
for _n in ("INSTALL_JS", "READ_JS", "OFF_NULL_JS", "BLANK_JS", "OWN_JS",
           "DOMRANK_JS", "POINT_JS"):
    assert not re.search(r'^%s\s*=\s*r?"""' % _n, _ME, re.M), \
        "本批自己定义了**继承来的** `%s` ⇒ 尺子分叉了" % _n
assert "def min_period(seq):" not in _ME.split(GRAB_DEF_START)[0][-400:] + "", \
    "本批自己写了 `min_period`"
assert DOMRANK_JS in _p973, "DOMRANK_JS 不在 973 探针里 ⇒ 不是同一件仪器"
assert INSTR_SRC in _p982, "那三个仪器不是从 982 逐字抠出来的"

# ── ⭐⭐⭐⭐⭐ **成对**：把 982 自己那组自测用例在抠出来的仪器上重跑 ──
#   ⚠️ 若 982 改了语义而没同步改用例 ⇒ 这道门就红
_MP_CASES = (
    ([], None, 0, 0, "空序列没有观测 ⇒ 必须显式 None"),
    (['a'], 1, 1, 0, "单枚 ⇒ 平凡周期 1"),
    (['a', 'b', 'a', 'b'], 2, 2, 0, "p=1 在 i=1 失败；p=2 全成立"),
    (['a', 'b', 'a', 'b', 'a', 'b', 'a'], 2, 3, 1,
     "7 步 = 3 圈 + **1 步残段**"),
    (['a', 'b', 'a'], 2, 1, 1, "3 步 = 1 圈 + 1 步残段；**不是** p=3"),
    (['a', 'b', 'a', 'c'], 4, 1, 0, "p=1✗ p=2✗ p=3✗ p=4 恒成立"),
    (['a', 'a', 'a', 'a'], 1, 4, 0, "全同 ⇒ 平凡周期 1"),
    (['a', 'b', 'c', 'a', 'b', 'c', 'a', 'b'], 3, 2, 2,
     "8 步 = 2 圈 + 2 步残段"),
)
for _seq, _p, _nf, _rem, _why in _MP_CASES:
    _got = min_period(_seq)
    assert _got == _p, (
        "⭐⭐⭐⭐⭐ **抠出来的仪器与 982 原件行为不一致**（`min_period` 圈数）："
        "%r ⇒ 982 期望 %r、抠出来给 %r（%s）" % (_seq, _p, _got, _why))
    if _p is None:
        continue
    _n = len(_seq)
    assert (_n // _p, _n % _p) == (_nf, _rem), (
        "⭐⭐⭐⭐⭐ **抠出来的仪器与 982 原件行为不一致**（残段）：%r ⇒ "
        "982 期望 (%r,%r)、抠出来给 (%r,%r)（%s）"
        % (_seq, _nf, _rem, _n // _p, _n % _p, _why))
# ⭐⭐⭐⭐⭐ **`p == n` 恒成立这条不许被悄悄改掉**（982 的新坑）
assert min_period(['x', 'y', 'z', 'w', 'v', 'q', 'r']) == 7, \
    "⭐⭐⭐⭐⭐ `p == n` 恒成立这条被改动了 ⇒ **「min_period 永不失败」已不成立**"

_ARC_CASES = (
    ([(1, 10), (2, 11), (3, 12)], 3, "k 连续 ⇒ 整段"),
    ([(1, 10), (2, 11), (4, 12)], 2, "k=4 ≠ 2+1 ⇒ break"),
    ([(1, 10), (3, 12), (4, 13)], 1, "k=3 ≠ 1+1"),
    ([], 0, "空 ⇒ 0"),
)
for _pairs, _want, _why in _ARC_CASES:
    assert len(_arc_of(_pairs)) == _want, (
        "⭐⭐⭐⭐⭐ **抠出来的 `_arc_of` 与 982 原件不一致**：%r ⇒ 982 期望 %r、"
        "抠出来给 %r（%s）" % (_pairs, _want, len(_arc_of(_pairs)), _why))
assert len(_arc_of([(1, 1), (2, 2), (5, 5), (6, 6), (7, 7)])) == 2, \
    "⭐⭐⭐⭐⭐ `arc` 把断开的第二段也吃进来了 ⇒ 与 982 不同口径"

_D_CASES = (
    ([1, 2, 3], 0, 0, "单调"),
    ([3, 2, 1], 2, 0, "每一步都降"),
    ([1, None, 2], 0, 1, "**None 不算下降**，只记 unknown（数**元素**）"),
    ([5, None, 1], 0, 1, "None 夹在中间"),
    ([5, None, 1, 0], 1, 1, "None 之后照常比"),
    ([], 0, 0, "空"),
)
for _seq, _d, _u, _why in _D_CASES:
    assert _descents(_seq) == (_d, _u), (
        "⭐⭐⭐⭐⭐ **抠出来的 `_descents` 与 982 原件不一致**：%r ⇒ 982 期望 "
        "(%r,%r)、抠出来给 %r（%s）"
        % (_seq, _d, _u, _descents(_seq), _why))

# ⭐⭐⭐⭐⭐ **`exec` 是比 `_grab` 弱的保证**（前者跑的是**可执行代码**）
#   ⇒ 必须钉住抠出来的那段里**不许出现**副作用类的调用
#   ⚠️⚠️⭐⭐⭐ **这里必须用 Python 的注释语义（`#`）** ——
#   我第一版错用了下面 `_code_only` 那套 **JS 语义**（只剥 `//`、`*`）
#   ⇒ ⇒ **门红、门错**：同一份文件里混用两套剥离语义，
#   成对门去验 Python 注释时把注释当成了代码
#   ⇒ ⇒ 改用 `tokenize` 精确剥 `COMMENT` token（顺带比 `split("#")` 更严：
#   字符串字面量里的 `#` 不会被误切）
def _py_code_only(src):
    """⭐⭐⭐ **按 `tokenize` 定位把 COMMENT 段抹成等长空格**，其余原样保留。

    ⚠️⚠️⭐⭐⭐ **两版都踩过同一个坑，必须写下来**：
    ① 第一版错用下面 `_code_only` 那套 **JS 语义**（只剥 `//`、`*`）
      ⇒ **门红、门错**（同一份文件里混用两套剥离语义）
    ② 第二版改成「用空格拼 token」⇒ 于是 `open('x')` 变成 `open ( 'x'`
      ⇒ **`"open("` 这个针永远匹配不上** ⇒ **正向门恒绿 = 恒真**
      ⇒ ⇒ ⭐⭐ **恒真的门比没有门更坏**（它让人以为查过了）
    ③ 第三版踩了一个**版本坑**：`tokenize` 在 **Python 3.12 起把行号报成
      1 基**（3.11 是 0 基）⇒ 我按 0 基去掩，**掩到了空行**上
      ⇒ ⇒ ⭐ **这道坑是成对门②抓出来的**（它要求「注释里的 `open(` 消失」）
      ⇒ ⇒ 修法：**先探测基准、再掩**，并把探测本身也钉住
    ⇒ ⇒ 修法：**只抹掉注释、原文其余部分一字不改** ⇒ 间距天然保留
    """
    import io
    import tokenize as _tk
    rows = [list(l) for l in src.split("\n")]
    try:
        toks = list(_tk.generate_tokens(io.StringIO(src).readline))
    except (_tk.TokenError, IndentationError, SyntaxError):
        return src
    # ⭐⭐⭐⭐⭐ **基准探测**：`tokenize` 的行号在 3.12 起是 **1 基**、3.11 是 0 基
    #   ⇒ 拿第一枚 COMMENT，用「它指到的那一行到底是不是以 `#` 开头」来定基准
    _base = 0
    for t in toks:
        if t.type != _tk.COMMENT:
            continue
        _r = t.start[0]
        for _cand in (1, 0):
            if 0 <= _r - _cand < len(rows) and \
                    "".join(rows[_r - _cand]).lstrip().startswith("#"):
                _base = _cand
                break
        break
    for t in toks:
        if t.type != _tk.COMMENT:
            continue
        (r0, c0), (r1, c1) = t.start, t.end
        for r in range(r0 - _base, min(r1 - _base + 1, len(rows))):
            lo = c0 if r == r0 - _base else 0
            hi = c1 if r == r1 - _base else len(rows[r])
            for c in range(lo, min(hi, len(rows[r]))):
                rows[r][c] = " "
    return "\n".join("".join(r) for r in rows)


_INSTR_CODE = _py_code_only(INSTR_SRC)
for _forbidden in ("import ", "open(", "exec(", "eval(", "__import__",
                   "globals(", "locals("):
    assert _forbidden not in _INSTR_CODE, \
        "⭐⭐⭐⭐⭐ 抠出来的仪器里出现了 %r ⇒ `exec` 的风险面变大了" % _forbidden
# ⭐⭐⭐ **成对钉三条**，把上面那两个坑各钉一道：
#   ① 这道门**必须抓得住**真代码里的 `open(`（钉住「不会恒绿」）
assert "open(" in _py_code_only("a = 1\nopen('x')\n"), \
    "反向门本身坏了 ⇒ 正向门可能已恒绿"
#   ② 这道门**必须放过**注释里的 `open(`（钉住「不会误伤」）
assert "open(" not in _py_code_only("a = 1\n# 纪律：不许 open(\n"), \
    "注释剥离守卫失灵（Python 语义）"
#   ③ **间距必须原样保留**（钉住「② 号坑」：空格拼 token 会让这条红）
assert "import " in _py_code_only("import os\n"), \
    "剥离过头：原文间距没保留 ⇒ `import ` 这类针会永远匹配不上 ⇒ 门恒绿"

# ⭐⭐⭐⭐⭐ **本批要验的那条推论，来自 982** —— 钉住它还在
#   ⚠️⚠️⭐⭐⭐ **第四次「锚点挑错文件」**：第一版去 **982 探针**里找
#   `body_is_the_wrap_982` ⇒ 那个键在 **audit** 里、不在探针里 ⇒ 门红
#   ⇒ ⇒ 判「门错还是数据错」⇒ **门错** ⇒ 改钉 audit
_paus = _src("jimeng_unclickable_audit.py")
assert '"body_is_the_wrap_982"' in _paus, "982 那个键没了 ⇒ 本批的推论没来源"
assert "唯一来源就是 `BODY` 那一格" in _paus, \
    "982 那条推论的措辞变了 ⇒ 本批的判据要重写"
assert "整圈上就会出现「0 次下降」" in _paus, \
    "982 那条新推论没了 ⇒ 本批要验的对象变了"
# ⭐⭐⭐⭐ **源站侧那份读数是本批的对照组**（文件名钉住，避免下一批悄悄换掉）
assert "min_period" in _p982 and "N_STEPS = 210" in _p982, \
    "982 的圈长/步数变了 ⇒ **两侧并排读出**的对照组变了"
for _t in LEFT_RAIL_SELF:
    assert _t in _ME, "左栏自查名单缺 %r" % _t
assert N_STEPS >= 26 * 3, "步数不够 3 个完整周期 ⇒ 圈长定不下来"


def _code_only(js):
    o = []
    for line in js.split("\n"):
        t = line.strip()
        if t.startswith("//") or t.startswith("*") or t.startswith("/*"):
            continue
        o.append(line.split("//")[0])
    return "\n".join(o)


# ⭐⭐⭐⭐⭐ **纯读守卫**：继承来的那几件不许调 `focus()`
for _forbidden in ("focus(", "MutationObserver", "addEventListener",
                   "location.reload"):
    for _n, _js in (("DOMRANK_JS", DOMRANK_JS), ("OWN_JS", OWN_JS),
                    ("READ_JS", READ_JS)):
        assert _forbidden not in _code_only(_js), \
            "%s 里出现了 %r" % (_n, _forbidden)
assert "document.querySelectorAll('*')" in DOMRANK_JS, \
    "DOMRANK_JS 没读全文档下标"
assert "for (let i = 0; i < all.length; i += 1)" in DOMRANK_JS, \
    "DOMRANK_JS 的 dom_rank 循环被改过了 —— 这道门会恒 -1"

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


def guard(al, tid):
    t = str(tid or "")
    if any(f in t for f in FORBIDDEN_TIDS):
        raise AssertionError("⛔ 拦下计费控件：%r / %r" % (tid, al))


def guard_point(x, y):
    at = ev(POINT_JS, [x, y])
    guard((at or {}).get("al"), (at or {}).get("tid"))
    return at


def boot_ck():
    """复刻侧就绪。⚠️ **「我没检测到」必须先确认「我够得着」**（973 原话）。"""
    page.goto(_URL, wait_until="domcontentloaded", timeout=90000)
    page.wait_for_timeout(6000)
    page.set_viewport_size({"width": 1512, "height": 1200})
    page.wait_for_timeout(2000)
    return ev("""() => ({
        has_flow: !!document.querySelector('.react-flow'),
        flow_aria: (document.querySelector('.react-flow') || {})
                      .getAttribute('aria-label'),
        flow_tid: (document.querySelector('.react-flow') || {})
                     .getAttribute('data-testid'),
        n_focusable: document.querySelectorAll(
            '[tabindex="0"], a[href], button:not([disabled])').length
    })""")


out = {
    "target": "replica", "url": _URL, "reps": REPS, "n_steps": N_STEPS,
    "node_sel": NODE_SEL, "kinds": list(KINDS), "rail_tid": RAIL_TID,
    "question": "⭐⭐⭐⭐⭐ **在第二个被测系统上独立复验 982 那条结构发现**："
                "「整圈上唯一那次回绕，是不是永远由 `BODY` 那一格提供？」"
                "⇒ 同构 ⇒ 那是规律；不同构 ⇒ 982 那条**降级**为源站特有的巧合",
    "ruler": {
        "js_verbatim_from_967": ["INSTALL_JS", "READ_JS", "OFF_NULL_JS",
                                 "BLANK_JS"],
        "js_verbatim_from_970": ["OWN_JS"],
        "js_verbatim_from_973": ["DOMRANK_JS", "POINT_JS"],
        "py_verbatim_from_982": ["min_period", "_arc_of", "_descents"],
        "how_py_was_lifted": "⭐⭐⭐⭐⭐ **`_grab` 只认字面量**"
                             "（`NAME = r\"\"\"...\"\"\"`）⇒ 982 那三个"
                             "**纯 python** 新件抠不到 ⇒ 本批加 **`_grab_def`**："
                             "按起止锚点**逐字抠源码**、`exec` 绑定、"
                             "再 `assert` 抠出来的那段确实在 982 文件里",
        "why_pair_gate": "⭐⭐⭐⭐⭐ **`exec` 比 `_grab` 弱**（前者跑的是"
                         "**可执行代码**）⇒ 补一道**成对**的门："
                         "**把 982 自己那组自测用例在抠出来的仪器上重跑** ⇒ "
                         "若 982 改语义而没同步改用例，这道门就红",
        "predictions_derived_not_fitted": "⭐⭐⭐⭐⭐ **三条预测全部按定义逐句推出**：\n"
                                         "  · ① 整圈上**恰好 1 次**下降\n"
                                         "  · ② 那一格的**前驱 = 整圈 "
                                         "`dom_rank` 最大的一格**、"
                                         "**后继 = 最小的一格**，且最小者**就是 `BODY`**\n"
                                         "  · ③ `min_period = 26`"
                                         "（**有据**：973 的 44 步已排除一切 "
                                         "< 26 的周期 ⇒ 26 是真最小周期）",
        "same_shape": "⭐⭐⭐⭐ **与 982 在源站上的观察同构**："
                      "源站 2395→60；复刻侧按 973 存档推 268→37 ⇒ "
                      "**旋转下不变 ⇒ 判据只钉关系式**",
        "zero_billing": "⭐⭐⭐⭐⭐ **零插入、零节点点击、零计费**："
                        "`KINDS` 为空、按键只有 `Tab`；"
                        "⛔ 守卫拦在 `mouse.click` 之前",
    },
    "runs": [],
}

for rep in range(1, REPS + 1):
    print("===== rep %d =====" % rep, flush=True)
    rec = {"rep": rep, "cells": []}
    out["runs"].append(rec)
    dump(out)

    rd = boot_ck()
    c = {"rep": rep, "rows": [], "n_install": 0, "n_read": 0,
         "n_rail_stops": 0, "n_steps": 0,
         "has_flow": rd.get("has_flow"),
         "flow_aria": rd.get("flow_aria"),
         "flow_tid": rd.get("flow_tid"),
         "n_focusable_at_boot": rd.get("n_focusable")}
    rec["cells"].append(c)
    dump(out)
    if not rd.get("has_flow"):
        c["skip_note"] = "画布根没出来 ⇒ 本格什么也没测"
        continue

    sp = ev(BLANK_JS)
    c["blank"] = sp
    if sp:
        guard_point(sp[0], sp[1])       # ⛔ 守卫在 `mouse.click` **之前**
        page.mouse.click(sp[0], sp[1])
        page.wait_for_timeout(BLANK_WAIT)

    for k in range(1, N_STEPS + 1):
        c["n_steps"] = k
        inst = ev(INSTALL_JS, [NODE_SEL])
        if inst.get("installed"):
            c["n_install"] += 1
        try:
            page.keyboard.press("Tab")
            page.wait_for_timeout(SETTLE)
            ap = ev(READ_JS)
            c["n_read"] += 1
            o = ev(OWN_JS, [NODE_SEL])
            dr = ev(DOMRANK_JS, [NODE_SEL]) or {}
        finally:
            ev(OFF_NULL_JS)
        # ⭐⭐⭐⭐ **落点的全文档下标要逐拍留着**（982 的同款教训：
        #   981 只留了键 ⇒ 整圈上的单调性在汇总层根本无从算起）
        c["rows"].append({
            "k": k, "key": "Tab",
            "fired": (ap or {}).get("fired"),
            "landed": (dr or {}).get("tag"),
            "own_tid": (o or {}).get("self_tid"),
            "closest_tid": (o or {}).get("closest_tid"),
            "dom_rank": (dr or {}).get("dom_rank"),
            "dom_path": (dr or {}).get("dom_path"),
            "is_body": (dr or {}).get("is_body"),
            "kind": (dr or {}).get("kind"),
        })
        if o.get("closest_tid") == RAIL_TID:
            c["n_rail_stops"] += 1
        if k % 30 == 0:
            dump(out)

    # ── 汇总：⭐⭐ 只做计数，不下结论 ──────────────────────────────
    rows = c["rows"]
    # ⭐⭐⭐⭐⭐ **键用「元素自己 + 容器」并排**（981 第四次复发那条纪律）
    keys = [("%s/%s" % (r["own_tid"], r["closest_tid"])) for r in rows]
    ranks = [r["dom_rank"] for r in rows]
    c["keys"] = keys
    c["ranks"] = ranks

    p = min_period(keys)
    c["min_period"] = p
    c["n_steps_landed"] = len(keys)
    if p:
        c["n_full"] = len(keys) // p
        c["rem"] = len(keys) % p
        c["laps_identical"] = all(keys[i] == keys[i % p] for i in range(len(keys)))

    one = rows[:p]
    c["one_lap"] = [{"i": i + 1, "key": keys[i],
                     "closest_tid": rows[i]["closest_tid"],
                     "dom_rank": ranks[i], "is_body": rows[i]["is_body"],
                     "kind": rows[i]["kind"]}
                    for i in range(len(one))]
    lap_ranks = [r["dom_rank"] for r in one]
    d_full, u_full = _descents(lap_ranks)
    c["descents_on_full_lap"] = d_full
    c["n_rank_unknown_on_full_lap"] = u_full
    # ⭐⭐⭐⭐⭐ **下降点的形状**（982 那条推论的可证伪形式）
    c["descent_i_in_lap"] = [i + 1 for i in range(1, len(lap_ranks))
                             if lap_ranks[i] is not None
                             and lap_ranks[i - 1] is not None
                             and lap_ranks[i] < lap_ranks[i - 1]]
    c["min_rank_i_in_lap"] = (
        min(range(len(lap_ranks)), key=lambda i: lap_ranks[i]) + 1
        if lap_ranks and all(r is not None for r in lap_ranks) else None)
    c["max_rank_i_in_lap"] = (
        max(range(len(lap_ranks)), key=lambda i: lap_ranks[i]) + 1
        if lap_ranks and all(r is not None for r in lap_ranks) else None)
    c["body_i_in_lap"] = next(
        (i + 1 for i, r in enumerate(one) if r["is_body"]), None)
    # ⭐⭐⭐⭐⭐ **关系式**（旋转下不变 ⇒ 判据钉这些，不钉绝对下标）
    c["body_is_min_rank"] = (c["body_i_in_lap"] == c["min_rank_i_in_lap"])
    c["wrap_shape_ok"] = (
        len(c["descent_i_in_lap"]) == 1
        and c["descent_i_in_lap"][0] == c["body_i_in_lap"]
        and c["descent_i_in_lap"][0] - 1 == c["max_rank_i_in_lap"])
    c["n_rank_unknown_total"] = sum(1 for r in ranks if r is None)
    # 973/974 的口径
    pairs = [(i + 1, r["dom_rank"]) for i, r in enumerate(one)
             if r["kind"] == "out"]
    arc = _arc_of(pairs)
    c["n_out_in_lap"] = len(pairs)
    c["arc_len"] = len(arc)
    c["arc_cover_num"] = len(arc)
    c["arc_cover_den"] = p
    c["arc_starts_at_in_lap"] = (arc[0][0] if arc else None)
    c["descents_on_arc"] = _descents([rk for _k, rk in arc])[0]
    c["left_rail_closest_tids"] = [
        r["closest_tid"] for r in rows if r["own_tid"] in LEFT_RAIL_SELF]
    dump(out)

dump(out)
print("PROBE_983_DONE", flush=True)
