#!/usr/bin/env python3
"""Verify Batch 435: VR-017 INVALID_TARGET slice — setActiveCanvas unknown
target is a zero-partial NOOP.

Contract: docs/research/LIBTV_MULTI_CANVAS_LIFECYCLE_ISOLATION_CONTRACT.md
§11.2 scene 9 (INVALID_TARGET) + §12 "unknown target guarded" and the pure
planner row (switch: unknown → noop, zero-partial behavior).

Source evidence: none required (clone-only correctness slice); before this
batch setActiveCanvas wrote any id unguarded (canvasStore.ts), poisoning
every downstream active-canvas consumer (routeReactFlowChanges, history,
viewport restore all resolve the active canvas by id).

Scenes:
- invalid_target_noop: bogus id (and empty string) keeps activeCanvasId,
  selection, canvases and histories byte-identical (zero-partial);
- valid_switch_baseline: real target switches, selection clears;
- switch_back_restore: returning canvas keeps graphs/histories intact.
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
    / "liblib-canvas-batch435-2026-09-13"
    / "runtime-audit.json"
)
SCREENSHOT_PATH = (
    ROOT
    / "docs"
    / "design-references"
    / "liblib-clone-batch435-invalid-target-guard-929-2026-09-13.png"
)
INVALID_TARGETS = ["canvas-invalid-target-batch435", ""]


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


def snapshot(page: Page):
    return page.evaluate(
        """() => {
          const state = window.__libtv_store.getState();
          return {
            activeCanvasId: state.activeCanvasId,
            activeResolves: Boolean(state.getActiveCanvas()),
            selectedNodeIds: state.selectedNodeIds,
            selectedNodeId: state.selectedNodeId,
            selectedEdgeIds: state.selectedEdgeIds,
            canvases: JSON.stringify(
              state.canvases.map((canvas) => ({
                id: canvas.id,
                name: canvas.name,
                nodes: canvas.nodes.map((node) => node.id),
                edges: canvas.edges.map((edge) => edge.id),
              })),
            ),
            histories: JSON.stringify(
              Object.fromEntries(
                Object.entries(state.historyByCanvas).map(([id, history]) => [
                  id,
                  { past: history.past.length, future: history.future.length },
                ]),
              ),
            ),
            canvasIds: state.canvases.map((canvas) => canvas.id),
          };
        }"""
    )


def call_set_active(page: Page, canvas_id: str):
    return page.evaluate(
        """(canvasId) => {
          window.__libtv_store.getState().setActiveCanvas(canvasId);
          const state = window.__libtv_store.getState();
          return {
            activeCanvasId: state.activeCanvasId,
            activeResolves: Boolean(state.getActiveCanvas()),
          };
        }""",
        canvas_id,
    )


def run_invalid_target_noop(page: Page):
    baseline = snapshot(page)
    assert baseline["activeResolves"], "active canvas must resolve at start"
    assert len(baseline["canvasIds"]) >= 2, "fixture needs at least two canvases"
    first_node = page.evaluate(
        """() => {
          const state = window.__libtv_store.getState();
          const canvas = state.getActiveCanvas();
          state.selectNode(canvas.nodes[0].id);
          return canvas.nodes[0].id;
        }"""
    )
    selected = snapshot(page)
    assert selected["selectedNodeId"] == first_node
    assert selected["selectedNodeIds"] == [first_node]

    results = []
    for target in INVALID_TARGETS:
        outcome = call_set_active(page, target)
        after = snapshot(page)
        assert outcome["activeCanvasId"] == baseline["activeCanvasId"], (
            target,
            outcome,
        )
        assert outcome["activeResolves"], (target, outcome)
        assert after["selectedNodeIds"] == [first_node], (target, after)
        assert after["selectedNodeId"] == first_node, (target, after)
        assert after["canvases"] == baseline["canvases"], (target, after)
        assert after["histories"] == baseline["histories"], (target, after)
        results.append(
            {
                "target": target or "<empty-string>",
                "activeCanvasIdUnchanged": True,
                "selectionPreserved": True,
                "zeroPartial": True,
            }
        )
    return {"baseline": baseline, "probes": results}


def run_valid_switch(page: Page, baseline_active: str):
    other = page.evaluate(
        """() => {
          const state = window.__libtv_store.getState();
          return state.canvases
            .map((canvas) => canvas.id)
            .find((id) => id !== state.activeCanvasId);
        }"""
    )
    outcome = call_set_active(page, other)
    after = snapshot(page)
    assert outcome["activeCanvasId"] == other, (other, outcome)
    assert outcome["activeResolves"], (other, outcome)
    assert after["selectedNodeIds"] == [], (other, after)
    assert after["selectedNodeId"] is None, (other, after)
    return {"switchedTo": other, "selectionCleared": True}


def run_switch_back(page: Page, baseline_active: str):
    outcome = call_set_active(page, baseline_active)
    after = snapshot(page)
    assert outcome["activeCanvasId"] == baseline_active, outcome
    assert outcome["activeResolves"], outcome
    assert after["selectedNodeIds"] == [], outcome
    return {"restoredTo": baseline_active, "activeResolves": True}


def main():
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REFERENCE_DIR = SCREENSHOT_PATH.parent
    REFERENCE_DIR.mkdir(parents=True, exist_ok=True)

    errors = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(
            viewport={"width": 929, "height": 874}, device_scale_factor=1
        )
        errors.extend(attach_errors(page))
        page.goto(URL, wait_until="networkidle")
        page.wait_for_timeout(450)

        invalid = run_invalid_target_noop(page)
        baseline_active = invalid["baseline"]["activeCanvasId"]
        switched = run_valid_switch(page, baseline_active)
        restored = run_switch_back(page, baseline_active)
        final = snapshot(page)
        assert final["canvases"] == invalid["baseline"]["canvases"]
        assert final["histories"] == invalid["baseline"]["histories"]
        assert final["activeCanvasId"] == baseline_active

        page.screenshot(path=str(SCREENSHOT_PATH))
        assert_no_overflow(page)
        browser.close()
    assert not errors, errors

    audit = {
        "url": URL,
        "status": "SCRIPT_RECORDED_PASS",
        "slice": "VR-017 INVALID_TARGET — setActiveCanvas unknown target zero-partial NOOP",
        "contract": "docs/research/LIBTV_MULTI_CANVAS_LIFECYCLE_ISOLATION_CONTRACT.md §11.2 scene 9 / §12",
        "invalid_target_noop": invalid,
        "valid_switch": switched,
        "switch_back": restored,
        "remaining_vr017_gaps": [
            "demo viewport ownership",
            "page transaction generation",
            "late callback",
            "async/resource isolation",
        ],
        "errors": {"console": [], "page": [], "request": []},
    }
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    print(
        "Batch 435 Playwright verification passed: setActiveCanvas unknown/empty "
        "target is a zero-partial NOOP (active id, selection, canvases and "
        "histories untouched), valid switch/restore semantics unchanged, "
        "browser diagnostics clean."
    )


if __name__ == "__main__":
    main()
