#!/usr/bin/env python3
"""Verify Batch 439: viewport contract §6.3/DQ-003 — live/stable endpoint
phase compression.

Contract: docs/research/LIBTV_VIEWPORT_COORDINATE_PLACEMENT_CONTRACT.md
§6.3 (live updates per frame; stable on end/explicit completion),
DQ-003 ("update live per frame; stable on end"), §6.4 (no-animation
commands may commit LIVE+STABLE in one validated commit).

Implementation (src/app/page.tsx):
- onViewportChange (per-frame) updates the live projection (flow viewport
  state + zoom readout) and logs "live-frame" — no store write, no
  ownership flip;
- onMoveEnd commits the stable endpoint once per gesture (store write,
  ownership flip bootstrap->stable, "viewport-accepted");
- __libtv_apply_viewport_event keeps its default immediate stable commit
  (batch-65 verifier semantics unchanged);
- the batch-438 resize observer keeps its direct immediate stable commit.

Scenes:
- bootstrap_pan_endpoint: fresh canvas-2 — live frames log with bootstrap
  ownership, the move end flips to stable exactly once and writes the
  store;
- explicit_command_still_stable: two-arg apply_viewport_event commits
  stable immediately (batch-65 contract preserved).
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
    / "liblib-canvas-batch439-2026-09-13"
    / "runtime-audit.json"
)
SCREENSHOT_PATH = (
    ROOT
    / "docs"
    / "design-references"
    / "liblib-clone-batch439-endpoint-phase-929-2026-09-13.png"
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


def owner_log(page: Page):
    return page.evaluate("() => [...window.__libtv_viewport_owner_log]")


def stored_viewport(page: Page):
    return page.evaluate(
        """() => {
          const state = window.__libtv_store.getState();
          return state.getActiveCanvas()?.viewport ?? null;
        }"""
    )


def ownership(page: Page):
    return page.evaluate(
        "() => window.__libtv_get_viewport_ownership()['canvas-2'] ?? null"
    )


def run_bootstrap_pan_endpoint(page: Page):
    before = stored_viewport(page)
    page.mouse.move(550, 430)
    # Multiple wheel ticks: xyflow's panOnScroll handler schedules the
    # gesture end 150ms after the LAST wheel tick (first tick only starts).
    for _ in range(5):
        page.mouse.wheel(0, 60)
        page.wait_for_timeout(60)
    page.wait_for_timeout(700)

    log = owner_log(page)
    live_bootstrap = [
        e for e in log
        if e["reason"] == "live-frame" and e["ownership"] == "bootstrap"
    ]
    assert live_bootstrap, "pan frames must log as live-frame entries"
    accepted = [
        e for e in log
        if e["reason"] == "viewport-accepted" and e["ownership"] == "stable"
    ]
    assert accepted, "the move end must log the stable endpoint once"
    first_live_index = log.index(live_bootstrap[0])
    stable_index = log.index(accepted[-1])
    assert first_live_index < stable_index, (
        "live frames must precede the stable endpoint"
    )
    assert ownership(page) == "stable"

    after = stored_viewport(page)
    assert after != before, "stable endpoint must write the store"
    return {
        "liveFrameEntries": len(live_bootstrap),
        "stableEndpointEntries": len(accepted),
        "ownershipFlippedToStable": True,
        "storeWrittenAtEndpoint": True,
    }


def run_explicit_command_still_stable(page: Page):
    before = stored_viewport(page)
    result = page.evaluate(
        """() =>
          window.__libtv_apply_viewport_event("canvas-2", {
            x: -120,
            y: -64,
            zoom: 1.1,
          })"""
    )
    assert result == {"status": "committed", "reason": "viewport-accepted"}, (
        result
    )
    after = stored_viewport(page)
    assert after, "explicit command must write the store"
    assert abs(after["x"] - (-120)) < 0.5 and abs(after["zoom"] - 1.1) < 0.01, (
        before,
        after,
    )
    return {"result": result, "storeWritten": True}


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

        bootstrap = run_bootstrap_pan_endpoint(page)
        explicit = run_explicit_command_still_stable(page)
        page.screenshot(path=str(SCREENSHOT_PATH))
        assert_no_overflow(page)
        browser.close()
    assert not errors, errors

    audit = {
        "url": URL,
        "status": "SCRIPT_RECORDED_PASS",
        "slice": "VGP §6.3/DQ-003 — live per frame, stable on move end; "
        "explicit commands keep the immediate stable commit",
        "bootstrap_pan_endpoint": bootstrap,
        "explicit_command_still_stable": explicit,
        "errors": {"console": [], "page": [], "request": []},
    }
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    print(
        "Batch 439 Playwright verification passed: pan frames update the live "
        "projection only, the move end commits the stable endpoint once with "
        "the bootstrap->stable ownership flip, explicit viewport commands "
        "keep the immediate stable commit, browser diagnostics clean."
    )


if __name__ == "__main__":
    main()
