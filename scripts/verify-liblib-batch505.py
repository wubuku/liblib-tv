#!/usr/bin/env python3
"""Verify Batch 505: VR-018 sweep closure — empty-canvas quick chips
surface carries an explicit disposition tone.

Contract: docs/research/LIBTV_COMMAND_OUTCOME_FEEDBACK_CONTRACT.md §16 /
§17 — unavailable commands project diagnostic; graph-producing commands
present their node result as the primary surface and stay feedback-free
(no success toast standing in for the result).

Scenes:
- quick_generate_diagnostic: 角色三视图 chip surfaces
  data-status-tone="diagnostic" with the existing prototype copy;
- story_script_graph_result: 故事脚本生成 chip creates the text +
  script-v2 node pair with zero feedback (no status line appears).
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
    / "liblib-canvas-batch505-2026-09-14"
    / "runtime-audit.json"
)
SCREENSHOT_PATH = (
    ROOT
    / "docs"
    / "design-references"
    / "liblib-clone-batch505-empty-chips-tones-929-2026-09-14.png"
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


def empty_status(page: Page):
    return page.evaluate(
        """() => {
          const el = document.querySelector('[data-canvas-empty-status]');
          return el ? { text: el.innerText, tone: el.dataset.statusTone } : null;
        }"""
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

        # Reach an empty canvas: the boot canvas ships demo nodes; canvas-1
        # is the empty one (same entry as the batch 100 contract).
        page.locator("[data-canvas-trigger]").click()
        page.locator("[data-canvas-row='canvas-1']").get_by_role("button").first.click()
        page.wait_for_timeout(300)
        page.locator("[data-canvas-empty-state]").wait_for(state="visible")

        # Scene 1: unavailable quick chip → diagnostic.
        page.locator('[data-canvas-empty-chip="character-turnaround"]').click()
        page.wait_for_timeout(120)
        chip_status = empty_status(page)
        assert chip_status == {
            "text": "本地原型：快速生成入口未接入",
            "tone": "diagnostic",
        }, chip_status

        page.screenshot(path=str(SCREENSHOT_PATH))

        # Scene 2: story-script chip → graph result, zero feedback.
        page.locator('[data-canvas-empty-chip="story-script"]').click()
        page.wait_for_timeout(420)
        result = page.evaluate(
            """() => {
              const state = window.__libtv_store.getState();
              const canvas = state.getActiveCanvas();
              const nodes = canvas?.nodes ?? [];
              return {
                textNodes: nodes.filter((n) => n.type === 'text').length,
                scriptNodes: nodes.filter((n) => n.type === 'script-v2').length,
                emptyStateGone: !document.querySelector('[data-canvas-empty-state]'),
                statusElement: !!document.querySelector('[data-canvas-empty-status]'),
              };
            }"""
        )
        assert result["textNodes"] >= 1, result
        assert result["scriptNodes"] >= 1, result
        assert result["emptyStateGone"], result
        assert not result["statusElement"], result

        browser.close()
    assert not errors, errors

    audit = {
        "url": URL,
        "status": "SCRIPT_RECORDED_PASS",
        "slice": "VR-018 sweep closure — empty-canvas quick chips: "
        "unavailable disclosure projects diagnostic, graph result stays "
        "feedback-free",
        "scenes": {
            "quick_generate_diagnostic": chip_status,
            "story_script_graph_result": result,
        },
        "errors": {"console": [], "page": [], "request": []},
    }
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    print(
        "Batch 505 verification passed: quick-chip disclosure projects "
        "diagnostic via the VR-018 catalog; story-script pair stays a "
        "graph result with zero feedback; recorded in runtime-audit.json."
    )


if __name__ == "__main__":
    main()
