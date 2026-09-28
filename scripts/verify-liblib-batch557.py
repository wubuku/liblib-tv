#!/usr/bin/env python3
"""Verify Batch 557: camera track row 绘制轨迹 affordance.

Contract: source-site sampling (screenshot 48-director-timeline-open.png)
— the source timeline's camera track row (主机位) shows a 「ⓘ绘制轨迹」
affordance on the right. In the clone, camera track rows without a bound
motion path render the affordance; clicking selects the track and opens
the same motion-path menu as the control-bar 创建运动轨迹 trigger.
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
    / "liblib-canvas-batch557-2026-09-27"
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
        assert ok, f"batch557 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/?batch70=1", wait_until="networkidle")
    page.wait_for_function(
        """() => Boolean(window.__libtv_store && window.__libtv_ui_store && window.__director_store)"""
    )

    page.evaluate(
        """() => {
          const store = window.__libtv_store.getState();
          store.addNode("script-execution", { title: "Batch 557" });
          const node = store.getActiveCanvas().nodes.at(-1);
          window.__libtv_ui_store.getState().openDirectorDesk(node.id, store.activeCanvasId);
        }"""
    )
    page.locator("[data-director-workspace]").wait_for(state="visible")
    page.wait_for_timeout(600)

    # 新增机位保证存在 camera 轨道；先跳过引导气泡（遮挡轨道行）
    page.evaluate("window.__director_store.getState().addDirectorCamera()")
    page.wait_for_timeout(400)
    skip_button = page.locator("[data-director-coachmark-skip]")
    if skip_button.count():
        skip_button.first.click()
        page.wait_for_timeout(200)

    camera_track = page.locator(
        "[data-director-track-draw-trail]"
    ).first
    check("affordance:visible", camera_track.is_visible())
    check("affordance:label", "绘制轨迹" in camera_track.inner_text())

    # 点击 → 选中该轨道并打开运动路径菜单
    camera_track.click()
    page.wait_for_timeout(300)
    menu = page.locator("[data-director-motion-path-menu], [data-director-path-menu]").first
    menu_visible = menu.count() > 0 and menu.is_visible()
    check("menu:opens", menu_visible)

    # ESC 关闭菜单
    if menu_visible:
        page.keyboard.press("Escape")
        page.wait_for_timeout(200)
    check("menu:closes", not menu.is_visible())

    check("diagnostics:zero", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 557,
        "title": "Camera track row 绘制轨迹 affordance",
        "evidence": (
            "docs/research/liblib-source-exploration-2026-09-25/NOTES.md "
            "§12 + screenshot 48-director-timeline-open.png (batch 552)"
        ),
        "results": [],
    }
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        desktop = browser.new_page(
            viewport={"width": 1440, "height": 900}, device_scale_factor=1
        )
        audit["results"].append(run_desktop(desktop))
        desktop.close()
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    checks = audit["results"][0]["checks"]
    print(
        "Batch 557 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "camera track row 绘制轨迹 affordance opening the motion-path menu "
        "recorded in runtime-audit.json."
    )


if __name__ == "__main__":
    main()
