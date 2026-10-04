#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""batch 974 · 源站探针：⭐⭐⭐⭐⭐ **把 973 那件仪器逐字搬到源站**
⇒ 补上 973 明确留下的那个对照缺口。

── 973 留的口子（**必须先核「我比的是不是同一个东西」**）──────────────

973 在**复刻侧**用 `DOMRANK_JS` 证明了「环序 = DOM 序」（全文档下标单调、
恰好一次回绕），并据此判定 `rf__wrapper` 的位置差异是**实现差异**。

⚠️⚠️⚠️ **但 973 自己写明了**：**源站侧的 `dom_rank` 没量**
⇒ 「源站的环**也是** DOM 序」**不能**由 973 下结论
⇒ ⇒ ⭐⭐⭐⭐⭐ **本批就是去补这一侧的**：把同一件仪器、**同一把尺子**、
**逐字**搬到源站跑一遍。

⚠️⭐⭐ **不复制源码**：`DOMRANK_JS` 用 `_grab("DOMRANK_JS", _p973)` 从
973 的**文件内容**里逐字抠出来，再 `assert _s in _p973src`
⇒ **「同一件仪器」是可证的、不是口头保证**。

── ⭐⭐⭐⭐⭐ 本批要判的三件事（每件都有独立的分母与自证门）────────────

① **源站的环序也是 DOM 序吗？**（973 只证了复刻侧）
② **`rf__wrapper` 在源站 DOM 序里的位置**（973 说它在 `用户菜单` 与 `文本` 之间）
③ ⭐⭐⭐ **源站那一枚 `BODY` 的前一格能不能聚焦？**
   973 在复刻侧读到「前一格 `focusable = false`、是 `NEXTJS-PORTAL`」
   ⇒ 并明确警告「**两侧的 `BODY` 很可能不是同一个机制**、不许照搬」
   ⇒ ⇒ **本批去测源站那一侧，把它并排摆出来**
   ⇒ ⚠️ **判据只钉「测到了、且能判红」，不预写它该是什么**

**本批零计费动作。** 每轮只在开头点**一次画布空白**去焦点，⛔ 守卫拦在
`mouse.click` 之前；按键只有 `Tab`。
"""
from __future__ import annotations

import json
import os
import re

OUT = "/tmp/b974-source-domrank.json"
REPS = 2
SETTLE = 260           # ms（照 967–973）
BLANK_WAIT = 900       # ms
N_LEAD_CAP = 140       # ⭐ 硬上限，不是目标
RAIL_TID = "canvas-fixed-toolbar"
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
_p971 = _src("jimeng_probe971_savestate_src.py")
_p972 = _src("jimeng_probe972_seam_src.py")
_p973 = _src("jimeng_probe973_ringorder_ck.py")


def _grab(name, src=None):
    """⭐ 逐字从上游探针里抠出那一段 JS，并 `assert` 它真的在那份源码里。"""
    m = re.search(r'^%s\s*=\s*r?"""(.*?)"""' % name, src or "", re.S | re.M)
    assert m, "抠不到 %s" % name
    _s = m.group(1)
    assert _s in (src or ""), "%s 不是逐字抠出来的" % name
    return _s


# ── ⭐⭐⭐⭐⭐ **同一件仪器**：从 973 逐字抠，不复制、不改写 ──────────────
DOMRANK_JS = _grab("DOMRANK_JS", _p973)
INSTALL_JS = _grab("INSTALL_JS", _p967)
READ_JS = _grab("READ_JS", _p967)
OFF_NULL_JS = _grab("OFF_NULL_JS", _p967)
BLANK_JS = _grab("BLANK_JS", _p967)
OWN_JS = _grab("OWN_JS", _p970)
TEXTHO_JS = _grab("TEXTHO_JS", _p971)
SEAT_JS = _grab("SEAT_JS", _p972)

# ⭐⭐⭐⭐⭐ **「同一把尺子」必须可证**，不能只写在文档里
assert DOMRANK_JS in _p973, "DOMRANK_JS 不在 973 探针里 ⇒ 不是同一件仪器"
assert "document.querySelectorAll('*')" in DOMRANK_JS, \
    "DOMRANK_JS 没读全文档下标"
assert "focus(" not in DOMRANK_JS, "DOMRANK_JS 不许调 focus()"
# ⚠️⚠️ 973 踩过两次：门 1 写坏（`ring_tids and 6`）、门 6 挂在空列表上恒真
assert DOMRANK_JS.count("dom_rank:") >= 1
assert DOMRANK_JS.count("tag:") >= 1, "DOMRANK_JS 少了 tag（973 加的）"
assert DOMRANK_JS.count("focusable:") >= 1, "DOMRANK_JS 少了 focusable（973 加的）"

# ⛔ 计费守卫用的纯读件
POINT_JS = """([x, y]) => {
  const el = document.elementFromPoint(x, y);
  const host = el && el.closest('[data-testid]');
  return {tid: host ? host.getAttribute('data-testid') : null,
          al: (el.innerText || el.textContent || '').slice(0, 40)};
}"""


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
    "n_lead_cap": N_LEAD_CAP, "node_sel": NODE_SEL,
    "question": "⭐⭐⭐⭐⭐ **把 973 那件 `DOMRANK_JS` 逐字搬到源站** ⇒ "
                "① 源站的环**也是** DOM 序吗？② `rf__wrapper` 在源站 DOM 序里"
                "**哪个位置**？③ 源站那一枚 `BODY` 的**前一格能不能聚焦**"
                "（973 警告「两侧很可能不是同一个机制」）？",
    "ruler": {
        "js_verbatim_from_973": ["DOMRANK_JS"],
        "js_verbatim_from_967": ["INSTALL_JS", "READ_JS", "OFF_NULL_JS",
                                 "BLANK_JS"],
        "js_verbatim_from_970": ["OWN_JS"],
        "js_verbatim_from_971": ["TEXTHO_JS"],
        "js_verbatim_from_972": ["SEAT_JS"],
        "new_pieces": ["POINT_JS"],
        "how_proved": "⭐ `_grab(name, src)` 抠出那一段，再 `assert _s in src` "
                      "⇒ **「同一件仪器」是可证的、不是口头保证**",
        "why_not_retyped": "⚠️⭐⭐ **不复制源码** —— 复制一份就多一处可能漂移的地方；"
                           "`_grab` 把「两侧真的是同一件仪器」变成**一条断言**",
        "why_read_not_instrument": "⭐ `DOMRANK_JS` **只读属性**、"
                                   "**从不调 `focus()`** ⇒ 不污染焦点读数",
    },
    "baseline": {
        "s973_replica": "⭐ 973 实测（复刻侧）：`arc_ranks` 单调、恰好一次回绕 ⇒ "
                        "**环序 = DOM 序**；`rf__wrapper` 的 `dom_rank` = **42**、"
                        "是环里**最小**的真 UI 下标；`BODY` 的前一格 = "
                        "`NEXTJS-PORTAL`、`focusable = false`",
        "s973_gap": "⚠️⚠️ **973 明确：源站侧的 `dom_rank` 没量** ⇒ "
                    "**本批就是去补这一侧**",
        "s972_source_ring": "⭐ 972 实测（源站）：环长 18 枚、`BODY` 在下标 6、"
                            "前面那一枚是 `与 AI 对话`、后面还有 11 枚真 UI；"
                            "`rf__wrapper` 在 `用户菜单` 与 `文本` 之间",
        "no_predicted_value": "⚠️⭐⭐ **本批不预写结论** —— 门只钉"
                              "「**测到了**」与「**能判红**」，"
                              "**不钉**源站 `BODY` 的前一格**该是什么**",
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
            t = ev(TEXTHO_JS, [NODE_SEL])
        finally:
            ev(OFF_NULL_JS)
        row = {"k": c["n_lead"], "key": "Tab",
               "fired": (ap or {}).get("fired"),
               "landed": (ap or {}).get("landed"),
               "own": o, "seat": s, "dom": dr, "text": t}
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
    # ⭐⭐⭐⭐ **两个平行列表、不是元组**（973 那一族栽到第五次 ⇒ 结构上拆掉）
    out_rows = [r for r in rows if r["own"].get("kind") == "out"]
    out_ks = [r["k"] for r in out_rows]
    assert all(isinstance(r, dict) and "own" in r for r in out_rows), \
        "out_rows 里有不是 row-dict 的元素"
    c["n_out_presses"] = len(out_rows)

    # 取**本段第一个 out 行起的连续一段**（走查不重试 ⇒ 一段 = 一圈）
    # ⚠️⚠️ **不能靠「首遇重复就停」** —— 源站 `搜索` 与 `生成历史` **共用一个
    # tid**，靠 tid 去重会**截断在 12**（971 已经栽过一次这个坑）
    arc_rows, arc_ks = [], []
    for j, r in enumerate(out_rows):
        if arc_ks and out_ks[j] != arc_ks[-1] + 1:
            break
        arc_ks.append(out_ks[j])
        arc_rows.append(r)
    c["arc_len"] = len(arc_rows)
    c["arc_ranks"] = [(r.get("dom") or {}).get("dom_rank") for r in arc_rows]

    # ── ① 源站的环序**是不是** DOM 序（关系式，不钉绝对值）─────────
    wraps, unknown = 0, 0
    ranks = c["arc_ranks"]
    for j in range(1, len(ranks)):
        a, b = ranks[j - 1], ranks[j]
        if a is None or b is None:
            unknown += 1
        elif b <= a:
            wraps += 1
    c["n_rank_descents"] = wraps
    c["n_rank_unknown"] = unknown
    c["ring_follows_dom_order"] = (unknown == 0 and wraps <= 1
                                   and len(arc_rows) >= 10)

    # ── ② `rf__wrapper` 在源站 DOM 序里的座位 ────────────────────
    flow_idx = [i for i, r in enumerate(arc_rows)
                if (r.get("dom") or {}).get("tag") == "DIV"
                and (r.get("dom") or {}).get("dom_path", "").startswith(
                    "div#rf__wrapper")]
    flow_idx2 = [i for i, r in enumerate(arc_rows)
                 if (r.get("own") or {}).get("self_tid") == "rf__wrapper"]
    c["flow_seats_by_tag"] = flow_idx
    c["flow_seats_by_tid"] = flow_idx2
    c["n_flow_seats"] = len(flow_idx2)

    # ── ③ 源站那一枚 `BODY` 的**前一格能不能聚焦**（并排摆出，不预写）──
    body_i = [i for i, r in enumerate(arc_rows)
              if (r.get("seat") or {}).get("is_body") is True]
    c["body_seats"] = body_i
    c["seam_pred"] = [
        {"seat": i,
         "prev_tag": ((arc_rows[i - 1].get("dom") or {}).get("tag")
                      if i > 0 else None),
         "prev_focusable": ((arc_rows[i - 1].get("dom") or {}).get("focusable")
                            if i > 0 else None),
         "prev_tid": ((arc_rows[i - 1].get("own") or {}).get("closest_tid")
                      if i > 0 else None),
         "self_rank": (arc_rows[i].get("dom") or {}).get("dom_rank"),
         "prev_rank": ((arc_rows[i - 1].get("dom") or {}).get("dom_rank")
                       if i > 0 else None),
         "prev_dom_path": ((arc_rows[i - 1].get("dom") or {}).get("dom_path")
                           if i > 0 else None)}
        for i in body_i]
    # ⚠️ 只记**测到了**（`focusable` 不是哨兵值），**不预写它该是什么**
    c["seam_pred_measured"] = bool(body_i) and all(
        x["prev_focusable"] is not None for x in c["seam_pred"])

    def _nm(r):
        o = r.get("own") or {}
        t = o.get("closest_tid") or o.get("self_tid")
        return "%s/%s" % (o.get("tag"), t or ("<%s>" % (o.get("aria") or "?")))

    # ⭐⭐ 972 的老门：`is_body`（比引用）与 `tag == 'BODY'`（比标签）
    #   **必须同时**成立 ⇒ 标签相同但**不是** body 的元素分得开
    # ⭐⭐⭐⭐⭐ **顺序签名**：只记「相邻两项谁大」，**不记绝对值**
    #   ⇒ 与源站 DOM 的总大小**无关** ⇒ 逐轮多一个少一个元素都不影响
    #   ⚠️⚠️⚠️ **第一版的跨轮门拿 `arc_ranks` 直接比相等** ⇒ 那是一道
    #   **错在种类**的门：源站 DOM 逐轮在动（本批两轮每项正好差 **1**）⇒
    #   **它必然红，而红的原因不是「环序变了」** ⇒ 改成比**顺序关系**，
    #   **不是放宽**：环序若真变了，签名一定跟着变
    _sig = []
    for _j in range(1, len(c["arc_ranks"])):
        _a, _b = c["arc_ranks"][_j - 1], c["arc_ranks"][_j]
        _sig.append("up" if (_a is not None and _b is not None and _b > _a)
                    else ("down" if (_a is not None and _b is not None) else "?"))
    c["rank_order_signature"] = _sig
    c["is_body_eq_tag_body"] = all(
        ((r.get("seat") or {}).get("is_body") is True)
        == ((r.get("own") or {}).get("tag") == "BODY")
        for r in out_rows)
    c["arc_names"] = [_nm(r) for r in arc_rows]
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
    _c0.get("rank_order_signature") == _c1.get("rank_order_signature")
    and _c0.get("arc_names") == _c1.get("arc_names")
    and _c0.get("arc_len") == _c1.get("arc_len"))

out["design_gates"] = {
    # ① ⭐⭐⭐⭐⭐ **源站的环也**是 DOM 序（973 只证了复刻侧 —— 本批补这一侧）
    "source_ring_follows_dom_order_both_reps": _both(
        lambda c: c.get("ring_follows_dom_order") is True),
    # ② ⭐⭐⭐⭐ **`dom_rank` 是活读数**（防恒 `-1` ⇒ 防整条链安静空转）
    "source_dom_rank_is_live_both_reps": _both(
        lambda c: (c.get("n_rank_unknown") == 0)
        and all(r is not None and r >= 0
                for r in (c.get("arc_ranks") or []))),
    # ③ ⭐⭐⭐ 回绕**恰好 ≤ 1** 次（一圈只该绕一次）
    "source_at_most_one_wrap_both_reps": _both(
        lambda c: (c.get("n_rank_descents") or 0) <= 1),
    # ④ ⭐⭐⭐⭐ **`rf__wrapper` 那枚被找到了**（分母**先钉非空** ⇒ `all([])` 恒真的坑）
    "source_flow_stop_is_live_both_reps": _both(
        lambda c: (c.get("n_flow_seats") or 0) >= 1),
    # ⑤ ⭐⭐⭐ **源站 `BODY` 的前一格「测到了」** ——
    #    ⚠️ **只钉「测到」，不钉「它该不可聚焦」** ⇒ 不把复刻的机制预写给源站
    "source_seam_pred_measured_both_reps": _both(
        lambda c: c.get("seam_pred_measured") is True),
    # ⑥ ⭐⭐ `is_body` 与 `tag == 'BODY'` **必须同时**成立（972 的老门）
    #    ⚠️⚠️⚠️ **第一版这里写成了 `... if False else True` —— 那是一道**恒真门**，
    #    比没有门更坏** ⇒ 已删掉重写：判据落到**后处理真算的字段**上
    "is_body_eq_tag_body_both_reps": _both(
        lambda c: c.get("is_body_eq_tag_body") is True),
    # ⭐⭐⭐⭐⭐ **跨轮门：比「顺序签名」**（方向序列），**不比绝对下标**
    #   ⇒ 与 DOM 总大小无关 ⇒ 逐轮多/少一个元素**不该**让它红
    #   ⇒ 而**环序真变了**的话签名一定变 ⇒ **不是放宽**
    "source_ring_order_agrees_across_reps": bool(
        _c0.get("rank_order_signature")
        and _c0.get("rank_order_signature") == _c1.get("rank_order_signature")
        and _c0.get("arc_names") == _c1.get("arc_names")),
    "fired_eq_rows_both_reps": _both(lambda c: c.get("fired_eq_rows") is True),
    "listener_balanced_both_reps": _both(
        lambda c: c.get("listener_balanced") is True),
}

RAW_KEYS = {"k", "fired", "landed", "own", "seat", "dom", "text"}
DERIVED_KEYS = {"arc_ranks", "arc_names", "arc_len", "dom_ranks",
                "n_rank_descents", "n_rank_unknown", "ring_follows_dom_order",
                "body_seats", "seam_pred", "seam_pred_measured",
                "flow_seats_by_tag", "flow_seats_by_tid", "n_flow_seats"}
out["keys_disjoint"] = bool(not (RAW_KEYS & DERIVED_KEYS))

out["recon"] = {
    "rep%d" % i: {
        "n_rows": c.get("n_rows"),
        "arc_len": c.get("arc_len"),
        "n_out_presses": c.get("n_out_presses"),
        "arc_ranks": c.get("arc_ranks"),
        "rank_order_signature": c.get("rank_order_signature"),
        "arc_names": c.get("arc_names"),
        "n_rank_descents": c.get("n_rank_descents"),
        "n_rank_unknown": c.get("n_rank_unknown"),
        "ring_follows_dom_order": c.get("ring_follows_dom_order"),
        "body_seats": c.get("body_seats"),
        "seam_pred": c.get("seam_pred"),
        "seam_pred_measured": c.get("seam_pred_measured"),
        "is_body_eq_tag_body": c.get("is_body_eq_tag_body"),
        "flow_seats_by_tag": c.get("flow_seats_by_tag"),
        "flow_seats_by_tid": c.get("flow_seats_by_tid"),
        "n_flow_seats": c.get("n_flow_seats"),
        "fired_eq_rows": c.get("fired_eq_rows"),
        "listener_balanced": c.get("listener_balanced"),
    }
    for i, c in enumerate(r["cells"][0] for r in out["runs"])
}

out["gate_notes"] = (
    "⭐ 974 的门围绕「**补上 973 留的那一侧**」与「**不预写结论**」：\n"
    "  · `source_seam_pred_measured_both_reps` 只要求源站 `BODY` 的前一格"
    "**测到了**（`focusable` **不是**哨兵值）⇒ **刻意不钉「它该不可聚焦」** —— "
    "973 明确警告「两侧的 `BODY` 很可能不是同一个机制、"
    "**不许把复刻的机制预写给源站**」⇒ "
    "**把判据钉在「我测到了」而不是「我猜的答案」上**；\n"
    "  · `source_flow_stop_is_live_both_reps` 的分母**先钉非空** ⇒ "
    "`all([])` 恒真的坑（972/973 各栽过一次）在这道门上仍然成立。")

out["what_974_measures"] = (
    "① ⭐⭐⭐⭐⭐ **同一件仪器**（`DOMRANK_JS` 从 973 **逐字 `_grab`**、"
    "不复制源码）跑到**源站** ⇒ ① 源站的环**是不是** DOM 序；"
    "② `rf__wrapper` 在源站 DOM 序里的**座位**；"
    "③ ⭐⭐⭐ 源站那一枚 `BODY` 的**前一格能不能聚焦**（并排摆出，**不预写**）\n"
    "  ⇒ ⇒ **只补那一侧、只回答「测到什么」，不下「所以该怎样改」的结论**")

out["discipline_974"] = (
    "① ⭐⭐⭐⭐⭐ **先核「我比的是不是同一个东西」** —— "
    "973 只证了复刻侧，**源站那一侧没量** ⇒ "
    "**跨侧的结论必须两侧各量一次**，这与 968b/969/970 是**同一条纪律**；\n"
    "  ② ⭐⭐⭐ **不复制源码** —— `_grab` 把「两侧真的是同一件仪器」"
    "变成**一条断言**，而不是文档里的一句保证；\n"
    "  ③ ⭐⭐⭐ **不预写结论** —— 门钉「**测到了**」与「**能判红**」，"
    "**不钉**源站 `BODY` 的前一格**该是什么** ⇒ "
    "**上一批的机制不许直接当成这一批的预期**；\n"
    "  ④ ⭐⭐ **`all([])` 是恒真** ⇒ 每道「全部都是……」的门分母先钉非空；\n"
    "  ⑤ ⭐⭐ **两个平行列表、不是元组**（973 那一族栽到第五次 ⇒ 结构上拆掉）；\n"
    "  ⑥ ⭐ **零计费**：按键只有 `Tab`，⛔ 守卫拦在 `mouse.click` 之前")

out["skip_note"] = (
    "⚠️ **「环的起点」不可比**：两侧走查的**进入点**不同（复刻从画布根进、"
    "源站从节点进）⇒ 本批**不比较下标**，只比较**「单调 + 回绕次数」这类关系**。")

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1, default=str)
print("已写出 %s" % OUT, flush=True)
print("design_gates: %s" % json.dumps(out["design_gates"], ensure_ascii=False),
      flush=True)
