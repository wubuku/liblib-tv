#!/usr/bin/env python3
"""Verify Batch 450: VR-021 Slice A — pure media-ingress descriptors,
entry-profile registry and ordered validation with stable reasons.

Contract: docs/research/LIBTV_MEDIA_INGRESS_RESOURCE_LIFECYCLE_CONTRACT.md
§5 ten named entry profiles, §8.1 validation order (client-pure steps 1-6),
§8.2 profile registry requirements (clone-only fixture budgets), §8.3
stable reason family. Slice A is pure: no UI/store integration.

Scenes:
- registry: ten declared entry profiles with cardinality/policy;
- accepted_intent: a valid ADD_RESOURCE_MULTI image upload is accepted;
- ordered_rejections: empty list, unknown profile, cardinality overflow,
  stale canvas, missing canvas, invalid descriptor, ambiguous type,
  unsupported family and oversized bytes each surface their stable
  reason (multiple reasons reported in validation order).
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
    / "liblib-canvas-batch450-2026-09-13"
    / "runtime-audit.json"
)
SCREENSHOT_PATH = (
    ROOT
    / "docs"
    / "design-references"
    / "liblib-clone-batch450-ingress-registry-929-2026-09-13.png"
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
          const profiles = window.__libtv_media_ingress_profiles;
          const validate = window.__libtv_media_ingress_validate;
          const file = (over = {}) => ({
            kind: 'LOCAL_FILE',
            name: 'sample.png',
            declaredMimeType: 'image/png',
            sizeBytes: 1024,
            lastModified: 1,
            ...over,
          });
          const base = {
            canvasExists: true,
            canvasGeneration: 3,
            expectedCanvasGeneration: 3,
          };
          const out = {};

          out.profileCount = Object.keys(profiles).length;
          out.gatedCardinality =
            profiles.GENERATED_HISTORY_ATTACH.cardinalityMax;

          out.accepted = validate({
            ...base,
            profileId: 'ADD_RESOURCE_MULTI',
            descriptors: [file()],
          });

          out.empty = validate({
            ...base,
            profileId: 'ADD_RESOURCE_MULTI',
            descriptors: [],
          });

          out.unknownProfile = validate({
            ...base,
            profileId: 'NOT_A_PROFILE',
            descriptors: [file()],
          });

          out.cardinality = validate({
            ...base,
            profileId: 'GENERATED_HISTORY_ATTACH',
            descriptors: Array.from({ length: 11 }, () => file()),
          });

          out.staleCanvas = validate({
            ...base,
            expectedCanvasGeneration: 2,
            profileId: 'ADD_RESOURCE_MULTI',
            descriptors: [file()],
          });

          out.missingCanvas = validate({
            ...base,
            canvasExists: false,
            profileId: 'ADD_RESOURCE_MULTI',
            descriptors: [file()],
          });

          out.invalidDescriptor = validate({
            ...base,
            profileId: 'ADD_RESOURCE_MULTI',
            descriptors: [file({ name: '', sizeBytes: Number.NaN })],
          });

          out.emptyFile = validate({
            ...base,
            profileId: 'ADD_RESOURCE_MULTI',
            descriptors: [file({ sizeBytes: 0 })],
          });

          out.ambiguousType = validate({
            ...base,
            profileId: 'ADD_RESOURCE_MULTI',
            descriptors: [
              file({ name: 'thing.bin', declaredMimeType: 'application/x-unknown' }),
            ],
          });

          out.unsupportedFamily = validate({
            ...base,
            profileId: 'ADD_RESOURCE_MULTI',
            descriptors: [
              // director-model family has no ordinary-upload budget
              file({
                name: 'model.blend',
                declaredMimeType: 'application/octet-stream',
                sizeBytes: 5,
              }),
            ],
          });

          out.oversized = validate({
            ...base,
            profileId: 'ADD_RESOURCE_MULTI',
            descriptors: [
              file({ sizeBytes: 21 * 1024 * 1024 }),
            ],
          });

          out.orderedReasons = validate({
            ...base,
            expectedCanvasGeneration: 9,
            profileId: 'GENERATED_HISTORY_ATTACH',
            descriptors: [file({ sizeBytes: 0 }), file({ sizeBytes: -1 })],
          });

          return out;
        }"""
    )


def assert_scenes(out):
    assert out["profileCount"] == 10, out
    assert out["gatedCardinality"] == 10, out

    assert out["accepted"]["status"] == "accepted", out["accepted"]
    assert out["accepted"]["family"] == "image"
    assert out["accepted"]["reasons"] == []

    assert out["empty"]["reasons"] == ["MEDIA_EMPTY"], out["empty"]
    assert out["unknownProfile"]["reasons"] == ["MEDIA_ENTRY_PROFILE_INVALID"]
    assert out["cardinality"]["reasons"] == ["MEDIA_CARDINALITY_EXCEEDED"]
    assert out["staleCanvas"]["reasons"] == ["MEDIA_CANVAS_STALE"]
    assert out["missingCanvas"]["reasons"] == ["MEDIA_TARGET_MISSING"]
    assert out["invalidDescriptor"]["reasons"] == [
        "MEDIA_SOURCE_DESCRIPTOR_INVALID"
    ]
    assert out["emptyFile"]["reasons"] == ["MEDIA_EMPTY"]
    assert out["ambiguousType"]["reasons"] == ["MEDIA_TYPE_AMBIGUOUS"]
    assert out["unsupportedFamily"]["reasons"] == ["MEDIA_TYPE_UNSUPPORTED"]
    assert out["unsupportedFamily"]["status"] == "rejected"
    assert out["oversized"]["reasons"] == ["MEDIA_SIZE_EXCEEDED"]
    # ordered multi-reason report: stale canvas first, then empty files
    assert out["orderedReasons"]["reasons"] == [
        "MEDIA_CANVAS_STALE",
        "MEDIA_EMPTY",
        "MEDIA_SOURCE_DESCRIPTOR_INVALID",
    ], out["orderedReasons"]


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
        "slice": "VR-021 Slice A — pure ingress descriptors, entry-profile "
        "registry, ordered validation with stable reasons",
        "scenes": scenes,
        "errors": {"console": [], "page": [], "request": []},
    }
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    print(
        "Batch 450 Playwright verification passed: ten-profile ingress "
        "registry, accepted valid intent, and every §8.1 client rejection "
        "surfaces its stable reason in validation order, diagnostics clean."
    )


if __name__ == "__main__":
    main()
