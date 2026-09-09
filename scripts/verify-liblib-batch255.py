#!/usr/bin/env python3
"""Verify Batch 255: attempt persistence on node data.

Source evidence (2026-09-10, docs/research/liblib-canvas-batch254-2026-09-10/
README.md): the committed attempt state persists across deselect/re-select
— the suggestion chips do not come back. The clone converges by storing
attempt on the video node's data; the first-frame/first-last/destroy store
actions merge the attempt write into their own transaction so a chip commit
is ONE history entry (no attempt-without-graph intermediate).

The persistence contract is asserted through the exposed store
(window.__libtv_store): node.data.attempt after commit/destroy/undo. The
deselect/re-select UI steps from earlier drafts were dropped — the preset
canvas' overlapping nodes make geometric re-selection unreliable in
automation (batch 246 lesson)."""

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
    / "liblib-canvas-batch255-2026-09-10"
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
        assert ok, f"batch255 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto("http://localhost:4317", wait_until="networkidle")
    page.wait_for_timeout(500)

    # fresh video node (batch176 recipe)
    page.get_by_role("button", name="添加节点").click()
    page.wait_for_timeout(300)
    page.locator("[data-liblib-overlay='add-node']").get_by_role("button", name="视频", exact=True).click()
    page.wait_for_timeout(1000)
    page.locator(".react-flow__node-video").last.click()
    page.wait_for_timeout(600)

    def node_attempt():
        return page.evaluate(
            """() => {
            const store = window.__libtv_store;
            const canvas = store.getState().getActiveCanvas();
            const video = canvas.nodes.find((n) => n.type === 'video' && n.data.attempt !== undefined);
            return video ? (video.data.attempt ?? null) : undefined;
        }"""
        )

    def image_edge_count() -> int:
        return page.evaluate(
            """() => {
            const store = window.__libtv_store;
            const canvas = store.getState().getActiveCanvas();
            const video = canvas.nodes.find((n) => n.type === 'video' && n.data.attempt !== undefined);
            if (!video) return 0;
            return canvas.edges.filter((e) => {
                if (e.target !== video.id) return false;
                return canvas.nodes.some((n) => n.id === e.source && n.type === 'image');
            }).length;
        }"""
        )

    check("initial:no-attempt", node_attempt() in (None, undefined_marker()))
    check("initial:no-image-edge", image_edge_count() == 0)

    # commit first-frame chip: attempt + reference in one transaction
    page.locator('[data-video-attempt="首帧生成视频"]').click()
    page.wait_for_timeout(500)
    check("commit:node-attempt", node_attempt() == "首帧生成视频")
    check("commit:image-edge", image_edge_count() == 1)
    check("commit:slot-present", page.locator("[data-video-firstframe-slot]").count() == 1)

    # destroy: attempt cleared and reference removed in the same transaction
    page.locator("[data-video-firstframe-slot]").hover()
    page.wait_for_timeout(200)
    page.locator("[data-video-firstframe-destroy]").click()
    page.wait_for_timeout(500)
    check("destroy:node-attempt-cleared", node_attempt() in (None, ""))
    check("destroy:image-edge-removed", image_edge_count() == 0)
    check("destroy:slot-gone", page.locator("[data-video-firstframe-slot]").count() == 0)

    # re-commit then undo: single transaction removes node, edge AND attempt
    page.locator('[data-video-attempt="首帧生成视频"]').click()
    page.wait_for_timeout(500)
    check("recommit:node-attempt", node_attempt() == "首帧生成视频")
    check("recommit:image-edge", image_edge_count() == 1)
    page.keyboard.press("Control+z")
    page.wait_for_timeout(500)
    check("undo:node-attempt-cleared", node_attempt() in (None, ""))
    check("undo:image-edge-removed", image_edge_count() == 0)

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def undefined_marker():
    return "__unset__"


def main() -> None:
    audit: dict[str, Any] = {"batch": 255, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        try:
            audit["results"].append(run_desktop(page))
        except Exception as exc:  # noqa: BLE001
            page.screenshot(path=str(AUDIT_PATH.parent / "fail.png"))
            print("EXC:", str(exc)[:300])
            raise
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch255: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
