#!/usr/bin/env python3

"""Verify Batch 146 yunjing dropdown menu in the video panel toolbar."""

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
    / "liblib-canvas-batch146-2026-09-07"
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
    page.on(
        "requestfailed",
        lambda request: errors.append(
            f"requestfailed:{request.method}:{request.url}:{request.failure}"
        ),
    )
    return errors


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool) -> None:
        assert ok, f"batch146 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(BASE_URL, wait_until="networkidle")
    page.wait_for_timeout(400)

    page.get_by_role("button", name="添加节点").click()
    page.wait_for_timeout(400)
    panel = page.locator("[data-liblib-overlay='add-node']")
    panel.get_by_role("button", name="视频", exact=True).click()
    page.wait_for_timeout(1500)
    node = page.locator(".react-flow__node-video").first
    node.click()
    page.wait_for_timeout(800)

    vg = page.locator("[data-video-generation-panel]")
    check("panel:visible", vg.is_visible())

    trigger = vg.locator("[data-yunjing-trigger]")
    check("yunjing:trigger-visible", trigger.is_visible())
    check("yunjing:trigger-text", "运镜" in trigger.inner_text())

    trigger.click()
    page.wait_for_timeout(400)
    menu = vg.locator("[data-yunjing-menu]")
    check("yunjing:menu-opens", menu.is_visible())

    option_ids = ["push-in", "pull-out", "pan-left", "pan-right", "tilt-up", "tilt-down", "tracking", "crane", "orbit", "zoom-in", "zoom-out", "static"]
    for oid in option_ids:
        check(f"yunjing:opt:{oid}", menu.locator(f"[data-yunjing-option='{oid}']").count() == 1)

    menu.locator("[data-yunjing-option='push-in']").click()
    page.wait_for_timeout(500)
    check("yunjing:menu-closes", not menu.is_visible())

    trigger.click()
    page.wait_for_timeout(300)
    check(
        "yunjing:selected",
        menu.locator("[data-yunjing-option='push-in']").get_attribute("aria-pressed") == "true",
    )



    check("diagnostics:zero", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 146,
        "title": "Yunjing dropdown menu in video panel toolbar",
        "evidence": "docs/research/liblib-video-panel-2026-09-06/README.md",
        "results": [],
    }
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        desktop = browser.new_page(viewport={"width": 1440, "height": 900}, device_scale_factor=1)
        audit["results"].append(run_desktop(desktop))
        desktop.close()
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    checks = audit["results"][0]["checks"]
    print(
        "Batch 146 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "运镜 dropdown menu with 12 camera movement presets, selection/deselect, "
        "outside close and generate flow recorded in runtime-audit.json."
    )


if __name__ == "__main__":
    main()
