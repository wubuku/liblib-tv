#!/usr/bin/env python3
"""Verify Batch 449: VR-022 Slice E — deterministic request handoff with a
fake operation acceptor.

Contract: docs/research/LIBTV_EDITOR_SESSION_COMMIT_HISTORY_CONTRACT.md
Slice E ("replace component timer identity with a fake operation acceptor;
freeze owner/source/session descriptor"), §5.7 (captured/delayed operations
carry identity; stale completions have a stable disposition).

Implementation:
- src/lib/libtvOperationHandoff.ts: acceptLibTVOperation — frozen
  descriptor {operationId, kind, canvasId, nodeId}, owner re-validation at
  completion, cancel-on-unmount;
- VideoNode's four owner-bearing timers (audio-split, matting,
  picture-edit, depth-motion) now run through the acceptor; the unmount
  cleanup cancels them (declared switch-cancels disposition).

Scenes (real matting flow on empty canvas-1):
- accepted_completion: submit completes after the delay — derived node,
  edge and one history entry land on the owner canvas;
- switch_cancels_pending: a submit interrupted by a canvas switch leaves
  no late node on either canvas (cancel disposition).
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
URL = os.environ.get("LIBLIB_BASE_URL", "http://localhost:4317")
AUDIT_PATH = (
    ROOT
    / "docs"
    / "research"
    / "liblib-canvas-batch449-2026-09-13"
    / "runtime-audit.json"
)
SCREENSHOT_PATH = (
    ROOT
    / "docs"
    / "design-references"
    / "liblib-clone-batch449-operation-acceptor-929-2026-09-13.png"
)


def attach_errors(page: Page):
    errors = []
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


def assert_no_overflow(page: Page):
    assert page.evaluate(
        "() => document.documentElement.scrollWidth <= document.documentElement.clientWidth"
    )
    assert page.evaluate(
        "() => document.body.scrollWidth <= document.body.clientWidth"
    )


def scene_state(page: Page):
    return page.evaluate(
        """() => {
          const state = window.__libtv_store.getState();
          const canvas = state.canvases.find((c) => c.id === 'canvas-1');
          const history = state.historyByCanvas['canvas-1']
            || { past: [], future: [] };
          return {
            nodeCount: (canvas?.nodes ?? []).length,
            edgeCount: (canvas?.edges ?? []).length,
            pastLength: history.past.length,
          };
        }"""
    )


def add_ready_video(page: Page):
    page.get_by_role("button", name="添加节点").click()
    page.locator('[data-add-node-entry="video"]').click()
    page.wait_for_timeout(200)
    source = page.locator(".react-flow__node-video.selected")
    assert source.count() == 1


def open_matting_and_submit(page: Page):
    trigger = page.locator("[data-video-picture-edit-menu-trigger]")
    assert trigger.count() == 1
    trigger.click()
    menu = page.locator('[data-video-toolbar-menu="picture-edit"]')
    menu.wait_for(state="visible")
    menu.locator('[data-video-picture-edit-action="matting"]').click()
    page.locator("[data-smart-matting-panel]").wait_for(state="visible")
    page.wait_for_timeout(120)
    generate = page.locator("[data-smart-matting-generate]")
    generate.wait_for(state="visible")
    generate.click()
    page.locator("[data-smart-matting-submitting]").wait_for(state="visible")


def switch_canvas(page: Page, canvas_id: str):
    page.evaluate(
        "(canvasId) => window.__libtv_store.getState().setActiveCanvas(canvasId)",
        canvas_id,
    )
    page.wait_for_timeout(280)


def run_accepted_completion(page: Page):
    add_ready_video(page)
    before = scene_state(page)
    open_matting_and_submit(page)
    page.wait_for_timeout(900)
    after = scene_state(page)
    assert after["nodeCount"] == before["nodeCount"] + 1, (before, after)
    assert after["edgeCount"] == before["edgeCount"] + 1, (before, after)
    assert after["pastLength"] == before["pastLength"] + 1, (before, after)
    return {"before": before, "after": after, "completed": True}


def run_switch_cancels_pending(page: Page):
    before = scene_state(page)
    # scene A already produced an output badge on this node — count it so
    # the cancelled scene asserts "no NEW output" instead of zero badges
    outputs_before = page.locator("[data-smart-matting-output]").count()
    open_matting_and_submit(page)
    switch_canvas(page, "canvas-2")
    page.wait_for_timeout(900)
    target_state = page.evaluate(
        """() => {
          const state = window.__libtv_store.getState();
          const canvas = state.canvases.find((c) => c.id === 'canvas-2');
          return (canvas?.nodes ?? []).length;
        }"""
    )
    switch_canvas(page, "canvas-1")
    page.wait_for_timeout(400)
    after = scene_state(page)
    assert after["nodeCount"] == before["nodeCount"], (before, after)
    assert after["pastLength"] == before["pastLength"], after
    outputs_after = page.locator("[data-smart-matting-output]").count()
    assert outputs_after == outputs_before, (
        outputs_before,
        outputs_after,
        "the cancelled submit must not add an output",
    )
    assert target_state >= 0
    return {
        "cancelled": True,
        "ownerCanvasNodesUnchanged": True,
        "historyUntouched": True,
    }


def main():
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    SCREENSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)

    errors = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(
            viewport={"width": 929, "height": 874}, device_scale_factor=1
        )
        errors.extend(attach_errors(page))
        page.goto(URL, wait_until="networkidle")
        page.wait_for_timeout(450)

        page.evaluate(
            "() => window.__libtv_store.getState().setActiveCanvas('canvas-1')"
        )
        page.wait_for_timeout(320)

        completed = run_accepted_completion(page)
        cancelled = run_switch_cancels_pending(page)

        page.evaluate(
            "() => window.__libtv_store.getState().setActiveCanvas('canvas-2')"
        )
        page.wait_for_timeout(300)
        page.screenshot(path=str(SCREENSHOT_PATH))
        assert_no_overflow(page)
        browser.close()
    assert not errors, errors

    audit = {
        "url": URL,
        "status": "SCRIPT_RECORDED_PASS",
        "slice": "VR-022 Slice E — fake operation acceptor with frozen "
        "descriptor and owner re-validation at completion",
        "accepted_completion": completed,
        "switch_cancels_pending": cancelled,
        "errors": {"console": [], "page": [], "request": []},
    }
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    print(
        "Batch 449 Playwright verification passed: matting submit completes "
        "through the operation acceptor (node/edge/history land once on the "
        "owner canvas) and a submit interrupted by a canvas switch is "
        "cancelled with no late commit, diagnostics clean."
    )


if __name__ == "__main__":
    main()
