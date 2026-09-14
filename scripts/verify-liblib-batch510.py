#!/usr/bin/env python3
"""Verify Batch 510: VR-018 §13 — LIBTV-FIX-LOCAL-COMMAND-FEEDBACK-01
runtime fixture, deterministic and pure.

Contract: docs/research/LIBTV_COMMAND_OUTCOME_FEEDBACK_CONTRACT.md §13
(controls, 15 scenes, reset assertions). The fixture world is exposed as
window.__libtv_command_feedback_fixture_scenes and runs every scene with
§13.3 invariant assertions. Route isolation (§13.2 scene 15) is completed
statically: this module must reference no FrameOS route.

Scenes:
- fixture_scenes: all §13.2 scenes 1-15 report ok, each with §13.3
  invariants asserted inside the runner;
- route_isolation_static: no FrameOS reference in the fixture module.
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
    / "liblib-canvas-batch510-2026-09-14"
    / "runtime-audit.json"
)
MODULE_PATH = ROOT / "src" / "lib" / "libtvCommandFeedbackFixture.ts"


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

    # Static route isolation: the fixture module is a liblib-route artifact.
    # Strip comment lines first — the check targets actual code references.
    code_lines = [
        line
        for line in MODULE_PATH.read_text(encoding="utf-8").splitlines()
        if not line.strip().startswith("//") and not line.strip().startswith("*")
    ]
    code_source = "\n".join(code_lines).lower()
    assert "frameos" not in code_source, "fixture references FrameOS"

    errors = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(
            viewport={"width": 929, "height": 874}, device_scale_factor=1
        )
        errors.extend(attach_errors(page))
        page.goto(URL, wait_until="networkidle")
        page.wait_for_timeout(450)

        scenes = page.evaluate(
            "() => window.__libtv_command_feedback_fixture_scenes()"
        )
        expected = [
            "connection_allow_reject",
            "field_reject_edit_retry",
            "prototype_unavailable",
            "node_guard_timer_replacement",
            "visible_graph_result",
            "started_progress_completed",
            "retry_stale_then_success",
            "switch_canvas_terminal",
            "delete_owner_orphan",
            "panel_close_local_vs_background",
            "duplicate_terminal_suppressed",
            "burst_bounded_aggregation",
            "undo_redo_no_feedback_replay",
            "long_message_bound",
            "route_isolation_libtv_owners",
        ]
        assert len(scenes) == len(expected), sorted(scenes)
        failed = {k: v for k, v in scenes.items() if not v["ok"]}
        assert not failed, failed
        for name in expected:
            assert name in scenes, name

        browser.close()
    assert not errors, errors

    audit = {
        "url": URL,
        "status": "PURE_RUNTIME_RECORDED_PASS",
        "slice": "VR-018 §13 LIBTV-FIX-LOCAL-COMMAND-FEEDBACK-01 runtime — "
        "deterministic fixture world, 15 scenes, §13.3 reset assertions",
        "scenes": scenes,
        "route_isolation_static": "no FrameOS reference in fixture module",
        "errors": {"console": [], "page": [], "request": []},
    }
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    print(
        "Batch 510 verification passed: all 15 §13.2 fixture scenes green "
        "with §13.3 reset invariants; route isolation static check green; "
        "recorded in runtime-audit.json."
    )


if __name__ == "__main__":
    main()
