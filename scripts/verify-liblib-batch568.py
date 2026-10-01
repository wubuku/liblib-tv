#!/usr/bin/env python3
"""Verify Batch 568: timeline current-time editable input.

Contract: source-site sampling (screenshots 48/55) — the timeline time
display is an editable bordered input (0.00) alongside a duration input
(10.00 s). In the clone the current-time is an input: typing a time and
pressing Enter seeks the timeline via setTimelineTime (clamped to
[0, duration]); the display resyncs on playback/seek. The duration stays
a read-only label.
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
    / "liblib-canvas-batch568-2026-09-27"
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
        assert ok, f"batch568 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/?batch70=1", wait_until="networkidle")
    page.wait_for_function(
        """() => Boolean(window.__libtv_store && window.__libtv_ui_store && window.__director_store)"""
    )

    page.evaluate(
        """() => {
          const store = window.__libtv_store.getState();
          store.addNode("script-execution", { title: "Batch 568" });
          const node = store.getActiveCanvas().nodes.at(-1);
          window.__libtv_ui_store.getState().openDirectorDesk(node.id, store.activeCanvasId);
        }"""
    )
    page.locator("[data-director-workspace]").wait_for(state="visible")
    page.wait_for_timeout(400)

    time_input = page.locator("[data-director-timeline-time]")
    check("time:input-visible", time_input.is_visible())
    duration_label = page.locator("[data-director-timeline-duration]")
    check("duration:label-visible", duration_label.is_visible())

    # 输入 3500 + Enter → seek to 3.5s
    # Batch 601: the toolbar now opens in the source's **ms** unit, so the
    # playhead box is read and written in integer milliseconds (3.5 is no
    # longer a valid entry there — it would mean 3.5ms). The seek itself is
    # unchanged, only the literal that expresses it.
    time_input.fill("3500")
    time_input.press("Enter")
    page.wait_for_timeout(250)
    check(
        "seek:store-time",
        page.evaluate(
            "window.__director_store.getState().timeline.currentTime"
        )
        == 3.5,
    )

    # 超界钳制（20000ms = 20s > 10s）
    time_input.fill("20000")
    time_input.press("Enter")
    page.wait_for_timeout(250)
    current = page.evaluate(
        "window.__director_store.getState().timeline.currentTime"
    )
    check("seek:clamped", 0 <= current <= 10)

    # 负值钳制
    time_input.fill("-4000")
    time_input.press("Enter")
    page.wait_for_timeout(250)
    check(
        "seek:negative-clamped",
        page.evaluate(
            "window.__director_store.getState().timeline.currentTime"
        ) == 0,
    )

    check("diagnostics:zero", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 568,
        "title": "Timeline current-time editable input",
        "evidence": (
            "docs/research/liblib-source-exploration-2026-09-25/NOTES.md "
            "§12/§13 + screenshots 48/55"
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
        "Batch 568 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "editable current-time input seeking via setTimelineTime with "
        "clamping recorded in runtime-audit.json."
    )


if __name__ == "__main__":
    main()
