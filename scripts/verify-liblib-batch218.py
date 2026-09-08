#!/usr/bin/env python3

"""Verify Batch 218: mark select-mode banner blue card style.

Source evidence (source-mark-banner-style.json / screenshot): the 标记
select-mode banner is a blue (#1F6DFF) rounded-2xl card at top-center
(316×56) with a wand icon tile, title 元素选择模式, subtitle 点击图片选择
局部元素, a 返回节点 button and an × close. The clone banner now matches
this structure.
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
    / "liblib-canvas-batch218-2026-09-09"
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
        assert ok, f"batch218 check failed: {name}"
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
    check("banner:text", "元素选择模式" in text and "点击图片选择局部元素" in text and "返回节点" in text)

    bg = banner.evaluate("el => getComputedStyle(el).backgroundColor")
    check("banner:blue-bg", "0.99" in bg or bg.startswith("rgb(31") or bg.startswith("#1F6DFF") or "31, 109" in bg or "31, 109, 255" in bg)

    check("banner:wand-icon", banner.locator("svg").count() >= 1)
    check("banner:return-button", banner.locator("[data-mark-select-return]").count() == 1)
    check("banner:close-button", banner.get_by_label("关闭").count() == 1)

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 218, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch218: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
