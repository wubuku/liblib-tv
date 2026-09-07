#!/usr/bin/env python3

"""Verify Batch 168: /project left sidebar per the 2026-09-07 DOM re-audit.

Source facts: 240px sticky sidebar with 新建项目 on top, nav rows
首页/项目(active)/LibTV Agent/创作者挑战赛 (h-9, icon+label), and a bottom
section with the SD2.5 promo card + 帮助.
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
    / "liblib-canvas-batch168-2026-09-07"
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
        assert ok, f"batch168 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(BASE_URL + "/project", wait_until="networkidle")
    page.wait_for_timeout(500)

    sidebar = page.locator("[data-project-sidebar]")
    check("sidebar:visible", sidebar.is_visible())
    sbox = sidebar.bounding_box()
    check("sidebar:w-240", sbox is not None and 235 <= sbox["width"] <= 245)

    new_project = page.locator("[data-sidebar-new-project]")
    check("sidebar:new-project", new_project.is_visible())
    np_box = new_project.bounding_box()
    check("sidebar:new-project-h36", np_box is not None and 32 <= np_box["height"] <= 40)

    nav = page.locator("[data-sidebar-nav] button")
    check("sidebar:nav-4", nav.count() == 4)
    labels = [nav.nth(i).inner_text().strip() for i in range(nav.count())]
    check(
        "sidebar:nav-labels",
        labels == ["首页", "项目", "LibTV Agent", "创作者挑战赛"],
    )
    active = page.locator("[data-sidebar-item='项目']")
    check(
        "sidebar:project-active",
        active.get_attribute("aria-current") == "page",
    )
    nav_h = nav.first.bounding_box()
    check("sidebar:row-h36", nav_h is not None and 32 <= nav_h["height"] <= 40)

    check("sidebar:promo", page.locator("[data-sidebar-promo]").is_visible())
    promo_text = page.locator("[data-sidebar-promo]").inner_text()
    check("sidebar:promo-copy", "SD2.5畅享卡上线" in promo_text and "积分超市限时抢购" in promo_text)
    check("sidebar:help", page.locator("[data-sidebar-help]").is_visible())

    # 内容区仍在侧边栏右侧
    content = page.locator("[data-project-list-page] .flex-1")
    cbox = content.first.bounding_box()
    check("sidebar:content-right", cbox is not None and cbox["x"] > sbox["width"] - 10)

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 168, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch168: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
