#!/usr/bin/env python3
"""Verify Batch 441: VR-023 Slice A — dimension-authority classification
with observable conflicts, no visual change.

Contract: docs/research/LIBTV_MEDIA_RENDITION_GEOMETRY_CONTRACT.md
§3 conceptual descriptors, GI-102 (intrinsic / request / node-frame /
measured / export-frame are distinct authorities), Slice A ("typed
conceptual helpers/field classification; make frame conflicts observable
in diagnostics; no provider, output history or resize UI").

Implementation:
- src/lib/libtvMediaDimensionAuthority.ts — pure classifier, display-string
  parser and conflict detector;
- src/app/page.tsx — read-only window diagnostics over the canvas graph.

Scenes:
- pure_classification: field table + display-string parsing;
- fixture_scan_readonly: scanning the fixture produces conflicts with the
  expected kinds and mutates nothing;
- derived_generic_frame_detection: a real smart-matting derived node
  (generic 512x288 frame) sourced from a 1:1 image is flagged.
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
    / "liblib-canvas-batch441-2026-09-13"
    / "runtime-audit.json"
)
SCREENSHOT_PATH = (
    ROOT
    / "docs"
    / "design-references"
    / "liblib-clone-batch441-dimension-authorities-929-2026-09-13.png"
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


def graph_snapshot(page: Page):
    return page.evaluate(
        """() => JSON.stringify(window.__libtv_store.getState().canvases)"""
    )


def run_pure_classification(page: Page):
    result = page.evaluate(
        """() => {
          const classify = window.__libtv_classify_dimension_field;
          const parse = window.__libtv_parse_display_dimensions;
          return {
            width: classify("width"),
            resolution: classify("resolution"),
            generationSettings: classify("generationSettings"),
            editorHeight: classify("editorHeight"),
            mystery: classify("mystery"),
            parsed: parse("1280 × 720"),
            parsedAlt: parse("622x350"),
            parsedJunk: parse("not-a-size"),
          };
        }"""
    )
    assert result["width"] == {
        "field": "width",
        "authority": "intrinsic",
        "kind": "dimensions",
    }, result
    assert result["resolution"]["authority"] == "intrinsic"
    assert result["resolution"]["kind"] == "display-string"
    assert result["generationSettings"]["authority"] == "request"
    assert result["editorHeight"]["authority"] == "unknown"
    assert result["mystery"]["authority"] == "unknown"
    assert result["parsed"] == {"width": 1280, "height": 720}, result
    assert result["parsedAlt"] == {"width": 622, "height": 350}, result
    assert result["parsedJunk"] is None
    return result


def run_fixture_scan_readonly(page: Page):
    before = graph_snapshot(page)
    conflicts = page.evaluate(
        "() => window.__libtv_detect_dimension_conflicts('canvas-2')"
    )
    after = graph_snapshot(page)
    assert before == after, "scan must be read-only"

    for conflict in conflicts:
        assert set(conflict) == {"nodeId", "kind", "detail"}, conflict

    image_conflicts = [
        c for c in conflicts if c["kind"] == "request-display-string-only"
    ]
    video_conflicts = [
        c for c in conflicts if c["kind"] == "intrinsic-display-string-only"
    ]
    assert image_conflicts, "fixture image nodes must surface the request "
    "display-string diagnostic"
    assert video_conflicts, "fixture video nodes must surface the intrinsic "
    "display-string diagnostic"
    return {"total": len(conflicts), "byKind": {
        kind: len([c for c in conflicts if c["kind"] == kind])
        for kind in {c["kind"] for c in conflicts}
    }}


def run_derived_generic_frame_detection(page: Page):
    conflicts_before = page.evaluate(
        "() => window.__libtv_detect_dimension_conflicts('canvas-2')"
    )
    flagged_before = {
        c["nodeId"]
        for c in conflicts_before
        if c["kind"] == "derived-frame-generic-default"
    }
    result_id = page.evaluate(
        """() => {
          const state = window.__libtv_store.getState();
          const canvas = state.getActiveCanvas();
          const genericRatio = 512 / 288;
          const image = canvas.nodes.find(
            (node) => node.type === "image" &&
              typeof node.data?.width === "number" &&
              typeof node.data?.height === "number" &&
              Math.abs(
                node.data.width / node.data.height - genericRatio,
              ) / genericRatio > 0.02,
          );
          if (!image) return null;
          return state.createSmartMatting(image.id);
        }"""
    )
    assert result_id, (
        "fixture needs an image node whose intrinsic ratio differs from the "
        "generic 512x288 frame"
    )
    conflicts_after = page.evaluate(
        "() => window.__libtv_detect_dimension_conflicts('canvas-2')"
    )
    flagged_after = {
        c["nodeId"]
        for c in conflicts_after
        if c["kind"] == "derived-frame-generic-default"
    }
    assert result_id in flagged_after, (
        result_id,
        "derived node with generic 512x288 frame from a 1:1 source must be "
        "flagged",
    )
    return {
        "derivedNodeId": result_id,
        "flagged": True,
        "newConflictKinds": sorted(
            c["kind"]
            for c in conflicts_after
            if c["nodeId"] == result_id
        ),
        "previouslyFlaggedCount": len(flagged_before),
    }


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

        pure = run_pure_classification(page)
        scan = run_fixture_scan_readonly(page)
        derived = run_derived_generic_frame_detection(page)
        page.screenshot(path=str(SCREENSHOT_PATH))
        assert_no_overflow(page)
        browser.close()
    assert not errors, errors

    audit = {
        "url": URL,
        "status": "SCRIPT_RECORDED_PASS",
        "slice": "VR-023 Slice A — dimension-authority classification and "
        "observable conflicts (GI-102), diagnostics only",
        "pure_classification": pure,
        "fixture_scan_readonly": scan,
        "derived_generic_frame_detection": derived,
        "errors": {"console": [], "page": [], "request": []},
    }
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    print(
        "Batch 441 Playwright verification passed: field classification and "
        "display-string parsing exact, fixture scan read-only with expected "
        "conflict kinds, smart-matting derived node flagged for the generic "
        "512x288 frame against a 1:1 source, browser diagnostics clean."
    )


if __name__ == "__main__":
    main()
