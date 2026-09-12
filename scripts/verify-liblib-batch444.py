#!/usr/bin/env python3
"""Verify Batch 444: VR-023 Slice D — local mixed-ratio output fixture.

Contract: docs/research/LIBTV_MEDIA_RENDITION_GEOMETRY_CONTRACT.md Slice D
("add stable output identities/per-output metadata in fixture scope;
exercise reflow/cover/contain/source-gated policies; keep real provider/
history integration out of scope").

Implementation:
- getLibTVNodeIntrinsicDimensions: per-output metadata (data.outputs +
  selectedOutputId) wins as the intrinsic authority;
- canvasStore.selectNodeOutput: selects a declared output and reflows the
  node frame from the newly selected intrinsic ratio (Slice B policy);
  rendition state only — no graph history entry; unknown node/output is a
  stable false NOOP.

Scenes (injected mixed-ratio node on empty canvas-1):
- output_selection_reflow: selecting the portrait output reflows the frame
  288x288 -> 162x288 and records selectedOutputId;
- unknown_output_noop: unknown output id is a stable false with zero
  mutation;
- history_untouched: no graph history entries across output switches.
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
    / "liblib-canvas-batch444-2026-09-13"
    / "runtime-audit.json"
)
SCREENSHOT_PATH = (
    ROOT
    / "docs"
    / "design-references"
    / "liblib-clone-batch444-output-reflow-929-2026-09-13.png"
)

SOURCE_NODE = {
    "id": "src-mixed-outputs",
    "type": "image",
    "position": {"x": 0, "y": 0},
    "width": 288,
    "height": 288,
    "style": {"width": 288, "height": 288},
    "data": {
        "filename": "mixed",
        "selectedOutputId": "out-square",
        "outputs": [
            {"outputId": "out-square", "width": 512, "height": 512},
            {"outputId": "out-portrait", "width": 720, "height": 1280},
            {"outputId": "out-wide", "width": 1920, "height": 1080},
        ],
    },
}


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


def node_state(page: Page, node_id: str):
    return page.evaluate(
        """(nodeId) => {
          const state = window.__libtv_store.getState();
          const canvas = state.canvases.find((c) => c.id === 'canvas-1');
          const node = canvas?.nodes.find((n) => n.id === nodeId);
          const history = state.historyByCanvas['canvas-1']
            || { past: [], future: [] };
          return node
            ? {
                width: node.width,
                height: node.height,
                selectedOutputId: node.data?.selectedOutputId ?? null,
                pastLength: history.past.length,
                futureLength: history.future.length,
              }
            : null;
        }""",
        node_id,
    )


def select_output(page: Page, node_id: str, output_id: str):
    return page.evaluate(
        """({nodeId, outputId}) =>
          window.__libtv_store.getState().selectNodeOutput(nodeId, outputId)
        """,
        {"nodeId": node_id, "outputId": output_id},
    )


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
        page.evaluate(
            """(node) => {
              window.__libtv_store.setState((state) => ({
                canvases: state.canvases.map((canvas) =>
                  canvas.id === 'canvas-1'
                    ? { ...canvas, nodes: [...canvas.nodes, node] }
                    : canvas,
                ),
              }));
            }""",
            SOURCE_NODE,
        )
        page.wait_for_timeout(200)

        node_id = SOURCE_NODE["id"]
        baseline = node_state(page, node_id)
        assert baseline and baseline["width"] == 288, baseline

        # reflow: select the portrait output (ratio 0.5625)
        result = select_output(page, node_id, "out-portrait")
        assert result is True, result
        after = node_state(page, node_id)
        assert after["width"] == 162 and after["height"] == 288, after
        assert after["selectedOutputId"] == "out-portrait", after

        # another switch keeps the reflow deterministic (wide output 16:9)
        result = select_output(page, node_id, "out-wide")
        assert result is True
        after_wide = node_state(page, node_id)
        assert after_wide["width"] == 512 and after_wide["height"] == 288, (
            after_wide
        )

        # unknown output: stable false NOOP
        result = select_output(page, node_id, "out-missing")
        assert result is False, result
        after_missing = node_state(page, node_id)
        assert after_missing == after_wide, (after_wide, after_missing)

        # rendition state: no graph history entries across all switches
        assert after_missing["pastLength"] == baseline["pastLength"] == 0
        assert after_missing["futureLength"] == 0

        conflicts = page.evaluate(
            """() =>
              window.__libtv_detect_dimension_conflicts('canvas-1').filter(
                (conflict) => conflict.nodeId === 'src-mixed-outputs',
              )
            """
        )
        assert not conflicts, conflicts

        page.evaluate(
            "() => window.__libtv_store.getState().setActiveCanvas('canvas-2')"
        )
        page.wait_for_timeout(320)
        page.screenshot(path=str(SCREENSHOT_PATH))
        assert_no_overflow(page)
        browser.close()
    assert not errors, errors

    audit = {
        "url": URL,
        "status": "SCRIPT_RECORDED_PASS",
        "slice": "VR-023 Slice D — mixed-ratio output fixture: per-output "
        "identities, selection reflow, no history integration",
        "scenes": {
            "output_selection_reflow": {
                "square": "288x288",
                "portrait": "162x288",
                "wide": "512x288",
                "selectedOutputIdRecorded": True,
            },
            "unknown_output_noop": {
                "returnedFalse": True,
                "zeroPartial": True,
            },
            "history_untouched": True,
            "detector_coherent": True,
        },
        "errors": {"console": [], "page": [], "request": []},
    }
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    print(
        "Batch 444 Playwright verification passed: per-output identity "
        "selection reflows the frame from the selected intrinsic ratio "
        "(288x288 -> 162x288 -> 512x288), unknown output is a stable false "
        "NOOP, no graph history entries, diagnostics clean."
    )


if __name__ == "__main__":
    main()
