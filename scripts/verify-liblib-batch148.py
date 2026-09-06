#!/usr/bin/env python3

"""Verify Batch 148 project card cover placeholders."""

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
    / "liblib-canvas-batch148-2026-09-07"
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
        assert ok, f"batch148 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/project", wait_until="domcontentloaded")
    page.wait_for_timeout(600)
    page_root = page.locator("[data-project-list-page]")
    check("page:mounted", page_root.is_visible())

    cards = page_root.locator("[data-project-card]")
    card_count = cards.count()
    check("cards:exist", card_count >= 2)

    # 每张卡有封面区
    for i in range(card_count):
        card = cards.nth(i)
        cover = card.locator(".bg-gradient-to-br")
        check(f"card{i}:cover", cover.count() >= 1)
        check(f"card{i}:node-count", cover.locator("span").inner_text().strip() != "")

    # canvas-2（demo 项目）卡片名称正确
    demo_card_name = cards.nth(1).get_attribute("data-project-card")
    check("card1:is-canvas-2", demo_card_name == "canvas-2")

    # hover 无报错
    cards.nth(0).hover()
    page.wait_for_timeout(200)

    check("diagnostics:zero", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 148,
        "title": "Project card cover placeholders",
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
        "Batch 148 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "Project card cover placeholders with gradient backgrounds, node "
        "counts and hover behavior recorded in runtime-audit.json."
    )


if __name__ == "__main__":
    main()
