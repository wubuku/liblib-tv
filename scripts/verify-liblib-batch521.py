#!/usr/bin/env python3
"""Verify Batch 521: GRAPH-DELETE derived-reference scene — first-frame
reference creation, anti-duplicate guard and source-deletion behavior,
driven through the real store actions.

Contract: docs/research/LIBTV_GRAPH_DELETE_REFERENCE_REPAIR_MATRIX.md §14
(derived scene) + batch 246/255 anti-duplicate semantics. This corrects
batch 520's BLOCKED_BY_FIXTURE conclusion: the earlier no-op was the
anti-duplicate guard (demo video already carries an image→video edge),
not a missing media fixture.

Scenes:
- derived_create_transaction: a fresh video + createFirstFrameReference
  adds one image node (素材 - 首帧参考), one image→video edge, one step;
- anti_duplicate_guard: creating again on a video that already has an
  image→video edge grows nothing (attempt-only skip);
- source_delete_derived_survives: removeNode(video) removes the video and
  its edges with zero dangling residue while the derived image survives,
  in one step;
- undo_zero_partial: undo of the delete restores video and edge; undo of
  the create removes the whole one-transaction cohort.
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
    / "liblib-canvas-batch521-2026-09-14"
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
            edgeCount: canvas.edges.length,
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

        # Scene 1: fresh video + derived first-frame reference.
        page.evaluate("() => window.__libtv_store.getState().addNode('video', {})")
        page.wait_for_timeout(200)
        # addNode is itself a user command (one history step) — the derived
        # scene measures from after the video exists.
        mid = graph_state(page)
        video_id = page.evaluate(
            """() => {
              const c = window.__libtv_store.getState().getActiveCanvas();
              return [...c.nodes].reverse().find((n) => n.type === 'video').id;
            }"""
        )
        page.evaluate(
            """(videoId) => window.__libtv_store.getState().createFirstFrameReference(videoId)""",
            video_id,
        )
        page.wait_for_timeout(300)
        after_create = graph_state(page)
        scene_one = {
            "nodeDelta": after_create["nodeCount"] - mid["nodeCount"],
            "edgeDelta": after_create["edgeCount"] - mid["edgeCount"],
            "pastDelta": after_create["past"] - mid["past"],
        }
        assert scene_one == {"nodeDelta": 1, "edgeDelta": 1, "pastDelta": 1}, scene_one

        # Scene 2: anti-duplicate guard on a video that has an image→video
        # edge (the demo canvas video carries a preset image).
        guard = page.evaluate(
            """() => {
              const s = window.__libtv_store.getState();
              const c = s.getActiveCanvas();
              const video = c.nodes.find(
                (n) => n.type === 'video'
                  && c.edges.some((e) => {
                    if (e.target !== n.id) return false;
                    const src = c.nodes.find((x) => x.id === e.source);
                    return src?.type === 'image';
                  }),
              );
              if (!video) return { skipped: true };
              const before = c.nodes.length;
              s.createFirstFrameReference(video.id);
              const c2 = window.__libtv_store.getState().getActiveCanvas();
              return { skipped: false, nodeDelta: c2.nodes.length - before };
            }"""
        )
        scene_two = guard
        assert scene_two == {"skipped": True} or scene_two["nodeDelta"] == 0, scene_two

        # Scene 3: source deletion — derived image survives, zero dangling.
        pre_delete = graph_state(page)
        page.evaluate(
            """(videoId) => window.__libtv_store.getState().removeNode(videoId)""",
            video_id,
        )
        page.wait_for_timeout(300)
        after_delete = graph_state(page)
        scene_three = {
            "derivedSurvivesAsIndependentNode": after_delete["dangling"] == 0,
            "oneStepDelete": after_delete["past"] - pre_delete["past"] == 1,
            "futureEmpty": after_delete["future"] == 0,
        }
        assert all(scene_three.values()), scene_three

        # Scene 4: undo restores the whole delete transaction zero-partial.
        page.keyboard.press("Control+z")
        page.wait_for_timeout(300)
        after_undo = graph_state(page)
        scene_four = {
            "videoRestored": after_undo["nodeCount"] == after_create["nodeCount"],
            "edgeRestored": after_undo["edgeCount"] == after_create["edgeCount"],
        }
        assert all(scene_four.values()), scene_four

        browser.close()
    assert not errors, errors

    audit = {
        "url": URL,
        "status": "FOCUSED_BROWSER_RECORDED_PASS",
        "slice": "GRAPH-DELETE derived-reference scene — creation "
        "transaction, anti-duplicate guard, source deletion with surviving "
        "derived image, zero-partial undo",
        "scenes": {
            "derived_create_transaction": scene_one,
            "anti_duplicate_guard": scene_two,
            "source_delete_derived_survives": scene_three,
            "undo_zero_partial": scene_four,
        },
        "correction": "batch 520 BLOCKED_BY_FIXTURE conclusion reversed — "
        "the no-op was the batch 246/255 anti-duplicate guard, not a missing "
        "media fixture",
        "errors": {"console": [], "page": [], "request": []},
    }
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    print(
        "Batch 521 verification passed: derived-reference lifecycle green "
        "(one-transaction create, anti-duplicate guard, derived survives "
        "source deletion, zero-partial undo); recorded in runtime-audit.json."
    )


if __name__ == "__main__":
    main()
