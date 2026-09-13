#!/usr/bin/env python3
"""Verify Batch 470: VR-018 Slice D — duplicate export suppression.

Contract: docs/research/LIBTV_COMMAND_OUTCOME_FEEDBACK_CONTRACT.md
Slice D ("suppress stale/duplicate completion announcement").

Implementation (src/store/canvasStore.ts): createDirectorAnimationExport
resolves the same exportId to the existing node (no duplicate node/edge/
history); a missing source or empty video still returns null.

Scenes (empty canvas-1, injected source):
- export_accepted: first export creates one node/edge/history entry;
- export_duplicate_suppressed: re-exporting the same exportId returns
  the original node id with zero new node/edge/history;
- missing_source_stable_null: unknown source returns null.
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
    / "liblib-canvas-batch470-2026-09-14"
    / "runtime-audit.json"
)
SCREENSHOT_PATH = (
    ROOT
    / "docs"
    / "design-references"
    / "liblib-clone-batch470-export-suppression-929-2026-09-14.png"
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


def main():
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    SCREENSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)

    errors = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
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
            """() => {
              window.__libtv_store.setState((state) => ({
                canvases: state.canvases.map((canvas) =>
                  canvas.id === 'canvas-1'
                    ? {
                        ...canvas,
                        nodes: [
                          ...canvas.nodes,
                          {
                            id: 'dir-src-470',
                            type: 'video',
                            position: { x: 0, y: 0 },
                            width: 512,
                            height: 288,
                            style: { width: 512, height: 288 },
                            data: { filename: '导演源', status: 'ready' },
                          },
                        ],
                      }
                    : canvas,
                ),
              }));
            }"""
        )
        page.wait_for_timeout(200)

        scenes = page.evaluate(
            """() => {
              const state = window.__libtv_store.getState();
              const animation = {
                exportId: 'exp-470',
                sceneName: '场景一',
                cameraId: 'cam-1',
                cameraName: '机位一',
                aspectRatio: '16:9',
                width: 1280,
                height: 720,
                durationSeconds: 6,
                mimeType: 'video/webm',
                sizeBytes: 1024,
                createdAt: '2026-09-14T00:00:00Z',
                videoUrl: 'blob:fixture-470',
                posterDataUrl: 'data:image/png;base64,AAAA',
              };
              const first = state.createDirectorAnimationExport(
                'dir-src-470', animation,
              );
              const duplicate = state.createDirectorAnimationExport(
                'dir-src-470', animation,
              );
              const missing = state.createDirectorAnimationExport(
                'ghost-470', animation,
              );
              const fresh = window.__libtv_store.getState();
              const history = fresh.historyByCanvas['canvas-1']
                || { past: [], future: [] };
              const canvas = fresh.canvases.find((c) => c.id === 'canvas-1');
              return {
                first,
                duplicate,
                missing,
                nodeCount: (canvas?.nodes ?? []).length,
                edgeCount: (canvas?.edges ?? []).length,
                pastLength: history.past.length,
              };
            }"""
        )
        assert scenes["first"], "first export must create a node"
        assert scenes["duplicate"] == scenes["first"], (
            scenes,
            "duplicate exportId must resolve to the existing node",
        )
        assert scenes["missing"] is None
        assert scenes["nodeCount"] == 2, scenes  # source + one export
        assert scenes["edgeCount"] == 1, scenes
        assert scenes["pastLength"] == 1, scenes

        page.screenshot(path=str(SCREENSHOT_PATH))
        assert_no_overflow(page)
        browser.close()
    assert not errors, errors

    audit = {
        "url": URL,
        "status": "SCRIPT_RECORDED_PASS",
        "slice": "VR-018 Slice D — duplicate export suppression "
        "(stale/duplicate completion announcement suppressed)",
        "scenes": scenes,
        "errors": {"console": [], "page": [], "request": []},
    }
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    print(
        "Batch 470 Playwright verification passed: director export duplicate "
        "suppression returns the existing node for the same exportId (no "
        "duplicate node/edge/history), missing source is a stable null, "
        "diagnostics clean."
    )


if __name__ == "__main__":
    main()
