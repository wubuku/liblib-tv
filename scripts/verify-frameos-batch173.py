#!/usr/bin/env python3

"""Verify Batch 173: FrameOS empty video node is a plain film card.

2026-09-23 source re-sampling (live canvas): an empty video node shows only
the centered film icon plus handles — no play button, no duration badge, no
replace button. The clone rendered play/replace buttons unconditionally.
Now those buttons render only for video nodes carrying content (imageUrl).
Verifies both states and the batch-158 text guard regression. Alignment
guides remain unverified (automation drag could not sample them reliably).
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
BASE_URL = os.environ.get("LIBLIB_BASE_URL", "http://localhost:4317")
AUDIT_PATH = (
    ROOT
    / "docs"
    / "research"
    / "liblib-frameos-batch173-2026-09-24"
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
    page.on("dialog", lambda d: d.dismiss())
    return errors


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool) -> None:
        assert ok, f"batch173 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/frameos/canvas/demo", wait_until="domcontentloaded")
    page.wait_for_timeout(1200)

    # 有内容的视频节点: 播放按钮 + 替换按钮可见
    video = page.locator(".react-flow__node-video").first
    check("boot:video-node", video.count() == 1)
    video.click(position={"x": 60, "y": 30})
    page.wait_for_timeout(300)
    check(
        "content-video:play-visible",
        video.locator("button[aria-label='播放视频']").is_visible(),
    )
    check(
        "content-video:replace-visible",
        video.locator("button[aria-label='替换内容']").is_visible(),
    )

    # 移除内容 → 空视频节点: 播放/替换按钮消失, 纯图标
    page.evaluate(
        """(() => {
          const s = window.__frameos_store.getState();
          s.updateNodeData(s.selectedNodeId ?? 'video-1', { imageUrl: null, imageUrlCleared: true });
        })()"""
    )
    page.wait_for_timeout(400)
    video.click(position={"x": 60, "y": 30})
    page.wait_for_timeout(300)
    check(
        "empty-video:play-hidden",
        video.locator("button[aria-label='播放视频']").count() == 0,
    )
    check(
        "empty-video:replace-hidden",
        video.locator("button[aria-label='替换内容']").count() == 0,
    )

    # 回归: 文本节点守卫 (batch158)
    text = page.locator(".react-flow__node-text").first
    if text.count() == 0:
        pane = page.locator(".react-flow__pane")
        pane.click(button="right", position={"x": 700, "y": 480})
        page.wait_for_timeout(300)
        page.locator("[data-frameos-context-item='添加文本节点']").click()
        page.wait_for_timeout(600)
    text.click(position={"x": 60, "y": 30})
    page.wait_for_timeout(300)
    check(
        "regression:text-guard",
        page.locator(".frameos-prompt-editor").count() == 0
        or not page.locator(".frameos-prompt-editor").first.is_visible(),
    )

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 173, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch173: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
