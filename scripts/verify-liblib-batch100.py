#!/usr/bin/env python3

"""Verify Batch 100 empty-canvas state and quick-create chips."""

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
    / "liblib-canvas-batch100-2026-09-05"
    / "runtime-audit.json"
)

CHIPS = {
    "story-script": "故事脚本生成",
    "character-turnaround": "角色三视图",
    "reference-to-video": "全能参考生视频",
    "audio-to-video": "音频生视频",
}


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


def switch_canvas(page: Page, canvas_id: str) -> None:
    page.locator("[data-canvas-trigger]").click()
    page.locator(f"[data-canvas-row='{canvas_id}']").get_by_role("button").first.click()
    page.wait_for_timeout(300)


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool) -> None:
        assert ok, f"batch100 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(BASE_URL, wait_until="networkidle")
    page.wait_for_timeout(400)

    check("boot:demo-canvas-no-empty-state", page.locator("[data-canvas-empty-state]").count() == 0)
    demo_nodes = page.locator(".react-flow__node").count()
    check("boot:demo-has-nodes", demo_nodes > 0)

    switch_canvas(page, "canvas-1")
    empty_state = page.locator("[data-canvas-empty-state]")
    check("empty:visible", empty_state.is_visible())
    check("empty:hint", empty_state.get_by_text("双击画布", exact=True).is_visible())
    check("empty:hint-generate", empty_state.get_by_text("自由生成节点", exact=True).is_visible())
    check("empty:no-nodes", page.locator(".react-flow__node").count() == 0)
    for chip_id, label in CHIPS.items():
        chip = empty_state.locator(f"[data-canvas-empty-chip='{chip_id}']")
        check(f"chip:{chip_id}", chip.count() == 1 and label in chip.inner_text())
    check(
        "chip:video-badges",
        "SD 2.5" in empty_state.locator("[data-canvas-empty-chip='reference-to-video']").inner_text()
        and "SD 2.5" in empty_state.locator("[data-canvas-empty-chip='audio-to-video']").inner_text(),
    )

    empty_state.locator("[data-canvas-empty-chip='audio-to-video']").click()
    check("chip:local-status", "本地原型" in page.locator("[data-canvas-empty-status]").inner_text())
    check("chip:zero-graph-side-effect", page.locator(".react-flow__node").count() == 0)

    switch_canvas(page, "canvas-2")
    check("back:empty-state-hidden", page.locator("[data-canvas-empty-state]").count() == 0)
    check("back:graph-preserved", page.locator(".react-flow__node").count() == demo_nodes)
    check("back:status-unmounted", page.locator("[data-canvas-empty-status]").count() == 0)

    check("diagnostics:zero", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def run_mobile(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "390x844", "checks": []}
    errors = attach_errors(page)
    page.goto(BASE_URL, wait_until="networkidle")
    page.wait_for_timeout(400)
    page.locator("[data-canvas-trigger]").click()
    page.locator("[data-canvas-row='canvas-1']").get_by_role("button").first.click()
    page.wait_for_timeout(300)
    result["checks"].append("empty:visible")
    assert page.locator("[data-canvas-empty-state]").is_visible()
    result["checks"].append("mobile:no-horizontal-overflow")
    assert page.evaluate(
        "document.documentElement.scrollWidth <= document.documentElement.clientWidth"
    )
    result["checks"].append("diagnostics:zero")
    assert not errors, errors
    result["diagnostics"] = {"console": len(errors)}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 100,
        "title": "Empty-canvas state and quick-create chips",
        "evidence": "docs/research/liblib-live-2026-09-05/README.md",
        "results": [],
    }
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        desktop = browser.new_page(viewport={"width": 1440, "height": 900}, device_scale_factor=1)
        audit["results"].append(run_desktop(desktop))
        desktop.close()
        mobile = browser.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=1)
        audit["results"].append(run_mobile(mobile))
        mobile.close()
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(item["checks"]) for item in audit["results"])
    print(
        "Batch 100 verification passed: "
        f"{total} checks, 0 diagnostics. "
        "Empty-canvas hint/chips on canvas-1, local chip feedback, graph "
        "isolation across canvas switch and mobile overflow recorded in "
        "runtime-audit.json."
    )


if __name__ == "__main__":
    main()
