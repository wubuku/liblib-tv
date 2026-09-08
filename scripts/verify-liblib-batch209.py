#!/usr/bin/env python3

"""Verify Batch 209: canvas chrome matches the source (no attribution).

Source evidence (2026-09-08 CDP): the source canvas renders NO minimap, NO
controls and NO react-flow attribution — only the background dots. The
clone's minimap is already opt-in (default off); the attribution is now
hidden via proOptions.
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
    / "liblib-canvas-batch209-2026-09-08"
    / "runtime-audit.json"
)


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool) -> None:
        assert ok, f"batch209 check failed: {name}"
        result["checks"].append(name)

    errors: list[str] = []
    page.on("pageerror", lambda error: errors.append(f"pageerror:{error}"))
    page.goto("http://localhost:4317", wait_until="networkidle")
    page.wait_for_timeout(500)

    check("minimap:absent", page.locator(".react-flow__minimap").count() == 0)
    check("attribution:absent", page.locator(".react-flow__attribution").count() == 0)
    check("controls:absent", page.locator(".react-flow__controls").count() == 0)
    check("background:present", page.locator(".react-flow__background").count() == 1)

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 209, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch209: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
