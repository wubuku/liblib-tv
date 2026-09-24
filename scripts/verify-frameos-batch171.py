#!/usr/bin/env python3

"""Verify Batch 171: FrameOS video node toolbar aligned to source.

2026-09-23 source re-sampling: selecting the video node shows the same two
icon buttons as text nodes — 全屏查看 / 下载 (the stale clone had 下载/收藏/
查看历史/超清/去字幕). Verifies the toolbar contents and the media-node
PromptEditor regression (video still shows the panel; text does not).
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
    / "liblib-frameos-batch171-2026-09-23"
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
        assert ok, f"batch171 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/frameos/canvas/demo", wait_until="domcontentloaded")
    page.wait_for_timeout(1200)

    video = page.locator(".react-flow__node-video").first
    check("boot:video-node", video.count() == 1)
    video.click(position={"x": 60, "y": 30})  # 避开中心播放按钮
    page.wait_for_timeout(400)
    # Batch 225 更新 (2026-09-25 源站实测): 内容视频工具条 = 九项
    # 全屏查看/下载/收藏/剪辑/裁剪/音视频分离/超清/去字幕/片段重拍
    toolbar = page.locator(".frameos-floating-toolbar-new")
    check("video:toolbar-opens", toolbar.is_visible())
    buttons = toolbar.locator("button")
    check("video:toolbar-nine-buttons", buttons.count() == 9)
    expected = [
        "全屏查看",
        "下载",
        "收藏",
        "剪辑",
        "裁剪",
        "音视频分离",
        "超清",
        "去字幕",
        "片段重拍",
    ]
    for idx, name in enumerate(expected):
        check(
            f"video:toolbar-item-{idx}-{name}",
            buttons.nth(idx).get_attribute("aria-label") == name,
        )

    # Batch 225 回归: 内容视频节点无 PromptEditor (源站实测); 文本节点不渲染
    check(
        "regression:content-video-no-prompt-editor",
        page.locator(".frameos-prompt-editor").count() == 0
        or not page.locator(".frameos-prompt-editor").first.is_visible(),
    )
    # 空视频节点保留面板 (清空内容后选中)
    page.evaluate(
        "window.__frameos_store.getState().updateNodeData('video-1', { imageUrl: null })"
    )
    page.wait_for_timeout(300)
    video.click(position={"x": 60, "y": 30})
    page.wait_for_timeout(400)
    check(
        "regression:empty-video-prompt-editor",
        page.locator(".frameos-prompt-editor").is_visible(),
    )
    text = page.locator(".react-flow__node-text").first
    if text.count() == 0:
        pane = page.locator(".react-flow__pane")
        pane.click(button="right", position={"x": 700, "y": 480})
        page.wait_for_timeout(300)
        page.locator("[data-frameos-context-item='添加文本节点']").click()
        page.wait_for_timeout(600)
    text.click()
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
    audit: dict[str, Any] = {"batch": 171, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch171: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
