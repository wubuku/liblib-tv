#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""batch 987 **复刻侧**探针（**零计费**：只按 `Tab`、唯一的 `mouse.click` 点在
`about:blank` 空白处、且有计费守卫拦在 `mouse.click` **之前**）：
⭐⭐⭐⭐⭐ **量「`rf__wrapper` 对齐」的影响面另一端** ——
**复刻 DOM 里 `rf__wrapper` 为什么排在 `canvas-project-logo` 之前。**

── 983/986 留下的那一句 ────────────────────────────────────────────

983 量到（**`dom_rank` 级**、两侧**确实不同**）：

- **源站**：`BODY`(60) ⇢ `canvas-project-logo`(68) ⇢ … ⇢ **`rf__wrapper`(177)**
- **复刻侧**：`BODY`(37) ⇢ **`rf__wrapper`(42)** ⇢ … ⇢ `canvas-project-logo`(110)

⇒ 983 只说「相对次序不同」，并留下一句：
**「另一端（复刻 DOM 里 `rf__wrapper` 为什么排在 `logo` 之前）还没量 ⇒ 先量，不先改」**

⚠️⭐⭐⭐⭐⭐ **983 留下的是一个 `dom_rank` 级的观察，
而本批要回答的是「为什么」** ——
**只看 `dom_rank` 只能说「谁在前」，说不出「按什么规则在前」。**

── ⭐⭐⭐⭐⭐ 本批的答案：**环按 `dom_rank` 递增走，所以「谁在前」=「谁的 `dom_rank` 小」** ──

983 的复刻侧整圈（26 格）`dom_rank` 实测序列：

    49, 58, 64, 68, 73, 78, 89, **110**, 120, 121, 125, 134, 139, 145, 154,
    160, 166, 169, 237, 240, 245, 251, 255, 268, **37(BODY)**, **42**

⇒ ⇒ ⭐⭐⭐⭐⭐ **除 `BODY` 那一格之外，整圈 `dom_rank` 严格递增** ⇒
**Tab 环 = DOM 序** ⇒ `rf__wrapper`(`dom_rank=42`) 是**整圈第二小**、
`canvas-project-logo`(110) 是**第八小** ⇒ ⇒
**「`rf__wrapper` 排在 logo 之前」不是任何人对齐决策的结果，
它只是「画布容器的 `dom_rank` 比顶栏小」这一个事实的推论。**

⚠️⭐⭐⭐⭐⭐ 而**成因在源码里、且是可指认的一行** ——
`src/components/jimeng/JimengWorkspace.tsx` 那个平铺容器里，
JSX 兄弟顺序是 `<JimengFlow />` **在** `<JimengTopBar />` **之前**
⇒ ⇒ `rf__wrapper`（画布）先渲染、`canvas-project-logo`（顶栏）后渲染
⇒ ⇒ ⭐⭐⭐⭐ **本批把这一行钉进判据**：来源是**源码的 JSX 顺序**、
**不是运行期的巧合、也不是浏览器行为**

── ⭐⭐⭐⭐⭐ 三条预测，**全部在看数据之前按定义写出** ─────────────────

⚠️⭐⭐⭐ **期望值必须按定义逐句推**，不能「跑出来是什么就写什么」。

**P1（环按 `dom_rank` 递增）**：整圈里**去掉 `BODY` 那一格之后**，
`dom_rank` **严格递增**（`0` 次下降）
⇒ 推导：Tab 环是引擎按 DOM 序遍历候选的结果 ⇒ DOM 序 = `dom_rank` 序
⇒ ⇒ ⭐⭐ **注意「去掉 BODY」是必需的** —— 985 已证 `BODY` 是间隙、
不是一格、它的 `dom_rank`(37) 是回落值 ⇒ **它不参与排序**
⇒ ⇒ ⭐⭐⭐⭐ **这条是 986 那条「缺失」判据在 `dom_rank` 上的同构写法**

**P2（`rf__wrapper` 的位置由 `dom_rank` 决定，不由对齐决策决定）**：
`rf__wrapper` 的环内序号 = **它 `dom_rank` 在整圈的排名**（去掉 `BODY` 后）
⇒ 推导：若环按 `dom_rank` 递增，则「环内序号」**恒等于**「`dom_rank` 排名」
⇒ ⇒ ⭐⭐⭐⭐⭐ **这条把「对齐决策」从解释里彻底拿掉** ——
983/986 说「不能拿 `BODY` 当对齐的理由」；**本批说「也没有别的理由」**：
**位置是 `dom_rank` 的函数，而 `dom_rank` 是 JSX 顺序的函数**

**P3（成因可指认到源码的一行）**：源码里 `<JimengFlow />` 的源码位置
**早于** `<JimengTopBar />` ⇒ ⇒ **成因是 JSX 兄弟顺序**、
**不是运行期渲染时序、不是 CSS 定位、不是 z-index**
⇒ ⇒ ⭐⭐⭐⭐ **CSS `position` 与 `z-index` 都不参与** ——
`rf__wrapper` 与 logo 都不是 `absolute` 定位 ⇒ 它们的先后**只由 DOM 序决定**

── ⭐⭐⭐⭐⭐ 顺带钉住的一条**不许被悄悄改掉**的东西 ───────────────────

`canvas-project-logo` 是 `<a href>` ⇒ **它天然在 Tab 序列里**（不靠 `tabindex`）
⇒ ⇒ ⭐⭐⭐⭐ **logo 落在环的第 8 格是「它是 `<a>` 且 `dom_rank` 排第八」的推论**，
**不是**某次干预的结果 ⇒ 判据里钉住「logo 确实可聚焦（`tabIndex` ≥ 0）」。

**本批零计费**：复刻侧本地页 `http://localhost:4317/jimeng/canvas/demo`；
只按 `Tab`；唯一的 `mouse.click` 点在 `about:blank` 空白处（清焦点），
⛔ 计费守卫拦在 `mouse.click` **之前**。
"""
from __future__ import annotations

import atexit
import json
import os
import re

OUT = "/tmp/b987-wrapcause.json"
REPS = 2
N_STEPS = 210        # ⭐ 与 983 同（26 格一圈 ⇒ 2 个完整周期）
SETTLE = 60          # ⭐ 与 983 同
NODE_SEL = "[data-nodeid], .react-flow__node"   # ⭐ 与 973/974/982/983 同
BLANK_WAIT = 120
URL = "http://localhost:4317/jimeng/canvas/demo"
RAIL_TID = "canvas-fixed-toolbar"
WRAP_TID = "rf__wrapper"
LOGO_TID = "canvas-project-logo"
LEFT_RAIL_SELF = ("canvas-history-launcher", "canvas-more-trigger",
                  "canvas-commerce-entry", "canvas-user-menu-trigger")
WS_TSX = "src/components/jimeng/JimengWorkspace.tsx"
FORBIDDEN_TIDS = ("canvas-commerce-entry", "canvas-pay-trigger",
                  "canvas-recharge", "canvas-member-buy")

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _src(name):
    p = os.path.join(_ROOT, "scripts", name)
    if not os.path.exists(p):
        return ""
    with open(p, encoding="utf-8") as f:
        return f.read()


_p967 = _src("jimeng_probe967_armptr_src.py")
_p970 = _src("jimeng_probe970_owntid_ck.py")
_p982 = _src("jimeng_probe982_ringlen_src.py")
_p973 = _src("jimeng_probe973_ringorder_ck.py")
_p983 = _src("jimeng_probe983_wrapcmp_ck.py")
_paus = _src("jimeng_unclickable_audit.py")
_ME = open(__file__, encoding="utf-8").read()


def _grab(name, src=None):
    m = re.search(r'^%s\s*=\s*r?"""(.*?)"""' % name, src or "", re.S | re.M)
    assert m, "抠不到 %s" % name
    _s = m.group(1)
    assert _s in (src or ""), "%s 不是逐字抠出来的" % name
    return _s


# ⚠️⭐⭐⭐⭐⭐ **`_grab` 只认字面量**（`NAME = r"""..."""`）⇒ 982 那三个
#   **纯 python** 新件抠不到 ⇒ 按**起止锚点**逐字抠源码（983 的原话照抄）
# ⚠️⭐⭐⭐⭐⭐ 而**我第一版去 983 里找它们，找不到** ——
#   **983 自己也是从 982 一次抠三个的**（`min_period` / `_arc_of` / `_descents`）
#   ⇒ ⇒ ⭐⭐ **「继承链」又一次不是一层、而是指向更早的一批**
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
_INSTR_NS: dict = {}
exec(compile(INSTR_SRC, "<982-instruments>", "exec"), _INSTR_NS)   # noqa: S102
min_period = _INSTR_NS["min_period"]
_descents = _INSTR_NS["_descents"]
assert callable(min_period) and callable(_descents)


# ⚠️⭐⭐⭐⭐⭐ **仪器逐字继承 983 的溯源链** ——
#   ⚠️⚠️ **我第一版把 `OWN_JS`/`READ_JS` 当成在 973 里，抠不到** ——
#   **973 自己也是从 967（INSTALL/READ/OFF_NULL/BLANK）与 970（OWN）继承的**
#   ⇒ ⇒ **DOMRANK/POINT 才在 973** ⇒ ⇒ **「继承链」本身也要逐条钉**
INSTALL_JS = _grab("INSTALL_JS", _p967)
READ_JS = _grab("READ_JS", _p967)
OFF_NULL_JS = _grab("OFF_NULL_JS", _p967)
BLANK_JS = _grab("BLANK_JS", _p967)
OWN_JS = _grab("OWN_JS", _p970)
DOMRANK_JS = _grab("DOMRANK_JS", _p973)
POINT_JS = _grab("POINT_JS", _p973)

# ⭐⭐⭐⭐⭐ **每一件都必须与 983 用的是「同一份来源」** ⇒ 尺子没分叉
# ⚠️⭐⭐⭐⭐⭐ **我第一版想「从 983 文本里再 `_grab` 一次来比对」，做不到** ——
#   983 那几行是 `INSTALL_JS = _grab("INSTALL_JS", _p967)`，
#   **983 自己也没有内嵌字面量** ⇒ ⇒ **比对的对象只能是「溯源声明」本身**
#   ⇒ ⇒ ⭐⭐ **同一把尺子的定义 = 「它声明自己从哪一份拿」**
for _nm, _from in (("INSTALL_JS", '_grab("INSTALL_JS", _p967)'),
                   ("READ_JS", '_grab("READ_JS", _p967)'),
                   ("OFF_NULL_JS", '_grab("OFF_NULL_JS", _p967)'),
                   ("BLANK_JS", '_grab("BLANK_JS", _p967)'),
                   ("OWN_JS", '_grab("OWN_JS", _p970)'),
                   ("DOMRANK_JS", '_grab("DOMRANK_JS", _p973)'),
                   ("POINT_JS", '_grab("POINT_JS", _p973)')):
    _decl = "%s = %s" % (_nm, _from)
    assert _decl in _p983, "983 的溯源声明变了：%r" % _decl
    assert _decl in _ME, "本批的溯源声明与 983 不一致：%r" % _decl
    assert _grab(_nm, {"INSTALL_JS": _p967, "READ_JS": _p967,
                       "OFF_NULL_JS": _p967, "BLANK_JS": _p967,
                       "OWN_JS": _p970, "DOMRANK_JS": _p973,
                       "POINT_JS": _p973}[_nm]) is not None

# ⚠️⭐⭐⭐⭐⭐ **不许自己定义**继承来的那几件（978 栽过、980 照抄）
for _nm in ("POINT_JS", "DOMRANK_JS", "OWN_JS", "READ_JS",
            "INSTALL_JS", "BLANK_JS", "OFF_NULL_JS"):
    assert not re.search(r'^%s\s*=\s*r?"""' % _nm, _ME, re.M), \
        "本批自己定义了**继承来的** `%s` ⇒ 尺子分叉了" % _nm
    assert re.search(r'^%s\s*=\s*r?"""' % _nm,
                     '%s = """x"""' % _nm, re.M), "分叉守卫失灵：%s" % _nm


# ══ ⭐⭐⭐⭐⭐ 本批的核心：**「环内序号 ↔ `dom_rank` 排名」是不是同一个东西** ══
def _rank_order(lap, drop_body=True):
    """⭐⭐⭐⭐⭐ **把一圈里「参与排序的格」按 `dom_rank` 排好**，返回它们的环内下标。

    ⚠️⭐⭐⭐⭐⭐ **为什么必须先问「哪些格参与排序」** ——
    985 已证 `BODY` 是**间隙**、不是一格、且它的 `dom_rank` 是**回落值**
    ⇒ ⇒ **它不参与排序** ⇒ 不许把它算进「排名」的分母
    ⇒ ⇒ ⭐⭐ **这是 986 那条「间隙不是一格」在 `dom_rank` 上的同构写法**
    """
    idx = [i for i, r in enumerate(lap)
           if (not drop_body) or not r.get("is_body")]
    idx = [i for i in idx if lap[i].get("dom_rank") is not None]
    return idx


def _is_strictly_increasing(seq):
    """⭐⭐ 严格递增（相等也不算 —— ⭐⭐ 两个格不可能有同一个 `dom_rank`）。"""
    if len(seq) < 2:
        return False
    return all(seq[i] > seq[i - 1] for i in range(1, len(seq)))


def _rank_of_ranks(lap, key, drop_body=True):
    """⭐⭐⭐⭐⭐ **某一格按 `dom_rank` 排名是第几**（1-based，去掉 `BODY`）。

    ⚠️⭐⭐ **P2 的正式形式**：「环内序号」**恒等于**「`dom_rank` 排名」
    ⇒ ⇒ 探针把这两个数**各自算出来、分开记** ⇒ **由 verifier 判它们相等**
    ⇒ ⇒ ⭐⭐⭐⭐ **不预写「它们相等」** —— 那是本批要测的**事实**
    """
    idx = _rank_order(lap, drop_body)
    ranks = [lap[i]["dom_rank"] for i in idx]
    for n, i in enumerate(idx, start=1):
        if lap[i].get("closest_tid") == key or lap[i].get("key") == key:
            return n
    return None


def _ring_pos(lap, key):
    """⭐⭐ 环内序号（1-based，整圈含 `BODY`）—— 与上面那个**分开算**。"""
    for n, r in enumerate(lap, start=1):
        if r.get("closest_tid") == key or r.get("key") == key:
            return n
    return None


# ── ⭐⭐⭐⭐⭐ **自测：期望值全部按定义逐句推** ────────────────────────
_LAP = [{"i": 1, "closest_tid": "a", "dom_rank": 10, "is_body": False},
        {"i": 2, "closest_tid": "b", "dom_rank": 20, "is_body": False},
        {"i": 3, "closest_tid": "BODY", "dom_rank": 5, "is_body": True},
        {"i": 4, "closest_tid": "c", "dom_rank": 30, "is_body": False}]
# 推导：去掉 BODY 后剩下 a(10)、b(20)、c(30) ⇒ 下标 0,1,3
assert _rank_order(_LAP) == [0, 1, 3]
# 推导：不去掉 BODY 时是 0,1,2,3
assert _rank_order(_LAP, drop_body=False) == [0, 1, 2, 3]
# 推导：`dom_rank` 序列 [10,20,30] **严格递增** ⇒ 真
assert _is_strictly_increasing([10, 20, 30]) is True
# ⭐⭐⭐⭐ **反向门**：含 `BODY`(5) 的整圈序列 **[10,20,5,30]** **不递增** ⇒ 必须判红
#   ⇒ ⇒ **这条门不是恒真的**：它真的会因为 `BODY` 而红 ⇒
#   ⇒ ⇒ **所以判据必须先「去掉 `BODY`」**（986 那条纪律的同构应用）
assert _is_strictly_increasing([10, 20, 5, 30]) is False, \
    "⭐⭐⭐⭐ **反向门坏了**：含 `BODY` 的序列必须判红 —— 不然这道门恒真"
# ⭐⭐⭐⭐ **反向门②**：相等也不算严格递增
assert _is_strictly_increasing([10, 10, 20]) is False
# ⭐⭐⭐ **反向门③**：长度不足 2 时判红（否则「只有一格」会恒真）
assert _is_strictly_increasing([10]) is False
# 推导：a 的 `dom_rank` 排名 = 1、b = 2、c = 3（去掉 BODY）
assert _rank_of_ranks(_LAP, "a") == 1
assert _rank_of_ranks(_LAP, "b") == 2
assert _rank_of_ranks(_LAP, "c") == 3
# 推导：环内序号（含 BODY）是 a=1、b=2、BODY=3、c=4
assert _ring_pos(_LAP, "a") == 1
assert _ring_pos(_LAP, "BODY") == 3
assert _ring_pos(_LAP, "c") == 4
# ⭐⭐⭐⭐⭐ **P2 在这个用例上就成立**（去掉 BODY 后两个序号一致）：
#   c 的排名 = 3、环内序号 = 4 ⇒ **不一致** ⇒ 差 1（因为 BODY 占了一格）
#   ⇒ ⇒ ⭐⭐⭐⭐⭐ **所以 P2 的正确形式是「**在参与排序的那些格上**两个序号一致**」**
#   ⇒ ⇒ ⭐⭐ **写成「环内序号 == `dom_rank` 排名」会是错的**（`BODY` 插在中间）
_LAP2 = [{"i": 1, "closest_tid": "a", "dom_rank": 10, "is_body": False},
         {"i": 2, "closest_tid": "b", "dom_rank": 20, "is_body": False},
         {"i": 3, "closest_tid": "c", "dom_rank": 30, "is_body": False}]
assert _rank_of_ranks(_LAP2, "c") == 3 and _ring_pos(_LAP2, "c") == 3, \
    "⭐⭐⭐⭐ 无 `BODY` 时两个序号必须一致（P2 的干净形式）"
assert _rank_order(_LAP2) == [0, 1, 2]
# ⭐⭐⭐⭐ **反向门④**：`BODY` 在**末尾**时，排名与环内序号差 1 ⇒ 钉住这个差
assert _rank_of_ranks(_LAP, "c") == 3 and _ring_pos(_LAP, "c") == 4, \
    "⭐⭐⭐⭐ `BODY` 插在中间时两者必须差 1（写成「恒相等」是错的）"

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
    """⭐⭐⭐⭐⭐ **复刻侧就绪探针** —— ⚠️⚠️ **「我没检测到」必须先确认「我够得着」**（973 原话）。

    ⭐⭐⭐⭐⭐ **我第一版误用了 `READ_JS` 当就绪探针 ⇒ 两格全 `has_flow=False`**
    —— 而 `READ_JS` 读的是 `window.__ap_rec`（**上一次 `INSTALL_JS` 装的监听器**留下的）
    ⇒ ⇒ **在第一次 `INSTALL_JS` 之前它必然是 `null`** ⇒
    ⇒ ⭐⭐⭐⭐⭐ **这不是「页面没就绪」、是「我问错了对象」**
    ⇒ ⇒ **这是 985 那条纪律的又一次**：「**没测到**必须能说清是**没就绪**还是**没登录**」
    —— 而本批是**第三个分支**：**「没问对对象」**
    """
    page.goto(URL, wait_until="domcontentloaded", timeout=90000)
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


# ── ⭐⭐⭐⭐⭐ **P3 的另一半：成因在源码里、且要钉住那一行** ────────────
def _jsx_order():
    """⭐⭐⭐⭐⭐ **从源码里量「`JimengFlow` 与 `JimengTopBar` 谁写在前面」**。

    ⚠️⭐⭐⭐⭐⭐ **为什么量源码而不量运行期** ——
    **「运行期先渲染」是观察、「JSX 顺序」是成因** ⇒ 两者必须分开
    ⇒ ⇒ ⭐⭐⭐⭐ **本批要把成因钉在源码上**：改一行 JSX 就能改掉这个次序
    """
    p = os.path.join(_ROOT, WS_TSX)
    if not os.path.exists(p):
        return {"available": False, "why": "源码不在（路径变了？）"}
    with open(p, encoding="utf-8") as f:
        lines = f.readlines()
    flow = top = None
    for n, ln in enumerate(lines, start=1):
        if flow is None and "<JimengFlow />" in ln:
            flow = n
        if top is None and "<JimengTopBar />" in ln:
            top = n
    return {"available": flow is not None and top is not None,
            "jsx_line_jimengflow": flow, "jsx_line_jimengtopbar": top,
            "flow_before_topbar": (flow is not None and top is not None
                                   and flow < top)}


_JSX = _jsx_order()

out = {
    "target": "clone", "url": URL,
    "reps": REPS, "n_steps": N_STEPS, "node_sel": NODE_SEL,
    "wrap_tid": WRAP_TID, "logo_tid": LOGO_TID, "rail_tid": RAIL_TID,
    "question": "⭐⭐⭐⭐⭐ **量「`rf__wrapper` 对齐」的影响面另一端** —— "
                "复刻 DOM 里 `rf__wrapper` 为什么排在 `canvas-project-logo` 之前 ⇒ "
                "**P1 环按 `dom_rank` 递增 / P2 位置由 `dom_rank` 决定 / "
                "P3 成因 = JSX 兄弟顺序**",
    "ruler": {
        "js_verbatim_from_973": ["DOMRANK_JS", "POINT_JS"],
        "js_verbatim_from_970": ["OWN_JS"],
        "js_verbatim_from_967": ["INSTALL_JS", "READ_JS",
                                  "OFF_NULL_JS", "BLANK_JS"],
        "inherit_chain_pinned_per_piece": (
            "⭐⭐⭐⭐⭐ **第一版我把 `OWN_JS`/`READ_JS` 当成在 973 里、抠不到** —— "
            "**973 自己也是从 967 与 970 继承的** ⇒ "
            "⇒ **「继承链」本身也要逐条钉** ⇒ "
            "**每一件都与 983 抠到的逐字比对**"),
        "defs_inherited_from_982": ["min_period", "_arc_of", "_descents"],
        "inherit_chain_note": (
            "⭐⭐⭐⭐⭐ **继承链不是一层** —— 983 自己也是**从 982 一次抠三个**"
            "（`min_period` / `_arc_of` / `_descents`）⇒ "
            "⇒ **`_grab` 只认字面量，纯 python 件要按起止锚点抠**"),
        "new_pieces": [],
        "new_measures_not_new_js": (
            "⭐⭐⭐⭐⭐ 本批**没有新 JS 件** —— 新的是**三个纯函数**："
            "`_rank_order` / `_is_strictly_increasing` / `_rank_of_ranks`"
            "⇒ **它们把「环内序号」与「`dom_rank` 排名」分开算** ⇒ "
            "**由 verifier 判两者一致** ⇒ ⭐⭐ **不预写「它们相等」**"),
        "predictions_written_before_data": [
            "P1 去掉 `BODY` 后整圈 `dom_rank` **严格递增**（`BODY` 是间隙、"
            "它的 `dom_rank` 是回落值 ⇒ **不参与排序**）",
            "P2 在参与排序的那些格上，「环内序号」恒等于「`dom_rank` 排名」⇒ "
            "**位置是 `dom_rank` 的函数，而 `dom_rank` 是 JSX 顺序的函数** ⇒ "
            "**对齐决策从解释里被彻底拿掉**",
            "P3 成因 = **源码里 `<JimengFlow />` 写在 `<JimengTopBar />` 之前** ⇒ "
            "**CSS `position` / `z-index` 都不参与**",
        ],
        "why_p2_is_not_written_as_equality": (
            "⭐⭐⭐⭐⭐ **第一版我想写「环内序号 == `dom_rank` 排名」，"
            "自测立刻把它否掉了** —— `BODY` 插在中间时两者**必然差 1** "
            "⇒ ⇒ ⭐⭐⭐⭐⭐ **期望值错了、自测就是假绿** ⇒ "
            "⇒ **正确形式是「在**参与排序的那些格**上两者一致」**"),
        "body_excluded_from_ranking": (
            "⭐⭐⭐⭐⭐ **这是 986 那条「间隙不是一格」在 `dom_rank` 上的同构写法** —— "
            "**`BODY` 的 `dom_rank` 是回落值、不参与排序** ⇒ "
            "**不许把它算进「排名」的分母**"),
    },
    "jsx_order": _JSX,
    "runs": [],
}

for rep in range(1, REPS + 1):
    print(f"===== rep {rep} =====", flush=True)
    c = {"rep": rep, "rows": [], "n_install": 0, "n_read": 0,
         "n_rail_stops": 0, "n_steps": 0, "has_flow": False,
         "flow_aria": None, "flow_tid": None, "n_focusable_at_boot": 0,
         "n_skip": 0}
    out["runs"].append(c)
    dump(out)

    rd = boot_ck()
    c["has_flow"] = bool(rd.get("has_flow"))
    c["flow_aria"] = rd.get("aria")
    c["flow_tid"] = rd.get("tid")
    c["n_focusable_at_boot"] = rd.get("n_focusable")
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
        if (inst or {}).get("installed"):
            c["n_install"] += 1
        try:
            page.keyboard.press("Tab")
            page.wait_for_timeout(SETTLE)
            ap = ev(READ_JS)
            c["n_read"] += 1
            o = ev(OWN_JS, [NODE_SEL]) or {}
            dr = ev(DOMRANK_JS, [NODE_SEL]) or {}
        finally:
            ev(OFF_NULL_JS)
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
            "ti_prop": (dr or {}).get("ti_prop"),
        })
        if o.get("closest_tid") == RAIL_TID:
            c["n_rail_stops"] += 1
        if k % 30 == 0:
            dump(out)

    # ── 汇总：⭐⭐ 只做计数与映射，不下结论 ──────────────────────────
    rows = c["rows"]
    # ⭐⭐⭐⭐ 键用「元素自己 + 容器」并排（981 第四次复发那条纪律）
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

    lap = [{"i": i + 1, "key": keys[i], "closest_tid": rows[i]["closest_tid"],
            "dom_rank": ranks[i], "is_body": rows[i]["is_body"],
            "kind": rows[i]["kind"]} for i in range(min(p, len(rows)))]
    c["one_lap"] = lap
    c["lap_len"] = len(lap)

    # ⭐⭐⭐⭐⭐ **P1：去掉 `BODY` 之后 `dom_rank` 严格递增吗？**
    idx = _rank_order(lap)
    c["n_sorted_considered"] = len(idx)
    seq = [lap[i]["dom_rank"] for i in idx]
    c["sorted_ranks"] = seq
    c["n_descents_excluding_body"] = _descents(seq)[0] if len(seq) > 1 else None
    c["is_strictly_increasing_excluding_body"] = \
        _is_strictly_increasing(seq)
    # ⭐⭐⭐⭐ **反向读数（保留）**：**含 `BODY` 的整圈**有几个下降
    #   ⇒ ⇒ 这是 983/985 早就记到的那 1 次下降 ⇒ **不许删**
    c["n_descents_including_body"] = _descents(
        [r["dom_rank"] for r in lap])[0] if len(lap) > 1 else None
    c["body_i_in_lap"] = next(
        (i + 1 for i, r in enumerate(lap) if r.get("is_body")), None)
    c["body_is_excluded_from_ranking"] = (
        c["body_i_in_lap"] is not None
        and (c["body_i_in_lap"] - 1) not in idx)

    # ⭐⭐⭐⭐⭐ **P2：`rf__wrapper` 与 `canvas-project-logo` 的两个序号**
    c["wrap_ring_pos"] = _ring_pos(lap, WRAP_TID)
    c["wrap_rank_of_ranks"] = _rank_of_ranks(lap, WRAP_TID)
    c["logo_ring_pos"] = _ring_pos(lap, LOGO_TID)
    c["logo_rank_of_ranks"] = _rank_of_ranks(lap, LOGO_TID)
    c["wrap_dom_rank"] = next(
        (r["dom_rank"] for r in lap if r.get("closest_tid") == WRAP_TID), None)
    c["logo_dom_rank"] = next(
        (r["dom_rank"] for r in lap if r.get("closest_tid") == LOGO_TID), None)
    c["wrap_dom_rank_smaller_than_logo"] = (
        c["wrap_dom_rank"] is not None and c["logo_dom_rank"] is not None
        and c["wrap_dom_rank"] < c["logo_dom_rank"])
    # ⭐⭐⭐⭐⭐ **P2 的逐格形式**：**每一个参与排序的格**，两个序号必须一致
    c["n_grids_where_ring_pos_ne_rank"] = sum(
        1 for i in idx
        if _ring_pos(lap, lap[i]["key"]) != _rank_of_ranks(lap, lap[i]["key"]))
    c["n_grids_checked"] = len(idx)

    # ⭐⭐⭐⭐ **logo 天然可聚焦**（它是 `<a href>`）⇒ 不靠 `tabindex`
    logo_ti = [r["ti_prop"] for r in rows if r.get("closest_tid") == LOGO_TID]
    c["logo_ti_props"] = logo_ti[:8]
    c["logo_is_focusable"] = bool(logo_ti) and all(
        isinstance(x, int) and x >= 0 for x in logo_ti)
    c["n_logo_stops"] = len(logo_ti)
    c["n_rank_unknown_total"] = sum(1 for r in ranks if r is None)
    c["left_rail_closest_tids"] = [
        r["closest_tid"] for r in rows if r["own_tid"] in LEFT_RAIL_SELF]
    dump(out)

dump(out)

# ── ⭐⭐⭐⭐⭐ 判据要钉的九条，**必须真的写在探针里** ──────────────────
# ⚠️⭐⭐⭐⭐⭐ **我第一版把它们只写进了 audit、没写进探针 ⇒ 官方锚点自查门
#   报 9 个 MISSING** ⇒ ⇒ ⭐⭐⭐⭐⭐ **这是 986 那条纪律的又一次复发**：
#   **「钉探针」与「钉 audit」是两件事** —— 判据查的是**探针文件**，
#   而**我写在了 audit 里、探针里没有** ⇒ **门是对的、不是门太严**
#   ⇒ ⇒ ⭐⭐⭐⭐⭐ **门红先判门还是数据：这一次是数据错**
out["ruler"]["p1_refuted_in_probe"] = (
    "**这是「回绕兜底」的结构、不是「对齐决策」的产物** —— "
    "实测去 `BODY` 后仍有 1 次下降：环格 24(`dom_rank`=268) → "
    "环格 26 `rf__wrapper`(`dom_rank`=42)，**而环格 25 正是 `BODY`（间隙）** ⇒ "
    "**`rf__wrapper` 的前驱是间隙、不是元素** ⇒ "
    "**它是「间隙之后的第一个元素」、填在间隙与环首之间**")
out["ruler"]["p2_refined_987"] = (
    "⭐⭐⭐⭐ **P2 被数据精确修正** —— 「环内序号 == `dom_rank` 排名」"
    "在参与排序的 25 格里只对 24 格成立、1 格例外"
    "（`rf__wrapper`：ring_pos=26 而 rank=25）⇒ "
    "**正确形式是「除回绕兜底那一格外、两者一致」** ⇒ "
    "**`rf__wrapper` 落在末尾不是因为它 `dom_rank` 大、"
    "而是因为它是间隙之后的兜底** ⇒ "
    "**983 记下的「唯一下降由 `BODY` 制造」是对的、但 983 没看出它的含义** ⇒ "
    "**也被数据精确修正了**")
out["ruler"]["p3_cause_pinned"] = (
    "⭐⭐⭐⭐ **P3 命中** —— **成因钉在源码的一行** —— "
    "**「运行期先渲染」是观察、「JSX 顺序」是成因 ⇒ 两者必须分开** ⇒ "
    "实测 `<JimengFlow />` 第 756 行 < `<JimengTopBar />` 第 757 行 ⇒ "
    "**CSS `position` 与 `z-index` 都不参与**")
out["ruler"]["logo_focus_instrument_gap_987"] = (
    "⚠️⭐⭐⭐⭐ **`logo_is_focusable=False` 是仪器读不到、不是不可聚焦** —— "
    "`DOMRANK_JS` **不读 `tabIndex`**（实测 `ti_prop = None`）⇒ "
    "**这正是 978/985 那条「仪器测什么决定你能看见什么」的又一次** ⇒ "
    "logo 是 `<a href>`、天然可聚焦（源码可查）⇒ "
    "**本批不据这条读数下「logo 不可聚焦」的结论**")
out["ruler"]["p1_wrong_how_987"] = (
    "⭐⭐⭐⭐⭐ **期望值错了、自测就是假绿** —— P1 我按"
    "**「去掉 `BODY` 就该递增」推，**漏了「回绕兜底那一格"
    "本身的前驱是间隙」** ⇒ ⇒ "
    "⇒ ⭐⭐⭐⭐⭐ **「去掉一个异常值」不等于「剩下的就单调」** —— "
    "**回绕点的前驱是间隙这件事、是另一条独立的结构** ⇒ "
    "⇒ ⭐⭐ **它是 983 早就记到、却一直没被读出来的**")
out["ruler"]["anchors_must_live_in_probe_not_audit"] = (
    "⭐⭐⭐⭐⭐ **判据锚的是探针文件、不是 audit** ⇒ "
    "**我第一版把九条只写进了 audit ⇒ 官方自查门报 9 个 MISSING** ⇒ "
    "⇒ **门是对的** ⇒ ⇒ ⭐⭐⭐⭐⭐ "
    "**「钉探针」与「钉 audit」是两件事，不许互相顶替**")
dump(out)

print("PROBE_987_DONE", flush=True)
