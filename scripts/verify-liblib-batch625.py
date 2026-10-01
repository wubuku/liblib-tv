#!/usr/bin/env python3
"""Batch 625 — check the stacking of every rail flyout, because "the geometry
does not overlap" is not the same claim as "the z-index is in effect".

Batch 624 found the AI-import modal's `z-[290]` had never once taken effect: it
is rendered inside `DirectorIconRail`, whose `absolute ... z-30` creates a
stacking context, so the modal's effective z at the workspace level was 30 —
below the timeline's 40.  Nothing was visibly wrong at 1920x1150, which is
exactly why 619's sweep called that state clean.

The same ruler is applied here to the five flyouts that live in the rail:

    character-flyout   z-40      geometry-submenu   z-50
    panorama-flyout    z-40      crowd-dialog       z-50
    aspect-flyout      z-40

All five are children of the rail, so all five have an **effective** z of 30
even though their class names say 40 or 50.  This batch measures that directly
(the nearest ancestor stacking context is what a z-index actually competes in)
and then measures the consequence: for every control whose centre lands inside
the timeline's rect, does it take its own hit?

Both halves matter.  The structural half says "the z is trapped"; the
geometric half says "and here is a control it traps".  Asserting only the
first would be a claim about code shape; asserting only the second would go
blind whenever the current viewport happens not to overlap — which is the
mistake that hid 624's bug from 619.

Note the deliberate asymmetry with the 624 fix: a flyout is a *transient menu*
anchored to its trigger, and the source's own rail menus are not measured at
any of these widths, so this batch does not decide the source question.  It
decides the clone question: a control the user can see must be clickable.

Usage: python3 verify-liblib-batch625.py
"""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = ROOT / "docs/research/liblib-canvas-batch625-2026-10-01/runtime-audit.json"

_spec = importlib.util.spec_from_file_location(
    "b619", ROOT / "scripts/verify-liblib-batch619.py")
b619 = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(b619)

IGNORE_PAGE_ERROR = ("TransformControls",)

# (label, rail entry to click, an option to click *inside* the flyout, overlay)
# The two submenu kinds are not top-level rail entries at all: 群众 (3x3) and
# 几何模型 are rendered as rows inside the 添加角色 flyout, so they need the
# parent opened first.  The first pass of the probe got this wrong twice —
# once by treating them as rail entries (timeouts) and once by passing a
# "@geometry@" sentinel straight to locator() (unsupported token).
FLOUTS: list[tuple[str, str, str | None, str]] = [
    ("panorama-flyout", "[data-director-rail-entry='panorama']", None,
     "[data-director-panorama-flyout]"),
    ("aspect-flyout", "[data-director-rail-entry='aspect-ratio']", None,
     "[data-director-aspect-flyout]"),
    ("add-character-flyout", "[data-director-rail-entry='add-character']", None,
     "[data-director-character-flyout]"),
    ("geometry-submenu", "[data-director-rail-entry='add-character']",
     "[data-director-character-option='geometry']",
     "[data-director-geometry-submenu]"),
    ("crowd-dialog", "[data-director-rail-entry='add-character']",
     "[data-director-character-option='crowd-3x3']",
     "[data-director-crowd-dialog]"),
]

# Deliberately includes short viewports: the timeline is a fixed 182px tall at
# the bottom, so the shorter the window the larger its share of the height and
# the more likely a tall flyout reaches into it.
VIEWPORTS = [(1920, 1150), (1440, 900), (1280, 720), (1920, 844), (1100, 700)]

MEASURE_JS = r"""(sel) => {
  const el = document.querySelector(sel);
  if (!el) return {missing: true};
  const createsCtx = (cs) =>
    (cs.position !== 'static' && cs.zIndex !== 'auto') ||
    cs.transform !== 'none' || cs.filter !== 'none' ||
    cs.backdropFilter !== 'none' || cs.isolation === 'isolate' ||
    cs.perspective !== 'none' || cs.opacity !== '1' ||
    cs.mixBlendMode !== 'normal' || cs.contain.includes('paint') ||
    cs.willChange !== 'auto' || cs.containerType !== 'normal';
  const nm = (n) => n.tagName.toLowerCase() +
    (Object.keys(n.dataset || {}).filter(k => k.startsWith('director') || k.startsWith('liblib')).length
      ? '[' + Object.keys(n.dataset).filter(k => k.startsWith('director') || k.startsWith('liblib')).join(',') + ']' : '');
  // the nearest ancestor stacking context is where this element's z competes;
  // its own z means nothing outside that context
  let ctxEl = null, n = el.parentElement;
  while (n && n !== document.body) {
    if (createsCtx(getComputedStyle(n))) { ctxEl = n; break; }
    n = n.parentElement;
  }
  const r = el.getBoundingClientRect();
  const tl = document.querySelector('[data-director-timeline]');
  const tr = tl ? tl.getBoundingClientRect() : null;
  const lbl = (b) => b.getAttribute('aria-label')
                    || (b.textContent || '').trim().slice(0, 16)
                    || b.tagName.toLowerCase();
  const inBand = [];
  let nCtrls = 0;
  for (const b of el.querySelectorAll('button, [role="button"], [role="menuitem"], a[href], input')) {
    const br = b.getBoundingClientRect();
    if (br.width <= 0 || br.height <= 0) continue;
    nCtrls += 1;
    const cx = br.x + br.width / 2, cy = br.y + br.height / 2;
    if (!tr) continue;
    if (cx >= tr.x && cx <= tr.x + tr.width && cy >= tr.y && cy <= tr.y + tr.height) {
      const h = document.elementFromPoint(cx, cy);
      inBand.push({label: lbl(b),
                   box: [Math.round(br.x), Math.round(br.y), Math.round(br.width), Math.round(br.height)],
                   hitSelf: !!(h && (h === b || b.contains(h))),
                   hitLabel: h ? (h.getAttribute('aria-label')
                                  || (h.textContent || '').trim().slice(0, 16)
                                  || h.tagName.toLowerCase()) : null});
    }
  }
  return {
    ownZ: getComputedStyle(el).zIndex,
    ctxEl: ctxEl ? nm(ctxEl) : null,
    ctxZ: ctxEl ? getComputedStyle(ctxEl).zIndex : null,
    box: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
    timeline: tr ? [Math.round(tr.x), Math.round(tr.y), Math.round(tr.width), Math.round(tr.height)] : null,
    nCtrls, inBand,
  };
}"""


def open_flyout(page: Any, trig: str, option: str | None, overlay: str) -> None:
    page.locator(trig).first.click(timeout=10_000)
    if option:
        # the submenu kinds are rows inside the 添加角色 flyout
        page.wait_for_timeout(500)
        page.locator(option).first.click(timeout=10_000)
    page.locator(overlay).first.wait_for(state="visible", timeout=10_000)


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


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 625,
        "title": "check the stacking of every rail flyout: the z-index is in "
                 "effect, and no control that lands inside the timeline is "
                 "covered by it",
        "date": "2026-10-01",
        "sourceEvidence": [
            "no live source reading: the shared source tab is at 1600x1000 "
            "with another user in it (probe616), so this batch makes no "
            "fidelity claim — in particular it does not decide what the "
            "source's rail menus do at these widths",
            "batch 624's finding, applied here as a method: the AI-import "
            "modal's z-[290] was trapped in the rail's z-30 context and never "
            "took effect, and it was invisible to the sweep because at "
            "1920x1150 nothing overlapped",
            "/tmp/dbg625a.py: first pass — established that all five rail "
            "flyouts declare z-40/z-50 while their nearest stacking context "
            "is the rail at z-30, and exposed two wrong triggers "
            "(geometry-submenu, crowd-dialog) plus a hit-test that measured "
            "the wrong control",
            "/tmp/dbg625b.py: second pass — correct triggers, and the hit test "
            "restricted to controls whose centre lies inside the timeline rect",
        ],
        "claims": {
            "cloneDecision": [],
            "notClaimed": [
                "anything about the source — not the flyouts' z, not whether "
                "the source lets a rail menu cover its timeline, nothing",
                "that a flyout with no control in the timeline band is fine. "
                "That is a statement about this viewport only, which is "
                "exactly the hole 624 fell into",
            ],
        },
        "viewports": [list(v) for v in VIEWPORTS],
    }
    v = Verifier()
    rows: list[dict[str, Any]] = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for vw, vh in VIEWPORTS:
            for label, trig, option, overlay in FLOUTS:
                page = browser.new_page(viewport={"width": vw, "height": vh},
                                        device_scale_factor=1)
                errors: list[str] = []
                page.on("pageerror", lambda e: errors.append(str(e)[:160]))
                row: dict[str, Any] = {"vw": vw, "vh": vh, "flyout": label}
                try:
                    b619.open_desk(page)
                    open_flyout(page, trig, option, overlay)
                    page.wait_for_timeout(700)
                    page.mouse.move(5, 5)
                    page.wait_for_timeout(150)
                    row.update(page.evaluate(MEASURE_JS, overlay))
                    row["pageErrors"] = [e for e in errors
                                         if not any(k in e for k in IGNORE_PAGE_ERROR)]
                except Exception as exc:  # noqa: BLE001
                    row["error"] = f"{type(exc).__name__}: {str(exc)[:120]}"
                finally:
                    page.close()
                rows.append(row)
        browser.close()

    live = [r for r in rows if "error" not in r]
    audit["measurements"] = rows
    v.check("every-flyout-opens-at-every-viewport", len(live) == len(rows),
            detail={"live": len(live), "total": len(rows),
                    "errors": [(r["flyout"], r.get("error")) for r in rows
                               if "error" in r][:4]})

    # 1. structural: the effective z is what the class name says it is
    trapped = [(r["flyout"], r["vw"], r["vh"], r["ownZ"], r["ctxZ"], r["ctxEl"])
               for r in live
               if r["ctxEl"] and r["ctxZ"] not in (None, "auto")
               and int(r["ownZ"]) > int(r["ctxZ"])]
    v.result["trapped"] = trapped
    v.check("no-flyout-has-a-z-trapped-below-its-own-number",
            not trapped, detail=trapped[:5])

    # 2. geometric: no control inside the timeline band is covered
    covered = [(r["flyout"], r["vw"], r["vh"],
                [(c["label"], c["hitLabel"]) for c in r["inBand"] if not c["hitSelf"]])
               for r in live
               if any(not c["hitSelf"] for c in r["inBand"])]
    v.result["covered"] = covered
    v.check("no-control-inside-the-timeline-band-is-covered", not covered,
            detail=covered[:5])

    # 3. the check must not be vacuous: the flyouts really do carry controls,
    #    and record how many land in the band so a reader can see the coverage
    v.check("the-flyouts-really-carry-controls",
            all(r["nCtrls"] > 0 for r in live),
            detail=sorted({(r["flyout"], r["nCtrls"]) for r in live}))
    v.result["controlsInTimelineBand"] = {
        f"{r['flyout']}@{r['vw']}x{r['vh']}": len(r["inBand"]) for r in live
        if r["inBand"]}

    # 4. the portal changed stacking only, not geometry.  These boxes were
    #    measured before the change (runtime-audit.json of the first run, and
    #    /tmp/dbg625b.py); the rail is viewport-anchored, so a flyout's box must
    #    be identical at every width and height.  A portal that nudged a flyout
    #    by even a pixel would be a silent fidelity regression.
    BEFORE = {
        "panorama-flyout": [48, 196, 232, 134],
        "aspect-flyout": [48, 236, 232, 350],
        "add-character-flyout": [48, 116, 232, 390],
        "geometry-submenu": [52, 508, 204, 270],
        "crowd-dialog": [294, 52, 220, 208],
    }
    moved = [(r["flyout"], r["vw"], r["vh"], r["box"], BEFORE[r["flyout"]])
             for r in live if r["box"] != BEFORE[r["flyout"]]]
    v.result["geometryBefore"] = BEFORE
    v.check("the-portal-moved-nothing", not moved, detail=moved[:5])

    audit["checks"] = v.result
    audit["result"] = f"{v.count - len(v.failures)}/{v.count} passed"
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2))
    print(f"\n{audit['result']}")
    if v.failures:
        print("FAILED: " + ", ".join(v.failures))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
