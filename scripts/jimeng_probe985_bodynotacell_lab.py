#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""batch 985 **实验室 + 源站**探针（**零计费**：只按 `Tab`）：
⭐⭐⭐⭐⭐⭐ **一次自我推翻** —— **`BODY` 根本不是一格** —— 而**同一批把 H₃ 的
「出处」彻底落定**。

── 984 留下的那一句，以及本批怎么把它坐实 ────────────────────────

984 说：「本批做的是**把问题缩小**」——
「顺序焦点导航在环的回绕点上，是否接纳 `tabIndex < 0` 的 `document.body`？」

⇒ ⇒ ⭐⭐⭐⭐⭐ **本批去读了实现，答案是：那个问题本身问错了。**

**`document.body` 不是顺序焦点导航的候选**，两处都排除它：

1. `element.cc` 的 `Element::SupportsFocus` ⇒ 对 `document.body` 返回
   `FocusableState::kNotFocusable`（它没有显式 `tabindex`、不是可编辑根、
   不是 scroll marker、也不是可聚焦滚动容器）⇒ `IsFocusable()` 为**假**
   ⇒ `FocusController::AdjustedTabIndex` 的默认值取 **−1**
   （`GetIntegralAttribute(kTabindexAttr, IsFocusable() ? 0 : -1)`）
   —— ⭐ **这正是 984 读到的 `ti_prop = -1` 的出处**
2. `focus_controller.cc` 的 `ShouldVisit(element)`（要求
   `IsKeyboardFocusableSlow()` 等）与遍历里那句
   `ReadingFlowAdjustedTabIndex(*current) >= 0` ⇒ **`document.body` 双双被排除**

⇒ ⇒ **那么 `document.activeElement === document.body` 是什么？**
**是「文档里没有任何元素持有焦点」这个状态** —— 按 DOM 规范，
`Document.activeElement` 在没有聚焦元素时**返回 `document.body`**。

⭐⭐⭐⭐⭐ **于是本批的全部仪器都测的是「间隙」，却把它记成了「一格」。**

── ⭐⭐⭐⭐⭐ 决定性读数（实验室，2/2 逐格相同） ──────────────────────

| 步 | `activeElement` | `body.matches(':focus')` | 真正持有焦点的元素数 | `document.hasFocus()` |
|---|---|---|---|---|
| 1–2 | `BUTTON` | `False` | **1** | `True` |
| **3** | **`BODY`** | **`False`** | **0** | **`False`** |
| 4–6 | `BUTTON` | `False` | **1** | `True` |

⇒ ⇒ ⭐⭐⭐⭐⭐ **`BODY` 那一步：`body` 从未获得焦点、文档里零个元素持有焦点、
连 `document.hasFocus()` 都是 `false`** ⇒ **它是间隙，不是格子**
⇒ ⇒ ⭐⭐⭐⭐⭐ **这与实现逐行对上**：`focus_controller.cc` 在找不到候选时
走 `document->ClearFocusedElement()` ＋ `page_->GetChromeClient()->TakeFocus(type)`
—— **焦点被交给 Chrome 的 UI 层** ⇒ 页面里自然「一个焦点都没有」

── ⭐⭐⭐⭐⭐ 本批把计数口径整个换掉 ──────────────────────────────

| 旧口径（976–984） | 新口径（本批） |
|---|---|
| 环长 = 观察到的停靠点数（**含 `BODY`**） | ⭐ **可聚焦停靠点数 = 旧环长 − 1** |
| 「某圈没走 `BODY`」= **缺失** | ⭐ **「某圈没有间隙」= 另一种现象** |
| `BODY` 是整圈 `dom_rank` 最小的一格 | ⭐ **`dom_rank` 最小是因为它是 `document.body`（DOM 序第 60 个），与它在环里的位置无关** |

⇒ ⇒ ⭐⭐⭐⭐⭐ **而 H₃ 那个「位置命题」到此变成同义反复**：
「间隙夹在最后一个与第一个可聚焦元素之间」—— **这在定义上就是必然的**，
**它从来不是一个发现** ⇒ ⇒ **H₃ 应当作废重写**（§195 第四节）

**本批零计费**：只按 `Tab`；⛔ 计费守卫拦在 `mouse.click` **之前**；
源站那一臂**只按 `Tab`、从不点击任何控件**。
"""
from __future__ import annotations

import atexit
import json
import os
import re

OUT = "/tmp/b985-bodynotacell.json"
REPS = 2
N_STEPS_LAB = 10        # 实验室：3 button ⇒ 2 个多圈
N_STEPS_SRC = 210       # 源站：101 格 ⇒ 2 个完整周期（与 982 同）
SETTLE_LAB = 150
SETTLE_SRC = 140        # 与 982 同
NODE_SEL = "[data-nodeid], .react-flow__node"   # ⭐ 与 973/974/982/983 同
PAGE_HTML = (
    '<!doctype html><html><head><meta charset="utf-8">'
    "<title>b985</title></head><body>"
    '<button id="lab-b1">b1</button>'
    '<button id="lab-b2">b2</button>'
    '<button id="lab-b3">b3</button>'
    "</body></html>"
)
PAGE_HTML_ZERO = (
    '<!doctype html><html><head><meta charset="utf-8">'
    "<title>b985-zero</title></head><body><p>零个可聚焦元素</p>"
    "</body></html>"
)
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


# ⚠️⭐⭐⭐ 三件都**逐字继承**、本批**一个都不自己重写**
_p978 = _src("jimeng_probe978_lab_body_stop.py")
_p982 = _src("jimeng_probe982_ringlen_src.py")
_p984 = _src("jimeng_probe984_bodytabindex_lab.py")
_paus = _src("jimeng_unclickable_audit.py")
_ME = open(__file__, encoding="utf-8").read()


def _grab(name, src=None):
    m = re.search(r'^%s\s*=\s*r?"""(.*?)"""' % name, src or "", re.S | re.M)
    assert m, "抠不到 %s" % name
    _s = m.group(1)
    assert _s in (src or ""), "%s 不是逐字抠出来的" % name
    return _s


STOP_JS = _grab("STOP_JS", _p978)          # 旧的纯读件（`is_document_body` / `ti_*`）

# ⭐⭐⭐⭐⭐ 984 把基线环写成了**赋值语句**、不是字面量 ⇒ 抠不到 ⇒ 本批**重述**
#   （**并在门里钉住它必须与 984 的那一份逐字相同** ⇒ 两批不会各说各话）
assert 'BASELINE_CYCLE = ["lab-b1", "lab-b2", "lab-b3", "BODY"]' in _p984, \
    "⭐⭐⭐⭐ 984 的基线环变了 ⇒ 本批的回归门钉的不再是同一个环"
BASELINE_CYCLE = ["lab-b1", "lab-b2", "lab-b3", "BODY"]

# ── ⭐⭐⭐⭐⭐ **本批唯一的新件，也是全部要害** ────────────────────────
#   它要问的**不是**「落点是谁」，而是「**谁真的持有焦点**」——
#   ⚠️ 这是 976–984 **全部仪器**缺的那一问
FOCUS_JS = """() => {
  const a = document.activeElement;
  const isBody = (a === document.body);
  // ⭐⭐⭐⭐⭐ **逐个问「谁真的持有焦点」** ——
  //   `document.activeElement` 只是**兜底返回值**，不是「谁被聚焦了」
  let n = 0, who = null;
  const all = document.querySelectorAll('*');
  for (const el of all) {
    if (el !== document.body && el.matches(':focus')) { n += 1; who = el; }
  }
  return {
    tag: (a === null) ? null
         : ((typeof a.tagName === 'string') ? a.tagName.toUpperCase() : null),
    tid: (a && a.getAttribute) ? a.getAttribute('data-testid') : null,
    id: (a && a.getAttribute) ? a.getAttribute('id') : null,
    is_document_body: isBody,
    ti_attr: (a && a.getAttribute) ? a.getAttribute('tabindex') : null,
    ti_prop: (a === null) ? null : ((a.tabIndex === undefined) ? null : a.tabIndex),
    // ⭐⭐⭐⭐⭐ **三个决定性读数**
    body_matches_focus: document.body.matches(':focus'),
    n_real_focus: n,
    real_focus_tid: who ? who.getAttribute('data-testid') : null,
    real_focus_id: who ? who.getAttribute('id') : null,
    has_focus: document.hasFocus(),
    // ⭐⭐ **间隙的判定式**（本批的核心定义，必须能一眼看懂）
    //   「`activeElement` 是 body」 **且** 「body 并未真的被聚焦」
    is_gap: (isBody && !document.body.matches(':focus'))
  };
}"""

POINT_JS = _grab("POINT_JS", _src("jimeng_probe973_ringorder_ck.py"))

assert not re.search(r'^STOP_JS\s*=\s*r?"""', _ME, re.M), \
    "本批自己定义了**继承来的** `STOP_JS` ⇒ 尺子分叉了"
assert STOP_JS in _p978, "STOP_JS 不在 978 探针里 ⇒ 不是同一件仪器"
# ⭐⭐⭐⭐⭐ **要推翻的是 984 那条边界，所以那句话必须还在**
assert "**本批没有找到出处，而且必须这么写**" in _paus, \
    "984 那条「仍未找到出处」的边界不见了 ⇒ 本批要推翻的对象变了"
assert '"still_not_the_source_984"' in _paus, "984 那个键没了 ⇒ 本批的前提没了"
assert "**顺序焦点导航在环的回绕点上，是否接纳" in _paus, \
    "984 那句收窄后的问题不见了 ⇒ 本批要回答的不是它"


def _cycle_of(keys):
    """⭐⭐⭐ 逐字沿用 **978** 的 `cycle_sig` 口径：首次重复之前的那一段。
    ⚠️⭐⭐⭐ **980 的纪律：切圈残段不许算进分母** ⇒ 门只能拿「首个周期」去比。"""
    for i in range(1, len(keys)):
        if keys[i] == keys[0]:
            return keys[:i]
    return list(keys)


def _code_only(js):
    o = []
    for line in js.split("\n"):
        t = line.strip()
        if t.startswith("//") or t.startswith("*") or t.startswith("/*"):
            continue
        o.append(line.split("//")[0])
    return "\n".join(o)


# ⭐⭐⭐⭐⭐ **纯读守卫（983 那三坑的教训 ⇒ 用正则、且成对钉三条）**
_CODE = _code_only(FOCUS_JS)
for _pat, _why in (
        (r"\.focus\s*\(", "调 focus()"),
        (r"\.tabIndex\s*=(?!=)", "**写** IDL 属性 `tabIndex`"),
        (r"\.setAttribute\s*\(", "写属性"),
        (r"new\s+MutationObserver", "MutationObserver"),
        (r"\.addEventListener\s*\(", "addEventListener")):
    assert not re.search(_pat, _CODE), \
        "`FOCUS_JS` 里出现了%s ⇒ 它不再是**纯读件**" % _why
# 成对①：真赋值必须被抓住
assert re.search(r"\.tabIndex\s*=(?!=)", "var a = 1;\na.tabIndex = 0;\n"), \
    "反向门①坏了：写 `tabIndex` 抓不住"
# 成对②：**读**属性不许被当成写（983 那个坑）
assert not re.search(r"\.tabIndex\s*=(?!=)",
                     "var a = 1;\na.tabIndex === undefined;\n"), \
    "⭐⭐⭐ **反向门②坏了**：**读**属性被当成**写** ⇒ 这道门「过窄」"
# 成对③：必须**读得到** `tabIndex`（否则可能退化成恒真）
assert re.search(r"\.tabIndex\b", _CODE), \
    "`FOCUS_JS` 连 `tabIndex` 都不读了 ⇒ 纯读守卫可能变成**恒真**"
# ⭐⭐⭐⭐⭐ **本批的新件必须真的问出那三问**（否则等于没推翻任何东西）
for _must in (":focus", "hasFocus()", "is_gap", "n_real_focus"):
    assert _must in FOCUS_JS, "FOCUS_JS 少了 %r ⇒ 本批的正题不成立" % _must
assert STOP_JS in _p978 and ":focus" not in STOP_JS, \
    "⭐⭐⭐⭐ `STOP_JS` 里已经有 `:focus` 了 ⇒ 978 那件被改过 ⇒ 本批的前提要重看"
assert N_STEPS_LAB >= 2 * 4 and N_STEPS_SRC >= 2 * 101, \
    "步数不够（实验室 ≥2 圈、源站 ≥2 个完整周期）⇒ 数出来的圈数不足"


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


def min_period(seq):
    """⭐⭐⭐ 逐字继承 **982** 的那件（`exec`，靠成对门钉一致性）——
    「圈」的定义不许各批各说各话。"""
    i = _p982.index("def min_period(seq):")
    j = _p982.index("def _code_only(js):")
    src = _p982[i:j]
    assert src in _p982, "抠出来的仪器不是逐字抠出来的"
    ns = {}
    exec(compile(src, "<982-min_period>", "exec"), ns)   # noqa: S102
    mp = ns["min_period"]
    # ⭐⭐⭐⭐ **成对门**：把 982 自己那组用例重跑一遍
    for _seq, _p, _nf, _rem in (([], None, 0, 0), (['a'], 1, 1, 0),
                                (['a', 'b', 'a', 'b'], 2, 2, 0),
                                (['a', 'b', 'a'], 2, 1, 1),
                                (['a', 'b', 'a', 'c'], 4, 1, 0),
                                (['x', 'y', 'z', 'w', 'v', 'q', 'r'], 7, 1, 0)):
        assert mp(_seq) == _p, "⭐⭐ 抠出来的 min_period 与 982 原件不一致：%r" % (_seq,)
        if _p is not None:
            assert (len(_seq) // _p, len(_seq) % _p) == (_nf, _rem), \
                "⭐⭐ 抠出来的 min_period 的残段读法与 982 原件不一致"
    return mp


_MIN_PERIOD = min_period(_p982)

out = {
    "target": "lab+source", "src_url": SRC_URL, "reps": REPS,
    "n_steps_lab": N_STEPS_LAB, "n_steps_src": N_STEPS_SRC,
    "node_sel": NODE_SEL,
    "question": "⭐⭐⭐⭐⭐⭐ **`BODY` 根本不是一格** —— 984 收窄后问的那个问题"
                "**本身问错了**：`document.body` 压根不是顺序焦点导航的候选"
                "⇒ 「`activeElement` 是 body」= **「文档里没有任何元素持有焦点」**"
                "⇒ ⇒ ⭐⭐⭐⭐⭐ **我的仪器测的是「间隙」，却把它记成了「一格」**",
    "ruler": {
        "js_verbatim_from_978": ["STOP_JS"],
        "js_verbatim_from_973": ["POINT_JS"],
        "py_verbatim_from_982": ["min_period"],
        "new_pieces": ["FOCUS_JS"],
        "what_new_piece_asks": "⭐⭐⭐⭐⭐ **本批的新件问的不是「落点是谁」，"
                               "而是「**谁真的持有焦点**」** ⇒ ⭐⭐⭐⭐ "
                               "**这是 976–984 全部仪器缺的那一问** ⇒ "
                               "`document.activeElement` 只是**兜底返回值**，"
                               "不是「谁被聚焦了」",
        "impl_reading": "⭐⭐⭐⭐⭐ **实现给了两处独立排除**（本批去读了源码）：\n"
                        "  · `element.cc` 的 `Element::SupportsFocus` 对 "
                        "`document.body` 返回 `kNotFocusable` ⇒ "
                        "`FocusController::AdjustedTabIndex` 默认取 **−1** "
                        "⇒ **这正是 984 读到的 `ti_prop = -1` 的出处**\n"
                        "  · `focus_controller.cc` 的 `ShouldVisit()` 与遍历里"
                        "那句 `ReadingFlowAdjustedTabIndex(*current) >= 0` "
                        "⇒ **`document.body` 双双被排除**",
        "counting_caliber_changed": "⭐⭐⭐⭐⭐ **本批把计数口径整个换掉**：\n"
                                    "  · 旧：环长 = 观察到的停靠点数（**含 `BODY`**）"
                                    "⇒ 新：⭐ **可聚焦停靠点数 = 旧环长 − 1**\n"
                                    "  · 旧：「某圈没走 `BODY`」= **缺失** ⇒ 新：⭐ "
                                    "**「某圈没有间隙」= 另一种现象**\n"
                                    "  · 旧：`BODY` 是整圈 `dom_rank` 最小的一格 ⇒ 新：⭐ "
                                    "**它最小只因为它是 `document.body`"
                                    "（DOM 序第 60 个），与它在环里的位置无关**",
        "zero_billing": "⭐⭐⭐⭐⭐ **零计费**：只按 `Tab`；⛔ 守卫拦在 "
                        "`mouse.click` 之前；源站那一臂**只按 `Tab`、"
                        "从不点击任何控件**",
    },
    "baseline": {
        "s984_still_not_source": "⭐⭐⭐⭐⭐ **984 说「本批没有找到出处」** ⇒ "
                                 "**本批要推翻的正是那句话** ⇒ "
                                 "**门必须钉住「984 那条边界仍在」**",
        "s984_baseline_cycle": "⭐⭐⭐⭐ **984 的基线环 = "
                               "`['lab-b1','lab-b2','lab-b3','BODY']`（长 4）** ⇒ "
                               "本批 `A0` 是**回归门** ⇒ "
                               "⚠️ 984 把它写成**赋值语句**、`_grab` 抠不到 ⇒ "
                               "**本批重述它、并在门里钉住两者逐字相同**",
    },
    "arms": [{"key": "A0", "html": "3 button", "n_steps": N_STEPS_LAB},
             {"key": "A1", "html": "**零个**可聚焦元素", "n_steps": N_STEPS_LAB}],
    "runs": [],
}

for rep in range(1, REPS + 1):
    print("===== rep %d =====" % rep, flush=True)
    rec = {"rep": rep, "arms": [], "src": None}
    out["runs"].append(rec)
    dump(out)

    for key, html in (("A0", PAGE_HTML), ("A1", PAGE_HTML_ZERO)):
        page.set_content(html, wait_until="domcontentloaded")
        page.wait_for_timeout(400)
        steps = []
        for k in range(1, N_STEPS_LAB + 1):
            page.keyboard.press("Tab")
            page.wait_for_timeout(SETTLE_LAB)
            steps.append({"k": k, "key": "Tab", "f": ev(FOCUS_JS)})
        cell = {"arm": key, "steps": steps}
        obs = [s["f"] for s in steps]
        cell["obs"] = [("GAP" if o["is_gap"] else
                        (o["tid"] or o["id"] or o["tag"])) for o in obs]
        cell["n_gap"] = sum(1 for o in obs if o["is_gap"])
        cell["n_focus_stops"] = sum(1 for o in obs if not o["is_gap"])
        cell["gap_ks"] = [s["k"] for s, o in zip(steps, obs) if o["is_gap"]]
        # ⭐⭐⭐⭐⭐ **三个决定性读数**（在 `GAP` 那一步上）
        gaps = [(s["k"], o) for s, o in zip(steps, obs) if o["is_gap"]]
        cell["gap_facts"] = [
            {"k": k, "body_matches_focus": o["body_matches_focus"],
             "n_real_focus": o["n_real_focus"], "has_focus": o["has_focus"],
             "ti_attr": o["ti_attr"], "ti_prop": o["ti_prop"]}
            for k, o in gaps]
        cell["n_gap_ever_body_focused"] = sum(
            1 for _k, o in gaps if o["body_matches_focus"])
        cell["n_gap_ever_has_focus"] = sum(
            1 for _k, o in gaps if o["has_focus"])
        cell["n_gap_ever_any_focus"] = sum(
            1 for _k, o in gaps if o["n_real_focus"] > 0)
        # ⭐⭐⭐⭐⭐ **可按定义推出的真门**（见 §195 第六节）
        cell["gap_plus_focus_eq_steps"] = (cell["n_gap"] + cell["n_focus_stops"]
                                          == len(steps))
        if key == "A0":
            # ⭐⭐⭐⭐⭐ **这里我第一版写错了一扇门**（口径错 ⇒ 门必然红）：
            #   我拿**含 `GAP` 的本批序列**去比**含 `BODY` 的 984 基线**
            #   ⇒ `eq_984_baseline` 必然是 `False`，而它**不是**发现
            # ⇒ ⇒ **正确的门是**：把本批的 `GAP` **换名**成 `BODY` 之后，
            #     必须**逐格等于** 984 的基线 ⇒ 那才证明
            #     「**同一条环、同一批位置，只是两批各叫各的**」
            cell["obs_as_body"] = ["BODY" if x == "GAP" else x
                                   for x in cell["obs"]]
            # ⭐⭐⭐⭐⭐ **第二版门还是错的，同一类**（980 那条：
            #   **切圈残段不许算进分母**）—— 我拿 **10 步整段**去比
            #   **4 格**的一圈 ⇒ 必然不等 ⇒ ⇒ **只取首个周期**
            cell["first_cycle"] = _cycle_of(cell["obs_as_body"])
            cell["eq_984_baseline_after_rename"] = (
                cell["first_cycle"] == BASELINE_CYCLE)
            # ⭐⭐ **原样保留那个必然红的读数**（它就是「口径不同」的证据）
            cell["eq_984_baseline_naive"] = (cell["obs"] == BASELINE_CYCLE)
            cell["naive_vs_renamed_note"] = (
                "⭐⭐⭐⭐⭐ **本批第一版把 `eq_984_baseline` 当回归门、"
                "拿含 `GAP` 的序列去比含 `BODY` 的 984 基线 ⇒ 必然红** ⇒ "
                "⇒ ⭐⭐ **门错、不是数据错** ⇒ 真正的回归门是"
                "**换名之后逐格相等** ⇒ 而 `naive` 那个恒假的读数"
                "**原样保留**（它就是两批口径不同的证据）")
        rec["arms"].append(cell)
        dump(out)

    # ── 源站那一臂：只按 `Tab` ────────────────────────────────────
    page.goto(SRC_URL, wait_until="domcontentloaded", timeout=90000)
    page.wait_for_timeout(10000)
    page.set_viewport_size({"width": 1512, "height": 1200})
    page.wait_for_timeout(3000)
    n_ready = page.locator('button[aria-label="音频"]').count()
    # ⭐⭐⭐⭐⭐ **「我没测到」必须能说清是「没就绪」还是「没登录」**
    #   —— 985 第一版只写「左栏入口没出来」，害我差点误判成「源站改版」
    diag = page.evaluate("""() => ({
        n_btn: document.querySelectorAll('button').length,
        n_ti0: document.querySelectorAll('[tabindex="0"]').length,
        n_nodeid: document.querySelectorAll('[data-nodeid]').length,
        text: (document.body.innerText || '').slice(0, 90)
                 .replace(/\\n/g, ' | ')
    })""") or {}
    s = {"n_ready": n_ready, "diag": diag, "steps": []}
    rec["src"] = s
    if n_ready == 0:
        s["skip_note"] = "左栏入口没出来 ⇒ 源站这一格什么也没测"
        # ⭐⭐⭐⭐⭐ **区分两种「没测到」**（第一版没分 ⇒ 差点误判成「源站改版」）
        _t = (diag.get("text") or "")
        s["why_not_measured"] = (
            "未登录（页面文本含「登录」）⇒ **不是产品改版、也不是就绪探针失效**"
            if ("登录" in _t or "Dreamina" in _t)
            else "⚠️ **待查**：既不是未登录、页面里又没有可聚焦元素 ⇒ "
                 "就绪探针本身可能已失效（**下一批要分辨这两种**）")
        s["note_about_old_baselines"] = (
            "⭐⭐⭐⭐ **旧口径的源站数字（环长 101、arc 18/101）自此只能算"
            "**历史记录** —— 拿不到登录态就复不了它们** ⇒ "
            "⇒ **「复现不出来」与「没量到」要分开记**（981 的纪律）")
        dump(out)
        continue
    sp = ev("""() => {
        const x = Math.floor(window.innerWidth / 2);
        const y = Math.floor(window.innerHeight * 0.92);
        const el = document.elementFromPoint(x, y);
        return (el && el.id !== 'canvas-watermark') ? [x, y] : null;
    }""")
    if sp:
        guard_point(sp[0], sp[1])      # ⛔ 守卫在 `mouse.click` **之前**
        page.mouse.click(sp[0], sp[1])
        page.wait_for_timeout(900)
    for k in range(1, N_STEPS_SRC + 1):
        page.keyboard.press("Tab")
        page.wait_for_timeout(SETTLE_SRC)
        s["steps"].append({"k": k, "key": "Tab", "f": ev(FOCUS_JS)})
        if k % 40 == 0:
            dump(out)
    obs = [x["f"] for x in s["steps"]]
    s["obs"] = [("GAP" if o["is_gap"] else (o["tid"] or o["id"] or o["tag"]))
                for o in obs]
    s["n_gap"] = sum(1 for o in obs if o["is_gap"])
    s["n_focus_stops"] = sum(1 for o in obs if not o["is_gap"])
    s["gap_ks"] = [x["k"] for x, o in zip(s["steps"], obs) if o["is_gap"]]
    s["gap_facts"] = [{"k": x["k"], "body_matches_focus": o["body_matches_focus"],
                       "n_real_focus": o["n_real_focus"],
                       "has_focus": o["has_focus"]}
                      for x, o in zip(s["steps"], obs) if o["is_gap"]]
    s["n_gap_ever_body_focused"] = sum(1 for f in s["gap_facts"]
                                       if f["body_matches_focus"])
    s["n_gap_ever_has_focus"] = sum(1 for f in s["gap_facts"] if f["has_focus"])
    s["n_gap_ever_any_focus"] = sum(1 for f in s["gap_facts"]
                                    if f["n_real_focus"] > 0)
    s["gap_plus_focus_eq_steps"] = (s["n_gap"] + s["n_focus_stops"]
                                    == len(obs))
    # ⭐⭐⭐⭐⭐ **旧口径 vs 新口径**（982 报的是「环长 101」⇒ 新口径是 **100 个
    #   可聚焦停靠点 + 1 个间隙**）⇒ 这就是「同一个东西要比同一个口径」
    p_old = _MIN_PERIOD(s["obs"])
    s["min_period_old_caliber"] = p_old
    s["note_caliber"] = (
        "⭐⭐⭐⭐⭐ **旧口径**（982/983 的 `min_period`）把 `GAP` **算成了格子** ⇒ "
        "环长 101 ⇒ ⚠️ **新口径下可聚焦停靠点是 100、间隙是 1** ⇒ "
        "⇒ **「环长」这个数在换口径后不再是同一件事** ⇒ "
        "**凡引用「101 格 / 26 格」的旧结论，分母都要减一**")
    dump(out)

dump(out)
print("PROBE_985_DONE", flush=True)
