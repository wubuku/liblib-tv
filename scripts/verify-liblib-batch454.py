#!/usr/bin/env python3
"""Verify Batch 454: VR-021 Slice D — generated-history / registered-asset
reference attach.

Contract: docs/research/LIBTV_MEDIA_INGRESS_RESOURCE_LIFECYCLE_CONTRACT.md
Slice D ("preserve separate surfaces/provenance; local fixture data only;
no account/backend claim") + §5 profiles (GENERATED_HISTORY_ATTACH 1..10
immediate atomic stable-reference; REGISTERED_ASSET_ATTACH 1..N immediate
atomic alias/reference).

Implementation: canvasStore.attachAssetReferences — STABLE_ASSET_REFERENCE
nodes with per-surface provenance, one graph transaction per attach,
already-referenced assetIds skipped without mutation.

Scenes (empty canvas-1):
- registered_attach_accepted: three registered assets -> three
  STABLE_ASSET_REFERENCE nodes, one history entry, provenance recorded;
- resubmit_skips_referenced: re-attaching the same three plus one new
  asset skips the three and attaches only the new one (still one
  transaction, one history entry);
- cardinality_and_generation_rejections: 11 history assets exceed the
  profile cap; a stale generation is MEDIA_CANVAS_STALE — both zero
  mutation.
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
    / "liblib-canvas-batch454-2026-09-13"
    / "runtime-audit.json"
)
SCREENSHOT_PATH = (
    ROOT
    / "docs"
    / "design-references"
    / "liblib-clone-batch454-asset-references-929-2026-09-13.png"
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

        page.evaluate(
            "() => window.__libtv_store.getState().setActiveCanvas('canvas-1')"
        )
        page.wait_for_timeout(320)

        scenes = page.evaluate(
            """() => {
              const state = window.__libtv_store.getState();
              const gen = state.canvasGeneration;
              const attach = (profileId, assets, g = gen) =>
                state.attachAssetReferences(profileId, assets, g);
              const assets = [
                { assetId: 'hist-1', renderUrl: '/images/scene-coffee-1.png', mediaFamily: 'image' },
                { assetId: 'hist-2', renderUrl: '/images/scene-coffee-4.png', mediaFamily: 'image' },
                { assetId: 'reg-1', renderUrl: '/images/watermark.png', mediaFamily: 'image' },
              ];
              const canvasState = () => {
                const s = window.__libtv_store.getState();
                const canvas = s.canvases.find((c) => c.id === 'canvas-1');
                const history = s.historyByCanvas['canvas-1']
                  || { past: [], future: [] };
                const refs = (canvas?.nodes ?? []).map(
                  (n) => n.data?.mediaReference,
                );
                return {
                  nodeCount: (canvas?.nodes ?? []).length,
                  pastLength: history.past.length,
                  provenance: Array.from(
                    new Set(refs.map((r) => r?.provenance ?? '')),
                  ).sort(),
                  referenceCount: refs.filter(Boolean).length,
                };
              };
              const out = {};
              out.before = canvasState();
              const first = attach('REGISTERED_ASSET_ATTACH', assets);
              out.first = {
                status: first.status,
                attached: first.attachedAssetIds,
                skipped: first.skippedAssetIds,
                after: canvasState(),
              };
              const resubmit = attach('REGISTERED_ASSET_ATTACH', [
                ...assets,
                { assetId: 'reg-2', renderUrl: '/images/scene-coffee-1.png', mediaFamily: 'image' },
              ]);
              out.resubmit = {
                status: resubmit.status,
                attached: resubmit.attachedAssetIds,
                skipped: resubmit.skippedAssetIds,
                after: canvasState(),
              };
              const oversized = attach('GENERATED_HISTORY_ATTACH',
                Array.from({ length: 11 }, (_, i) => ({
                  assetId: 'h' + i,
                  renderUrl: '/images/scene-coffee-1.png',
                  mediaFamily: 'image',
                })));
              out.cardinality = {
                status: oversized.status,
                reasons: oversized.reasons,
                after: canvasState(),
              };
              const stale = attach('GENERATED_HISTORY_ATTACH',
                [{ assetId: 'hx', renderUrl: '/x.png', mediaFamily: 'image' }],
                gen - 1);
              out.stale = {
                status: stale.status,
                reasons: stale.reasons,
                after: canvasState(),
              };
              return out;
            }"""
        )
        browser.close()

    assert scenes["first"]["status"] == "accepted"
    assert scenes["first"]["attached"] == ["hist-1", "hist-2", "reg-1"]
    assert scenes["first"]["after"]["nodeCount"] == 3
    assert scenes["first"]["after"]["pastLength"] == 1
    assert scenes["first"]["after"]["provenance"] == ["REGISTERED_ASSET_ATTACH"]

    assert scenes["resubmit"]["status"] == "accepted"
    assert scenes["resubmit"]["attached"] == ["reg-2"]
    assert sorted(scenes["resubmit"]["skipped"]) == ["hist-1", "hist-2", "reg-1"]
    assert scenes["resubmit"]["after"]["nodeCount"] == 4
    assert scenes["resubmit"]["after"]["pastLength"] == 2

    assert scenes["cardinality"]["status"] == "rejected"
    assert scenes["cardinality"]["reasons"] == ["MEDIA_CARDINALITY_EXCEEDED"]
    assert scenes["cardinality"]["after"]["nodeCount"] == 4
    assert scenes["cardinality"]["after"]["pastLength"] == 2

    assert scenes["stale"]["status"] == "rejected"
    assert scenes["stale"]["reasons"] == ["MEDIA_CANVAS_STALE"]
    assert scenes["stale"]["after"]["nodeCount"] == 4

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(
            viewport={"width": 929, "height": 874}, device_scale_factor=1
        )
        errors.extend(attach_errors(page))
        page.goto(URL, wait_until="networkidle")
        page.wait_for_timeout(450)
        page.screenshot(path=str(SCREENSHOT_PATH))
        assert_no_overflow(page)
        browser.close()
    assert not errors, errors

    audit = {
        "url": URL,
        "status": "SCRIPT_RECORDED_PASS",
        "slice": "VR-021 Slice D — generated-history/registered-asset "
        "reference attach (stable references, per-surface provenance, "
        "skip-duplicates, one transaction per attach)",
        "scenes": scenes,
        "errors": {"console": [], "page": [], "request": []},
    }
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    print(
        "Batch 454 Playwright verification passed: registered-asset attach "
        "creates stable-reference nodes with per-surface provenance in one "
        "transaction, referenced assetIds are skipped on resubmit, "
        "cardinality and stale-generation rejections leave zero mutation, "
        "diagnostics clean."
    )


if __name__ == "__main__":
    main()
