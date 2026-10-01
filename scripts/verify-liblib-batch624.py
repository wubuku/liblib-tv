#!/usr/bin/env python3
"""Batch 624 — sweep width × open-state, not width alone.

623 swept 86 widths but only the **plain** state.  Every real defect the
census has caught so far lived in an **open** state: 619's narrow export
panel crushed by the viewport bottom bar, 620's asset sidebar footer button
buried by the canvas toolbar, 618's property drawer tucked under the header.
Plain-state sweeps cannot see any of those.

So this batch multiplies the two dimensions.  The hard part is not running
it, it is deciding which cells are even meaningful:

  * the rail flyouts (panorama / aspect / add-character / ai-import) hang off
    the resource rail, which is `display:none` at <= 898 — clicking one at
    500px fails because **the state does not exist there**, not because of a
    defect;
  * the drawers exist only below the breakpoint, and at >= 899 the buttons
    that open them are not rendered at all;
  * the tree context menu needs the tree drawer opened first on narrow.

Each cell therefore carries an applicability rule.  A cell that does not
apply is recorded as skipped, never as a failure — otherwise most of the
matrix would be false red.

The census itself is 619's, which already carries the coveredByPanel
attribution rule ("something an open transient panel covers is not a
defect"), so `unexpected` here really is the defect list.

Usage: python3 verify-liblib-batch624.py
"""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = ROOT / "docs/research/liblib-canvas-batch624-2026-10-01/runtime-audit.json"

_spec = importlib.util.spec_from_file_location(
    "b619", ROOT / "scripts/verify-liblib-batch619.py")
b619 = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(b619)

IGNORE_PAGE_ERROR = ("TransformControls",)

# Batch 623 established the boundary: narrow is <= 898, desktop is >= 899.
DESKTOP_MIN = 899
WIDTHS = [390, 620, 768, 850, 898, 899, 900, 1024, 1440, 1920]


def states_for(w: int) -> list[tuple[str, str, str | None]]:
    desk = w >= DESKTOP_MIN
    out: list[tuple[str, str, str | None]] = [
        ("export-panel", "[data-director-export-trigger]",
         "[data-director-export-panel]"),
    ]
    if desk:
        out += [
            ("rail-panorama", "[data-director-rail-entry='panorama']",
             "[data-director-panorama-flyout]"),
            ("rail-aspect", "[data-director-rail-entry='aspect-ratio']",
             "[data-director-aspect-flyout]"),
            ("rail-add-character", "[data-director-rail-entry='add-character']",
             "[data-director-character-flyout]"),
            ("rail-ai-import", "[data-director-rail-entry='ai-import']",
             "[data-director-ai-import-modal]"),
            ("tree-context-menu", "@tree-rctx@",
             "[data-director-tree-context-menu]"),
        ]
    else:
        out += [
            ("tree-context-menu", "@tree-drawer+@tree-rctx@",
             "[data-director-tree-context-menu]"),
            ("track-context-menu", "@track-rctx@", None),
        ]
    return out


def open_state(page: Page, setup: str) -> bool:
    try:
        if setup == "@tree-drawer+@tree-rctx@":
            btn = page.locator("button[aria-label='打开场景对象']")
            if btn.count() == 0:
                return False
            btn.first.click(timeout=8_000)
            page.wait_for_timeout(600)
            page.locator("[data-director-tree] [data-director-object-id]").first.click(
                button="right", timeout=8_000)
            return True
        if setup == "@tree-rctx@":
            page.locator("[data-director-tree] [data-director-object-id]").first.click(
                button="right", timeout=8_000)
            return True
        if setup == "@track-rctx@":
            page.locator("[data-director-timeline-object-row]").first.click(
                button="right", timeout=8_000)
            return True
        loc = page.locator(setup)
        if loc.count() == 0:
            return False
        loc.first.click(timeout=8_000)
        return True
    except Exception:  # noqa: BLE001
        return False


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


GEOM_JS = """() => {
  const at = (sel) => { const e = document.querySelector(sel); if (!e) return null;
    const r = e.getBoundingClientRect();
    return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]; };
  const modal = document.querySelector('[data-director-ai-import-modal]');
  const backdrop = document.querySelector('[data-director-ai-import-backdrop]');
  // The regression: the modal used to be rendered inside the resource rail, so
  // its z-[290] was trapped in the rail's z-30 stacking context.  Assert the
  // rail is NOT an ancestor — that is the structural cause, and geometry alone
  // would only show it at the widths/heights where the two happen to overlap.
  const inRail = (el) => { let n = el; while (n && n !== document.body) {
    if (n.hasAttribute && n.hasAttribute('data-director-icon-rail')) return true;
    n = n.parentElement; } return false; };
  return {
    vw: innerWidth, vh: innerHeight,
    modal: at('[data-director-ai-import-modal]'),
    backdrop: at('[data-director-ai-import-backdrop]'),
    modalInRail: modal ? inRail(modal) : null,
    backdropInRail: backdrop ? inRail(backdrop) : null,
    backdropZ: backdrop ? getComputedStyle(backdrop).zIndex : null,
    inspector: at('aside[aria-label="属性"]'),
    timeline: at('[data-director-timeline]'),
  };
}"""


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 624,
        "title": "sweep width x open-state: the census multiplied by the state "
                 "dimension, with per-width applicability rules",
        "date": "2026-10-01",
        "sourceEvidence": [
            "no live source reading: the shared source tab is at 1600x1000 "
            "with another user in it (probe616), so this batch makes no "
            "fidelity claim",
            "the defect history that motivates the state dimension: 619 found "
            "the narrow export panel crushed by data-director-bottom-bar "
            "z-[200]; 620 found the asset sidebar footer button buried by the "
            "canvas toolbar; 618 found the property drawer under the header. "
            "All three are open states; none is visible in a plain-state sweep",
            "/tmp/dbg624a.py: the matrix, each cell on a fresh page load",
        ],
        "claims": {
            "cloneDecision": [
                "the census runs over 10 widths x the states that exist at "
                "each, with cells that do not apply recorded as skipped rather "
                "than failed",
            ],
            "notClaimed": [
                "anything about the source at all",
                "completeness. 10 widths is a sample, not the 86 of 623, and "
                "only the states reachable from a director-desk control are "
                "covered — the camera preset panel and the motion path menu "
                "need a camera track selected first and are not in this matrix",
                "that the state list is complete. It is the set 619 could open "
                "from a plain desk, plus the tree/track context menus",
            ],
        },
        "widths": WIDTHS,
        "desktopMin": DESKTOP_MIN,
    }
    v = Verifier()
    cells: list[dict[str, Any]] = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for w in WIDTHS:
            for name, setup, overlay in states_for(w):
                page = browser.new_page(viewport={"width": w, "height": 900},
                                        device_scale_factor=1)
                errors: list[str] = []
                page.on("pageerror", lambda e: errors.append(str(e)[:160]))
                try:
                    b619.open_desk(page)
                    if not open_state(page, setup):
                        cells.append({"w": w, "state": name, "skipped": "not-applicable"})
                        continue
                    if overlay:
                        page.locator(overlay).first.wait_for(state="visible",
                                                              timeout=8_000)
                    page.wait_for_timeout(700)
                    r = b619.census(page)
                    real = [e for e in errors
                            if not any(k in e for k in IGNORE_PAGE_ERROR)]
                    cells.append({
                        "w": w, "state": name, "total": r["total"],
                        "unexpected": [(b["label"], b["hitLabel"], b["box"])
                                       for b in r["unexpected"]],
                        "covered": [b["label"] for b in r["covered"]][:6],
                        "clipped": len(r["clipped"]),
                        "openOverlays": len(r.get("openOverlays", [])),
                        "pageErrors": real[:2],
                    })
                except Exception as exc:  # noqa: BLE001
                    cells.append({"w": w, "state": name,
                                  "error": f"{type(exc).__name__}: {str(exc)[:120]}"})
                finally:
                    page.close()
        # --- the ai-import modal must not be trapped in the rail's z-30 ----------
        # Checked at the two viewports where the geometry actually overlapped
        # (h < 903 puts the centred modal's foot under the timeline; narrow enough
        # widths push its right edge into the inspector column), plus one tall one
        # as a control.
        trap_rows = []
        for w, h in ((900, 900), (1920, 900), (1920, 1150)):
            pg = browser.new_page(viewport={"width": w, "height": h},
                                    device_scale_factor=1)
            try:
                b619.open_desk(pg)
                pg.locator("[data-director-rail-entry='ai-import']").first.click(
                    timeout=15_000)
                pg.locator("[data-director-ai-import-modal]").first.wait_for(
                    state="visible", timeout=15_000)
                pg.wait_for_timeout(800)
                g = pg.evaluate(GEOM_JS)
                v.result[f"trap-{w}x{h}"] = g
                v.check(f"{w}x{h}:the-ai-import-modal-is-not-inside-the-rail",
                        g["modalInRail"] is False and g["backdropInRail"] is False,
                        detail={"modalInRail": g["modalInRail"],
                                "backdropInRail": g["backdropInRail"],
                                "backdropZ": g["backdropZ"]})
                # and the control that was buried by the timeline must take its own hit
                hit = pg.evaluate(
                    """() => {
                      const b = [...document.querySelectorAll('button')]
                        .find(x => (x.textContent || '').includes('生成站位参考'));
                      if (!b) return null;
                      const r = b.getBoundingClientRect();
                      const h = document.elementFromPoint(r.x + r.width/2, r.y + r.height/2);
                      return !!(h && (h === b || b.contains(h)));
                    }""")
                v.check(f"{w}x{h}:the-buried-generate-button-takes-its-own-hit", hit is True,
                        detail=hit)
                trap_rows.append(g)
            finally:
                pg.close()

        browser.close()

    live = [c for c in cells if "skipped" not in c and "error" not in c]
    defects = [c for c in live if c["unexpected"] or c["pageErrors"]]
    v.result["cells"] = cells
    # Derived, not a magic number: the first version asserted >= 50 and went red
    # on a 45-cell matrix because the author guessed the count.  Deriving it from
    # states_for() means the check cannot drift when a state or a width is added.
    expected_cells = sum(len(states_for(w)) for w in WIDTHS)
    v.check("the-matrix-ran-every-applicable-cell", len(cells) == expected_cells,
            detail={"got": len(cells), "expected": expected_cells,
                    "widths": len(WIDTHS)})
    v.check("every-cell-actually-ran", len(live) == len(cells),
            detail={"live": len(live), "skipped": len(cells) - len(live)})
    v.check("no-cell-has-an-unexpected-covered-control", not defects,
            detail=[(c["w"], c["state"], c["unexpected"][:2], c["pageErrors"])
                    for c in defects][:8])
    # a state that opens a panel must be seen as open, or the cell proves nothing
    panel_cells = [c for c in live if c["state"].startswith(("rail-", "export-",
                                                            "tree-", "ai-"))]
    v.check("every-panel-state-was-seen-open",
            all(c["openOverlays"] >= 1 for c in panel_cells),
            detail=[(c["w"], c["state"], c["openOverlays"])
                    for c in panel_cells if c["openOverlays"] < 1][:6])

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
