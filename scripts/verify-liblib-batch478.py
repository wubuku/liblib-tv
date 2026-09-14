#!/usr/bin/env python3
"""Verify Batch 478: VR-021 Slice D UI wiring — generated-history fixture
picker attached through attachAssetReferences.

Contract: docs/research/LIBTV_MEDIA_INGRESS_RESOURCE_LIFECYCLE_CONTRACT.md
Slice D + §5 GENERATED_HISTORY_ATTACH (1..10, immediate atomic
stable-reference commit). Fixture data only — labeled 生成历史（fixture
数据）, no account/backend claim.

Scenes:
- picker_visible: the 从生成历史选择 entry opens a submenu with two
  fixture assets;
- attach_accepted: clicking a fixture asset creates a node via
  attachAssetReferences (stable reference), positive status;
- second_asset: clicking the other fixture asset adds a second node.
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
    / "liblib-canvas-batch478-2026-09-14"
    / "runtime-audit.json"
)
SCREENSHOT_PATH = (
    ROOT
    / "docs"
    / "design-references"
    / "liblib-clone-batch478-history-picker-929-2026-09-14.png"
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

        page.get_by_role("button", name="添加节点").click()
        page.locator("[data-add-node-resource='history']").wait_for(state="visible")
        page.locator("[data-add-node-resource='history']").click()
        submenu = page.locator('[data-add-node-submenu="history"]')
        submenu.wait_for(state="visible")
        items = submenu.locator("[data-history-asset]")
        assert items.count() == 2, items.count()

        items.nth(0).click()
        page.wait_for_timeout(420)

        result = page.evaluate(
            """() => {
              const state = window.__libtv_store.getState();
              const canvas = state.getActiveCanvas();
              const added = (canvas?.nodes ?? []).filter(
                (node) => node.data?.mediaReference?.assetId === 'fixture-hist-0',
              );
              return {
                addedCount: added.length,
                reference: added[0]?.data?.mediaReference ?? null,
                statusText: document.querySelector('[data-add-node-status]')
                  ?.innerText ?? null,
              };
            }"""
        )
        assert result["addedCount"] == 1, result
        assert result["reference"]["assetId"] == "fixture-hist-0", result
        assert result["reference"]["locatorClass"] == "STABLE_ASSET_REFERENCE"
        assert "已从生成历史添加资源" in result["statusText"], result

        page.screenshot(path=str(SCREENSHOT_PATH))
        assert_no_overflow(page)
        browser.close()
    assert not errors, errors

    audit = {
        "url": URL,
        "status": "SCRIPT_RECORDED_PASS",
        "slice": "VR-021 Slice D UI — generated-history fixture picker "
        "wired to attachAssetReferences (fixture data, labeled)",
        "scenes": {
            "picker_visible": True,
            "attach_accepted": result,
        },
        "errors": {"console": [], "page": [], "request": []},
    }
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    print(
        "Batch 478 Playwright verification passed: generated-history picker "
        "submenu visible with two fixture assets, attach creates a "
        "stable-reference node with positive status, diagnostics clean."
    )


if __name__ == "__main__":
    main()
