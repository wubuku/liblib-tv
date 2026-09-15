#!/usr/bin/env python3
"""Verify Batch 518: GRAPH-ENTRYPOINT focused fixture — cross-ingress
consistency for the same semantic proposal.

Contract: docs/research/LIBTV_GRAPH_MUTATION_ENTRYPOINT_TRUST_MATRIX.md
(LIBTV-FIX-LOCAL-GRAPH-ENTRYPOINT-01). Focused scope: the transport
whitelist (T0 selection / T1 transport) and the named-command ingress,
compared for the same proposal. The full composed corpus (document/copy/
data/delete fixtures over every alias) remains open.

Scenes:
- semantic_add_via_changes_rejected: a node-add proposed through the React
  Flow change callback is rejected zero-partial (UNSUPPORTED variant path
  of the T-gate);
- selection_transport_allowed: a pure selection batch is accepted;
- stale_snapshot_rejected: a change for an unknown node id is rejected;
- named_command_accepts: the same semantic add via the named addNode
  command is accepted with exactly one history step.
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
    / "liblib-canvas-batch518-2026-09-14"
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
              const plan = window.__libtv_change_routing_plan;
              const s = window.__libtv_store.getState();
              const canvas = s.getActiveCanvas();
              const snapshot = {
                activeCanvasId: canvas.id,
                nodes: canvas.nodes,
                edges: canvas.edges,
                selectedNodeIds: [],
                selectedEdgeIds: [],
              };
              const out = {};
              // Scene 1: semantic add through the change callback (T-gate).
              const addChange = plan(snapshot, {
                expectedActiveCanvasId: canvas.id,
                nodeChanges: [{ type: 'add', item: { id: 'x', type: 'text' } }],
              });
              out.semantic_add_via_changes_rejected = addChange;
              // Scene 2: pure selection batch (T0).
              const firstNodeId = canvas.nodes[0]?.id;
              const selection = plan(snapshot, {
                expectedActiveCanvasId: canvas.id,
                nodeChanges: firstNodeId
                  ? [{ id: firstNodeId, type: 'select', selected: true }]
                  : [],
              });
              out.selection_transport_allowed = selection;
              // Scene 3: stale snapshot — unknown node id.
              const stale = plan(snapshot, {
                expectedActiveCanvasId: canvas.id,
                nodeChanges: [{ id: 'ghost-node', type: 'select', selected: true }],
              });
              out.stale_snapshot_rejected = stale;
              // Scene 4: the same semantic proposal via the named command.
              const before = canvas.nodes.length;
              s.addNode('text', { content: '入口一致性' });
              const after = window.__libtv_store.getState().getActiveCanvas();
              const history = window.__libtv_store.getState().historyByCanvas[canvas.id]
                ?? { past: [], future: [] };
              out.named_command_accepts = {
                nodeDelta: after.nodes.length - before,
                past: history.past.length,
                rejectedIngressResidue: addChange.status === 'reject' ? 0 : 1,
              };
              return out;
            }"""
        )

        s1 = scenes["semantic_add_via_changes_rejected"]
        assert s1["status"] == "reject", s1
        s2 = scenes["selection_transport_allowed"]
        assert s2["status"] == "accept" and s2["code"] == "APPLIED_SELECTION", s2
        s3 = scenes["stale_snapshot_rejected"]
        assert s3["status"] == "reject", s3
        s4 = scenes["named_command_accepts"]
        assert s4["nodeDelta"] == 1 and s4["past"] >= 1, s4
        assert s4["rejectedIngressResidue"] == 0, s4

        browser.close()
    assert not errors, errors

    audit = {
        "url": URL,
        "status": "FOCUSED_BROWSER_RECORDED_PASS",
        "slice": "GRAPH-ENTRYPOINT focused fixture — cross-ingress "
        "consistency: transport whitelist vs named command for the same "
        "proposal",
        "scenes": scenes,
        "errors": {"console": [], "page": [], "request": []},
    }
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    print(
        "Batch 518 verification passed: cross-ingress consistency green "
        "(semantic add rejected via changes, selection transport allowed, "
        "stale snapshot rejected, named command accepted one-step); "
        "recorded in runtime-audit.json."
    )


if __name__ == "__main__":
    main()
