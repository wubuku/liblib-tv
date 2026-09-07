#!/usr/bin/env python3

"""Verify Batch 198: topnav right cluster uses source libtv glyphs.

Source evidence (2026-09-08 CDP, source-topnav-right.json): the cluster is
share-nodes (0 0 14 14), member shop (0 0 16 16, cyan --nt-cyan-400),
credits bolt (0 0 16 16) and Agent robot face (0 0 17.58 14). The clone
embeds the harvested paths verbatim (ShareNodesGlyph/MemberShopGlyph/
BoltGlyph/AgentFaceGlyph) replacing lucide Share2/Zap/Bot and the
placeholder ♦ diamond.
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
    / "liblib-canvas-batch198-2026-09-08"
    / "runtime-audit.json"
)

EXPECTED = {
    "ShareNodesGlyph": "0 0 14 14",
    "MemberShopGlyph": "0 0 16 16",
    "BoltGlyph": "0 0 16 16",
    "AgentFaceGlyph": "0 0 17.5777 14",
}


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool) -> None:
        assert ok, f"batch198 check failed: {name}"
        result["checks"].append(name)

    errors: list[str] = []
    page.on("pageerror", lambda error: errors.append(f"pageerror:{error}"))
    page.goto("http://localhost:4317", wait_until="networkidle")
    page.wait_for_timeout(400)

    dom = page.evaluate(
        """() => {
        const g = document.querySelector('g[transform="translate(2.935 1.665)"]');
        return g ? {bolt: true, y: Math.round(g.closest('svg').getBoundingClientRect().y)} : {bolt: false};
        }"""
    )
    check("credits:bolt-in-dom", dom["bolt"] is True)
    check("credits:bolt-in-topnav", dom.get("y", 999) < 60)

    src = (ROOT / "src" / "components" / "ChromeIcons.tsx").read_text()
    for name, vb in EXPECTED.items():
        check(f"chrome:{name}:defined", f"export function {name}" in src)
        check(f"chrome:{name}:viewbox", f'viewBox="{vb}"' in src)

    topnav = (ROOT / "src" / "components" / "TopNavBar.tsx").read_text()
    check("topnav:uses-glyphs", all(n in topnav for n in EXPECTED))

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 198, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch198: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
