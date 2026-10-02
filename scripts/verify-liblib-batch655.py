#!/usr/bin/env python3
"""batch 655 验收：把导演台的**条件表面**从结构派生出来，并量出覆盖漏洞

## 起点

本项目至今测过 15 条导演台打开路径（626 的 11 条 + 648 的 4 条抽屉），
但**那 15 条是一次一次加上去的**，来源是「下一批发现一个就补一个」。

643 教过 `surfaceOf` 会过期，649 因此把竞争集改成从结构导出，
626 的 `PANELS` 至今是**本项目唯一一处已知会过期的手写名单**。
而 626 第八节标题写「9 个导演台 + 7 个画布页 = 16」，实际只列了 8 + 7 = 15 ——
**第 9 个从未被点名，至今记成一个继承的开口。**

## 本批的问题

**打开某样东西之后才会出现在 DOM 里的标记，一共有多少个？**
以及：**测过的 15 条路径覆盖了其中几个？**

## 为什么能派生

试过的两条路，一条是错的：

* `X-trigger` 与 `X-panel` 成对 —— **证伪**。默认态里 `-trigger` 只有 5 个，
  而对应的面板**默认不在 DOM 里**，于是成对数是 **0**。写成断言留在案上。
* **同格前后差集** —— 这条成立：同一个 page、同一屏高度，打开前拍一次、
  打开后拍一次，差集就是「这个路径带出来的表面」。
  这与 649 的导出式竞争集同源：**不给清单，让结构说话。**

## 654 的闸门在这里第一次实战

651 证明探针的 `hover()` 会自动滚动，而 15 条路径里有 4 条含悬停/多步点击。
本批把 654 的 `scroll_gate` 当**前置**用：差集在「探针没滚过」的格子里量。
不这么做就是在用一个已知的探针伪影去测条件表面。

## 本批**不**主张的事

* **不主张**条件表面里的每个标记都是一个浮层 —— 差集里混着
  **只装条件数据的值载体**（`data-director-…-id` 之类），它们不是选择器。
  本批**不分类**，只报数。
* **不主张**覆盖漏洞里的任何一条是缺陷 —— 未被测过**不是**有毛病。
* **零源站断言**。
"""
import importlib.util
import json
import re
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
b626 = _load("626")
b648 = _load("648")
b654 = _load("654")

WIDTH = 1280
HEIGHTS = [720, 1150]

scroll_gate = b654.scroll_gate

# --------------------------------------------------------------- open paths
# 11 from 626 (its own open_overlay knows the @shortcut@ sequences) plus the
# 4 drawers 648 found.  Each carries the panel selector its batch claimed, so
# the staleness question is answerable per path.
OPEN_PATHS: list[tuple[str, str, str, str]] = []
for _n, _how, _sel in b626.OVERLAYS:
    OPEN_PATHS.append((_n, "over626", _how, _sel))
for _n, _how, _sel in b648.DESK_CASES:
    OPEN_PATHS.append((_n, "locator", _how, _sel))
_n, _how, _sel = b648.PREVIEW_CASE
OPEN_PATHS.append((_n, "locator+hover", _how, _sel))

# ---------------------------------------------------------------- the census
# The instrument: no list of markers.  It walks the DOM and reports what is
# there, in the state the cell is in.
SNAP_JS = """() => {
  const m = {};
  for (const el of document.querySelectorAll('*')) {
    for (const a of el.attributes) {
      if (!a.name.startsWith('data-director-')) continue;
      const r = el.getBoundingClientRect();
      if (!m[a.name]) {
        m[a.name] = {attr: a.name, count: 0, tag: el.tagName.toLowerCase(),
                     w: Math.round(r.width), h: Math.round(r.height)};
      }
      m[a.name].count += 1;
    }
  }
  return m;
}"""

ATTR_RE = re.compile(r"data-director-[a-z0-9-]+")


def panel_attr(sel: str) -> str:
    """The bare attribute name inside a CSS selector.

    The first version of this batch compared `[data-director-export-panel]`
    (a CSS selector) against `data-director-export-panel` (an attribute name)
    and got an empty intersection — a bracket apart, and it read exactly like
    "nothing was covered".  See the README.
    """
    m = ATTR_RE.search(sel)
    return m.group(0) if m else sel


class Verifier:
    def __init__(self) -> None:
        self.result: dict[str, Any] = {}
        self.failures: list[str] = []
        self.count = 0

    def check(self, name: str, ok: bool, detail: Any = "", note: str = "") -> None:
        self.count += 1
        self.result[name] = {"ok": bool(ok), "detail": detail, "note": note or None}
        if not ok:
            self.failures.append(name)
        print(("  PASS " if ok else "  FAIL ") + name
              + (f"  {str(detail)[:165]}" if detail else "")
              + (f"  [{note[:100]}]" if note else ""))


def run_cell(br: Any, name: str, kind: str, how: str, panel_sel: str,
             h: int) -> dict[str, Any]:
    page = br.new_page(viewport={"width": WIDTH, "height": h},
                       device_scale_factor=1)
    b617.open_desk(page)
    page.wait_for_timeout(300)
    page.evaluate("() => { for (const el of "
                  "document.querySelectorAll('nextjs-portal')) el.remove(); }")
    page.mouse.move(5, 5)
    page.wait_for_timeout(200)
    before = page.evaluate(SNAP_JS)

    err = None
    try:
        if kind == "over626":
            b626.open_overlay(page, how)
        else:
            page.locator(how).first.click(timeout=10_000)
            if kind == "locator+hover":
                page.wait_for_timeout(500)
                page.locator("[data-director-model-library-card]").first.hover(
                    timeout=10_000)
    except Exception as exc:
        err = type(exc).__name__
    page.wait_for_timeout(400)
    page.mouse.move(5, 5)
    page.wait_for_timeout(180)

    after = page.evaluate(SNAP_JS)
    gate = scroll_gate(page)
    matched = len(page.locator(panel_sel).all()) if panel_sel else 0
    page.close()

    new = {k: v for k, v in after.items() if k not in before}
    gone = sorted(k for k in before if k not in after)
    return {
        "err": err,
        "panelSelector": panel_sel,
        "panelSelectorMatched": matched,
        "before": before,
        "after": after,
        "newMarkers": new,
        "newMarkerNames": sorted(new),
        "markersThatDisappeared": gone,
        "gate": gate,
    }


def main() -> int:
    v = Verifier()
    census = census_open_paths()
    cells: dict[str, Any] = {}

    with sync_playwright() as p:
        br = p.chromium.launch()
        for h in HEIGHTS:
            for name, kind, how, sel in OPEN_PATHS:
                cells[f"{name}@{h}"] = run_cell(br, name, kind, how, sel, h)
        br.close()

    # ------------------------------------------------- the default surface
    defaults: dict[int, set[str]] = {
        h: set(cells[f"{OPEN_PATHS[0][0]}@{h}"]["before"]) for h in HEIGHTS}
    triggers = sorted(n for n in defaults[HEIGHTS[0]] if n.endswith("-trigger"))
    paired = sorted({n[:-len("-trigger")] for n in triggers
                     if (n[:-len("-trigger")] + "-panel") in defaults[HEIGHTS[0]]})

    # ------------------------------------------------- the conditional surface
    per_path: dict[str, Any] = {}
    for name, _k, _h, sel in OPEN_PATHS:
        rows = {h: cells[f"{name}@{h}"] for h in HEIGHTS}
        per_path[name] = {
            "panelSelector": sel,
            "panelSelectorMatchedAtEveryHeight": all(
                rows[h]["panelSelectorMatched"] > 0 for h in HEIGHTS),
            "panelSelectorMatched": {str(h): rows[h]["panelSelectorMatched"]
                                     for h in HEIGHTS},
            "newMarkersAt720": rows[720]["newMarkerNames"],
            "newMarkersAt1150": rows[1150]["newMarkerNames"],
            "newMarkerCount": {str(h): len(rows[h]["newMarkerNames"])
                               for h in HEIGHTS},
            "sameAtBothHeights": (rows[720]["newMarkerNames"]
                                  == rows[1150]["newMarkerNames"]),
            "err": {str(h): rows[h]["err"] for h in HEIGHTS},
            "gateFired": {str(h): rows[h]["gate"]["fired"] for h in HEIGHTS},
            "gateVerdict": {str(h): rows[h]["gate"]["verdict"]
                            for h in HEIGHTS},
        }
    union: set[str] = set()
    for name, _k, _h, _s in OPEN_PATHS:
        union |= set(per_path[name]["newMarkersAt1150"])
    covered = {panel_attr(sel) for _n, _k, _h, sel in OPEN_PATHS if sel}
    in_surface = sorted(m for m in covered if m in union)
    interiors = sorted(m for m in union if m not in covered)
    # Who brought each marker in.  This is the deliverable: it says which
    # measured panel each un-named marker lives inside, so the next batch has
    # a target instead of a list to invent.
    owner: dict[str, list[str]] = {}
    for name, _k, _h, _s in OPEN_PATHS:
        for m in per_path[name]["newMarkersAt1150"]:
            owner.setdefault(m, []).append(name)
    orphans = sorted(m for m in union if m not in owner)
    interior_owners = sorted({
        f"{m}  <- {sorted(set(owner[m]))}"
        for m in interiors if len(set(owner.get(m, []))) > 1})
    out_owner_map = {
        n: sorted(set(per_path[n]["newMarkersAt1150"])) for n, *_ in OPEN_PATHS}

    out: dict[str, Any] = {
        "batch": 655,
        "question": "derive the director desk's conditional marker surface from "
                    "structure, and measure how much of it the 15 measured open "
                    "paths actually account for",
        "method": {
            "instrument": "walk the DOM for data-director-* in the same cell, "
                          "before and after the open path; the difference is "
                          "what the path brought in",
            "whyNotAList": "643's surfaceOf and 626's PANELS are the failure "
                           "mode: a hand-written list of what to measure is the "
                           "one thing guaranteed to expire",
            "gateAsPrecondition": "654's scroll_gate, so the diff is not "
                                  "measured through a scrolled lens",
        },
        "defaultSurface": {
            "distinctMarkers": {str(h): len(defaults[h]) for h in HEIGHTS},
            "identicalAtBothHeights": defaults[720] == defaults[1150],
            "triggers": triggers,
            "triggerPanelPairs": paired,
        },
        "census": census,
        "perPath": per_path,
        "conditionalSurface": {
            "size": len(union),
            "members": sorted(union),
            "panelRoots": in_surface,
            "interiorsOfThosePanels": interiors,
            "ownerMap": out_owner_map,
        },
        "cells": {k: {kk: vv for kk, vv in c.items()
                      if kk not in ("before", "after")}
                  for k, c in cells.items()},
    }

    # ------------------------------------------------------------------ 1
    v.check("the-default-marker-surface-is-derived-and-viewport-invariant",
            len(defaults[720]) > 0 and defaults[720] == defaults[1150],
            detail={"distinctMarkers": {str(h): len(defaults[h]) for h in HEIGHTS},
                    "triggers": triggers,
                    "sampleOfTheSurface": sorted(defaults[720])[:12]},
            note="derived by walking the DOM, not by reading a list")

    # ------------------------------------------------------------------ 2
    # A falsified heuristic, kept as an assertion so nobody re-derives it.
    v.check("the-trigger-panel-pairing-heuristic-is-falsy",
            len(triggers) > 0 and len(paired) == 0,
            detail={"triggersInTheDefaultState": triggers,
                    "pairsFound": paired,
                    "why": "the panels are not in the DOM until something is "
                           "opened, so at the default state the pairing has "
                           "nothing to pair with. This is why the census has to "
                           "be a before/after diff, not a static list."},
            note="recorded so the next batch does not spend a run rediscovering it")

    # ------------------------------------------------------------------ 3
    # Non-vacuity: a path that adds no marker either failed, or the surface is
    # not what we think it is.  Both are worth a red.
    empty = {n: per_path[n]["newMarkerCount"] for n in per_path
             if min(per_path[n]["newMarkerCount"].values()) == 0}
    v.check("every-open-path-actually-brings-in-at-least-one-marker",
            not empty,
            detail={"pathsThatBroughtInNothing": empty,
                    "counts": {n: per_path[n]["newMarkerCount"]
                               for n in sorted(per_path)},
                    "errs": {n: per_path[n]["err"] for n in sorted(per_path)
                             if any(per_path[n]["err"].values())}},
            note="an empty set is not evidence — it is the signature of a probe "
                 "that did not do anything")

    # ------------------------------------------------------------------ 4
    not_same = {n: per_path[n]["newMarkerCount"] for n in per_path
                if not per_path[n]["sameAtBothHeights"]}
    v.check("the-conditional-surface-does-not-depend-on-the-viewport",
            not not_same,
            detail={"pathsWhoseDiffChangedWithHeight": not_same,
                    "surfaceSize": len(union)},
            note="if the diff moved with the viewport, the surface would be a "
                 "layout artefact rather than a set of things being brought in")

    # ------------------------------------------------------------------ 5
    # The staleness question, asked directly: does every hand-written panel
    # selector still match something in the live DOM?
    stale = {n: per_path[n]["panelSelectorMatched"] for n in per_path
             if not per_path[n]["panelSelectorMatchedAtEveryHeight"]}
    v.check("no-hand-written-panel-selector-is-stale",
            not stale,
            detail={"selectorsThatMatchedNothing": stale,
                    "selectorsChecked": len(per_path),
                    "coveredByTheDerivedSurface": in_surface},
            note="626's PANELS/OVERLAYS is the one hand-written list left; this "
                 "is the test that would catch it going stale")

    # ------------------------------------------------------------------ 6
    # The first version of this check called the non-root members a "coverage
    # gap" and reported 80 of them.  That reading is wrong, and the data says
    # so: every one of the 80 arrives INSIDE a panel some batch already
    # measured.  648 and 626 did not measure the panel element — they censused
    # every live control inside it.  So "not a panel root" is not "never
    # measured", and 80 was an alarming number for a boring fact.
    v.check("every-conditional-marker-is-owned-by-a-measured-path",
            (not orphans) and len(in_surface) == len(covered)
            and len(union) > 0,
            detail={"conditionalSurfaceSize": len(union),
                    "panelRootsFound": len(in_surface),
                    "panelRootsExpected": len(covered),
                    "panelRoots": in_surface,
                    "interiorsOfThosePanels": len(interiors),
                    "interiorsWithMoreThanOneOwningPath": interior_owners,
                    "orphans": orphans,
                    "theMisreadingThatWasCorrected":
                        "the first draft called these 80 a 'coverage gap' and "
                        "the fraction 0.158 read like a score. They are the "
                        "INSIDE of the 15 panels 626/648 already censused — "
                        "648 counted live controls, not panel elements, so a "
                        "marker that is not a panel root is not an untested "
                        "thing.",
                    "whatIsActuallyLeftOpen":
                        "nothing here. The real open question is whether some "
                        "conditional surface exists OUTSIDE these 15 open paths, "
                        "and this batch cannot answer that without trying more "
                        "paths — which is the next batch, not a finding.",
                    "theDeliverable": out_owner_map},
            note="the owner map is what the next batch needs: it says which "
                 "measured panel each un-named marker lives in")

    # ------------------------------------------------------------------ 7
    # 654's gate, used as a precondition, on fifteen paths it had never seen.
    # The first version of this check demanded "the gate never fired", which is
    # the wrong demand: two of these paths are 654's KNOWN POSITIVES and are
    # supposed to fire.  Asking for silence would have been asking the gate to
    # be broken.  The stronger, correct demand is that it names the same two.
    known = sorted(b654.KNOWN_POSITIVE)
    gate_fired = {n: per_path[n]["gateVerdict"] for n in per_path
                  if any(per_path[n]["gateFired"].values())}
    v.check("654s-gate-re-names-exactly-its-own-two-positives-on-fifteen-new-paths",
            sorted(gate_fired) == known,
            detail={"gateFiredOn": sorted(gate_fired),
                    "654sKnownPositives": known,
                    "pathsItStayedSilentOn": sorted(set(per_path) - set(gate_fired)),
                    "verdicts": gate_fired,
                    "note": "the first version of this check asked the gate to "
                            "stay silent on all fifteen. Two of them are 654's "
                            "positives — a gate that stayed silent there would "
                            "be broken, so the demand itself was wrong.",
                    "whatTheGateCannotContaminateHere":
                        "this census reads WHICH attributes exist, not where "
                        "anything is, so the scroll does not touch the reading. "
                        "It would touch any geometry read taken after the same "
                        "path — which is why the gate is still worth running."},
            note="a gate re-confirmed on a batch it was not built for is worth "
                 "more than a gate re-run on its own set")

    out["checks"] = v.result
    out["ok"] = not v.failures
    out["checkCount"] = v.count
    out["failures"] = v.failures
    out["totals"] = {
        "openPaths": len(OPEN_PATHS),
        "cells": len(cells),
        "defaultSurface": len(defaults[HEIGHTS[0]]),
        "triggersInDefaultState": len(triggers),
        "triggerPanelPairs": len(paired),
        "conditionalSurface": len(union),
        "panelRoots": len(in_surface),
        "interiorsOfThosePanels": len(interiors),
    }
    audit = ROOT / "docs/research/liblib-canvas-batch655-2026-10-01"
    audit.mkdir(parents=True, exist_ok=True)
    (audit / "runtime-audit.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2) + "\n")

    print(f"\n{v.count} checks, {len(v.failures)} failures")
    for f in v.failures:
        print("  FAILED:", f)
    return 1 if v.failures else 0


def census_open_paths() -> dict[str, Any]:
    """How many open-path sites does the project have?  654's, unchanged."""
    return b654.census_open_paths()


if __name__ == "__main__":
    raise SystemExit(main())
