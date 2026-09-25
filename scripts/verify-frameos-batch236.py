#!/usr/bin/env python3

"""Verify Batch 236: zoom-aware replace-content buttons.

Source measurement 2026-09-26: the node's 替换内容 button scales linearly
with canvas zoom — 30x30 px at 100%, ~22.7px at 75% (30 * zoom). The clone
had a fixed 22px button at every zoom level.

Checks (content image node, 100% → zoom out twice → 75%):
1. button ≈ 30px at 100%;
2. button shrinks after zoom-out (≤ 27px, i.e. 30 * ≤0.9);
3. click still opens the file chooser (position/size independent);
4. errors clean.
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
    / "liblib-frameos-batch236-2026-09-26"
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


def btn_size(page: Page) -> float:
    return page.evaluate(
        """(() => {
          const img = document.querySelector('.react-flow__node[data-id=\\'image-1\\']');
          const btn = img.querySelector('button[aria-label=\\'替换内容\\']');
          return btn.getBoundingClientRect().width;
        })"""
    )


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool) -> None:
        assert ok, f"batch236 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/frameos/canvas/demo", wait_until="domcontentloaded", timeout=90000)
    page.wait_for_timeout(1500)

    size_100 = btn_size(page)
    check("zoom100:button-approx-30", 26 <= size_100 <= 34)

    # 缩小两档 (MapDock 缩小按钮)
    page.locator("button[aria-label='缩小']").first.click()
    page.wait_for_timeout(300)
    page.locator("button[aria-label='缩小']").first.click()
    page.wait_for_timeout(500)
    size_out = btn_size(page)
    check("zoom75:button-shrinks", size_out < size_100 - 2)
    check("zoom75:button-scales", 18 <= size_out <= 27)

    # 按钮仍可点击 (触发了 file chooser)
    with page.expect_file_chooser() as fc_info:
        page.locator(
            ".react-flow__node[data-id='image-1'] button[aria-label='替换内容']"
        ).click(force=True)
    check("zoom75:still-opens-chooser", fc_info.value is not None)

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 236, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch236: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
