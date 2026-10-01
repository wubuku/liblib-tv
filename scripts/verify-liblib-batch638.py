#!/usr/bin/env python3
"""batch 638 验收：**审计我自己的量具** —— 把「时间轴高度」的三方真值表钉死。

## 为什么要审量具

636 在「高度恰好等于 182」时挖到 store 与 DOM 分歧；637 发现收起态下 store 被
完全忽略。两批都靠 `getBoundingClientRect` 取高度。但高度在代码里有**三个**独立的
表述来源，任何一个撒谎都会污染下游：

    store 的 timelineHeight  |  行内样式 / CSS 类  |  data-director-timeline-height 属性

`:794` 把属性写成 `timelineCollapsed ? 88 : timelineHeight` —— **收起态硬编码 88**，
而 ≤898 实际渲染 **124**。所以属性在「收起 + 窄族」这一格里**自己就是个错的数字**。

## 本批审的是「谁读了它」

全仓只有两个脚本读这个属性：

- `verify-liblib-batch607.py:109` —— 记录进 `attr`，并在 `:218/:271/:307` **把它当
  高度来断言**。但 607 同时断言了 `getComputedStyle` 的高度（合取），所以它没被
  属性单独骗过去；**问题是它的 viewport 是 1920×1150，只跑过桌面族**，于是
  「收起态 = 88」这条合同**只在桌面族成立而它从没说**。
- `verify-liblib-batch637.py:96` —— 记录进 `heightAttr`，但**所有断言都不用它**
  （断言一律用 rect 读出的 `timelineH`）。

629–637 其余各批**都不读这个属性**，只读 rect。本批把这两件事都做成断言，
这样以后有人开始读它时，红灯会告诉他读错了。

## 607 的合同被迁移，不是被删掉

`collapse:independent-of-resize`（607）断言 `(计算高 == 88 且 属性 == "88")`。
本批在三个宽度上**原样重放**这个合取：≥899 必须成立，**≤898 必须不成立**
（计算高 124、属性 88）。**红灯是预期内的、被断言要求的事实** ——
这正是 607 从未跑过的那一格。

## 零源站断言

源站窄屏的时间轴默认高度与收起高度**未取证**。本批只主张 clone 的读数，
**不发明新数**，也**不主张该往哪边修**（同 636/637 的处置）。
"""
import importlib.util
import json
import re
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
STORE_HEIGHTS = [88, 124, 176, 182, 240, 420]
CONTROL_WH = 1150        # tall: 630's clamp cannot fire, so CSS/inline decide
DESKTOP_DEFAULT = 182

# The two CSS-only answers, as established (and measured) by 636 and 637.
CSS_COLLAPSED = {False: 88, True: 124}        # keyed by narrow
CSS_AT_DEFAULT = {False: 182, True: 176}

GEOM_JS = """() => {
  const el = document.querySelector('[data-director-timeline]');
  if (!el) return null;
  const r = el.getBoundingClientRect();
  const cs = getComputedStyle(el);
  return {
    rectH: Math.round(r.height * 10) / 10,
    rectT: Math.round(r.top * 10) / 10,
    rectB: Math.round(r.bottom * 10) / 10,
    computedH: parseFloat(cs.height),
    inlineH: el.style.height || '',
    attr: el.getAttribute('data-director-timeline-height'),
    collapsedAttr: el.getAttribute('data-director-timeline-collapsed'),
  };
}"""

FULL_JS = """() => {
  const rd = (sel) => {
    const e = document.querySelector(sel);
    if (!e) return null;
    const r = e.getBoundingClientRect();
    return {t: Math.round(r.top*10)/10, l: Math.round(r.left*10)/10,
            w: Math.round(r.width*10)/10, h: Math.round(r.height*10)/10,
            b: Math.round(r.bottom*10)/10, r: Math.round(r.right*10)/10,
            display: getComputedStyle(e).display};
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
    page.wait_for_timeout(140)
    page.evaluate("() => { for (const el of document.querySelectorAll('nextjs-portal'))"
                  " el.remove(); }")


def ask_height(page, th: int) -> None:
    page.evaluate("(n) => window.__director_store.getState().setTimelineHeight(n)", th)
    page.wait_for_timeout(200)


def ask_collapse(page, want: bool) -> bool:
    attr = page.evaluate(
        "() => document.querySelector('[data-director-timeline]')"
        ".getAttribute('data-director-timeline-collapsed')")
    is_now = attr == "true"
    if is_now != want:
        label = "展开时间线" if is_now else "时间线最小化"
        page.locator(f'[aria-label="{label}"]').first.click(timeout=15_000)
        page.wait_for_timeout(320)
    now = page.evaluate(
        "() => document.querySelector('[data-director-timeline]')"
        ".getAttribute('data-director-timeline-collapsed')")
    # Compare against `want`.  My first version returned the current state
    # instead, so every already-correct state was logged as a failed
    # transition — a harness bug that looked like three broken toggles.
    return (now == "true") == want


def classify(collapsed: bool, store: int, narrow: bool) -> tuple[str, float]:
    """Which of the three regimes a cell is in, and what it must render."""
    if collapsed:
        return "collapsed-css-only", float(CSS_COLLAPSED[narrow])
    if store == DESKTOP_DEFAULT:
        return "expanded-at-default-css", float(CSS_AT_DEFAULT[narrow])
    return "expanded-inline", float(store)


def measure(page, w: int, collapsed: bool, store: int) -> dict[str, Any]:
    r = page.evaluate(b617.AUDIT_JS, list(b617.TRANSIENT_OVERLAYS))
    g = page.evaluate(FULL_JS)
    h = page.evaluate(GEOM_JS)
    store_h = page.evaluate(
        "() => window.__director_store.getState().timelineHeight")
    vp, tl = g["viewport"], g["timeline"]
    narrow = w <= 898
    regime, predicted = classify(collapsed, store, narrow)
    rows = [(b["label"], b["box"], column_of(b["box"], g))
            for b in r["coveredByTimelineOverlay"]]
    labels = sorted({x[0] for x in rows})
    blocked = [(b["label"], b["box"], b["panel"], b["timelineOverlay"],
                b["clipped"], b["victimInViewport"]) for b in r["blocked"]]
    shim = {"viewportTop": vp["t"] if vp else None,
            "viewportH": vp["h"] if vp else None,
            "band": g["bottomBar"]["h"] if g["bottomBar"] else 48,
            "blocked": blocked}
    predicted_squeeze = sorted(b629.predict(shim))
    observed_squeeze = sorted({b["label"] for b in r["coveredByViewportSqueeze"]})
    return {
        "width": w, "narrow": narrow, "collapsed": collapsed,
        "storeRequested": store, "storeHeight": store_h,
        "regime": regime, "predictedHeight": predicted,
        "rectH": h["rectH"], "computedH": h["computedH"], "inlineH": h["inlineH"],
        "attr": h["attr"], "collapsedAttr": h["collapsedAttr"],
        "attrSays": float(h["attr"]) if h["attr"] and h["attr"].isdigit() else None,
        "attrTruthful": h["attr"] is not None
                        and abs(float(h["attr"]) - h["computedH"]) < 0.5,
        "607Conjunction": (abs(h["computedH"] - 88) < 0.6 and h["attr"] == "88"),
        "spill": max(0, tl["b"] - CONTROL_WH),
        "offViewport": len(r["offViewportItems"]),
        "unreachable": [(b["label"], b["box"]) for b in r["offViewportUnreachable"]],
        "zeroSize": page.evaluate(b623.BLIND_JS),
        "unexplained": [(b["label"], b["hitLabel"], b["box"]) for b in r["covered"]],
        "buriedCount": len(labels),
        "aboveTimelineTop": [x[0] for x in rows
                             if x[1][1] + x[1][3] <= tl["t"] + 0.5],
        "predictAgrees": observed_squeeze == predicted_squeeze,
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
                for store in STORE_HEIGHTS:
                    ask_height(page, store)
                    page.wait_for_timeout(200)
                    prep(page)
                    cells[f"w{w}/{'col' if collapsed else 'exp'}/store={store}"] = \
                        measure(page, w, collapsed, store)
            page.close()
        br.close()

    out = {
        "batch": 638,
        "title": "instrument audit — the three-way truth table for the timeline's "
                 "height, and where data-director-timeline-height lies",
        "date": "2026-10-01",
        "widths": WIDTHS, "storeHeights": STORE_HEIGHTS,
        "cssCollapsed": {str(k): v2 for k, v2 in CSS_COLLAPSED.items()},
        "cssAtDefault": {str(k): v2 for k, v2 in CSS_AT_DEFAULT.items()},
        "cells": cells,
    }

    n = len(cells)
    expected = len(WIDTHS) * 2 * len(STORE_HEIGHTS)
    v.check(f"the-grid-runs-{expected}-cells", n == expected, detail=n)

    v.check("the-collapse-toggle-is-reachable-and-flips-the-data-attribute",
            not toggle_failures, detail={"failedTransitions": toggle_failures})

    # --- THE TRUTH TABLE -------------------------------------------------
    wrong = {k: {"regime": r["regime"], "store": r["storeRequested"],
                 "predicted": r["predictedHeight"], "computed": r["computedH"]}
             for k, r in cells.items()
             if abs(r["computedH"] - r["predictedHeight"]) > 0.5}
    v.check("every-cell-renders-what-its-regime-predicts", not wrong,
            detail={"wrong": dict(list(wrong.items())[:6])})

    # Non-vacuity: the three regimes must all be populated, or the table above
    # could be satisfied by a single regime's rule.
    regimes = {}
    for r in cells.values():
        regimes.setdefault(r["regime"], set()).add(
            (r["narrow"], r["collapsed"], r["storeRequested"] == DESKTOP_DEFAULT))
    v.check("all-three-height-regimes-are-exercised", len(regimes) == 3,
            detail={k: len(v2) for k, v2 in regimes.items()})

    only182 = {k: {"store": r["storeRequested"], "computed": r["computedH"]}
               for k, r in cells.items()
               if not r["collapsed"] and r["storeRequested"] != DESKTOP_DEFAULT
               and abs(r["computedH"] - r["storeRequested"]) > 0.5}
    v.check("182-is-the-only-store-value-that-goes-to-css", not only182,
            detail={"swept": STORE_HEIGHTS, "rewritten": only182})

    # --- where the attribute lies ----------------------------------------
    # Derived from the mechanism, NOT from a list I typed from memory.  My
    # first version hardcoded "collapsed and narrow" and went red on
    # `w898/exp/store=182` — the 636 cell, which I had forgotten.  The two
    # cells are the same bug seen twice: the attribute mirrors the STORE,
    # while the DOM follows CSS on exactly the two occasions the inline style
    # is omitted.  Deriving the expected set keeps it honest when the code
    # changes; a transcribed list would have hidden 636's own finding.
    liars = sorted(k for k, r in cells.items() if not r["attrTruthful"])
    expect_liars = sorted(
        k for k, r in cells.items()
        if r["narrow"] and (r["collapsed"] or r["storeRequested"] == DESKTOP_DEFAULT))
    v.check("the-height-attribute-lies-in-exactly-the-two-css-handoff-cells",
            liars == expect_liars,
            detail={"liars": liars, "derived": expect_liars,
                    "whatItSays": {k: {"attr": cells[k]["attr"],
                                       "computed": cells[k]["computedH"]}
                                   for k in liars[:8]},
                    "whyItLies": "the attribute mirrors the store, but the DOM "
                                 "follows CSS on the two handoffs: collapsed "
                                 "(`:794` hardcodes 88 while the narrow CSS is "
                                 "124) and store==182 (the inline style is "
                                 "omitted while the narrow CSS is 176)"})

    attr_mirrors_store = {k: {"attr": r["attr"], "store": r["storeHeight"]}
                          for k, r in cells.items()
                          if not r["collapsed"] and r["attr"] != str(r["storeHeight"])}
    v.check("while-expanded-the-attribute-is-always-just-the-store-value",
            not attr_mirrors_store,
            detail={"mismatches": attr_mirrors_store,
                    "collapsedAttr": sorted({r["attr"] for r in cells.values()
                                             if r["collapsed"]}),
                    "collapsedStoreValues": sorted({r["storeHeight"] for r in
                                                    cells.values()
                                                    if r["collapsed"]})})

    # --- the instrument the other batches actually used -------------------
    rectbad = {k: {"rect": r["rectH"], "computed": r["computedH"]}
               for k, r in cells.items() if abs(r["rectH"] - r["computedH"]) > 0.5}
    v.check("the-rect-readers-629-to-637-were-reading-the-true-height", not rectbad,
            detail={"divergentCells": rectbad,
                    "whyItMatters": "629-637 derive every height claim from "
                                    "getBoundingClientRect, so this is the "
                                    "check that those claims are sound"})

    # --- 607's own contract, replayed per width ---------------------------
    by_width: dict[str, Any] = {}
    for w in WIDTHS:
        col = [r for r in cells.values() if r["width"] == w and r["collapsed"]]
        by_width[str(w)] = {"conjunctionHolds": all(r["607Conjunction"] for r in col),
                            "computed": sorted({r["computedH"] for r in col}),
                            "attr": sorted({r["attr"] for r in col})}
    v.check("607s-collapse-contract-holds-only-in-the-desktop-family",
            by_width["1440"]["conjunctionHolds"]
            and by_width["899"]["conjunctionHolds"]
            and not by_width["898"]["conjunctionHolds"],
            detail={"perWidth": by_width,
                    "607Viewport": "1920x1150 (desktop only)",
                    "607Assertion": "computed==88 AND attr=='88'"})

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

    above = {k: r["aboveTimelineTop"] for k, r in cells.items()
             if r["aboveTimelineTop"]}
    v.check("every-buried-control-sits-below-the-timelines-top-edge", not above,
            detail=dict(list(above.items())[:6]))

    sp = {k: r["spill"] for k, r in cells.items() if r["spill"] > 0.5}
    v.check("no-timeline-spills-past-the-window", not sp,
            detail=dict(list(sp.items())[:6]))

    pd = {k: {} for k, r in cells.items() if not r["predictAgrees"]}
    v.check("629s-closed-form-predicts-the-squeeze-in-every-cell", not pd,
            detail=dict(list(pd.items())[:6]))

    # --- who reads the attribute: a static audit of sibling scripts -------
    readers: dict[str, dict[str, Any]] = {}
    for path in sorted((ROOT / "scripts").glob("verify-liblib-batch*.py")):
        text = path.read_text()
        if "data-director-timeline-height" not in text:
            continue
        uses_attr_in_assertion = bool(
            re.search(r'attr["\']?\]\s*==|\["attr"\]', text))
        cross_checks_geometry = "getComputedStyle" in text
        readers[path.name] = {"usesAttrInAnAssertion": uses_attr_in_assertion,
                              "alsoReadsComputedGeometry": cross_checks_geometry}
    unsound = {k: r2 for k, r2 in readers.items()
               if r2["usesAttrInAnAssertion"] and not r2["alsoReadsComputedGeometry"]}
    v.check("every-script-that-asserts-on-the-height-attribute-also-reads-geometry",
            not unsound,
            detail={"readers": readers, "unsound": unsound,
                    "note": "637 records the attribute but asserts on the rect; "
                            "607 asserts on both, so neither is fooled by it"})

    out["checks"] = v.result
    out["ok"] = not v.failures
    out["checkCount"] = v.count
    out["failures"] = v.failures
    out["totals"] = {
        "unreachable": sum(len(r["unreachable"]) for r in cells.values()),
        "zeroSize": sum(len(r["zeroSize"]) for r in cells.values()),
        "unexplained": sum(len(r["unexplained"]) for r in cells.values()),
        "offViewport": sum(r["offViewport"] for r in cells.values()),
        "truthTable": {
            f"{'narrow' if r['narrow'] else 'desktop'}"
            f"/{'collapsed' if r['collapsed'] else 'expanded'}"
            f"/store={r['storeRequested']}": {
                "regime": r["regime"], "store": r["storeHeight"],
                "computed": r["computedH"], "attr": r["attr"],
                "inline": r["inlineH"] or "(none)"}
            for r in cells.values()},
        "attributeLiars": liars,
        "con607": by_width,
        "attributeReaders": readers,
    }
    audit = ROOT / "docs/research/liblib-canvas-batch638-2026-10-01"
    audit.mkdir(parents=True, exist_ok=True)
    (audit / "runtime-audit.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2) + "\n")

    print(f"\n{v.count} checks, {len(v.failures)} failures")
    for f in v.failures:
        print("  FAILED: " + f)
    return 1 if v.failures else 0


if __name__ == "__main__":
    sys.exit(main())
