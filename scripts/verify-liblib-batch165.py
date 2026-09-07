#!/usr/bin/env python3

"""Verify Batch 165: reference slot row layout per sampled source classes.

Source evidence (2026-09-07 carrier panel): slot row `flex w-full min-w-0
flex-wrap items-start gap-2 pl-1`, no fixed height (h-12 clipped the 55px
slots), and no 「Auto Link：」summary text in any sampled panel state.
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
    / "liblib-canvas-batch165-2026-09-07"
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
    return errors


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool) -> None:
        assert ok, f"batch165 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(BASE_URL, wait_until="networkidle")
    page.wait_for_timeout(400)

    page.get_by_role("button", name="添加节点").click()
    page.wait_for_timeout(400)
    panel = page.locator("[data-liblib-overlay='add-node']")
    panel.get_by_role("button", name="视频", exact=True).click()
    page.wait_for_timeout(1200)
    node = page.locator(".react-flow__node-video").first
    node.click()
    page.wait_for_timeout(600)

    vg = page.locator("[data-video-generation-panel]")
    check("panel:open", vg.is_visible())

    # 槽行：高 ≥55（槽不被裁切）、flex-wrap、items-start
    row = vg.locator(".flex-wrap").first
    check("slots:row-present", row.count() >= 1)
    rbox = row.bounding_box()
    check("slots:row-fits-55", rbox is not None and rbox["height"] >= 54)
    check(
        "slots:items-start",
        row.evaluate("el => getComputedStyle(el).alignItems") == "flex-start",
    )
    slot = row.locator(".cursor-grab").first
    sbox = slot.bounding_box()
    check("slots:48x55", sbox is not None and abs(sbox["width"] - 48) <= 2 and abs(sbox["height"] - 55) <= 3)

    # 无 Auto Link 汇总文字
    check("slots:no-autolink-text", vg.get_by_text("Auto Link：").count() == 0)

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 165, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch165: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
