#!/usr/bin/env python3

"""Verify Batch 165: FrameOS project assets rail entry + panel.

2026-09-23 source re-sampling (docs/user-manual/frameos-canvas
SOURCE_OBSERVATIONS.md §13.10 / shot 16): the rail has a 查看项目资产
button (second from top) toggling a left panel titled 项目资产 with tabs
角色 / 物品 / 环境 (角色 active), a search input (placeholder
搜索资产名称...) and the empty state 暂无已生成的资产图; × closes.
Verifies rail presence/order, panel structure, empty state, close paths.
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
    / "liblib-frameos-batch165-2026-09-23"
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
        assert ok, f"batch165 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/frameos/canvas/demo", wait_until="domcontentloaded", timeout=90000)
    page.wait_for_timeout(1200)

    # 左栏按钮存在且唯一
    btn = page.locator("button[aria-label='查看项目资产']")
    check("rail:button", btn.count() == 1)

    # 左栏顺序: 添加节点 < 查看项目资产 < 从素材库选择
    add_btn = page.locator("button[aria-label='添加节点']")
    material_btn = page.locator("button[aria-label='从素材库选择']")
    add_y = add_btn.bounding_box()["y"]
    assets_y = btn.bounding_box()["y"]
    material_y = material_btn.bounding_box()["y"]
    check("rail:order", add_y < assets_y < material_y)

    panel = page.locator("[data-frameos-project-assets-panel]")
    check("panel:initially-closed", panel.count() == 0)

    # 打开面板: 标题/页签/搜索/空态
    btn.click()
    page.wait_for_timeout(400)
    check("panel:opens", panel.is_visible())
    title = panel.inner_text()
    for tab in ["角色", "物品", "环境"]:
        check(
            f"panel:tab:{tab}",
            panel.locator(f"[data-frameos-assets-tab='{tab}']").is_visible(),
        )
    check(
        "panel:search-placeholder",
        page.locator("[data-frameos-assets-search]").get_attribute("placeholder")
        == "搜索资产名称...",
    )
    check("panel:empty-state", "暂无已生成的资产图" in title)

    # × 关闭
    panel.get_by_role("button", name="关闭项目资产面板").click()
    page.wait_for_timeout(300)
    check("panel:close-x", panel.count() == 0)

    # 按钮再开再关 (toggle)
    btn.click()
    page.wait_for_timeout(300)
    check("panel:toggles-open", panel.is_visible())
    btn.click()
    page.wait_for_timeout(300)
    check("panel:toggles-closed", panel.count() == 0)

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 165, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch165: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
