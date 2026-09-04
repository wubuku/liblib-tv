#!/usr/bin/env python3

"""Verify Batch 105 follow banner alignment with the 2026-09-05 source audit."""

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
    / "liblib-canvas-batch105-2026-09-05"
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


def set_following(page: Page, value: bool) -> None:
    page.evaluate(
        f"() => window.__libtv_ui_store.setState({{ isFollowingSession: {str(value).lower()} }})"
    )
    page.wait_for_timeout(250)


def banner_opacity(page: Page) -> str:
    return page.locator("[data-follow-banner]").evaluate(
        "(el) => getComputedStyle(el).opacity"
    )


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool) -> None:
        assert ok, f"batch105 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(BASE_URL, wait_until="networkidle")
    page.wait_for_timeout(400)

    banner = page.locator("[data-follow-banner]")
    check("boot:banner-mounted", banner.count() == 1)
    check("boot:hidden", banner_opacity(page) == "0")
    check("boot:aria-hidden", banner.get_attribute("aria-hidden") == "true")

    set_following(page, True)
    check("follow:visible", banner_opacity(page) == "1")
    check("follow:not-aria-hidden", banner.get_attribute("aria-hidden") == "false")
    check("follow:text", banner.get_by_text("正在跟随", exact=True).is_visible())
    check("follow:tooltip", banner.get_by_text("按 ESC 退出", exact=True).is_visible())
    check("follow:cancel-visible", banner.locator("[data-follow-cancel]").is_visible())

    page.keyboard.press("Escape")
    page.wait_for_timeout(250)
    check("escape:exits-follow", banner_opacity(page) == "0")

    set_following(page, True)
    page.get_by_role("button", name="添加节点").click()
    page.wait_for_timeout(250)
    add_panel = page.locator('[data-liblib-overlay="add-node"]')
    check("priority:add-panel-open", add_panel.is_visible())
    page.keyboard.press("Escape")
    page.wait_for_timeout(250)
    check("priority:follow-first", banner_opacity(page) == "0")
    check("priority:add-panel-kept", add_panel.is_visible())
    page.keyboard.press("Escape")
    page.wait_for_timeout(250)
    check("priority:add-panel-then-closes", not add_panel.is_visible())

    set_following(page, True)
    banner.locator("[data-follow-cancel]").click()
    page.wait_for_timeout(250)
    check("cancel:exits-follow", banner_opacity(page) == "0")

    check("diagnostics:zero", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 105,
        "title": "Follow banner alignment with 2026-09-05 source audit",
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
        "Batch 105 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "Follow banner structure, faded default, cancel button, single-layer "
        "escape priority over add-node panel recorded in runtime-audit.json."
    )


if __name__ == "__main__":
    main()
