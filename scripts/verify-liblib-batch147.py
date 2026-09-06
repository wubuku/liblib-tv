#!/usr/bin/env python3

"""Verify Batch 147 character library filter end-to-end behavior."""

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
    / "liblib-canvas-batch147-2026-09-07"
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
        assert ok, f"batch147 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(BASE_URL, wait_until="networkidle")
    page.wait_for_timeout(500)

    # 打开角色库
    page.locator("button[aria-label='角色库']").click()
    page.wait_for_timeout(800)
    modal = page.locator('[data-liblib-overlay="primary:character"]')
    check("modal:opens", modal.is_visible())

    # 打开筛选面板
    filter_toggle = modal.locator("[data-character-filter-toggle]")
    filter_toggle.click()
    page.wait_for_timeout(300)
    filter_panel = modal.locator("[data-character-filter-panel]")
    check("filter:panel-opens", filter_panel.is_visible())

    # 性别组
    check("filter:性别-label", filter_panel.get_by_text("性别", exact=True).is_visible())
    for chip in ["男", "女", "中性"]:
        check(f"filter:chip:{chip}", filter_panel.locator(f"[data-character-filter-chip='{chip}']").count() == 1)

    # 点击 女 → 过滤出女性角色
    filter_panel.locator("[data-character-filter-chip='女']").click()
    page.wait_for_timeout(500)
    female_count = page.evaluate(
        "() => Array.from(document.querySelectorAll('[data-character-strip-card]')).filter(e => e.textContent.includes('女') || e.textContent.includes('母')).length"
    )
    check("filter:female-has-results", female_count >= 1)

    # 清空筛选
    filter_panel.locator("[data-character-filter-clear]").click()
    page.wait_for_timeout(300)
    all_count = page.locator("[data-character-strip-card]").count()
    check("clear:restores", all_count >= 10)

    # 关闭筛选面板
    filter_toggle.click()
    page.wait_for_timeout(200)
    check("filter:closes", filter_panel.count() == 0)

    check("diagnostics:zero", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 147,
        "title": "Character library filter end-to-end behavior",
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
        "Batch 147 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "Character filter panel open/chips/clear/close cycle recorded in "
        "runtime-audit.json."
    )


if __name__ == "__main__":
    main()
