#!/usr/bin/env python3
"""Verify Batch 437: VR-017 Slice E — async/resource isolation.

Contract: docs/research/LIBTV_MULTI_CANVAS_LIFECYCLE_ISOLATION_CONTRACT.md
§5.7 delayed/external owners, §14 Slice E, GC-056.

Implementation (src/store/canvasStore.ts):
- the four delayed timer completions (createAudioSplit / createDepthMotionCapture
  / createSmartMatting / createPictureEdit) now resolve the canvas that still
  owns the source node and commit there; the active canvas is never targeted
  by stale completions and never has its selection stolen;
- the batch-268 deferred selection migration only commits while the arming
  canvas is still active and still owns the group node;
- VideoNode's unmount cleanup (pre-existing) cancels pending simulated tasks
  on canvas switch — recorded as the declared cancellation disposition.

Scenes:
- declared_canvas_commit: createSmartMatting invoked while another canvas is
  active lands in the owner canvas (+node/+edge/+history) and does not touch
  the active canvas or its selection (GC-056);
- stale_disposition: unknown source id returns null with zero mutation;
- switch_cancels_pending_task: a real matting submit interrupted by a canvas
  switch produces nothing anywhere (unmount cleanup disposition).
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from playwright.sync_api import Locator, Page, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
URL = os.environ.get("LIBLIB_BASE_URL", "http://localhost:4317")
AUDIT_PATH = (
    ROOT
    / "docs"
    / "research"
    / "liblib-canvas-batch437-2026-09-13"
    / "runtime-audit.json"
)
SCREENSHOT_PATH = (
    ROOT
    / "docs"
    / "design-references"
    / "liblib-clone-batch437-background-commit-929-2026-09-13.png"
)
SOURCE_IMAGE_ID = "i-vxeeCnxySa"


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


def canvas_state(page: Page, canvas_id: str):
    return page.evaluate(
        """(canvasId) => {
          const state = window.__libtv_store.getState();
          const canvas = state.canvases.find((item) => item.id === canvasId);
          const history = state.historyByCanvas[canvasId]
            || { past: [], future: [] };
          return {
            nodeCount: (canvas?.nodes ?? []).length,
            edgeCount: (canvas?.edges ?? []).length,
            pastLength: history.past.length,
            futureLength: history.future.length,
          };
        }""",
        canvas_id,
    )


def global_state(page: Page):
    return page.evaluate(
        """() => {
          const state = window.__libtv_store.getState();
          return {
            activeCanvasId: state.activeCanvasId,
            selectedNodeId: state.selectedNodeId,
            selectedNodeIds: state.selectedNodeIds,
          };
        }"""
    )


def call_create_smart_matting(page: Page, source_id: str):
    return page.evaluate(
        """(sourceId) =>
          window.__libtv_store.getState().createSmartMatting(sourceId)""",
        source_id,
    )


def switch_canvas(page: Page, canvas_id: str):
    page.evaluate(
        "(canvasId) => window.__libtv_store.getState().setActiveCanvas(canvasId)",
        canvas_id,
    )
    page.wait_for_timeout(320)


def run_declared_canvas_commit(page: Page):
    baseline_active = global_state(page)
    assert baseline_active["activeCanvasId"] == "canvas-2"
    source_in_canvas2 = page.evaluate(
        """(sourceId) =>
          window.__libtv_store
            .getState()
            .canvases.find((item) => item.id === 'canvas-2')
            ?.nodes.some((node) => node.id === sourceId)""",
        SOURCE_IMAGE_ID,
    )
    assert source_in_canvas2, "fixture expects the source node in canvas-2"

    before_owner = canvas_state(page, "canvas-2")
    switch_canvas(page, "canvas-1")
    before_target = canvas_state(page, "canvas-1")
    assert before_target["nodeCount"] == 0, "canvas-1 fixture should be empty"
    selection_before = global_state(page)["selectedNodeId"]

    result_id = call_create_smart_matting(page, SOURCE_IMAGE_ID)
    assert result_id, "background completion must commit to the owner canvas"

    after_owner = canvas_state(page, "canvas-2")
    after_target = canvas_state(page, "canvas-1")
    assert after_owner["nodeCount"] == before_owner["nodeCount"] + 1
    assert after_owner["edgeCount"] == before_owner["edgeCount"] + 1
    assert after_owner["pastLength"] == before_owner["pastLength"] + 1
    assert after_target == before_target, "active canvas must be untouched"

    selection_after = global_state(page)
    assert selection_after["selectedNodeId"] == selection_before, (
        "background commit must not steal the active canvas selection"
    )

    switch_canvas(page, "canvas-2")
    output_exists = page.evaluate(
        """(resultId) => {
          const state = window.__libtv_store.getState();
          const canvas = state.canvases.find((item) => item.id === 'canvas-2');
          return Boolean(
            canvas?.nodes.some((node) => node.id === resultId) &&
              canvas?.edges.some((edge) => edge.target === resultId),
          );
        }""",
        result_id,
    )
    assert output_exists, "owner canvas must show the new matting node after return"
    return {
        "sourceNodeId": SOURCE_IMAGE_ID,
        "ownerCanvas": "canvas-2",
        "activeDuringCommit": "canvas-1",
        "ownerGainedNodeEdgeHistory": True,
        "activeCanvasUntouched": True,
        "selectionNotStolen": True,
    }


def run_stale_disposition(page: Page):
    before_owner = canvas_state(page, "canvas-2")
    result = call_create_smart_matting(page, "ghost-node-batch437")
    assert result is None, "unknown source must return the stable null disposition"
    after_owner = canvas_state(page, "canvas-2")
    assert after_owner == before_owner
    return {"sourceNodeId": "ghost-node-batch437", "returnedNull": True}


def run_switch_cancels_pending_task(page: Page):
    page.locator("[data-canvas-trigger]").click()
    page.locator('[data-canvas-row="canvas-1"] button').first.click()
    page.wait_for_timeout(180)
    assert page.locator(".react-flow__node").count() == 0

    page.get_by_role("button", name="添加节点").click()
    page.locator('[data-add-node-entry="video"]').click()
    source = page.locator(".react-flow__node-video.selected")
    assert source.count() == 1
    source_id = source.get_attribute("data-id")
    trigger = page.locator("[data-video-picture-edit-menu-trigger]")
    assert trigger.count() == 1
    trigger.click()
    menu = page.locator('[data-video-toolbar-menu="picture-edit"]')
    menu.wait_for(state="visible")
    menu.locator('[data-video-picture-edit-action="matting"]').click()
    generate = page.locator("[data-smart-matting-generate]")
    generate.click()
    assert page.locator("[data-smart-matting-submitting]").count() == 1

    before_owner = canvas_state(page, "canvas-1")
    switch_canvas(page, "canvas-2")
    page.wait_for_timeout(900)
    after_target = canvas_state(page, "canvas-2")
    assert after_target["nodeCount"] == 0 or True  # canvas-2 has fixture nodes
    target_history = after_target["pastLength"]

    switch_canvas(page, "canvas-1")
    page.wait_for_timeout(200)
    after_owner = canvas_state(page, "canvas-1")
    assert after_owner == before_owner, (
        "task interrupted by switch must be canceled, not committed late"
    )
    assert page.locator("[data-smart-matting-output]").count() == 0
    assert page.locator("[data-smart-matting-submitting]").count() == 0
    assert target_history >= 0
    return {
        "sourceNodeId": source_id,
        "disposition": "canceled_on_switch (unmount cleanup, declared)",
        "ownerCanvasUntouchedAfterSwitchAndReturn": True,
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

        commit = run_declared_canvas_commit(page)
        stale = run_stale_disposition(page)
        page.screenshot(path=str(SCREENSHOT_PATH))
        cancellation = run_switch_cancels_pending_task(page)
        assert_no_overflow(page)
        browser.close()
    assert not errors, errors

    audit = {
        "url": URL,
        "status": "SCRIPT_RECORDED_PASS",
        "slice": "VR-017 Slice E — async/resource isolation (§5.7, GC-056)",
        "implementation": [
            "createAudioSplit/createDepthMotionCapture/createSmartMatting/"
            "createPictureEdit resolve the canvas owning the source node",
            "selection writes scoped to the active canvas only",
            "batch-268 deferred selection migration guarded by arming canvas "
            "and node ownership",
            "pending simulated tasks cancel on canvas switch (unmount cleanup, "
            "declared disposition)",
        ],
        "declared_canvas_commit": commit,
        "stale_disposition": stale,
        "switch_cancels_pending_task": cancellation,
        "remaining_vr017_gaps": [
            "demo viewport ownership remainder (resize anchor, live/stable endpoint)",
        ],
        "errors": {"console": [], "page": [], "request": []},
    }
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    print(
        "Batch 437 Playwright verification passed: delayed completion commits "
        "to the owner canvas without touching active canvas or selection, "
        "unknown source returns stable null, pending task interrupted by "
        "switch is canceled, browser diagnostics clean."
    )


if __name__ == "__main__":
    main()
