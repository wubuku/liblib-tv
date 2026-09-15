#!/usr/bin/env python3
"""Verify Batch 523/527: GRAPH-DELETE canvas scene — canvas deletion with
recycle-bin snapshot, history cleanup and restore, driven through the real
store actions.

Contract: docs/research/LIBTV_GRAPH_DELETE_REFERENCE_REPAIR_MATRIX.md §14
(LIBTV-FIX-LOCAL-GRAPH-DELETE-01 canvas scene) + batch 114 (adjacent
fallback) + batch 124/136 (soft-delete recycle bin / restore).

Scenes:
- delete_canvas_cleanup: deleting a non-active canvas removes it from the
  registry, snapshots it into removedCanvases (with removedAt), and cleans
  its historyByCanvas entry;
- delete_active_fallback: deleting the active canvas falls back to the
  adjacent canvas and clears the selection;
- restore_recovers_graph: restoreCanvas puts the canvas back with its
  graph intact.
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
    / "liblib-canvas-batch527-2026-09-14"
    / "runtime-audit.json"
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


def main():
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)

    errors = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(
            viewport={"width": 929, "height": 874}, device_scale_factor=1
        )
        errors.extend(attach_errors(page))
        page.goto(URL, wait_until="networkidle")
        page.wait_for_timeout(500)

        scenes = page.evaluate(
            """() => {
              const s = window.__libtv_store.getState();
              const out = {};
              // Prepare: a dedicated victim canvas with a node + history.
              const beforeCount = s.canvases.length;
              s.addCanvas();
              let st = window.__libtv_store.getState();
              const victim = st.canvases[st.canvases.length - 1];
              st.setActiveCanvas(victim.id);
              st = window.__libtv_store.getState();
              st.addNode('text', { content: '画布删除场景' });
              st = window.__libtv_store.getState();
              const victimHadHistory = Boolean(
                st.historyByCanvas[victim.id]?.past?.length,
              );
              // Scene 1: delete the non-active victim from the registry.
              st.setActiveCanvas('demo');
              st = window.__libtv_store.getState();
              const removedBefore = st.removedCanvases.length;
              st.removeCanvas(victim.id);
              st = window.__libtv_store.getState();
              out.delete_canvas_cleanup = {
                registryDropped: !st.canvases.some((c) => c.id === victim.id),
                recycleSnapshot: st.removedCanvases.length === removedBefore + 1
                  && Boolean(st.removedCanvases.at(-1).removedAt),
                historyCleaned: !(victim.id in st.historyByCanvas),
                victimHadHistory,
                countRestored: st.canvases.length === beforeCount,
              };
              // Scene 2: delete the ACTIVE canvas — adjacent fallback and
              // selection clear.
              st.setActiveCanvas(victim.id);
              st = window.__libtv_store.getState();
              st.addNode('text', { content: '活动画布场景' });
              st.selectElements({
                nodeIds: st.getActiveCanvas().nodes.map((n) => n.id),
                edgeIds: [],
              });
              st = window.__libtv_store.getState();
              const activeBefore = st.activeCanvasId;
              st.removeCanvas(activeBefore);
              st = window.__libtv_store.getState();
              out.delete_active_fallback = {
                activeChanged: st.activeCanvasId !== activeBefore,
                activeExists: st.canvases.some((c) => c.id === st.activeCanvasId),
                selectionCleared: (st.getSelectionSnapshot().nodeIds ?? []).length === 0,
              };
              // Scene 3: recycle-bin restore recovers the graph.
              const restoredId = st.removedCanvases.at(-1).id;
              st.restoreCanvas(restoredId);
              st = window.__libtv_store.getState();
              const restoredCanvas = st.canvases.find((c) => c.id === restoredId);
              out.restore_recovers_graph = {
                backInRegistry: Boolean(restoredCanvas),
                graphIntact: (restoredCanvas?.nodes ?? []).some(
                  (n) => n.data?.content === '活动画布场景',
                ),
                removedShrunk: st.removedCanvases.every(
                  (c) => c.id !== restoredId,
                ),
              };
              return out;
            }"""
        )

        s1 = scenes["delete_canvas_cleanup"]
        assert all(s1.values()), s1
        s2 = scenes["delete_active_fallback"]
        assert all(s2.values()), s2
        s3 = scenes["restore_recovers_graph"]
        assert all(s3.values()), s3

        browser.close()
    assert not errors, errors

    audit = {
        "url": URL,
        "status": "FOCUSED_BROWSER_RECORDED_PASS",
        "slice": "GRAPH-DELETE canvas scene — soft-delete recycle snapshot, "
        "history cleanup, adjacent fallback with selection clear, restore "
        "recovers graph",
        "scenes": scenes,
        "errors": {"console": [], "page": [], "request": []},
    }
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    print(
        "Batch 527 verification passed: canvas deletion scenes green "
        "(cleanup snapshot, history cleaned, active fallback + selection "
        "clear, restore recovers graph); recorded in runtime-audit.json."
    )


if __name__ == "__main__":
    main()
