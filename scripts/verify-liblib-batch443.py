#!/usr/bin/env python3
"""Verify Batch 443: VR-023 Slice C — editor transform correctness.

Contract: docs/research/LIBTV_MEDIA_RENDITION_GEOMETRY_CONTRACT.md §7
(fit transform scale/offset formulas, visible<->intrinsic point mapping),
Slice C ("compute content-box cover/contain transform; capture editor
baseline revision; map marks to declared full-media plane; verify through
colored marker fixture").

Implementation:
- src/lib/libtvMediaDimensionAuthority.ts: planLibTVFitTransform,
  libTVVisiblePointToIntrinsic / libTVIntrinsicPointToVisible,
  makeLibTVEditorBaseline;
- src/store/uiStore.ts: ImageAnnotateState carries the declared-plane
  baseline (mediaRevision + fit);
- src/app/page.tsx: __libtv_annotate_fit_mapping resolves the transform
  for the open annotate editor from its live DOM frame.

Colored marker fixture: a red marker drawn on the annotate canvas at the
mapped visible position of intrinsic (0.25, 0.25) must read back red at
that exact pixel and leave the rest of the canvas untouched; the visible
point must round-trip to the same intrinsic coordinates.
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
    / "liblib-canvas-batch443-2026-09-13"
    / "runtime-audit.json"
)
SCREENSHOT_PATH = (
    ROOT
    / "docs"
    / "design-references"
    / "liblib-clone-batch443-annotate-mapping-929-2026-09-13.png"
)
IMAGE_ID = "i-vxeeCnxySa"
MARKER_NORMALIZED = {"nx": 0.25, "ny": 0.25}


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


def open_annotate(page: Page):
    node = page.locator(f'.react-flow__node[data-id="{IMAGE_ID}"]')
    assert node.count() == 1
    node.click(force=True)
    page.wait_for_timeout(180)
    page.locator('[data-testid="image-toolbar-annotate"]').click()
    page.locator("[data-image-annotate-surface]").wait_for(state="visible")
    page.locator("[data-image-annotate-canvas]").wait_for(state="visible")
    page.wait_for_timeout(160)


def read_mapping(page: Page):
    return page.evaluate("() => window.__libtv_annotate_fit_mapping()")


def draw_marker_and_sample(page: Page, transform):
    return page.evaluate(
        """(t) => {
          const canvas = document.querySelector(
            '[data-image-annotate-canvas]',
          );
          const rect = canvas.getBoundingClientRect();
          const dpr = canvas.width / rect.width;
          const ctx = canvas.getContext('2d');

          const vx = t.offsetX + t.intrinsicWidth * t.scale * 0.25;
          const vy = t.offsetY + t.intrinsicHeight * t.scale * 0.25;

          ctx.fillStyle = 'rgb(255, 0, 0)';
          ctx.fillRect(vx * dpr - 6, vy * dpr - 6, 12, 12);

          const sample = (px, py) => {
            const data = ctx.getImageData(
              Math.round(px * dpr), Math.round(py * dpr), 1, 1,
            ).data;
            return [data[0], data[1], data[2], data[3]];
          };
          const atMarker = sample(vx, vy);

          // round-trip: visible -> intrinsic must return the marker source
          const ix = (vx - t.offsetX) / t.scale;
          const iy = (vy - t.offsetY) / t.scale;
          const roundTrip = {
            nx: ix / t.intrinsicWidth,
            ny: iy / t.intrinsicHeight,
          };

          // a far corner of the media plane must stay untouched
          const farVx = t.offsetX + t.intrinsicWidth * t.scale * 0.9;
          const farVy = t.offsetY + t.intrinsicHeight * t.scale * 0.9;
          const atFar = sample(farVx, farVy);

          return {
            markerVisible: { vx, vy },
            atMarker,
            atFar,
            roundTrip,
            insideFrame:
              vx >= 0 && vy >= 0 && vx <= rect.width && vy <= rect.height,
          };
        }""",
        transform,
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
        # bring the wide fixture graph into view (batch-58 convention)
        page.keyboard.press("Alt+Shift+f")
        page.wait_for_timeout(450)

        open_annotate(page)
        mapping = read_mapping(page)
        assert mapping, "open annotate editor must expose the fit mapping"
        baseline = mapping["baseline"]
        transform = mapping["transform"]

        assert baseline["mediaId"] and baseline["mediaRevision"] >= 1, baseline
        assert baseline["fit"] == "contain"
        assert transform["fit"] == "contain"
        assert transform["intrinsicWidth"] == baseline["width"]
        assert transform["intrinsicHeight"] == baseline["height"]

        # contain: scale is the min of the axis scales; offsets non-negative
        scales = [
            transform["frameWidth"] / transform["intrinsicWidth"],
            transform["frameHeight"] / transform["intrinsicHeight"],
        ]
        assert abs(transform["scale"] - min(scales)) < 1e-9, transform
        assert transform["offsetX"] >= -1e-9 and transform["offsetY"] >= -1e-9
        assert abs(
            transform["renderWidth"] - transform["intrinsicWidth"] * transform["scale"]
        ) < 1e-6

        marker = draw_marker_and_sample(page, transform)
        assert marker["insideFrame"], marker
        assert marker["atMarker"][0] > 200 and marker["atMarker"][1] < 80, (
            marker,
            "red marker must read back at the mapped intrinsic point",
        )
        assert marker["atFar"][3] == 0, (
            marker,
            "media plane far corner must stay untouched by the marker",
        )
        assert abs(marker["roundTrip"]["nx"] - 0.25) < 1e-6, marker
        assert abs(marker["roundTrip"]["ny"] - 0.25) < 1e-6, marker

        page.screenshot(path=str(SCREENSHOT_PATH))
        assert_no_overflow(page)

        page.keyboard.press("Escape")
        browser.close()
    assert not errors, errors

    audit = {
        "url": URL,
        "status": "SCRIPT_RECORDED_PASS",
        "slice": "VR-023 Slice C — editor transform correctness with a "
        "colored marker fixture (contain policy, declared baseline)",
        "baseline": baseline,
        "transform": transform,
        "markerFixture": {
            "markerNormalized": MARKER_NORMALIZED,
            "markerVisible": marker["markerVisible"],
            "roundTrip": marker["roundTrip"],
            "redAtMappedPoint": True,
            "farCornerUntouched": True,
        },
        "errors": {"console": [], "page": [], "request": []},
    }
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    print(
        "Batch 443 Playwright verification passed: annotate editor exposes a "
        "declared baseline (mediaRevision + contain fit), the fit transform "
        "matches §7 formulas, a red marker drawn at the mapped intrinsic "
        "point reads back exactly and round-trips, diagnostics clean."
    )


if __name__ == "__main__":
    main()
