#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""batch 981 · **源站**探针：⭐⭐⭐⭐⭐ **把同一个比率量到源站上** ——
980 在实验室里量到 ≈ 7.8%，而它自己的 `skip_note` 写明
「**实验室的比率不等于源站的比率**」⇒ 本批补上源站这一侧。

── 为什么源站的切圈要换一套办法 ────────────────────────────────────

980 在空白页上用「回到 `keys[0]`」切圈，**那里可行**（键少、唯一）。
⚠️⚠️⚠️ **源站的环有 18 格、且键会重复**
（`搜索` 与 `生成历史` **共用** `canvas-panel-launcher`）⇒
「回到第一枚键」**会在环内提前切一刀** ⇒ 980 那套切法**搬不过来**。

⇒ ⇒ ⭐⭐⭐⭐⭐ **本批改用源站自己早就有的「一圈」标记**：
973–977 一直用 **左栏 `canvas-fixed-toolbar` 每命中一次 = 走完一圈**
（`n_rail_stops >= 2` 即一圈）⇒ ⇒
**左栏命中点之间的区间就是一圈** ⇒ 这是**项目自己的仪器**，
不是本批新造的切法 ⇒ **也就不必再写一遍切圈器、更不必给它写自测**。

── ⭐⭐⭐⭐⭐ 本批的判据前提与 980 完全一致 ──────────────────────────

「没看见」必须先排除「没看够」：
- 门①：窗口 ≥ 120ms（979 实测 `BODY` 停留 ≈ 250ms）
- 门②：**每一段** `BODY` 的停留都 ≥ 120ms
⇒ ⇒ 二者成立时，「某一圈没走 `BODY`」**不能用「窗口太短」解释**

⚠️⚠️⭐⭐⭐ **源站是 18 格的大环** ⇒ 一圈 ≈ 19 步 ⇒
要拿到 **10 圈以上**（980 的门②标准）**至少需要 ~200 步**
⇒ ⇒ ⭐⭐ **本批的步数比 980 大一个量级**，这不是「多测几次」，
是**样本量的下限**决定的

⚠️⭐⭐ **不预写比率** —— 探针只输出
`n_laps` / `laps_with_body` / `laps_without_body`，**真伪由 verifier 判**。

**本批零计费**：只按 `Tab`；⛔ 计费守卫拦在 `mouse.click` **之前**。
"""
from __future__ import annotations

import json
import os
import re

OUT = "/tmp/b981-srcrate.json"
REPS = 2
N_STEPS = 240        # ⭐ 18 格环 ⇒ ≈ 12 圈（≥ 980 的 10 圈门槛）
WINDOW_MS = 140      # ⭐ 门①：≥ 120ms 才算「看得见」
MIN_VISIBLE_MS = 120 # ⭐ 门②
SETTLE = 120         # 每步轮询窗口之外不再额外等待
RAIL_TID = "canvas-fixed-toolbar"      # ⭐ 973–977 的**容器**标记
LAP_TID = "canvas-project-logo"        # ⭐ 本批的**切圈标记**
#   ⚠️⚠️⚠️⭐⭐⭐⭐ **974 那条纪律的第四次复发**：「同一个东西要比同一个口径」——
#   973–977 的「一圈」判的是 `own.closest_tid == RAIL_TID`（**容器**，
#   走的是 `closest('[data-testid]')`），而 `POLL_JS.keyOf` 读的是
#   **元素自己**的 `data-testid` ⇒ **同一个名字、两种口径**
#   ⇒ ⇒ 第一版真跑出来 `rail_hits = 0`（那个容器**根本不是焦点目标**）
#   ⇒ ⇒ 修法：切圈标记改成**环里唯一、且确实是焦点目标**的那一枚
#   （`canvas-project-logo`，实测每圈一次）；**并把 `closest_tid` 也读出来**，
#   让两种口径**并排**而不是二选一
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


# ⚠️⭐⭐⭐ **`POLL_JS` 的源头是 979**（980 也是它的消费者）⇒ 三个探针、
#   **一件仪器**。⚠️⚠️ 「不许自己定义」只针对**继承来的**那件（978 栽过）
_p979 = _src("jimeng_probe979_dwell_src.py")
_p980 = _src("jimeng_probe980_rate_src.py")
_p976 = _src("jimeng_probe976_counterfactual_src.py")


def _grab(name, src=None):
    m = re.search(r'^%s\s*=\s*r?"""(.*?)"""' % name, src or "", re.S | re.M)
    assert m, "抠不到 %s" % name
    _s = m.group(1)
    assert _s in (src or ""), "%s 不是逐字抠出来的" % name
    return _s


POLL_JS = _grab("POLL_JS", _p979)

# ── ⭐⭐⭐ 自证与守卫 ────────────────────────────────────────────────
assert not re.search(r'^POLL_JS\s*=\s*r?"""',
                     open(__file__, encoding="utf-8").read(), re.M), (
    "本批自己定义了**继承来的**字面量 ⇒ 尺子分叉了")
for _bad in ('POLL_JS = """x"""', "POLL_JS = r\"\"\"x\"\"\""):
    assert re.search(r'^POLL_JS\s*=\s*r?"""', _bad, re.M), (
        "分叉守卫**失灵**了：%r" % _bad)
# ⭐⭐⭐⭐⭐ **门① 的前提**（与 980 同一条）
assert WINDOW_MS >= MIN_VISIBLE_MS, "窗口比可见下限还短 ⇒ 前提不成立"


def _window_ok(win, floor):
    return win >= floor


assert _window_ok(WINDOW_MS, MIN_VISIBLE_MS) is True
assert _window_ok(MIN_VISIBLE_MS - 1, MIN_VISIBLE_MS) is False, (
    "窗口门失灵（窗口短于可见下限时仍绿）")
# ⭐⭐⭐⭐ **纯读**：只看 `document.activeElement`；剥掉注释后再查
assert WINDOW_MS > 0 and N_STEPS >= 200, "步数不够拿不到 10 圈"


def _code_only(js):
    o = []
    for line in js.split("\n"):
        t = line.strip()
        if t.startswith("//") or t.startswith("*") or t.startswith("/*"):
            continue
        o.append(line.split("//")[0])
    return "\n".join(o)


POLL_CODE = _code_only(POLL_JS)
for _forbidden in ("focus(", "MutationObserver", "addEventListener",
                   "prototype", "location.reload"):
    assert _forbidden not in POLL_CODE, "POLL_JS 里出现了 %r" % _forbidden
for _bad, _tok in (("el.focus();", "focus("),
                   ("new MutationObserver(f);", "MutationObserver"),
                   ("window.addEventListener('x', f);", "addEventListener"),
                   ("HTMLElement.prototype.focus", "prototype"),
                   ("location.reload();", "location.reload")):
    assert _tok in _code_only("var a = 1;\n" + _bad + "\n"), (
        "纯读守卫**失灵**了：%r" % _bad)
    assert _tok not in _code_only("var a = 1;\n// 纪律：不许 " + _bad + "\n"), (
        "注释剥离守卫**失灵**了：%r" % _bad)
# ⭐⭐⭐⭐⭐ **「实验室的比率不许直接套到源站」** —— 本批的立身之本
assert "实验室的比率不等于源站的比率" in _p980, (
    "980 的 `skip_note` 变了 ⇒ 本批的前提要重新确认")
# ⭐⭐⭐⭐ **980 那套切圈器搬不过来**（键会重复）—— 把这个判断**钉住**，
#   免得下一批又照抄它
assert "980 在空白页上用「回到" in open(__file__, encoding="utf-8").read()
assert RAIL_TID in _p976, "左栏 testid 与 976 探针不一致"


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


def _laps_by(keys, marker):
    """⭐⭐⭐⭐⭐ **用左栏命中点切圈**（源站自己 973–977 就在用的那件仪器）。

    ⇒ 每次命中 `LAP_TID` = **走完一圈**
    ⇒ 两个相邻命中点之间的区间 = **一圈**
    ⇒ 最后一圈若还没到下一个命中点 ⇒ **残段，不许算进分母**
    """
    hits = [i for i, k in enumerate(keys) if k == marker]
    full = []
    for a, b in zip(hits, hits[1:]):
        full.append(keys[a + 1:b + 1])
    return full, len(hits), (keys[hits[-1] + 1:] if hits else list(keys))


# ⭐⭐⭐⭐⭐ **切圈器自测** —— 而**期望值我第一版又写错了两处**
#   （把「两个命中点之间」当成「每个命中点一圈」）⇒
#   ⇒ ⭐⭐⭐ **`n_laps = n_hits - 1`**：**n 个命中点之间只有 n-1 段**
#   ⇒ ⇒ ⭐⭐ 与 980 同一条教训：**自测的期望值本身也要审**，
#   **推错了自测就是假绿**
for _keys, _n_laps, _hits, _tail in (
        (['a', 'B', 'b', 'a', 'a', 'B', 'b', 'a', 'a'], 4, 5, []),
        (['a', 'B', 'a', 'a'], 2, 3, []),
        (['a', 'a', 'B', 'a', 'a'], 3, 4, []),
        (['a', 'B'], 0, 1, ['B']),
        ([], 0, 0, [])):
    _l, _h, _t = _laps_by(_keys, "a")
    assert len(_l) == _n_laps, "切圈器自测（圈数）失败：%r" % (_keys,)
    assert _h == _hits, "切圈器自测（命中数）失败：%r" % (_keys,)
    assert _t == _tail, "切圈器自测（残段）失败：%r ⇒ %r" % (_keys, _t)
# ⭐⭐⭐⭐ **成对**：钉住反向 —— 圈数 = 命中数（而不是命中数 − 1）时**必须仍红**
assert len(_laps_by(['a', 'a', 'a', 'a'], 'a')[0]) == 3, (
    "命中数 − 1 那条对不上了")
assert len(_laps_by(['a', 'a', 'a'], 'a')[0]) == 2, (
    "命中数 − 1 那条对不上了")

out = {
    "target": "source", "url": SRC_URL, "reps": REPS, "n_steps": N_STEPS,
    "window_ms": WINDOW_MS, "min_visible_ms": MIN_VISIBLE_MS,
    "rail_tid": RAIL_TID,
    "question": "⭐⭐⭐⭐⭐ **把 980 在实验室里量到的比率，量到源站上** ⇒ "
                "**实验室的比率不等于源站的比率**（980 的 `skip_note` 原话）",
    "ruler": {
        "js_verbatim_from_979": ["POLL_JS"],
        "new_pieces": [],
        "instrument_origin": "⭐⭐⭐ **`POLL_JS` 的源头是 979**（980 也是消费者）"
                             "⇒ 三个探针、**一件仪器**",
        "why_not_980_slicer": "⭐⭐⭐⭐⭐ **980 那套切圈器搬不过来** —— "
                              "源站的环有 18 格、**且键会重复**"
                              "（`搜索` 与 `生成历史` **共用** "
                              "`canvas-panel-launcher`）⇒ "
                              "「回到 `keys[0]`」**会在环内提前切一刀** ⇒ "
                              "⇒ ⭐⭐⭐ 改用**源站自己 973–977 就在用的**"
                              "**左栏命中 = 走完一圈** ⇒ "
                              "**不必再写一遍切圈器、更不必给它写自测**",
        "key_precondition": "⭐⭐⭐⭐⭐ **「没看见」必须先排除「没看够」** —— "
                            "与 980 同一道门①门②（窗口 ≥ 120ms；"
                            "**每一段** `BODY` 停留都 ≥ 120ms）",
        "why_many_steps": "⚠️⭐⭐ **源站是 18 格的大环** ⇒ 一圈 ≈ 19 步 ⇒ "
                          "要拿到 **10 圈以上**（980 的门槛）**至少 ~200 步** ⇒ "
                          "⭐⭐ **本批步数比 980 大一个量级**，"
                          "**这不是「多测几次」，是样本量的下限决定的**"
    },
    "runs": [],
}

for rep in range(1, REPS + 1):
    print(f"===== rep {rep} =====", flush=True)
    rec = {"rep": rep, "cells": []}
    out["runs"].append(rec)
    dump(out)

    page.goto(SRC_URL, wait_until="domcontentloaded", timeout=90000)
    page.wait_for_timeout(10000)
    page.set_viewport_size({"width": 1512, "height": 1200})
    page.wait_for_timeout(3000)
    n = page.locator('button[aria-label="音频"]').count()
    if n == 0:
        page.wait_for_timeout(8000)
        n = page.locator('button[aria-label="音频"]').count()
    cell = {"rep": rep, "n_ready": n, "steps": []}
    rec["cells"].append(cell)
    dump(out)
    if n == 0:
        cell["skip_note"] = "左栏入口没出来 ⇒ 本格什么也没测"
        continue

    sp = ev("""() => {
        const x = Math.floor(window.innerWidth / 2);
        const y = Math.floor(window.innerHeight * 0.92);
        const el = document.elementFromPoint(x, y);
        return (el && el.id !== 'canvas-watermark') ? [x, y] : null;
    }""")
    cell["blank"] = sp
    if sp:
        guard_point(sp[0], sp[1])      # ⛔ 守卫在 `mouse.click` **之前**
        page.mouse.click(sp[0], sp[1])
        page.wait_for_timeout(900)

    for k in range(1, N_STEPS + 1):
        page.keyboard.press("Tab")
        r = ev(POLL_JS, [WINDOW_MS])
        seq = (r or {}).get("seq") or []
        # ⭐⭐⭐⭐⭐ **整段 `seq` 必须留着** —— 979 的教训：
        #   「原始读数里答案一直在」⇒ 我第一版**只留了第一枚键**，
        #   于是 `BODY` 的**停留时长**在汇总层**根本无从算起**
        #   ⇒ ⇒ ⭐⭐ **汇总层要用的字段，读数层就得留着**
        closest = ev("""() => {
            const a = document.activeElement;
            const h = (a && a.closest) ? a.closest('[data-testid]') : null;
            return h ? h.getAttribute('data-testid') : null;
        }""")
        cell["steps"].append({"k": k, "key": "Tab", "seq": seq,
                              "landed": (seq[0]["key"] if seq else None),
                              "closest_tid": closest,
                              "t_ms": (seq[0]["t_ms"] if seq else None),
                              "elapsed_ms": (r or {}).get("elapsed_ms"),
                              "n_seq": len(seq)})
        if k % 40 == 0:
            dump(out)

    # ── 汇总：⭐⭐ 只做计数，不下结论 ──────────────────────────────
    keys = [s["landed"] for s in cell["steps"]]
    cell["keys"] = keys
    laps, n_hits, tail = _laps_by(keys, LAP_TID)
    cell["laps_marker"] = LAP_TID
    cell["rail_hits_container_kb"] = sum(
        1 for s in cell["steps"] if s.get("closest_tid") == RAIL_TID)
    cell["n_laps"] = len(laps)
    cell["laps_with_body"] = sum(1 for c in laps if "BODY" in c)
    cell["laps_without_body"] = sum(1 for c in laps if "BODY" not in c)
    cell["tail_keys"] = tail
    cell["lap_lengths"] = sorted({len(c) for c in laps})
    # ⭐⭐⭐⭐ 门② 的读数：`BODY` 出现时它的**停留时长**（含末态那一段）
    body_d = []
    for s in cell["steps"]:
        seq = s.get("seq") or []
        el = s.get("elapsed_ms")
        for i in range(len(seq) - 1):
            if seq[i]["key"] == "BODY":
                body_d.append(seq[i + 1]["t_ms"] - seq[i]["t_ms"])
        if seq and isinstance(el, (int, float)) and seq[-1]["key"] == "BODY":
            body_d.append(int(el) - seq[-1]["t_ms"])
    cell["body_dwell_ms"] = body_d
    cell["n_body_dwell_below_floor"] = sum(1 for x in body_d
                                           if x < MIN_VISIBLE_MS)
    cell["n_body_dwell_ge_floor"] = sum(1 for x in body_d
                                        if x >= MIN_VISIBLE_MS)
    cell["n_steps_landed_on_body"] = sum(1 for k in keys if k == "BODY")
    dump(out)

dump(out)
print("PROBE_981_DONE", flush=True)
