#!/usr/bin/env python3
"""Verify Batch 298: asset drawer view-layout menu.

Source evidence (2026-09-10, docs/research/liblib-canvas-batch297-2026-09-10/
display-menu.png): the drawer's 展示设置 opens a view-layout menu (180px,
four items — 列表展示/宫格展示/展开全部分组/收起全部分组), while the
type-filter menu (batch 204 content) lives on the 筛选 button."""

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
    / "liblib-canvas-batch298-2026-09-10"
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
        assert ok, f"batch298 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto("http://localhost:4317", wait_until="networkidle")
    page.wait_for_timeout(500)

    page.get_by_text("资产管理", exact=True).click(force=True)
    page.wait_for_timeout(600)

    drawer = page.locator("[data-liblib-overlay='asset']")
    check("drawer:open", drawer.is_visible())

    display = page.locator("[data-asset-manager-display]")
    check("display:label", display.inner_text().strip() == "展示设置")
    display.click()
    page.wait_for_timeout(300)
    viewmenu = page.locator("[data-asset-manager-viewmenu]")
    check("view:menu-opens", viewmenu.count() == 1)
    for label in ("列表展示", "宫格展示", "展开全部分组", "收起全部分组"):
        check(f"view:item-{label}", viewmenu.get_by_text(label, exact=True).count() == 1)

    # 宫格展示: switch view mode
    page.locator('[data-asset-manager-view-option="grid"]').click()
    page.wait_for_timeout(300)
    check("view:menu-closes-on-pick", viewmenu.count() == 0)
    grid_first = page.locator("[data-asset-manager-item]").first
    check("view:grid-item-card", grid_first.bounding_box()["width"] <= 160)

    # 收起全部分组: hide depth-1 children via the menu
    display.click()
    page.wait_for_timeout(300)
    page.locator("[data-asset-manager-collapse-groups]").click()
    page.wait_for_timeout(300)
    depth1 = page.locator('[data-asset-manager-depth="1"]').count()
    check("groups:collapse-hides-children", depth1 == 0)
    # expand restores
    display.click()
    page.wait_for_timeout(300)
    page.locator("[data-asset-manager-expand-groups]").click()
    page.wait_for_timeout(300)
    display.click()
    page.wait_for_timeout(300)
    page.locator("[data-asset-manager-expand-groups]").click()
    page.wait_for_timeout(300)
    depth1_after = page.locator('[data-asset-manager-depth="1"]').count()
    check("groups:expand-restores", depth1_after > 0)
    page.keyboard.press("Escape")
    page.wait_for_timeout(300)

    # type menu lives on the 筛选 button (batch 204 content, batch 298 move)
    filter_btn = page.locator("[data-asset-manager-filter]")
    check("filter:label", filter_btn.get_attribute("aria-label") == "筛选：全部")
    filter_btn.click()
    page.wait_for_timeout(300)
    check("filter:type-menu", page.locator("[data-asset-manager-typemenu]").count() == 1)
    check("filter:type-options", page.locator("[data-asset-manager-type-option]").count() == 10)
    page.locator("[data-asset-manager-filter]").click()
    page.wait_for_timeout(300)

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 298, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        try:
            audit["results"].append(run_desktop(page))
        except Exception as exc:  # noqa: BLE001
            page.screenshot(path=str(AUDIT_PATH.parent / "fail.png"))
            print("EXC:", str(exc)[:300])
            raise
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch298: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
