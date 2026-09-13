#!/usr/bin/env python3
"""Verify Batch 467: VR-018 Slice A — command feedback inventory and reason
projection.

Contract: docs/research/LIBTV_COMMAND_OUTCOME_FEEDBACK_CONTRACT.md
Slice A ("catalog ordinary LibTV command adapters; preserve existing
connection reason union; define UI-only mapping without changing graph
validation; keep source-unconfirmed presentation disabled/diagnostic").

Implementation:
- src/lib/libtvCommandFeedback.ts: the command surface inventory
  (nine surfaces across the canvas, panels and store adapters) and the
  stable outcome -> disposition projection (§9.2: a no-op is inert and
  never announces success);
- read-only window diagnostics.

Scenes:
- catalog: nine surfaces declared, each with component/kind/profile;
- projection: accepted -> success(announce), no-op -> inert(silent),
  rejected/stale/conflict/invalid-target -> error(announce).
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
    / "liblib-canvas-batch467-2026-09-14"
    / "runtime-audit.json"
)
SCREENSHOT_PATH = (
    ROOT
    / "docs"
    / "design-references"
    / "liblib-clone-batch467-command-feedback-929-2026-09-14.png"
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
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(
            viewport={"width": 929, "height": 874}, device_scale_factor=1
        )
        errors.extend(attach_errors(page))
        page.goto(URL, wait_until="networkidle")
        page.wait_for_timeout(450)

        catalog = page.evaluate(
            "() => window.__libtv_command_feedback_catalog"
        )
        assert len(catalog) == 9, catalog
        surface_ids = {entry["surfaceId"] for entry in catalog}
        assert {
            "add-node-panel",
            "add-resource-upload",
            "video-clip-panel",
            "subtitle-erase-panel",
            "smart-matting-panel",
            "shot-breakdown-card",
            "editor-session-commit",
            "asset-reference-attach",
            "annotate-toolbar",
        } == surface_ids, surface_ids

        projection = page.evaluate(
            """() => ({
              accepted: window.__libtv_project_command_feedback('accepted'),
              noOp: window.__libtv_project_command_feedback('no-op'),
              rejected: window.__libtv_project_command_feedback('rejected'),
              stale: window.__libtv_project_command_feedback('stale'),
              invalidTarget:
                window.__libtv_project_command_feedback('invalid-target'),
              conflict: window.__libtv_project_command_feedback('conflict'),
            })"""
        )
        assert projection["accepted"] == {
            "disposition": "success",
            "announce": True,
        }, projection
        assert projection["noOp"] == {
            "disposition": "inert",
            "announce": False,
        }, projection
        for key in ("rejected", "stale", "invalidTarget", "conflict"):
            assert projection[key]["disposition"] == "error", (key, projection)
            assert projection[key]["announce"] is True, (key, projection)

        page.screenshot(path=str(SCREENSHOT_PATH))
        assert_no_overflow(page)
        browser.close()
    assert not errors, errors

    audit = {
        "url": URL,
        "status": "SCRIPT_RECORDED_PASS",
        "slice": "VR-018 Slice A — command feedback inventory and reason "
        "projection",
        "catalogSize": len(catalog),
        "projection": projection,
        "errors": {"console": [], "page": [], "request": []},
    }
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    print(
        "Batch 467 Playwright verification passed: command feedback catalog "
        "covers nine surfaces, outcome->disposition projection exact "
        "(accepted success, no-op inert, rejections error/announce), "
        "diagnostics clean."
    )


if __name__ == "__main__":
    main()
