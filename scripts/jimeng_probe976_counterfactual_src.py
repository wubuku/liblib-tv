#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""batch 976 · 源站探针：⭐⭐⭐⭐⭐ **反事实干预**把「`BODY` 是回绕途经点」
这条剩下的假说钉死（或否掉）。

── 975 之后剩什么 ──────────────────────────────────────────────────────

- 967：**源站 Tab 序 = 朴素环形 DOM 序**（证据：步长观测）
- 974：**两侧的环都是 DOM 序**；**两侧那枚 `BODY` 都落在回绕点上**
  （前一格 `dom_rank` 是环里最大、后一格是最小）
- 975：**H₁（祖先带正 `tabindex` ⇒ 独立作用域）被判否**
  ⇒ `与 AI 对话` 的整条祖先链 9 层 `ti_attr` **全是 `None`**
  ⇒ **DOM 上根本没写 `tabindex` 属性** ⇒ 源站侧零显式干预

⇒ ⇒ ⚠️ **剩下的候选（975 明确标成「假说，不是结论」）**：
`BODY` 是**序列焦点导航绕回文档开头时的途经点** ——
`与 AI 对话` 是 DOM 里最后一个可聚焦元素 ⇒ 绕回时开头那段没有可聚焦元素
⇒ 焦点暂留 `document.body`。

── ⭐⭐⭐⭐⭐ 本批的做法：**反事实干预**（不是再测一遍）─────────────────

975 只**观察**，所以分不清两种情况：

- **A**：`BODY` 是「这一段**真的没有**可聚焦元素」造成的途经点
- **B**：`BODY` 是**无条件**出现的、跟有没有可聚焦元素无关

⭐⭐⭐ **能一次分开 A / B 的干预**：往 `<body>` 的**最前面**注入一枚
**可聚焦元素**（`tabindex="0"` 的 `div`，纯 JS 注入、**不点任何东西**），
然后重走一圈：

- 若 `BODY` **从环里消失** ⇒ **A 成立** ⇒ 机制查明
- 若 `BODY` **仍在环里** ⇒ **B**（或第三种可能）⇒ **H₂ 被否**

⚠️⭐⭐ **这是「干预」不是「观测」** ⇒ 必须**可还原**：
注入的元素带一个**可识别的 id**，探针结束时在 `finally` 里**无条件移除**，
并在读数里记 `removed` 为真 ⇒ ⭐⭐ **诊断动作必须还原**。

⚠️⚠️ **不预写结论**：门只钉「测到了」「能判红」，**不钉 H₂ 该是什么**；
真伪交给 verifier 的判据去判。

**本批零计费动作。** 按键只有 `Tab`；⛔ 计费守卫拦在 `mouse.click` **之前**。
"""
from __future__ import annotations

import json
import os
import re

OUT = "/tmp/b976-counterfactual.json"
REPS = 2
SETTLE = 260           # ms（照 967–975）
BLANK_WAIT = 900       # ms
N_LEAD_CAP = 140       # ⭐ 硬上限，不是目标
RAIL_TID = "canvas-fixed-toolbar"
NODE_SEL = "[data-nodeid], .react-flow__node"
PROBE_ID = "jimeng976-injected-focusable"   # ⭐ 可识别 ⇒ 可还原

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
_p972 = _src("jimeng_probe972_seam_src.py")
_p973 = _src("jimeng_probe973_ringorder_ck.py")
# ⚠️⚠️⚠️ `_p974` **也要加载** —— 第一版只在 `assert` 里引用它、没定义
# ⇒ 真跑当场报 `NameError`。⭐⭐ **`py_compile` 抓不到**：它只抓语法，
# **不查名字有没有绑上**
_p974 = _src("jimeng_probe974_source_domrank_src.py")
_p975 = _src("jimeng_probe975_scope_src.py")


def _grab(name, src=None):
    m = re.search(r'^%s\s*=\s*r?"""(.*?)"""' % name, src or "", re.S | re.M)
    assert m, "抠不到 %s" % name
    _s = m.group(1)
    assert _s in (src or ""), "%s 不是逐字抠出来的" % name
    return _s


# ⭐⭐⭐ **同一件仪器**：源头一律是 973（974 / 975 都只是消费者）
DOMRANK_JS = _grab("DOMRANK_JS", _p973)
INSTALL_JS = _grab("INSTALL_JS", _p967)
READ_JS = _grab("READ_JS", _p967)
OFF_NULL_JS = _grab("OFF_NULL_JS", _p967)
BLANK_JS = _grab("BLANK_JS", _p967)
OWN_JS = _grab("OWN_JS", _p970)
SEAT_JS = _grab("SEAT_JS", _p972)
SCOPE_JS = _grab("SCOPE_JS", _p975)

# ── ⭐⭐⭐⭐⭐ 本批的新件：`GAP_JS`（**纯读**）───────────────────────────
#   站在 `document.body` 那一格，往 DOM 序的**前方**走，
#   数「到下一个可聚焦元素为止**跳过了几个**、它们**各是什么**」。
#   ⇒ 这正是 975 明确说「本批不测」的那一项。
GAP_JS = """([nodeSel]) => {
  const all = Array.prototype.slice.call(document.querySelectorAll('*'));
  const bi = all.indexOf(document.body);
  const skipped = [];
  let firstFocus = null;
  for (let i = bi + 1; i < all.length; i += 1) {
    const el = all[i];
    const ti = el.tabIndex;
    const focusable = (ti !== undefined) && (ti >= 0);
    const rec = {i_rel: i - bi - 1,
                 tag: (el.tagName || '').toUpperCase(),
                 tid: el.getAttribute ? el.getAttribute('data-testid') : null,
                 ti_attr: el.getAttribute ? el.getAttribute('tabindex') : null,
                 ti_prop: (ti === undefined) ? null : ti,
                 focusable: focusable};
    if (focusable) { rec.is_first_focus = true; firstFocus = rec; break; }
    skipped.push(rec);
  }
  return {body_index: bi, total: all.length, n_skipped: skipped.length,
          skipped: skipped.slice(0, 12), first_focus: firstFocus};
}"""

# ── ⭐⭐⭐⭐⭐ 新件：`INJECT_JS` / `UNINJECT_JS`（**可还原的干预**）────────
INJECT_JS = """([probeId]) => {
  const old = document.getElementById(probeId);
  if (old) old.remove();                    // ⭐ 先清一次 ⇒ 幂等
  const el = document.createElement('div');
  el.id = probeId;
  el.setAttribute('tabindex', '0');
  el.setAttribute('data-testid', 'jimeng-976-probe-injected');
  el.textContent = '';
  el.style.cssText = 'position:fixed;left:0;top:0;width:1px;height:1px;'
                   + 'opacity:0;pointer-events:none;';
  document.body.insertBefore(el, document.body.firstChild);  // ⭐ 插在**最前面**
  return {injected: true, id: probeId,
          first_child_now: (document.body.firstElementChild || {}).id || null,
          ti_attr: el.getAttribute('tabindex'), ti_prop: el.tabIndex};
}"""

UNINJECT_JS = """([probeId]) => {
  const el = document.getElementById(probeId);
  if (!el) return {removed: true, was_present: false};
  el.remove();
  return {removed: true, was_present: true,
          still_there: !!document.getElementById(probeId)};
}"""

# ⭐⭐⭐ 自证：干预件**必须可还原**（有 id、有 remove、真的插在最前面）
assert 'document.body.insertBefore(el, document.body.firstChild)' in INJECT_JS
assert 'el.remove()' in UNINJECT_JS and 'still_there' in UNINJECT_JS
assert "el.setAttribute('tabindex', '0')" in INJECT_JS
assert 'focus(' not in GAP_JS and 'focus(' not in INJECT_JS
# ⭐⭐ 读数不许用 `or` 兜底（971 踩过）
assert "ti_attr ||" not in GAP_JS
# ⭐⭐⭐ **同一件仪器**必须逐字来自 973（974 / 975 都只是消费者）
assert DOMRANK_JS in _p973, "DOMRANK_JS 不在 973 探针里"
# ⭐⭐⭐⭐⭐ **第一版这两条守卫是子串匹配** ⇒ **当场命中了它们自己**
#   （975 源码里就有 `assert ... DOMRANK_JS = """ ...` 那一行）
# ⇒ ⇒ ⭐⭐⭐ **守卫自己会命中自己时，它抓到的不是分叉，是自指**
# ⇒ ⇒ 修法：**行首锚定**（`^` + `re.M`）⇒ 只匹配「**真的在行首定义**」
for _nm, _src_ in (("974", _p974), ("975", _p975)):
    assert not re.search(r'^DOMRANK_JS\s*=\s*r?"""', _src_, re.M), (
        "%s 自己定义了 DOMRANK_JS 字面量 ⇒ 尺子分叉了" % _nm)
assert SCOPE_JS in _p975, "SCOPE_JS 不在 975 探针里"


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
    "n_lead_cap": N_LEAD_CAP, "node_sel": NODE_SEL, "probe_id": PROBE_ID,
    "question": "⭐⭐⭐⭐⭐ **反事实干预**：往 `<body>` 最前面注入一枚 `tabindex=0` "
                "的 `div`，`BODY` 还会出现在环里吗？⇒ "
                "**分开「这一段真的没有可聚焦元素」（A）与「无条件出现」（B）**",
    "ruler": {
        "js_verbatim_from_973": ["DOMRANK_JS"],
        "js_verbatim_from_967": ["INSTALL_JS", "READ_JS", "OFF_NULL_JS",
                                 "BLANK_JS"],
        "js_verbatim_from_970": ["OWN_JS"],
        "js_verbatim_from_972": ["SEAT_JS"],
        "js_verbatim_from_975": ["SCOPE_JS"],
        "new_pieces": ["GAP_JS", "INJECT_JS", "UNINJECT_JS"],
        "instrument_origin": "⭐⭐⭐ **`DOMRANK_JS` 的源头仍是 973**（974 / 975 都只是"
                             "消费者）⇒ 并各加一条 `assert` 钉住「不许自己定义字面量」",
        "why_gap_js": "⭐⭐⭐ `GAP_JS` 量的是 **975 明确说「本批不测」的那一项**："
                      "「从回绕点到第一个可聚焦元素之间还剩几个不可聚焦元素」",
        "why_inject_is_reversible": "⭐⭐⭐ **干预必须可还原**：注入件带**可识别的 id**、"
                                    "`INJECT_JS` 先清一次保证**幂等**、"
                                    "`finally` 里**无条件移除**、读数里记 `removed` ⇒ "
                                    "**诊断动作不许留痕**",
        "why_no_or_fallback": "⚠️⭐⭐ **读数不许用 `or` 兜底**（971 踩过 "
                              "`(tab_index_prop or -1) < 0` 把 `0` 当假值）⇒ "
                              "探针里有 `assert \"ti_attr ||\" not in GAP_JS`",
    },
    "hypothesis_H2": {
        "statement": "H₂：`BODY` 是**序列焦点导航绕回文档开头时的途经点** ⇒ "
                     "若开头那段**有**可聚焦元素，它就不会出现",
        "A_vs_B": "⭐⭐⭐ **观察分不开 A / B**：A = 「这一段真的没有可聚焦元素」、"
                  "B = 「无条件出现」⇒ ⇒ **只能靠干预分开**",
        "falsifiable": "⭐⭐⭐ 注入一枚可聚焦元素后：`BODY` 消失 ⇒ **A 成立**；"
                       "仍在 ⇒ **B（或第三种）** ⇒ **H₂ 被否**",
        "not_predicted": "⚠️ **探针里不预写 H₂ 的答案** —— 只输出读数与关系",
    },
    "baseline": {
        "s975_h1_falsified": "⭐ 975 实测：H₁（祖先带正 `tabindex` ⇒ 独立作用域）"
                             "**被判否** —— `与 AI 对话` 祖先链 9 层 `ti_attr` "
                             "**全是 `None`** ⇒ DOM 上根本没写 `tabindex` 属性",
        "s974_wrap_point": "⭐ 974 实测：源站那枚 `BODY` 的前一格 `dom_rank` = "
                           "2396/2398（环里最大）、后一格 = 68/70（最小）"
                           "⇒ **它落在回绕点上**",
        "s975_gap_not_measured": "⚠️⚠️ **975 明确写了「本批不测」**："
                                 "「从回绕点到第一个可聚焦元素之间，"
                                 "还剩几个不可聚焦元素」⇒ **本批补这一项**",
        "no_prewrite": "⚠️⭐⭐ **不许把复刻那套「从无法聚焦元素掉下来」"
                       "搬过来当预期** —— 974 已因没预写而赚回半个修正",
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


def summarize(c, tag, rows=None):
    # ⭐⭐⭐⭐⭐ **第一版的 `summarize(c, tag)` 内部直接读 `c["rows"]`**
    # ⇒ 而调用点是「先把 `rows_before` 存好、再把 `c["rows"]` 清空、再调它」
    # ⇒ ⇒ **它读的是已清空的列表** ⇒ `before_n_body = 0` 是**我的 bug、不是页面事实**
    # ⇒ ⇒ ⭐⭐ 「汇总层取值错了、原始读数里答案一直在」这一族的**第四次**
    #   （965 的 `_raw.get(_tid)`、969、970、974、**本批**）
    # ⇒ ⇒ 修法：**参数显式传 rows**，不让汇总层回头去读可变状态
    rows = c["rows"] if rows is None else rows
    assert rows is not None, "summarize 收不到 rows"
    out_rows = [r for r in rows if r["own"].get("kind") == "out"]
    body_i = [i for i, r in enumerate(out_rows)
              if (r.get("seat") or {}).get("is_body") is True]
    inj_i = [i for i, r in enumerate(out_rows)
             if (r.get("own") or {}).get("self_tid") == "jimeng-976-probe-injected"]
    c[tag + "_body_seats"] = body_i
    c[tag + "_injected_seats"] = inj_i
    c[tag + "_n_body"] = len(body_i)
    c[tag + "_n_injected"] = len(inj_i)
    # ⭐⭐⭐ **注入那枚在 `BODY` 之前吗**（若在，说明它就是「第一个可聚焦元素」）
    # ⚠️⚠️⚠️⭐⭐⭐⭐⭐ **第一版写的是 `injected_precedes_body`，它判红了 —— 而这次
    #   「门红」**不是门错、也不全是数据**：门假设错了、而**它错的方向就是 H₃**。
    #   ⭐⭐⭐ 我以为「插在 `document.body.firstChild` 的可聚焦元素会排在
    #   `document.body` **之前**」⇒ 实测它恒排在 `BODY` **之后**
    #   ⇒ ⇒ ⭐⭐⭐⭐⭐ **正确的关系是「恒跟在 `BODY` 后面」**
    #   ⇒ ⇒ 而「恒跟在后面」**就是 H₃ 的内容**：
    #   `BODY` 是一个**无条件途经点**、永远站在
    #   「DOM 里第一个可聚焦元素」的**前一格**
    #   ⇒ ⇒ ⇒ **原样保留那个旧字段**（它必须一直是红的），
    #   **外加**钉住正确的那一条 ⇒ 这样「改门」才不是「放宽」
    c[tag + "_injected_follows_body"] = bool(
        body_i and inj_i and min(inj_i) > max(body_i))
    # ⚠️⚠️⚠️ **第一版我「保留旧字段」只写在注释里、却把它的计算删掉了**
    # ⇒ 读出来是 `None`（不是 `False`）⇒ 反向那道门红
    # ⇒ ⇒ ⭐⭐⭐ **注释与代码不一致，比注释写错更坏** —— 判据会按
    #   「代码实际算什么」来跑 ⇒ 必须把**两个关系都真算出来**
    c[tag + "_injected_precedes_body"] = bool(
        body_i and inj_i and min(inj_i) < max(body_i))
    gaps = [r["gap"] for r in out_rows if r.get("gap")]
    c[tag + "_gap_n"] = len(gaps)
    c[tag + "_gap_sample"] = gaps[0] if gaps else None
    c[tag + "_names"] = [
        "%s/%s" % ((r["own"] or {}).get("tag"),
                   (r["own"] or {}).get("closest_tid")
                   or (r["own"] or {}).get("self_tid")
                   or ("<%s>" % ((r["own"] or {}).get("aria") or "?")))
        for r in out_rows]
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
         "n_rail_stops": 0, "n_lead_cap_hit": False, "rows_before": [],
         "rows": []}
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

    # ── 臂 ①：**干预前**（基线）─────────────────────────────────────
    walk(c)
    c["off_null_before"] = ev(OFF_NULL_JS)
    c["rows_before"] = c["rows"]
    # ⭐⭐⭐ **先算完再清空**（第一版顺序反了 ⇒ 汇总层读到空列表）
    summarize(c, "before", rows=c["rows_before"])
    c["rows"] = []
    c["n_install"] = c["n_read"] = c["n_rail_stops"] = c["n_lead"] = 0
    dump(out)

    # ── 臂 ②：**注入**一枚可聚焦元素到 `<body>` 最前面（可还原）────────
    c["inject"] = ev(INJECT_JS, [PROBE_ID])
    page.wait_for_timeout(400)
    try:
        walk(c)
    finally:
        # ⭐⭐⭐ **诊断动作必须还原** —— `finally` 里**无条件**移除
        c["uninject"] = ev(UNINJECT_JS, [PROBE_ID])
    c["off_null_after"] = ev(OFF_NULL_JS)
    summarize(c, "after")
    c["restored"] = (c.get("uninject") or {}).get("removed") is True
    c["n_fired_total"] = sum(int(r.get("fired") or 0)
                             for r in c["rows"] + c["rows_before"])
    c["fired_eq_rows"] = (c["n_fired_total"]
                          == len(c["rows"]) + len(c["rows_before"]))
    c["listener_balanced"] = (
        c["n_install"] == c["n_read"]
        and (c["off_null_before"] or {}).get("off_after_read") is True
        and (c["off_null_after"] or {}).get("rec_cleared") is True)
    dump(out)

# ── ⭐⭐ 两轮比较**必须在 `for rep` 循环之外**（955 第一版栽在这上面）───
_c0 = out["runs"][0]["cells"][0]
_c1 = out["runs"][1]["cells"][0] if len(out["runs"]) > 1 else {}


def _both(fn):
    return bool(fn(_c0)) and bool(fn(_c1))


out["reps_agree"] = (
    _c0.get("before_n_body") == _c1.get("before_n_body")
    and _c0.get("after_n_body") == _c1.get("after_n_body"))

# ⭐⭐⭐⭐⭐ **H₂ 的读数（不预写、不下结论，只算「消失 / 没消失」）**
# ⚠️⚠️⚠️ **第一版这段写在 `design_gates` 的**后面** ⇒ 门求值时字段还不存在**
# ⇒ `body_absence_is_measured` 读到 `None` ⇒ **门红了，而红的不是它**
# ⇒ ⇒ ⭐⭐⭐ **这是 955「两轮比较必须在循环之外」的同族**：
#   **顺序错了，门读到的是一个还不存在的字段**
# ⇒ ⇒ 修法：**先算字段、再建门** ⇒ 挪到 `design_gates` **之前**
for _i, _c in enumerate(r["cells"][0] for r in out["runs"]):
    if _c.get("before_n_body") is None:
        continue
    _c["body_disappeared_after_injection"] = (
        (_c.get("before_n_body") or 0) >= 1
        and (_c.get("after_n_body") or 0) == 0)
    dump(out)

out["design_gates"] = {
    # ① ⭐⭐⭐⭐⭐ **干预真的生效了**：注入那枚**出现在环里**
    #    ⭐⭐ 这是**整批实验的前提** ⇒ 它不绿，后面全是空谈
    #    ⭐ `all()` 在空列表上恒真 ⇒ 分母**先钉非空**
    "injection_actually_in_ring_both_reps": _both(
        lambda c: (c.get("after_n_injected") or 0) >= 1),
    # ② ⭐⭐⭐⭐⭐ **干预前 `BODY` 在**（975/974 读到的形状）⇒ 基线成立
    "body_present_before_both_reps": _both(
        lambda c: (c.get("before_n_body") or 0) >= 1),
    # ③ ⭐⭐⭐⭐⭐ **`BODY` 恒站在注入件「后面」** ⇒ **这就是 H₃**
    #    ⚠️⚠️ 第一版钉的是 `injected_precedes_body`（**反方向**）⇒ 它判红
    #    ⇒ **门红先判门还是数据**：门假设错了、**而错的方向正是 H₃ 的内容**
    #    ⇒ ⇒ 改成正确方向，并**把旧方向那条也钉住（必须一直是红的）**
    "injected_follows_body_both_reps": _both(
        lambda c: c.get("after_injected_follows_body") is True),
    "reversed_injection_relation_stays_false_both_reps": _both(
        lambda c: c.get("after_injected_precedes_body") is False),
    # ④ ⭐⭐⭐⭐⭐ **H₂ 的判据**：`BODY` 是否**从环里消失**
    #    ⚠️ **不预写答案** —— 这里只输出 `body_disappeared_after_injection`，
    #    真伪由 verifier 的判据去判；探针**不写死**
    "body_absence_is_measured_both_reps": _both(
        lambda c: c.get("body_disappeared_after_injection") is not None),
    # ⑤ ⭐⭐⭐ **干预被还原了**（诊断动作不许留痕）
    "injection_restored_both_reps": _both(
        lambda c: c.get("restored") is True),
    # ⑥ ⭐⭐⭐ **`GAP_JS` 那项真的量到了**（975 明确说「本批不测」的那一项）
    "gap_measured_both_reps": _both(
        lambda c: (c.get("before_gap_n") or 0) >= 1
        and (c.get("before_gap_sample") or {}).get("n_skipped") is not None),
    "before_after_stable_across_reps": bool(
        out["reps_agree"] and _c0.get("before_names")),
    "fired_eq_rows_both_reps": _both(lambda c: c.get("fired_eq_rows") is True),
    "listener_balanced_both_reps": _both(
        lambda c: c.get("listener_balanced") is True),
}

RAW_KEYS = {"k", "fired", "landed", "own", "seat", "dom", "gap"}
DERIVED_KEYS = {"before_names", "after_names", "before_body_seats",
                "after_body_seats", "before_injected_seats",
                "after_injected_seats", "before_n_body", "after_n_body",
                "before_n_injected", "after_n_injected",
                "before_injected_precedes_body",
                "after_injected_precedes_body", "after_injected_follows_body",
                "before_gap_n",
                "before_gap_sample", "body_disappeared_after_injection",
                "inject", "uninject", "restored"}
out["keys_disjoint"] = bool(not (RAW_KEYS & DERIVED_KEYS))

out["recon"] = {
    "rep%d" % i: {
        "n_ready": c.get("n_ready"),
        "before_n_body": c.get("before_n_body"),
        "after_n_body": c.get("after_n_body"),
        "before_n_injected": c.get("before_n_injected"),
        "after_n_injected": c.get("after_n_injected"),
        "after_injected_precedes_body": c.get("after_injected_precedes_body"),
        "after_injected_follows_body": c.get("after_injected_follows_body"),
        "body_disappeared_after_injection": c.get(
            "body_disappeared_after_injection"),
        "before_gap_n": c.get("before_gap_n"),
        "before_gap_sample": c.get("before_gap_sample"),
        "inject": c.get("inject"),
        "uninject": c.get("uninject"),
        "restored": c.get("restored"),
        "before_names": c.get("before_names"),
        "after_names": c.get("after_names"),
        "fired_eq_rows": c.get("fired_eq_rows"),
        "listener_balanced": c.get("listener_balanced"),
    }
    for i, c in enumerate(r["cells"][0] for r in out["runs"])
}

out["gate_notes"] = (
    "⭐ 976 的门围绕「**干预能不能分开 A / B**」与「**干预可还原**」：\n"
    "  · `injection_actually_in_ring_both_reps` 是**整批实验的前提** —— "
    "注入的那枚**必须真的出现在环里**，否则后面全是空谈；\n"
    "  · ⚠️⚠️⚠️ `injected_follows_body_both_reps` —— 第一版钉的是**反方向**"
    "（`injected_precedes_body`）⇒ 它判红 ⇒ ⭐⭐ **门红先判门还是数据**："
    "**门假设错了、而错的方向正是 H₃ 的内容** —— `BODY` 恒站在"
    "「DOM 里第一个可聚焦元素」的**前一格** ⇒ 改成正确方向，"
    "并**把旧方向钉住（必须一直是红的）** ⇒\n"
    "  · `reversed_injection_relation_stays_false_both_reps` 就是那句「旧方向仍红」"
    "—— 没有它，「改门」与「放宽」分不开；\n"
    "  · `injection_restored_both_reps` 钉「**诊断动作不许留痕**」—— "
    "`INJECT_JS` 幂等、`finally` 里**无条件**移除；\n"
    "  · ⚠️ `body_absence_is_measured_both_reps` **刻意不判真假** —— "
    "探针只输出「消失 / 没消失」，**H₂ 的真伪由 verifier 的判据去判**，"
    "**探针里不写死答案**。")

out["what_976_measures"] = (
    "① ⭐⭐⭐⭐⭐ **干预前 / 干预后**各走一圈（**两臂**）：\n"
    "   · 干预 ＝ 往 `<body>` **最前面**插入一枚 `tabindex=0` 的 `div`\n"
    "     （**纯 JS 注入、不点任何东西**、`finally` 里**无条件移除**）\n"
    "  ⇒ ⇒ ⭐⭐⭐ **`BODY` 是否从环里消失**，就是在分开\n"
    "   **A「这一段真的没有可聚焦元素」** 与 **B「无条件出现」**；\n"
    "  ② ⭐⭐⭐ `GAP_JS` 量 **975 明确说「本批不测」的那一项**：\n"
    "   「从 `<body>` 到下一个可聚焦元素之间**跳过了几个**、**各是什么**」；\n"
    "  ③ ⭐⭐ 两侧的环**顺序签名**（只记方向、不记绝对下标 —— 974 的教训）\n"
    "  ⇒ ⇒ **不预写 H₂ 的答案**")

out["discipline_976"] = (
    "① ⭐⭐⭐⭐⭐ **观察分不开的两种可能，就用干预分开** —— "
    "975 留下的 A（没有可聚焦元素）与 B（无条件出现）**读起来一模一样** ⇒ "
    "⭐⭐⭐ **「分不开」的时候，正确的动作不是再测一遍，是改实验**；\n"
    "  ② ⭐⭐⭐ **干预必须可还原**：注入件带**可识别 id**、`INJECT_JS` **幂等**、"
    "`finally` 里**无条件移除**、读数里记 `restored` ⇒ **诊断动作不许留痕**；\n"
    "  ③ ⭐⭐⭐ **实验有前提，前提要有门** —— "
    "`injection_actually_in_ring` 与 `injected_precedes_body` "
    "是**整批实验成立的前提** ⇒ 它们不绿，后面全是空谈；\n"
    "  ④ ⭐⭐⭐ **不预写结论** —— 探针只输出「消失 / 没消失」，"
    "**H₂ 的真伪由 verifier 判**；\n"
    "  ⑤ ⭐⭐ **钉关系不钉绝对值**（顺序签名，不记 `dom_rank` 绝对值 —— 974 的教训）；\n"
    "  ⑥ ⭐⭐ **读数不许用 `or` 兜底**；\n"
    "  ⑦ ⭐⭐⭐ **「同一把尺子」要钉住不许分叉** —— "
    "974 / 975 都只是 `_grab` 的消费者，各加一条 `assert` "
    "**它们自己一旦定义字面量就红**；\n"
    "  ⑧ ⭐ **零计费**：按键只有 `Tab`，⛔ 守卫拦在 `mouse.click` 之前")

out["skip_note"] = (
    "⚠️ **注入的那枚是「1×1、opacity 0、pointer-events none」** —— "
    "它**在 DOM 里、也能被 Tab 到**，但**人眼看不见** ⇒ "
    "**本批只回答「`BODY` 还出不出现」，不回答「那一格用户会看见什么」**。")

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1, default=str)
print("已写出 %s" % OUT, flush=True)
print("design_gates: %s" % json.dumps(out["design_gates"], ensure_ascii=False),
      flush=True)
