#!/usr/bin/env python3
"""batch 636 验收：633 的「宽度不是变量」在**短窗区**重验一遍。

## 为什么必须重验

633 在窗口高固定 **660** 的网格上量到「掩埋曲面是 2×8 阶梯函数、宽度不是变量」。
660 恰好落在 635 刚测出的**饱和区**（饱和线 = 窗高 436）。635 证明曲面有一个
633 没看见的**第二变量**（窗口高），于是 633 当时那句「宽度不是变量」只在其
采样域内成立 —— **和 634 自己栽的是同一种坑：在饱和区里量，然后外推。**

本批把**顶边钉死**、让窗口高横扫整个量程（含饱和线两侧），对每个宽度取一条
掩埋曲线，逐格对比：

- 桌面族（899/1024/1280/1440/1920）若**逐格相同** → 宽度在**两个区**里都不是变量，
  633 的断言被**推广**而不是被推翻；
- 若出现分歧 → 存在宽度 × 窗高的交互，本批把它定位到具体宽度。

## 顺带钉住家族边界是**宽度驱动**的

898 属于窄族（列是屏外 `inert` 抽屉），掩埋恒为 **0**；899 属于桌面族。这个 1px
的断崖在**任何**窗高下都该在 898/899 之间 —— 若它随窗高移动，就说明家族划分
其实由窗高参与，633 的「两个族」说法要重写。

## 零源站断言

第一族是 613 在源站 1920×1150 实测的**源站事实**；源站在矮视口下掩埋多少行
**未取证**，本批只主张 clone 的读数。
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

# 898/899 straddle the family boundary; 633 recorded narrow <= 898, desktop >= 899.
WIDTHS = [898, 899, 1024, 1280, 1440, 1920]
NARROW = 898
DESKTOP = [w for w in WIDTHS if w != NARROW]

# For a pinned top T the window height must be wh = T + req with req in [88,420],
# and the clamp never fires (req <= wh - 88 <=> T >= 88).
TOPS = {
    240: [328, 364, 400, 436, 480, 560, 660],
    360: [448, 480, 542, 660, 720, 780],
}

PRIOR_635 = ROOT / "docs/research/liblib-canvas-batch635-2026-10-01/runtime-audit.json"
PRIOR_633 = ROOT / "docs/research/liblib-canvas-batch633-2026-10-01/runtime-audit.json"

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


def measure(page, w: int, wh: int, top: int) -> dict[str, Any]:
    req = wh - top
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
        "width": w, "windowH": wh, "pinnedTop": top, "requested": req,
        "timelineTop": tl["t"], "timelineH": tl["h"],
        "storeHeight": store_h,
        "storeAgreesWithDom": store_h is None
                           or abs(store_h - tl["h"]) < 0.5,
        "clamped": abs(tl["h"] - req) > 0.5,
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
    with sync_playwright() as p:
        br = p.chromium.launch()
        for w in WIDTHS:
            page = br.new_page(viewport={"width": w, "height": 900},
                               device_scale_factor=1)
            b617.open_desk(page)
            for top, whs in TOPS.items():
                for wh in whs:
                    page.set_viewport_size({"width": w, "height": wh})
                    page.wait_for_timeout(170)
                    ask(page, wh - top)
                    prep(page)
                    cells[f"w{w}|T{top}/wh={wh}"] = measure(page, w, wh, top)
            page.close()
        br.close()

    out = {
        "batch": 636,
        "title": "633's \"width is not a variable\" re-checked in the short-window "
                 "regime 635 uncovered — and the 898/899 family cliff pinned as "
                 "width-driven",
        "date": "2026-10-01",
        "widths": WIDTHS,
        "tops": {str(k): val for k, val in TOPS.items()},
        "cells": cells,
    }

    n = len(cells)
    expected = len(WIDTHS) * sum(len(v) for v in TOPS.values())
    v.check(f"the-grid-runs-{expected}-cells", n == expected, detail=n)

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

    pd = {k: {"observed": len(r["buriedLabels"])} for k, r in cells.items()
          if not r["predictAgrees"]}
    v.check("629s-closed-form-predicts-the-squeeze-in-every-cell", not pd,
            detail=dict(list(pd.items())[:4]))

    # --- 630's clamp, composed with the 182 shortcut this batch found ------
    # 630's law is `min(requested, window - 88)`, but it only holds for values
    # that carry an inline height.  `DirectorTimeline.tsx:843-845` deliberately
    # omits the inline style when the height IS the desktop default (182), so
    # CSS decides — and the `max-[899px]` breakpoint's CSS default is 176.  The
    # store keeps 182, so state and UI disagree at exactly one value, in exactly
    # one family.  Recorded and pinned, not fixed: which side should give way is
    # a product decision, and 176 is the narrow default 630 already pinned.
    DESKTOP_DEFAULT = 182
    NARROW_CSS_DEFAULT = 176
    narrow_of = lambda r: r["width"] <= 898

    def expected_height(r: dict[str, Any]) -> float:
        if r["requested"] == DESKTOP_DEFAULT:
            return (NARROW_CSS_DEFAULT if narrow_of(r) else DESKTOP_DEFAULT)
        return float(min(r["requested"], r["windowH"] - 88))

    clampbad = {k: {"requested": r["requested"], "windowH": r["windowH"],
                    "width": r["width"], "expected": expected_height(r),
                    "actual": r["timelineH"]}
                for k, r in cells.items()
                if abs(r["timelineH"] - expected_height(r)) > 0.5}
    v.check("the-timeline-height-law-is-min-with-window-minus-88-except-at-the"
            "-182-shortcut", not clampbad, detail=dict(list(clampbad.items())[:4]))

    div = {k: {"width": r["width"], "store": r["storeHeight"],
               "dom": r["timelineH"]}
           for k, r in cells.items() if not r["storeAgreesWithDom"]}
    only182narrow = all(r["requested"] == DESKTOP_DEFAULT and narrow_of(r)
                        for r in cells.values() if not r["storeAgreesWithDom"])
    v.check("the-store-and-the-dom-diverge-only-at-182-in-the-narrow-family",
            only182narrow,
            detail={"divergentCells": div,
                    "divergences": len(div), "of": len(cells)})

    v.check("the-182-shortcut-costs-exactly-the-6px-family-gap",
            all(abs(r["timelineH"] - r["requested"]) == 6
                for r in cells.values() if not r["storeAgreesWithDom"]),
            detail={"requestedAtDesktopDefault": DESKTOP_DEFAULT,
                    "renderedInNarrowFamily": NARROW_CSS_DEFAULT})

    # The pinned-top check must tolerate exactly the cells that go through the
    # 182 shortcut, and nothing else.  Silently widening it would hide a second
    # deviation; excluding by a named reason keeps the assertion load-bearing.
    shortcut = {k for k, r in cells.items()
                if r["requested"] == DESKTOP_DEFAULT and narrow_of(r)}
    topbad = {k: {"pinned": r["pinnedTop"], "actual": r["timelineTop"]}
              for k, r in cells.items()
              if abs(r["timelineTop"] - r["pinnedTop"]) > 0.5 and k not in shortcut}
    v.check("every-cell-except-the-named-182-shortcut-sat-on-its-pinned-top",
            not topbad, detail={"shortcutCells": sorted(shortcut),
                                "otherDeviations": dict(list(topbad.items())[:6])})

    # --- THE CLAIM: width is not a variable in EITHER regime -------------
    curves: dict[str, dict[int, tuple[int, tuple[str, ...]]]] = {}
    for w in WIDTHS:
        curves[str(w)] = {}
        for top, whs in TOPS.items():
            curves[str(w)][str(top)] = {
                wh: (cells[f"w{w}|T{top}/wh={wh}"]["buriedCount"],
                     tuple(cells[f"w{w}|T{top}/wh={wh}"]["buriedLabels"]))
                for wh in whs}

    split = {}
    for top in TOPS:
        ref = str(DESKTOP[0])
        for w in DESKTOP[1:]:
            for wh in TOPS[top]:
                if curves[str(w)][str(top)][wh] != curves[ref][str(top)][wh]:
                    split.setdefault(f"T{top}", []).append(
                        {"width": w, "windowH": wh,
                         "reference": {"width": ref, **{
                             "count": curves[ref][str(top)][wh][0],
                             "labels": list(curves[ref][str(top)][wh][1])}},
                         "observed": {"count": curves[str(w)][str(top)][wh][0],
                                      "labels": list(curves[str(w)][str(top)][wh][1])}})
    v.check("633s-width-is-not-a-variable-holds-in-the-short-window-regime-too",
            not split,
            detail={"desktopWidths": DESKTOP,
                    "disagreements": {k: v[:4] for k, v in split.items()}})

    # Non-vacuity, stated correctly.  My first version demanded EVERY curve
    # move, and it went red on the top-360 curves being flat at 4 — which is not
    # a defect but a fact: 360 sits above every fixed row, so the band
    # [360, window] gains nothing as the window grows.  The right demand is that
    # each width has at least one curve that moves, plus a positive assertion
    # that the flat one is flat for that structural reason and nowhere else.
    flat: dict[str, list[int]] = {}
    no_move: list[str] = []
    for w in DESKTOP:
        moving = 0
        for top, whs in TOPS.items():
            series = [curves[str(w)][str(top)][wh][0] for wh in whs]
            if len(set(series)) == 1:
                flat[f"w{w}|T{top}"] = series
            else:
                moving += 1
        if moving == 0:
            no_move.append(str(w))
    v.check("every-desktop-width-has-at-least-one-curve-that-moves",
            not no_move, detail={"widthsWithNoMovingCurve": no_move,
                                 "flatCurves": flat})

    v.check("only-the-top-360-curves-are-flat", set(flat) ==
            {f"w{w}|T360" for w in DESKTOP},
            detail={"flatCurves": sorted(flat),
                    "top240Curves": {str(w): [curves[str(w)]["240"][wh][0]
                                              for wh in TOPS[240]]
                                     for w in DESKTOP}})

    unsat = {}
    for w in DESKTOP:
        for top, whs in TOPS.items():
            short = [curves[str(w)][str(top)][wh][0] for wh in whs if wh < 436]
            if short and len(set(short)) == 1:
                unsat[f"w{w}|T{top}"] = short
    v.check("every-desktop-width-shows-the-unsaturated-regime-at-top-240",
            not unsat, detail={"flatBelowSaturation": unsat})

    # The saturation line itself must be width-independent, not just the counts.
    sat = {}
    for w in DESKTOP:
        whs = TOPS[240]
        series = [(wh, curves[str(w)]["240"][wh][0]) for wh in whs]
        peak = max(c for _wh, c in series)
        sat[str(w)] = min(wh for wh, c in series if c == peak)
    v.check("the-saturation-line-is-the-same-for-every-desktop-width",
            len(set(sat.values())) == 1, detail=sat)

    # --- the 898/899 family cliff is width-driven ------------------------
    narrow_counts = {f"T{top}/wh={wh}": cells[f"w{NARROW}|T{top}/wh={wh}"]["buriedCount"]
                     for top, whs in TOPS.items() for wh in whs}
    v.check("the-narrow-family-column-buries-nothing-at-any-window-height",
            all(c == 0 for c in narrow_counts.values()),
            detail={"width": NARROW, "counts": narrow_counts})

    cliff = {str(w): sorted({cells[f"w{w}|T{top}/wh={wh}"]["buriedCount"]
                             for top, whs in TOPS.items() for wh in whs})
             for w in (898, 899)}
    v.check("the-family-cliff-sits-at-898-899-and-not-at-a-window-height",
            cliff[str(NARROW)] == [0] and cliff["899"] != [0], detail=cliff)

    # --- cross-batch reconciliation -------------------------------------
    # 635 recorded the same curve at width 1440; every window height this grid
    # shares with 635's top-240 sweep must reproduce it.
    shared = []
    if PRIOR_635.exists():
        d635 = json.loads(PRIOR_635.read_text())
        for key, prev in d635["cells"].items():
            if not key.startswith("sweep240|"):
                continue
            wh = key.split("wh=")[1].split("/")[0]
            mine = cells.get(f"w1440|T240/wh={wh}")
            if mine is None:
                continue
            if sorted(prev["buriedLabels"]) != mine["buriedLabels"]:
                shared.append({"prior": key,
                               "priorCount": len(prev["buriedLabels"]),
                               "mine": mine["buriedCount"]})
    v.check("this-run-reproduces-635s-recorded-audit-on-every-shared-1440-cell",
            not shared, detail={"disagreements": shared[:4]})

    # 633 recorded the desktop row keyed by REQUESTED timeline height at window
    # 1440x660.  Two of its eight points land on this grid, and both must match:
    #   req 420 -> top 240 -> 15     req 300 -> top 360 -> 4
    fn633: dict[str, Any] | None = None
    if PRIOR_633.exists():
        d633 = json.loads(PRIOR_633.read_text())
        fn633 = d633["totals"]["burialSurface"].get("desktop")
    probe = {660 - top: cells[f"w1440|T{top}/wh=660"]["buriedCount"]
             for top in (240, 360)}
    disagree633 = {k: {"prior": (fn633 or {}).get(str(k)), "mine": c}
                   for k, c in probe.items()
                   if fn633 is None or (fn633 or {}).get(str(k)) != c}
    v.check("633s-desktop-row-agrees-with-this-run-at-its-two-shared-points",
            not disagree633,
            detail={"prior633Desktop": fn633, "mineAt1440x660": probe,
                    "disagreements": disagree633})

    out["checks"] = v.result
    out["ok"] = not v.failures
    out["checkCount"] = v.count
    out["failures"] = v.failures
    out["totals"] = {
        "unreachable": sum(len(r["unreachable"]) for r in cells.values()),
        "zeroSize": sum(len(r["zeroSize"]) for r in cells.values()),
        "unexplained": sum(len(r["unexplained"]) for r in cells.values()),
        "offViewport": sum(r["offViewport"] for r in cells.values()),
        "curves": {w: {t: [[wh, curves[w][t][wh][0]] for wh in TOPS[int(t)]]
                       for t in curves[w]} for w in curves},
        "saturationByWidth": sat,
        "familyCliff": cliff,
    }
    audit = ROOT / "docs/research/liblib-canvas-batch636-2026-10-01"
    audit.mkdir(parents=True, exist_ok=True)
    (audit / "runtime-audit.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2) + "\n")

    print(f"\n{v.count} checks, {len(v.failures)} failures")
    for f in v.failures:
        print("  FAILED: " + f)
    return 1 if v.failures else 0


if __name__ == "__main__":
    sys.exit(main())
