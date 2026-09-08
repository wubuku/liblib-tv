#!/usr/bin/env python3

"""Verify Batch 216: 参考 pill enters reference-select mode with banner.

Source evidence (source-参考-js-click.json): clicking the 参考 pill shows a
top-center banner 从画布或资产管理选择参考返回节点 (364x56) instructing the
user to pick a reference. The clone renders this banner (data-reference-
select-banner) when the pill is clicked; picking semantics on the canvas
remain unsampled.
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
    / "liblib-canvas-batch216-2026-09-08"
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
        assert ok, f"batch216 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto("http://localhost:4317", wait_until="networkidle")
    page.wait_for_timeout(500)

    page.locator('.react-flow__node[data-id="v-UGQZzZOpbv"]').click(force=True)
    page.wait_for_timeout(400)

    banner = page.locator("[data-reference-select-banner]")
    check("banner:closed-initial", banner.count() == 0)

    page.locator("[data-reference-select-trigger]").click()
    page.wait_for_timeout(400)
    check("banner:appears", banner.count() == 1)
    bb = banner.bounding_box()
    check("banner:width-364", abs(bb["width"] - 364) <= 4)
    check("banner:top-center", abs(bb["x"] + bb["width"] / 2 - 720) <= 8 and bb["y"] < 80)
    text = banner.inner_text().strip()
    check("banner:text", text == "从画布或资产管理选择参考返回节点")

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 216, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch216: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
