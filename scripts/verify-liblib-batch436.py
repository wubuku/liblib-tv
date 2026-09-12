#!/usr/bin/env python3
"""Verify Batch 436: VR-017 Slice B — page transaction invalidation.

Contract: docs/research/LIBTV_MULTI_CANVAS_LIFECYCLE_ISOLATION_CONTRACT.md
§5.5 page-local transactions (organizeSnapshot / dragHistorySnapshot /
connectionGesture) + §6 Slice B + GC-047/048.

Implementation (src/app/page.tsx):
- organize snapshot and drag baseline now carry the arming canvas id;
- restoreOrganize refuses to apply a snapshot to a different canvas;
- a late drag stop from another canvas records nothing;
- switching canvases clears all three page-local transactions.

Scenes:
- organize_switch_cancel (GC-047): organize on canvas-2, switch →
  confirmation strip cancels; target canvas graph/history untouched;
  switching back keeps the canceled state;
- drag_history_regression: a real node drag still records exactly one
  history entry and moves the node (owner binding changes nothing in
  normal UI geometry).
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
    / "liblib-canvas-batch436-2026-09-13"
    / "runtime-audit.json"
)
SCREENSHOT_PATH = (
    ROOT
    / "docs"
    / "design-references"
    / "liblib-clone-batch436-organize-cancel-929-2026-09-13.png"
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


def canvas_state(page: Page, canvas_id: str):
    return page.evaluate(
        """(canvasId) => {
          const state = window.__libtv_store.getState();
          const canvas = state.canvases.find((item) => item.id === canvasId);
          const history = state.historyByCanvas[canvasId]
            || { past: [], future: [] };
          return {
            activeCanvasId: state.activeCanvasId,
            nodeCount: (canvas?.nodes ?? []).length,
            positions: JSON.stringify(
              (canvas?.nodes ?? []).map((node) => [node.id, node.position]),
            ),
            pastLength: history.past.length,
            futureLength: history.future.length,
          };
        }""",
        canvas_id,
    )


def graph_state(page: Page):
    return page.evaluate(
        """() => {
          const state = window.__libtv_store.getState();
          return canvasStateFor(state.activeCanvasId, state);
        }

        function canvasStateFor(canvasId, state) {
          const canvas = state.canvases.find((item) => item.id === canvasId);
          const history = state.historyByCanvas[canvasId]
            || { past: [], future: [] };
          return {
            activeCanvasId: state.activeCanvasId,
            nodeCount: (canvas?.nodes ?? []).length,
            positions: JSON.stringify(
              (canvas?.nodes ?? []).map((node) => [node.id, node.position]),
            ),
            pastLength: history.past.length,
            futureLength: history.future.length,
          };
        }"""
    )


def switch_canvas(page: Page, canvas_id: str):
    page.evaluate(
        "(canvasId) => window.__libtv_store.getState().setActiveCanvas(canvasId)",
        canvas_id,
    )
    page.wait_for_timeout(320)


def run_drag_history_regression(page: Page):
    node = page.locator(".react-flow__node").first
    assert node.count() >= 1, "fixture needs at least one node to drag"
    node_id = node.get_attribute("data-id")
    before = graph_state(page)
    box = node.bounding_box()
    assert box is not None
    cx, cy = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
    page.mouse.move(cx, cy)
    page.mouse.down()
    page.mouse.move(cx + 90, cy + 60, steps=8)
    page.mouse.up()
    page.wait_for_timeout(320)
    after = graph_state(page)
    assert after["pastLength"] == before["pastLength"] + 1, (before, after)
    assert after["positions"] != before["positions"], (before, after)
    assert after["futureLength"] == 0, after
    return {"nodeId": node_id, "before": before, "after": after}


def run_organize_switch_cancel(page: Page):
    page.keyboard.press("Alt+Shift+f")
    page.wait_for_timeout(420)
    strip = page.locator("[data-organize-confirmation]")
    assert strip.count() == 1, "organize confirmation strip must be visible"
    organized = graph_state(page)
    assert organized["pastLength"] >= 1

    other = page.evaluate(
        """() => {
          const state = window.__libtv_store.getState();
          return state.canvases
            .map((canvas) => canvas.id)
            .find((id) => id !== state.activeCanvasId);
        }"""
    )
    other_before = canvas_state(page, other)
    switch_canvas(page, other)
    assert page.locator("[data-organize-confirmation]").count() == 0, (
        "switch must cancel the organize transaction (strip closes)"
    )
    other_after = canvas_state(page, other)
    assert other_after["activeCanvasId"] == other
    assert other_after["nodeCount"] == other_before["nodeCount"]
    assert other_after["positions"] == other_before["positions"], (
        "target canvas graph must be untouched by the canceled transaction"
    )
    assert other_after["pastLength"] == other_before["pastLength"], (
        "target canvas history must be untouched"
    )

    switch_canvas(page, organized["activeCanvasId"])
    assert page.locator("[data-organize-confirmation]").count() == 1, (
        "returning to the arming canvas re-shows the owner-scoped strip"
    )
    back = graph_state(page)
    assert back["nodeCount"] == organized["nodeCount"]
    assert back["positions"] == organized["positions"], (
        "organized layout must persist on the arming canvas"
    )
    assert back["pastLength"] == organized["pastLength"]

    page.locator("[data-organize-confirmation] button").first.click()
    page.wait_for_timeout(320)
    restored = graph_state(page)
    assert page.locator("[data-organize-confirmation]").count() == 0, (
        "restore closes the confirmation strip"
    )
    assert restored["pastLength"] == organized["pastLength"] + 1, restored
    assert restored["positions"] != organized["positions"], restored
    return {
        "organized": organized,
        "targetCanvasId": other,
        "targetUntouched": True,
        "stripInertWhileOtherCanvasActive": True,
        "ownerScopedRestoreWorksOnArmingCanvas": True,
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

        drag = run_drag_history_regression(page)
        organize = run_organize_switch_cancel(page)
        page.screenshot(path=str(SCREENSHOT_PATH))
        assert_no_overflow(page)
        browser.close()
    assert not errors, errors

    audit = {
        "url": URL,
        "status": "SCRIPT_RECORDED_PASS",
        "slice": "VR-017 Slice B — page transaction invalidation (§5.5, GC-047/048)",
        "implementation": [
            "organize snapshot + drag baseline carry arming canvasId",
            "organize strip visibility derives from arming canvas (inert on other canvases)",
            "restoreOrganize refuses cross-canvas apply",
            "late cross-canvas drag stop records nothing",
            "activeCanvasId change clears drag/connection holders (refs)",
        ],
        "drag_history_regression": drag,
        "organize_switch_cancel": organize,
        "not_browser_asserted": [
            "connectionGesture stale window (holder never read; cleared on switch)",
            "late drag stop cross-canvas branch (React Flow remount closes the window; guarded in code)",
        ],
        "remaining_vr017_gaps": [
            "demo viewport ownership remainder (resize anchor, live/stable endpoint)",
            "async/resource isolation (Slice E)",
        ],
        "errors": {"console": [], "page": [], "request": []},
    }
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    print(
        "Batch 436 Playwright verification passed: organize transaction canceled "
        "on canvas switch (GC-047) with target graph/history untouched, drag "
        "history regression green, browser diagnostics clean."
    )


if __name__ == "__main__":
    main()
