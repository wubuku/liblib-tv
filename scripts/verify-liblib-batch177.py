#!/usr/bin/env python3

"""Verify Batch 177: model row hover slide + attempt chip no-toggle.

Source evidence (2026-09-08 CDP, rendering window):
- model row text column slides via
  `translate-y-2 group-hover:translate-y-0 group-data-[selected=true]:translate-y-0`
  with a 200ms transition inside the 36px overflow-hidden column: default
  shows the 20px title with the 16px description clipped to an 8px sliver;
  hover OR selected slides it up 8px to reveal the description (row stays
  52px, hover bg white/10);
- attempt chips are NOT toggles: re-clicking the pressed 5分钟超长视频 chip
  keeps long mode and Auto·720P·300s; clicking another chip (首帧生成视频)
  switches with Auto·720P·5s and mode label 全能参考; the model switched to
  2.5 by the long chip does NOT revert on exit;
- source chips carry no aria-pressed / visible selected marker.
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
    / "liblib-canvas-batch177-2026-09-08"
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
        assert ok, f"batch177 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(BASE_URL, wait_until="networkidle")
    page.wait_for_timeout(500)

    page.locator('.react-flow__node[data-id="v-UGQZzZOpbv"]').click(force=True)
    page.wait_for_timeout(300)
    page.locator("[data-video-model-trigger]").click(force=True)
    page.wait_for_timeout(400)

    row = page.locator('[data-video-model-option="2.0 VIP"]')
    kid = row.locator("span[class*='translate-y-2']").first
    cls = (kid.get_attribute("class") or "")
    check("row:slide-classes", "translate-y-2" in cls and "group-hover:translate-y-0" in cls and "group-data-[selected=true]:translate-y-0" in cls and "transition-transform" in cls)
    check("row:group-on-button", "group" in (row.get_attribute("class") or ""))
    check("row:data-selected-attr", page.locator('[data-video-model-option][data-selected="true"]').count() == 1)

    # hover reveals description: after hover the kid translate should be 0
    row.hover()
    page.wait_for_timeout(350)
    tr = kid.evaluate("el => getComputedStyle(el).translate + '|' + getComputedStyle(el).transform")
    check("row:hover-slide-0", tr.split("|")[0] in ("0px", "0px 0px", "none") or tr.split("|")[1] != "none")
    h = row.bounding_box()["height"]
    check("row:hover-still-52", abs(h - 52) <= 1)

    # selected row shows slide-0 permanently (data-selected)
    sel_kid = page.locator('[data-video-model-option][data-selected="true"]').locator("span[class*='translate-y-2']").first
    page.mouse.move(700, 200)
    page.wait_for_timeout(350)
    sel_cls = (sel_kid.get_attribute("class") or "")
    check("row:selected-slide-class", "group-data-[selected=true]:translate-y-0" in sel_cls)

    page.keyboard.press("Escape")
    page.wait_for_timeout(200)

    # chips: re-click keeps selection (non-toggle)
    page.get_by_role("button", name="添加节点").click()
    page.wait_for_timeout(300)
    page.locator("[data-liblib-overlay='add-node']").get_by_role("button", name="视频", exact=True).click()
    page.wait_for_timeout(1000)
    attempts = page.locator("[data-video-attempts]")
    chip = attempts.locator("[data-video-attempt='5分钟超长视频']")
    chip.click()
    page.wait_for_timeout(400)
    chip.click()
    page.wait_for_timeout(400)
    check("chip:reclick-no-toggle", chip.get_attribute("aria-pressed") == "true")
    check(
        "chip:settings-still-long",
        "Auto · 720P · 300s" in page.locator("[data-video-params-trigger]").inner_text(),
    )

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 177, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch177: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
