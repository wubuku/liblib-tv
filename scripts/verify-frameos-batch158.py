#!/usr/bin/env python3

"""Verify Batch 158: FrameOS text-node selection UI drift catch-up.

2026-09-23 source re-sampling (see docs/user-manual/frameos-canvas
SOURCE_OBSERVATIONS.md §13.3): selecting a text node shows a floating
toolbar with exactly two icon buttons (全屏查看 / 下载) and NO prompt
panel. The clone still had the stale snapshot behavior (下载-only toolbar
+ PromptEditor for text nodes). This batch aligns the clone and verifies:

1. selecting a text node opens the toolbar with exactly [全屏查看, 下载];
2. no .frameos-prompt-editor renders for a selected text node;
3. double-click still enters the inline textarea and blank-click commits;
4. regression: image/video nodes still show the PromptEditor.
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
    / "liblib-frameos-batch158-2026-09-23"
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


def ensure_text_node(page: Page, nodes_before: int) -> None:
    """Create a text node via the proven context-menu path when missing."""
    if page.locator(".react-flow__node-text").count() > 0:
        return
    pane = page.locator(".react-flow__pane")
    pane.click(button="right", position={"x": 700, "y": 480})
    page.wait_for_timeout(300)
    menu = page.locator("[data-frameos-context-menu]")
    menu.locator("[data-frameos-context-item='添加文本节点']").click()
    page.wait_for_timeout(600)
    assert page.locator(".react-flow__node").count() == nodes_before + 1, (
        "batch158: context-menu text node was not created"
    )


def ensure_media_node(page: Page, nodes_before: int) -> str:
    """Ensure an image-or-video node exists; returns its type selector."""
    for selector in (".react-flow__node-image", ".react-flow__node-video"):
        if page.locator(selector).count() > 0:
            return selector
    page.locator("button[aria-label='添加节点']").click()
    page.wait_for_timeout(300)
    page.get_by_text("图片节点", exact=True).click()
    page.wait_for_timeout(600)
    assert page.locator(".react-flow__node-image").count() > 0, (
        "batch158: tool-rail image node was not created"
    )
    _ = nodes_before
    return ".react-flow__node-image"


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool) -> None:
        assert ok, f"batch158 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/frameos/canvas/demo", wait_until="domcontentloaded")
    page.wait_for_timeout(1200)
    nodes_before = page.locator(".react-flow__node").count()
    check("boot:nodes", nodes_before >= 3)

    ensure_text_node(page, nodes_before)
    text_node = page.locator(".react-flow__node-text").first
    check("text:exists", text_node.count() == 1)

    # 选中文本节点 → 浮动工具条恰好两个按钮: 全屏查看 / 下载
    text_node.click()
    page.wait_for_timeout(400)
    toolbar = page.locator(".frameos-floating-toolbar-new")
    check("text:toolbar-opens", toolbar.is_visible())
    buttons = toolbar.locator("button")
    check("text:toolbar-two-buttons", buttons.count() == 2)
    check(
        "text:toolbar-fullscreen-view",
        buttons.nth(0).get_attribute("aria-label") == "全屏查看",
    )
    check(
        "text:toolbar-download",
        buttons.nth(1).get_attribute("aria-label") == "下载",
    )

    # 文本节点不渲染 prompt 面板 (2026-09-23 源站实测)
    check("text:no-prompt-editor", page.locator(".frameos-prompt-editor").count() == 0)

    # 双击仍进入内联 textarea, 点空白提交并退出
    text_node.dblclick()
    page.wait_for_timeout(300)
    check("text:dblclick-textarea", text_node.locator("textarea").is_visible())
    page.locator(".react-flow__pane").click(position={"x": 100, "y": 100})
    page.wait_for_timeout(300)
    check("text:blank-click-exits-edit", text_node.locator("textarea").count() == 0)

    # 回归: 图片/视频节点选中仍然显示 prompt 面板
    media_selector = ensure_media_node(page, nodes_before)
    page.locator(media_selector).first.click()
    page.wait_for_timeout(400)
    check("media:prompt-editor-still-shows", page.locator(".frameos-prompt-editor").is_visible())

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 158, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch158: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
