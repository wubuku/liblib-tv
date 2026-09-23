#!/usr/bin/env python3

"""Verify Batch 205: FrameOS fullscreen text view (全屏查看).

The text node toolbar's 全屏查看 opens a fullscreen reading overlay with
the node title and content; × / Esc closes. Inferred implementation (the
source button exists; its exact behavior unsampled).
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
    / "liblib-frameos-batch205-2026-09-24"
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


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool) -> None:
        assert ok, f"batch205 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/frameos/canvas/demo", wait_until="domcontentloaded")
    page.wait_for_timeout(1200)

    text_node = page.locator(".react-flow__node-text").first
    text_node.click(position={"x": 150, "y": 100})
    page.wait_for_timeout(400)
    toolbar = page.locator(".frameos-floating-toolbar-new")
    check("toolbar:opens", toolbar.is_visible())

    toolbar.locator("button[aria-label='全屏查看']").click()
    page.wait_for_timeout(500)
    view = page.locator("[data-frameos-fullscreen-text]")
    check("fullscreen-view:opens", view.is_visible())
    check(
        "fullscreen-view:content",
        "一对怨侣在咖啡馆对峙" in view.inner_text(),
    )

    view.locator("button[aria-label='关闭全屏查看']").click()
    page.wait_for_timeout(300)
    check("fullscreen-view:closes", page.locator("[data-frameos-fullscreen-text]").count() == 0)

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 205, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch205: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
