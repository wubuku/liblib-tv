#!/usr/bin/env python3
"""Verify Batch 575: per-axis keyframe diamond badges in the camera panel.

Contract: source-site sampling (screenshot 60) — the camera panel's
位置 X/Y/Z inputs show a teal diamond badge on axes that have a keyframe
at the current playhead time. In the clone the badges derive from the
camera's transform track (timeline.tracks) filtered to keyframes at the
current time; with autoKeyframe on and a transform committed, all three
position axes show badges.
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
    / "liblib-canvas-batch575-2026-09-29"
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
        assert ok, f"batch575 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/?batch70=1", wait_until="networkidle")
    page.wait_for_function(
        """() => Boolean(window.__libtv_store && window.__libtv_ui_store && window.__director_store)"""
    )
    # 抑制 1/5 引导气泡（避免遮挡面板交互；batch 36 先例）
    page.evaluate(
        "() => window.localStorage.setItem("
        "'director-timeline-coach-dismissed', '1')"
    )

    page.evaluate(
        """() => {
          const store = window.__libtv_store.getState();
          store.addNode("script-execution", { title: "Batch 575" });
          const node = store.getActiveCanvas().nodes.at(-1);
          window.__libtv_ui_store.getState().openDirectorDesk(node.id, store.activeCanvasId);
        }"""
    )
    page.locator("[data-director-workspace]").wait_for(state="visible")
    page.wait_for_timeout(600)

    # 新增机位（addDirectorCamera 同步创建变换轨道，t=0 创建关键帧覆盖
    # 三轴）并选中 → 三轴徽标立现
    camera_id = page.evaluate(
        """() => {
          const s = window.__director_store.getState();
          s.addDirectorCamera();
          return s.objects.filter((o) => o.kind === "camera").at(-1).id;
        }"""
    )
    check("camera:added", camera_id is not None)

    page.evaluate(
        """(cameraId) => window.__director_store.getState().selectObject(cameraId)""",
        camera_id,
    )
    page.wait_for_timeout(300)
    badges = page.locator("[data-director-keyframed-axis='position']")
    check("badge:three-initial", badges.count() == 3)

    # 经面板 UI 提交位置变换（onChange 走 recordObjectKeyframe）→ 徽标保持
    for axis, value in [("x", "4.2"), ("y", "2.2"), ("z", "9.5")]:
        page.locator(
            '[data-director-transform-field="position"]'
            f'[data-director-transform-axis="{axis}"]'
        ).fill(value)
        page.wait_for_timeout(120)
    page.wait_for_timeout(300)
    check("badge:three-after-commit", badges.count() == 3)

    check("diagnostics:zero", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 575,
        "title": "Per-axis keyframe diamond badges in the camera panel",
        "evidence": (
            "docs/research/liblib-source-exploration-2026-09-25/NOTES.md "
            "§16 + screenshot 60 (batch 574 sampling)"
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
        "Batch 575 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "per-axis keyframe badges appear after auto-keyframed transforms "
        "recorded in runtime-audit.json."
    )


if __name__ == "__main__":
    main()
