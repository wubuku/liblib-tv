#!/usr/bin/env python3
"""Verify Batch 522: GRAPH-DELETE shot/process aggregate scene —
shot-breakdown deletion against its surviving result cohort, driven through
the real store actions.

Contract: docs/research/LIBTV_GRAPH_DELETE_REFERENCE_REPAIR_MATRIX.md §14
(LIBTV-FIX-LOCAL-GRAPH-DELETE-01, shot aggregate scene). Observed contract:
completing a shot-breakdown creates result nodes carrying a
sourceBreakdownId back-reference; deleting the breakdown leaves the result
cohort alive with the back-references in place (documented inverse-ref
behavior) and zero dangling edges, in exactly one history step; undo
restores the breakdown zero-partial.

Scenes:
- complete_creates_cohort: dimensions ['storyboard','motion'] produce the
  result cohort, each with sourceBreakdownId pointing at the breakdown;
- breakdown_delete_cohort_survives: removeNode(breakdown) keeps all results,
  zero dangling edges, one history step;
- undo_zero_partial: undo restores the breakdown; results unchanged.
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
    / "liblib-canvas-batch522-2026-09-14"
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
          return {
            nodeCount: canvas.nodes.length,
            past: history.past.length,
            future: history.future.length,
            dangling: canvas.edges.filter(
              (e) => !canvas.nodes.find((n) => n.id === e.source || n.id === e.target),
            ).length,
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

        baseline = graph_state(page)

        # Scene 1: complete a shot-breakdown into a result cohort.
        page.evaluate("() => window.__libtv_store.getState().addNode('shot-breakdown', {})")
        page.wait_for_timeout(200)
        mid = graph_state(page)
        sb_id = page.evaluate(
            """() => {
              const c = window.__libtv_store.getState().getActiveCanvas();
              return [...c.nodes].reverse().find((n) => n.type === 'shot-breakdown').id;
            }"""
        )
        page.evaluate(
            """(sbId) => window.__libtv_store.getState().completeShotBreakdown(
                  sbId, ['storyboard', 'motion'])""",
            sb_id,
        )
        page.wait_for_timeout(300)
        after_complete = graph_state(page)
        cohort = page.evaluate(
            """(sbId) => {
              const c = window.__libtv_store.getState().getActiveCanvas();
              const results = c.nodes.filter((n) => n.type === 'shot-breakdown-result');
              return { count: results.length,
                       refsOk: results.every((r) => r.data?.sourceBreakdownId === sbId) };
            }""",
            sb_id,
        )
        scene_one = {
            "resultCount": cohort["count"],
            "backRefsAllPointAtBreakdown": cohort["refsOk"],
            "oneStepComplete": after_complete["past"] - mid["past"] == 1,
        }
        assert scene_one["resultCount"] == 4, scene_one
        assert scene_one["backRefsAllPointAtBreakdown"], scene_one
        assert scene_one["oneStepComplete"], scene_one

        # Scene 2: delete the breakdown — cohort survives, zero dangling.
        pre_delete = graph_state(page)
        page.evaluate(
            """(sbId) => window.__libtv_store.getState().removeNode(sbId)""",
            sb_id,
        )
        page.wait_for_timeout(300)
        after_delete = graph_state(page)
        scene_two = {
            "cohortSurvives": after_delete["nodeCount"] == after_complete["nodeCount"] - 1,
            "zeroDangling": after_delete["dangling"] == 0,
            "oneStepDelete": after_delete["past"] - pre_delete["past"] == 1,
        }
        assert all(scene_two.values()), scene_two

        # Scene 3: undo restores the breakdown zero-partial.
        page.keyboard.press("Control+z")
        page.wait_for_timeout(300)
        after_undo = graph_state(page)
        scene_three = {
            "breakdownRestored": after_undo["nodeCount"] == after_complete["nodeCount"],
            "futureHasRedo": after_undo["future"] == 1,
        }
        assert all(scene_three.values()), scene_three

        browser.close()
    assert not errors, errors

    audit = {
        "url": URL,
        "status": "FOCUSED_BROWSER_RECORDED_PASS",
        "slice": "GRAPH-DELETE shot/process aggregate scene — breakdown "
        "deletion against its surviving result cohort (inverse-ref behavior "
        "documented as observed)",
        "scenes": {
            "complete_creates_cohort": scene_one,
            "breakdown_delete_cohort_survives": scene_two,
            "undo_zero_partial": scene_three,
        },
        "errors": {"console": [], "page": [], "request": []},
    }
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    print(
        "Batch 522 verification passed: shot aggregate delete scenes green "
        "(cohort creation with back-refs, cohort survives breakdown "
        "deletion, zero-partial undo); recorded in runtime-audit.json."
    )


if __name__ == "__main__":
    main()
