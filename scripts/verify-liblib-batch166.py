#!/usr/bin/env python3

"""Verify Batch 166: prompt region visual + AutoLink chip removal.

Source evidence (2026-09-07 full-panel dumps):
- prompt region `generator-prompt-scroll-region` has no background/rounding;
  the clone's `rounded-xl bg-black/10` box is removed (plain textarea).
- toolbar shows only the five pills in both sampled states; the 「3 个匹配」
  AutoLink chip (trigger of the superseded advanced popup) is removed.
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
    / "liblib-canvas-batch166-2026-09-07"
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
        assert ok, f"batch166 check failed: {name}"
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

    vg = page.locator("[data-video-generation-panel]")
    ta = vg.locator("textarea").first
    style = ta.evaluate(
        """el => { const s = getComputedStyle(el);
        return {bg: s.backgroundColor, radius: s.borderTopLeftRadius}; }"""
    )
    check("prompt:transparent", style["bg"] in ("rgba(0, 0, 0, 0)", "transparent"))
    check("prompt:no-radius", style["radius"] == "0px")
    check("prompt:editable", ta.is_editable())

    check("toolbar:no-autolink-chip", vg.get_by_text("3 个匹配").count() == 0)
    # 工具行五个 pill 保留
    toolbar = vg.locator("[data-video-toolbar]")
    check("toolbar:pills-intact", toolbar.locator("button").count() >= 5)

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 166, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch166: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
