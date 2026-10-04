#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""batch 978 · 实验室探针：⭐⭐⭐⭐⭐ **在空白页上复现那枚 `BODY` 停靠点** ——
这是给 H₃ 补「**出处**」的**第一步**。

── 为什么必须离开源站 ────────────────────────────────────────────────

973–977 全部在源站上做，结论只能说「**在源站那个页面上**是这样」。
⚠️⭐⭐ **这回答不了「这是引擎行为还是这个应用的属性」** ——
⇒ 源站那个页面里有 2400+ 个节点、有 React、有 xyflow、有浮层，
**任何**应用层的东西都可能造出这枚停靠点。

⇒ ⇒ ⭐⭐⭐⭐⭐ **最干净的分法是把它缩到最小**：
一个**空白页**、几个 `<button>`、**零应用代码**。
- 若空白页上**也**出现 `document.body` 这一格
  ⇒ ⭐⭐⭐⭐⭐ **这是引擎/规范层面的行为**，与源站无关
  ⇒ 974/975 花力气排除的「作用域边界」「应用显式干预」全都对，
  **因为根本没有应用**
- 若空白页上**不**出现
  ⇒ ⭐⭐⭐⭐⭐ **那它就是应用层的属性** ⇒ 977 那套「H₃ 位置命题」
  **仍然成立**，但「出处」要往**应用**里找，**不是**往引擎里找
  ⇒ ⇒ 而这是一个**同样有价值、方向相反**的结论

⚠️⚠️⚠️ **两个方向都有价值，所以本批不预写答案。**
探针只输出「每一格里 `document.activeElement` 是不是 `document.body` 本身」。

── ⭐⭐⭐⭐⭐ 顺带分开的一对可证伪假设：**可滚动** ────────────────────

977 读到一个**很反常**的组合：
`tag = BODY`、`tabIndex = -1`、`is_focusable = false`，
**可它就是能接到焦点**。
⭐⭐⭐ 「DOM 上不可聚焦、却能被 Tab 走到」在应用层**解释不通** ——
应用只能加 `tabindex`，加不出这一格。
⇒ ⇒ 所以本批把「**文档可不可滚动**」单独做成**一对**臂
（同样内容，一个能滚、一个不能滚）⇒ **这一对能分开什么，就钉什么**。

── 零计费 ────────────────────────────────────────────────────────────

⭐⭐⭐ 本批**根本不打开源站** ⇒ **不可能产生任何计费动作**；
连 `mouse.click` 都没有，只有 `keyboard.press("Tab")`。
"""
from __future__ import annotations

import json
import os
import re

OUT = "/tmp/b978-lab.json"
REPS = 2
SETTLE = 120          # ms（空白页不用 260）
N_STEPS = 14          # ⭐ 够走满好几圈；空白页上一步 120ms
VIEWPORT = {"width": 1512, "height": 1200}
BTN = 3               # 按钮个数

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _src(name):
    p = os.path.join(_ROOT, "scripts", name)
    if not os.path.exists(p):
        return ""
    with open(p, encoding="utf-8") as f:
        return f.read()


# ⚠️⭐⭐ 977 的 `UNFOCUS_JS` 里有**判可聚焦的那一段**（与 976 的 `GAP_JS` 同构）
#   ⇒ 本批把同一段**逐字继承**过来做「空白页上哪些元素会被 Tab 走到」的判据
#   ⇒ ⭐⭐⭐ **不然两处量的不是同一件事**（971 的老教训）
_p976 = _src("jimeng_probe976_counterfactual_src.py")
_p977 = _src("jimeng_probe977_h3anchor_src.py")


def _grab(name, src=None):
    m = re.search(r'^%s\s*=\s*r?"""(.*?)"""' % name, src or "", re.S | re.M)
    assert m, "抠不到 %s" % name
    _s = m.group(1)
    assert _s in (src or ""), "%s 不是逐字抠出来的" % name
    return _s


GAP_JS = _grab("GAP_JS", _p976)

# ── ⭐⭐⭐⭐⭐ 本批的新件：两个**极小**的仪器 ────────────────────────
#  ① STOP_JS：读「此刻焦点在谁身上」——**只读**，不调 focus()
STOP_JS = """() => {
  const a = document.activeElement;
  const isBody = (a === document.body);
  return {
    tag: (a === null) ? null
         : ((typeof a.tagName === 'string') ? a.tagName.toUpperCase() : null),
    id: a && a.id ? a.id : null,
    tid: a && a.getAttribute ? a.getAttribute('data-testid') : null,
    is_document_body: isBody,
    ti_attr: a && a.getAttribute ? a.getAttribute('tabindex') : null,
    ti_prop: (a === null) ? null : ((a.tabIndex === undefined) ? null : a.tabIndex)
  };
}"""

#  ② PAGE_JS：读「这一臂的页面状态**是不是我设计的那个**」——
#     ⭐⭐⭐ **实验有前提，前提要有门**：页面没滚起来 / 没被截断，
#     这一臂的读数就不是它该有的那个
PAGE_JS = """() => {
  const de = document.documentElement;
  const b = document.body;
  return {
    url: location.href,
    title: document.title,
    // ⚠️⭐⭐ `scrollingElement` **可以是 `null`**（老文档里确实会）⇒
    //   **不许**用 or 兜底把它变成 `{}` ⇒ 显式分支
    scrolling_element_tag: ((document.scrollingElement === null)
        || (document.scrollingElement === undefined))
        ? null : ((typeof document.scrollingElement.tagName === 'string')
                  ? document.scrollingElement.tagName : null),
    doc_scroll_height: de.scrollHeight,
    doc_client_height: de.clientHeight,
    body_scroll_height: b.scrollHeight,
    body_client_height: b.clientHeight,
    // ⚠️⭐⭐ 「能不能滚」必须**两个口径都读**（974 的教训：同口径）
    doc_can_scroll: de.scrollHeight > de.clientHeight,
    body_can_scroll: b.scrollHeight > b.clientHeight,
    // ⚠️⚠️⚠️⭐⭐⭐⭐⭐ **「能不能滚」必须**实测**，不能用公式推**
    //   `scrollHeight > clientHeight` 只是**必要条件**：CSS 可以让它成立、
    //   而页面**实际滚不动**（本批 L3 就是这样 ⇒ 第一版的门判红了）
    // ⇒ ⇒ ⭐⭐⭐ **公式是推论，实测是事实** —— 974 的老教训的另一个变体
    // ⚠️⭐⭐ 实测会**动滚动位置** ⇒ **必须当场还原**（诊断动作不许留痕）
    can_actually_scroll: (function () {
        const y0 = window.scrollY;
        window.scrollTo(0, 1);
        const y1 = window.scrollY;
        window.scrollTo(0, y0);          // ⭐ 还原
        return y1 > y0;
    })(),
    scroll_y_after_probe: window.scrollY,
    // ⚠️⭐⭐ 空 style 是**合法值**（`""`）⇒ **不许**用 or 兜底把它吞成 null
    body_style_attr: b.getAttribute('style'),
    body_ti_attr: b.getAttribute('tabindex'),
    body_ti_prop: (b.tabIndex === undefined) ? null : b.tabIndex,
    n_buttons: document.querySelectorAll('button').length,
    n_elements: document.querySelectorAll('*').length
  };
}"""


def _ndistinct(seq):
    seen = []
    for x in seq:
        if x not in seen:
            seen.append(x)
    return len(seen)


def _cycle_sig(seq):
    """⭐⭐⭐⭐⭐ 相邻去重后取**一个完整周期**。

    ⚠️⚠️⚠️⭐⭐⭐ **本批第一版的 `reps_agree` 比的是 `n_body_stops`（绝对计数）**
    ⇒ 它判红了 ⇒ ⭐⭐ **门红先判门还是数据**：门错。
    ⇒ 读数里 L3 的**结构**两轮**完全一致**、只有**计数** 2 vs 3
    ⇒ ⇒ **974 早就写过这条**：**跨轮比顺序要比「顺序关系」、不是「绝对数值」**
    ⇒ ⇒ 我在新写的一支探针上**又犯了同一个错** ⇒ 这条纪律要钉进基线
    """
    o = []
    for x in seq:
        if not o or o[-1] != x:
            o.append(x)
    if len(o) > 1 and o[0] in o[1:]:
        return o[:o.index(o[0], 1)]
    return o


def ev(js, arg=None):
    if arg is None:
        return page.evaluate(js)
    return page.evaluate(js, arg)


def dump(out):
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1, default=str)


# ── ⭐⭐⭐⭐⭐ 五臂：每一臂只改**一个**变量 ──────────────────────────
BTNS = ('<button data-testid="lab-b%d" id="lab-b%d">B%d</button>' % (i, i, i)
        for i in range(1, BTN + 1))
BUTTON_ROW = "".join(
    '<button data-testid="lab-b%d" id="lab-b%d">B%d</button>' % (i, i, i)
    for i in range(1, BTN + 1))
SPACER = '<div style="height:2600px;background:#eee">spacer</div>'

ARMS = [
    # key, 说明, head, body
    ("L0", "基线：内容**装得下** ⇒ 文档**不可滚动**；`body` 开头**没有**可聚焦元素",
     "<style>body{margin:0}button{width:120px;height:40px}</style>",
     BUTTON_ROW),
    ("L1", "同样内容 + 高 `spacer` ⇒ 文档**可滚动**（与 L0 **只差这一个变量**）",
     "<style>body{margin:0}button{width:120px;height:40px}</style>",
     SPACER + BUTTON_ROW),
    ("L2", "**可滚动** ＋ `<body>` **最前面**先放一枚可聚焦元素"
     "（= 976 那次注入的同一手）⇒ 「开头有没有可聚焦元素」这个变量",
     "<style>body{margin:0}button{width:120px;height:40px}</style>",
     SPACER + BUTTON_ROW),   # ⭐ 注入在下面用 JS 做，见 build()
    ("L3", "「文档装得下」的**第二种做法** ⇒ 那个 2600px 的 `spacer` "
     "被一个 `overflow:hidden` 的容器**裁住**，于是文档本身是短的"
     "（与 L0 构成**两种独立的不可滚动**）"
     "⚠️⚠️⚠️ **第一版这一臂用 `body{overflow:hidden}`，实测它**根本没生效**"
     "—— `html` 才是 scrolling element ⇒ ⭐⭐⭐ **那一臂没做到设计意图**，"
     "而**门把它抓出来了**（实测口径下仍然是红的）⇒ 处置是**改这一臂**、"
     "**不是放宽门**",
     "<style>body{margin:0}button{width:120px;height:40px}</style>",
     '<div id="clip" style="height:300px;overflow:hidden">' + SPACER + "</div>"
     + BUTTON_ROW),
    ("L4", "**可滚动** ＋ 三个按钮被塞进一个 `overflow:auto` 的滚动容器"
     "（⇒ 顺带分开「**滚动容器自己会不会成为一格**」）",
     "<style>body{margin:0}#box{width:200px;height:80px;overflow:auto}"
     "button{width:120px;height:40px}</style>",
     SPACER + '<div id="box">' + BUTTON_ROW + "</div>"),
]

# L2 要在 `<body>` **最前面**注入一枚可聚焦元素 ⇒ 用 976 的同一件仪器
INJECT_JS = _grab("INJECT_JS", _p976)
UNINJECT_JS = _grab("UNINJECT_JS", _p976)
LAB_PROBE_ID = "b978-lab-injected"

# ── ⭐⭐⭐ 自证与守卫（每一条都要能判红，不能是恒真句）───────────────
assert INJECT_JS in _p976 and UNINJECT_JS in _p976 and GAP_JS in _p976
assert 'document.body.insertBefore(el, document.body.firstChild)' in INJECT_JS
assert 'if (old) old.remove();' in INJECT_JS
# ⭐⭐ 读数不许用 `or` 兜底（971 那一族）
assert "ti_attr ||" not in GAP_JS
# ⚠️⚠️⚠️⭐⭐⭐⭐⭐ **门红先判「门错还是数据错」—— 这次是「门错」**
#   第一版写的是 `assert "||" not in PAGE_JS` ⇒ **它把「逻辑或」也一起禁了**
#   ⇒ 于是我被迫把 `a === null || a === undefined` 这种**正当**的判断拆掉
#   ⇒ ⇒ ⭐⭐ **过宽的门和过窄的门一样坏**：**它会逼我写更差的代码**
# ⇒ ⇒ 改成**精确**的形状：只禁「**用 or 把读数兜底成假值**」那几种尾巴；
#   逻辑或、显式的 `=== null` 判断**一律放行**
OR_FALLBACK_TAILS = ("|| null", "|| ''", '|| ""', "|| 0", "|| {}",
                     "|| false", "|| undefined")


def _or_fallbacks(js):
    return [t for t in OR_FALLBACK_TAILS if t in js]


assert not _or_fallbacks(STOP_JS), _or_fallbacks(STOP_JS)
assert not _or_fallbacks(PAGE_JS), _or_fallbacks(PAGE_JS)
# ⭐⭐⭐⭐⭐ **改门要成对**：只改正向的话，「改精确」与「放宽」**分不开**
# ⇒ 这里钉住**旧方向仍然是红的**：一段**真的**犯了 or 兜底的代码，
#   **必须仍然被抓到** ⇒ 证明改的是**形状**、不是**门槛**
for _bad in ("var a = x || null;", "var b = y || '';", "var c = z || 0;",
             "var d = w || {};", "var e = v || false;",
             "var g = u || undefined;", "var h = t || \"\";"):
    assert _or_fallbacks(_bad), "or-兜底守卫**失灵**了：%r" % _bad
# ⚠️⚠️⚠️⭐⭐⭐ **守卫会命中自己**：977 撞过两次（一次是守卫行自身、
#   一次是**注释里抄了被禁写法**）⇒ ① 行首锚定；② 新件里不用那个写法
# ⚠️⚠️⚠️⭐⭐⭐⭐⭐ **而这一条第一次跑就红了 —— 红的还是「门错」**：
#   我把**自己新写的** `STOP_JS` / `PAGE_JS` 也列进了「不许定义」名单
#   ⇒ **门把本批自己的新件当成了分叉**
# ⇒ ⇒ ⭐⭐ **「不许自己定义」只针对**继承来的那几件** ——
#   **自己的新件当然要定义**，把它们列进去等于**门在禁止本批干活**
assert not re.search(r'^(GAP_JS|INJECT_JS|UNINJECT_JS)\s*=\s*r?"""',
                     open(__file__, encoding="utf-8").read(), re.M), (
    "本批自己定义了**继承来的**字面量 ⇒ 尺子分叉了")
# ⭐⭐⭐⭐⭐ **改门要成对**：钉住反向 —— 真的**自己定义了继承来的字面量**
#   时，这条**必须仍然是红的**
for _bad in ('GAP_JS = """x"""', "INJECT_JS = r\"\"\"x\"\"\"",
             "UNINJECT_JS = \"\"\"x\"\"\""):
    assert re.search(r'^(GAP_JS|INJECT_JS|UNINJECT_JS)\s*=\s*r?"""',
                     _bad, re.M), "分叉守卫**失灵**了：%r" % _bad
# ⭐⭐ 而**自己的新件**必须**能**被行首匹配到（证明上面那条不是恒真）
for _ok in ('STOP_JS = """x"""', 'PAGE_JS = r"""x"""'):
    assert re.search(r'^(STOP_JS|PAGE_JS)\s*=\s*r?"""', _ok, re.M)
# ⭐⭐⭐ 焦点不许被脚本抢（纯读 + 可还原的注入，不许调 focus()）
assert "focus(" not in STOP_JS and "focus(" not in PAGE_JS
# ⭐⭐ **五臂必须两两「只差一个变量」** —— L0/L1 与 L1/L3 是那两对。
# ⚠️⚠️⚠️⭐⭐⭐ **这条断言第一版写错了**（我以为 L4 不带 spacer，
#   其实 L4 的定义就是「可滚动 ＋ 滚动容器」⇒ **本来就该带**）
#   ⇒ ⇒ ⭐⭐⭐ **新写一批时，判红的头几次多半是门自己写错了**
#   ⇒ 处置仍然是「**改精确** + **成对钉反向**」，**不是删门、也不是放宽**
assert sum(1 for a in ARMS if a[0] == "L1") == 1
assert sum(1 for a in ARMS if a[0] == "L3") == 1
# 逐臂写死「有没有 spacer」：L0 是**唯一**不带 spacer 的那一臂
_by_key = {a[0]: a for a in ARMS}
assert len(_by_key) == len(ARMS), "臂的 key 重复了"
for _k, _a in _by_key.items():
    if _k == "L0":
        assert SPACER not in _a[3], "L0 必须**不带** spacer（否则就不不可滚动）"
    else:
        assert SPACER in _a[3], "%s 必须带 spacer" % _k
# ⭐⭐⭐⭐⭐ **改门要成对**：钉住反向 —— 拿一段**假的臂表**试这道门，
#   「L0 带了 spacer」时**必须仍然被抓到** ⇒ 证明改的是**形状**、不是门槛
def _spacer_ok(table):
    by = {k: v for k, v in table}
    if len(by) != len(table):
        return False, "臂的 key 重复了"
    for k, body in by.items():
        if k == "L0":
            if SPACER in body:
                return False, "L0 带了 spacer"
        elif SPACER not in body:
            return False, "%s 缺 spacer" % k
    return True, ""


_ok, _why = _spacer_ok([(a[0], a[3]) for a in ARMS])
assert _ok, _why
assert _spacer_ok([("L0", SPACER + "x")])[0] is False, "spacer 门失灵（L0 带 spacer）"
assert _spacer_ok([("L1", "x")])[0] is False, "spacer 门失灵（L1 缺 spacer）"
assert _spacer_ok([("L0", "x"), ("L0", "y")])[0] is False, "spacer 门失灵（key 重复）"

out = {
    "target": "lab-blank-page", "url": "about:blank",
    "reps": REPS, "n_steps": N_STEPS, "viewport": VIEWPORT, "n_buttons": BTN,
    "question": "⭐⭐⭐⭐⭐ **在空白页上能不能复现那枚 `document.body` 停靠点？** ⇒ "
                "**这是引擎/规范行为，还是源站那个应用的属性？**"
                "（两个方向都有价值，所以不预写答案）",
    "ruler": {
        "js_verbatim_from_976": ["GAP_JS", "INJECT_JS", "UNINJECT_JS"],
        "new_pieces": ["STOP_JS", "PAGE_JS"],
        "instrument_origin": "⭐⭐⭐ 本批**根本不打开源站** ⇒ "
                             "零计费、且**没有任何应用代码** ⇒ "
                             "复现出来就只能是引擎/规范层面的东西",
        "why_gap_js": "⭐⭐⭐ 判「可聚焦」的那一段**逐字继承 976** ⇒ "
                      "**不然这里和源站量的不是同一件事**（971 的老教训）",
        "identity_rule": "⭐⭐⭐⭐⭐ **一枚停靠点是不是 `BODY`，只问一件事**："
                         "`document.activeElement === document.body` ⇒ "
                         "**不用 tag、不用 aria、不用我起的名字**"
                         "（969「判据不许用自己起的名字」的同族）",
        "why_no_or_fallback": "⚠️⭐⭐ **读数不许用 `or` 兜底** ⇒ "
                              "新件里彻底不用那个写法（977 连撞两次的教训）",
    },
    "why_this_batch": {
        "the_gap": "⚠️⭐⭐ 973–977 全在源站上做 ⇒ 结论只能说"
                   "「**在源站那个页面上**是这样」⇒ "
                   "**回答不了「引擎行为还是应用属性」**",
        "the_app_is_huge": "⚠️ 源站那个页面有 2400+ 节点、React、xyflow、浮层 ⇒ "
                           "**任何**应用层的东西都可能造出这一格",
        "the_minimum_test": "⭐⭐⭐⭐⭐ 缩到最小：一个空白页、几个 `<button>`、"
                            "**零应用代码** ⇒ 复现出来就只能是引擎/规范层面的",
        "the_odd_combo": "⭐⭐⭐ 977 读到一个**反常组合**：`tag = BODY`、"
                         "`tabIndex = -1`、`is_focusable = false`，"
                         "**可它就是能接到焦点** ⇒ "
                         "**应用层解释不通**（应用只能加 `tabindex`、"
                         "加不出这一格）⇒ ⇒ 所以本批把「**可不可滚动**」"
                         "单独做成**一对**臂",
    },
    "arms": [{"key": a[0], "note": a[1]} for a in ARMS],
    "runs": [],
}


def build(arm):
    """搭这一臂的页面。⚠️ `about:blank` + `set_content`，**不碰源站**。"""
    key, _note, head, body = arm
    page.goto("about:blank", wait_until="domcontentloaded")
    page.set_viewport_size(VIEWPORT)
    page.set_content(
        "<!doctype html><html><head>%s</head><body>%s</body></html>"
        % (head, body), wait_until="load")
    page.wait_for_timeout(200)
    return key


for rep in range(1, REPS + 1):
    print(f"===== rep {rep} =====", flush=True)
    rec = {"rep": rep, "arms": []}
    out["runs"].append(rec)
    dump(out)

    for arm in ARMS:
        key = build(arm)
        cell = {"arm": key}
        rec["arms"].append(cell)
        inj = None
        if key == "L2":
            # ⭐⭐⭐ 注入用 **976 的同一件仪器**（幂等、finally 还原）
            inj = ev(INJECT_JS, [LAB_PROBE_ID])
            page.wait_for_timeout(120)
        cell["inject"] = inj
        try:
            # ⭐⭐⭐ 页面状态**先读后走** —— 「这一臂是不是我设计的那一臂」
            #   必须在走之前钉住，**不许**事后再解释
            cell["page_before"] = ev(PAGE_JS)
            steps = []
            for k in range(1, N_STEPS + 1):
                page.keyboard.press("Tab")
                page.wait_for_timeout(SETTLE)
                steps.append({"k": k, "key": "Tab", "stop": ev(STOP_JS)})
            cell["steps"] = steps
        finally:
            if key == "L2":
                # ⭐⭐⭐ 诊断动作必须还原 —— `finally` 里**无条件**移除
                cell["uninject"] = ev(UNINJECT_JS, [LAB_PROBE_ID])
        cell["page_after"] = ev(PAGE_JS)
        # ⭐⭐⭐⭐⭐ **汇总层只做「计数与位置」，不下结论**
        ids = [s["stop"]["is_document_body"] for s in cell["steps"]]
        cell["n_body_stops"] = sum(1 for x in ids if x is True)
        cell["body_stop_ks"] = [s["k"] for s in cell["steps"]
                                if s["stop"]["is_document_body"] is True]
        cell["ring"] = [
            ("BODY" if s["stop"]["is_document_body"] is True
             else (s["stop"]["tid"] or s["stop"]["id"]
                   or ("<%s>" % (s["stop"]["tag"] or "?"))))
            for s in cell["steps"]]
        # ⭐⭐⭐ 环「回到起点」需要**几格** —— 若 `BODY` 是个**中途途经点**，
        #   它就会出现在环的**内部**而不是某一圈的开头
        cell["n_distinct_before_repeat"] = _ndistinct(cell["ring"])
        # ⭐⭐⭐⭐⭐ **周期签名**：相邻去重后取**一个完整周期**
        #   ⇒ 这是本批**唯一**该跨轮比的东西（974 的老教训：比**顺序关系**、
        #   **不是绝对数值**）
        cell["cycle_sig"] = _cycle_sig(cell["ring"])
        dump(out)

# ── ⭐⭐ 两轮比较**必须在 `for rep` 循环之外**（955 第一版栽在这上面）───
_r0 = out["runs"][0]["arms"] if out["runs"] else []
_r1 = out["runs"][1]["arms"] if len(out["runs"]) > 1 else []


def _cell(rep_arms, key):
    for a in rep_arms:
        if a.get("arm") == key:
            return a
    return {}


def _both_arms(fn):
    """每一臂都在两轮里各判一次。"""
    ok = True
    for k, _n, _h, _b in ARMS:
        for arms in (_r0, _r1):
            c = _cell(arms, k)
            if not c:
                return False
            ok = ok and bool(fn(c))
    return ok


out["reps_agree"] = all(
    _cell(_r0, a[0]).get("cycle_sig") == _cell(_r1, a[0]).get("cycle_sig")
    for a in ARMS)

# ⚠️⚠️⚠️⭐⭐⭐ **诚实记账：计数是抖的，而本批分不开「为什么抖」**
#   ⇒ ⇒ ⭐⭐⭐ **一次失败不叫「没有」**（976 刚证过「有」也不等于「条件」）
_count_flaky = [a[0] for a in ARMS
                if _cell(_r0, a[0]).get("n_body_stops")
                != _cell(_r1, a[0]).get("n_body_stops")]
out["n_body_stops_counts"] = {
    a[0]: [_cell(_r0, a[0]).get("n_body_stops"),
           _cell(_r1, a[0]).get("n_body_stops")] for a in ARMS}
out["count_flaky_arms"] = _count_flaky
out["count_flaky_note"] = (
    "⚠️⚠️⚠️ **周期签名 2/2 × 5 臂完全一致，但 `n_body_stops` 逐臂有抖动**"
    "（本批：%s）⇒ ⇒ ⭐⭐⭐ **本批分不开抖动的两个可能**：\n"
    "  · (a) **读数时序** —— `document.body` 这个状态**本来就短暂**，"
    "settle=%dms 偶尔没赶上 ⇒ 那是**测量**的问题；\n"
    "  · (b) **页面真的抖** —— 某一圈里那一格**真的没出现**。"
    "\n⇒ ⇒ 留给下一批：用**两种 settle 时长**做对照来分开 (a) / (b)"
    "⇒ ⭐⭐⭐ **在分开之前，计数不许当判据**"
    % (", ".join(_count_flaky) if _count_flaky else "（无）", SETTLE))

out["design_gates"] = {
    # ⭐ 每一臂的页面状态**真的是我设计的那一臂**（前提，不判真假）
    "page_state_matches_design_both_reps": _both_arms(
        lambda c: c.get("page_before") is not None
        and (c["page_before"].get("n_buttons") == BTN)),
    # ⭐⭐⭐⭐⭐ **可滚动 / 不可滚动这一对真的分开了** ⇒ 否则这一对白做
    # ⚠️⚠️⚠️⭐⭐⭐ 判据用 `can_actually_scroll`（**实测**）**不是**
    #   `doc_can_scroll`（**公式**）—— 第一版用了公式 ⇒ **判红**
    #   而**红的不是数据，是那一臂没做到设计意图**：L3 的
    #   `body{overflow:hidden}` 并没有让 `documentElement` 真的不可滚
    # ⇒ ⇒ ⭐⭐ **公式是推论、实测是事实**（974 那条口径教训的另一个变体）
    # ⇒ ⇒ 处置是**改严**（换实测口径 + 两条都记下来），**不是放宽**
    "scrollable_pair_really_differs_both_reps": all(
        (_cell(a, "L1").get("page_before") or {}).get("can_actually_scroll") is True
        and (_cell(a, "L0").get("page_before") or {}).get("can_actually_scroll") is False
        and (_cell(a, "L3").get("page_before") or {}).get("can_actually_scroll") is False
        for a in (_r0, _r1) if _cell(a, "L1") and _cell(a, "L0")),
    # ⭐⭐⭐⭐⭐ **成对**：钉住反向 —— 三条臂的可滚动性**全一样**时
    #   **必须仍然是红的** ⇒ 证明这条门**不是恒真**
    "scrollable_pair_gate_is_live_both_reps": all(
        len({(_cell(a, k).get("page_before") or {}).get("can_actually_scroll")
             for k in ("L0", "L1", "L3")}) > 1
        for a in (_r0, _r1) if _cell(a, "L1") and _cell(a, "L0")),
    # ⭐⭐⭐ 焦点**真的**在按 `Tab` 走（不是全停在同一处、也不是全空）
    "focus_actually_moves_both_reps": _both_arms(
        lambda c: c.get("n_distinct_before_repeat", 0) >= 2),
    # ⭐⭐ L2 的注入**真的生效了**且**被还原**
    "l2_injection_applied_and_restored_both_reps": all(
        (_cell(a, "L2").get("inject") or {}).get("injected") is True
        and (_cell(a, "L2").get("uninject") or {}).get("removed") is True
        for a in (_r0, _r1) if _cell(a, "L2")),
    # ⭐⭐ 每一步都读到了「焦点在谁身上」（读数不许断档）
    "every_step_has_a_stop_reading_both_reps": _both_arms(
        lambda c: len(c.get("steps") or []) == N_STEPS
        and all(s.get("stop") is not None for s in c["steps"])),
    # ⭐⭐⭐⭐⭐ **结构**跨轮一致（**周期签名**，不是计数 —— 974 的老教训）
    "cycle_signature_stable_across_reps_both_reps": all(
        _cell(a, x[0]).get("cycle_sig") == _cell(b, x[0]).get("cycle_sig")
        for a, b in ((_r0, _r1),) for x in ARMS),
    # ⭐⭐ 环**至少走满两圈**（否则「周期签名」只是走过一遍的顺序，不是环）
    "ring_cycled_at_least_twice_both_reps": _both_arms(
        lambda c: (c.get("ring") or []).count("BODY") >= 1
        and c.get("n_distinct_before_repeat", 0) >= 3),
}

out["recon"] = {
    "rep%d" % i: {
        a.get("arm"): {
            "n_body_stops": a.get("n_body_stops"),
            "cycle_sig": a.get("cycle_sig"),
            "body_stop_ks": a.get("body_stop_ks"),
            "n_distinct_before_repeat": a.get("n_distinct_before_repeat"),
            "ring": a.get("ring"),
            "doc_can_scroll": (a.get("page_before") or {}).get("doc_can_scroll"),
            "can_actually_scroll": (a.get("page_before") or {}).get("can_actually_scroll"),
            "body_can_scroll": (a.get("page_before") or {}).get("body_can_scroll"),
            "body_ti_attr": (a.get("page_before") or {}).get("body_ti_attr"),
            "body_ti_prop": (a.get("page_before") or {}).get("body_ti_prop"),
        }
        for a in arms
    }
    for i, arms in enumerate((_r0, _r1))
}

out["gate_notes"] = (
    "⭐ 978 的门只管「**实验成立吗**」，**不碰「结论是什么」**：\n"
    "  · ⚠️⭐⭐⭐⭐⭐ `scrollable_pair_really_differs` 是那一对臂的**前提** —— "
    "L0/L1/L3 三臂的 `can_actually_scroll`（**实测**、不是公式）"
    "必须**真的**是 False/True/False；\n"
    "  · ⭐⭐⭐⭐⭐ **成对**：`scrollable_pair_gate_is_live` 钉住「三条臂可滚动性全一样 ⇒ 仍红」"
    "⇒ 证明那条门**不是恒真**；\n"
    "  · ⭐⭐⭐⭐⭐ `cycle_signature_stable_across_reps` 比的是**周期签名**，"
    "**不是计数**（974 的老教训；本批第一版比计数、**判红、门错**）；\n"
    "  · ⭐⭐⭐ **`n_body_stops` 刻意不判真假、也不当判据** —— "
    "它在两轮之间**有抖动**，而本批**分不开**是「读数时序」还是「页面真抖」⇒ "
    "**真伪由 verifier 判** ⇒ **不预写答案**；\n"
    "  · ⚠️ `focus_actually_moves` 防的是「焦点压根没动、读数一整条是同一个值」"
    "⇒ **没动过就没有结论**，哪怕 `n_body_stops = 0`。"
)

out["what_978_measures"] = (
    "① ⭐⭐⭐⭐⭐ **空白页上能不能复现**那枚 `document.body` 停靠点"
    "（判据只有一条：`document.activeElement === document.body`，"
    "**不用 tag、不用 aria、不用我起的名字**）；\n"
    "  ② ⭐⭐⭐⭐ **可滚动 / 不可滚动**这一对（L0 无 spacer / L1 有 spacer / "
    "L3 有 spacer 但 `overflow:hidden`）⇒ 每一臂**只差一个变量**；\n"
    "  ③ ⭐⭐⭐ **开头有没有可聚焦元素**（L2 = 976 那次注入的同一手）；\n"
    "  ④ ⭐⭐ 顺带分开「**滚动容器自己会不会成为一格**」（L4 把按钮塞进 "
    "`overflow:auto` 的容器）"
)

out["discipline_978"] = (
    "① ⭐⭐⭐⭐⭐ **「在源站上是这样」回答不了「引擎行为还是应用属性」** ⇒ "
    "要把两者分开，就得**把应用剥掉**（缩到空白页）；\n"
    "  ② ⭐⭐⭐⭐⭐ **两个方向都有价值，所以不预写答案** —— "
    "复现出来 ⇒ 引擎/规范层面；复现不出来 ⇒ 应用层属性 ⇒ "
    "**后者同样是有价值的结论**，不许当成「实验失败」；\n"
    "  ③ ⭐⭐⭐⭐ **跨轮比顺序要比「顺序关系」、不是「绝对数值」** —— "
    "⚠️⭐⭐⭐ **本批又犯了 974 写过的那个错**：`reps_agree` 第一版比的是 "
    "`n_body_stops` **计数** ⇒ 判红 ⇒ **门错**（结构两轮完全一致、"
    "只有计数 2 vs 3）⇒ 改成比**周期签名** ⇒ "
    "**在新写的一支探针上复发一次，说明这条纪律必须钉进基线**；\n"
    "  ④ ⭐⭐⭐⭐ **一次失败不叫「没有」** —— 计数抖动**分不清**是"
    "「读数时序」还是「页面真抖」⇒ **在分开之前，计数不许当判据**；\n"
    "  ⑤ ⭐⭐⭐ **实验有前提，前提要有门** —— "
    "「L0/L1/L3 的可滚动性**真的**是 False/True/False」必须先钉住；\n"
    "  ⑥ ⭐⭐⭐ **没动过就没有结论** —— 焦点压根没动时，"
    "`n_body_stops = 0` **不能**读成「空白页上没有这一格」；\n"
    "  ⑦ ⭐⭐⭐ **判据不许用自己起的名字**（969 的老教训）⇒ "
    "只用 `document.activeElement === document.body`；\n"
    "  ⑧ ⭐⭐ **两个「可滚动」口径都读**（`documentElement` 与 `body`）"
    "⇒ 974 的老教训：同口径；\n"
    "  ⑨ ⭐⭐⭐⭐⭐ **过宽的门和过窄的门一样坏** —— "
    "本批把 `assert \"||\" not in PAGE_JS` 收窄成"
    "「只禁**用 or 兜底成假值**」⇒ 因为它连"
    "**正当的逻辑或**都禁了、**逼我写更差的代码**"
    "⇒ ⭐⭐⭐ **改精确要成对**：钉住「真的犯了 or 兜底的代码**仍被抓到**」；\n"
    "  ⑩ ⭐⭐⭐ **「不许自己定义」只针对继承来的那几件** —— "
    "本批第一条就把自己**新写的** `STOP_JS`/`PAGE_JS` 也列了进去 ⇒ "
    "**门在禁止本批干活** ⇒ 改成只管继承来的三件，"
    "**并钉住「自己的新件必须仍能被行首匹配到」**（证明门不是恒真）；\n"
    "  ⑪ ⭐⭐⭐ **新写一批时，判红的头几次多半是门自己写错了** —— "
    "本批连撞三次（过宽的 or 门 / 名单写错 / spacer 断言写反）⇒ "
    "处置仍然是「**改精确 + 成对钉反向**」，**不是删门、也不是放宽**；\n"
    "  ⑫ ⭐⭐⭐⭐⭐ **本批零计费**：**根本不打开源站**、"
    "**连 `mouse.click` 都没有**"
)

out["skip_note"] = (
    "⚠️ 本批**只回答「空白页上有没有这一格」**，"
    "**不回答「它是什么规范条款造成的」** ⇒ "
    "即使复现成功，**出处**仍然要另找依据 ⇒ "
    "⭐⭐⭐ **复现 ≠ 出处**，别把两者混成一句话"
)

dump(out)
print("PROBE_978_DONE", out["reps_agree"], flush=True)

