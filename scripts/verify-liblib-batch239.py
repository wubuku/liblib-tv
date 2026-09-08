#!/usr/bin/env python3
"""Verify Batch 239: first-frame attempt chip auto-creates a connected image
node and shows the reference slot + explanation panel state.

Source evidence (2026-09-09, docs/research/liblib-canvas-batch237-2026-09-09/
a1-after-firstframe.png + panel zooms):
- Clicking 首帧生成视频 auto-creates an image node to the LEFT of the video
  node, connected by an edge INTO the video node.
- Panel shows one 48×55 reference slot (badge 1) + explanation text
  以当前图为首帧生成视频。 and NO prompt textarea in this state.
- Selection stays on the video node (panel remains open); chip re-click must
  not duplicate the image node (store guard).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = (
    ROOT
    / "docs"
    / "research"
    / "liblib-canvas-batch239-2026-09-09"
    / "runtime-audit.json"
)


def attach_errors(page: Page) -> list[str]:
    errors: list[str] = []
    page.on(
        "console",
        lambda message: errors.append(f"console:{message.type}:{message.text}")
        if message.type == "error"
        else None,
    )
    page.on("pageerror", lambda error: errors.append(f"pageerror:{error}"))
    return errors


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool) -> None:
        assert ok, f"batch239 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto("http://localhost:4317", wait_until="networkidle")
    page.wait_for_timeout(500)

    # fresh video node (batch176 recipe)
    page.get_by_role("button", name="添加节点").click()
    page.wait_for_timeout(300)
    page.locator("[data-liblib-overlay='add-node']").get_by_role("button", name="视频", exact=True).click()
    page.wait_for_timeout(1000)

    def graph_state() -> dict[str, Any]:
        # the clone default canvas ships preset nodes — assert deltas, not totals
        return page.evaluate(
            """() => ({
                total: document.querySelectorAll('.react-flow__node').length,
                edges: document.querySelectorAll('.react-flow__edge').length,
            })"""
        )

    mode_trigger = page.locator("[data-video-mode-trigger]")

    # ---- click 首帧生成视频: image node + edge auto-created (delta assertions —
    # the default canvas ships preset nodes)
    before = graph_state()
    page.locator('[data-video-attempt="首帧生成视频"]').click()
    page.wait_for_timeout(500)
    state = graph_state()
    check("graph:one-node-added", state["total"] == before["total"] + 1)
    check("graph:one-edge-added", state["edges"] == before["edges"] + 1)
    check("graph:video-selected-panel-open", page.locator("[data-video-attempts]").count() == 1)

    # panel first-frame state
    check("panel:slot", page.locator("[data-video-firstframe-slot]").count() == 1)
    slot_box = page.locator("[data-video-firstframe-slot] > div").first.bounding_box()
    check("panel:slot-48x55", slot_box is not None and 40 <= slot_box["width"] <= 56
          and 48 <= slot_box["height"] <= 64)
    check(
        "panel:hint-text",
        page.locator("[data-video-firstframe-hint]").inner_text().strip()
        == "以当前图为首帧生成视频。",
    )
    check(
        "panel:no-textarea",
        page.locator("textarea[aria-label='视频生成提示词']").count() == 0,
    )
    check("panel:mode-全能参考", mode_trigger.inner_text().strip() == "全能参考")

    # edge direction: image -> video (edge id encodes e-<image id>-<video id>)
    edge_ok = page.evaluate(
        """() => [...document.querySelectorAll('.react-flow__edge')]
            .some(el => {
                const id = el.getAttribute('data-id') || el.className.toString();
                return /e-image-.*-video-/.test(id) || (id.includes('e-image-') && id.includes('-video-'));
            })"""
    )
    check("graph:edge-image-to-video", edge_ok)

    # ---- chip re-click must not duplicate (store guard)
    page.locator('[data-video-attempt="首帧生成视频"]').click(force=True)
    page.wait_for_timeout(400)
    state = graph_state()
    check(
        "guard:no-duplicate",
        state["total"] == before["total"] + 1 and state["edges"] == before["edges"] + 1,
    )

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 239, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch239: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
