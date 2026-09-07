#!/usr/bin/env python3

"""Verify Batch 161: video panel height fits the vertical advanced column.

Regression found by measurement: the fixed 274px panel overflowed after
Batch 149's ~156px advanced column — the prompt textarea collapsed to 16px
and the advanced section crossed the section border by 35px. Source panel
shows a ~96px prompt region (2026-09-07 dump). Panel now 397px.
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
    / "liblib-canvas-batch161-2026-09-07"
    / "runtime-audit.json"
)
MOBILE_SCREENSHOT = (
    ROOT
    / "docs"
    / "design-references"
    / "liblib-clone-batch162-video-panel-mobile-390-2026-09-07.png"
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
        assert ok, f"batch161 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(BASE_URL, wait_until="networkidle")
    page.wait_for_timeout(400)

    page.get_by_role("button", name="添加节点").click()
    page.wait_for_timeout(400)
    panel = page.locator("[data-liblib-overlay='add-node']")
    panel.get_by_role("button", name="视频", exact=True).click()
    page.wait_for_timeout(1200)
    node = page.locator(".react-flow__node-video").first
    node.click()
    page.wait_for_timeout(600)

    m = page.evaluate("""() => {
      const section = document.querySelector("[data-video-generation-panel] section");
      const ta = document.querySelector("[data-video-generation-panel] textarea");
      const adv = document.querySelector("[data-video-advanced-inline]");
      const sec = section.getBoundingClientRect();
      const a = adv.getBoundingClientRect();
      return {
        sectionH: Math.round(sec.height),
        taH: Math.round(ta.getBoundingClientRect().height),
        overflow: Math.round(a.bottom - sec.bottom),
      };
    }""")
    check("panel:height-397", m["sectionH"] == 397)
    check("panel:prompt-96", 88 <= m["taH"] <= 102)
    check("panel:no-overflow", m["overflow"] <= 0)
    result["measurements"] = m

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def run_mobile(page: Page) -> dict[str, Any]:
    """Batch 162: 390x844 移动端断点 —— 397px 增高后无页面级溢出，提示词完好。"""
    result: dict[str, Any] = {"viewport": "390x844", "checks": []}

    def check(name: str, ok: bool) -> None:
        assert ok, f"batch162 mobile check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(BASE_URL, wait_until="networkidle")
    page.wait_for_timeout(500)
    page.get_by_role("button", name="添加节点").click()
    page.wait_for_timeout(400)
    overlay = page.locator("[data-liblib-overlay='add-node']")
    overlay.get_by_role("button", name="视频", exact=True).click()
    page.wait_for_timeout(1400)
    page.locator(".react-flow__node-video").first.click()
    page.wait_for_timeout(600)

    m = page.evaluate("""() => {
      const panel = document.querySelector("[data-video-generation-panel]");
      const ta = panel && panel.querySelector("textarea");
      const sec = panel && panel.querySelector("section");
      const b = panel.getBoundingClientRect();
      return {
        scrollW: document.documentElement.scrollWidth,
        innerW: window.innerWidth,
        panelBottom: Math.round(b.bottom),
        sectionH: sec ? Math.round(sec.getBoundingClientRect().height) : 0,
        taH: ta ? Math.round(ta.getBoundingClientRect().height) : 0,
      };
    }""")
    check("mobile:no-page-overflow", m["scrollW"] <= m["innerW"])
    check("mobile:panel-height", m["sectionH"] == 397)
    check("mobile:prompt-intact", 88 <= m["taH"] <= 102)
    check("mobile:panel-in-viewport-v", 0 < m["panelBottom"] <= 844)
    result["measurements"] = m

    MOBILE_SCREENSHOT.parent.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(MOBILE_SCREENSHOT))
    check("mobile:screenshot", MOBILE_SCREENSHOT.exists())

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 161, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        mobile_page = browser.new_page(viewport={"width": 390, "height": 844})
        audit["results"].append(run_mobile(mobile_page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch161: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
