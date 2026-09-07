#!/usr/bin/env python3

"""Verify Batch 178: chip selected marker + mode-menu cancel path.

Source evidence (2026-09-08 CDP, rendering window):
- chip selected marker = background white/10% with unchanged #f7f7f7 text
  (the clone's former cyan #09caf5 tint dropped); chips are rounded-lg with
  a leading 14px icon (lucide substitutes: Infinity / GalleryHorizontalEnd /
  Frame);
- ESC does NOT cancel the attempt — it deselects the node; the attempt
  persists across reselect;
- the real cancel path is the MODE MENU: switching out of 超长视频 (click
  文生视频) clears the chip and clamps duration 300 -> 30 (ratio Auto kept).
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
    / "liblib-canvas-batch178-2026-09-08"
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
        assert ok, f"batch178 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(BASE_URL, wait_until="networkidle")
    page.wait_for_timeout(500)

    # fresh video node + long chip
    page.get_by_role("button", name="添加节点").click()
    page.wait_for_timeout(300)
    page.locator("[data-liblib-overlay='add-node']").get_by_role("button", name="视频", exact=True).click()
    page.wait_for_timeout(1000)
    attempts = page.locator("[data-video-attempts]")
    chip = attempts.locator("[data-video-attempt='5分钟超长视频']")
    chip.click()
    page.wait_for_timeout(400)

    # chip visual: white/10 bg (Tailwind 4 oklab), #f7f7f7 text, icon, rounded-lg
    bg = chip.evaluate("el => getComputedStyle(el).backgroundColor")
    color = chip.evaluate("el => getComputedStyle(el).color")
    radius = chip.evaluate("el => getComputedStyle(el).borderTopLeftRadius")
    cls = chip.get_attribute("class") or ""
    check("chip:selected-white-10", "bg-white/[0.1]" in cls and "0.1" in bg and "bg-white/[0.05]" not in cls)
    check("chip:text-f7", color == "rgb(247, 247, 247)")
    check("chip:rounded-lg", radius == "8px")
    check("chip:has-icon", chip.locator("svg").count() == 1)
    # Batch 180: 图标换为源站 iconify 原字形（viewBox 直采断言由 batch179 覆盖）

    # mode menu cancel path: switch to 文生视频 -> chip cleared + duration clamped
    page.locator("[data-video-mode-trigger]").click(force=True)
    page.wait_for_timeout(300)
    page.locator('[data-video-mode-option="text"]').click(force=True)
    page.wait_for_timeout(500)
    check("cancel:chip-cleared", chip.get_attribute("aria-pressed") == "false")
    label = page.locator("[data-video-params-trigger]").inner_text()
    seconds = int(label.split("·")[2].strip().replace("s", ""))
    check("cancel:duration-clamped-30", seconds <= 30)
    check("cancel:mode-label", "文生视频" in page.locator("[data-video-mode-trigger]").inner_text())

    # ESC keeps the attempt (only deselects the node): re-select and check long persists.
    # Drag the node up-left first (the in-card panel follows; avoids the
    # preset-node overlap at flow center, stays in viewport).
    node_box = page.locator(".react-flow__node-video").last.bounding_box()
    sx, sy = node_box["x"] + node_box["width"] / 2, node_box["y"] + 12
    page.mouse.move(sx, sy)
    page.mouse.down()
    page.mouse.move(sx - 260, sy - 240, steps=8)
    page.mouse.up()
    page.wait_for_timeout(400)
    chip.click()
    page.wait_for_timeout(400)
    check("reengage:chip-on", chip.get_attribute("aria-pressed") == "true")
    page.keyboard.press("Escape")
    page.wait_for_timeout(300)
    page.locator(".react-flow__node-video").last.click(position={"x": 40, "y": 12}, force=True)
    page.wait_for_timeout(600)
    check("esc:attempt-persists", attempts.locator("[data-video-attempt='5分钟超长视频']").get_attribute("aria-pressed") == "true")
    check("esc:mode-still-long", "超长视频" in page.locator("[data-video-mode-trigger]").inner_text())

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 178, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch178: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
