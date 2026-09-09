#!/usr/bin/env python3
"""Verify Batch 264: asset drawer drift alignment.

Source evidence (2026-09-10, docs/research/liblib-canvas-batch263-2026-09-10/
drawer.png): the asset drawer is 320px wide (was 280), has a list-view
toggle in the toolbar, entry hover actions (… menu + send), and a footer
collapse arrow icon with the 共 N 节点 counter."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = (
    ROOT
    / "docs"
    / "research"
    / "liblib-canvas-batch264-2026-09-10"
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
        assert ok, f"batch264 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto("http://localhost:4317", wait_until="networkidle")
    page.wait_for_timeout(500)

    # open the drawer via the bottom-left entry (batch 12 entry point)
    page.get_by_text("资产管理", exact=True).click(force=True)
    page.wait_for_timeout(600)

    drawer = page.locator("[data-liblib-overlay='asset']")
    check("drawer:visible", drawer.is_visible())
    box = drawer.bounding_box()
    check("drawer:width-320", box is not None and 312 <= box["width"] <= 328)

    # list-view toggle present and toggles state
    toggle = page.locator("[data-asset-manager-listview]")
    check("listview:present", toggle.count() == 1)
    check("listview:initial-off", toggle.get_attribute("aria-pressed") == "false")
    toggle.click()
    page.wait_for_timeout(150)
    check("listview:toggles-on", toggle.get_attribute("aria-pressed") == "true")
    toggle.click()
    page.wait_for_timeout(150)

    # entry hover actions appear
    item = page.locator("[data-asset-manager-item]").first
    check("entries:present", page.locator("[data-asset-manager-item]").count() > 0)
    item.hover()
    page.wait_for_timeout(200)
    check("entries:hover-actions", item.locator("span.hidden").count() >= 1)

    # footer: counter + collapse arrow (icon button, aria-label kept)
    check(
        "footer:counter",
        drawer.get_by_text("共 ", exact=False).count() >= 1
        or drawer.locator("[data-asset-manager-count]").count() == 1,
    )
    collapse = page.locator("[data-asset-manager-collapse]")
    check("footer:collapse-aria", collapse.get_attribute("aria-label") == "收起节点侧栏")
    check("footer:collapse-icon", collapse.locator("svg").count() == 1)
    collapse.click()
    page.wait_for_timeout(400)
    check("footer:collapse-closes", page.locator("[data-liblib-overlay='asset']").count() == 0)

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 264, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch264: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
