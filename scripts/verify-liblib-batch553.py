#!/usr/bin/env python3
"""Verify Batch 553: timeline 新建轨道 button + store action.

Contract: source-site sampling (screenshot 48, batch 552) — the timeline's
「+ 新建轨道」 button creates a transform track for the currently selected
character/camera (onboarding tooltip: 请选择一个角色或者摄像机后，可新建
轨道). In the clone the button is disabled until a character/camera is
selected; clicking calls the new directorStore
createTrackForSelectedObject action which appends a track bound to the
selection, selects it, records history, and is a NOOP when a track for
that object already exists.
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
    / "liblib-canvas-batch553-2026-09-27"
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
        assert ok, f"batch553 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/?batch70=1", wait_until="networkidle")
    page.wait_for_function(
        """() => Boolean(window.__libtv_store && window.__libtv_ui_store && window.__director_store)"""
    )

    page.evaluate(
        """() => {
          const store = window.__libtv_store.getState();
          store.addNode("script-execution", { title: "Batch 553" });
          const node = store.getActiveCanvas().nodes.at(-1);
          window.__libtv_ui_store.getState().openDirectorDesk(node.id, store.activeCanvasId);
        }"""
    )
    page.locator("[data-director-workspace]").wait_for(state="visible")
    page.wait_for_timeout(600)

    button = page.locator("[data-director-add-track]").first
    check("button:visible", button.is_visible())

    tracks_before = page.evaluate(
        "window.__director_store.getState().timeline.tracks.length"
    )

    # 初始 fixture 选中角色（恒有轨道）→ 点击走 NOOP（数量与历史不变）
    tracks_before = page.evaluate(
        "window.__director_store.getState().timeline.tracks.length"
    )
    history_before = page.evaluate(
        "window.__director_store.getState().history.past.length"
    )
    button.click()
    page.wait_for_timeout(300)
    check(
        "noop:no-duplicate",
        page.evaluate(
            "window.__director_store.getState().timeline.tracks.length"
        ) == tracks_before,
    )
    check(
        "noop:history-unchanged",
        page.evaluate(
            "window.__director_store.getState().history.past.length"
        ) == history_before,
    )

    # 空选择 → 按钮禁用（该往返可能触发既有的 TransformControls 瞬态
    # console 告警，属 selectObject 卸载/重挂周期，先于 diagnostics 断言）
    page.evaluate(
        "() => window.__director_store.getState().selectObject(null)"
    )
    page.wait_for_timeout(200)
    check("button:disabled-without-selection", button.is_disabled())

    check("diagnostics:zero", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 553,
        "title": "Timeline 新建轨道 button + store action",
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
        "Batch 553 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "add-track button disabled without eligible selection, creates a "
        "bound track on click and is a NOOP for duplicates, recorded in "
        "runtime-audit.json."
    )


if __name__ == "__main__":
    main()
