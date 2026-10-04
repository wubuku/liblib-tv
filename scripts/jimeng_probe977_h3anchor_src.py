#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""batch 977 · 源站探针：⭐⭐⭐⭐⭐ 正面检验 **H₃** —— 那枚 `BODY` 到底是不是
「**无条件**站在 DOM 里第一个可聚焦元素的**前一格**」。

── 976 之后剩什么 ──────────────────────────────────────────────────────

- 975：H₁（祖先带正 `tabindex` ⇒ 独立作用域）**被判否**
- 976：H₂（开头那段没有可聚焦元素 ⇒ 才是 `BODY` 出现的条件）**被判否**
  —— 往 `<body>` 最前面注入一枚 `tabindex=0` 的 `div`，
  **`BODY` 仍在环里、位置一点没变**（2/2）
- 976 的副产品：H₃ 浮出且**有实测支撑** ——
  `BODY` 恒站在「DOM 里第一个可聚焦元素」的**前一格**
  ⚠️ 但**出处仍未标注**（实测如此 ≠ 规范如此）

⚠️⚠️⚠️ **976 那个支撑其实是「弱」的** ——
976 只在**开头那一段**试过一次，而 H₃ 说的是「**恒**」。
⚠️⭐⭐⭐ **一次成功不叫可靠** ⇒ 本批要把它变成**可判红**的强命题。

── ⭐⭐⭐⭐⭐ 本批的三个臂，以及「哪一个才是 H₃ 的正面检验」──────────────

- **臂 0（基线）**：什么也不做
- **臂 A（连插两枚）**：往 `<body>` 最前面**连插两枚**可聚焦元素
  ⇒ 问：`BODY` 还在吗？它还是「第一个可聚焦元素的前一格」吗？
  ⚠️ **注意：臂 A 单独看并不能分开任何东西** ——
  「回绕途经点」与「无条件途经点」在两枚的情况下**预测完全一样**。
  臂 A 的价值是**给出计数与座位**（`BODY` 是不是被彻底挤掉）。
- ⭐⭐⭐⭐⭐ **臂 B（去掉第一个可聚焦元素的资格）** —— **这才是 H₃ 的正面检验**：
  把 DOM 里**第一个**可聚焦元素临时设成 `tabindex="-1"`
  （**纯 JS、可还原**、原属性值先记下来）⇒
  于是「第一个可聚焦元素」**换成了下一个** ⇒
  ⭐⭐⭐ **H₃ 预测：`BODY` 会重新锚定，仍然紧贴在新第一个的前一格。**
  若 `BODY` 消失 ⇒ H₃ 的「无条件」不成立；
  若 `BODY` 还在但**不再紧贴**新第一个 ⇒ H₃ 被否。

⚠️⭐⭐ **不预写答案**：探针只输出**读数与关系**，
三个臂各自都能判红，真伪交给 verifier。

⚠️⭐⭐ **干预必须可还原**（976 的纪律，本批继续照办）：
两枚注入件各带**可识别 id**、`INJECT_JS` 幂等、`finally` 里**无条件移除**；
臂 B 的属性改动**先记原值**、再改、**无条件**还原、
并**单独复查**改完 / 还原后的 `tabindex` ⇒ ⭐⭐ **「清理代码跑过了」
不等于「东西真的变回去了」**。

⚠️⭐⭐⭐ **读数不许用 `or` 兜底**（971 踩过把 `0` 当假值那一族）——
本批 `UNFOCUS_JS` 里区分「属性**不存在**」与「属性是空串」，**不许**用 `||`。

⚠️⭐⭐⭐⭐ **干预件的身份用 `own.id` 认，不用 `data-testid`** ——
976 的 `INJECT_JS` 把 `data-testid` **写死**成同一个值 ⇒ 两枚会撞名
⇒ ⭐⭐⭐ **读数里撞名的字段不能当身份**（那正是 969「用 `landed` 当代理条件」
把 `BODY` 整行滤掉的那一族）。

**本批零计费动作。** 按键只有 `Tab`；⛔ 计费守卫拦在 `mouse.click` **之前**。
"""
from __future__ import annotations

import json
import os
import re

OUT = "/tmp/b977-h3.json"
REPS = 2
SETTLE = 260           # ms（照 967–976）
BLANK_WAIT = 900       # ms
N_LEAD_CAP = 140       # ⭐ 硬上限，不是目标
RAIL_TID = "canvas-fixed-toolbar"
NODE_SEL = "[data-nodeid], .react-flow__node"
ID_A = "jimeng977-injected-a"
ID_B = "jimeng977-injected-b"

FORBIDDEN_TIDS = ("canvas-commerce-entry", "canvas-pay-trigger",
                  "canvas-recharge", "canvas-member-buy")

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _src(name):
    p = os.path.join(_ROOT, "scripts", name)
    if not os.path.exists(p):
        return ""
    with open(p, encoding="utf-8") as f:
        return f.read()


# ⚠️⚠️⚠️ **976 是本批的仪器来源**（不是 973 了 —— 976 是**消费者**，
#   本批要连**干预件**也一起继承）
_p973 = _src("jimeng_probe973_ringorder_ck.py")
_p967 = _src("jimeng_probe967_armptr_src.py")
_p970 = _src("jimeng_probe970_owntid_ck.py")
_p972 = _src("jimeng_probe972_seam_src.py")
# ⚠️⭐⭐ **连 974 / 975 也要加载** —— 它们只出现在 `assert` 里，
#   **不定义就是运行期 `NameError`**，而 `py_compile` **抓不到**
_p974 = _src("jimeng_probe974_source_domrank_src.py")
_p975 = _src("jimeng_probe975_scope_src.py")
_p976 = _src("jimeng_probe976_counterfactual_src.py")


def _grab(name, src=None):
    m = re.search(r'^%s\s*=\s*r?"""(.*?)"""' % name, src or "", re.S | re.M)
    assert m, "抠不到 %s" % name
    _s = m.group(1)
    assert _s in (src or ""), "%s 不是逐字抠出来的" % name
    return _s


# ⭐⭐⭐ 同一件仪器：源头一律是 973（974 / 975 / 976 都只是消费者）
DOMRANK_JS = _grab("DOMRANK_JS", _p973)
INSTALL_JS = _grab("INSTALL_JS", _p967)
READ_JS = _grab("READ_JS", _p967)
OFF_NULL_JS = _grab("OFF_NULL_JS", _p967)
BLANK_JS = _grab("BLANK_JS", _p967)
OWN_JS = _grab("OWN_JS", _p970)
SEAT_JS = _grab("SEAT_JS", _p972)
# ⭐⭐⭐⭐⭐ 干预件也**逐字继承 976** ⇒ 「本批的干预和 976 是同一件东西」
GAP_JS = _grab("GAP_JS", _p976)
INJECT_JS = _grab("INJECT_JS", _p976)
UNINJECT_JS = _grab("UNINJECT_JS", _p976)

# ── ⭐⭐⭐⭐⭐ 本批**唯一**的新件：`UNFOCUS_JS` / `REFOCUS_JS`（**可还原**）──
#   臂 B 的动作：把「DOM 里第一个可聚焦元素」临时设成 `tabindex="-1"`。
#   ⚠️⭐⭐⭐ 扫描逻辑与 976 的 `GAP_JS` **逐字同构**（同样的
#   `(tabIndex !== undefined) && (tabIndex >= 0)` 判据、同样的
#   「从 `body` 索引 +1 往后找第一个」）⇒ **不然两臂量的不是同一件事**。
UNFOCUS_JS = """() => {
  const all = Array.prototype.slice.call(document.querySelectorAll('*'));
  const bi = all.indexOf(document.body);
  for (let i = bi + 1; i < all.length; i += 1) {
    const el = all[i];
    const ti = el.tabIndex;
    const focusable = (ti !== undefined) && (ti >= 0);
    if (!focusable) continue;
    // ⭐⭐⭐ 区分「属性不存在」与「属性是空串」⇒ **不许用 or 兜底**
    //    （⚠️ 这条纪律**不许**把被禁的写法原文抄进注释 —— 门会连注释一起扫）
    const had = el.hasAttribute('tabindex');
    const orig = had ? el.getAttribute('tabindex') : null;
    el.setAttribute('tabindex', '-1');
    return {found: true,
            i_rel: i - bi - 1,
            tag: (typeof el.tagName === 'string') ? el.tagName.toUpperCase() : '',
            tid: el.getAttribute ? el.getAttribute('data-testid') : null,
            eid: el.id ? el.id : null,
            had_tabindex_attr: had,
            orig_tabindex_attr: orig,
            ti_attr_now: el.getAttribute('tabindex'),
            ti_prop_now: (el.tabIndex === undefined) ? null : el.tabIndex,
            still_focusable: (el.tabIndex !== undefined) && (el.tabIndex >= 0)};
  }
  return {found: false};
}"""

REFOCUS_JS = """([rec]) => {
  const all = Array.prototype.slice.call(document.querySelectorAll('*'));
  const bi = all.indexOf(document.body);
  // ⭐⭐ 下标不许用 `or` 兜底 —— `0` 是合法下标（`rec.i_rel` 用三元判类型）
  const rel = (typeof rec.i_rel === 'number') ? rec.i_rel : -1;
  const target = (rel >= 0) ? all[bi + 1 + rel] : null;
  if (!target) return {restored: false, why: 'no_target'};
  const tagNow = (typeof target.tagName === 'string')
      ? target.tagName.toUpperCase() : '';
  // ⭐⭐⭐ **还原前先核对身份**：下标对上了但**不是同一枚元素** ⇒ 宁可报红
  if (typeof rec.tag === 'string' && tagNow !== rec.tag) {
    return {restored: false, why: 'tag_mismatch',
            tag_now: tagNow, tag_expected: rec.tag};
  }
  if (rec.had_tabindex_attr === true) {
    target.setAttribute('tabindex', rec.orig_tabindex_attr);
  } else {
    target.removeAttribute('tabindex');
  }
  return {restored: true,
          had_tabindex_attr: rec.had_tabindex_attr,
          ti_attr_now: target.getAttribute('tabindex'),
          ti_prop_now: (target.tabIndex === undefined) ? null : target.tabIndex,
          focusable_now: (target.tabIndex !== undefined) && (target.tabIndex >= 0)};
}"""

# ── ⭐⭐⭐ 自证与守卫（每一条都要能判红，不能是恒真句）────────────────
# 1) 干预件逐字来自 976
assert INJECT_JS in _p976 and UNINJECT_JS in _p976 and GAP_JS in _p976
# 2) `INJECT_JS` 必须真的插在**最前面**、且**先清一次**（幂等）
assert 'document.body.insertBefore(el, document.body.firstChild)' in INJECT_JS
assert 'if (old) old.remove();' in INJECT_JS
# 3) 读数不许用 `or` 兜底 —— 物理禁止
#    ⚠️⚠️⚠️⭐⭐⭐ **这道门第一次跑就红了，而红的不是代码，是**注释**——
#    注释里**引用了被禁的那一种写法**（还举了例子）⇒ **子串匹配把注释也扫进来了**
#    ⇒ ⇒ ⭐⭐⭐ **「守卫会命中自己」有两种形态**：
#       976 那种是「**守卫那行自己**在源码里」，
#       本批这种是「**注释为了说明纪律、抄了一遍被禁的写法**」
#       ⇒ ⇒ 两条都归同一族：**守卫的匹配范围比它想匹配的大**
#    ⇒ ⇒ 修法：注释**不许抄被禁的写法原文**，改用**描述**
assert "ti_attr ||" not in GAP_JS
assert "||" not in UNFOCUS_JS
assert "||" not in REFOCUS_JS
# 4) 臂 B 的扫描判据必须与 976 的 `GAP_JS` **逐字同构**
for _frag in ("const ti = el.tabIndex;",
              "const focusable = (ti !== undefined) && (ti >= 0);"):
    assert _frag in UNFOCUS_JS, "臂 B 的判据与 GAP_JS 不同构：%s" % _frag
    assert _frag in GAP_JS, "GAP_JS 里没有：%s" % _frag
# 5) ⭐⭐⭐⭐⭐ **守卫会命中自己**（976 踩过）⇒ **行首锚定**（`^` + `re.M`），
#   只匹配「**真的在行首定义**」，不会命中源码里那行 `assert` 自身
for _nm, _src_ in (("974", _p974), ("975", _p975), ("976", _p976)):
    assert not re.search(r'^DOMRANK_JS\s*=\s*r?"""', _src_, re.M), (
        "%s 自己定义了 DOMRANK_JS 字面量 ⇒ 尺子分叉了" % _nm)
# 6) ⭐⭐ **不许自己在行首定义那些继承来的字面量**
assert not re.search(r'^(INJECT_JS|UNINJECT_JS|GAP_JS|SEAT_JS|OWN_JS)\s*=\s*r?"""',
                     __file__ and open(__file__, encoding="utf-8").read(), re.M), (
    "本批自己定义了继承来的字面量 ⇒ 尺子分叉了")
# 7) 臂 B 的还原**必须**是「有则设回、无则删掉」两条路都写全
assert "target.removeAttribute('tabindex')" in REFOCUS_JS
assert "target.setAttribute('tabindex', rec.orig_tabindex_attr)" in REFOCUS_JS
# 8) ⭐ **焦点不许被脚本抢**（纯读 + 可还原的属性改动，不许调 `focus()`）
assert "focus(" not in UNFOCUS_JS and "focus(" not in REFOCUS_JS


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
        raise AssertionError("⛔ 拦下计费控件：%r" % t)


def guard_point(x, y):
    at = ev("""([x, y]) => {
        const el = document.elementFromPoint(x, y);
        const host = el && el.closest('[data-testid]');
        return {tid: host ? host.getAttribute('data-testid') : null,
                al: (el.innerText || el.textContent || '').slice(0, 40)};
    }""", [x, y])
    guard((at or {}).get("al"), (at or {}).get("tid"))
    return at


URL = ("https://jimeng.jianying.com/ai-tool/ai-canvas/"
       "64b58cd5-7b04-4312-890a-09f2d1d3399f"
       "?enter_from=project_list&from_page=create")

out = {
    "target": "source", "url": URL, "reps": REPS, "rail_tid": RAIL_TID,
    "n_lead_cap": N_LEAD_CAP, "node_sel": NODE_SEL,
    "ids": [ID_A, ID_B],
    "question": "⭐⭐⭐⭐⭐ **正面检验 H₃**：那枚 `BODY` 是不是"
                "**无条件**站在「DOM 里第一个可聚焦元素」的**前一格**？⇒ "
                "**臂 A** 连插两枚（看计数/座位）、"
                "**臂 B** 把第一个可聚焦元素临时设为不可聚焦（看会不会重新锚定）",
    "ruler": {
        "js_verbatim_from_973": ["DOMRANK_JS"],
        "js_verbatim_from_967": ["INSTALL_JS", "READ_JS", "OFF_NULL_JS",
                                 "BLANK_JS"],
        "js_verbatim_from_970": ["OWN_JS"],
        "js_verbatim_from_972": ["SEAT_JS"],
        "js_verbatim_from_976": ["GAP_JS", "INJECT_JS", "UNINJECT_JS"],
        "new_pieces": ["UNFOCUS_JS", "REFOCUS_JS"],
        "instrument_origin": "⭐⭐⭐ 本批的**干预件也逐字继承 976** ⇒ "
                             "「本批的干预和 976 是同一件东西」由 `assert` 钉住，"
                             "不是文档保证",
        "why_own_id_is_identity": "⭐⭐⭐⭐⭐ 976 的 `INJECT_JS` 把 `data-testid` "
                                  "**写死**成同一个值 ⇒ 两枚会**撞名** ⇒ "
                                  "**读数里撞名的字段不能当身份** ⇒ "
                                  "本批用 `own.id`（两枚各自的 id）认身份",
        "why_arm_b_is_the_real_test": "⭐⭐⭐⭐⭐ 臂 A **单独看分不开任何东西** —— "
                                      "「回绕途经点」与「无条件途经点」在两枚的情况下"
                                      "**预测完全一样** ⇒ ⭐⭐⭐ **臂 B 才是 H₃ 的正面检验**",
        "why_arm_b_scan_is_isomorphic": "⭐⭐⭐ 臂 B 的扫描判据与 976 的 `GAP_JS` "
                                        "**逐字同构**（同样的 focusable 判据、"
                                        "同样的「从 body 索引 +1 往后找」）⇒ "
                                        "**不然两臂量的不是同一件事**",
        "why_no_or_fallback": "⚠️⭐⭐ **读数不许用 `or` 兜底** ⇒ "
                              "UNFOCUS_JS 区分「属性不存在」与「属性是空串」；"
                              "REFOCUS_JS 的下标不许写 `rec.i_rel || 0`",
        "reversibility": "⭐⭐⭐ **干预必须可还原**：注入件带可识别 id、"
                         "`INJECT_JS` 幂等、`finally` 里**无条件**移除；"
                         "臂 B **先记原属性值**、**无条件**还原、"
                         "并**单独复查** ⇒ ⭐⭐ 「清理代码跑过了」"
                         "**不等于**「东西真的变回去了」",
    },
    "hypothesis_H3": {
        "statement": "H₃：`BODY` 是**无条件途经点**，**恒站在"
                     "「DOM 里第一个可聚焦元素」的**前一格",
        "s975_h1_no": "H₁（作用域边界）975 判否",
        "s976_h2_no": "H₂（开头没有可聚焦元素才是条件）976 判否",
        "falsifiable_two_ways": "⭐⭐⭐ **两个方向都能判红**："
                                "臂 B 之后 `BODY` **消失** ⇒ H₃ 的「无条件」不成立；"
                                "`BODY` **还在但不紧贴**新第一个 ⇒ H₃ 被否；"
                                "`BODY` **仍紧贴**新第一个 ⇒ H₃ 这一次**扛住了**",
        "honest_limit": "⚠️⚠️ **一次扛住不叫证明** ⇒ 977 仍只记"
                        "「这一次、这两个条件下」⇒ **出处仍未标注**",
        "not_predicted": "⚠️ **探针里不预写 H₃ 的答案** —— 只输出读数与关系",
    },
    "baseline": {
        "s976_h2_falsified": "⭐ 976 实测：注入一枚真可聚焦元素后，"
                             "`BODY` 仍在环里、位置一点没变 ⇒ H₂ 被否",
        "s976_weak_spot": "⚠️⚠️ 976 那个支撑是**弱**的 —— "
                          "它只在**开头那一段**试过一次，"
                          "而 H₃ 说的是「**恒**」⇒ ⭐⭐⭐ **一次成功不叫可靠**",
        "no_prewrite": "⚠️⭐⭐ **不许把复刻那套机制当预期**",
    },
    "runs": [],
}


def walk(c):
    """走一圈；读数里每一格都带 `dom` 与 `seat`。"""
    c["n_lead"] = 0
    while c["n_lead"] < N_LEAD_CAP:
        c["n_lead"] += 1
        inst = ev(INSTALL_JS, [NODE_SEL])
        if inst.get("installed"):
            c["n_install"] += 1
        try:
            page.keyboard.press("Tab")
            page.wait_for_timeout(SETTLE)
            ap = ev(READ_JS)
            c["n_read"] += 1
            o = ev(OWN_JS, [NODE_SEL])
            s = ev(SEAT_JS, [NODE_SEL])
            dr = ev(DOMRANK_JS, [NODE_SEL])
            g = ev(GAP_JS, [NODE_SEL]) if (s or {}).get("is_body") else None
        finally:
            ev(OFF_NULL_JS)
        c["rows"].append({"k": c["n_lead"], "key": "Tab",
                          "fired": (ap or {}).get("fired"),
                          "landed": (ap or {}).get("landed"),
                          "own": o, "seat": s, "dom": dr, "gap": g})
        if o.get("closest_tid") == RAIL_TID:
            c["n_rail_stops"] += 1
            if c["n_rail_stops"] >= 2:
                break        # ⭐ 数到第 2 次命中左栏 = 走满一圈
        dump(out)
    else:
        c["n_lead_cap_hit"] = True


def _key(own):
    """⭐⭐⭐ **身份只用 `id` / testid / tag**，绝不靠撞名的 `data-testid` 排序。"""
    own = own or {}
    for f in ("self_tid", "closest_tid", "id"):
        v = own.get(f)
        if isinstance(v, str) and v:
            return v
    return "<%s/%s>" % (own.get("tag"), own.get("aria") or "?")


def summarize(c, tag, rows):
    # ⚠️⭐⭐⭐ **参数显式传 rows**（976 的教训：汇总层回头去读可变状态
    #   ⇒ 读到的是**已清空的列表** ⇒ 「汇总层取值错了、原始读数里答案
    #   一直在」这一族的**第五次**风险）
    assert rows is not None, "summarize 收不到 rows"
    out_rows = [r for r in rows if (r.get("own") or {}).get("kind") == "out"]
    keys = [_key(r.get("own")) for r in out_rows]
    body_i = [i for i, r in enumerate(out_rows)
              if (r.get("seat") or {}).get("is_body") is True]
    inj_i = [i for i, r in enumerate(out_rows)
             if (r.get("own") or {}).get("id") in (ID_A, ID_B)]
    c[tag + "_names"] = keys
    c[tag + "_body_seats"] = body_i
    c[tag + "_injected_seats"] = inj_i
    c[tag + "_n_body"] = len(body_i)
    c[tag + "_n_injected"] = len(inj_i)
    c[tag + "_ring_len"] = len(out_rows)
    # ⭐⭐⭐⭐⭐ **H₃ 的可判红命题**：`BODY` 的**环上后继**
    #   是不是「DOM 里第一个可聚焦元素」
    gap = [r["gap"] for r in out_rows if r.get("gap")]
    c[tag + "_gap"] = gap[0] if gap else None
    ff = (c[tag + "_gap"] or {}).get("first_focus") or {}
    dom_first = ff.get("tid") if isinstance(ff.get("tid"), str) else None
    c[tag + "_dom_first_focusable"] = dom_first
    c[tag + "_body_next_key"] = (
        keys[body_i[0] + 1] if body_i and body_i[0] + 1 < len(keys) else None)
    c[tag + "_body_precedes_dom_first"] = bool(
        dom_first is not None
        and c[tag + "_body_next_key"] is not None
        and c[tag + "_body_next_key"] == dom_first)
    # ⚠️ 反向**也要真算**（976 教训：注释写「保留旧字段」却删了计算
    #   ⇒ 读出来是 `None` 而不是 `False`）⇒ ⭐⭐ 两个关系都真算
    c[tag + "_body_follows_dom_first"] = bool(
        dom_first is not None
        and body_i and body_i[0] > 0
        and keys[body_i[0] - 1] == dom_first)
    return out_rows


for rep in range(1, REPS + 1):
    print(f"===== rep {rep} =====", flush=True)
    rec = {"rep": rep, "cells": []}
    out["runs"].append(rec)
    dump(out)

    page.goto(URL, wait_until="domcontentloaded", timeout=90000)
    page.wait_for_timeout(10000)
    page.set_viewport_size({"width": 1512, "height": 1200})
    page.wait_for_timeout(3000)
    n = page.locator('button[aria-label="音频"]').count()
    if n == 0:
        page.wait_for_timeout(8000)
        n = page.locator('button[aria-label="音频"]').count()
    c = {"ci": 0, "n_ready": n, "n_install": 0, "n_read": 0,
         "n_rail_stops": 0, "n_lead_cap_hit": False, "rows": []}
    rec["cells"].append(c)
    dump(out)
    if n == 0:
        c["skip_note"] = "左栏入口没出来 ⇒ 本格什么也没测"
        continue

    sp = ev(BLANK_JS)
    c["blank"] = sp
    if sp:
        guard_point(sp[0], sp[1])       # ⛔ 守卫在 `mouse.click` **之前**
        page.mouse.click(sp[0], sp[1])
        page.wait_for_timeout(BLANK_WAIT)

    # ── 臂 0：基线 ────────────────────────────────────────────────────
    walk(c)
    c["off_null_before"] = ev(OFF_NULL_JS)
    summarize(c, "before", c["rows"])
    c["rows"] = []
    c["n_install"] = c["n_read"] = c["n_rail_stops"] = c["n_lead"] = 0
    dump(out)

    # ── 臂 A：**连插两枚**可聚焦元素到 `<body>` 最前面（可还原）────────
    c["inject_a"] = ev(INJECT_JS, [ID_A])
    c["inject_b"] = ev(INJECT_JS, [ID_B])
    page.wait_for_timeout(400)
    # ⚠️⭐⭐ 第二次插会把 ID_B 放到**更前面** ⇒ 真实 DOM 顺序要**读出来**、
    #   不能按调用顺序假设
    c["inject_order"] = ev("""([a, b]) => {
        const ids = Array.prototype.slice.call(
            document.body.querySelectorAll('[id]'))
            .map(function (x) { return x.id; })
            .filter(function (x) { return (x === a) || (x === b); });
        return {front_ids: ids,
                first_child_now: (document.body.firstElementChild || {}).id || null};
    }""", [ID_A, ID_B])
    try:
        walk(c)
    finally:
        # ⭐⭐⭐ 诊断动作必须还原 —— `finally` 里**无条件**移除，**两枚都**
        c["uninject"] = [ev(UNINJECT_JS, [ID_A]), ev(UNINJECT_JS, [ID_B])]
    c["off_null_two"] = ev(OFF_NULL_JS)
    summarize(c, "two", c["rows"])
    c["rows"] = []
    c["n_install"] = c["n_read"] = c["n_rail_stops"] = c["n_lead"] = 0
    dump(out)

    # ── ⭐⭐⭐⭐⭐ 臂 B：**去掉第一个可聚焦元素的资格**（可还原）──────────
    c["unfocus"] = ev(UNFOCUS_JS)
    page.wait_for_timeout(400)
    try:
        walk(c)
    finally:
        # ⭐⭐ **无条件**还原；原值可能**本来就不存在** ⇒ 两条路都写全
        c["refocus"] = ev(REFOCUS_JS, [c["unfocus"]])
    c["off_null_unfocus"] = ev(OFF_NULL_JS)
    summarize(c, "unfocus", c["rows"])
    c["restored"] = (c.get("refocus") or {}).get("restored") is True
    c["uninjected"] = all((u or {}).get("removed") is True
                          for u in (c.get("uninject") or []))
    c["n_fired_total"] = sum(int(r.get("fired") or 0) for r in c["rows"])
    c["fired_eq_rows"] = (c["n_fired_total"] == len(c["rows"]))
    c["listener_balanced"] = (
        c["n_install"] == c["n_read"]
        and (c["off_null_two"] or {}).get("off_after_read") is True
        and (c["off_null_unfocus"] or {}).get("rec_cleared") is True)
    dump(out)

# ── ⭐⭐ 两轮比较**必须在 `for rep` 循环之外**（955 第一版栽在这上面）───
_c0 = out["runs"][0]["cells"][0]
_c1 = out["runs"][1]["cells"][0] if len(out["runs"]) > 1 else {}


def _both(fn):
    return bool(fn(_c0)) and bool(fn(_c1))


out["reps_agree"] = (
    _c0.get("before_n_body") == _c1.get("before_n_body")
    and _c0.get("two_n_body") == _c1.get("two_n_body")
    and _c0.get("unfocus_n_body") == _c1.get("unfocus_n_body"))

out["design_gates"] = {
    # ⭐ 前提：基线那一枚 `BODY` 在（否则后面全是空谈）
    "body_present_in_baseline_both_reps": _both(
        lambda c: c.get("before_n_body") == 1),
    # ⭐ 臂 A 的前提：**两枚都真进了环**
    "two_injections_actually_in_ring_both_reps": _both(
        lambda c: c.get("two_n_injected") == 2),
    # ⭐ 臂 B 的前提：那个改动**真的生效**（改完就不再可聚焦）
    "arm_b_mutation_took_effect_both_reps": _both(
        lambda c: (c.get("unfocus") or {}).get("found") is True
        and (c.get("unfocus") or {}).get("still_focusable") is False),
    # ⭐ 臂 B 的前提：还原**真的把资格还回去了**
    "arm_b_restored_both_reps": _both(
        lambda c: c.get("restored") is True
        and (c.get("refocus") or {}).get("focusable_now") is True),
    # ⭐ 干预件**无痕**
    "injections_restored_both_reps": _both(
        lambda c: c.get("uninjected") is True),
    # ⭐⭐ 三臂各自的读数**都拿到了**（不判真假，只判「测到了」）
    "h3_relation_measured_in_all_three_arms_both_reps": _both(
        lambda c: isinstance(c.get("before_body_precedes_dom_first"), bool)
        and isinstance(c.get("two_body_precedes_dom_first"), bool)
        and isinstance(c.get("unfocus_body_precedes_dom_first"), bool)),
    # ⭐⭐ 臂 B 之后「第一个可聚焦元素」**真的换人了** —— 否则臂 B 没打中靶子
    "arm_b_moved_the_dom_first_focusable_both_reps": _both(
        lambda c: isinstance(c.get("unfocus_dom_first_focusable"), str)
        and c.get("unfocus_dom_first_focusable")
        != c.get("before_dom_first_focusable")),
    "fired_eq_rows_both_reps": _both(lambda c: c.get("fired_eq_rows") is True),
    "listener_balanced_both_reps": _both(
        lambda c: c.get("listener_balanced") is True),
}

out["recon"] = {
    "rep%d" % i: {
        k: (c.get(k) if k.endswith(("_names", "_seats", "_gap")) is False else c.get(k))
        for k in ("before_n_body", "before_ring_len", "before_dom_first_focusable",
                  "before_body_next_key", "before_body_precedes_dom_first",
                  "two_n_body", "two_ring_len", "two_n_injected",
                  "two_dom_first_focusable", "two_body_next_key",
                  "two_body_precedes_dom_first",
                  "unfocus_n_body", "unfocus_ring_len",
                  "unfocus_dom_first_focusable", "unfocus_body_next_key",
                  "unfocus_body_precedes_dom_first",
                  "unfocus", "refocus", "inject_order", "restored", "uninjected")
    }
    for i, c in enumerate((_c0, _c1))
}

out["gate_notes"] = (
    "⭐ 977 的门围绕「**臂 B 有没有打中靶子**」与「**干预可还原**」：\n"
    "  · ⚠️⚠️ `arm_b_mutation_took_effect` / `arm_b_restored` / "
    "`arm_b_moved_the_dom_first_focusable` 三条是**整批的前提** —— "
    "臂 B 若没真的让「第一个可聚焦元素」换人，"
    "那 H₃ 的结论就是**打在空气上**；\n"
    "  · ⭐ `h3_relation_measured_in_all_three_arms` **刻意不判真假** —— "
    "探针只输出「紧贴 / 不紧贴」，**H₃ 的真伪由 verifier 判** ⇒ "
    "**不预写结论**；\n"
    "  · ⚠️ `two_injections_actually_in_ring` 提醒：臂 A **单独看分不开任何东西** "
    "—— 两种机制在两枚的情况下**预测完全一样** ⇒ 臂 A 的价值只是计数与座位。"
)

out["what_977_measures"] = (
    "① ⭐⭐⭐⭐⭐ **臂 B**（正面检验 H₃）：把 DOM 里第一个可聚焦元素临时设成 "
    "`tabindex=\"-1\"`（**纯 JS、可还原**、**先记原属性值**）⇒ "
    "「第一个可聚焦元素」换人 ⇒ 看 `BODY` 会不会**重新锚定**；\n"
    "  ② ⭐⭐⭐ **臂 A**（连插两枚）：给计数与座位，"
    "**但它单独看分不开任何东西**；\n"
    "  ③ ⭐⭐ 三臂各记 `body_precedes_dom_first`（**H₃ 的可判红命题**）"
    "与**反向** `body_follows_dom_first`（⭐⭐ 两个关系都真算，"
    "不然反向那道门读到的是 `None` 而不是 `False`）"
)

out["discipline_977"] = (
    "① ⭐⭐⭐⭐⭐ **一次成功不叫可靠** —— 976 那个支撑是**弱**的："
    "它只在开头那一段试过一次，而 H₃ 说的是「**恒**」；\n"
    "  ② ⭐⭐⭐ **实验有前提，前提要有门** —— "
    "臂 B 有没有**真的**让「第一个可聚焦元素」换人，"
    "是 H₃ 结论的**成立条件**，不是细节；\n"
    "  ③ ⭐⭐⭐⭐⭐ **观察分不开 ⇒ 改实验，不改次数** —— "
    "臂 A 是「再多测一次」，臂 B 才是「改实验」"
    "⇒ **两条臂都留着，但只有一条有判别力**；\n"
    "  ④ ⭐⭐⭐ **读数里撞名的字段不能当身份** —— 976 的 `INJECT_JS` 把 "
    "`data-testid` 写死 ⇒ 两枚撞名 ⇒ 本批用 `own.id`；\n"
    "  ⑤ ⭐⭐⭐ **干预必须可还原，且要单独复查** —— "
    "「清理代码跑过了」**不等于**「东西真的变回去了」；\n"
    "  ⑥ ⭐⭐ **两个关系都真算**（正向 + 反向）"
    "⇒ 注释写「保留旧字段」却删了计算，读出来是 `None` 不是 `False`；\n"
    "  ⑦ ⭐⭐ **守卫会命中自己 ⇒ 行首锚定**（976 踩过）；\n"
    "  ⑧ ⭐ **零计费**：按键只有 `Tab`，⛔ 守卫拦在 `mouse.click` 之前；\n"
    "  ⑨ ⚠️ **出处仍未标注** —— 就算这一批扛住了，也只是"
    "「这一次、这两个条件下」⇒ ⭐⭐ **实测如此 ≠ 规范如此**"
)

out["skip_note"] = (
    "⚠️ 臂 A 的两枚注入件与臂 B 改过属性的那一枚，"
    "都是**人眼看不见 / 看不出来**的改动 ⇒ 本批只回答"
    "「`BODY` 还在不在、还紧不紧贴」，"
    "**不回答「用户会看到什么」**。"
)

dump(out)
print("PROBE_977_DONE", out["reps_agree"], flush=True)
