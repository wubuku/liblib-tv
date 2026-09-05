#!/usr/bin/env python3

"""Verify Batch 121 topbar freshness alignment with the 2026-09-06 source."""

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
    / "liblib-canvas-batch121-2026-09-06"
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
        assert ok, f"batch121 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(BASE_URL, wait_until="networkidle")
    page.wait_for_timeout(400)

    actions = page.locator("[data-liblib-topnav-actions]")
    check("credits:100", actions.locator("button").filter(has_text="100").count() == 1)
    check(
        "membership:button",
        actions.get_by_text("开通会员", exact=True).count() == 1
        and actions.get_by_text("限时 45 折", exact=True).count() == 1,
    )

    # 教程入口更名
    tutorial = page.get_by_role("button", name="教程", exact=True)
    check("tutorial:entry", tutorial.count() == 1)
    tutorial.click()
    page.wait_for_timeout(500)
    check(
        "tutorial:popover-items",
        all(page.get_by_text(t, exact=True).count() >= 1 for t in ["使用教程", "联系客服", "联系销售", "关注公众号"]),
    )
    page.keyboard.press("Escape")
    page.wait_for_timeout(300)

    # 顶栏按钮集合关键项
    for name in ["发布与分享", "积分超市", "开通会员 限时 45 折", "Agent"]:
        check(f"topbar:{name}", page.get_by_role("button", name=name, exact=True).count() >= 1)

    check("diagnostics:zero", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 121,
        "title": "Topbar freshness alignment with the 2026-09-06 source",
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
        "Batch 121 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "Credits 100, membership 限时 45 折 entry, 教程 entry rename and "
        "topbar key buttons recorded in runtime-audit.json."
    )


if __name__ == "__main__":
    main()
