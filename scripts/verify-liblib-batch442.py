#!/usr/bin/env python3
"""Verify Batch 442: VR-023 Slice B — deterministic frame/rendition policy.

Contract: docs/research/LIBTV_MEDIA_RENDITION_GEOMETRY_CONTRACT.md Slice B
("preserve current source-backed landscape fixtures; make generic square
and portrait outputs aspect-aware").

Implementation (src/store/canvasStore.ts + src/lib/libtvMediaDimensionAuthority.ts):
- getDerivedFrameDimensions() applies planLibTVAspectAwareDerivedFrame() to
  derived image/video frames: landscape (16:9-class, ±2%) sources keep the
  generic 512x288 frame; any other intrinsic ratio derives a frame at the
  same profile height with width rounded from the ratio (clamped 160..640);
  outside the clamp the generic frame is kept (and the batch-441 detector
  flags it again — policy/detector coherence).

Scenes (injected sources on the empty canvas-1):
- square 512x512 -> 288x288, portrait 720x1280 -> 162x288,
- landscape 1280x720 -> generic 512x288 preserved,
- extreme 360x1440 -> generic fallback AND flagged by the detector,
- video source with a portrait resolution display string -> 162x288.
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
    / "liblib-canvas-batch442-2026-09-13"
    / "runtime-audit.json"
)
SCREENSHOT_PATH = (
    ROOT
    / "docs"
    / "design-references"
    / "liblib-clone-batch442-aspect-aware-frames-929-2026-09-13.png"
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


def inject_source(page: Page, node: dict):
    page.evaluate(
        """(node) => {
          window.__libtv_store.setState((state) => ({
            canvases: state.canvases.map((canvas) =>
              canvas.id === 'canvas-1'
                ? { ...canvas, nodes: [...canvas.nodes, node] }
                : canvas,
            ),
          }));
        }""",
        node,
    )


def derive_from(page: Page, source_id: str, derived_type: str):
    return page.evaluate(
        """({sourceId, type}) => {
          const state = window.__libtv_store.getState();
          state.addDerivedNode(sourceId, type);
          const fresh = window.__libtv_store.getState();
          const canvas = fresh.canvases.find((item) => item.id === 'canvas-1');
          const edge = canvas.edges.find(
            (edge) => edge.source === sourceId &&
              edge.target !== undefined,
          );
          if (!edge) return null;
          const derived = canvas.nodes.find((node) => node.id === edge.target);
          return derived
            ? { id: derived.id, width: derived.width, height: derived.height }
            : null;
        }""",
        {"sourceId": source_id, "type": derived_type},
    )


def conflicts_for(page: Page, node_id: str):
    return page.evaluate(
        """(nodeId) =>
          window.__libtv_detect_dimension_conflicts('canvas-1').filter(
            (conflict) => conflict.nodeId === nodeId,
          )
        """,
        node_id,
    )


def run_frame_policy_scene(
    page: Page,
    label: str,
    source: dict,
    derived_type: str,
    expected_frame: dict,
    expect_generic_conflict: bool,
):
    inject_source(page, source)
    derived = derive_from(page, source["id"], derived_type)
    assert derived, (label, "derived node must be created")
    assert derived["width"] == expected_frame["width"], (label, derived)
    assert derived["height"] == expected_frame["height"], (label, derived)
    conflicts = conflicts_for(page, derived["id"])
    flagged = any(
        c["kind"] == "derived-frame-generic-default" for c in conflicts
    )
    assert flagged is expect_generic_conflict, (label, conflicts)
    return {
        "label": label,
        "source": source["id"],
        "derivedType": derived_type,
        "frame": {"width": derived["width"], "height": derived["height"]},
        "genericConflictFlagged": flagged,
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

        # switch to the empty canvas so injected sources stay isolated
        page.evaluate(
            "() => window.__libtv_store.getState().setActiveCanvas('canvas-1')"
        )
        page.wait_for_timeout(320)

        results = [
            run_frame_policy_scene(
                page,
                "square-source-aspect-aware",
                {
                    "id": "src-square",
                    "type": "image",
                    "position": {"x": 0, "y": 0},
                    "data": {"filename": "sq", "width": 512, "height": 512},
                },
                "image",
                {"width": 288, "height": 288},
                False,
            ),
            run_frame_policy_scene(
                page,
                "portrait-source-aspect-aware",
                {
                    "id": "src-portrait",
                    "type": "image",
                    "position": {"x": 0, "y": 400},
                    "data": {"filename": "pt", "width": 720, "height": 1280},
                },
                "image",
                {"width": 162, "height": 288},
                False,
            ),
            run_frame_policy_scene(
                page,
                "landscape-source-preserves-generic",
                {
                    "id": "src-landscape",
                    "type": "image",
                    "position": {"x": 0, "y": 800},
                    "data": {
                        "filename": "ls",
                        "width": 1280,
                        "height": 720,
                    },
                },
                "image",
                {"width": 512, "height": 288},
                False,
            ),
            run_frame_policy_scene(
                page,
                "extreme-ratio-generic-fallback-flagged",
                {
                    "id": "src-extreme",
                    "type": "image",
                    "position": {"x": 0, "y": 1200},
                    "data": {"filename": "xt", "width": 360, "height": 1440},
                },
                "image",
                {"width": 512, "height": 288},
                True,
            ),
            run_frame_policy_scene(
                page,
                "video-display-string-portrait",
                {
                    "id": "src-video-portrait",
                    "type": "video",
                    "position": {"x": 0, "y": 1600},
                    "data": {
                        "filename": "vt",
                        "resolution": "720 × 1280",
                    },
                },
                "video",
                {"width": 162, "height": 288},
                False,
            ),
        ]

        page.evaluate(
            "() => window.__libtv_store.getState().setActiveCanvas('canvas-2')"
        )
        page.wait_for_timeout(320)
        page.screenshot(path=str(SCREENSHOT_PATH))
        assert_no_overflow(page)
        browser.close()
    assert not errors, errors

    audit = {
        "url": URL,
        "status": "SCRIPT_RECORDED_PASS",
        "slice": "VR-023 Slice B — deterministic aspect-aware derived frame "
        "policy (landscape fixtures preserved)",
        "policy": {
            "landscapeTolerance": "±2% of the generic frame ratio",
            "frame": "same profile height, width rounded from the intrinsic "
            "ratio, clamped to 160..640",
            "fallback": "generic frame kept outside the clamp; detector "
            "flags it again (policy/detector coherence)",
        },
        "scenes": results,
        "errors": {"console": [], "page": [], "request": []},
    }
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    print(
        "Batch 442 Playwright verification passed: square/portrait sources "
        "derive aspect-aware frames (288x288 / 162x288), landscape sources "
        "keep the generic 512x288, extreme ratios fall back and are flagged, "
        "video display-string intrinsics drive the policy, diagnostics clean."
    )


if __name__ == "__main__":
    main()
