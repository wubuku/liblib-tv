#!/usr/bin/env python3

"""Verify Batch 214: yunjing menu is a pure launcher (no selection marker).

Source evidence (source-yunjing-selected-cards.json): selected and
unselected cards render identical classes/markers — the menu shows no
selection state; the pill keeps reading 运镜 after selection. The clone
now matches: no ✓ 已选 marker on cards, menu closes on selection, pill
label unchanged.
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
    / "liblib-canvas-batch214-2026-09-09"
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
        assert ok, f"batch214 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto("http://localhost:4317", wait_until="networkidle")
    page.wait_for_timeout(500)

    page.locator('.react-flow__node[data-id="v-UGQZzZOpbv"]').click(force=True)
    page.wait_for_timeout(400)

    page.locator("[data-yunjing-trigger]").click()
    page.wait_for_timeout(400)
    menu = page.locator("[data-yunjing-menu]")
    check("menu:opens", menu.count() == 1)

    options = page.locator("[data-yunjing-option]")
    check("menu:23-cards", options.count() == 23)

    # no selection marker rendered on any card
    markers = page.evaluate(
        """() => [...document.querySelectorAll('[data-yunjing-menu] *')]
        .filter(el => (el.textContent||'').trim() === '✓ 已选').length"""
    )
    check("menu:no-selection-marker", markers == 0)

    # select a card: menu closes, pill unchanged
    options.nth(0).click()
    page.wait_for_timeout(300)
    check("menu:closes-on-select", menu.count() == 0)
    pill = page.locator("[data-yunjing-trigger]")
    check("pill:label-unchanged", pill.inner_text().strip() == "运镜")

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 214, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch214: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
