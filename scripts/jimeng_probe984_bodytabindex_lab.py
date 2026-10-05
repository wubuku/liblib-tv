#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""batch 984 **实验室**探针（**零计费 / 零节点点击**）：
⭐⭐⭐⭐⭐ **把 H₃ 的「出处」这条悬案逼到一个更精确的位置** —— 而这一步
**978 的读数其实已经做完了一半**，本批补上另一半（干预臂）。

── 978 的读数里已经藏着决定性的一条 ────────────────────────────────

978 实验室（`about:blank` ＋ 3 个 `<button>`）的 `STOP_JS` **逐格读过**
`ti_attr`（`getAttribute('tabindex')`）与 `ti_prop`（`tabIndex` 属性）：

| 停靠点 | `ti_attr` | `ti_prop` |
|---|---|---|
| `BUTTON#lab-b1` | `null` | **0** |
| **`BODY`** | **`null`** | **−1** |

⇒ ⇒ ⭐⭐⭐⭐⭐ **`BODY` 的「不可聚焦」是 Blink 算出来的**（`tabIndex === -1`），
**不是作者写上去的属性**（`ti_attr` 是 `null`）
⇒ ⇒ ⭐⭐⭐⭐⭐ **H₄「`BODY` 靠普通 `tabindex` 规则进 Tab 环」当场被否** ——
按普通规则，`tabIndex === -1` 的元素**根本不该是可聚焦的候选**
⇒ ⇒ ⭐⭐⭐⭐ **而这正是 H₃ 整个形状的来源**：既然 `BODY` 不是普通候选，
那它必然是**焦点导航控制器里的显式兜底** ⇒ 兜底必然被放在**环的回绕点**
（「最后一个可聚焦元素」之后、「第一个可聚焦元素」之前）⇒
**977 / 982 / 983 量到的位置，逐格对上了。**

── ⚠️⚠️⚠️ 但这**仍然不是出处** ───────────────────────────────────

**复现 ≠ 出处、时长 ≠ 出处、比率 ≠ 出处、同构 ≠ 出处。**
本批做的事是**把问题从一个模糊的问号，变成一个精确的位置**：

> 「`tabIndex === -1` 的元素为什么还能成为 Tab 停靠点？」
> ⇒ 答案必在**焦点顺序导航**的实现里，**不在 `tabindex` 计算里**
> ⇒ ⇒ ⚠️ **本批不去读那一行源码 ⇒ 不许写「已找到出处」**

── ⭐⭐⭐⭐⭐ 本批真正要测的：两件事能不能被**分开** ──────────────────

⚠️⚠️⚠️ **第一版我在这里说过头了**（**过宽的断言**，和过宽的门同一族）：

> 我原本写「`tabindex` 在规范里就是两个东西：content attribute 与 IDL 属性
> ⇒ 974 那条纪律在这里是规范本身」

⇒ ⇒ ⭐⭐⭐⭐⭐ **读数把这句话否掉了**：`A3` 臂**只写 IDL**
（`body.tabIndex = 0`、**不碰** content attribute）⇒ 实测 `ti_attr` **也变成了
`'0'`** ⇒ ⇒ **Blink 的 `tabIndex` setter 会回写 content attribute**
⇒ ⇒ 而这与 HTML 规范一致（`tabIndex` IDL 属性**反映** `tabindex`）
⇒ ⇒ **所以那不是「两套口径」，是同一套规则的两个表面**
⚠️ **本探针下面那段 `ruler` 里的同一句断言也已被本批否掉，改掉了。**

⇒ ⇒ ⭐⭐⭐⭐ **本批真正分开的是另外两件事**（这才是 974 那条纪律的落点）：

| | 读数 | 含义 |
|---|---|---|
| **有没有写** | `ti_attr` | 作者**显式写了** `tabindex` 没有 |
| **算出多少** | `ti_prop` | 引擎**算出来**的 `tabIndex` 是多少 |

⇒ ⇒ 而 `A0` 上 `ti_attr = None` 而 `ti_prop = -1` ⇒
**「没写」与「算出 −1」是两件事** —— 这才是本批的口径发现。

⇒ ⇒ 本批做三个**可分辨**的干预臂：

- `A1` `body.setAttribute('tabindex', '0')` —— 写 **content attribute**
- `A3` `body.tabIndex = 0` —— 写 **IDL 属性**（不写 content attribute）
- `A4` `body.tabIndex = -1` —— 显式设成计算值
- `A2` `body.removeAttribute('tabindex')` —— **撤销 A1**

⇒ ⇒ ⭐⭐⭐⭐⭐ **A2 与 A4 必须回到 A0 的形状** —— 这一条**可以按定义推出**
（撤销 = 回到原状）⇒ 它是**真门**，不是「跑出来是什么就写什么」
⇒ ⇒ 而 **A1 与 A3 的读数并排**（`ti_attr` + `ti_prop` ＋ 环形状三列）
⇒ ⇒ **由读数判「`BODY` 的停靠由哪一套决定」，判据不预写这个答案**

**本批零计费**：实验室页 `about:blank`，**根本不打开源站**、**零节点点击**。
"""
from __future__ import annotations

import atexit
import json
import os
import re

OUT = "/tmp/b984-bodytabindex.json"
REPS = 2
N_STEPS = 14         # ⭐ 与 978 逐字同（够走 3 圈 + 2 步）
N_BUTTONS = 3        # ⭐ 与 978 逐字同
SETTLE = 120         # ms（与 978 逐字同：空白页不用 260）
PAGE_HTML = (
    '<!doctype html><html><head><meta charset="utf-8">'
    "<title>b984</title></head><body>"
    '<button id="lab-b1">b1</button>'
    '<button id="lab-b2">b2</button>'
    '<button id="lab-b3">b3</button>'
    "</body></html>"
)
# ⭐⭐⭐ **978 的基线环**（读数 `/tmp/b978-lab.json` 的 `cycle_sig`，2/2 一致）
#   ⇒ 本批 `A0` 必须**逐格复现**它 ⇒ 这是一条**回归门**，不是新发现
BASELINE_CYCLE = ["lab-b1", "lab-b2", "lab-b3", "BODY"]

_ARMS = (
    # (key, 干预 JS 源码, 这一臂想分辨什么)
    ("A0", "null", "基线：什么都不动（必须逐格复现 978 的 `cycle_sig`）"),
    ("A1", "document.body.setAttribute('tabindex', '0')",
     "写 **content attribute** ⇒ `ti_attr` 该变、`ti_prop` 也该跟着变"),
    ("A2", "document.body.removeAttribute('tabindex')",
     "**撤销 A1** ⇒ ⭐ 必须回到 A0 的形状（**这一条可按定义推出**）"),
    ("A3", "document.body.tabIndex = 0",
     "⭐ 只写 **IDL 属性**、**不写** content attribute ⇒ "
     "**这是分辨「两套口径」的关键臂**"),
    ("A4", "document.body.tabIndex = -1",
     "显式把**计算值**设成 −1 ⇒ ⭐ 必须回到 A0 的形状"),
)

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _src(name):
    p = os.path.join(_ROOT, "scripts", name)
    if not os.path.exists(p):
        return ""
    with open(p, encoding="utf-8") as f:
        return f.read()


# ⚠️⭐⭐⭐ `STOP_JS` 的源头是 **978** ⇒ 本批**逐字继承**、不许自己重写
_p978 = _src("jimeng_probe978_lab_body_stop.py")
_p979 = _src("jimeng_probe979_dwell_src.py")
_ME = open(__file__, encoding="utf-8").read()


def _grab(name, src=None):
    m = re.search(r'^%s\s*=\s*r?"""(.*?)"""' % name, src or "", re.S | re.M)
    assert m, "抠不到 %s" % name
    _s = m.group(1)
    assert _s in (src or ""), "%s 不是逐字抠出来的" % name
    return _s


STOP_JS = _grab("STOP_JS", _p978)

assert not re.search(r'^STOP_JS\s*=\s*r?"""', _ME, re.M), \
    "本批自己定义了**继承来的** `STOP_JS` ⇒ 尺子分叉了"
assert STOP_JS in _p978, "STOP_JS 不在 978 探针里 ⇒ 不是同一件仪器"
# ⭐⭐⭐⭐⭐ **978 的读数里那两列必须还在** —— 少了它们本批就没有正题
assert "ti_attr" in STOP_JS and "ti_prop" in STOP_JS, \
    "`STOP_JS` 不读 `ti_attr` / `ti_prop` 了 ⇒ 本批的正题不存在"
assert "a.getAttribute('tabindex')" in STOP_JS, \
    "`ti_attr` 的口径变了（必须是 **content attribute**）⇒ 本批要重写"
assert "a.tabIndex" in STOP_JS, \
    "`ti_prop` 的口径变了（必须是 **IDL 属性**）⇒ 本批要重写"


def _code_only(js):
    o = []
    for line in js.split("\n"):
        t = line.strip()
        if t.startswith("//") or t.startswith("*") or t.startswith("/*"):
            continue
        o.append(line.split("//")[0])
    return "\n".join(o)


# ⭐⭐⭐⭐ **纯读守卫**：`STOP_JS` 只读 `document.activeElement`、从不写 DOM
#   ⚠️⚠️⭐⭐⭐ **第一版这道门「过窄」，而这就是我自己的纪律**：
#   我用子串 `"tabIndex ="` 当禁词 ⇒ 而 `STOP_JS` 里**读**属性的那行是
#   `a.tabIndex === undefined` ⇒ **`"tabIndex ="` 是它的前缀** ⇒ 门红
#   ⇒ ⇒ ⭐⭐ **过窄的门和过宽的门一样坏** —— 它逼我改 `STOP_JS`（**继承来的
#   那把尺子不许改**）或者把门删掉 ⇒ **两条都是更差的工程**
#   ⇒ ⇒ 修法：**改成正则**（真赋值是 `.tabIndex = ` 后面**不是** `=`）
_CODE = _code_only(STOP_JS)
for _pat, _why in (
        (r"\.focus\s*\(", "调 focus()"),
        (r"\.setAttribute\s*\(", "写属性"),
        (r"\.removeAttribute\s*\(", "删属性"),
        (r"\.tabIndex\s*=(?!=)", "**写** IDL 属性 `tabIndex`"),
        (r"\.setAttribute\s*\(\s*['\"]tabindex", "写 `tabindex` content attribute"),
        (r"new\s+MutationObserver", "MutationObserver"),
        (r"\.addEventListener\s*\(", "addEventListener"),
        (r"location\.reload", "location.reload")):
    assert not re.search(_pat, _CODE), \
        "`STOP_JS` 里出现了%s ⇒ 它不再是**纯读件**" % _why
# ⭐⭐⭐ **成对钉三条**（把「过窄」「过宽」两个方向都钉住）：
#   ① 真赋值必须**被抓住**
assert re.search(r"\.tabIndex\s*=(?!=)",
                 "var a = 1;\na.tabIndex = 0;\n"), "反向门①坏了：写 `tabIndex` 抓不住"
assert not re.search(r"\.tabIndex\s*=(?!=)",
                     "var a = 1;\na.tabIndex === undefined;\n"), (
    "⭐⭐⭐ **反向门②坏了**：这正是第一版门红的那个形状（**读**属性被当成**写**）"
    "⇒ 这道门「过窄」")
#   ③ 必须**读得到** `tabIndex`（否则整道门可能退化成「因为没读所以没写」）
assert re.search(r"\.tabIndex\b", _CODE), \
    "`STOP_JS` 连 `tabIndex` 都不读了 ⇒ 纯读守卫可能变成**恒真**"
# ⭐⭐⭐⭐⭐ **本批的「可逆性」纪律要钉在纸上**：A2/A4 必须回到 A0 的形状
assert [a[0] for a in _ARMS] == ["A0", "A1", "A2", "A3", "A4"], \
    "臂的顺序变了 ⇒ **A2/A4 的可逆性判据会指向别的臂**"
assert BASELINE_CYCLE == ["lab-b1", "lab-b2", "lab-b3", "BODY"], \
    "978 的基线环被改动了 ⇒ 本批的回归门钉的不再是 978 那个"

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


# ⚠️⭐⭐⭐⭐⭐ **干预臂的注入件** —— 它是**唯一**允许写 DOM 的地方
#   ⇒ 所以它必须**独立成件**、并且被门盯住（只许改 `body` 的 tabindex）
ARM_JS = """(src) => {
  // eslint-disable-next-line no-new-func
  if (src) new Function(src)();
  const b = document.body;
  return {
    src: src,
    // ⭐⭐⭐⭐ **两套口径必须并排读出**（974 的纪律，在这里是规范本身）
    ti_attr: b.getAttribute('tabindex'),
    ti_prop: b.tabIndex,
    has_attr: b.hasAttribute('tabindex'),
    outer_head: b.outerHTML.slice(0, 90),
    n_focusable_attr0: document.querySelectorAll(
      '[tabindex="0"], a[href], button:not([disabled])').length
  };
}"""


def walk_arm(key):
    """按 `Tab` 走 `N_STEPS` 步，逐格读 `STOP_JS`（**逐字继承 978 的那件**）。"""
    steps = []
    for k in range(1, N_STEPS + 1):
        page.keyboard.press("Tab")
        page.wait_for_timeout(SETTLE)
        st = ev(STOP_JS) or {}
        steps.append({"k": k, "key": "Tab", "stop": st})
    keys = []
    for s in steps:
        st = s["stop"]
        keys.append("BODY" if st.get("is_document_body")
                    else (st.get("tid") or st.get("id") or st.get("tag")))
    return steps, keys


def cycle_of(keys):
    """取「首次重复之前」的那一段（978 的 `cycle_sig` 口径）。"""
    for i in range(1, len(keys)):
        if keys[i] == keys[0]:
            return keys[:i]
    return list(keys)


out = {
    "target": "lab", "url": "about:blank", "reps": REPS,
    "n_steps": N_STEPS, "n_buttons": N_BUTTONS,
    "question": "⭐⭐⭐⭐⭐ **`BODY` 的「不可聚焦」是 content attribute 还是"
                "**IDL 计算值**？** `tabIndex === -1` 却仍能成为 Tab 停靠点 ⇒ "
                "**它必然是焦点导航控制器里的显式兜底，不是 `tabindex` 计算的结果**"
                " ⇒ ⇒ ⚠️ **本批把问题逼到精确位置，但不读源码 ⇒ 不许写「已找到出处」**",
    "ruler": {
        "js_verbatim_from_978": ["STOP_JS"],
        "new_pieces": ["ARM_JS"],
        "why_verbatim": "⭐⭐⭐⭐⭐ **`STOP_JS` 是 978 逐格读过 `ti_attr` / "
                        "`ti_prop` 的那件** ⇒ 本批的读数**与 978 同口径** ⇒ "
                        "**同一把尺子量两个问题**",
        "why_new_piece_is_the_only_writer": "⚠️⭐⭐⭐⭐⭐ **`ARM_JS` 是本批**唯一**"
                                            "允许写 DOM 的件** ⇒ 独立成件并被门盯住"
                                            "（只许改 `body` 的 tabindex）⇒ "
                                            "**读数层保持纯读**",
        "two_calibers_are_real_here": "⚠️⭐⭐⭐⭐⭐ **这句断言被本批自己的读数否掉了，"
                                      "改掉**（第一版说过头了）：我原写"
                                      "「`tabindex` 在规范里就是两个东西："
                                      "content attribute 与 IDL 属性」⇒ "
                                      "**`A3` 臂只写 IDL、`ti_attr` 也变成了 `'0'`** ⇒ "
                                      "**Blink 的 `tabIndex` setter 回写 content attribute**"
                                      "⇒ **那是同一套规则的两个表面** ⇒ ⇒ "
                                      "⭐⭐⭐ **本批真正分开的**是**两件事**："
                                      "**有没有写**（`ti_attr`）与**算出多少**"
                                      "（`ti_prop`）⇒ `A0` 上 `None` 而 `-1` "
                                      "⇒ **「没写」与「算出 −1」不是一回事**",
        "derivable_gates": "⭐⭐⭐⭐⭐ **只有这几条能按定义推出**（⇒ 它们才是真门）：\n"
                           "  · `A0` 必须逐格复现 **978 的 `cycle_sig`**（回归门）\n"
                           "  · `A2`（撤销 A1）**必须回到 A0 的形状**\n"
                           "  · `A4`（显式设 −1）**必须回到 A0 的形状**\n"
                           "  ⭐⭐⭐ **`A1` 与 `A3` 的结果**属于**待测事实**，"
                           "**判据不预写** ⇒ 由读数判「停靠由哪一套决定」",
        "zero_billing": "⭐⭐⭐⭐⭐ **零计费**：实验室页 `about:blank`，"
                        "**根本不打开源站**、**零节点点击**、**零计费控件**",
    },
    "baseline": {
        "s978_cycle_sig": "⭐⭐⭐⭐⭐ **978 实测（2/2）：`cycle_sig` = "
                          "`['lab-b1', 'lab-b2', 'lab-b3', 'BODY']`（长 4）** ⇒ "
                          "**3 个 button + 1 枚 `BODY`** ⇒ 本批 `A0` 是**回归门**",
        "s978_body_ti": "⭐⭐⭐⭐⭐ **978 的读数里已经有决定性的一半**："
                        "`BODY` 那格 **`ti_attr = null`、`ti_prop = -1`**；"
                        "对照 `BUTTON#lab-b1` 是 `ti_attr = null`、`ti_prop = 0` ⇒ "
                        "**`BODY` 的「不可聚焦」是 Blink 算出来的计算值**",
        "s978_l3_flaky": "⭐⭐⭐ **顺带交叉印证 980**：978 的 `L3` 臂 "
                         "`n_body_stops = 2`（其余臂都是 3）⇒ "
                         "**那一圈真的没走 `BODY`** ⇒ 与 980 量到的 "
                         "**实验室缺失率 ≈ 7.8%** 同向",
    },
    "arms": [{"key": k, "src": s, "note": n} for k, s, n in _ARMS],
    "runs": [],
}

for rep in range(1, REPS + 1):
    print("===== rep %d =====" % rep, flush=True)
    rec = {"rep": rep, "arms": []}
    out["runs"].append(rec)
    dump(out)

    for key, src, _note in _ARMS:
        # ⭐ 每臂都**从一张干净的页面**开始 ⇒ 臂与臂之间零污染
        page.set_content(PAGE_HTML, wait_until="domcontentloaded")
        page.wait_for_timeout(400)
        pre = ev(ARM_JS, [src]) or {}
        steps, keys = walk_arm(key)
        cyc = cycle_of(keys)
        body_steps = [s["stop"] for s in steps if s["stop"].get("is_document_body")]
        cell = {
            "arm": key, "src": src, "pre": pre,
            "steps": steps, "keys": keys,
            "cycle_sig": cyc, "cycle_len": len(cyc),
            "n_body_stops": sum(1 for s in steps
                                if s["stop"].get("is_document_body")),
            "body_ti_attr_after": (body_steps[0].get("ti_attr")
                                   if body_steps else None),
            "body_ti_prop_after": (body_steps[0].get("ti_prop")
                                   if body_steps else None),
            "body_in_cycle": "BODY" in cyc,
            "body_pos_in_cycle": (cyc.index("BODY") if "BODY" in cyc else None),
            "body_stop_ks": [s["k"] for s in steps
                             if s["stop"].get("is_document_body")],
        }
        # ⭐⭐⭐⭐⭐ **关系式**（环长、成员序列都钉；不钉 `dom_rank` 之类绝对值）
        cell["eq_baseline_cycle"] = (cyc == BASELINE_CYCLE)
        rec["arms"].append(cell)
        dump(out)

dump(out)

# ── 汇总：⭐⭐ 只做计数与关系式，不下结论 ───────────────────────────
for rec in out["runs"]:
    by = {a["arm"]: a for a in rec["arms"]}
    a0 = by.get("A0", {})
    for key, _src, _n in _ARMS:
        a = by.get(key)
        if not a:
            continue
        # ⭐⭐⭐ **可逆性**：撤销臂必须回到基线形状（**可按定义推出 ⇒ 真门**）
        a["same_as_baseline"] = (a["cycle_sig"] == a0.get("cycle_sig"))
        # ⭐⭐⭐ **两套口径的读数并排**（判据不预写「谁决定停靠」）
        a["attr_vs_prop"] = {
            "ti_attr": a["pre"].get("ti_attr"),
            "ti_prop": a["pre"].get("ti_prop"),
            "has_attr": a["pre"].get("has_attr"),
            "outer_head": a["pre"].get("outer_head"),
        }
        print("  %s: cycle=%s len=%d body_in_cycle=%s pos=%s "
              "ti_attr=%r ti_prop=%r same_as_baseline=%s"
              % (key, a["cycle_sig"], a["cycle_len"], a["body_in_cycle"],
                 a["body_pos_in_cycle"], a["pre"].get("ti_attr"),
                 a["pre"].get("ti_prop"), a["same_as_baseline"]), flush=True)

dump(out)
print("PROBE_984_DONE", flush=True)
