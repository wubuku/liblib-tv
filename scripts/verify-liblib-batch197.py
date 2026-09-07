#!/usr/bin/env python3

"""Verify Batch 197: canvas dropdown chevron uses the source libtv glyph.

Source evidence (2026-09-08 CDP, source-chrome-icons.json): the topnav
dropdown chevrons are 12x12 libtv icons (viewBox 0 0 16 16, g transform
translate(4.345 5.825), 133-char path) with a data-open rotate-180
transition. The clone's canvas dropdown now embeds that path verbatim
(ChevronDownGlyph) instead of lucide ChevronDown.
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
    / "liblib-canvas-batch197-2026-09-08"
    / "runtime-audit.json"
)


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool) -> None:
        assert ok, f"batch197 check failed: {name}"
        result["checks"].append(name)

    errors: list[str] = []
    page.on("pageerror", lambda error: errors.append(f"pageerror:{error}"))
    page.goto("http://localhost:4317", wait_until="networkidle")
    page.wait_for_timeout(400)

    # DOM: the dropdown chevron svg with the harvested transform
    dom = page.evaluate(
        """() => {
        const g = document.querySelector('g[transform="translate(4.345 5.825)"]');
        if (!g) return {found: false};
        const svg = g.closest('svg');
        const r = svg.getBoundingClientRect();
        return {found: true, vb: svg.getAttribute('viewBox'), y: Math.round(r.y), w: Math.round(r.width)};
        }"""
    )
    check("chevron:in-dom", dom["found"] is True)
    check("chevron:viewbox", dom.get("vb") == "0 0 16 16")
    check("chevron:in-topnav", dom.get("found") and dom.get("y", 999) < 60 and dom.get("w", 999) <= 14)

    # static contract
    src = (ROOT / "src" / "components" / "ChromeIcons.tsx").read_text()
    check("chrome:ChevronDownGlyph:defined", "export function ChevronDownGlyph" in src)
    check("chrome:ChevronDownGlyph:transform", "translate(4.345 5.825)" in src)
    check("topnav:uses-glyph", "ChevronDownGlyph" in (ROOT / "src" / "components" / "TopNavBar.tsx").read_text())

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 197, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch197: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
