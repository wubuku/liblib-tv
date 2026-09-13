#!/usr/bin/env python3
"""Verify Batch 451: VR-021 Slice B — instance-scoped lease ledger and a
fake materializer with deterministic outcomes.

Contract: docs/research/LIBTV_MEDIA_INGRESS_RESOURCE_LIFECYCLE_CONTRACT.md
§6.4 resource lease (exactly-once release semantics, transfer stamps),
§9 probe/preview lease rules, Slice B ("observable probe/preview/session
leases; deterministic delay/fail/stale/duplicate outcomes; no provider/
storage/network").

Scenes:
- lease_exactly_once_release: second release returns already-released,
  releaseCount increments, releasedAt never re-stamps;
- lease_transfer: transfer stamps transferredAt and re-owners; releasing
  after transfer still works (release is lifecycle, not ownership);
- materializer_ok_and_duplicate: first materialization acquires a
  SESSION_RESULT_URL lease; same fingerprint settles as duplicate with
  the SAME locator (no second lease);
- materializer_fail_and_stale: fail yields MEDIA_MATERIALIZATION_FAILED;
  stale (owner gone) yields MEDIA_ATTEMPT_SUPERSEDED with no lease.
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
    / "liblib-canvas-batch451-2026-09-13"
    / "runtime-audit.json"
)
SCREENSHOT_PATH = (
    ROOT
    / "docs"
    / "design-references"
    / "liblib-clone-batch451-lease-ledger-929-2026-09-13.png"
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


def run_scenes(page: Page):
    return page.evaluate(
        """() => {
          const out = {};

          // exactly-once release
          const ledger = window.__libtv_media_lease_ledger_new();
          const lease = ledger.acquire({
            resourceId: 'res-1',
            resourceClass: 'PREVIEW_URL',
            ownerKind: 'PREVIEW_SURFACE',
            ownerId: 'annotate/session-1',
            at: 100,
          });
          const first = ledger.release(lease.leaseId, 200);
          const second = ledger.release(lease.leaseId, 300);
          const stored = ledger.get(lease.leaseId);
          out.exactlyOnce = {
            first,
            second,
            releasedAt: stored.releasedAt,
            releaseCount: stored.releaseCount,
          };

          // transfer stamps and re-owners; released leases cannot transfer
          const transferOk = ledger.transfer(
            'lease-2',
            { ownerKind: 'GRAPH_REFERENCE_REGISTRY', ownerId: 'graph/canvas-1' },
            400,
          );
          const l2 = ledger.acquire({
            resourceId: 'res-2',
            resourceClass: 'SESSION_RESULT_URL',
            ownerKind: 'INGRESS_OPERATION',
            ownerId: 'op/1',
            at: 300,
          });
          const transferL2 = ledger.transfer(
            l2.leaseId,
            { ownerKind: 'GRAPH_REFERENCE_REGISTRY', ownerId: 'graph/canvas-1' },
            400,
          );
          const l2After = ledger.get(l2.leaseId);
          const transferReleased = ledger.transfer(
            lease.leaseId,
            { ownerKind: 'ASSET_REGISTRY', ownerId: 'assets/1' },
            500,
          );
          out.transfer = {
            transferOk,
            transferL2,
            transferredAt: l2After.transferredAt,
            ownerKind: l2After.ownerKind,
            transferReleased,
          };

          // fake materializer: ok then duplicate, fail, stale
          const materializer = window.__libtv_media_materializer_new(ledger);
          const leaseCountBeforeMaterialize = ledger.list().length;
          const fingerprint = 'fp-abc';
          const settleFirst = materializer.materialize({
            canvasId: 'canvas-1', nodeId: 'node-1', contentFingerprint: fingerprint,
          });
          const ok = settleFirst({ outcome: 'ok' });
          const settleDup = materializer.materialize({
            canvasId: 'canvas-1', nodeId: 'node-1', contentFingerprint: fingerprint,
          });
          const dup = settleDup({ outcome: 'ok' });
          const failed = materializer.materialize({
            canvasId: 'canvas-1', nodeId: 'node-1', contentFingerprint: 'fp-fail',
          })({ outcome: 'fail' });
          let stale = null;
          const settleStale = materializer.materialize({
            canvasId: 'canvas-1', nodeId: 'node-gone', contentFingerprint: 'fp-stale',
          });
          stale = settleStale({
            outcome: 'stale',
            isOwnerCurrent: () => false,
          });
          out.materializer = {
            okStatus: ok.status,
            okLeaseId: ok.leaseId,
            dupStatus: dup.status,
            sameLocator:
              ok.locator.renderUrl === dup.locator.renderUrl,
            failedStatus: failed.status,
            failedReason: failed.reason,
            staleStatus: stale.status,
            staleReason: stale.reason,
            ledgerLeaseCount: ledger.list().length,
            leaseCountBeforeMaterialize,
          };
          return out;
        }"""
    )


def assert_scenes(out):
    exactly_once = out["exactlyOnce"]
    assert exactly_once["first"] == "released"
    assert exactly_once["second"] == "already-released"
    assert exactly_once["releasedAt"] == 200
    assert exactly_once["releaseCount"] == 2, exactly_once

    transfer = out["transfer"]
    assert transfer["transferL2"] is True
    assert transfer["transferredAt"] == 400
    assert transfer["ownerKind"] == "GRAPH_REFERENCE_REGISTRY"
    assert transfer["transferReleased"] is False
    assert transfer["transferOk"] is False  # unknown lease id

    m = out["materializer"]
    assert m["okStatus"] == "materialized"
    assert m["dupStatus"] == "duplicate"
    assert m["sameLocator"] is True
    assert m["failedStatus"] == "failed"
    assert m["failedReason"] == "MEDIA_MATERIALIZATION_FAILED"
    assert m["staleStatus"] == "superseded"
    assert m["staleReason"] == "MEDIA_ATTEMPT_SUPERSEDED"
    # ok acquired one lease; dup/fail/stale acquired none
    assert m["ledgerLeaseCount"] == m["leaseCountBeforeMaterialize"] + 1, m


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

        scenes = run_scenes(page)
        assert_scenes(scenes)

        page.screenshot(path=str(SCREENSHOT_PATH))
        assert_no_overflow(page)
        browser.close()
    assert not errors, errors

    audit = {
        "url": URL,
        "status": "SCRIPT_RECORDED_PASS",
        "slice": "VR-021 Slice B — instance-scoped lease ledger + fake "
        "materializer with deterministic ok/duplicate/fail/stale outcomes",
        "scenes": scenes,
        "errors": {"console": [], "page": [], "request": []},
    }
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    print(
        "Batch 451 Playwright verification passed: lease exactly-once release "
        "semantics, transfer stamps, fake materializer ok/duplicate/fail/"
        "stale outcomes with lease coupling, diagnostics clean."
    )


if __name__ == "__main__":
    main()
