#!/usr/bin/env python3
"""Verify Batch 517: GRAPH-DELETE focused fixture — structural closure,
selection invalidation, zero-partial undo, driven through the real store
remove actions.

Contract: docs/research/LIBTV_GRAPH_DELETE_REFERENCE_REPAIR_MATRIX.md §14
(LIBTV-FIX-LOCAL-GRAPH-DELETE-01). Focused scope: plain node deletion with
edge closure, selected-endpoint edge removal, selection invalidation and
zero-partial undo/redo. Derived/shot/process aggregate repair scenes and
canvas-scoped deletion stay open (recorded in FIXTURE_CATALOG).

Scenes:
- plain_delete_closure: deleting a node removes it and its connected
  edges, one history step;
- selection_invalidated: deleting a selected node clears the selection;
- undo_redo_zero_partial: undo restores the node AND its edges; redo
  removes them again (no half-restored state).
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
    / "liblib-canvas-batch517-2026-09-14"
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


def graph_state(page: Page):
    return page.evaluate(
        """() => {
          const s = window.__libtv_store.getState();
          const canvas = s.getActiveCanvas();
          const history = s.historyByCanvas[canvas.id] ?? { past: [], future: [] };
          const selection = s.getSelectionSnapshot();
          return {
            nodeIds: canvas.nodes.map((n) => n.id),
            edges: canvas.edges.map((e) => ({ id: e.id, source: e.source, target: e.target })),
            past: history.past.length,
            future: history.future.length,
            selection: selection.nodeIds ?? [],
          };
        }"""
    )


def add_text_node(page: Page, content: str):
    page.evaluate(
        """(content) => {
          const s = window.__libtv_store.getState();
          s.addNode('text', { content });
        }""",
        content,
    )
    page.wait_for_timeout(200)


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

        # Build: source -> target edge between two text nodes.
        add_text_node(page, "删除源")
        add_text_node(page, "删除目标")
        ids = graph_state(page)["nodeIds"]
        source_id, target_id = ids[-2], ids[-1]
        edge_added = page.evaluate(
            """(input) => {
              const s = window.__libtv_store.getState();
              const result = s.addEdge({
                id: `e-${input.source}-${input.target}-${Date.now()}`,
                source: input.source,
                target: input.target,
                sourceHandle: 'source',
                targetHandle: 'target',
                type: 'default',
              });
              return result && result.status;
            }""",
            {"source": source_id, "target": target_id},
        )
        assert edge_added == "allow", edge_added
        page.wait_for_timeout(200)

        # Scene 1 + 2: select the target node (node + its edge selected),
        # delete it via the real selection action.
        page.evaluate(
            """(targetId) => {
              const s = window.__libtv_store.getState();
              s.selectElements({ nodeIds: [targetId], edgeIds: [] });
            }""",
            target_id,
        )
        before_delete = graph_state(page)
        page.evaluate(
            """(targetId) => {
              const s = window.__libtv_store.getState();
              s.removeSelectedNodes([targetId]);
            }""",
            target_id,
        )
        page.wait_for_timeout(300)
        after_delete = graph_state(page)
        edges_before = {
            (e["source"], e["target"]) for e in before_delete["edges"]
        }
        edges_after = {
            (e["source"], e["target"]) for e in after_delete["edges"]
        }
        scene_one = {
            "nodeRemoved": target_id not in after_delete["nodeIds"],
            "sourceSurvives": source_id in after_delete["nodeIds"],
            "edgeClosure": (source_id, target_id) not in edges_after,
            "edgeExistedBefore": (source_id, target_id) in edges_before,
            "oneHistoryStep": after_delete["past"] - before_delete["past"] == 1,
        }
        assert all(scene_one.values()), scene_one
        scene_two = {
            "selectionNoLongerHoldsDeleted": target_id not in after_delete["selection"],
        }
        assert scene_two["selectionNoLongerHoldsDeleted"], scene_two

        # Scene 3: zero-partial undo restores node AND edge; redo removes.
        page.keyboard.press("Control+z")
        page.wait_for_timeout(300)
        after_undo = graph_state(page)
        undo_ok = (
            target_id in after_undo["nodeIds"]
            and (source_id, target_id) in {
                (e["source"], e["target"]) for e in after_undo["edges"]
            }
            and after_undo["future"] == 1
        )
        page.keyboard.press("Control+Shift+z")
        page.wait_for_timeout(300)
        after_redo = graph_state(page)
        redo_ok = (
            target_id not in after_redo["nodeIds"]
            and (source_id, target_id) not in {
                (e["source"], e["target"]) for e in after_redo["edges"]
            }
        )
        scene_three = {
            "undo_restores_node_and_edge": undo_ok,
            "redo_removes_again": redo_ok,
        }
        assert scene_three["undo_restores_node_and_edge"], scene_three
        assert scene_three["redo_removes_again"], scene_three

        browser.close()
    assert not errors, errors

    audit = {
        "url": URL,
        "status": "FOCUSED_BROWSER_RECORDED_PASS",
        "slice": "GRAPH-DELETE focused fixture — structural closure, "
        "selection invalidation, zero-partial undo/redo (plain node scene)",
        "scenes": {
            "plain_delete_closure": scene_one,
            "selection_invalidated": scene_two,
            "undo_redo_zero_partial": scene_three,
        },
        "errors": {"console": [], "page": [], "request": []},
    }
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    print(
        "Batch 517 verification passed: graph delete focused scenes green "
        "(edge closure, selection invalidation, zero-partial undo/redo); "
        "recorded in runtime-audit.json."
    )


if __name__ == "__main__":
    main()
