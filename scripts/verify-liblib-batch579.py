#!/usr/bin/env python3
"""Verify Batch 579: keyframe diamond click seeks the playhead.

Contract: source-site CDP sampling (screenshot 63, batch 578) — clicking a
keyframe diamond selects the keyframe AND seeks the playhead to the
keyframe's time (playhead moved from 2s to the 0s keyframe, time input
synced to 0.00). In the clone the diamond click now also calls
setTimelineTime(keyframe.time) in addition to selecting the keyframe.
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
    / "liblib-canvas-batch579-2026-09-29"
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
        assert ok, f"batch579 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/?batch70=1", wait_until="networkidle")
    page.wait_for_function(
        """() => Boolean(window.__libtv_store && window.__libtv_ui_store && window.__director_store)"""
    )

    page.evaluate(
        """() => {
          const store = window.__libtv_store.getState();
          store.addNode("script-execution", { title: "Batch 579" });
          const node = store.getActiveCanvas().nodes.at(-1);
          window.__libtv_ui_store.getState().openDirectorDesk(node.id, store.activeCanvasId);
        }"""
    )
    page.locator("[data-director-workspace]").wait_for(state="visible")
    page.wait_for_timeout(400)

    # 播头移到 3s，选中角色轨道，添加一个关键帧（t=3）
    page.evaluate(
        "() => window.__director_store.getState().setTimelineTime(3)"
    )
    page.evaluate(
        """() => {
          const s = window.__director_store.getState();
          const character = s.objects.find((o) => o.kind === "character");
          if (character) s.selectObject(character.id);
        }"""
    )
    page.locator("[data-director-add-keyframe]").click()
    page.wait_for_timeout(300)
    diamond = page.locator("[data-director-keyframe-id]").first
    keyframe_time = float(
        diamond.get_attribute("data-director-keyframe-time") or "0"
    )
    check("diamond:visible", diamond.is_visible())

    # 播头移到 1s（离开关键帧时间）
    page.evaluate("() => window.__director_store.getState().setTimelineTime(1)")
    page.wait_for_timeout(200)
    check(
        "pre:playhead-off-keyframe",
        page.evaluate(
            "window.__director_store.getState().timeline.currentTime"
        ) == 1,
    )

    # 点击菱形 → 播头 seek 到关键帧时间 + 关键帧选中
    diamond.click()
    page.wait_for_timeout(300)
    check(
        "click:seek-to-keyframe",
        page.evaluate(
            "window.__director_store.getState().timeline.currentTime"
        ) == keyframe_time,
    )
    check(
        "click:keyframe-selected",
        page.evaluate(
            "window.__director_store.getState().timeline.selectedKeyframeId"
        )
        is not None,
    )

    check("diagnostics:zero", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 579,
        "title": "Keyframe diamond click seeks the playhead",
        "evidence": (
            "docs/research/liblib-source-exploration-2026-09-25/NOTES.md "
            "§12/§16 + screenshot 63-director-diamond-seek.png (batch 578)"
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
        "Batch 579 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "keyframe diamond click selects and seeks the playhead to the "
        "keyframe time recorded in runtime-audit.json."
    )


if __name__ == "__main__":
    main()
