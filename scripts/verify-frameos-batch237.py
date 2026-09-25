#!/usr/bin/env python3

"""Verify Batch 237: zoom-aware floating node titles.

Source measurement 2026-09-26: the node's floating title font scales with
canvas zoom — 9.07px at ~69% zoom (12 * zoom); fixed 12px at 100%. The
clone had a stylesheet-fixed 12px.

Checks:
1. title font ≈ 12px at 100%;
2. title font shrinks after two zoom-outs (< 11px);
3. errors clean.
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
    / "liblib-frameos-batch237-2026-09-26"
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


def title_font(page: Page) -> float:
    return page.evaluate(
        """(() => {
          const name = document.querySelector('.react-flow__node[data-id=\\'image-1\\'] .node-floating-title__name');
          return parseFloat(getComputedStyle(name).fontSize);
        })"""
    )


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool) -> None:
        assert ok, f"batch237 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/frameos/canvas/demo", wait_until="domcontentloaded", timeout=90000)
    page.wait_for_timeout(1500)

    font_100 = title_font(page)
    check("zoom100:title-approx-12", 11 <= font_100 <= 13)

    page.locator("button[aria-label='缩小']").first.click()
    page.wait_for_timeout(300)
    page.locator("button[aria-label='缩小']").first.click()
    page.wait_for_timeout(500)
    font_out = title_font(page)
    check("zoomout:title-shrinks", font_out < font_100 - 1.5)
    check("zoomout:title-floor", font_out >= 7)

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 237, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch237: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
