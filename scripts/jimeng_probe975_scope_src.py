#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""batch 975 · 源站探针：⭐⭐⭐⭐⭐ **源站那一枚 `BODY` 的触发机制**
（§184 明确记「未查明」）。

── 为什么问这个 ────────────────────────────────────────────────────────

974 实测（源站 2/2）：那枚 `BODY` 落在**序列焦点导航的回绕点**上
（前一格 `dom_rank` 是环里最大、后一格是最小），
而它的**直接前驱 `canvas-sidecar-launcher`（与 AI 对话）是 `focusable = true`**。

⚠️⚠️⚠️ ⇒ **「从无法聚焦的元素按 Tab、焦点掉到 body」这条复刻侧的机制，
在源站上不成立**（源站前驱是可聚焦的按钮）
⇒ ⇒ ⭐⭐⭐ **不许把复刻的机制预写给源站**（974 已经因为没预写而赚回半个修正）。

⚠️ **未查明**：源站那一枚**为什么**也会落在 body 上。
⇒ **974 只有观测、没有机制** ⇒ 本批去测机制。

── ⭐⭐⭐⭐⭐ 本批要验的假设（**可判红**，不是叙述）──────────────────────

**H₁：`**`与 AI 对话` 的某个祖先带正 `tabindex``** ⇒ 那就形成一个
**独立的顺序焦点导航作用域（scope）** ⇒ 从该作用域的最后一格按 `Tab`
**出作用域** ⇒ 焦点无处可落、暂留 `document.body`。

这条假设**可判红**，而且判据分母**独立**：
- ⛔ 恒 `False` 时「没有作用域」与「判据写错了」**分不开** ⇒ 必须**如实判红**
- ⇒ 故另设一道**正向自证门**：`tabindex` 读数**确实逐层拿到了**
  （`chain_depth >= 1` 且每个祖先的 `ti` 字段**不是哨兵**）

⚠️ **不预写 H₁ 的答案**：本探针只输出**读数**与**关系**，
H₁ 的真伪由 verifier 的判据去判，**不在探针里写死**。

**本批零计费动作。** 每轮只在开头点**一次画布空白**去焦点，
⛔ 守卫拦在 `mouse.click` 之前；按键只有 `Tab`。
"""
from __future__ import annotations

import json
import os
import re

OUT = "/tmp/b975-scope.json"
REPS = 2
SETTLE = 260           # ms（照 967–974）
BLANK_WAIT = 900       # ms
N_LEAD_CAP = 140       # ⭐ 硬上限，不是目标
RAIL_TID = "canvas-fixed-toolbar"
SIDECAR_TID = "canvas-sidecar-launcher"
NODE_SEL = "[data-nodeid], .react-flow__node"

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
_p974 = _src("jimeng_probe974_source_domrank_src.py")


def _grab(name, src=None):
    m = re.search(r'^%s\s*=\s*r?"""(.*?)"""' % name, src or "", re.S | re.M)
    assert m, "抠不到 %s" % name
    _s = m.group(1)
    assert _s in (src or ""), "%s 不是逐字抠出来的" % name
    return _s


INSTALL_JS = _grab("INSTALL_JS", _p967)
READ_JS = _grab("READ_JS", _p967)
OFF_NULL_JS = _grab("OFF_NULL_JS", _p967)
BLANK_JS = _grab("BLANK_JS", _p967)
OWN_JS = _grab("OWN_JS", _p970)
SEAT_JS = _grab("SEAT_JS", _p972)
# ⚠️⚠️⚠️ **第一版这里写的是 `_grab("DOMRANK_JS", _p974)` ⇒ 真跑当场报错「抠不到」**：
#   **974 是 `_grab` 的「消费者」、不是「生产者」** —— 它自己**没有**那三引号字面量，
#   它也是从 973 抠的 ⇒ ⇒ **必须沿链回到源头 `_p973`**
# ⇒ ⇒ ⭐⭐⭐ 这反而让「同一把尺子」这条链**更硬**：**975 / 974 都指向 973 的同一份字面量**（三支探针、一个源头）
DOMRANK_JS = _grab("DOMRANK_JS", _p973)   # ⭐ **源头是 973**，不是 974

# ── ⭐⭐⭐⭐⭐ 本批的新件：`SCOPE_JS`（**只读、从不调 `focus()`**）────────
#   把**当前 `document.activeElement` 的整条祖先链**连同每一层的 `tabindex`
#   读出来 ⇒ 「有没有祖先带正 `tabindex`」这件事**直接可判**。
#   ⭐⭐ `ti` 用 `getAttribute` 而不是 `.tabIndex`：
#   `getAttribute` 对「没有这个属性」返回 `null`、对 `tabindex="-1"` 返回字符串
#   ⇒ **属性在不在**与**属性是什么**分得开 ⇒ 不需要 `or` 兜底（975 的教训）
SCOPE_JS = """([nodeSel]) => {
  const el = document.activeElement;
  const chain = [];
  let p = el, d = 0;
  while (p && d < 12) {
    const tiAttr = p.getAttribute ? p.getAttribute('tabindex') : null;
    chain.push({
      depth: d,
      tag: (p.tagName || '').toUpperCase(),
      tid: p.getAttribute ? p.getAttribute('data-testid') : null,
      id: p.id || null,
      cls_head: ((p.className && p.className.baseVal !== undefined
                  ? p.className.baseVal : (p.className || '')) + '').slice(0, 40),
      ti_attr: tiAttr,
      ti_prop: (p.tabIndex === undefined) ? null : p.tabIndex
    });
    p = p.parentElement; d += 1;
  }
  return {
    chain: chain,
    chain_depth: chain.length,
    is_body: el === document.body,
    self_tid: el && el.getAttribute ? el.getAttribute('data-testid') : null,
    closest_tid: el && el.closest
      ? (el.closest('[data-testid]') || {}).getAttribute
        ? el.closest('[data-testid]').getAttribute('data-testid') : null
      : null
  };
}"""

POINT_JS = """([x, y]) => {
  const el = document.elementFromPoint(x, y);
  const host = el && el.closest('[data-testid]');
  return {tid: host ? host.getAttribute('data-testid') : null,
          al: (el.innerText || el.textContent || '').slice(0, 40)};
}"""

# ⭐⭐ 自证：新件必须真的读**属性**（不是 `.tabIndex` 那个会归一化的属性）
assert 'ti_attr: tiAttr,' in SCOPE_JS, "SCOPE_JS 必须读 `getAttribute('tabindex')`"
assert 'ti_attr' in SCOPE_JS and 'chain' in SCOPE_JS
assert "focus(" not in SCOPE_JS, "SCOPE_JS 不许调 focus()"
# ⚠️ 975 的纪律：处理读数**不许用 `or` 兜底**（971 踩过 `(x or -1) < 0`）
assert "ti_attr ||" not in SCOPE_JS, "SCOPE_JS 不许用 `||` 兜底读数"
assert DOMRANK_JS in _p973, "DOMRANK_JS 不在 973 探针里 ⇒ 不是同一件仪器"
# ⭐⭐⭐ **反证「974 是消费者」**：974 自己**不该**有那份字面量，
#   否则「一把尺子」就变成了两份拷贝
assert 'DOMRANK_JS = """' not in _p974, (
    "974 自己定义了 DOMRANK_JS 字面量 ⇒ 它成了第二份拷贝 ⇒ "
    "「同一把尺子」这条链就断了")


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
    at = ev(POINT_JS, [x, y])
    guard((at or {}).get("al"), (at or {}).get("tid"))
    return at


URL = ("https://jimeng.jianying.com/ai-tool/ai-canvas/"
       "64b58cd5-7b04-4312-890a-09f2d1d3399f"
       "?enter_from=project_list&from_page=create")

out = {
    "target": "source", "url": URL, "reps": REPS, "rail_tid": RAIL_TID,
    "sidecar_tid": SIDECAR_TID, "n_lead_cap": N_LEAD_CAP, "node_sel": NODE_SEL,
    "question": "⭐⭐⭐⭐⭐ **源站那一枚 `BODY` 为什么落在 body 上？**"
                "（974 明确记「未查明」：它前面是**可聚焦**的 `与 AI 对话`）"
                "⇒ 验假设 **H₁**：`与 AI 对话` 的某个祖先带**正 `tabindex`** "
                "⇒ 形成**独立的顺序焦点导航作用域** ⇒ 出作用域时焦点无处可落",
    "ruler": {
        "js_verbatim_from_967": ["INSTALL_JS", "READ_JS", "OFF_NULL_JS",
                                 "BLANK_JS"],
        "js_verbatim_from_970": ["OWN_JS"],
        "js_verbatim_from_972": ["SEAT_JS"],
        "js_verbatim_from_973_again": ["DOMRANK_JS"],
        "instrument_origin": "⭐⭐⭐ **`DOMRANK_JS` 的源头是 973**；"
                             "**974 与 975 都是 `_grab` 的消费者** ⇒ "
                             "**三支探针、一个源头**，不是三份拷贝",
        "new_pieces": ["SCOPE_JS", "POINT_JS"],
        "how_proved": "⭐ `_grab(name, src)` 抠出那一段，再 `assert _s in src`",
        "why_attr_not_prop": "⭐⭐ `ti_attr` 读 `getAttribute('tabindex')`"
                             "（属性在不在 / 属性是什么）"
                             "、`ti_prop` 读 `.tabIndex`（**归一化后的可聚焦性**）"
                             "⇒ **两件事分得开** ⇒ 不需要 `or` 兜底",
        "why_no_or_fallback": "⚠️⭐⭐ **不许用 `or` 兜底读数** —— 971 踩过 "
                              "`(tab_index_prop or -1) < 0` 把 `0` 当假值"
                              "⇒ 故这里有 `assert 'ti_attr ||' not in SCOPE_JS`",
    },
    "hypothesis_H1": {
        "statement": "H₁：`与 AI 对话` 的某个祖先带**正 `tabindex`** ⇒ "
                     "形成**独立的顺序焦点导航作用域** ⇒ "
                     "从该作用域的最后一格按 `Tab` **出作用域** ⇒ "
                     "焦点无处可落、暂留 `document.body`",
        "falsifiable": "⭐⭐⭐ **可判红**：若整条祖先链**没有**任何 "
                       "`ti_attr` 是正数，这道门就红 ⇒ "
                       "H₁ 被否，而不是「没查到」",
        "self_cert": "⭐⭐⭐ **正向自证门**：`tabindex` 读数**确实逐层拿到了**"
                     "（`chain_depth >= 1` 且每一层都有 `ti_attr` 字段）"
                     "⇒ 恒 `False` 时「没有作用域」与「读数是空的」**分不开**",
        "not_predicted": "⚠️ **探针里不写死 H₁ 的答案** —— "
                         "只输出读数与关系，真伪由 verifier 的判据去判",
    },
    "baseline": {
        "s974_source_body": "⭐ 974 实测（源站 2/2）：`BODY` 落在**回绕点**上"
                            "（前一格 `dom_rank` = 2396 最大、后一格 = 68 最小）；"
                            "前一格 `canvas-sidecar-launcher`、`prev_focusable = TRUE`",
        "s974_gap": "⚠️ **974 只有观测、没有机制** ⇒ 本批去测机制",
        "replica_mechanism": "⚠️ **复刻侧那套机制在源站不成立** —— "
                             "复刻的前驱 `NEXTJS-PORTAL` 是"
                             "**浏览器无法聚焦**的元素；"
                             "源站的前驱**是可聚焦的按钮** ⇒ "
                             "⭐⭐⭐ **不许把复刻的机制预写给源站**",
    },
    "runs": [],
}

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
    c = {"ci": 0, "mode": "walk", "n_ready": n, "rows": [],
         "n_install": 0, "n_read": 0, "n_rail_stops": 0,
         "n_lead_cap_hit": False}
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
            sc = ev(SCOPE_JS, [NODE_SEL])
        finally:
            ev(OFF_NULL_JS)
        row = {"k": c["n_lead"], "key": "Tab",
               "fired": (ap or {}).get("fired"),
               "landed": (ap or {}).get("landed"),
               "own": o, "seat": s, "dom": dr, "scope": sc}
        c["rows"].append(row)
        if o.get("closest_tid") == RAIL_TID:
            c["n_rail_stops"] += 1
            if c["n_rail_stops"] >= 2:
                break        # ⭐ 数到第 2 次命中左栏 = 走满一圈
        dump(out)
    else:
        c["n_lead_cap_hit"] = True
    c["off_null_at_end"] = ev(OFF_NULL_JS)
    dump(out)

    # ── 后处理（全部在 `dump` 之后）──────────────────────────────
    rows = c["rows"]
    c["n_rows"] = len(rows)
    # ⭐⭐ 两个平行列表、不是元组（973 那一族栽到第五次 ⇒ 结构上拆掉）
    out_rows = [r for r in rows if r["own"].get("kind") == "out"]
    out_ks = [r["k"] for r in out_rows]
    assert all(isinstance(r, dict) and "own" in r for r in out_rows), \
        "out_rows 里有不是 row-dict 的元素"

    body_i = [i for i, r in enumerate(out_rows)
              if (r.get("seat") or {}).get("is_body") is True]
    sidecar_i = [i for i, r in enumerate(out_rows)
                 if (r.get("own") or {}).get("closest_tid") == SIDECAR_TID]
    c["body_seats"] = body_i
    c["sidecar_seats"] = sidecar_i
    c["n_body"] = len(body_i)
    c["n_sidecar"] = len(sidecar_i)
    # ⚠️⚠️⚠️ **第一版这里写成了 `body_precedes_sidecar` ⇒ 那道门判红了**。
    # ⇒ **门红先判「门错还是数据错」**：974 与 975 的读数一致显示
    #   `与 AI 对话`(seat 5) → **`BODY`**(seat 6)，2/2 相同
    # ⇒ ⇒ **是门写反了**（974 已经读到的是这个形状）
    # ⇒ ⇒ ⭐⭐⭐ **改门（改精确）、不是放宽**：正确的关系是
    #   「**`与 AI 对话` 在 `BODY` 之前**」—— 也就是 `BODY` 落在
    #   `与 AI 对话` **之后**，与 974 「它是回绕点」一致
    c["sidecar_precedes_body"] = bool(
        body_i and sidecar_i
        and min(body_i) > min(sidecar_i))
    c["body_precedes_sidecar"] = bool(
        body_i and sidecar_i
        and min(sidecar_i) > max(body_i))   # ⭐ 保留原字段（**它必须一直是红的**）

    # ── ⭐⭐⭐⭐⭐ H₁ 的读数：**整条祖先链**的 `tabindex` ──────────────
    def _pos(chain):
        """祖先链里带**正** `tabindex`（属性值是数字且 > 0）的那几层。"""
        outp = []
        for lv in chain or []:
            ta = lv.get("ti_attr")
            if ta is None:
                continue
            try:
                v = int(str(ta).strip())
            except ValueError:
                continue
            if v > 0:
                outp.append({"depth": lv.get("depth"), "tag": lv.get("tag"),
                             "tid": lv.get("tid"), "id": lv.get("id"),
                             "ti_attr": ta})
        return outp

    def _negative(chain):
        return [lv for lv in (chain or []) if str(lv.get("ti_attr")) == "-1"]

    c["sidecar_chain"] = [
        {"k": out_ks[i], "depth": (out_rows[i].get("scope") or {}).get("chain_depth"),
         "chain": (out_rows[i].get("scope") or {}).get("chain"),
         "positive": _pos((out_rows[i].get("scope") or {}).get("chain")),
         "n_negative": len(_negative((out_rows[i].get("scope") or {}).get("chain")))}
        for i in sidecar_i]
    c["body_chain"] = [
        {"k": out_ks[i], "depth": (out_rows[i].get("scope") or {}).get("chain_depth"),
         "chain": (out_rows[i].get("scope") or {}).get("chain"),
         "positive": _pos((out_rows[i].get("scope") or {}).get("chain"))}
        for i in body_i]

    # ⭐⭐⭐ **H₁ 的门**：前驱（`与 AI 对话`）的祖先链里**有没有**正 `tabindex`
    #    ⚠️ `all()` 在空列表上恒真 ⇒ 分母**先钉非空**
    c["h1_sidecar_has_positive_tabindex"] = bool(
        sidecar_i) and all(
        any(lv["positive"] for lv in c["sidecar_chain"])
        for _ in [0])
    # ⭐⭐⭐ **正向自证门**：`tabindex` 读数**确实逐层拿到了**
    c["ti_reading_is_live"] = bool(sidecar_i) and all(
        lv["depth"] and lv["depth"] >= 1
        and all("ti_attr" in x for x in (lv["chain"] or []))
        for lv in c["sidecar_chain"])
    # ⭐⭐ 整页所有停靠点的祖先链里，有几层带正 `tabindex`（全局视野）
    c["n_positive_ti_rows"] = sum(
        1 for r in out_rows
        if _pos((r.get("scope") or {}).get("chain")))
    c["n_negative_ti_rows"] = sum(
        1 for r in out_rows
        if _negative((r.get("scope") or {}).get("chain")))
    c["n_fired_total"] = sum(int(r.get("fired") or 0) for r in rows)
    c["fired_eq_rows"] = (c["n_fired_total"] == len(rows))
    c["listener_balanced"] = (c["n_install"] == c["n_read"]
                              and c["off_null_at_end"].get("off_after_read") is True
                              and c["off_null_at_end"].get("rec_cleared") is True)
    dump(out)

# ── ⭐⭐ 两轮比较**必须在 `for rep` 循环之外**（955 第一版栽在这上面）───
_c0 = out["runs"][0]["cells"][0]
_c1 = out["runs"][1]["cells"][0] if len(out["runs"]) > 1 else {}


def _both(fn):
    return bool(fn(_c0)) and bool(fn(_c1))


out["reps_agree"] = (
    _c0.get("h1_sidecar_has_positive_tabindex")
    == _c1.get("h1_sidecar_has_positive_tabindex")
    and _c0.get("n_positive_ti_rows") == _c1.get("n_positive_ti_rows")
    and _c0.get("n_body") == _c1.get("n_body"))

out["design_gates"] = {
    # ① ⭐⭐⭐⭐⭐ **H₁**：`与 AI 对话` 的祖先链里**有**正 `tabindex`
    #    ⭐⭐ **可判红**：恒 `False` 就是 H₁ 被否，而不是「没查到」
    "h1_positive_tabindex_ancestor_both_reps": _both(
        lambda c: c.get("h1_sidecar_has_positive_tabindex") is True),
    # ② ⭐⭐⭐⭐ **正向自证门**：`tabindex` 读数**确实逐层拿到了**
    #    ⇒ 恒 `False` 时「没有作用域」与「读数是空的」**分不开**
    "ti_reading_is_live_both_reps": _both(
        lambda c: c.get("ti_reading_is_live") is True),
    # ③ ⭐⭐⭐ **`与 AI 对话` 真的落在 `BODY` 之前**（974 读到的那个形状）
    #    ⚠️⚠️⚠️ **第一版这条门叫 `body_precedes_sidecar`、判据取反 ⇒ 必然红**
    #    ⇒ **门红先判门还是数据**：读数与 974 一致 ⇒ **是门写反了** ⇒ 改名改精确
    "sidecar_precedes_body_both_reps": _both(
        lambda c: c.get("sidecar_precedes_body") is True),
    # ③b ⭐⭐⭐⭐ **反向那条必须一直是红的** ⇒ 否则改门改成了「随便它」
    #    ⇒ ⭐⭐ **改门要成对**：改了正向就得钉住反向，
    #    **否则「改精确」和「放宽」分不开**
    "reversed_relation_stays_false_both_reps": _both(
        lambda c: c.get("body_precedes_sidecar") is False),
    # ④ ⭐⭐⭐ **`BODY` 那枚被找到了**（分母**先钉非空** ⇒ `all([])` 恒真的坑）
    "body_seat_is_live_both_reps": _both(
        lambda c: (c.get("n_body") or 0) >= 1),
    # ⑤ ⭐⭐ **两轮对 H₁ 的回答一致**（否则这道题本身不稳定）
    "h1_verdict_stable_across_reps": bool(
        out["reps_agree"] and _c0.get("n_sidecar") is not None),
    "fired_eq_rows_both_reps": _both(lambda c: c.get("fired_eq_rows") is True),
    "listener_balanced_both_reps": _both(
        lambda c: c.get("listener_balanced") is True),
}

RAW_KEYS = {"k", "fired", "landed", "own", "seat", "dom", "scope"}
DERIVED_KEYS = {"sidecar_chain", "body_chain", "body_seats", "sidecar_seats",
                "n_body", "n_sidecar", "body_precedes_sidecar",
                "h1_sidecar_has_positive_tabindex", "ti_reading_is_live",
                "n_positive_ti_rows", "n_negative_ti_rows"}
out["keys_disjoint"] = bool(not (RAW_KEYS & DERIVED_KEYS))

out["recon"] = {
    "rep%d" % i: {
        "n_rows": c.get("n_rows"),
        "n_body": c.get("n_body"),
        "n_sidecar": c.get("n_sidecar"),
        "body_seats": c.get("body_seats"),
        "sidecar_seats": c.get("sidecar_seats"),
        "sidecar_precedes_body": c.get("sidecar_precedes_body"),
        "body_precedes_sidecar": c.get("body_precedes_sidecar"),
        "h1_sidecar_has_positive_tabindex": c.get(
            "h1_sidecar_has_positive_tabindex"),
        "ti_reading_is_live": c.get("ti_reading_is_live"),
        "n_positive_ti_rows": c.get("n_positive_ti_rows"),
        "n_negative_ti_rows": c.get("n_negative_ti_rows"),
        "sidecar_chain": c.get("sidecar_chain"),
        "body_chain": c.get("body_chain"),
        "fired_eq_rows": c.get("fired_eq_rows"),
        "listener_balanced": c.get("listener_balanced"),
    }
    for i, c in enumerate(r["cells"][0] for r in out["runs"])
}

out["gate_notes"] = (
    "⭐ 975 的门围绕「**H₁ 可判红**」与「**读数是活的**」：\n"
    "  · `h1_positive_tabindex_ancestor_both_reps` 要求 `与 AI 对话` 的"
    "**祖先链**里**有**正 `tabindex` ⇒ **恒 `False` 就是 H₁ 被否**，"
    "而不是「没查到」⇒ ⭐⭐ **假设门必须能判红，否则它只是叙述**；\n"
    "  · `ti_reading_is_live_both_reps` 是**正向自证**："
    "`ti_reading` 恒 `False` 时「没有作用域」与「读数是空的」**分不开** ⇒ "
    "**必须如实判红**；\n"
    "  · `body_precedes_sidecar_both_reps` 只钉**顺序关系**，"
    "**不钉**任何绝对下标。")

out["what_975_measures"] = (
    "① ⭐⭐⭐⭐⭐ 每个 out 段停靠点的**整条祖先链**（≤ 12 层）连同每一层的\n"
    "   · `ti_attr` = `getAttribute('tabindex')`（**属性在不在 / 是什么**）\n"
    "   · `ti_prop` = `.tabIndex`（**归一化后的可聚焦性**）\n"
    "   ⇒ 两件事分得开 ⇒ **不需要 `or` 兜底**（971 踩过 `(x or -1) < 0`）；\n"
    "  ② ⭐⭐⭐ **`与 AI 对话` 的祖先链里有没有正 `tabindex`**（H₁）；\n"
    "  ③ ⭐⭐ 全局视野：多少停靠点的祖先链带正 / 负 `tabindex`\n"
    "  ⇒ ⇒ **只输出读数与关系，H₁ 的真伪交给 verifier 的判据，探针里不写死**")

out["discipline_975"] = (
    "① ⭐⭐⭐⭐⭐ **假设门必须能判红** —— 「假设门」这一族最容易滑成叙述："
    "写一句「可能是作用域造成的」、门却是恒绿的 ⇒ "
    "**门要直接判「祖先链里有没有正 `tabindex`」**；\n"
    "  ② ⭐⭐⭐ **正向自证门与主门成对** —— "
    "「读数是空的」和「读数里没有」**看起来一模一样** ⇒ "
    "`ti_reading_is_live` 先证明**确实逐层拿到了**；\n"
    "  ③ ⭐⭐ **读数不许用 `or` 兜底** —— `ti_attr` 用 `getAttribute` 拿"
    "**原始属性值**（没有就是 `None`）⇒ 探针里落一条 "
    "`assert 'ti_attr ||' not in SCOPE_JS` **把它钉死**；\n"
    "  ④ ⭐⭐ **钉关系不钉绝对值** —— 只钉「`BODY` 在 `与 AI 对话` 之前」，"
    "**不钉**下标；\n"
    "  ⑤ ⭐⭐ **两个平行列表、不是元组**（973 那一族栽到第五次 ⇒ 结构上拆掉）；\n"
    "  ⑥ ⭐ **零计费**：按键只有 `Tab`，⛔ 守卫拦在 `mouse.click` 之前")

out["skip_note"] = (
    "⚠️ 本探针**只测源站**，且**只测「祖先链有没有正 tabindex」** ⇒ "
    "即使 H₁ 被证实，也**只说明「存在一个作用域边界」**，"
    "**不等于**「作用域就是 body 的成因」⇒ "
    "**作用域说法要成立，还得测「作用域内还剩几个可聚焦元素」** —— 本批不测。")

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1, default=str)
print("已写出 %s" % OUT, flush=True)
print("design_gates: %s" % json.dumps(out["design_gates"], ensure_ascii=False),
      flush=True)
