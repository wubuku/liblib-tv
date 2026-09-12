#!/usr/bin/env python3
"""Verify Batch 446: VR-022 Slice B — equality-aware graph commit adapter.

Contract: docs/research/LIBTV_EDITOR_SESSION_COMMIT_HISTORY_CONTRACT.md
Slice B ("current owner/generation/fingerprint validation; named sync
command result; zero history for no-op/reject; one history for accepted
change"), §8.2 drift classes, §9 no-op.

Implementation:
- planLibTVEditorSessionCommit (pure planner, libtvEditorSession.ts);
- canvasStore.submitLibTVEditorSessionCommit (adapter: named result,
  exactly one history entry on accept, zero mutation otherwise);
- canvasGeneration: monotonic per-successful-switch epoch in the store.

Scenes (injected node on empty canvas-1):
- accepted: normalized draft commits with exactly one history entry;
- no-op: re-committing the same draft is zero history, zero mutation;
- conflict: scoped field drifted under the session -> stable conflict;
- stale: generation bump (switch away/back) rejects the old epoch and
  accepts a fresh one;
- invalid-owner: missing node is a stable rejection.
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
    / "liblib-canvas-batch446-2026-09-13"
    / "runtime-audit.json"
)
SCREENSHOT_PATH = (
    ROOT
    / "docs"
    / "design-references"
    / "liblib-clone-batch446-commit-adapter-929-2026-09-13.png"
)

SOURCE_NODE = {
    "id": "src-editor-commit",
    "type": "image",
    "position": {"x": 0, "y": 0},
    "width": 288,
    "height": 288,
    "style": {"width": 288, "height": 288},
    "data": {"filename": "mixed", "width": 512, "height": 512},
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


def commit(page: Page, request: dict):
    return page.evaluate(
        """(request) =>
          window.__libtv_store.getState().submitLibTVEditorSessionCommit(request)
        """,
        request,
    )


def scene_state(page: Page):
    return page.evaluate(
        """() => {
          const state = window.__libtv_store.getState();
          const canvas = state.canvases.find((c) => c.id === 'canvas-1');
          const node = canvas?.nodes.find(
            (n) => n.id === 'src-editor-commit',
          );
          const history = state.historyByCanvas['canvas-1']
            || { past: [], future: [] };
          return {
            generation: state.canvasGeneration,
            filename: node?.data?.filename ?? null,
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

        base = scene_state(page)
        gen = base["generation"]
        base_request = {
            "profileId": "INLINE_SCALAR",
            "nodeId": "src-editor-commit",
            "expectedCanvasId": "canvas-1",
            "expectedCanvasGeneration": gen,
            "field": "filename",
            "baselineValue": "mixed",
            "draftValue": "  renamed  ",
        }

        accepted = commit(page, base_request)
        after_accept = scene_state(page)
        assert accepted["status"] == "accepted" and accepted["historyPushed"]
        assert after_accept["filename"] == "renamed", after_accept
        assert after_accept["pastLength"] == base["pastLength"] + 1

        noop = commit(page, base_request)
        after_noop = scene_state(page)
        assert noop["status"] == "no-op" and not noop["historyPushed"]
        assert after_noop == after_accept, (after_accept, after_noop)

        page.evaluate(
            """() => {
              window.__libtv_store.setState((state) => ({
                canvases: state.canvases.map((canvas) =>
                  canvas.id === 'canvas-1'
                    ? {
                        ...canvas,
                        nodes: canvas.nodes.map((node) =>
                          node.id === 'src-editor-commit'
                            ? { ...node, data: { ...node.data, filename: '第三方' } }
                            : node,
                        ),
                      }
                    : canvas,
                ),
              }));
            }"""
        )
        conflict = commit(page, base_request)
        after_conflict = scene_state(page)
        assert conflict["status"] == "conflict"
        assert conflict["reason"] == "SCOPED_FIELD_DRIFTED"
        assert not conflict["historyPushed"]
        assert after_conflict["filename"] == "第三方"
        assert after_conflict["pastLength"] == after_noop["pastLength"]

        # switch away and back: the pre-switch epoch (gen) is now stale
        page.evaluate(
            "() => window.__libtv_store.getState().setActiveCanvas('canvas-2')"
        )
        page.wait_for_timeout(240)
        page.evaluate(
            "() => window.__libtv_store.getState().setActiveCanvas('canvas-1')"
        )
        page.wait_for_timeout(240)
        bumped = scene_state(page)
        assert bumped["generation"] >= gen + 2

        stale = commit(
            page,
            {
                **base_request,
                "baselineValue": "第三方",
                "draftValue": "新名称",
                "expectedCanvasGeneration": gen,
            },
        )
        assert stale["status"] == "stale", stale
        assert stale["reason"] == "GENERATION_CHANGED"
        fresh = commit(
            page,
            {
                "profileId": "INLINE_SCALAR",
                "nodeId": "src-editor-commit",
                "expectedCanvasId": "canvas-1",
                "expectedCanvasGeneration": bumped["generation"],
                "field": "filename",
                "baselineValue": "第三方",
                "draftValue": "新名称",
            },
        )
        after_fresh = scene_state(page)
        assert fresh["status"] == "accepted" and fresh["historyPushed"]
        assert after_fresh["filename"] == "新名称"
        assert after_fresh["pastLength"] == bumped["pastLength"] + 1

        ghost = commit(
            page,
            {
                "profileId": "INLINE_SCALAR",
                "nodeId": "ghost-node",
                "expectedCanvasId": "canvas-1",
                "expectedCanvasGeneration": bumped["generation"],
                "field": "filename",
                "baselineValue": "",
                "draftValue": "x",
            },
        )
        assert ghost["status"] == "invalid-owner"
        assert ghost["reason"] == "OWNER_MISSING"

        page.screenshot(path=str(SCREENSHOT_PATH))
        assert_no_overflow(page)
        browser.close()
    assert not errors, errors

    audit = {
        "url": URL,
        "status": "SCRIPT_RECORDED_PASS",
        "slice": "VR-022 Slice B — equality-aware graph commit adapter",
        "accepted": {"normalized": True, "oneHistoryEntry": True},
        "noOp": {"zeroHistory": True, "zeroMutation": True},
        "conflict": {
            "reason": "SCOPED_FIELD_DRIFTED",
            "draftPreservedNotOverwritten": True,
        },
        "stale": {
            "oldGenerationRejected": True,
            "freshGenerationAccepted": True,
        },
        "invalidOwner": {"reason": "OWNER_MISSING"},
        "errors": {"console": [], "page": [], "request": []},
    }
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    print(
        "Batch 446 Playwright verification passed: normalized accepted "
        "commit with exactly one history entry, re-commit is a zero-history "
        "no-op, scoped drift conflicts without overwriting the draft, "
        "generation bump rejects the stale epoch while a fresh one commits, "
        "missing owner is a stable rejection, diagnostics clean."
    )


if __name__ == "__main__":
    main()
