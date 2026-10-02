#!/usr/bin/env python3
"""batch 639 验收：审 629 闭式里的**两个常数** —— 88 与 48 到底是不是族无关的。

## 为什么审它们

638 证明了凡是和时间轴**高度**有关的一切都是分族的。而 629 的闭式公式里有两个
数被当成普适常数用：

    viewportTop = 88      （3D 视口的顶边）
    band        = 48      （视口底部那条带的高度）

629/635/636/637 的每一条结论都建立在这两个数上。若任一随族变化，那些结论在那一族
就是错的 —— 而 629 自己只在**抽象层面**断言过公式，没在窄族上喂实测值跑过。

## 结论：两个常数都是真的，但**族相关性在旁边**

64 格（8 宽度 × 2 收起态 × 4 窗高，横跨两族）实测：

- `viewportTop` 恒 **88**，`band` 恒 **48**（且底带 `position: absolute` /
  `display: flex`）—— **族无关，状态无关，窗高无关**。
- `vpH = 时间轴顶边 − 88` 在**每一格**成立，所以 635 的关系式是普适的 ——
  **正因为** `viewportTop` 真的是常数。
- 族相关性**只从时间轴高度传导进来**：同窗高下窄族 `vpH` 比桌面族**大 6px**
  （窗高 328 时 64 vs 58），6px 正是 636/637 钉住的族差。

## 把 629 的闭式喂进实测常数，在两族都验一遍

629 的 `predict` 需要 `viewportTop` / `viewportH` / `band` 三个输入。本批**全部用
实测值**（不是写死的 88/48），在 64 格上逐格对账。这把 629 的公式从「一条写着
对的公式」升级成「在两个族、两个状态下逐格都对」。

## 零源站断言

本批只主张 clone 的读数。两个常数是 clone 自己的布局值，**源站未取证**。
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

WIDTHS = [360, 620, 780, 898, 899, 1024, 1440, 1920]
WIN_HEIGHTS = [328, 436, 900, 1150]
STORE = 182

GEOM_JS = """() => {
  const rd = (sel) => {
    const e = document.querySelector(sel);
    if (!e) return null;
    const r = e.getBoundingClientRect();
    const cs = getComputedStyle(e);
    return {t: Math.round(r.top*10)/10, l: Math.round(r.left*10)/10,
            w: Math.round(r.width*10)/10, h: Math.round(r.height*10)/10,
            b: Math.round(r.bottom*10)/10, r: Math.round(r.right*10)/10,
            computedH: parseFloat(cs.height), display: cs.display,
            position: cs.position};
  };
  return {viewport: rd('[data-director-viewport]'),
          timeline: rd('[data-director-timeline]'),
          bottomBar: rd('[data-director-bottom-bar]'),
          rail: rd('[data-director-icon-rail]'),
          tree: rd('aside[aria-label="场景对象"]'),
          inspector: rd('aside[aria-label="属性"]')};
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
    page.wait_for_timeout(120)
    page.evaluate("() => { for (const el of document.querySelectorAll('nextjs-portal'))"
                  " el.remove(); }")


def ask_collapse(page, want: bool) -> bool:
    attr = page.evaluate(
        "() => document.querySelector('[data-director-timeline]')"
        ".getAttribute('data-director-timeline-collapsed')")
    if (attr == "true") != want:
        label = "展开时间线" if attr == "true" else "时间线最小化"
        page.locator(f'[aria-label="{label}"]').first.click(timeout=15_000)
        page.wait_for_timeout(300)
    now = page.evaluate(
        "() => document.querySelector('[data-director-timeline]')"
        ".getAttribute('data-director-timeline-collapsed')")
    return (now == "true") == want


def measure(page, w: int, collapsed: bool, wh: int) -> dict[str, Any]:
    r = page.evaluate(b617.AUDIT_JS, list(b617.TRANSIENT_OVERLAYS))
    g = page.evaluate(GEOM_JS)
    z = page.evaluate(b623.BLIND_JS)
    vp, tl, bb = g["viewport"], g["timeline"], g["bottomBar"]
    rows = [(b["label"], b["box"], column_of(b["box"], g))
            for b in r["coveredByTimelineOverlay"]]
    blocked = [(b["label"], b["box"], b["panel"], b["timelineOverlay"],
                b["clipped"], b["victimInViewport"]) for b in r["blocked"]]
    shim = {"viewportTop": vp["t"] if vp else None,
            "viewportH": vp["h"] if vp else None,
            "band": bb["h"] if bb else None,
            "blocked": blocked}
    predicted = sorted(b629.predict(shim))
    observed = sorted({b["label"] for b in r["coveredByViewportSqueeze"]})
    return {
        "width": w, "narrow": w <= 898, "collapsed": collapsed, "windowH": wh,
        "vpTop": vp["t"] if vp else None, "vpH": vp["h"] if vp else None,
        "vpComputedH": vp["computedH"] if vp else None,
        "tlTop": tl["t"] if tl else None, "tlH": tl["h"] if tl else None,
        "band": bb["h"] if bb else None, "bandComputed": bb["computedH"] if bb else None,
        "bandDisplay": bb["display"] if bb else None,
        "bandPosition": bb["position"] if bb else None,
        "offViewport": len(r["offViewportItems"]),
        "unreachable": [(b["label"], b["box"]) for b in r["offViewportUnreachable"]],
        "zeroSize": z,
        "unexplained": [(b["label"], b["hitLabel"], b["box"]) for b in r["covered"]],
        "buriedCount": len({x[0] for x in rows}),
        "spill": max(0, tl["b"] - wh),
        "squeezeCount": len(observed),
        "predictAgrees": observed == predicted,
        "observedSqueeze": observed,
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
            page = br.new_page(viewport={"width": w, "height": 900},
                               device_scale_factor=1)
            b617.open_desk(page)
            for collapsed in (False, True):
                if not ask_collapse(page, collapsed):
                    toggle_failures.append(f"w{w}->{collapsed}")
                for wh in WIN_HEIGHTS:
                    page.set_viewport_size({"width": w, "height": wh})
                    page.wait_for_timeout(180)
                    page.evaluate("(n) => window.__director_store.getState()"
                                  ".setTimelineHeight(n)", STORE)
                    page.wait_for_timeout(200)
                    prep(page)
                    cells[f"w{w}/{'col' if collapsed else 'exp'}/wh={wh}"] = \
                        measure(page, w, collapsed, wh)
            page.close()
        br.close()

    out = {
        "batch": 639,
        "title": "instrument audit part 2 — viewportTop=88 and band=48 are genuinely "
                 "family-independent across 64 cells, and 629's closed form holds "
                 "in both families when fed measured inputs",
        "date": "2026-10-01",
        "widths": WIDTHS, "windowHeights": WIN_HEIGHTS, "storeHeight": STORE,
        "cells": cells,
    }

    n = len(cells)
    expected = len(WIDTHS) * 2 * len(WIN_HEIGHTS)
    v.check(f"the-grid-runs-{expected}-cells", n == expected, detail=n)
    v.check("the-collapse-toggle-is-reachable-and-flips-the-data-attribute",
            not toggle_failures, detail={"failedTransitions": toggle_failures})

    # --- the two constants -----------------------------------------------
    tops = sorted({r["vpTop"] for r in cells.values()})
    v.check("viewportTop-is-88-in-every-cell", tops == [88],
            detail={"distinctViewportTops": tops,
                    "cells": n, "families": sorted({r["narrow"] for r in cells.values()})})

    bands = sorted({r["band"] for r in cells.values()})
    v.check("the-bottom-band-is-48-in-every-cell", bands == [48],
            detail={"distinctBandHeights": bands,
                    "position": sorted({r["bandPosition"] for r in cells.values()}),
                    "display": sorted({r["bandDisplay"] for r in cells.values()})})

    # Instrument consistency, extended past the timeline.
    drift = {k: {"rect": r["vpH"], "computed": r["vpComputedH"]}
             for k, r in cells.items() if abs(r["vpH"] - r["vpComputedH"]) > 0.5}
    bdrift = {k: {"rect": r["band"], "computed": r["bandComputed"]}
              for k, r in cells.items() if abs(r["band"] - r["bandComputed"]) > 0.5}
    v.check("rect-and-computed-style-agree-for-the-viewport-and-the-band",
            not drift and not bdrift,
            detail={"viewportDrift": drift, "bandDrift": bdrift,
                    "whyItMatters": "this is the same sentinel 638 planted for the "
                                    "timeline height, now covering the two numbers "
                                    "629's formula consumes"})

    # --- the derived relation 635 relies on -------------------------------
    rel = {k: {"top": r["tlTop"], "vpH": r["vpH"], "topMinus88": round(r["tlTop"] - 88, 3)}
           for k, r in cells.items() if abs(r["vpH"] - (r["tlTop"] - 88)) > 0.5}
    v.check("viewportH-equals-the-timeline-top-minus-88-in-every-cell", not rel,
            detail={"violations": dict(list(rel.items())[:6]),
                    "note": "universal only because viewportTop really is 88; "
                            "if that constant ever moves, 635's relation moves with it"})

    # --- where the family dependence actually lives -----------------------
    # The delta is `desktopTimelineH - narrowTimelineH`, so its SIGN flips with
    # the state: +6 expanded (the narrow timeline is 6 shorter, so its viewport
    # is 6 TALLER) and -36 collapsed (the narrow timeline is 124 vs 88, i.e. 36
    # TALLER, so its viewport is 36 SHORTER).  My first version asserted
    # `delta == 6` — transcribed from the expanded rows only, the same mistake
    # this batch exists to catch.  Deriving it from the measured timeline
    # heights is what caught it.
    pair: dict[str, Any] = {}
    for collapsed in (False, True):
        for wh in WIN_HEIGHTS:
            n_cell = cells.get(f"w898/{'col' if collapsed else 'exp'}/wh={wh}")
            d_cell = cells.get(f"w1440/{'col' if collapsed else 'exp'}/wh={wh}")
            if n_cell and d_cell:
                pair[f"{'col' if collapsed else 'exp'}/wh={wh}"] = {
                    "narrowVpH": n_cell["vpH"], "desktopVpH": d_cell["vpH"],
                    "delta": round(n_cell["vpH"] - d_cell["vpH"], 3),
                    "predictedDelta": round(d_cell["tlH"] - n_cell["tlH"], 3)}
    v.check("the-family-gap-in-viewport-height-is-the-negated-timeline-height-gap",
            all(p["delta"] == p["predictedDelta"] for p in pair.values())
            and len(pair) == len(WIN_HEIGHTS) * 2,
            detail={"narrowMinusDesktopVpH": pair})

    by_state = {}
    for k, p in pair.items():
        by_state.setdefault(k.split("/")[0], set()).add(p["delta"])
    v.check("the-sign-of-the-family-gap-flips-between-expanded-and-collapsed",
            by_state.get("exp") == {6} and by_state.get("col") == {-36},
            detail={"expandedDelta": sorted(by_state.get("exp", [])),
                    "collapsedDelta": sorted(by_state.get("col", [])),
                    "reading": "expanded, the narrow timeline is 6 SHORTER so its "
                               "viewport is 6 TALLER; collapsed, the narrow "
                               "timeline is 36 TALLER (124 vs 88) so its viewport "
                               "is 36 SHORTER — the narrow family is the more "
                               "cramped one exactly when the user collapses the "
                               "timeline"})

    # --- 629's law, fed measured inputs, in both families -----------------
    pd = {k: {"observed": r["squeezeCount"]} for k, r in cells.items()
          if not r["predictAgrees"]}
    v.check("629s-closed-form-predicts-every-cell-including-the-narrow-family",
            not pd, detail=dict(list(pd.items())[:6]))

    nonempty = [k for k, r in cells.items() if r["squeezeCount"] > 0]
    empty = [k for k, r in cells.items() if r["squeezeCount"] == 0]
    v.check("the-squeeze-prediction-is-exercised-on-both-sides", bool(nonempty) and bool(empty),
            detail={"cellsWithSqueeze": len(nonempty), "cellsWithout": len(empty),
                    "squeezeCounts": sorted({r["squeezeCount"] for r in cells.values()})})
    v.check("the-narrow-family-is-actually-in-the-grid",
            sum(1 for r in cells.values() if r["narrow"]) == 32,
            detail={"narrowCells": sum(1 for r in cells.values() if r["narrow"])})

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

    sp = {k: r["spill"] for k, r in cells.items() if r["spill"] > 0.5}
    v.check("no-timeline-spills-past-the-window", not sp,
            detail=dict(list(sp.items())[:6]))

    out["checks"] = v.result
    out["ok"] = not v.failures
    out["checkCount"] = v.count
    out["failures"] = v.failures
    out["totals"] = {
        "unreachable": sum(len(r["unreachable"]) for r in cells.values()),
        "zeroSize": sum(len(r["zeroSize"]) for r in cells.values()),
        "unexplained": sum(len(r["unexplained"]) for r in cells.values()),
        "offViewport": sum(r["offViewport"] for r in cells.values()),
        "distinctViewportTops": tops,
        "distinctBandHeights": bands,
        "familyVpHDelta": pair,
        "squeezeCounts": sorted({r["squeezeCount"] for r in cells.values()}),
        "table": {k: {"vpTop": r["vpTop"], "vpH": r["vpH"], "band": r["band"],
                      "tlTop": r["tlTop"], "tlH": r["tlH"],
                      "squeeze": r["squeezeCount"]}
                  for k, r in cells.items()},
    }
    audit = ROOT / "docs/research/liblib-canvas-batch639-2026-10-01"
    audit.mkdir(parents=True, exist_ok=True)
    (audit / "runtime-audit.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2) + "\n")

    print(f"\n{v.count} checks, {len(v.failures)} failures")
    for f in v.failures:
        print("  FAILED: " + f)
    return 1 if v.failures else 0


if __name__ == "__main__":
    sys.exit(main())
