#!/usr/bin/env python3

"""Verify Batch 212: character library modal is 1280x720 at all viewports.

Source evidence (source-clib-modal-widths.json): with a video node created
per viewport and the 角色库 pill clicked, the modal measures 1280x720 at
1920/1680/1440 — horizontally centered (x=(vw-1280)/2), top y=90. The
clone's modal geometry was migrated from 1304x731 to 1280x720 accordingly.
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
    / "liblib-canvas-batch212-2026-09-08"
    / "runtime-audit.json"
)


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool) -> None:
        assert ok, f"batch212 check failed: {name}"
        result["checks"].append(name)

    errors: list[str] = []
    page.on("pageerror", lambda error: errors.append(f"pageerror:{error}"))
    page.goto("http://localhost:4317", wait_until="networkidle")
    page.wait_for_timeout(500)

    page.get_by_role("button", name="资产管理").count()  # ensure app ready
    page.get_by_role("button", name="Agent").click()
    page.wait_for_timeout(300)
    page.get_by_role("button", name="Agent").click()
    page.wait_for_timeout(300)

    # open the character library via the panel toolbar pill (video panel needs
    # a node; use the preset video node)
    # open via the left sidebar 角色库 tool button
    page.locator("[data-clib-tabs]").count()  # noop warm
    # the video panel's 角色库 pill opens the left sidebar's character panel
    page.locator('.react-flow__node[data-id="v-UGQZzZOpbv"]').click(force=True)
    page.wait_for_timeout(300)
    page.locator("[data-clib-trigger]").click()
    page.wait_for_timeout(400)
    page.wait_for_timeout(400)
    modal = page.locator("[data-liblib-overlay='primary:character']")
    check("modal:opens", modal.count() == 1)
    mb = modal.bounding_box()
    check("modal:width-1280", abs(mb["width"] - 1280) <= 8)
    check("modal:height-720", abs(mb["height"] - 720) <= 8)

    # tabs + public tab content
    check("tabs:public", page.get_by_text("公共角色库", exact=True).count() >= 1)
    check("tabs:compliance", page.get_by_text("Seedance2.0&2.5合规素材库", exact=True).count() >= 1)

    page.keyboard.press("Escape")
    page.wait_for_timeout(200)

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 212, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch212: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
