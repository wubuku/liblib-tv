#!/usr/bin/env python3

"""Verify Batch 171: bottom-left asset bar geometry per sampled source classes.

Source evidence (2026-09-07 canvas dumps): bar container 280x40 items-end
gap-2 without an inner padding box; 资产管理 button 94x28 rounded-lg 13px;
zoom chip 42x28 rounded-lg.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
BASE_URL = os.environ.get("LIBLIB_BASE_URL", "http://localhost:4317")
AUDIT_PATH = (
    ROOT
    / "docs"
    / "research"
    / "liblib-canvas-batch171-2026-09-07"
    / "runtime-audit.json"
)


def attach_errors(page: Page) -> list[str]:
    errors: list[str] = []
    page.on(
        "console",
        lambda message: errors.append(f"console:{message.type}:{message.text}")
        if message.type == "error"
        else None,
    )
    page.on("pageerror", lambda error: errors.append(f"pageerror:{error}"))
    return errors


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool) -> None:
        assert ok, f"batch171 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(BASE_URL, wait_until="networkidle")
    page.wait_for_timeout(500)

    asset = page.locator("button[aria-label='资产管理']")
    check("asset:visible", asset.is_visible())
    abox = asset.bounding_box()
    check("asset:h-28", abox is not None and 26 <= abox["height"] <= 30)
    check("asset:w-94", abox is not None and abox["width"] >= 80)
    check(
        "asset:rounded-lg",
        asset.evaluate("el => getComputedStyle(el).borderTopLeftRadius") == "8px",
    )

    zoom = page.locator("[data-viewport-menu-trigger='zoom']")
    zbox = zoom.bounding_box()
    check("zoom:h-28", zbox is not None and 26 <= zbox["height"] <= 30)
    check(
        "zoom:rounded-lg",
        zoom.evaluate("el => getComputedStyle(el).borderTopLeftRadius") == "8px",
    )
    check("zoom:label", zoom.inner_text().strip().endswith("%"))

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 171, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch171: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
