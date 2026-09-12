#!/usr/bin/env python3
"""Verify Batch 447: VR-022 Slice C — RECORD_EDITOR one-acceptance path
(idempotent subtitle-erase and picture-edit submissions).

Contract: docs/research/LIBTV_EDITOR_SESSION_COMMIT_HISTORY_CONTRACT.md
Slice C ("align Subtitle submit/idempotency with one acceptance path"),
§9.2 no-op (no duplicate output, no duplicate history).

Implementation (src/store/canvasStore.ts):
- createSubtitleErase / createPictureEdit return the named
  LibTVRecordEditorSubmitResult and fingerprint their request
  (mode + normalized records): an identical resubmit is a no-op
  returning the existing target — no duplicate node, no duplicate
  history; a different mode/records still creates a new target.

Scenes (injected video/image sources on empty canvas-1):
- subtitle_resubmit_noop: identical smart-mode submit twice -> second is
  a no-op with the same target id, one node/edge, one history entry;
- different_mode_accepts: region-mode submit creates a second target;
- picture_resubmit_noop: identical picture-edit marks submit twice ->
  second is a no-op with the same target id.
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
    / "liblib-canvas-batch447-2026-09-13"
    / "runtime-audit.json"
)
SCREENSHOT_PATH = (
    ROOT
    / "docs"
    / "design-references"
    / "liblib-clone-batch447-record-editor-idempotent-929-2026-09-13.png"
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
            """() => {
              window.__libtv_store.setState((state) => ({
                canvases: state.canvases.map((canvas) =>
                  canvas.id === 'canvas-1'
                    ? {
                        ...canvas,
                        nodes: [
                          ...canvas.nodes,
                          {
                            id: 'src-video-447',
                            type: 'video',
                            position: { x: 0, y: 0 },
                            width: 512,
                            height: 288,
                            style: { width: 512, height: 288 },
                            data: {
                              filename: '视频447',
                              durationSeconds: 30,
                              resolution: '1280 × 720',
                              posterUrl: '/images/scene-coffee-4.png',
                              status: 'ready',
                            },
                          },
                          {
                            id: 'src-image-447',
                            type: 'image',
                            position: { x: 0, y: 400 },
                            width: 288,
                            height: 288,
                            style: { width: 288, height: 288 },
                            data: {
                              filename: '图片447',
                              width: 512,
                              height: 512,
                            },
                          },
                        ],
                      }
                    : canvas,
                ),
              }));
            }"""
        )
        page.wait_for_timeout(200)

        submit_subtitle = page.evaluate(
            """() => {
              const state = window.__libtv_store.getState();
              const first = state.createSubtitleErase('src-video-447', 'smart', []);
              const second = state.createSubtitleErase('src-video-447', 'smart', []);
              return { first, second };
            }"""
        )
        assert submit_subtitle["first"]["status"] == "accepted", submit_subtitle
        assert submit_subtitle["second"] == {
            "status": "no-op",
            "targetId": submit_subtitle["first"]["targetId"],
        }, submit_subtitle

        after_subtitle = scene_state(page)
        assert after_subtitle["nodeCount"] == 3, after_subtitle  # 2 injected sources + 1 target
        assert after_subtitle["edgeCount"] == 1, after_subtitle
        assert after_subtitle["pastLength"] == 1, after_subtitle

        different = page.evaluate(
            """() =>
              window.__libtv_store.getState().createSubtitleErase(
                'src-video-447',
                'region',
                [
                  {
                    id: 'r1',
                    relX: 0.1,
                    relY: 0.1,
                    width: 0.3,
                    height: 0.2,
                  },
                ],
              )
            """
        )
        assert different["status"] == "accepted", different
        after_different = scene_state(page)
        assert after_different["nodeCount"] == 4, after_different  # +1 region-mode target
        assert after_different["pastLength"] == 2, after_different

        submit_picture = page.evaluate(
            """() => {
              const state = window.__libtv_store.getState();
              const mark = {
                id: 'm1',
                tool: 'box',
                frameSeconds: 1,
                relX: 0.2,
                relY: 0.2,
                width: 0.3,
                height: 0.3,
                candidate: '替换为天空',
              };
              const first = state.createPictureEdit(
                'src-image-447', 'subjectReplace', [mark],
              );
              const second = state.createPictureEdit(
                'src-image-447', 'subjectReplace',
                [{ ...mark, description: undefined }],
              );
              return { first, second };
            }"""
        )
        assert submit_picture["first"]["status"] == "accepted", submit_picture
        assert submit_picture["second"] == {
            "status": "no-op",
            "targetId": submit_picture["first"]["targetId"],
        }, submit_picture
        after_picture = scene_state(page)
        assert after_picture["nodeCount"] == 5, after_picture  # +1 picture-edit target
        assert after_picture["pastLength"] == 3, after_picture

        page.screenshot(path=str(SCREENSHOT_PATH))
        assert_no_overflow(page)
        browser.close()
    assert not errors, errors

    audit = {
        "url": URL,
        "status": "SCRIPT_RECORDED_PASS",
        "slice": "VR-022 Slice C — RECORD_EDITOR one-acceptance path "
        "(subtitle-erase / picture-edit idempotent submissions)",
        "subtitle_resubmit_noop": {
            "firstAccepted": True,
            "secondNoOpSameTarget": True,
            "singleNodeEdgeHistory": True,
        },
        "different_mode_accepts": True,
        "picture_resubmit_noop": {
            "firstAccepted": True,
            "secondNoOpSameTarget": True,
        },
        "errors": {"console": [], "page": [], "request": []},
    }
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    print(
        "Batch 447 Playwright verification passed: identical subtitle-erase "
        "and picture-edit resubmits are no-ops returning the existing "
        "target (one node/edge/history each), a different mode still "
        "creates, diagnostics clean."
    )


if __name__ == "__main__":
    main()
