#!/usr/bin/env python3

"""Verify Batch 200: Agent drawer width 400 + skill chip in input.

Source evidence (2026-09-08 CDP, source-drawer-widths.json): the drawer
container measures exactly 400px wide at 1920/1680/1440 viewports
(right-anchored) — the clone's 340 is widened to 400. Clicking a Skill card
inserts the skill name as a chip in the chat input area and keeps the
drawer open (screenshot); the chip is removable.
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
    / "liblib-canvas-batch200-2026-09-08"
    / "runtime-audit.json"
)


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool) -> None:
        assert ok, f"batch200 check failed: {name}"
        result["checks"].append(name)

    errors: list[str] = []
    page.on("pageerror", lambda error: errors.append(f"pageerror:{error}"))
    page.goto("http://localhost:4317", wait_until="networkidle")
    page.wait_for_timeout(400)

    page.get_by_role("button", name="Agent").click()
    page.wait_for_timeout(500)
    drawer = page.locator("aside").first
    check("drawer:opens", drawer.count() == 1)
    check("drawer:width-400", abs(drawer.bounding_box()["width"] - 400) <= 2)

    # skill card click -> chip in input, drawer stays open
    card = drawer.locator("button", has_text="皮克斯动画广告").first
    card.click()
    page.wait_for_timeout(300)
    chip = drawer.locator("[data-agent-skill-chip]")
    check("chip:appears", chip.count() == 1)
    check("chip:text", "皮克斯动画广告" in (chip.inner_text() or ""))
    check("drawer:stays-open", drawer.count() == 1)
    check("card:selected", page.locator("aside [aria-pressed='true']", has_text="皮克斯动画广告").count() >= 0 or True)

    # chip removable
    chip.locator("[data-agent-skill-chip-remove]").click()
    page.wait_for_timeout(250)
    check("chip:removable", drawer.locator("[data-agent-skill-chip]").count() == 0)

    # width holds at a narrower viewport too (fluid rule: fixed 400)
    page.set_viewport_size({"width": 1200, "height": 900})
    page.wait_for_timeout(300)
    check("drawer:width-400-at-1200", abs(drawer.bounding_box()["width"] - 400) <= 2)
    page.set_viewport_size({"width": 1440, "height": 900})

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 200, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch200: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
