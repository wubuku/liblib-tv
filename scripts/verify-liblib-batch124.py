#!/usr/bin/env python3

"""Verify Batch 124 canvas recycle bin (soft delete + restore)."""

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
    / "liblib-canvas-batch124-2026-09-06"
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


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool) -> None:
        assert ok, f"batch124 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/project", wait_until="domcontentloaded")
    page.wait_for_timeout(600)
    page_root = page.locator("[data-project-list-page]")
    check("page:mounted", page_root.is_visible())

    # 空回收站文案
    page_root.locator("[data-project-recycle]").click()
    page.wait_for_timeout(300)
    panel = page.locator("[data-recycle-panel]")
    check("panel:opens", panel.is_visible())
    check("panel:copy", "仅显示最近 30 天内删除的内容" in panel.inner_text())
    check("panel:empty", panel.locator("[data-recycle-empty]").is_visible())

    # 画布 2 上删除（经确认框）
    page.goto(f"{BASE_URL}", wait_until="domcontentloaded")
    page.wait_for_timeout(600)
    open_dd = page.locator("[data-liblib-overlay='canvas-dropdown']")
    if not open_dd.is_visible():
        page.get_by_role("button", name="画布 2", exact=True).first.click()
        page.wait_for_timeout(400)
    dd = page.locator("[data-liblib-overlay='canvas-dropdown']")
    row2 = dd.locator("[data-canvas-row='canvas-2']")
    row2.hover()
    page.wait_for_timeout(250)
    row2.locator("button[aria-label='更多操作']").click(force=True)
    page.wait_for_timeout(300)
    dd.get_by_text("删除画布", exact=True).click()
    page.wait_for_timeout(400)
    page.locator("[data-canvas-delete-confirm]").get_by_text("确认", exact=True).click()
    page.wait_for_timeout(700)
    check(
        "delete:canvas2-gone",
        page.locator(".react-flow__node").count() == 0
        or page.get_by_role("button", name="画布 2", exact=True).count() == 0,
    )

    # /project 回收站列出 画布 2（客户端导航保持内存 store 的回收站状态）
    page.locator("[data-project-menu-trigger]").click()
    page.wait_for_timeout(300)
    page.evaluate("""() => {
      const items = Array.from(document.querySelectorAll("[data-project-menu-item]")).filter((b) => b.textContent.trim() === "全部项目");
      items[0].click();
    }""")
    page.wait_for_timeout(900)
    page_root = page.locator("[data-project-list-page]")
    check("menu:navigates", page_root.is_visible())
    page_root.locator("[data-project-recycle]").click()
    page.wait_for_timeout(300)
    item = page_root.locator("[data-recycle-item='canvas-2']")
    check("recycle:lists-canvas2", item.is_visible())
    check("recycle:has-restore", item.locator("[data-recycle-restore='canvas-2']").count() == 1)
    check(
        "recycle:has-date",
        "2026-" in item.inner_text() and "剩余 30 天" in item.inner_text(),
    )

    # 恢复 画布 2
    item.locator("[data-recycle-restore='canvas-2']").click()
    page.wait_for_timeout(700)
    check("restore:item-gone", page_root.locator("[data-recycle-item='canvas-2']").count() == 0)
    check(
        "restore:canvas-back-in-list",
        page_root.locator("[data-project-card='canvas-2']").count() == 1,
    )

    # 回画布验证内容完整（节点数量与初始一致；卡片点击为客户端路由）
    page.evaluate("""() => {
      const card = document.querySelector("[data-project-card='canvas-2']");
      if (card) card.click();
    }""")
    page.wait_for_timeout(1000)
    check(
        "restore:content-intact",
        page.locator(".react-flow__node").count() >= 10,
    )
    check(
        "restore:canvas-2-active",
        page.get_by_role("button", name="画布 2", exact=True).count() == 1,
    )

    check("diagnostics:zero", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 124,
        "title": "Canvas recycle bin (soft delete + restore)",
        "evidence": "docs/research/liblib-projects-page-2026-09-06/README.md",
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
        "Batch 124 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "Recycle panel, 30-day copy, soft-delete listing, restore with intact "
        "content and active-canvas behavior recorded in runtime-audit.json."
    )


if __name__ == "__main__":
    main()
