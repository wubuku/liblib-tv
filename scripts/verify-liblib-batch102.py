#!/usr/bin/env python3

"""Verify Batch 102 asset manager drawer alignment with the 2026-09-05 source audit."""

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
    / "liblib-canvas-batch102-2026-09-05"
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
    page.on(
        "requestfailed",
        lambda request: errors.append(
            f"requestfailed:{request.method}:{request.url}:{request.failure}"
        ),
    )
    return errors


def open_drawer(page: Page) -> Any:
    page.get_by_role("button", name="资产管理").click()
    drawer = page.locator('[data-liblib-overlay="asset"]')
    assert drawer.is_visible()
    return drawer


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool) -> None:
        assert ok, f"batch102 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(BASE_URL, wait_until="networkidle")
    page.wait_for_timeout(400)

    drawer = open_drawer(page)

    check("tabs", drawer.locator('[data-asset-manager-tab="canvas"]').is_visible()
          and drawer.locator('[data-asset-manager-tab="assets"]').is_visible())
    check("search:aria", drawer.get_by_role("button", name="搜索节点").count() == 1)
    check("filter:aria", drawer.get_by_role("button", name="筛选：全部").count() == 1)

    rating = drawer.locator("[data-asset-manager-rating]")
    display = drawer.locator("[data-asset-manager-display]")
    check("rating:visible", rating.is_visible() and rating.inner_text().strip() == "所有评级")
    check("display:visible", display.is_visible() and display.inner_text().strip() == "展示设置")
    rating.click()
    check("rating:hint", "本地原型" in drawer.locator("[data-asset-manager-hint]").inner_text())
    display.click()
    check("display:hint", "展示设置" in drawer.locator("[data-asset-manager-hint]").inner_text())

    check("footer:count", "共 10 节点" in drawer.inner_text())
    check("footer:collapse-visible", drawer.locator("[data-asset-manager-collapse]").is_visible())

    drawer.locator("[data-asset-manager-collapse]").click()
    page.wait_for_timeout(200)
    check("collapse:closes", not drawer.is_visible())

    drawer = open_drawer(page)
    drawer.locator("[data-asset-manager-canvas]").click()
    page.locator("[data-canvas-row='canvas-1']").get_by_role("button").first.click()
    page.wait_for_timeout(300)
    # 画布切换会关闭资产抽屉（Batch 58/65 canvas-switch 契约），重开验证空画布内容
    drawer = open_drawer(page)
    check("empty:text", "画布暂无节点" in drawer.locator("[data-asset-manager-empty]").inner_text())
    check("empty:count", "共 0 节点" in drawer.inner_text())

    check("diagnostics:zero", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 102,
        "title": "Asset manager drawer alignment with 2026-09-05 source audit",
        "evidence": "docs/research/liblib-live-2026-09-05/README.md",
        "results": [],
    }
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        desktop = browser.new_page(viewport={"width": 1440, "height": 900}, device_scale_factor=1)
        audit["results"].append(run_desktop(desktop))
        desktop.close()
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    checks = audit["results"][0]["checks"]
    print(
        "Batch 102 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "Tabs, search/filter aria, rating/display controls with local hints, "
        "footer count/collapse, empty-canvas copy recorded in runtime-audit.json."
    )


if __name__ == "__main__":
    main()
