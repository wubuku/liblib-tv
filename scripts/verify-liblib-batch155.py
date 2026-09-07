#!/usr/bin/env python3

"""Verify Batch 155: 5分钟超长视频 chip switches the duration range to 30..300.

Before: chip set duration=300 while the params slider stayed 4..30 (broken
half-state: thumb clamped at 30, state value 300). After: params menu opens
in the long layout (range 30..300); deselecting the chip clamps duration
back to <=30 (CLONE_DECISION, source cancel linkage unsampled).
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
    / "liblib-canvas-batch155-2026-09-07"
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


def settings_label(page: Page) -> str | None:
    return page.evaluate(
        """() => { const b = Array.from(document.querySelectorAll("[data-video-generation-panel] button"))
        .find((x) => x.textContent.includes("· 720P")); return b ? b.textContent.trim() : null; }"""
    )


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool) -> None:
        assert ok, f"batch155 check failed: {name}"
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
    check("boot:default-settings", settings_label(page) == "16:9 · 720P · 5s · 1个 ·")

    # 点击 5分钟超长视频 → Auto/300s，随后参数菜单应处于长范围（30..300）。
    attempts = vg.locator("[data-video-attempts]")
    attempts.locator("[data-video-attempt='5分钟超长视频']").click()
    page.wait_for_timeout(300)
    check("chip:300s-label", settings_label(page) == "Auto · 720P · 300s · 1个 ·")

    page.locator("[data-video-params-trigger]").click()
    page.wait_for_timeout(300)
    menu = page.locator("[data-video-params-menu]")
    check("params:menu-open", menu.count() == 1)
    check("params:long-mode", menu.get_attribute("data-video-params-mode") == "long")
    slider = menu.locator("[data-video-duration]")
    check("params:max-300", slider.get_attribute("max") == "300")
    check("params:min-30", slider.get_attribute("min") == "30")
    check(
        "params:value-300",
        menu.locator("[data-video-duration-value]").inner_text().strip().startswith("300"),
    )
    # 关闭菜单（再次点击触发器）。
    page.locator("[data-video-params-trigger]").click()
    page.wait_for_timeout(200)

    # 取消芯片 → 时长回落 ≤30（标签恢复常规）。
    attempts.locator("[data-video-attempt='5分钟超长视频']").click()
    page.wait_for_timeout(300)
    label = settings_label(page) or ""
    seconds = int(label.split("·")[2].strip().replace("s", ""))
    check("deselect:clamp-30", seconds <= 30)
    check(
        "deselect:chip-off",
        attempts.locator("[data-video-attempt='5分钟超长视频']").get_attribute("aria-pressed") == "false",
    )

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 155, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch155: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
