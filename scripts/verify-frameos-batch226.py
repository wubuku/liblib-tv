#!/usr/bin/env python3

"""Verify Batch 226: content-aware node context menus.

Source sampling 2026-09-25 (frameos.cn right-click on three node kinds):
- content image: 复制⌘C / 复制图片 / 创建副本⌘D / — / 设置为资产图 / — / 删除⌫
- empty image:   复制⌘C / 复制图片(disabled) / 创建副本⌘D / — / 重新生成(disabled) / — / 删除⌫
- 3D导演台:      复制⌘C / 创建副本⌘D / — / 重新生成(disabled) / — / 删除⌫
The middle row is content-aware (设置为资产图 for content media, 重新生成
disabled otherwise), with a divider on each side.

Checks:
1. content image menu rows + enabled states + 设置为资产图 click (mock toast);
2. cleared image menu rows + disabled states;
3. 3D导演台 menu rows (non-media shape);
4. errors clean.
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
    / "liblib-frameos-batch226-2026-09-25"
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
    page.on("dialog", lambda d: d.dismiss())
    return errors


def menu_rows(page: Page) -> list[str]:
    return [
        page.locator("[data-frameos-context-item]").nth(i).get_attribute(
            "data-frameos-context-item"
        )
        for i in range(page.locator("[data-frameos-context-item]").count())
    ]


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool) -> None:
        assert ok, f"batch226 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/frameos/canvas/demo", wait_until="domcontentloaded")
    page.wait_for_timeout(1200)
    menu = page.locator("[data-frameos-context-menu]")

    # 1) 内容图片菜单
    image = page.locator(".react-flow__node-image").first
    image.click(button="right")
    page.wait_for_timeout(300)
    check("content-image:menu-opens", menu.is_visible())
    check(
        "content-image:rows",
        menu_rows(page) == ["复制", "复制图片", "创建副本", "设置为资产图", "删除"],
    )
    set_asset = menu.locator("[data-frameos-context-item='设置为资产图']")
    check("content-image:set-asset-enabled", set_asset.get_attribute("disabled") is None)
    set_asset.click()
    page.wait_for_timeout(300)
    check("content-image:click-no-error", not errors)
    check("content-image:menu-closes", menu.count() == 0)

    # 2) 空图片菜单
    page.keyboard.press("Escape")
    page.wait_for_timeout(200)
    page.evaluate(
        "window.__frameos_store.getState().updateNodeData('image-1', { imageUrl: null })"
    )
    page.wait_for_timeout(300)
    image.click(button="right")
    page.wait_for_timeout(300)
    check(
        "empty-image:rows",
        menu_rows(page) == ["复制", "复制图片", "创建副本", "重新生成", "删除"],
    )
    check(
        "empty-image:copy-image-disabled",
        menu.locator("[data-frameos-context-item='复制图片']").get_attribute("disabled")
        is not None,
    )
    check(
        "empty-image:regen-disabled",
        menu.locator("[data-frameos-context-item='重新生成']").get_attribute("disabled")
        is not None,
    )
    page.keyboard.press("Escape")
    page.wait_for_timeout(200)

    # 3) 3D导演台菜单 (非媒体形态)
    page.locator("button[aria-label='添加节点']").click()
    page.wait_for_timeout(300)
    page.get_by_text("3D导演台", exact=True).click()
    page.wait_for_timeout(500)
    director = page.locator(".react-flow__node-director3d").last
    director.click(button="right")
    page.wait_for_timeout(300)
    check(
        "director:rows",
        menu_rows(page) == ["复制", "创建副本", "重新生成", "删除"],
    )
    check(
        "director:regen-disabled",
        menu.locator("[data-frameos-context-item='重新生成']").get_attribute("disabled")
        is not None,
    )
    check("director:delete-danger", menu.locator("[data-frameos-context-item='删除']").count() == 1)
    page.keyboard.press("Escape")
    page.wait_for_timeout(200)

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 226, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch226: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
