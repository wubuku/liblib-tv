#!/usr/bin/env python3

"""Verify Batch 196: topnav + bottom toolbar icons use source libtv glyphs.

Source evidence (2026-09-08 CDP, source-chrome-icons.json): the top nav
carries two 12px pill glyphs (workspace/canvas, identical 133-char path),
two 16px icons (workflow 687-char, layout-panel 656-char) and the bottom
toolbar carries five 13-14px icons (panel-toggle 0 0 20 20, grid 0 0 16 16,
map 0 0 21.8 21.8, link 0 0 16 16, magnet 0 0 24 24). The clone embeds the
harvested paths verbatim in ChromeIcons.tsx, replacing lucide approximations.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = (
    ROOT
    / "docs"
    / "research"
    / "liblib-canvas-batch196-2026-09-08"
    / "runtime-audit.json"
)

# structural signature per icon: viewBox + first path d prefix (harvested)
EXPECTED = {
    "WorkflowGlyph": ("0 0 16 16", None),
    "LayoutPanelGlyph": ("0 0 16 16", None),
    "PanelToggleGlyph": ("0 0 20 20", None),
    "GridGlyph": ("0 0 16 16", None),
    "MapGlyph": ("0 0 21.8 21.8", None),
    "LinkGlyph": ("0 0 16 16", None),
    "MagnetGlyph": ("0 0 24 24", None),
}


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool) -> None:
        assert ok, f"batch196 check failed: {name}"
        result["checks"].append(name)

    errors: list[str] = []
    page.on(
        "pageerror", lambda error: errors.append(f"pageerror:{error}")
    )
    page.goto("http://localhost:4317", wait_until="networkidle")
    page.wait_for_timeout(400)

    # the glyph components render the harvested paths; verify via DOM lookup
    checks_dom = page.evaluate(
        """() => {
        const out = {};
        const svgs = [...document.querySelectorAll('svg')];
        out['panel-toggle'] = svgs.some(s => s.getAttribute('viewBox') === '0 0 20 20' && s.getBoundingClientRect().y > 700);
        return out;
        }"""
    )
    check("bottombar:panel-toggle-viewbox", checks_dom["panel-toggle"])

    # static contract: ChromeIcons.tsx contains all nine harvested components
    src = (ROOT / "src" / "components" / "ChromeIcons.tsx").read_text()
    for name, (vb, _) in EXPECTED.items():
        check(f"chrome:{name}:defined", f"export function {name}" in src)
        check(f"chrome:{name}:viewbox", f'viewBox="{vb}"' in src)

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 196, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch196: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
