#!/usr/bin/env python3

"""Verify Batch 128 attempt chips drive settings linkage."""

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
    / "liblib-canvas-batch128-2026-09-06"
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
        assert ok, f"batch128 check failed: {name}"
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
    page.wait_for_timeout(800)

    vg = page.locator("[data-video-generation-panel]")
    settings = page.evaluate("""() => { const b = Array.from(document.querySelectorAll("[data-video-generation-panel] button")).find((x) => x.textContent.includes("· 720P")); return b ? b.textContent.trim() : null; }""")
    # Batch 143: 默认时长 6s→5s（源站对齐）。
    check("boot:default-settings", settings == "16:9 · 720P · 5s · 1个 ·")

    # Batch 159: 尝试列移至节点卡内（面板外），用页面级定位。
    attempts = page.locator("[data-video-attempts]")
    attempts.locator("[data-video-attempt='5分钟超长视频']").click()
    page.wait_for_timeout(300)
    settings = page.evaluate("""() => { const b = Array.from(document.querySelectorAll("[data-video-generation-panel] button")).find((x) => x.textContent.includes("· 720P")); return b ? b.textContent.trim() : null; }""")
    check("linkage:5min", settings == "Auto · 720P · 300s · 1个 ·")

    attempts.locator("[data-video-attempt='首尾帧生成视频']").click()
    page.wait_for_timeout(300)
    settings = page.evaluate("""() => { const b = Array.from(document.querySelectorAll("[data-video-generation-panel] button")).find((x) => x.textContent.includes("· 720P")); return b ? b.textContent.trim() : null; }""")
    check("linkage:shouwei", settings == "Auto · 720P · 5s · 1个 ·")

    # 取消选择：设置保持（CLONE_DECISION，源站未采样取消联动）
    attempts.locator("[data-video-attempt='首尾帧生成视频']").click()
    page.wait_for_timeout(300)
    check(
        "deselect:chip-off",
        attempts.locator("[data-video-attempt='首尾帧生成视频']").get_attribute("aria-pressed") == "false",
    )

    check("diagnostics:zero", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 128,
        "title": "Attempt chips drive settings linkage",
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
        "Batch 128 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "Attempt chips driving settings label (Auto/300s/5s) and deselect "
        "recorded in runtime-audit.json."
    )


if __name__ == "__main__":
    main()
