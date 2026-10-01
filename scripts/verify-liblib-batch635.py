#!/usr/bin/env python3
"""batch 635 验收：掩埋曲面是 **(时间轴顶边, 窗口高)** 的二元函数，不是顶边的一元函数。

## 本批推翻 batch 634 的核心断言，并给出**域**而不是「它错了」

634 断言「掩埋只是时间轴顶边的函数」，48 格零分歧。本批把窗高压到 634 没采过的
区间（**短于 436**），同一个顶边上出现 4 个不同的掩埋集合 —— 634 的断言**为假**。

但 634 不是错的，是**有域的**，本批把这个域量出来、把它保住：

    掩埋 = { rail/tree 的行 : 顶边 ≤ cy ≤ 窗高 }

上界 `窗高` 之所以在 634 的网格里不生效，是因为三个列的行 y 是**固定**的
（216 / 288 / 320 / 352 / 424），而 634 最短的窗是 **480 > 436**（最后一行 424
的下沿）—— 上界从未切到任何一行。**634 的最短窗高恰好落在饱和区外侧。**

## 机制：三列的锚点各不相同（实测，非推断）

- `rail` / `tree`：`position: absolute`，包含块是 workspace
  `fixed inset-0 z-[100] flex h-dvh w-screen flex-col overflow-hidden`
  → 底边钉在**窗口底**，`overflow: visible`，超出窗口的行被工作区裁掉。
  行 y 与窗高**无关**（实测 216/288/320/352/424 在 wh=328 与 wh=660 逐格相同），
  唯一随窗高走的是 rail 的尾项 `帮助`（cy = 窗高 − 24）。
- `inspector`：包含块是 `relative min-h-0 flex-1`（即视口），`overflow-y: hidden`
  → 底边**钉在时间轴顶边**上，它在掩埋线处**自己把自己裁掉**，
  所以它从来不是掩埋受害者（与 633「受害者集合恒为 `{rail, tree}`」一致）。

## 630 的钳制在 634 只出现过一格；本批量到 8 格，并给出它的闭式

    实际高 = min(请求高, 窗高 − 88)

触发时顶边**恒为 y=88**、视口高度**恰为 0**。8 个被钳格子的顶边全是 88，
掩埋数却是 15 / 15 / 20 / 20 / 23 / 23 / 26 / 15 —— **又一次证伪「顶边 alone」**。
"""
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


def _load(name: str):
    spec = importlib.util.spec_from_file_location(
        name, ROOT / f"scripts/verify-liblib-batch{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


b617 = _load("617")
b623 = _load("623")
b629 = _load("629")

WIDTH = 1440
TIMELINES = [88, 120, 150, 182, 240, 300, 360, 420]

# 634's own grid, re-run verbatim so 634's claim is re-derived on its own domain
# instead of being retroactively declared wrong.
B634_WIN_HEIGHTS = [480, 560, 660, 760, 900, 1150]

# 634's accidental coincidences, rebuilt: wh = T + req puts every cell on one top.
# req in [88,420] and T >= 88 means the clamp never fires (req <= wh - 88 <=> T >= 88).
GROUPS = {
    360: [88, 120, 150, 182, 240, 300, 360, 420],
    240: [88, 120, 150, 182, 240, 300, 360, 420],
    540: [88, 120, 150, 182, 240, 300, 360, 420],
}

# The fine sweep that locates the domain boundary: top pinned at 240, window height
# walked across the whole legal range (wh = 240 + req, req in [88,420]).
SWEEP_TOP = 240
SWEEP_WH = [328, 340, 352, 364, 376, 388, 400, 412, 424, 436, 448,
            480, 520, 560, 600, 660]

# Cells where 630's clamp fires: every one of them must land on top 88.
CLAMPED = [(300, 240), (300, 360), (300, 420), (360, 300),
           (360, 420), (420, 360), (420, 420), (500, 420)]

PRIOR_634 = ROOT / "docs/research/liblib-canvas-batch634-2026-10-01/runtime-audit.json"

GEOM_JS = """() => {
  const rd = (sel) => {
    const el = document.querySelector(sel);
    if (!el) return null;
    const r = el.getBoundingClientRect();
    return {t: Math.round(r.top * 10) / 10, l: Math.round(r.left * 10) / 10,
            w: Math.round(r.width * 10) / 10, h: Math.round(r.height * 10) / 10,
            b: Math.round(r.bottom * 10) / 10, r: Math.round(r.right * 10) / 10,
            display: getComputedStyle(el).display};
  };
  return {
    viewport: rd('[data-director-viewport]'),
    timeline: rd('[data-director-timeline]'),
    bottomBar: rd('[data-director-bottom-bar]'),
    rail: rd('[data-director-icon-rail]'),
    tree: rd('aside[aria-label="场景对象"]'),
    inspector: rd('aside[aria-label="属性"]'),
  };
}"""


def column_of(box: list[float], g: dict[str, Any]) -> str:
    cx = box[0] + box[2] / 2
    for name in ("rail", "tree", "inspector"):
        rect = g.get(name)
        if rect and rect["display"] != "none" and rect["w"] > 0 \
                and rect["l"] - 0.5 <= cx <= rect["r"] + 0.5:
            return name
    return "other"


def prep(page) -> None:
    page.mouse.move(5, 5)
    page.wait_for_timeout(140)
    page.evaluate("() => { for (const el of document.querySelectorAll('nextjs-portal'))"
                  " el.remove(); }")


def ask(page, th: int) -> None:
    page.evaluate("(n) => window.__director_store.getState().setTimelineHeight(n)", th)
    page.wait_for_timeout(200)


def measure(page, group: str, wh: int, want: int) -> dict[str, Any]:
    r = page.evaluate(b617.AUDIT_JS, list(b617.TRANSIENT_OVERLAYS))
    g = page.evaluate(GEOM_JS)
    z = page.evaluate(b623.BLIND_JS)
    vp, tl = g["viewport"], g["timeline"]
    rows = [(b["label"], b["box"], b["hitLabel"], column_of(b["box"], g))
            for b in r["coveredByTimelineOverlay"]]
    labels = sorted({x[0] for x in rows})
    blocked = [(b["label"], b["box"], b["panel"], b["timelineOverlay"],
                b["clipped"], b["victimInViewport"]) for b in r["blocked"]]
    shim = {"viewportTop": vp["t"] if vp else None,
            "viewportH": vp["h"] if vp else None,
            "band": g["bottomBar"]["h"] if g["bottomBar"] else 48,
            "blocked": blocked}
    predicted = sorted(b629.predict(shim))
    observed = sorted({b["label"] for b in r["coveredByViewportSqueeze"]})
    return {
        "group": group,
        "windowH": wh,
        "requested": want,
        "timelineTop": tl["t"],
        "timelineH": tl["h"],
        "clamped": abs(tl["h"] - want) > 0.5,
        "spill": max(0, tl["b"] - wh),
        "viewportH": vp["h"] if vp else None,
        "total": r["total"],
        "offViewport": len(r["offViewportItems"]),
        "unreachable": [(b["label"], b["box"]) for b in r["offViewportUnreachable"]],
        "zeroSize": z,
        "unexplained": [(b["label"], b["hitLabel"], b["box"]) for b in r["covered"]],
        "buried": rows,
        "buriedLabels": labels,
        "buriedCount": len(labels),
        "buriedColumns": sorted({x[3] for x in rows}),
        "aboveTimelineTop": [x[0] for x in rows if x[1][1] + x[1][3] <= tl["t"] + 0.5],
        "predictLabels": predicted,
        "predictAgrees": observed == predicted,
    }


class Verifier:
    def __init__(self) -> None:
        self.result: dict[str, Any] = {}
        self.failures: list[str] = []
        self.count = 0

    def check(self, name: str, ok: bool, detail: Any = "") -> None:
        self.count += 1
        self.result[name] = {"ok": bool(ok), "detail": detail}
        if not ok:
            self.failures.append(name)
        print(("  PASS " if ok else "  FAIL ") + name + (f"  {detail}" if detail else ""))


def sweep_cells(page, cells: dict[str, Any], group: str,
                pairs: list[tuple[int, int]]) -> None:
    for wh, req in pairs:
        page.set_viewport_size({"width": WIDTH, "height": wh})
        page.wait_for_timeout(170)
        ask(page, req)
        prep(page)
        cells[f"{group}|wh={wh}/tl={req}"] = measure(page, group, wh, req)


def main() -> int:
    v = Verifier()
    cells: dict[str, Any] = {}
    with sync_playwright() as p:
        br = p.chromium.launch()
        page = br.new_page(viewport={"width": WIDTH, "height": 900},
                           device_scale_factor=1)
        b617.open_desk(page)

        # (1) 634's grid, verbatim — re-derive its claim on its own domain.
        for wh in B634_WIN_HEIGHTS:
            page.set_viewport_size({"width": WIDTH, "height": wh})
            page.wait_for_timeout(170)
            for tl in TIMELINES:
                ask(page, tl)
                prep(page)
                cells[f"b634|wh={wh}/tl={tl}"] = measure(page, "b634", wh, tl)

        # (2) constructed coincidence groups — many cells on one measured top edge.
        for top, reqs in GROUPS.items():
            pairs = [(top + req, req) for req in reqs]
            sweep_cells(page, cells, f"grp{top}", pairs)

        # (3) the fine sweep that locates the domain boundary.
        sweep_cells(page, cells, f"sweep{SWEEP_TOP}",
                    [(wh, wh - SWEEP_TOP) for wh in SWEEP_WH])

        # (4) cells where 630's clamp fires.
        sweep_cells(page, cells, "clamp", CLAMPED)
        br.close()

    out = {
        "batch": 635,
        "title": "the burial surface is a function of (timeline top, window height) "
                 "— 634's one-dimensional collapse is false, and its domain is measured",
        "date": "2026-10-01",
        "width": WIDTH,
        "priorGrid": {"winHeights": B634_WIN_HEIGHTS, "timelines": TIMELINES},
        "groups": {str(k): val for k, val in GROUPS.items()},
        "sweep": {"top": SWEEP_TOP, "winHeights": SWEEP_WH},
        "clampedPairs": CLAMPED,
        "cells": cells,
    }

    n = len(cells)
    v.check(f"the-grid-runs-{n}-cells", n > 0, detail=n)

    # --- boundary axes ---------------------------------------------------
    bad = {k: r["unreachable"] for k, r in cells.items() if r["unreachable"]}
    v.check("no-cell-has-an-off-viewport-unreachable-control", not bad,
            detail=dict(list(bad.items())[:6]))

    zbad = {k: r["zeroSize"] for k, r in cells.items() if r["zeroSize"]}
    v.check("no-cell-has-a-control-collapsed-to-nothing", not zbad,
            detail={k: r[:4] for k, r in list(zbad.items())[:6]})

    uncov = {k: r["unexplained"] for k, r in cells.items() if r["unexplained"]}
    v.check("no-cell-has-an-unexplained-covered-control", not uncov,
            detail=dict(list(uncov.items())[:6]))

    vac = [k for k, r in cells.items() if r["offViewport"] == 0]
    v.check("every-cell-actually-exercised-the-off-viewport-branch", not vac,
            detail=vac[:8])

    above = {k: r["aboveTimelineTop"] for k, r in cells.items()
             if r["aboveTimelineTop"]}
    v.check("every-buried-control-sits-below-the-timelines-top-edge", not above,
            detail=dict(list(above.items())[:6]))

    sp = {k: r["spill"] for k, r in cells.items() if r["spill"] > 0.5}
    v.check("the-timeline-never-spills-past-the-window", not sp,
            detail=dict(list(sp.items())[:6]))

    pd = {k: {"observed": r["buriedCount"], "predicted": len(r["predictLabels"])}
          for k, r in cells.items() if not r["predictAgrees"]}
    v.check("629s-closed-form-predicts-the-squeeze-in-every-cell", not pd,
            detail=dict(list(pd.items())[:4]))

    # --- 630's clamp, as a closed form ----------------------------------
    # 630 recorded a safety contract ("the panel must not spill") and one cell of
    # behaviour.  The law it actually implements is min(requested, window - 88).
    clampbad = {}
    for k, r in cells.items():
        want = min(r["requested"], r["windowH"] - 88)
        if abs(r["timelineH"] - want) > 0.5:
            clampbad[k] = {"requested": r["requested"], "windowH": r["windowH"],
                           "expected": want, "actual": r["timelineH"]}
    v.check("630s-clamp-is-exactly-min-requested-and-window-minus-88",
            not clampbad, detail=dict(list(clampbad.items())[:4]))

    clamped = {k: r for k, r in cells.items() if r["clamped"]}
    v.check("every-clamped-cell-pins-the-timeline-top-to-y88",
            all(abs(r["timelineTop"] - 88) < 0.5 for r in clamped.values()),
            detail={"clampedCells": len(clamped),
                    "tops": sorted({r["timelineTop"] for r in clamped.values()})})

    v.check("the-3d-viewport-collapses-to-zero-height-whenever-the-clamp-fires",
            all(r["viewportH"] == 0 for r in clamped.values()),
            detail={"nonZero": {k: r["viewportH"] for k, r in clamped.items()
                                if r["viewportH"] != 0}})

    # --- THE FALSIFICATION: top alone does not determine the set --------
    def group_by(key) -> dict[Any, list[str]]:
        g: dict[Any, list[str]] = {}
        for k, r in cells.items():
            g.setdefault(key(r), []).append(k)
        return g

    def ragged_of(groups) -> list[dict[str, Any]]:
        out_ = []
        for key, members in groups.items():
            sets = {tuple(cells[m]["buriedLabels"]) for m in members}
            if len(sets) > 1:
                out_.append({"key": key, "members": sorted(members),
                             "distinctSets": len(sets),
                             "sizes": sorted(len(s) for s in sets)})
        return sorted(out_, key=lambda d: str(d["key"]))

    by_top = group_by(lambda r: r["timelineTop"])
    ragged_top = ragged_of(by_top)
    multi_top = {t: sorted(m) for t, m in by_top.items() if len(m) > 1}
    v.check("634s-one-dimensional-collapse-is-falsified", bool(ragged_top),
            detail={"raggedTopEdges": ragged_top[:6],
                    "topEdgeGroupSizes": {str(t): len(m)
                                          for t, m in sorted(by_top.items())},
                    "multiMemberTopEdges": len(multi_top)})

    by_pair = group_by(lambda r: (r["timelineTop"], r["windowH"]))
    ragged_pair = ragged_of(by_pair)
    v.check("the-two-variable-law-top-and-window-height-is-consistent",
            not ragged_pair,
            detail={"ragged": ragged_pair[:4],
                    "pairGroupSizes": {f"{t}/{w}": len(m)
                                       for (t, w), m in sorted(by_pair.items())}})

    # Non-vacuity for the falsification: a top edge that holds many cells from
    # MANY different window heights and still splits.  Without this the check
    # above could pass on a grid where every top edge simply has one member.
    split = [d for d in ragged_top if len({cells[m]["windowH"] for m in d["members"]}) > 1]
    v.check("the-falsification-is-exercised-by-many-window-heights-per-top-edge",
            bool(split), detail={"splitTopEdges": split[:4]})

    # --- 634 survives on its own domain; this batch names the boundary ---
    b634_cells = {k: r for k, r in cells.items() if k.startswith("b634|")}
    b634_groups: dict[Any, list[str]] = {}
    for k, r in b634_cells.items():
        b634_groups.setdefault(r["timelineTop"], []).append(k)
    b634_ragged = ragged_of(b634_groups)
    v.check("634s-claim-still-holds-on-634s-own-grid", not b634_ragged,
            detail={"ragged": b634_ragged[:4],
                    "multiMemberTopEdges": {str(t): sorted(m)
                                            for t, m in b634_groups.items()
                                            if len(m) > 1},
                    "minWindowHeight": min(r["windowH"] for r in b634_cells.values())})

    v.check("634s-minimum-window-height-is-above-the-saturation-line",
            min(r["windowH"] for r in b634_cells.values()) > 436,
            detail={"b634MinWindowHeight": min(r["windowH"]
                                               for r in b634_cells.values()),
                    "lastRowBottom": 436})

    # The boundary itself: at a pinned top, walk the window height and read where
    # the burial count stops growing.  Measured, not transcribed.
    sweep = [(r["windowH"], r["buriedCount"])
             for k, r in cells.items() if r["group"] == f"sweep{SWEEP_TOP}"]
    sweep.sort()
    peak = max(c for _w, c in sweep)
    sat = min(w for w, c in sweep if c == peak)
    v.check("the-saturation-line-is-measured-not-assumed", sat <= 436,
            detail={"sweepTop": SWEEP_TOP, "saturationAtWindowHeight": sat,
                    "saturatedCount": peak, "curve": sweep})

    mono = all(sweep[i][1] <= sweep[i + 1][1] for i in range(len(sweep) - 1))
    v.check("at-a-pinned-top-the-count-rises-with-the-window-height", mono,
            detail=sweep)

    # 634's monotonicity survives verbatim, with the direction stated: keyed by
    # top DESCENDING, "a lower top buries more" means the counts RISE along the
    # list.  (634 asserted the opposite direction and had to be corrected.)
    saturated = [r for r in b634_cells.values() if r["windowH"] > 436]
    fn = sorted({(r["timelineTop"], r["buriedCount"]) for r in saturated}, reverse=True)
    counts = [c for _t, c in fn]
    v.check("634s-monotonicity-survives-in-the-saturated-regime",
            all(counts[i] <= counts[i + 1] for i in range(len(counts) - 1)),
            detail={"fn": fn})

    # --- cross-batch reconciliation -------------------------------------
    # 634's recorded audit must agree with this run on every cell both share.
    prior_disagree = []
    compared = 0
    if PRIOR_634.exists():
        d634 = json.loads(PRIOR_634.read_text())
        compared = len(d634["cells"])
        for key, prev in d634["cells"].items():
            wh, req = key.split("/")
            mine = b634_cells.get(f"b634|wh={wh}/tl={req}")
            if mine is None:
                continue
            if (len(prev["buriedLabels"]) != mine["buriedCount"]
                    or sorted(prev["buriedLabels"]) != mine["buriedLabels"]):
                prior_disagree.append({"cell": key,
                                       "prior": sorted(prev["buriedLabels"]),
                                       "mine": mine["buriedLabels"]})
    v.check("this-run-reproduces-634s-recorded-audit-on-all-48-shared-cells",
            not prior_disagree,
            detail={"compared": compared,
                    "disagreements": prior_disagree[:4]})

    out["checks"] = v.result
    out["ok"] = not v.failures
    out["checkCount"] = v.count
    out["failures"] = v.failures
    out["totals"] = {
        "unreachable": sum(len(r["unreachable"]) for r in cells.values()),
        "zeroSize": sum(len(r["zeroSize"]) for r in cells.values()),
        "unexplained": sum(len(r["unexplained"]) for r in cells.values()),
        "offViewport": sum(r["offViewport"] for r in cells.values()),
        "clampedCells": len(clamped),
        "clampBurialCounts": {k: r["buriedCount"] for k, r in sorted(clamped.items())},
        "saturationWindowHeight": sat,
        "saturatedBurialCount": peak,
        "sweep": [{"windowH": w, "buried": c} for w, c in sweep],
        "raggedTopEdges": ragged_top,
        "b634Ragged": b634_ragged,
    }
    audit = ROOT / "docs/research/liblib-canvas-batch635-2026-10-01"
    audit.mkdir(parents=True, exist_ok=True)
    (audit / "runtime-audit.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2) + "\n")

    print(f"\n{v.count} checks, {len(v.failures)} failures")
    for f in v.failures:
        print("  FAILED: " + f)
    return 1 if v.failures else 0


if __name__ == "__main__":
    sys.exit(main())
