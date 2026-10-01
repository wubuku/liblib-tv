#!/usr/bin/env python3
"""batch 637 验收：把 636 的「store 与 DOM 分歧」从一个魔数扩到一个**用户可见的开关**。

## 起点

636 发现：高度**恰好等于** `DIRECTOR_TIMELINE_DEFAULT_HEIGHT`(182) 时
`DirectorTimeline.tsx:843-845` 故意不设行内样式，把高度交给 CSS，而
`max-[899px]:h-[176px]` 给的是 176 —— store 存 182、DOM 是 176，**6px** 分歧。

但同一个三元的**另一个分支更彻底**：

    timelineCollapsed || height === 182  ?  undefined  :  { height }

**收起态下 store 的高度被完全忽略**，高度只由 CSS 决定，而收起态的 CSS 高度
（同文件 `:832-836`）是分族的：`h-[88px]`（≥899）/ `max-[899px]:h-[124px]`（≤898），
注释写明 124 = 36+36+52（618 把窄屏工具条改成两行后推出来的）。于是窄屏收起态的
store/DOM 分歧是 **182 − 124 = 58px** —— 636 那条的近十倍，而且**发生在一个用户
能亲手按下的开关上**，不是某个魔数常量。

## 631 没有覆盖的部分

631 确实把「收起侧栏」当状态轴扫过，但 (a) 它扫的是**视线轴的** `viewportPanelsCollapsed`
（侧栏），不是时间轴的 `timelineCollapsed`；(b) 它的 `WINDOWS` 是 (w,h) **耦合对**，
没有把窗高单独拿出来；(c) 它量的是掩埋曲面，**从未钉住收起态实际渲染成多高**，
也没测过 store/DOM 在收起态是否一致。本批补的正是这三条。

## 零源站断言

源站时间轴在窄屏的默认高度与收起高度**未取证**。本批只主张 clone 的读数，
**不主张 176/124/88 里哪个该是源站的数**，也不发明新数。
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

WIDTHS = [898, 899, 1440]
WIN_HEIGHTS = [328, 436, 560, 660, 900]
STORE_HEIGHTS = [88, 124, 182, 240, 420]
DEFAULT_STORE = 182
CONTROL_WH = 900          # tall window: the 630 clamp never fires here
CROSS_WH = 900            # window for the store-independence sweep

# The CSS-only heights.  Two DIFFERENT questions, and my first table conflated
# them, which made both height checks red on correct data:
#
#   CSS_COLLAPSED  — collapsed always drops the inline style, so CSS alone
#                    decides: 124 in the narrow family, 88 on desktop.
#   CSS_AT_DEFAULT — expanded drops the inline style ONLY when the store holds
#                    the desktop default 182 (636's finding), so CSS alone
#                    decides then too: 176 in the narrow family, 182 on desktop.
#
# Any other store value carries an inline height and renders verbatim.
CSS_COLLAPSED = {False: 88, True: 124}       # keyed by narrow
CSS_AT_DEFAULT = {False: 182, True: 176}

PRIOR_636 = ROOT / "docs/research/liblib-canvas-batch636-2026-10-01/runtime-audit.json"

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
  const tl = document.querySelector('[data-director-timeline]');
  return {
    viewport: rd('[data-director-viewport]'),
    timeline: rd('[data-director-timeline]'),
    bottomBar: rd('[data-director-bottom-bar]'),
    rail: rd('[data-director-icon-rail]'),
    tree: rd('aside[aria-label="场景对象"]'),
    inspector: rd('aside[aria-label="属性"]'),
    collapsedAttr: tl ? tl.getAttribute('data-director-timeline-collapsed') : null,
    heightAttr: tl ? tl.getAttribute('data-director-timeline-height') : null,
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


def ask_height(page, th: int) -> None:
    page.evaluate("(n) => window.__director_store.getState().setTimelineHeight(n)", th)
    page.wait_for_timeout(200)


def ask_collapse(page, want: bool) -> bool:
    """`timelineCollapsed` is local component state, not a store value, so the
    only honest way to flip it is to press the button the user presses."""
    attr = page.evaluate(
        "() => document.querySelector('[data-director-timeline]')"
        ".getAttribute('data-director-timeline-collapsed')")
    is_now = attr == "true"
    if is_now != want:
        label = "展开时间线" if is_now else "时间线最小化"
        page.locator(f'[aria-label="{label}"]').first.click(timeout=15_000)
        page.wait_for_timeout(320)
    attr2 = page.evaluate(
        "() => document.querySelector('[data-director-timeline]')"
        ".getAttribute('data-director-timeline-collapsed')")
    return (attr2 == "true") == want


def measure(page, w: int, wh: int, collapsed: bool, want: int) -> dict[str, Any]:
    r = page.evaluate(b617.AUDIT_JS, list(b617.TRANSIENT_OVERLAYS))
    g = page.evaluate(GEOM_JS)
    z = page.evaluate(b623.BLIND_JS)
    store_h = page.evaluate(
        "() => window.__director_store.getState().timelineHeight")
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
        "width": w, "windowH": wh, "collapsed": collapsed, "storeRequested": want,
        "collapsedAttr": g["collapsedAttr"], "heightAttr": g["heightAttr"],
        "narrow": w <= 898,
        "timelineTop": tl["t"], "timelineH": tl["h"],
        "storeHeight": store_h,
        "divergence": round(store_h - tl["h"], 3) if store_h is not None else None,
        "spill": max(0, tl["b"] - wh),
        "viewportH": vp["h"] if vp else None,
        "total": r["total"],
        "offViewport": len(r["offViewportItems"]),
        "unreachable": [(b["label"], b["box"]) for b in r["offViewportUnreachable"]],
        "zeroSize": z,
        "unexplained": [(b["label"], b["hitLabel"], b["box"]) for b in r["covered"]],
        "buriedLabels": labels, "buriedCount": len(labels),
        "buriedColumns": sorted({x[3] for x in rows}),
        "aboveTimelineTop": [x[0] for x in rows if x[1][1] + x[1][3] <= tl["t"] + 0.5],
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


def main() -> int:
    v = Verifier()
    cells: dict[str, Any] = {}
    toggle_failures: list[str] = []
    with sync_playwright() as p:
        br = p.chromium.launch()
        for w in WIDTHS:
            page = br.new_page(viewport={"width": w, "height": CONTROL_WH},
                               device_scale_factor=1)
            b617.open_desk(page)
            for collapsed in (False, True):
                if not ask_collapse(page, collapsed):
                    toggle_failures.append(f"w{w}->{collapsed}")
                for wh in WIN_HEIGHTS:
                    page.set_viewport_size({"width": w, "height": wh})
                    page.wait_for_timeout(180)
                    ask_height(page, DEFAULT_STORE)
                    page.wait_for_timeout(200)
                    prep(page)
                    key = f"main|w{w}/{'col' if collapsed else 'exp'}/wh={wh}"
                    cells[key] = measure(page, w, wh, collapsed, DEFAULT_STORE)
            # store-independence sweep: the store value must not matter.
            page.set_viewport_size({"width": w, "height": CROSS_WH})
            page.wait_for_timeout(180)
            for collapsed in (False, True):
                if not ask_collapse(page, collapsed):
                    toggle_failures.append(f"sweep-w{w}->{collapsed}")
                for h in STORE_HEIGHTS:
                    ask_height(page, h)
                    page.wait_for_timeout(200)
                    prep(page)
                    cells[f"sweep|w{w}/{'col' if collapsed else 'exp'}/store={h}"] = \
                        measure(page, w, CROSS_WH, collapsed, h)
            page.close()
        br.close()

    out = {
        "batch": 637,
        "title": "the store/DOM divergence 636 found at one magic constant also "
                 "covers the collapse toggle — where the store is ignored entirely "
                 "and the gap is 58px, not 6px",
        "date": "2026-10-01",
        "widths": WIDTHS, "windowHeights": WIN_HEIGHTS,
        "storeHeights": STORE_HEIGHTS,
        "cssOnlyHeights": {"collapsed": {str(k): v for k, v in CSS_COLLAPSED.items()},
                           "atStoreDefault": {str(k): v for k, v in CSS_AT_DEFAULT.items()}},
        "cells": cells,
    }

    n = len(cells)
    expected = len(WIDTHS) * 2 * len(WIN_HEIGHTS) + len(WIDTHS) * 2 * len(STORE_HEIGHTS)
    v.check(f"the-grid-runs-{expected}-cells", n == expected, detail=n)

    v.check("the-collapse-toggle-is-reachable-and-flips-the-data-attribute",
            not toggle_failures, detail={"failedTransitions": toggle_failures})

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
    v.check("the-timeline-never-spills-past-the-window-collapsed-or-not", not sp,
            detail=dict(list(sp.items())[:6]))

    pd = {k: {} for k, r in cells.items() if not r["predictAgrees"]}
    v.check("629s-closed-form-predicts-the-squeeze-in-every-cell", not pd,
            detail=dict(list(pd.items())[:6]))

    # --- THE LAW: collapsed height is CSS-only, per family ----------------
    collapsed_cells = [r for r in cells.values() if r["collapsed"]]
    wrong = {f"w{r['width']}": r["timelineH"] for r in collapsed_cells
             if abs(r["timelineH"] - CSS_COLLAPSED[r["narrow"]]) > 0.5}
    v.check("a-collapsed-timeline-renders-88-on-desktop-and-124-in-the-narrow-family",
            not wrong,
            detail={"expected": {"narrow": CSS_COLLAPSED[True],
                                 "desktop": CSS_COLLAPSED[False]},
                    "wrong": wrong,
                    "collapsedCells": len(collapsed_cells)})

    # The store is not merely clamped when collapsed — it is ignored outright.
    ignored = {f"w{w}/col/store={h}": cells[f"sweep|w{w}/col/store={h}"]["timelineH"]
               for w in WIDTHS for h in STORE_HEIGHTS}
    spread = {w: sorted({ignored[f"w{w}/col/store={h}"] for h in STORE_HEIGHTS})
              for w in WIDTHS}
    v.check("every-store-value-renders-the-same-height-while-collapsed",
            all(len(s) == 1 for s in spread.values()),
            detail={"storeHeightsSwept": STORE_HEIGHTS, "heightsPerWidth": spread})

    # Per cell, against ITS OWN store value: the sweep writes five different
    # store heights, and my first version compared every one of them to 182.
    v.check("the-collapsed-divergence-is-store-minus-the-family-css-default-per-cell",
            all(abs(r["divergence"] - (r["storeHeight"] - CSS_COLLAPSED[r["narrow"]]))
                < 0.5 for r in cells.values() if r["collapsed"]),
            detail={"cssCollapsed": {"narrow": CSS_COLLAPSED[True],
                                     "desktop": CSS_COLLAPSED[False]},
                    "gapsAtDefaultStore": {
                        "narrow": DEFAULT_STORE - CSS_COLLAPSED[True],
                        "desktop": DEFAULT_STORE - CSS_COLLAPSED[False]},
                    "sample": {k: {"store": r["storeHeight"],
                                   "dom": r["timelineH"], "gap": r["divergence"]}
                               for k, r in list(cells.items())
                               if r["collapsed"] and r["storeRequested"] == 240}})

    # 636's 6px finding must still hold in the expanded state — a batch that
    # contradicts the previous batch has to say so out loud.
    exp182 = {f"w{r['width']}": r["timelineH"] for r in cells.values()
              if not r["collapsed"] and r["storeRequested"] == DEFAULT_STORE}
    v.check("636s-6px-expanded-divergence-survives-this-batch",
            all(abs(exp182[f"w{w}"] - CSS_AT_DEFAULT[w <= 898]) < 0.5 for w in WIDTHS),
            detail={"expandedAtStore182": exp182,
                    "cssAtDefault": {"narrow": CSS_AT_DEFAULT[True],
                                     "desktop": CSS_AT_DEFAULT[False]},
                    "gaps": {f"w{w}": DEFAULT_STORE - exp182[f"w{w}"]
                             for w in WIDTHS}})

    gap_narrow = DEFAULT_STORE - CSS_COLLAPSED[True]        # 182 - 124 = 58
    gap_desktop = DEFAULT_STORE - CSS_COLLAPSED[False]      # 182 -  88 = 94
    gap_narrow_expanded = DEFAULT_STORE - CSS_AT_DEFAULT[True]   # 182 - 176 = 6
    v.check("the-collapsed-gap-is-ten-times-636s-narrow-gap",
            gap_narrow >= 9 * gap_narrow_expanded,
            detail={"narrowCollapsedGap": gap_narrow,
                    "narrowExpandedGap": gap_narrow_expanded,
                    "desktopCollapsedGap": gap_desktop,
                    "ratio": round(gap_narrow / gap_narrow_expanded, 2)})

    # --- crossing the collapse state with the window-height axis ---------
    pairs = {}
    for w in WIDTHS:
        for wh in WIN_HEIGHTS:
            e = cells[f"main|w{w}/exp/wh={wh}"]
            c = cells[f"main|w{w}/col/wh={wh}"]
            pairs[f"w{w}/wh={wh}"] = (e["buriedCount"], c["buriedCount"])
    notless = {k: p for k, p in pairs.items() if p[1] > p[0]}
    v.check("collapsing-the-timeline-never-buries-more", not notless,
            detail={"violations": notless, "pairs": pairs})

    changed = {k: p for k, p in pairs.items() if p[0] != p[1]}
    v.check("the-collapse-state-actually-changes-the-burial-surface", bool(changed),
            detail={"cellsWhereItChanges": len(changed), "of": len(pairs),
                    "examples": dict(list(changed.items())[:6])})

    # --- 635's two-variable law still holds across the state axis ---------
    # Keyed by FAMILY as well as (top, window).  My first version pooled the
    # narrow family with the desktop one and went red at four groups — all of
    # them narrow-vs-desktop pairs, because the narrow columns are off-screen
    # `inert` drawers that bury nothing (633's third variable, 636 re-pinned).
    # The narrow family is not a counterexample to 635; it was a missing key.
    by_fam: dict[str, dict[Any, list[str]]] = {"narrow": {}, "desktop": {}}
    for k, r in cells.items():
        fam = "narrow" if r["narrow"] else "desktop"
        by_fam[fam].setdefault((r["timelineTop"], r["windowH"]), []).append(k)
    ragged: list[dict[str, Any]] = []
    for fam, groups in by_fam.items():
        for key, members in groups.items():
            sets = {tuple(cells[m]["buriedLabels"]) for m in members}
            if len(sets) > 1:
                ragged.append({"family": fam, "key": list(key),
                               "members": sorted(members),
                               "distinctSets": len(sets)})
    v.check("635s-two-variable-law-survives-crossing-the-collapse-state",
            not ragged,
            detail={"pairGroups": {f: len(g) for f, g in by_fam.items()},
                    "ragged": ragged[:4]})

    narrow_nonzero = {k: r["buriedCount"] for k, r in cells.items()
                      if r["narrow"] and r["buriedCount"]}
    v.check("the-narrow-family-still-buries-nothing-in-either-collapse-state",
            not narrow_nonzero,
            detail={"nonZeroCells": dict(list(narrow_nonzero.items())[:6]),
                    "narrowCells": sum(1 for r in cells.values() if r["narrow"])})

    # --- cross-batch reconciliation -------------------------------------
    prior = []
    if PRIOR_636.exists():
        d636 = json.loads(PRIOR_636.read_text())
        for key, prev in d636["cells"].items():
            parts = key.split("|")[1].split("/")
            w = int(parts[0][1:])
            wh = int(parts[1].split("=")[1])
            top = int(parts[0].split("T")[1])
            mine = cells.get(f"main|w{w}/exp/wh={wh}")
            if mine is None or abs(mine["timelineTop"] - top) > 0.5:
                continue
            if sorted(prev["buriedLabels"]) != mine["buriedLabels"]:
                prior.append({"prior": key, "mine": mine["buriedCount"]})
    v.check("this-run-reproduces-636s-recorded-audit-on-every-shared-expanded-cell",
            not prior, detail={"disagreements": prior[:4]})

    out["checks"] = v.result
    out["ok"] = not v.failures
    out["checkCount"] = v.count
    out["failures"] = v.failures
    out["totals"] = {
        "unreachable": sum(len(r["unreachable"]) for r in cells.values()),
        "zeroSize": sum(len(r["zeroSize"]) for r in cells.values()),
        "unexplained": sum(len(r["unexplained"]) for r in cells.values()),
        "offViewport": sum(r["offViewport"] for r in cells.values()),
        "collapsePairCounts": {k: {"expanded": a, "collapsed": c}
                               for k, (a, c) in pairs.items()},
        "collapsedHeightsPerWidth": spread,
        "divergences": {k: r["divergence"] for k, r in cells.items()
                        if r["divergence"]},
    }
    audit = ROOT / "docs/research/liblib-canvas-batch637-2026-10-01"
    audit.mkdir(parents=True, exist_ok=True)
    (audit / "runtime-audit.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2) + "\n")

    print(f"\n{v.count} checks, {len(v.failures)} failures")
    for f in v.failures:
        print("  FAILED: " + f)
    return 1 if v.failures else 0


if __name__ == "__main__":
    sys.exit(main())
