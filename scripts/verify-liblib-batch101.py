#!/usr/bin/env python3

"""Verify Batch 101 generation-history panel alignment with the 2026-09-05 source audit."""

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
    / "liblib-canvas-batch101-2026-09-05"
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
        assert ok, f"batch101 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(BASE_URL, wait_until="networkidle")
    page.wait_for_timeout(400)

    page.get_by_role("button", name="生成历史").click()
    panel = page.locator('[data-liblib-overlay="primary:history"]')
    assert panel.is_visible()

    check("title", panel.get_by_role("heading", name="生成历史").is_visible())
    check("size-control", panel.locator("[data-history-size-control] input[type=range]").count() == 1)

    first_item = panel.locator("article").first
    size_before = first_item.evaluate("(el) => el.getBoundingClientRect().width")
    panel.locator("[data-history-size-control] input[type=range]").evaluate(
        "(el) => { const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set; setter.call(el, 150); el.dispatchEvent(new Event('input', { bubbles: true })); el.dispatchEvent(new Event('change', { bubbles: true })); }"
    )
    page.wait_for_timeout(150)
    size_after = first_item.evaluate("(el) => el.getBoundingClientRect().width")
    check("slider:resizes-thumbs", size_after > size_before)

    check("scope-chip", panel.locator("[data-history-scope-chip]").is_visible())
    check("scope-chip:pressed", panel.locator("[data-history-scope-chip]").get_attribute("aria-pressed") == "true")
    for tab_id, label, count in [("image", "图片", "3"), ("video", "视频", "0"), ("audio", "音频", "0")]:
        tab = panel.locator(f"[data-history-tab='{tab_id}']")
        check(f"tab:{tab_id}", tab.is_visible() and count in tab.inner_text())

    check("rating-button", panel.locator("[data-history-rating]").inner_text().strip() == "所有评级")
    panel.locator("[data-history-rating]").click()
    menu = panel.locator("[data-history-rating-menu]")
    check("rating-menu:open", menu.is_visible())
    check("rating-menu:options", menu.locator("[data-history-rating-option='all']").count() == 1 and menu.locator("[data-history-rating-option='favorited']").count() == 1)
    menu.locator("[data-history-rating-option='favorited']").click()
    page.wait_for_timeout(150)
    check("rating:filter-empty", "暂无历史记录" in panel.inner_text())
    check("rating:button-label", panel.locator("[data-history-rating]").inner_text().strip() == "已收藏")
    check("rating:menu-closed", panel.locator("[data-history-rating-menu]").count() == 0)
    panel.locator("[data-history-rating]").click()
    panel.locator("[data-history-rating-option='all']").click()
    page.wait_for_timeout(150)
    check("rating:all-restores", panel.locator("article").count() == 3)

    check("sort-button", panel.get_by_text("时间倒序", exact=True).is_visible())
    check("batch-button", panel.get_by_text("批量操作", exact=True).is_visible())

    panel.locator("[data-history-tab='video']").click()
    check("empty-tab:text", "暂无历史记录" in panel.inner_text())

    page.keyboard.press("Escape")
    page.wait_for_timeout(150)
    check("escape:closes", not panel.is_visible())

    check("diagnostics:zero", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 101,
        "title": "Generation-history panel alignment with 2026-09-05 source audit",
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
        "Batch 101 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "Title, size slider, scope chip, counted tabs, rating menu with local "
        "favorite filter, sort/batch controls, empty-state copy and escape "
        "recorded in runtime-audit.json."
    )


if __name__ == "__main__":
    main()
