#!/usr/bin/env python3

"""Verify Batch 203: asset drawer ratings filter menu.

Source evidence (2026-09-08 CDP, source-ratings-menu.json): clicking
所有评级 opens a 180x225 menu with six options — 所有评级 / 1 / 2 / 3 / 4 /
5 (verbatim labels). The clone implements the menu with selectable options
(selection sets the trigger label to the chosen rating).
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
    / "liblib-canvas-batch203-2026-09-08"
    / "runtime-audit.json"
)


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool) -> None:
        assert ok, f"batch203 check failed: {name}"
        result["checks"].append(name)

    errors: list[str] = []
    page.on("pageerror", lambda error: errors.append(f"pageerror:{error}"))
    page.goto("http://localhost:4317", wait_until="networkidle")
    page.wait_for_timeout(400)

    page.get_by_role("button", name="资产管理").click()
    page.wait_for_timeout(400)
    panel = page.locator("[data-liblib-overlay='asset']")
    check("drawer:opens", panel.count() == 1)

    panel.locator("[data-asset-manager-rating]").click()
    page.wait_for_timeout(300)
    menu = panel.locator("[data-asset-manager-rating-menu]")
    check("menu:opens", menu.count() == 1)
    mb = menu.bounding_box()
    check("menu:width-180", abs(mb["width"] - 180) <= 2)

    options = page.eval_on_selector_all(
        "[data-asset-manager-rating-option]",
        "els => els.map(el => el.getAttribute('data-asset-manager-rating-option'))",
    )
    check("menu:six-options", options == ["all", "1", "2", "3", "4", "5"])
    labels = menu.locator("[data-asset-manager-rating-option]").all_inner_texts()
    check("menu:labels-verbatim", [l.strip() for l in labels] == ["所有评级", "1", "2", "3", "4", "5"])

    # select 3 -> trigger label updates
    menu.locator("[data-asset-manager-rating-option='3']").click()
    page.wait_for_timeout(250)
    check("menu:selects-3", menu.count() == 0 and "3" in panel.locator("[data-asset-manager-rating]").inner_text())

    # reset to all
    panel.locator("[data-asset-manager-rating]").click()
    page.wait_for_timeout(250)
    panel.locator("[data-asset-manager-rating-option='all']").click()
    page.wait_for_timeout(250)
    check("menu:reset-all", "所有评级" in panel.locator("[data-asset-manager-rating]").inner_text())

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 203, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch203: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
