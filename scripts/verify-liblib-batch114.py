#!/usr/bin/env python3

"""Verify Batch 114 multi-canvas dropdown alignment with the 2026-09-06 sampling."""

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
    / "liblib-canvas-batch114-2026-09-06"
    / "runtime-audit.json"
)

MENU_ITEMS = ["在新窗口打开", "重命名画布", "复制画布", "删除画布"]


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


def open_dropdown(page: Page, trigger_name: str) -> None:
    dd = page.locator("[data-liblib-overlay='canvas-dropdown']")
    if dd.is_visible():
        return
    page.get_by_role("button", name=trigger_name, exact=True).first.click()
    page.wait_for_timeout(500)


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool) -> None:
        assert ok, f"batch114 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(BASE_URL, wait_until="networkidle")
    page.wait_for_timeout(400)

    # 1. 初始结构：最新在前
    open_dropdown(page, "画布 2")
    dd = page.locator("[data-liblib-overlay='canvas-dropdown']")
    check("open", dd.is_visible())
    check("header:create-btn", dd.locator("button[aria-label='新建画布']").count() == 1)
    check(
        "order:newest-first",
        dd.locator("[data-canvas-row]").first.get_attribute("data-canvas-row") == "canvas-2",
    )
    row2 = dd.locator("[data-canvas-row='canvas-2']")
    check(
        "row:switch-aria",
        row2.locator("button[aria-label='切换到画布 画布 2']").count() == 1,
    )
    check("row:more-aria", row2.locator("button[aria-label='更多操作']").count() == 1)

    # 2. 行级菜单四项
    row2.hover()
    page.wait_for_timeout(250)
    row2.locator("button[aria-label='更多操作']").click(force=True)
    page.wait_for_timeout(300)
    for item in MENU_ITEMS:
        check(f"menu:{item}", dd.get_by_text(item, exact=True).count() == 1)

    # 3. 新建画布（+）
    dd.locator("button[aria-label='新建画布']").click()
    page.wait_for_timeout(600)
    open_dropdown(page, "画布 3")
    check("create:画布3-active", page.get_by_role("button", name="画布 3", exact=True).count() == 1)
    dd = page.locator("[data-liblib-overlay='canvas-dropdown']")
    check(
        "create:order",
        dd.locator("[data-canvas-row]").first.get_attribute("data-canvas-row") == "canvas-3",
    )

    # 4. 重命名 画布 3 → 测试A
    row3 = dd.locator("[data-canvas-row='canvas-3']")
    row3.hover()
    page.wait_for_timeout(250)
    row3.locator("button[aria-label='更多操作']").click(force=True)
    page.wait_for_timeout(300)
    dd.get_by_text("重命名画布", exact=True).click()
    page.wait_for_timeout(300)
    rename_input = row3.locator("input")
    rename_input.fill("测试A")
    rename_input.press("Enter")
    page.wait_for_timeout(500)
    check(
        "rename:trigger",
        page.get_by_role("button", name="测试A", exact=True).count() == 1,
    )

    # 5. 复制 → 测试A副本1 + 自动切换
    open_dropdown(page, "测试A")
    dd = page.locator("[data-liblib-overlay='canvas-dropdown']")
    row_a = dd.locator("[data-canvas-row='canvas-3']")
    row_a.hover()
    page.wait_for_timeout(250)
    row_a.locator("button[aria-label='更多操作']").click(force=True)
    page.wait_for_timeout(300)
    dd.get_by_text("复制画布", exact=True).click()
    page.wait_for_timeout(800)
    check(
        "duplicate:named",
        page.get_by_role("button", name="测试A副本1", exact=True).count() == 1,
    )
    # 副本成为活动画布（触发器显示副本名）
    open_dropdown(page, "测试A副本1")
    dd = page.locator("[data-liblib-overlay='canvas-dropdown']")
    check(
        "duplicate:auto-switch",
        dd.locator("[data-canvas-row='canvas-4']").get_attribute("data-canvas-active") == "true",
    )

    # 6. 删除副本：确认框文案 + fallback
    row_dup = dd.locator("[data-canvas-row='canvas-4']")
    row_dup.hover()
    page.wait_for_timeout(250)
    row_dup.locator("button[aria-label='更多操作']").click(force=True)
    page.wait_for_timeout(300)
    dd.get_by_text("删除画布", exact=True).click()
    page.wait_for_timeout(400)
    confirm = page.locator("[data-canvas-delete-confirm]")
    check("delete:confirm-visible", confirm.is_visible())
    check(
        "delete:confirm-copy",
        "确定要删除画布「测试A副本1」吗？此操作不可恢复。" in confirm.inner_text(),
    )
    confirm.get_by_text("取消", exact=True).click()
    page.wait_for_timeout(300)
    check("delete:cancel-keeps", page.get_by_role("button", name="测试A副本1", exact=True).count() == 1)
    open_dropdown(page, "测试A副本1")
    dd = page.locator("[data-liblib-overlay='canvas-dropdown']")
    row_dup = dd.locator("[data-canvas-row='canvas-4']")
    row_dup.hover()
    page.wait_for_timeout(250)
    row_dup.locator("button[aria-label='更多操作']").click(force=True)
    page.wait_for_timeout(300)
    dd.get_by_text("删除画布", exact=True).click()
    page.wait_for_timeout(400)
    confirm = page.locator("[data-canvas-delete-confirm]")
    confirm.get_by_text("确认", exact=True).click()
    page.wait_for_timeout(600)
    check(
        "delete:fallback-to-测试A",
        page.get_by_role("button", name="测试A", exact=True).count() == 1
        and page.get_by_role("button", name="测试A副本1", exact=True).count() == 0,
    )

    # 7. 清理：删除 测试A（canvas-3），恢复初始 画布 1/画布 2
    open_dropdown(page, "测试A")
    dd = page.locator("[data-liblib-overlay='canvas-dropdown']")
    row_extra = dd.locator("[data-canvas-row='canvas-3']")
    row_extra.hover()
    page.wait_for_timeout(250)
    row_extra.locator("button[aria-label='更多操作']").click(force=True)
    page.wait_for_timeout(300)
    dd.get_by_text("删除画布", exact=True).click()
    page.wait_for_timeout(400)
    page.locator("[data-canvas-delete-confirm]").get_by_text("确认", exact=True).click()
    page.wait_for_timeout(600)
    open_dropdown(page, "画布 2")
    dd = page.locator("[data-liblib-overlay='canvas-dropdown']")
    check(
        "cleanup:back-to-initial",
        dd.locator("[data-canvas-row='canvas-1']").count() == 1
        and dd.locator("[data-canvas-row='canvas-2']").count() == 1
        and dd.locator("[data-canvas-row='canvas-3']").count() == 0,
    )

    check("diagnostics:zero", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 114,
        "title": "Multi-canvas dropdown alignment with 2026-09-06 sampling",
        "evidence": "docs/research/liblib-canvas-sampling-2026-09-06/README.md",
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
        "Batch 114 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "Row structure, newest-first order, four-item row menu, create 画布 3, "
        "rename, duplicate 副本 naming with auto-switch, delete confirm copy, "
        "cancel and fallback recorded in runtime-audit.json."
    )


if __name__ == "__main__":
    main()
