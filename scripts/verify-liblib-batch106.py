#!/usr/bin/env python3

"""Verify Batch 106 project menu alignment with the 2026-09-05 source audit."""

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
    / "liblib-canvas-batch106-2026-09-05"
    / "runtime-audit.json"
)

ITEMS = ["回到主页", "全部项目", "创建新项目", "删除项目"]


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
        assert ok, f"batch106 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(BASE_URL, wait_until="networkidle")
    page.wait_for_timeout(400)

    trigger = page.locator("[data-project-menu-trigger]")
    check("trigger", trigger.count() == 1)
    trigger.click()
    page.wait_for_timeout(200)
    menu = page.locator("[data-project-menu]")
    check("menu:open", menu.is_visible())
    for item in ITEMS:
        check(f"menu:item:{item}", menu.locator(f"[data-project-menu-item='{item}']").count() == 1)

    menu.locator("[data-project-menu-item='创建新项目']").click()
    page.wait_for_timeout(150)
    check("menu:status", "本地原型" in menu.locator("[data-project-menu-status]").inner_text())
    check("menu:still-open", menu.is_visible())

    page.get_by_role("button", name="移动", exact=True).click()
    page.wait_for_timeout(200)
    check("outside:closes", page.locator("[data-project-menu]").count() == 0)

    # 教程 popover 四项（既有实现，锁定合同）
    page.get_by_role("button", name="教程与帮助").click()
    page.wait_for_timeout(250)
    for item in ITEMS_TUTORIAL:
        check(f"tutorial:{item}", page.get_by_text(item, exact=True).is_visible())

    check("diagnostics:zero", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


ITEMS_TUTORIAL = ["使用教程", "联系客服", "联系销售", "关注公众号"]


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 106,
        "title": "Project menu alignment with 2026-09-05 source sampling",
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
        "Batch 106 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "Project menu items/grouping, local statuses, outside-close and "
        "tutorial popover contract recorded in runtime-audit.json."
    )


if __name__ == "__main__":
    main()
