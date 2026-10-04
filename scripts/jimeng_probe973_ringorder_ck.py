#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""batch 973 **复刻侧**探针（**纯诊断 / 零插入零节点点击**）：
⭐⭐⭐⭐⭐ **环序到底是不是「纯 DOM 序」** —— 判 `rf__wrapper` 那个位置差异
**是实现差异还是口径差异**。

── 972 挖到的东西（本批的正题）──────────────────────────────────────────

把两侧的 out 环旋到同一起点逐格对齐后，**是同一条环**（其余 16 枚逐格顺序相同），
复刻只差两处：

- ① 多一枚 **0×0 的 `NEXTJS-PORTAL`**（968b 已证是 **Next.js 开发态产物**）
- ② **`rf__wrapper`（Canvas）那枚的位置**：
  **源站**在 `用户菜单` 与 `文本` **之间**；**复刻**在**接缝之后、`返回首页` 之前**

⇒ ⇒ ⚠️⚠️ **972 明确「本批不提出产品改动」**，因为**复刻侧 `rf__wrapper`
的成因还没量过** ⇒ 本批去量。

── ⭐⭐⭐⭐⭐ 本批要把「环序」变成一条**可证伪**的判据 ──────────────────

967 写过「复刻严格按**纯 DOM 序**」，但那是**看步长**（`+1` 为主、`gt2 = 0`）推的
⇒ **步长对得上，不代表顺序的来源被证实过**。

本批给**每个停靠点**记两个新字段：

- `dom_rank`：该元素在 `document.querySelectorAll('*')` 里的**下标**
  （**全文档序**，与任何 testid、任何「簇」都无关）
- `dom_path`：向上最多 4 层的 `tag#tid.class` 链（**它住在哪个容器里**）

⇒ ⇒ ⭐⭐⭐ **门 `ring_follows_dom_order_both_reps`**：
环上 `dom_rank` **单调递增**（允许**恰好一次**回绕）
⇒ **证成**「复刻的环序就是 DOM 序」

⇒ ⇒ ⭐⭐⭐⭐⭐ **那么 `rf__wrapper` 的位置差异就必然是 DOM 摆放差异**
（**实现差异**），**不是**口径差异 ⇒ 这就是 972 悬着的那件事的答案。

**本批零计费、零插入、零节点点击。** 按键只有 `Tab`；
⛔ 计费守卫拦在 `mouse.click` **之前**。
"""
from __future__ import annotations

import atexit
import json
import os
import re
import time

OUT = "/tmp/b973-ringorder.json"
REPS = 2
SETTLE = 260           # ms（照 968–970）
BLANK_WAIT = 900       # ms
N_LEAD_CAP = 140       # ⭐ 硬上限，不是目标
RAIL_TID = "canvas-fixed-toolbar"
NODE_SEL = "[data-nodeid], .react-flow__node"
KINDS = ()             # ⭐ 空 ⇒ 零插入零节点点击

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


def _grab(name, src=None):
    """⭐ 逐字从上游探针里抠出那一段 JS，并 `assert` 它真的在那份源码里。"""
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

# ── ⭐⭐⭐⭐⭐ 本批的新件：`DOMRANK_JS`（**只读、从不调 `focus()`**）────────
#   `dom_rank` = 该元素在 `document.querySelectorAll('*')` 里的下标
#   ⭐ 它**不依赖任何 testid、不依赖任何「簇」** ⇒ 是最中立的「DOM 序」证据
DOMRANK_JS = """([nodeSel]) => {
  const el = document.activeElement;
  const all = document.querySelectorAll('*');
  if (!el) return {dom_rank: null, dom_path: null, is_body: null,
                   is_flow: null, tag: null, focusable: null,
                   tabindex: null, kind: null};
  // ⭐ `dom_rank` 用**全文档**下标 ⇒ 与 testid、与「哪一簇」全都无关
  let rank = -1;
  for (let i = 0; i < all.length; i += 1) { if (all[i] === el) { rank = i; break; } }
  const parts = [];
  let p = el, d = 0;
  while (p && d < 4) {
    const tid = p.getAttribute ? p.getAttribute('data-testid') : null;
    parts.push((p.tagName || '').toLowerCase() + (tid ? '#' + tid : ''));
    p = p.parentElement; d += 1;
  }
  return {
    dom_rank: rank,
    dom_path: parts.join('<'),
    is_body: el === document.body,
    is_flow: !!(el.classList && el.classList.contains('react-flow')),
    tag: (el.tagName || '').toUpperCase(),
    focusable: (el.tabIndex === undefined) ? null : (el.tabIndex >= 0),
    tabindex: el.getAttribute ? el.getAttribute('tabindex') : null,
    kind: (el.closest && el.closest(nodeSel)) ? 'self' : 'out'
  };
}"""

# ⭐⭐ 本批的新件：⛔ 计费守卫用的纯读件
POINT_JS = """([x, y]) => {
  const el = document.elementFromPoint(x, y);
  const host = el && el.closest('[data-testid]');
  return {tid: host ? host.getAttribute('data-testid') : null,
          al: (el.innerText || el.textContent || '').slice(0, 40)};
}"""

# ── ⭐⭐ 自证：新件必须真的读了「全文档下标」，且**只读**、**不调 focus** ──
assert "document.querySelectorAll('*')" in DOMRANK_JS, \
    "DOMRANK_JS 没读全文档下标"
assert "dom_rank" in DOMRANK_JS, "DOMRANK_JS 少了 dom_rank"
assert "dom_path" in DOMRANK_JS, "DOMRANK_JS 少了 dom_path"
assert "focus(" not in DOMRANK_JS, "DOMRANK_JS 不许调 focus()"
assert DOMRANK_JS.count("dom_rank:") >= 1
# ⚠️⚠️ 门必须挂在**独立分母**上：`querySelectorAll('*')` 取不到就恒 `-1`
assert "for (let i = 0; i < all.length; i += 1)" in DOMRANK_JS, \
    "DOMRANK_JS 的 dom_rank 循环被改过了 —— 这道门会恒 -1"

assert OWN_JS.count("kind:") >= 1, "OWN_JS 里没有 `kind` 字段"

_URL = "http://localhost:4317/jimeng/canvas/demo"

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
        raise AssertionError("⛔ 拦下计费控件：%r" % t)


def guard_point(x, y):
    at = ev(POINT_JS, [x, y])
    guard((at or {}).get("al"), (at or {}).get("tid"))
    return at


def boot_ck():
    """复刻侧就绪。⚠️ **「我没检测到」必须先确认「我够得着」**。"""
    page.goto(_URL, wait_until="domcontentloaded", timeout=90000)
    page.wait_for_timeout(6000)
    page.set_viewport_size({"width": 1512, "height": 1200})
    page.wait_for_timeout(2000)
    return ev("""() => ({
        has_flow: !!document.querySelector('.react-flow'),
        flow_aria: (document.querySelector('.react-flow') || {})
                      .getAttribute('aria-label'),
        flow_tabindex: (document.querySelector('.react-flow') || {})
                           .getAttribute('tabindex'),
        flow_tid: (document.querySelector('.react-flow') || {})
                     .getAttribute('data-testid'),
        n_focusable: document.querySelectorAll(
            '[tabindex="0"], a[href], button:not([disabled])').length
    })""")


out = {
    "target": "replica", "url": _URL, "reps": REPS, "rail_tid": RAIL_TID,
    "n_lead_cap": N_LEAD_CAP, "node_sel": NODE_SEL, "kinds": list(KINDS),
    "question": "⭐⭐⭐⭐⭐ **复刻的环序是不是「纯 DOM 序」**？"
                "⇒ 若是，**`rf__wrapper` 的位置差异就必然是 DOM 摆放差异"
                "（实现差异），不是口径差异** —— 972 悬的就是这件事",
    "ruler": {
        "js_verbatim_from_967": ["INSTALL_JS", "READ_JS", "OFF_NULL_JS",
                                 "BLANK_JS"],
        "js_verbatim_from_970": ["OWN_JS"],
        "how_proved": "⭐ `_grab(name, src)` 抠出那一段，再 `assert _s in _src`",
        "new_pieces": ["DOMRANK_JS", "POINT_JS"],
        "why_read_not_instrument": "⭐ `DOMRANK_JS` **只读属性**、"
                                   "**从不调 `focus()`** ⇒ 不污染焦点读数",
        "why_dom_rank_is_neutral": "⭐⭐⭐ `dom_rank` 取自 "
                                   "`document.querySelectorAll('*')` ⇒ "
                                   "**不依赖任何 `data-testid`、不依赖任何「簇」** "
                                   "⇒ 它是**最中立的「DOM 序」证据**",
        "insert_kinds": "⭐ 本批 `KINDS` 为空 ⇒ **零插入、零节点点击**",
    },
    "baseline": {
        "s972_source_ring": "⭐ 972 实测：源站环长 **18** 枚；"
                            "`rf__wrapper` 在 `用户菜单` 与 `文本` **之间**",
        "s972_replica_ring": "⭐ 970 实测：复刻环里 `rf__wrapper` 在"
                             "**接缝之后、`返回首页` 之前**",
        "s972_hypothesis": "⚠️ 972 的假说：复刻侧 `rf__wrapper` 的位置由"
                           "**DOM 位置**决定 —— 因为 `armRovingTabindex` "
                           "**只布 `.react-flow__node`、从不碰 `rf__wrapper`** "
                           "⇒ 它的 `tabindex` 来自 **xyflow 自己的静态属性**",
        "s972_no_product_change": "⚠️⚠️ **972 明确：本批之前不提出产品改动** ⇒ "
                                  "本批只测「是不是 DOM 序」，**不判该不该改**",
    },
    "runs": [],
}

for rep in range(1, REPS + 1):
    print(f"===== rep {rep} =====", flush=True)
    rec = {"rep": rep, "cells": []}
    out["runs"].append(rec)
    dump(out)

    rd = boot_ck()
    c = {"ci": 0, "mode": "walk", "rows": [],
         "n_install": 0, "n_read": 0, "n_rail_stops": 0,
         "n_lead_cap_hit": False, "has_flow": rd.get("has_flow"),
         "flow_aria": rd.get("flow_aria"),
         "flow_tabindex": rd.get("flow_tabindex"),
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
            dr = ev(DOMRANK_JS, [NODE_SEL])
        finally:
            ev(OFF_NULL_JS)
        row = {"k": c["n_lead"], "key": "Tab",
               "fired": (ap or {}).get("fired"),
               "landed": (ap or {}).get("landed"),
               "own": o, "dom": dr}
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
    # ⭐⭐⭐⭐⭐ **结构性修法（972/973 同一族栽到第五次）**：
    #   原来这里存的是 **`(k, row)` 二元组**，于是「把元组当 dict 用」这个错
    #   **可以安静地编译通过**、只在运行期炸。
    #   ⇒ **改成两个平行列表**（`out_ks` 存 k、`out_rows` 存 row）⇒
    #   **元组根本不再存在** ⇒ 这一族的坑从根上被拆掉。
    #   ⚠️⚠️ 972 加的那条「形状自证」**抓不到它** —— 因为错在**解包处**，
    #   不在元组形状 ⇒ ⭐⭐ **形状自证只挡「形状错」，挡不住「解包错」**
    out_rows = [r for r in rows if r["own"].get("kind") == "out"]
    out_ks = [r["k"] for r in out_rows]
    assert all(isinstance(r, dict) and "own" in r for r in out_rows), \
        "out_rows 里有不是 row-dict 的元素"

    # ── ⭐⭐⭐ 本批的正题：**环序是不是「纯 DOM 序」** ──────────────
    #   取**本段第一个 out 行起的连续一段**（走查不重试 ⇒ 一段 = 一圈）
    #   ⚠️⚠️ **不能靠「首遇重复就停」** —— 972/971 已证源站
    #   `搜索` 与 `生成历史` **共用一个 tid**，靠 tid 去重会**截断在 12**
    ranks = list(zip(out_ks, [(r.get("dom") or {}).get("dom_rank")
                               for r in out_rows]))
    c["dom_ranks"] = ranks
    c["n_out_presses"] = len(out_rows)
    # 找连续段起点：out 行在 `rows` 里应连续；用 k 的连续性判定
    arc = []
    for (k, rk) in ranks:
        if arc and k != arc[-1][0] + 1:
            break
        arc.append((k, rk))
    c["arc_len"] = len(arc)
    c["arc_ranks"] = [rk for _k, rk in arc]
    # ⭐⭐⭐ **单调性 + 回绕次数**（关系式，不钉绝对值）
    wraps, nonmono = 0, 0
    for i in range(1, len(arc)):
        a, b = arc[i - 1][1], arc[i][1]
        if a is None or b is None:
            nonmono += 1
            continue
        if b <= a:
            wraps += 1
    c["n_rank_descents"] = wraps
    c["n_rank_unknown"] = nonmono
    c["ring_follows_dom_order"] = (nonmono == 0 and wraps <= 1
                                    and len(arc) >= 10)
    # ⭐⭐⭐ **`rf__wrapper` 那枚的邻居**（972 问的就是这个）
    flow_idx = [i for i, r in enumerate(out_rows)
                if (r.get("dom") or {}).get("is_flow") is True]
    c["flow_seats"] = flow_idx

    def _nm(r):
        o = r.get("own") or {}
        t = o.get("closest_tid") or o.get("self_tid")
        return "%s/%s" % (o.get("tag"), t or ("<%s>" % (o.get("aria") or "?")))

    for i in flow_idx:
        lo, hi = max(0, i - 2), min(len(out_rows), i + 3)
        c.setdefault("flow_neighbourhood", []).append(
            {"seat": i, "k": out_ks[i],
             "window": [{"j": j, "name": _nm(out_rows[j]),
                         "dom_path": (out_rows[j].get("dom") or {}).get("dom_path"),
                         "dom_rank": (out_rows[j].get("dom") or {}).get("dom_rank")}
                        for j in range(lo, hi)]})
    c["arc_names"] = [_nm(r) for r in out_rows[:c["arc_len"]]]
    # ⭐⭐⭐⭐ **接缝的前一格能不能聚焦** —— 973 实测复刻那枚 `BODY` 的前一格
    #   是 `NEXTJS-PORTAL`（一个**浏览器无法聚焦**的 `<script>` 宿主元素）
    #   ⇒ 门 `body_predecessor_unfocusable_both_reps`
    body_i = [i for i, r in enumerate(out_rows)
              if (r.get("dom") or {}).get("is_body") is True]
    c["seam_pred_focusable"] = [
        {"seat": i,
         "prev_tag": ((out_rows[i - 1].get("dom") or {}).get("tag")
                      if i > 0 else None),
         "prev_focusable": ((out_rows[i - 1].get("dom") or {}).get("focusable")
                            if i > 0 else None),
         "self_tag": (out_rows[i].get("dom") or {}).get("tag"),
         "self_rank": (out_rows[i].get("dom") or {}).get("dom_rank"),
         "prev_rank": ((out_rows[i - 1].get("dom") or {}).get("dom_rank")
                       if i > 0 else None)}
        for i in body_i]
    c["body_predecessor_unfocusable"] = bool(body_i) and all(
        x["prev_focusable"] is False for x in c["seam_pred_focusable"])
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
    _c0.get("arc_names") == _c1.get("arc_names")
    and _c0.get("arc_ranks") == _c1.get("arc_ranks"))

out["design_gates"] = {
    # ① ⭐⭐⭐⭐⭐ **环序 = DOM 序**（这才是 972 悬着的那件事的答案）
    "ring_follows_dom_order_both_reps": _both(
        lambda c: c.get("ring_follows_dom_order") is True),
    # ② ⭐⭐⭐⭐ `dom_rank` **真的读到了**（防恒 `-1` ⇒ 防这道门空转）
    "dom_rank_is_live_both_reps": _both(
        lambda c: (c.get("n_rank_unknown") == 0)
        and all(r is not None and r >= 0
                for r in (c.get("arc_ranks") or []))),
    # ③ ⭐⭐⭐⭐ **回绕恰好 ≤ 1 次**（一圈只该绕一次）
    "at_most_one_wrap_both_reps": _both(
        lambda c: (c.get("n_rank_descents") or 0) <= 1),
    # ④ ⭐⭐⭐⭐ **`rf__wrapper` 那枚被找到了**（972 问的就是它）
    #    ⭐⭐ `all()` 在空列表上恒真 ⇒ 分母**先钉非空**
    "flow_stop_is_live_both_reps": _both(
        lambda c: len(c.get("flow_seats") or []) >= 1),
    # ⑤ ⭐⭐⭐ **`rf__wrapper` 的 `tabindex` 不是本实现布的**
    #    （`armRovingTabindex` 只布 `.react-flow__node` ⇒ 证它是 xyflow 自带的）
    "flow_tabindex_is_static_both_reps": _both(
        lambda c: str(c.get("flow_tabindex")) in ("0", "-1", "None")),
    # ⑥ ⭐⭐⭐⭐⭐ **接缝的前一格是「浏览器无法聚焦」的元素**
    #    （本批实测：复刻那枚 `BODY` 前面是 `NEXTJS-PORTAL` —— 一个
    #    **`<script>` 的宿主自定义元素**，浏览器聚焦不了它 ⇒ 焦点掉回 `body`）
    #    ⇒ ⇒ ⭐⭐ **复刻侧那枚 `BODY` 很可能是开发态产物的连带效应**，
    #    而 §182「两侧是同一条环」那句话**要打折扣**
    "body_predecessor_unfocusable_both_reps": _both(
        lambda c: c.get("body_predecessor_unfocusable") is True),
    "ring_order_agrees_across_reps": bool(
        out["reps_agree"] and _c0.get("arc_names")),
    "fired_eq_rows_both_reps": _both(lambda c: c.get("fired_eq_rows") is True),
    "listener_balanced_both_reps": _both(
        lambda c: c.get("listener_balanced") is True),
}

RAW_KEYS = {"k", "fired", "landed", "own", "dom"}
DERIVED_KEYS = {"dom_ranks", "arc_len", "arc_ranks", "n_rank_descents",
                "n_rank_unknown", "ring_follows_dom_order", "flow_seats",
                "flow_neighbourhood", "arc_names"}
out["keys_disjoint"] = bool(not (RAW_KEYS & DERIVED_KEYS))

out["recon"] = {
    "rep%d" % i: {
        "n_rows": c.get("n_rows"),
        "arc_len": c.get("arc_len"),
        "arc_ranks": c.get("arc_ranks"),
        "dom_ranks": c.get("dom_ranks"),
        "body_predecessor_unfocusable": c.get("body_predecessor_unfocusable"),
        "seam_pred_focusable": c.get("seam_pred_focusable"),
        "n_out_presses": c.get("n_out_presses"),
        "n_rank_descents": c.get("n_rank_descents"),
        "n_rank_unknown": c.get("n_rank_unknown"),
        "ring_follows_dom_order": c.get("ring_follows_dom_order"),
        "flow_seats": c.get("flow_seats"),
        "flow_tabindex": c.get("flow_tabindex"),
        "flow_tid": c.get("flow_tid"),
        "flow_aria": c.get("flow_aria"),
        "n_focusable_at_boot": c.get("n_focusable_at_boot"),
        "arc_names": c.get("arc_names"),
        "flow_neighbourhood": c.get("flow_neighbourhood"),
        "fired_eq_rows": c.get("fired_eq_rows"),
        "listener_balanced": c.get("listener_balanced"),
    }
    for i, c in enumerate(r["cells"][0] for r in out["runs"])
}

out["gate_notes"] = (
    "⭐ 973 的门围绕「**环序 = DOM 序**」与「**`dom_rank` 是不是活读数**」：\n"
    "  · `dom_rank_is_live_both_reps` 要求**每个**下标都 `>= 0` —— "
    "`querySelectorAll('*')` 找不到元素时 `rank` 会停在 `-1` ⇒ "
    "**那道自证门恒红**，而不会让整条链安静地空转；\n"
    "  · `at_most_one_wrap_both_reps` 钉的是**回绕次数**（关系式），"
    "**不是**任何绝对下标 ⇒ 源站/复刻逐轮 DOM 都在动也不影响；\n"
    "  · `flow_stop_is_live_both_reps` 的分母**先钉非空** —— "
    "`all([])` 是恒真（972 刚为这条栽过一次）。")

out["what_973_measures"] = (
    "① ⭐⭐⭐⭐⭐ 给每个 out 段停靠点记 `dom_rank`（**全文档**下标，"
    "**不依赖 testid、不依赖「簇」**）与 `dom_path`（向上 4 层的容器链）\n"
    "  ⇒ 于是「环序是不是 DOM 序」变成一条**可证伪的关系式**；\n"
    "  ② ⭐⭐⭐ **`rf__wrapper` 那枚的座位与邻居**（972 问的就是它）；\n"
    "  ③ ⭐⭐ 画布根的 `tabindex` / `data-testid` / `aria-label` "
    "（**反证 `armRovingTabindex` 从不碰它** —— 那是 972 的假说前提）；\n"
    "  ⇒ ⇒ **只回答「环序的来源是什么」，不判「该不该改」**")

out["discipline_973"] = (
    "① ⭐⭐⭐⭐⭐ **把上批的「假说」变成一条可证伪的关系式** —— "
    "967 写「复刻按纯 DOM 序」时**是靠步长推的**；"
    "步长对得上**不等于**顺序的来源被证实过 ⇒ "
    "本批直接读**全文档下标**（**最中立**，不依赖 testid）；\n"
    "  ② ⭐⭐⭐ **证据的粒度要匹配断言的粒度** —— "
    "「环序」是**顺序**命题 ⇒ 证据必须是**顺序**（单调性 + 回绕次数），"
    "**不是**「集合相等」；\n"
    "  ③ ⭐⭐⭐ **`all([])` 是恒真** ⇒ 每一道「全部都是……」的门"
    "**分母都要先钉非空**（972 刚栽过）；\n"
    "  ④ ⭐⭐ **读数恒为一个哨兵值时要判红** —— `dom_rank` 恒 `-1` "
    "会让整条链**安静空转** ⇒ 自证门与主门成对；\n"
    "  ⑤ ⭐⭐ **`DOMRANK_JS` 只读属性、从不调 `focus()`**；\n"
    "  ⑥ ⭐⭐ **零插入、零节点点击、零计费**：按键只有 `Tab`，"
    "⛔ 守卫拦在 `mouse.click` 之前")

out["skip_note"] = (
    "⚠️ 本探针**只测复刻侧** ⇒ 「两侧是不是同一条 DOM 序」**不能**由它单独下结论；"
    "源站那一侧见 972（源站 `rf__wrapper` 在 `用户菜单` 与 `文本` 之间）⇒ "
    "**两侧各测一轮、再对齐**，才是完整的一对。")

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1, default=str)
print("已写出 %s" % OUT, flush=True)
print("design_gates: %s" % json.dumps(out["design_gates"], ensure_ascii=False),
      flush=True)
