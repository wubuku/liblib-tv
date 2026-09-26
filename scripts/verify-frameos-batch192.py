#!/usr/bin/env python3

"""Verify Batch 192: FrameOS help panel layout aligned to source.

Source form (2026-09-24 re-sample): a LEFT slide-in side panel (~320px
wide, anchored below the top bar) with the four shortcut groups stacked in
a single scrollable column — not a centered two-column modal. Verifies the
panel geometry, single-column flow, verbatim rows, and close paths.
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
    / "liblib-frameos-batch192-2026-09-24"
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
        assert ok, f"batch192 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/frameos/canvas/demo", wait_until="domcontentloaded", timeout=90000)
    page.wait_for_timeout(1200)

    page.keyboard.press("?")
    page.wait_for_timeout(400)
    panel = page.locator(".frameos-shortcuts-panel")
    check("help:opens", panel.is_visible())
    box = panel.bounding_box()
    check(
        "panel:left-anchored",
        box is not None and abs(box["x"] - 72) < 6 and abs(box["width"] - 320) < 6,
    )

    # 单列: 创作和缩放两个分组的标题 y 递增 (纵向堆叠)
    y1 = page.locator("[data-frameos-help-icon='创作']").bounding_box()["y"]
    y2 = page.locator("[data-frameos-help-icon='缩放']").bounding_box()["y"]
    check("help:single-column", y2 > y1)

    rows = ["搜索节点", "取消选中"]
    text = panel.inner_text()
    for r in rows:
        check(f"help:row:{r}", r in text)

    # × 关闭
    panel.locator("button[aria-label='关闭']").click()
    page.wait_for_timeout(300)
    check("help:close-x", panel.count() == 0)

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 192, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch192: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
