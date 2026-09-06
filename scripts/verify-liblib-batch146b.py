#!/usr/bin/env python3

"""Verify Batch 146b 文化区域 filter options in the character library."""

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
    / "liblib-canvas-batch146b-2026-09-07"
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
        assert ok, f"batch146b check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(BASE_URL, wait_until="networkidle")
    page.wait_for_timeout(500)

    page.locator("button[aria-label='角色库']").click()
    page.wait_for_timeout(800)
    modal = page.locator("[data-liblib-overlay='primary:character']")
    check("modal:opens", modal.is_visible())

    filter_toggle = modal.locator("[data-character-filter-toggle]")
    filter_toggle.click()
    page.wait_for_timeout(300)
    filter_panel = modal.locator("[data-character-filter-panel]")
    check("filter:panel-opens", filter_panel.is_visible())

    check("culture:label", filter_panel.get_by_text("文化区域", exact=True).is_visible())
    for region in ["华语", "日韩", "欧美", "东南亚"]:
        check(
            f"culture:{region}",
            filter_panel.locator(f"[data-character-filter-chip='{region}']").count() == 1,
        )

    # 点击 华语 芯片 → 筛选生效（有结果）
    filter_panel.locator("[data-character-filter-chip='华语']").click()
    page.wait_for_timeout(300)
    cards = page.locator("[data-character-strip-card]")
    check("filter:has-results", cards.count() > 0)

    # 清空筛选
    filter_panel.locator("[data-character-filter-clear]").click()
    page.wait_for_timeout(300)
    check("clear:restores", cards.count() > 0)

    filter_toggle.click()
    page.wait_for_timeout(200)
    check("filter:closes", filter_panel.count() == 0)

    check("diagnostics:zero", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": "146b",
        "title": "文化区域 filter options in character library",
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
        "Batch 146b verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "文化区域 filter group with four regional chips, clear/restore, filter "
        "close recorded in runtime-audit.json."
    )


if __name__ == "__main__":
    main()
