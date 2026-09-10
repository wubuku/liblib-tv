#!/usr/bin/env python3
"""Verify Batch 336: storyboard pending-video confirm/cancel strip.

Source context (2026-09-11): the source storyboard shows a
「待确认后生成」 video card (Wan 3.0 Prime) whose confirmation
interaction could not be sampled (model-menu outage; BLOCKED_MANUAL).
The clone ships a CLONE_DECISION interaction: selecting a pending card
reveals a 确认生成 / 取消 strip; confirm flips status pending→ready,
cancel flips pending→empty (local mock via updateNodeData).
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
    / "liblib-canvas-batch336-2026-09-11"
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
        assert ok, f"batch336 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto("http://localhost:4317", wait_until="networkidle")
    page.wait_for_timeout(600)

    # pick the canvas's first video node and force it into the pending state
    video_id = page.evaluate(
        """() => {
        const store = window.__libtv_store.getState();
        const canvas = store.canvases.find((c) => c.id === store.activeCanvasId);
        const video = canvas.nodes.find((n) => n.type === 'video');
        return video ? video.id : null;
    }"""
    )
    check("setup:video-node", video_id is not None)
    page.evaluate(
        """(id) => window.__libtv_store.getState().updateNodeData(id, { status: 'pending' })""",
        video_id,
    )
    page.wait_for_timeout(250)

    # storyboard view
    page.get_by_role("button", name="故事板").click()
    page.wait_for_timeout(400)
    video_cards = page.locator("[data-storyboard-column='video'] [data-storyboard-card]")
    check("board:video-card", video_cards.count() >= 1)
    card = page.locator(f"[data-storyboard-card='{video_id}']")
    check("pending:status-attr", card.get_attribute("data-storyboard-video-status") == "pending")
    check("pending:overlay-text", card.inner_text().strip() != "" and "待确认后生成" not in "")
    check(
        "pending:overlay-label",
        "待确认后生成" in card.inner_text(),
    )
    check(
        "pending:strip-hidden-before-select",
        page.locator(f"[data-storyboard-pending-strip='{video_id}']").count() == 0,
    )

    # selecting the card reveals the confirm strip
    card.click()
    page.wait_for_timeout(250)
    strip = page.locator(f"[data-storyboard-pending-strip='{video_id}']")
    check("pending:strip-visible", strip.is_visible())
    check(
        "pending:confirm-label",
        page.locator(f"[data-storyboard-pending-confirm='{video_id}']").inner_text().strip() == "确认生成",
    )
    check(
        "pending:cancel-label",
        page.locator(f"[data-storyboard-pending-cancel='{video_id}']").inner_text().strip() == "取消",
    )

    # cancel → empty
    page.locator(f"[data-storyboard-pending-cancel='{video_id}']").click()
    page.wait_for_timeout(300)
    check(
        "cancel:status-empty",
        card.get_attribute("data-storyboard-video-status") == "empty",
    )
    check(
        "cancel:overlay-label",
        "暂无预览" in card.inner_text(),
    )
    check(
        "cancel:strip-gone",
        page.locator(f"[data-storyboard-pending-strip='{video_id}']").count() == 0,
    )

    # pending again → confirm → ready (play circle, no pending label)
    page.evaluate(
        """(id) => window.__libtv_store.getState().updateNodeData(id, { status: 'pending' })""",
        video_id,
    )
    page.wait_for_timeout(250)
    card.click()
    page.wait_for_timeout(250)
    page.locator(f"[data-storyboard-pending-confirm='{video_id}']").click()
    page.wait_for_timeout(300)
    check(
        "confirm:status-ready",
        card.get_attribute("data-storyboard-video-status") == "ready",
    )
    check(
        "confirm:pending-label-gone",
        "待确认后生成" not in card.inner_text(),
    )

    # store reflects the final status
    final_status = page.evaluate(
        """(id) => {
        const store = window.__libtv_store.getState();
        const canvas = store.canvases.find((c) => c.id === store.activeCanvasId);
        return canvas.nodes.find((n) => n.id === id).data.status;
    }""",
        video_id,
    )
    check("store:status-ready", final_status == "ready")

    # back to workbench
    page.get_by_role("button", name="工作流").click()
    page.wait_for_timeout(300)
    check("workbench:return", page.locator(".react-flow").is_visible())

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 336, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch336: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
