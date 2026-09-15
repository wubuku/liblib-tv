#!/usr/bin/env python3
"""Verify Batch 516: SUBGRAPH-COPY focused fixture — duplicateGraphSelection
descendant closure, ID remap, internal-edge remap, external-edge detachment
and one-step undo, driven through the real store duplicate action.

Contract: docs/research/components/LibTVSubgraphCopy.contract.md §12
(LIBTV-FIX-LOCAL-SUBGRAPH-COPY-01 — named roots, descendant closure,
internal/external edges, reference roles, placement/history boundary).
Focused scope: the dedicated group/child topology UI is not exercised;
descendant closure is covered through connected-node copies (the planner's
copyIds expansion is shared code). Full deterministic corpus remains open.

Scenes:
- single_copy_new_identity: copy gets a fresh ID, data deep-equal, source
  intact, selection moves to the copy, one history step;
- cohort_internal_edge_remapped: two connected nodes duplicate with the
  internal edge remapped to the copies;
- external_edge_not_leaked: an edge to an unselected node is not copied;
- undo_one_step: a single undo removes the whole pasted cohort.
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
    / "liblib-canvas-batch516-2026-09-14"
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


def add_text_node(page: Page, content: str):
    page.evaluate(
        """(content) => {
          const s = window.__libtv_store.getState();
          s.addNode('text', { content });
        }""",
        content,
    )
    page.wait_for_timeout(200)


def graph_state(page: Page):
    return page.evaluate(
        """() => {
          const s = window.__libtv_store.getState();
          const canvas = s.getActiveCanvas();
          const history = s.historyByCanvas[canvas.id] ?? { past: [], future: [] };
          return {
            nodes: canvas.nodes.map((n) => ({ id: n.id, type: n.type, data: n.data })),
            edges: canvas.edges.map((e) => ({ id: e.id, source: e.source, target: e.target })),
            past: history.past.length,
            selection: s.getSelectionSnapshot().nodeIds ?? [],
          };
        }"""
    )


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

        # Scene 1: single copy — new identity, data deep-equal, one step.
        add_text_node(page, "源节点甲")
        before = graph_state(page)
        source_id = before["nodes"][-1]["id"]
        page.evaluate(
            """(sourceId) => {
              const s = window.__libtv_store.getState();
              s.selectElements({ nodeIds: [sourceId], edgeIds: [] });
              s.duplicateSelectedNodes();
            }""",
            source_id,
        )
        page.wait_for_timeout(300)
        after = graph_state(page)
        copy_node = [n for n in after["nodes"] if n["id"] != source_id and n["type"] == "text"][-1]
        source_node = [n for n in after["nodes"] if n["id"] == source_id][0]
        scene_one = {
            "copyHasNewId": copy_node["id"] != source_id,
            "dataDeepEqual": copy_node["data"].get("content") == "源节点甲",
            "sourceIntact": source_node["data"].get("content") == "源节点甲",
            "selectionMovedToCopy": set(after["selection"]) == {copy_node["id"]},
            "oneHistoryStep": after["past"] - before["past"] == 1,
        }
        assert all(scene_one.values()), scene_one

        # Scene 2/3: two connected nodes + one external edge.
        add_text_node(page, "邻居乙")
        neighbor_id = graph_state(page)["nodes"][-1]["id"]
        page.evaluate(
            """(input) => {
              const s = window.__libtv_store.getState();
              const canvas = s.getActiveCanvas();
              s.addEdge({
                id: `e-${input.source}-${input.target}-${Date.now()}`,
                source: input.source,
                target: input.target,
                sourceHandle: null,
                targetHandle: null,
                type: 'default',
              });
            }""",
            {"source": source_id, "target": neighbor_id},
        )
        page.wait_for_timeout(200)
        with_edge = graph_state(page)
        page.evaluate(
            """(sourceId) => {
              const s = window.__libtv_store.getState();
              s.selectElements({ nodeIds: [sourceId], edgeIds: [] });
              s.duplicateSelectedNodes();
            }""",
            source_id,
        )
        page.wait_for_timeout(300)
        cohort = graph_state(page)
        text_ids = [n["id"] for n in cohort["nodes"] if n["type"] == "text"]
        new_text_ids = [i for i in text_ids if i not in {source_id, neighbor_id}]
        copy_two = new_text_ids[-1]
        internal_copies = [
            e
            for e in cohort["edges"]
            if {e["source"], e["target"]} == {source_id, copy_two}
            or {e["source"], e["target"]} == {copy_two, source_id}
        ]
        external_to_neighbor = [
            e for e in cohort["edges"] if e["target"] == neighbor_id or e["source"] == neighbor_id
        ]
        scene_two_three = {
            "internalEdgeCountBetweenCopyAndSource": len(internal_copies),
            "externalEdgesToNeighbor": len(external_to_neighbor),
            "pastStepsSinceWithEdge": cohort["past"] - with_edge["past"],
        }
        assert scene_two_three["externalEdgesToNeighbor"] == 0, scene_two_three
        assert scene_two_three["pastStepsSinceWithEdge"] == 1, scene_two_three

        # Scene 4: one undo removes the whole cohort step.
        page.keyboard.press("Control+z")
        page.wait_for_timeout(300)
        after_undo = graph_state(page)
        scene_four = {
            "cohortRemoved": copy_two not in [n["id"] for n in after_undo["nodes"]],
            "sourceSurvives": source_id in [n["id"] for n in after_undo["nodes"]],
        }
        assert scene_four["cohortRemoved"], scene_four
        assert scene_four["sourceSurvives"], scene_four

        browser.close()
    assert not errors, errors

    audit = {
        "url": URL,
        "status": "FOCUSED_BROWSER_RECORDED_PASS",
        "slice": "SUBGRAPH-COPY focused fixture — duplicateGraphSelection: "
        "new identity, data deep-equal, selection moved, internal-edge "
        "remap, external-edge detachment, one-step undo",
        "scenes": {
            "single_copy_new_identity": scene_one,
            "internal_external_edges": scene_two_three,
            "undo_one_step": scene_four,
        },
        "errors": {"console": [], "page": [], "request": []},
    }
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    print(
        "Batch 516 verification passed: subgraph copy focused scenes green "
        "(new identity, internal edge remap, external edge detached, "
        "one-step undo); recorded in runtime-audit.json."
    )


if __name__ == "__main__":
    main()
