#!/usr/bin/env python3

"""Verify Batch 217: 标记 pill opens the element-select mode banner.

Source evidence (source-mark-js-click.json): JS-clicking the 标记 pill shows
a top-center banner (316×56) reading 元素选择模式点击图片选择局部元素返回
节点 — an element-select mode like the 参考 pill's banner. The clone renders
this banner via data-mark-select-banner.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = (
    ROOT
    / "docs"
    / "research"
    / "liblib-canvas-batch217-2026-09-09"
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
        assert ok, f"batch217 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto("http://localhost:4317", wait_until="networkidle")
    page.wait_for_timeout(500)

    page.locator('.react-flow__node[data-id="v-UGQZzZOpbv"]').click(force=True)
    page.wait_for_timeout(400)

    banner = page.locator("[data-mark-select-banner]")
    check("banner:closed-initial", banner.count() == 0)

    page.locator("[data-mark-select-trigger]").click()
    page.wait_for_timeout(400)
    check("banner:appears", banner.count() == 1)
    bb = banner.bounding_box()
    check("banner:width-316", abs(bb["width"] - 316) <= 4)
    check("banner:top-center", abs(bb["x"] + bb["width"] / 2 - 720) <= 8 and bb["y"] < 80)
    text = banner.inner_text().strip()
    check("banner:text", text == "元素选择模式点击图片选择局部元素返回节点")

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 217, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch217: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
