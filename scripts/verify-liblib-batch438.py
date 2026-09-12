#!/usr/bin/env python3
"""Verify Batch 438: viewport contract §7.2 — host resize reconciliation
(resize anchor policy) on top of the batch-65 bootstrap/stable owner.

Contract: docs/research/LIBTV_VIEWPORT_COORDINATE_PLACEMENT_CONTRACT.md
§7.2 clone correctness default (preserve the flow point under the old host
center at the new host center), §7.4 responsive bootstrap boundary, and
`LIBTV-VGP-I-025` (one declared anchor-preservation policy).

Implementation (src/app/page.tsx): a ResizeObserver reconciles the live
viewport on host size change with center preservation; applies only to
stable (user-owned) viewports; breakpoint flips stay delegated to the
batch-65 responsive authority; every decision lands in
`window.__libtv_viewport_owner_log` with declared reasons.

Scenes:
- bootstrap_resize_skipped: resize before user ownership is not reconciled;
- resize_anchor_center_preserved: after wheel-pan ownership is stable, a
  host resize keeps zoom constant and the flow point under the old center
  stays under the new center;
- stored_viewport_survives_switch: the reconciled viewport persists across
  canvas switch and return.
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
    / "liblib-canvas-batch438-2026-09-13"
    / "runtime-audit.json"
)
SCREENSHOT_PATH = (
    ROOT
    / "docs"
    / "design-references"
    / "liblib-clone-batch438-resize-anchor-1200-2026-09-13.png"
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


def ownership(page: Page):
    return page.evaluate(
        "() => window.__libtv_get_viewport_ownership()['canvas-2'] ?? null"
    )


def stored_viewport(page: Page):
    return page.evaluate(
        """() => {
          const state = window.__libtv_store.getState();
          return state.getActiveCanvas()?.viewport ?? null;
        }"""
    )


def owner_log(page: Page):
    return page.evaluate("() => [...window.__libtv_viewport_owner_log]")


def host_rect(page: Page):
    return page.evaluate(
        """() => {
          const host = document.querySelector('[data-libtv-react-flow-host]');
          const rect = host?.getBoundingClientRect();
          return rect
            ? { width: rect.width, height: rect.height }
            : null;
        }"""
    )


def run_bootstrap_resize_skipped(page: Page):
    page.set_viewport_size({"width": 1100, "height": 820})
    page.wait_for_timeout(500)
    log = owner_log(page)
    committed = [e for e in log if e["reason"] == "resize-anchor"]
    skipped = [e for e in log if e["reason"] == "resize-anchor-not-applicable"]
    assert not committed, committed
    assert skipped, "bootstrap-phase resize must be recorded as skipped"
    assert ownership(page) == "bootstrap"
    return {"skipEntries": len(skipped), "committedEntries": len(committed)}


def run_resize_anchor_center_preserved(page: Page):
    page.mouse.move(550, 420)
    page.mouse.wheel(0, 240)
    page.wait_for_timeout(420)
    assert ownership(page) == "stable", "wheel pan must grant stable ownership"

    pre_viewport = stored_viewport(page)
    pre_host = host_rect(page)
    assert pre_viewport and pre_host
    pre_zoom = pre_viewport["zoom"]

    page.set_viewport_size({"width": 1360, "height": 940})
    page.wait_for_timeout(600)

    post_viewport = stored_viewport(page)
    post_host = host_rect(page)
    assert post_viewport and post_host
    assert abs(post_viewport["zoom"] - pre_zoom) < 0.01, (
        pre_viewport,
        post_viewport,
    )

    old_center_flow_x = (pre_host["width"] / 2 - pre_viewport["x"]) / pre_zoom
    old_center_flow_y = (pre_host["height"] / 2 - pre_viewport["y"]) / pre_zoom
    new_center_flow_x = (
        post_host["width"] / 2 - post_viewport["x"]
    ) / post_viewport["zoom"]
    new_center_flow_y = (
        post_host["height"] / 2 - post_viewport["y"]
    ) / post_viewport["zoom"]
    assert abs(old_center_flow_x - new_center_flow_x) < 2.0, (
        pre_viewport,
        post_viewport,
        pre_host,
        post_host,
    )
    assert abs(old_center_flow_y - new_center_flow_y) < 2.0, (
        pre_viewport,
        post_viewport,
        pre_host,
        post_host,
    )

    log = owner_log(page)
    committed = [e for e in log if e["reason"] == "resize-anchor"]
    assert committed, "resize-anchor commit must be logged"
    assert committed[-1]["ownership"] == "stable"
    return {
        "preViewport": pre_viewport,
        "postViewport": post_viewport,
        "preHost": pre_host,
        "postHost": post_host,
        "centerFlowDelta": [
            abs(old_center_flow_x - new_center_flow_x),
            abs(old_center_flow_y - new_center_flow_y),
        ],
    }


def run_stored_viewport_survives_switch(page: Page, expected_viewport):
    page.evaluate(
        "() => window.__libtv_store.getState().setActiveCanvas('canvas-1')"
    )
    page.wait_for_timeout(320)
    page.evaluate(
        "() => window.__libtv_store.getState().setActiveCanvas('canvas-2')"
    )
    page.wait_for_timeout(320)
    restored = stored_viewport(page)
    assert restored, "canvas viewport must exist after switch and return"
    assert abs(restored["x"] - expected_viewport["x"]) < 0.5, (
        expected_viewport,
        restored,
    )
    assert abs(restored["y"] - expected_viewport["y"]) < 0.5, (
        expected_viewport,
        restored,
    )
    assert abs(restored["zoom"] - expected_viewport["zoom"]) < 0.01
    return {"restoredViewport": restored}


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

        bootstrap = run_bootstrap_resize_skipped(page)
        anchor = run_resize_anchor_center_preserved(page)
        survived = run_stored_viewport_survives_switch(
            page, anchor["postViewport"]
        )
        page.screenshot(path=str(SCREENSHOT_PATH))
        assert_no_overflow(page)
        browser.close()
    assert not errors, errors

    audit = {
        "url": URL,
        "status": "SCRIPT_RECORDED_PASS",
        "slice": "VGP §7.2 host resize reconciliation — declared center-"
        "preservation anchor policy over batch-65 bootstrap/stable owner",
        "bootstrap_resize_skipped": bootstrap,
        "resize_anchor_center_preserved": anchor,
        "stored_viewport_survives_switch": survived,
        "errors": {"console": [], "page": [], "request": []},
    }
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    print(
        "Batch 438 Playwright verification passed: bootstrap-phase resize "
        "skipped and logged, stable-phase host resize keeps zoom and "
        "preserves the flow point under the host center, reconciled "
        "viewport survives switch, browser diagnostics clean."
    )


if __name__ == "__main__":
    main()
