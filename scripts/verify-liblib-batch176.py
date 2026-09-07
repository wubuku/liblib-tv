#!/usr/bin/env python3

"""Verify Batch 176: long-video params menu + chip model linkage.

Source evidence (2026-09-08 CDP, rendering window):
- long chip switches the footer model to 2.5 (long pipeline model) with
  mode 超长视频 and Auto · 720P · 300s;
- long params menu: 340x396, ratio grid SEVEN tiles WITH Auto first
  (selected white/10, 5 per row, 57x62), resolution 480P/720P/1080P
  (720P selected), duration slider input min=30 max=300 value=300 with the
  hint 因剧情和画面设计，实际时长可能略有差异, audio 开启/关闭, and NO
  count section;
- normal mode keeps six ratio tiles without Auto (Batch 175 contract).
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
    / "liblib-canvas-batch176-2026-09-08"
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
        assert ok, f"batch176 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(BASE_URL, wait_until="networkidle")
    page.wait_for_timeout(500)

    # fresh video node + long chip
    page.get_by_role("button", name="添加节点").click()
    page.wait_for_timeout(300)
    page.locator("[data-liblib-overlay='add-node']").get_by_role("button", name="视频", exact=True).click()
    page.wait_for_timeout(1000)
    page.locator("[data-video-attempts]").locator("[data-video-attempt='5分钟超长视频']").click()
    page.wait_for_timeout(500)

    check("chip:model-2-5", page.locator("[data-video-model-trigger]").inner_text().strip() == "2.5")
    check("chip:mode-long", "超长视频" in page.locator("[data-video-mode-trigger]").inner_text())
    check("chip:auto-300s", "Auto · 720P · 300s" in page.locator("[data-video-params-trigger]").inner_text())
    check("chip:credits-14700", page.locator("[data-video-credits]").inner_text() == "14700")

    page.locator("[data-video-params-trigger]").click(force=True)
    page.wait_for_timeout(300)
    check("menu:open-long", page.locator("[data-video-params-menu]").get_attribute("data-video-params-mode") == "long")

    ids = page.eval_on_selector_all(
        "[data-video-ratio-option]",
        "els => els.map(el => el.getAttribute('data-video-ratio-option'))",
    )
    check("menu:seven-tiles-with-auto", ids == ["Auto", "16:9", "4:3", "1:1", "3:4", "9:16", "21:9"])
    auto_pressed = page.locator('[data-video-ratio-option="Auto"]').get_attribute("aria-pressed")
    check("menu:auto-selected", auto_pressed == "true")
    tile = page.locator('[data-video-ratio-option="Auto"]').bounding_box()
    check("menu:tile-62", tile is not None and abs(tile["height"] - 62) <= 2)

    duration = page.locator("[data-video-duration]")
    check("menu:duration-30-300", duration.get_attribute("min") == "30" and duration.get_attribute("max") == "300" and duration.input_value() == "300")
    check("menu:long-hint-text", page.locator("[data-video-long-hint]").inner_text() == "因剧情和画面设计，实际时长可能略有差异")
    check("menu:no-count-in-long", page.locator("[data-video-count-option]").count() == 0)
    page.screenshot(path=str(AUDIT_PATH.parent / "clone-long-params.png"))

    page.keyboard.press("Escape")
    page.wait_for_timeout(200)
    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 176, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch176: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
