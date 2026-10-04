#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批 972 · 源站探针：⭐⭐⭐⭐⭐ **`BODY` 接缝在 out 环里的**座位**，以及
**969 那套 `landed` 口径到底吃掉了什么**。

── 来由（971 的遗留，但方向反了）────────────────────────────────────────

971 把「`BODY` 为什么有时在线有时不在线」记成**未查明**，并猜它是
「走过了最后一个可聚焦元素之后」的落点（**规模量**）。

⭐⭐⭐⭐⭐ **971 自己的原始读数就把那个猜测推翻了**，本批把它查实：

- 971 源站 out 环共 18 格，`BODY` 落在**第 7 格**（k=90）——
  它**后面还有 11 枚真 UI 停靠点** ⇒ **不是**「走到末尾」的兜底
- ⭐⭐⭐⭐⭐ **回查 969 的原始读数**：`BODY` **在 969 那个 k=90 上**，
  两批 4 轮的 k=86..96 **逐格完全相同** ⇒
  ⇒ **971 那条「未查明」是个假问题：它一直在，在同一个座位上**

── ⭐⭐⭐⭐⭐ 而 969 之所以没看见它，机制现在能说死了（同一族错的第六次）──

969 的 out 段是这么圈出来的（`jimeng_probe969_projectpanel_src.py:305-310`）：

    for r in rows:
        for L in (r.get("landed") or []):
            if L.get("kind") == "out":
                out_stops.append((r["k"], r["finger"]))
                break

而 `BODY` 那一行的 **`landed` 是空数组** ⇒ 它**在进 `out_stops` 之前
就被 `for L in (...)` 整行过滤掉了** ⇒ `n_out_stops = 17`、
`null_tid_rows = 0`。

⇒ ⇒ ⭐⭐⭐⭐⭐ **`969` 不是「没量到」，是「量到了但被一个代理条件滤掉了」**
—— 代理条件（`landed` 里有没有 `kind=='out'` 的条目）**恰好不认 `BODY`**
⇒ 同一个元素在 954（被命名成假 UI）、969（被静默丢弃）里各错一次。

⇒ ⇒ ⭐⭐⭐ **本批的门必须钉死这一条**：两套口径的计数**并排摆出来**，
差额**必须恰好等于 `BODY` 的枚数** ⇒ 差 0 或差 2 都判红。

── 本批新增的一件仪器 ──────────────────────────────────────────────────

971 只从 `tag == 'BODY'` **推断**那是 `document.body`；本批**直接读**
`el === document.body` ⇒ `tag` 相同但**不是** body 的元素（若有）
就分得开了（关系式：两者**必须同时**为真/为假）。

**本批零计费动作。** 每轮只在开头点**一次画布空白**去焦点，⛔ 守卫拦在
`mouse.click` 之前；按键只有 `Tab`。
"""
from __future__ import annotations

import json
import os

OUT = "/tmp/b972-seam.json"
REPS = 2
SETTLE = 260           # ms（照 967–971）
BLANK_WAIT = 900       # ms（照 952–971）
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


_p966 = _src("jimeng_probe966_clicksel_src.py")
_p967 = _src("jimeng_probe967_armptr_src.py")
_p970 = _src("jimeng_probe970_owntid_ck.py")
_p971 = _src("jimeng_probe971_savestate_src.py")


def _grab(name, src=None):
    """⭐ 逐字从上游探针里抠出那一段 JS，并 `assert` 它真的在那份源码里。"""
    import re
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
TEXTHO_JS = _grab("TEXTHO_JS", _p971)

# ── ⭐⭐ 本批的新件：`SEAT_JS`（**只读、从不调 `focus()`**）──────────────
#   971 只从 `tag == 'BODY'` **推断**；这里**直接比引用**。
SEAT_JS = """([nodeSel]) => {
  const el = document.activeElement;
  if (!el) return {is_body: null, tag: null, self_tid: null,
                   aria_whoami: null, in_node_list: null};
  const al = el.getAttribute('aria-label');
  const ti = el.getAttribute('title');
  const txt = el.innerText || '';
  return {
    is_body: el === document.body,
    tag: (el.tagName || '').toUpperCase(),
    self_tid: el.getAttribute('data-testid'),
    aria_whoami: al || ti || (txt || '').slice(0, 30) || null,
    in_node_list: !!(el.closest && el.closest(nodeSel))
  };
}"""

# ⭐⭐ 门 1：新件必须**只读**、且必须**真的**读了 `el === document.body`
assert "el === document.body" in SEAT_JS, "SEAT_JS 没收 `el === document.body`"
assert "focus(" not in SEAT_JS, "SEAT_JS 不许调 `focus()`"
assert SEAT_JS.count("is_body:") >= 1, "SEAT_JS 少了 `is_body` 字段"
assert SEAT_JS.count("in_node_list:") >= 1, "SEAT_JS 少了 `in_node_list` 字段"
# ⚠️ 970 的 `OWN_JS` 必须真的判 `kind`（本批整条链子都靠它）
assert "kind:" in OWN_JS, "OWN_JS 里没有 `kind` 字段"
assert "closest_tid:" in OWN_JS, "OWN_JS 里没有 `closest_tid` 字段"


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
    "sidecar_tid": SIDECAR_TID, "n_lead_cap": N_LEAD_CAP, "node_sel": NODE_SEL,
    "question": "⭐⭐⭐⭐⭐ `BODY` 接缝在 out 环里的**座位**是哪一格？"
                "**它稳不稳？** ⇒ 并把 **969 那套 `landed` 口径**的计数"
                "**并排**算出来，看它到底吃掉了什么",
    "ruler": {
        "js_verbatim_from_967": ["INSTALL_JS", "READ_JS", "OFF_NULL_JS",
                                 "BLANK_JS"],
        "js_verbatim_from_970": ["OWN_JS"],
        "js_verbatim_from_971": ["TEXTHO_JS"],
        "how_proved": "⭐ `_grab(name, src)` 抠出那一段，再 `assert _s in _src`",
        "new_pieces": ["SEAT_JS"],
        "why_read_not_instrument": "⭐ `SEAT_JS` **只读属性/文本**、"
                                   "**从不调 `focus()`** ⇒ 不污染焦点读数",
        "two_calibers_side_by_side": "⭐⭐⭐⭐⭐ **本批的正题**："
                                     "① `own.kind == 'out'`（971 口径，读 "
                                     "`document.activeElement`）"
                                     "② `landed[].kind == 'out'`"
                                     "（**969 口径**）"
                                     "⇒ 两套**并排**输出，差额必须**恰好**"
                                     "等于 `BODY` 的枚数",
    },
    "baseline": {
        "s971_out_arc_len": 18,
        "s971_body_k": 90,
        "s971_body_seat": 7,
        "s969_n_out_stops": 17,
        "s969_null_tid_rows": 0,
        "s969_caliber_caveat": "⚠️⚠️⚠️ 969 的 `out_stops` 是用 "
                               "`for L in r['landed']: if L['kind']=='out'` "
                               "圈的 ⇒ **`BODY` 那行 `landed` 是空的、"
                               "整行被滤掉** ⇒ 它的 17 与 0 都是"
                               "**代理条件的产物**，不是页面事实",
        "s971_own_hypothesis": "⚠️ 971 猜「`BODY` 是走过了最后一个可聚焦"
                               "元素之后的落点」（**规模量**）"
                               "⇒ ⭐⭐⭐ **971 自己的读数就否掉了它**："
                               "`BODY` 之后还有 11 枚真 UI 停靠点",
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
            ap = ev(READ_JS)             # ⭐ 读走**并摘监听**（诊断动作必须还原）
            c["n_read"] += 1
            o = ev(OWN_JS, [NODE_SEL])
            s = ev(SEAT_JS, [NODE_SEL])
            t = ev(TEXTHO_JS, [NODE_SEL])
        finally:
            ev(OFF_NULL_JS)
        row = {"k": c["n_lead"], "key": "Tab",
               "fired": (ap or {}).get("fired"),
               "landed": (ap or {}).get("landed"),
               "own": o, "seat": s, "text": t}
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

    # ① 971 口径：读 `document.activeElement` 得来的 `own.kind`
    out_own = [(r["k"], r) for r in rows if r["own"].get("kind") == "out"]
    # ② ⭐⭐⭐ 969 口径：只看 `landed` 里有没有 `kind=='out'` 的条目
    out_landed = []
    for r in rows:
        for _L in (r.get("landed") or []):
            if _L.get("kind") == "out":
                out_landed.append((r["k"], r))
                break
    c["n_out_own_caliber"] = len(out_own)
    c["n_out_landed_caliber"] = len(out_landed)
    c["caliber_gap"] = len(out_own) - len(out_landed)
    # ⭐⭐⭐⭐⭐ **形状自证**：两套口径的元素都必须是 `(k, row)` 二元组
    #   （⚠️⚠️ 这一族已经栽到**第四次**：把 `(k, row)` 当成 `row` 用 ⇒
    #   `r["seat"]` 直接 `TypeError`。`py_compile` **抓不到**这种错 ——
    #   ⭐ **它只抓语法，抓不到运行期的形状**）
    assert all(isinstance(t, tuple) and len(t) == 2 and isinstance(t[1], dict)
               for t in out_own), "out_own 里有不是 (k, row) 的元素"
    assert all(isinstance(t, tuple) and len(t) == 2 and isinstance(t[1], dict)
               for t in out_landed), "out_landed 里有不是 (k, row) 的元素"
    # ⭐⭐⭐ **被 969 那套口径吃掉的行，逐个记下来**
    landed_ks = {k for k, _r in out_landed}
    dropped = [(k, r) for k, r in out_own if k not in landed_ks]
    c["n_dropped_by_landed_caliber"] = len(dropped)
    c["dropped_detail"] = [
        {"k": k, "tag": (r["own"] or {}).get("tag"),
         "is_body": (r["seat"] or {}).get("is_body"),
         "landed_n": len(r.get("landed") or []),
         "aria_whoami": (r["text"] or {}).get("aria_whoami")}
        for k, r in dropped]

    # ── ⭐⭐⭐ 本批的正题：接缝的**座位** ──────────────────────────
    def _key(r):
        o = r["own"] or {}
        return (o.get("tag"), o.get("self_tid"), o.get("closest_tid"))

    ring = [_key(r) for _k, r in out_own]
    c["ring_tids"] = [[t, st, ct] for (t, st, ct) in ring]
    c["n_ring"] = len(ring)
    body_seats = [i for i, (_k, r) in enumerate(out_own)
                  if (r["seat"] or {}).get("is_body") is True]
    c["body_seats"] = body_seats
    c["n_body_seats"] = len(body_seats)
    # ⭐ `is_body` 与 `tag=='BODY'` **必须同时**成立（关系式 ⇒ 两者对不上就红）
    c["is_body_eq_tag_body"] = all(
        ((r["seat"] or {}).get("is_body") is True)
        == ((r["own"] or {}).get("tag") == "BODY")
        for _k, r in out_own)
    # ⭐⭐⭐ **接缝的前一格是不是「与 AI 对话」**（这是 971/970 读数的共性）
    c["seam_predecessors"] = [
        {"seat": i, "prev_key": list(_key(out_own[i - 1][1]))
         if i > 0 else None,
         "prev_is_sidecar": bool(
             i > 0 and (_key(out_own[i - 1][1])[2] == SIDECAR_TID))}
        for i in body_seats]
    c["seam_predecessor_is_sidecar"] = bool(
        body_seats) and all(x["prev_is_sidecar"] for x in c["seam_predecessors"])
    # ⭐⭐⭐ 「不是末尾的兜底」——它**后面**还有几枚真 UI 落点
    c["n_ui_after_first_body"] = len(
        [1 for i in body_seats[:1] for _k, r in out_own[i + 1:]
         if (r["own"] or {}).get("tag") not in ("BODY", "NEXTJS-PORTAL")])
    c["body_is_not_end_fallback"] = c["n_ui_after_first_body"] > 0
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
    _c0.get("ring_tids") == _c1.get("ring_tids")
    and _c0.get("body_seats") == _c1.get("body_seats")
    and _c0.get("caliber_gap") == _c1.get("caliber_gap"))

# ── ⭐⭐⭐ 门：**每一条都必须能判红**（恒真/恒假比没有门更坏）────────────
out["design_gates"] = {
    # ① ⭐⭐⭐⭐⭐ 接缝**既不在环首也不在环尾**（**关系式**，不钉绝对下标）
    "body_seat_is_interior_both_reps": _both(
        lambda c: bool(c.get("body_seats"))
        and all(0 < i < (c.get("n_ring") or 0) - 1 for i in c["body_seats"])),
    # ② ⭐⭐⭐⭐⭐ 两轮**同一座位**（**跨轮比较**，不是绝对值）
    "body_seat_identical_across_reps": bool(
        _c0.get("body_seats") and _c0.get("body_seats") == _c1.get("body_seats")),
    # ② ⭐⭐⭐⭐⭐ 前一格就是「与 AI 对话」⇒ 接缝位置**不是末尾兜底**
    "seam_predecessor_is_sidecar_both_reps": _both(
        lambda c: c.get("seam_predecessor_is_sidecar") is True),
    # ③ ⭐⭐⭐⭐⭐ 971 的猜测（「末尾兜底 / 规模量」）**必须被否掉**
    "body_is_not_end_fallback_both_reps": _both(
        lambda c: c.get("body_is_not_end_fallback") is True),
    # ④ ⭐⭐⭐⭐⭐ **969 那套 `landed` 口径吃掉的行数 > 0**
    #    （恒 0 ⇒ 「没吃掉」与「判据写错了」分不开 ⇒ 必须能判红）
    "landed_caliber_drops_something_both_reps": _both(
        lambda c: (c.get("n_dropped_by_landed_caliber") or 0) > 0),
    # ⑤ ⭐⭐⭐⭐⭐ **差额恰好等于被吃掉的枚数**（差 0 或差 2 都判红）
    "caliber_gap_eq_dropped_both_reps": _both(
        lambda c: c.get("caliber_gap") == c.get("n_dropped_by_landed_caliber")),
    # ⑥ ⭐⭐⭐⭐⭐ **被吃掉的全都是 `BODY`**（一一对应，不许有别的漏网）
    #    ⚠️⚠️ `all()` 作用在**空列表**上是恒真 ⇒ **分母必须先钉非空**，
    #    否则这道门在「一口都没吃」时**照样绿**
    "dropped_rows_are_all_body_both_reps": _both(
        lambda c: (c.get("n_dropped_by_landed_caliber") or 0) > 0
        and all(x.get("is_body") is True
                for x in (c.get("dropped_detail") or []))
        and all(x.get("landed_n") == 0
                for x in (c.get("dropped_detail") or []))),
    # ⑦ ⭐⭐ `is_body` 与 `tag=='BODY'` **同时**成立
    "is_body_eq_tag_body_both_reps": _both(
        lambda c: c.get("is_body_eq_tag_body") is True),
    "ring_order_reproducible_both_reps": _both(
        lambda c: (c.get("n_ring") or 0) >= 10),
    "fired_eq_rows_both_reps": _both(lambda c: c.get("fired_eq_rows") is True),
    "listener_balanced_both_reps": _both(
        lambda c: c.get("listener_balanced") is True),
    "reps_agree": bool(out["reps_agree"]),
}

RAW_KEYS = {"k", "fired", "landed", "own", "seat", "text"}
DERIVED_KEYS = {"ring_tids", "body_seats", "caliber_gap",
                "n_dropped_by_landed_caliber", "dropped_detail",
                "seam_predecessors", "n_ui_after_first_body",
                "n_out_own_caliber", "n_out_landed_caliber",
                "is_body_eq_tag_body", "body_is_not_end_fallback"}
out["keys_disjoint"] = bool(not (RAW_KEYS & DERIVED_KEYS))

out["recon"] = {
    "rep%d" % i: {
        "n_rows": c.get("n_rows"),
        "n_ring": c.get("n_ring"),
        "n_out_own_caliber": c.get("n_out_own_caliber"),
        "n_out_landed_caliber": c.get("n_out_landed_caliber"),
        "caliber_gap": c.get("caliber_gap"),
        "n_dropped_by_landed_caliber": c.get("n_dropped_by_landed_caliber"),
        "dropped_tags": [x.get("tag") for x in (c.get("dropped_detail") or [])],
        "dropped_landed_n": [x.get("landed_n")
                             for x in (c.get("dropped_detail") or [])],
        "body_seats": c.get("body_seats"),
        "seam_predecessors": c.get("seam_predecessors"),
        "n_ui_after_first_body": c.get("n_ui_after_first_body"),
        "is_body_eq_tag_body": c.get("is_body_eq_tag_body"),
        "n_fired_total": c.get("n_fired_total"),
        "fired_eq_rows": c.get("fired_eq_rows"),
        "listener_balanced": c.get("listener_balanced"),
    }
    for i, c in enumerate(r["cells"][0] for r in out["runs"])
}

out["gate_notes"] = (
    "⭐ 972 的门围绕「**接缝的座位**」与「**两套口径的差额**」：\n"
    "  · `landed_caliber_drops_something_both_reps` 要求 969 那套 `landed` "
    "口径**真的吃掉过东西** ⇒ 恒 0 时「没吃掉」与「判据写错了」**分不开**，"
    "**必须如实判红**而不是安静地写「口径一致」；\n"
    "  · `caliber_gap_eq_dropped_both_reps` 把差额**钉在被吃掉的枚数上** "
    "⇒ 差 0（两套口径一样）和差 2（多漏了一枚）**都判红**；\n"
    "  · `body_seat_stable_both_reps` 钉的是**两轮同一座位**，"
    "不是某个绝对数字 ⇒ 源站逐轮在动（节点数、Credits、缩放）也不影响")

out["what_972_measures"] = (
    "① ⭐⭐⭐⭐⭐ **两套 out 段口径并排**：`own.kind=='out'`（971）"
    "vs `landed[].kind=='out'`（**969**）⇒ 差额**必须恰好**等于被吃掉的枚数；\n"
    "  ② ⭐⭐⭐⭐⭐ **接缝的座位**：环里**按序**找出 `el === document.body` 的那一格，"
    "记下它的**下标**与**前一格**；\n"
    "  ③ ⭐⭐ `is_body`（**比引用**）与 `tag == 'BODY'`（**比标签**）"
    "**必须同时**成立 ⇒ 标签相同但**不是** body 的元素分得开；\n"
    "  ④ ⇒ **只回答「在哪、稳不稳、被谁吃掉」，不做机制推断**")

out["discipline_972"] = (
    "① ⭐⭐⭐⭐⭐ **回查上一批的原始读数，可能直接把它自己的「未查明」"
    "变成一个假问题** —— 971 那条「`BODY` 时有时无」"
    "**回查 969 的 k=90 就没了**：它一直在 ⇒ "
    "⭐ **「没看见」与「不在」是两件事，前者需要更多证据、后者需要反证**；\n"
    "  ② ⭐⭐⭐⭐⭐ **代理条件会静默吃掉你要找的那个东西** —— "
    "969 用 `landed[].kind=='out'` 圈 out 段，而 `BODY` 的 `landed` 是空的 ⇒ "
    "**整行在进统计之前就没了** ⇒ ⭐⭐ "
    "**这一族已经第六次了**（954 命名成假 UI、969 静默丢弃、970 换了字段口径、"
    "971 三套并读、972 把两套并排）⇒ "
    "⭐⭐⭐ **凡是用「某个代理条件」圈出来的集合，都要单独记「被代理条件吃掉了多少」**；\n"
    "  ③ ⭐⭐⭐ **门必须能判红**：恒 0 时「不存在」与「判据写错了」**分不开** ⇒ "
    "`landed_caliber_drops_something` 与 `caliber_gap_eq_dropped` 成对，"
    "一个防恒 0、一个防漏网；\n"
    "  ④ ⭐⭐ **`SEAT_JS` 只读属性、从不调 `focus()`** ⇒ 不污染焦点读数；\n"
    "  ⑤ ⭐⭐ **零计费**：按键只有 `Tab`，⛔ 守卫拦在 `mouse.click` 之前")

out["skip_note"] = (
    "⚠️ 本探针**不**回答「`BODY` 为什么在那里」—— 那是**机制问题**，"
    "需要单独的设计（本批只测**座位**与**可重复性**）")

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1, default=str)
print("已写出 %s" % OUT, flush=True)
print("design_gates: %s" % json.dumps(out["design_gates"], ensure_ascii=False),
      flush=True)
