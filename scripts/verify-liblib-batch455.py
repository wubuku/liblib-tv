#!/usr/bin/env python3
"""Verify Batch 455: VR-021 Slice E — shot source lifecycle.

Contract: docs/research/LIBTV_MEDIA_INGRESS_RESOURCE_LIFECYCLE_CONTRACT.md
§9.2 SHOT_SOURCE_UPLOAD states (EMPTY / LOCAL_PREVIEW / MATERIALIZING /
DURABLE_READY / SESSION_READY / FAILED), Slice E ("local-preview versus
durable/session-ready states; graph-media reference mode; source-version
freeze and aggregate reset; no provider run").

Implementation:
- reduceLibTVShotSourceLifecycle (pure reducer, libtvMediaIngress.ts):
  frozen sourceRef {mediaId, mediaRevision}, aggregate reset on source
  change, stable invalid-transition reasons;
- VideoNode createBreakdown + ShotBreakdownNode upload now mark the
  source LOCAL_PREVIEW (a component URL alone is not durable readiness)
  and freeze sourceRef.

Scenes:
- lifecycle_unit: main transition chain, source-change aggregate reset,
  invalid transitions stably rejected;
- fixture_local_preview: a real 逐帧拉片 derivation carries status
  local-preview and a frozen sourceRef.
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
    / "liblib-canvas-batch455-2026-09-14"
    / "runtime-audit.json"
)
SCREENSHOT_PATH = (
    ROOT
    / "docs"
    / "design-references"
    / "liblib-clone-batch455-shot-lifecycle-929-2026-09-14.png"
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


def run_lifecycle_unit(page: Page):
    result = page.evaluate(
        """() => {
          const reduce = window.__libtv_shot_source_reduce;
          const empty = { state: 'EMPTY', sourceRef: null };
          const preview = reduce(empty, {
            type: 'preview-acquired', mediaId: 'poster-a.png', mediaRevision: 1,
          });
          const materializing = reduce(preview, { type: 'materialize-started' });
          const durable = reduce(materializing, { type: 'materialized-durable' });
          const session = reduce(durable, { type: 'session-acquired' });
          const failed = reduce(materializing, {
            type: 'materialize-failed', reason: 'DECODE_ERROR',
          });
          // aggregate reset: a new source identity restarts the lifecycle
          const changed = reduce(durable, {
            type: 'preview-acquired', mediaId: 'poster-b.png', mediaRevision: 2,
          });
          const badStart = reduce(session, { type: 'materialize-started' });
          const badDurable = reduce(preview, { type: 'materialized-durable' });
          return {
            previewState: preview.state,
            previewRef: preview.sourceRef,
            materializingState: materializing.state,
            durableState: durable.state,
            sessionState: session.state,
            failedState: failed.state,
            failedReason: failed.reason,
            changedState: changed.state,
            changedReason: changed.reason,
            changedRefMediaId: changed.sourceRef?.mediaId,
            badStart: badStart.reason,
            badDurable: badDurable.reason,
          };
        }"""
    )
    assert result["previewState"] == "LOCAL_PREVIEW"
    assert result["previewRef"]["mediaId"] == "poster-a.png"
    assert result["materializingState"] == "MATERIALIZING"
    assert result["durableState"] == "DURABLE_READY"
    assert result["sessionState"] == "SESSION_READY"
    assert result["failedState"] == "FAILED"
    assert result["failedReason"] == "DECODE_ERROR"
    assert result["changedState"] == "LOCAL_PREVIEW"
    assert result["changedReason"] == "SOURCE_CHANGED_RESET"
    assert result["changedRefMediaId"] == "poster-b.png"
    assert result["badStart"] == "NOT_DURABLE_READY" or result["badStart"] in (
        "NOT_IN_LOCAL_PREVIEW",
        "NOT_MATERIALIZING",
    )
    assert result["badDurable"] in ("NOT_MATERIALIZING", "NOT_IN_LOCAL_PREVIEW")
    return result


def run_fixture_local_preview(page: Page):
    page.get_by_role("button", name="添加节点").click()
    page.locator('[data-add-node-entry="video"]').click()
    page.wait_for_timeout(220)
    source = page.locator(".react-flow__node-video.selected")
    assert source.count() == 1
    source_id = source.get_attribute("data-id")
    page.locator('button:has-text("逐帧拉片")').first.click()
    page.wait_for_function(
        """(sourceId) => {
          const state = window.__libtv_store.getState();
          const canvas = state.getActiveCanvas();
          return canvas.nodes.some(
            (n) =>
              n.type === 'shot-breakdown' &&
              canvas.edges.some(
                (e) => e.source === sourceId && e.target === n.id,
              ),
          );
        }""",
        arg=source_id,
        timeout=5000,
    )
    breakdown = page.evaluate(
        """(sourceId) => {
          const state = window.__libtv_store.getState();
          const canvas = state.getActiveCanvas();
          const node = canvas.nodes.find(
            (n) =>
              n.type === 'shot-breakdown' &&
              canvas.edges.some(
                (e) => e.source === sourceId && e.target === n.id,
              ),
          );
          return node
            ? {
                status: node.data.status,
                sourceRef: node.data.sourceRef ?? null,
                sourceName: node.data.sourceName ?? null,
              }
            : null;
        }""",
        arg=source_id,
    )
    assert breakdown, "derived shot-breakdown node must exist"
    assert breakdown["status"] == "local-preview", breakdown
    assert breakdown["sourceRef"], breakdown
    assert breakdown["sourceRef"]["mediaRevision"] >= 1
    assert breakdown["sourceName"], breakdown
    return breakdown


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

        unit = run_lifecycle_unit(page)

        page.evaluate(
            "() => window.__libtv_store.getState().setActiveCanvas('canvas-1')"
        )
        page.wait_for_timeout(320)
        fixture = run_fixture_local_preview(page)

        page.screenshot(path=str(SCREENSHOT_PATH))
        assert_no_overflow(page)
        browser.close()
    assert not errors, errors

    audit = {
        "url": URL,
        "status": "SCRIPT_RECORDED_PASS",
        "slice": "VR-021 Slice E — shot source lifecycle (§9.2 states, "
        "frozen sourceRef, aggregate reset)",
        "lifecycle_unit": unit,
        "fixture_local_preview": fixture,
        "errors": {"console": [], "page": [], "request": []},
    }
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    print(
        "Batch 455 Playwright verification passed: §9.2 lifecycle chain "
        "EMPTY->LOCAL_PREVIEW->MATERIALIZING->DURABLE_READY->SESSION_READY "
        "and FAILED, source-change aggregate reset, invalid transitions "
        "stably rejected; a real 逐帧拉片 derivation freezes a local-preview "
        "sourceRef, diagnostics clean."
    )


if __name__ == "__main__":
    main()
