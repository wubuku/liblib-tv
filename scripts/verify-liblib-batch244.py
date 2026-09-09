#!/usr/bin/env python3
"""Verify Batch 244: first-frame reference slot hover 销毁 button destroys
the auto-created image node + edge and reverts the panel.

Source evidence (2026-09-09, docs/research/liblib-canvas-batch241-2026-09-09/
m-HappyHorse1.1.png): the reference slot shows a 销毁 affordance on the
thumbnail. Click behavior (remove the auto-created image node + edge, clear
the attempt) is CLONE_DECISION — the inverse of createFirstFrameReference.
Note: the compact single-pill footer is Happy-Horse/model-specific (2.5's
first-frame state shows the full pill row, batch 237 a1) — deferred.
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
    / "liblib-canvas-batch244-2026-09-09"
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
        assert ok, f"batch244 check failed: {name}"
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
        return page.evaluate(
            """() => ({
                total: document.querySelectorAll('.react-flow__node').length,
                edges: document.querySelectorAll('.react-flow__edge').length,
            })"""
        )

    # commit first-frame: node + edge appear
    before = graph_state()
    page.locator('[data-video-attempt="首帧生成视频"]').click()
    page.wait_for_timeout(500)
    after = graph_state()
    check("setup:node-added", after["total"] == before["total"] + 1)
    check("setup:edge-added", after["edges"] == before["edges"] + 1)

    slot = page.locator("[data-video-firstframe-slot]")
    check("panel:slot-present", slot.count() == 1)

    # hover reveals the 销毁 button
    destroy = page.locator("[data-video-firstframe-destroy]")
    check("destroy:in-dom", destroy.count() == 1)
    check("destroy:label", destroy.inner_text().strip() == "销毁")
    slot.hover()
    page.wait_for_timeout(300)
    check("destroy:visible-on-hover", destroy.is_visible())

    # click destroys the reference: node + edge removed, attempt cleared
    destroy.click()
    page.wait_for_timeout(500)
    reverted = graph_state()
    check("destroy:node-removed", reverted["total"] == before["total"])
    check("destroy:edge-removed", reverted["edges"] == before["edges"])
    check(
        "destroy:attempt-cleared",
        page.locator('[data-video-attempt="首帧生成视频"]').get_attribute("aria-pressed")
        == "false",
    )
    # panel reverts to prompt state (textarea back, first-frame slot gone)
    check("destroy:slot-gone", page.locator("[data-video-firstframe-slot]").count() == 0)
    check(
        "destroy:textarea-back",
        page.locator("textarea[aria-label='视频生成提示词']").count() == 1,
    )

    # re-click chip re-creates the reference (guard allows after destroy)
    page.locator('[data-video-attempt="首帧生成视频"]').click()
    page.wait_for_timeout(500)
    recreated = graph_state()
    check("recreate:node-added", recreated["total"] == before["total"] + 1)
    check("recreate:edge-added", recreated["edges"] == before["edges"] + 1)
    check("recreate:slot-back", page.locator("[data-video-firstframe-slot]").count() == 1)

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 244, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch244: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
