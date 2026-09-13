#!/usr/bin/env python3
"""Verify Batch 453: VR-021 Slice C — Add Resource multi-file vertical slice.

Contract: docs/research/LIBTV_MEDIA_INGRESS_RESOURCE_LIFECYCLE_CONTRACT.md
Slice C ("current source-shaped chooser/dialog entry; runtime provisional
cohort; one accepted-success graph transaction; local fixture materializer
only; focused VR-021 scenes") + §8.1 ordered validation.

Implementation:
- canvasStore.addResourceCohort: ADD_RESOURCE_MULTI intent validated via
  the Slice-A registry, fixture-materialized locators, one node per file,
  ONE history entry for the whole cohort; rejection = stable reasons with
  zero mutation;
- AddNodePanel upload entry opens a real file chooser (hidden input) and
  surfaces the stable reasons on rejection.

Scenes (browser, real file input):
- accepted_cohort: two PNG files -> two nodes sharing one cohort id,
  exactly one history entry, status feedback;
- rejected_reason_surfaces: an ambiguous-type file shows
  MEDIA_TYPE_AMBIGUOUS in the panel and mutates nothing;
- stale_generation_zero_mutation: store-level commit with a wrong
  expected generation is MEDIA_CANVAS_STALE with zero mutation.
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
    / "liblib-canvas-batch453-2026-09-13"
    / "runtime-audit.json"
)
SCREENSHOT_PATH = (
    ROOT
    / "docs"
    / "design-references"
    / "liblib-clone-batch453-add-resource-cohort-929-2026-09-13.png"
)

PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"0" * 64


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


def open_panel(page: Page):
    page.get_by_role("button", name="添加节点").click()
    page.locator("[data-add-resource-input]").wait_for(state="attached")
    page.locator("[data-add-node-resource='upload']").wait_for(state="visible")
    page.wait_for_timeout(160)


def run_accepted_cohort(page: Page):
    before = page.evaluate(
        """() => {
          const state = window.__libtv_store.getState();
          const canvas = state.canvases.find((c) => c.id === 'canvas-1');
          const history = state.historyByCanvas['canvas-1']
            || { past: [], future: [] };
          return {
            nodeCount: (canvas?.nodes ?? []).length,
            pastLength: history.past.length,
            generation: state.canvasGeneration,
          };
        }"""
    )
    open_panel(page)
    page.locator("[data-add-node-resource='upload']").click()
    page.set_input_files(
        "[data-add-resource-input]",
        [
            {"name": "shot-a.png", "mimeType": "image/png", "buffer": PNG_BYTES},
            {"name": "shot-b.png", "mimeType": "image/png", "buffer": PNG_BYTES},
        ],
    )
    page.wait_for_timeout(420)

    status = page.locator("[data-add-node-status]")
    assert "已添加 2 个资源" in status.inner_text(), status.inner_text()
    # Batch 468 (VR-018 Slice B): the accepted status carries the positive tone
    assert status.get_attribute("data-status-tone") == "positive", status

    cohort = page.evaluate(
        """() => {
          const state = window.__libtv_store.getState();
          const canvas = state.canvases.find((c) => c.id === 'canvas-1');
          const added = (canvas?.nodes ?? []).filter(
            (node) => typeof node.data?.ingressCohortId === 'string',
          );
          const history = state.historyByCanvas['canvas-1']
            || { past: [], future: [] };
          return {
            addedCount: added.length,
            cohortIds: Array.from(
              new Set(added.map((n) => n.data.ingressCohortId)),
            ),
            urls: added.map((n) => n.data.imageUrl),
            pastLength: history.past.length,
          };
        }"""
    )
    assert cohort["addedCount"] == 2, cohort
    assert len(cohort["cohortIds"]) == 1, cohort
    assert all(
        str(u).startswith("blob:fixture-") for u in cohort["urls"]
    ), cohort
    assert cohort["pastLength"] == before["pastLength"] + 1, (
        before,
        cohort,
        "the whole cohort must be ONE accepted graph transaction",
    )
    # the accepted path schedules a delayed panel close — let it fire so the
    # next scene starts from a closed panel
    page.wait_for_timeout(750)
    return {"before": before, "cohort": cohort}


def run_rejected_reason_surfaces(page: Page):
    before = page.evaluate(
        """() => {
          const state = window.__libtv_store.getState();
          const canvas = state.canvases.find((c) => c.id === 'canvas-1');
          const history = state.historyByCanvas['canvas-1']
            || { past: [], future: [] };
          return {
            nodeCount: (canvas?.nodes ?? []).length,
            pastLength: history.past.length,
          };
        }"""
    )
    open_panel(page)
    page.locator("[data-add-node-resource='upload']").click()
    page.set_input_files(
        "[data-add-resource-input]",
        [
            {
                "name": "thing.bin",
                "mimeType": "application/x-unknown",
                "buffer": b"\x00\x01",
            }
        ],
    )
    page.wait_for_timeout(320)
    status = page.locator("[data-add-node-status]")
    assert "MEDIA_TYPE_AMBIGUOUS" in status.inner_text(), status.inner_text()
    # Batch 468 (VR-018 Slice B): the rejected status carries the diagnostic tone
    assert status.get_attribute("data-status-tone") == "diagnostic", status
    after = page.evaluate(
        """() => {
          const state = window.__libtv_store.getState();
          const canvas = state.canvases.find((c) => c.id === 'canvas-1');
          const history = state.historyByCanvas['canvas-1']
            || { past: [], future: [] };
          return {
            nodeCount: (canvas?.nodes ?? []).length,
            pastLength: history.past.length,
          };
        }"""
    )
    assert after == before, (before, after, "rejection must not mutate")
    return {"reasonSurfaced": "MEDIA_TYPE_AMBIGUOUS", "zeroMutation": True}


def run_stale_generation_zero_mutation(page: Page):
    result = page.evaluate(
        """() => {
          const state = window.__libtv_store.getState();
          const descriptor = {
            kind: 'LOCAL_FILE',
            name: 'late.png',
            declaredMimeType: 'image/png',
            sizeBytes: 10,
            lastModified: 1,
          };
          return state.addResourceCohort([descriptor], state.canvasGeneration - 1);
        }"""
    )
    assert result["status"] == "rejected", result
    assert result["reasons"] == ["MEDIA_CANVAS_STALE"], result
    assert result["nodeIds"] == [] and result["cohortId"] is None
    return {"reason": "MEDIA_CANVAS_STALE", "zeroMutation": True}


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

        accepted = run_accepted_cohort(page)
        rejected = run_rejected_reason_surfaces(page)
        stale = run_stale_generation_zero_mutation(page)

        page.screenshot(path=str(SCREENSHOT_PATH))
        assert_no_overflow(page)
        browser.close()
    assert not errors, errors

    audit = {
        "url": URL,
        "status": "SCRIPT_RECORDED_PASS",
        "slice": "VR-021 Slice C — Add Resource multi-file vertical slice "
        "(source-shaped chooser, provisional cohort, one accepted graph "
        "transaction, fixture materializer)",
        "accepted_cohort": accepted,
        "rejected_reason_surfaces": rejected,
        "stale_generation_zero_mutation": stale,
        "errors": {"console": [], "page": [], "request": []},
    }
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    print(
        "Batch 453 Playwright verification passed: the upload chooser creates "
        "a two-file cohort as one accepted graph transaction (single history "
        "entry, shared cohort id, fixture locators), an ambiguous file "
        "surfaces MEDIA_TYPE_AMBIGUOUS with zero mutation, and a stale "
        "generation is rejected, diagnostics clean."
    )


if __name__ == "__main__":
    main()
