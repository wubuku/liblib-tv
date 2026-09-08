#!/usr/bin/env python3

"""Verify Batch 215: effect application relabels the 特效 pill to 替换.

Source evidence (source-yunjing-selected.json / screenshot): with an effect
material connected, the panel toolbar pill reads 替换 instead of 特效
(replace semantics), and a 取消选择 picker appears on the canvas. The clone
now relabels the pill via the effectApplied flag once an effect is applied.
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
    / "liblib-canvas-batch215-2026-09-09"
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
        assert ok, f"batch215 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto("http://localhost:4317", wait_until="networkidle")
    page.wait_for_timeout(500)

    # fresh video node
    page.get_by_role("button", name="添加节点").click()
    page.wait_for_timeout(300)
    page.locator("[data-liblib-overlay='add-node']").get_by_role("button", name="视频", exact=True).click()
    page.wait_for_timeout(1000)
    created = page.locator(".react-flow__node-video").last
    cb = created.bounding_box()
    sx, sy = cb["x"] + cb["width"] / 2, cb["y"] + 12
    page.mouse.move(sx, sy)
    page.mouse.down()
    page.mouse.move(sx - 180, sy - 200, steps=8)
    page.mouse.up()
    page.wait_for_timeout(400)

    panel = page.locator("[data-video-generation-panel]")
    pills = panel.locator("[data-video-toolbar] button")
    before = pills.all_inner_texts()
    check("toolbar:before-特效", any("特效" in t for t in before))

    # apply an effect via the gallery
    panel.locator("[data-effects-trigger]").click()
    page.wait_for_timeout(350)
    page.locator("[data-effects-card='试妆特写']").click()
    page.wait_for_timeout(400)

    after = pills.all_inner_texts()
    check("toolbar:after-替换", any("替换" in t for t in after))
    check("toolbar:no-特效-after", not any("特效" in t for t in after))

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 215, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch215: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
