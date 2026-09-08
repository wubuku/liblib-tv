#!/usr/bin/env python3

"""Verify Batch 210: logo dropdown menu geometry vs the 2026-09-08 sample.

Source evidence (source-logo-menu.json / .png): the menu is 200×190 at the
logo with four 191×44 rows — 回到主页 / 全部项目 / 创建新项目 / 删除项目 —
and a divider before 创建新项目. The clone matches (rows now h-11, menu
w-[200px]).
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
    / "liblib-canvas-batch210-2026-09-08"
    / "runtime-audit.json"
)

EXPECTED_ITEMS = ["回到主页", "全部项目", "创建新项目", "删除项目"]


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool) -> None:
        assert ok, f"batch210 check failed: {name}"
        result["checks"].append(name)

    errors: list[str] = []
    page.on("pageerror", lambda error: errors.append(f"pageerror:{error}"))
    page.goto("http://localhost:4317", wait_until="networkidle")
    page.wait_for_timeout(400)

    page.locator("[data-project-menu-trigger]").click()
    page.wait_for_timeout(300)
    menu = page.locator("[data-project-menu]")
    check("menu:opens", menu.count() == 1)
    mb = menu.bounding_box()
    check("menu:width-200", abs(mb["width"] - 200) <= 2)

    items = page.eval_on_selector_all(
        "[data-project-menu-item]",
        "els => els.map(el => el.textContent.trim())",
    )
    check("menu:four-items-order", items == EXPECTED_ITEMS)

    row = page.locator("[data-project-menu-item='回到主页']")
    rh = row.bounding_box()["height"]
    check("menu:row-h44", abs(rh - 44) <= 2)

    # divider before 创建新项目
    divider = page.evaluate(
        """() => {
        const items = [...document.querySelectorAll("[data-project-menu-item]")];
        const create = items.find(el => el.textContent.trim() === '创建新项目');
        if (!create) return false;
        const prev = create.previousElementSibling;
        return prev && prev.tagName === 'DIV' && prev.className.includes('h-px');
        }"""
    )
    check("menu:divider-before-create", divider is True)

    page.keyboard.press("Escape")
    page.wait_for_timeout(200)

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 210, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch210: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
