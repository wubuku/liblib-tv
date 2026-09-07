#!/usr/bin/env python3

"""Verify Batch 179: canvas token harvest alignment + consent gate re-probe.

Source evidence (2026-09-08 CDP):
- :root tokens --canvas-controls-bg #262626 / -border #363636 / -text #fff /
  -hover #ffffff1a (chip hover bg measured rgba(255,255,255,0.1)),
  --canvas-shadow-* match the clone globals verbatim, --z-panel 400,
  --z-modal 500, --fg-default #f7f7f7, --fg-muted #919191;
- clone now defines the same tokens; chip hover uses the token; context
  menu item text uses the token (#fff);
- 素材库 consent gate re-probe: gate still blocks content on the source;
  nothing accepted on the user's behalf (batch169 clone gate unchanged).
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
    / "liblib-canvas-batch179-2026-09-08"
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
        assert ok, f"batch179 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(BASE_URL, wait_until="networkidle")
    page.wait_for_timeout(500)

    tokens = page.evaluate(
        """() => {
        const cs = getComputedStyle(document.documentElement);
        return ['--canvas-controls-bg','--canvas-controls-border','--canvas-controls-text',
                '--canvas-controls-hover','--canvas-shadow-menu','--z-panel','--z-modal',
                '--fg-default','--fg-muted'].map(k => [k, cs.getPropertyValue(k).trim()]);
        }"""
    )
    tok = dict(tokens)
    check("token:controls-bg", tok["--canvas-controls-bg"] == "#262626")
    check("token:controls-border", tok["--canvas-controls-border"] == "#363636")
    check("token:controls-text", tok["--canvas-controls-text"] == "#fff")
    check("token:controls-hover", tok["--canvas-controls-hover"] == "#ffffff1a")
    check("token:shadow-menu", "8px 32px" in tok["--canvas-shadow-menu"])
    check("token:z-panel-modal", tok["--z-panel"] == "400" and tok["--z-modal"] == "500")
    check("token:fg-default-muted", tok["--fg-default"] == "#f7f7f7" and tok["--fg-muted"] == "#919191")

    # chip hover uses the token value (alpha 0.1)
    page.get_by_role("button", name="添加节点").click()
    page.wait_for_timeout(300)
    page.locator("[data-liblib-overlay='add-node']").get_by_role("button", name="视频", exact=True).click()
    page.wait_for_timeout(1000)
    chip = page.locator("[data-video-attempt='首帧生成视频']")
    chip.hover()
    page.wait_for_timeout(300)
    hb = chip.evaluate("el => getComputedStyle(el).backgroundColor")
    check("chip:hover-alpha-0-1", "0.1" in hb)

    # context menu item text uses #fff
    page.mouse.click(1200, 300, button="right")
    page.wait_for_timeout(400)
    menu = page.locator("[data-canvas-context-menu]")
    if menu.count() == 0:
        page.mouse.click(1200, 300, button="right")
        page.wait_for_timeout(400)
    item = page.locator("[data-canvas-context-item='上传']")
    color = item.evaluate("el => getComputedStyle(el).color")
    check("menu:item-text-fff", color == "rgb(255, 255, 255)")
    page.keyboard.press("Escape")
    page.wait_for_timeout(200)

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 179, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch179: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
