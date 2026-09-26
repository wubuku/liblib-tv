#!/usr/bin/env python3

"""Verify Batch 220: FrameOS content-image rich floating toolbar.

2026-09-24 source sampling: selecting a content image node shows a rich
toolbar — ⛶全屏 / 下载 / ⭐收藏 / 超清 / 720全景 / 打光 / 改图 / 裁剪 / 标注 /
宫格切分∨ — while an EMPTY image node shows no toolbar at all (Batch 172).
The stale clone showed the old 6-item set regardless of content.

Checks:
1. content image selected → toolbar with exactly 10 buttons in source order;
2. imageUrl cleared → toolbar disappears;
3. regression: text node toolbar stays [全屏查看, 下载];
4. regression: content image selection still opens the prompt editor.
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
    / "liblib-frameos-batch220-2026-09-25"
    / "runtime-audit.json"
)

EXPECTED_ITEMS = [
    "全屏查看",
    "下载",
    "收藏",
    "超清",
    "720全景",
    "打光",
    "改图",
    "裁剪",
    "标注",
    "宫格切分 ∨",
]


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
        assert ok, f"batch220 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/frameos/canvas/demo", wait_until="domcontentloaded", timeout=90000)
    page.wait_for_timeout(1200)

    # 1) 有内容的图片节点 → 富工具条 (10 项, 源站顺序)
    content_img = page.locator(".react-flow__node-image").first
    check("boot:content-image", content_img.count() == 1)
    content_img.click(position={"x": 60, "y": 80})  # 避开右上替换按钮
    page.wait_for_timeout(400)
    toolbar = page.locator(".frameos-floating-toolbar-new")
    check("image:toolbar-opens", toolbar.is_visible())
    buttons = toolbar.locator("button")
    check("image:toolbar-ten-buttons", buttons.count() == 10)
    for idx, expected in enumerate(EXPECTED_ITEMS):
        if idx < 3:
            ok = buttons.nth(idx).get_attribute("aria-label") == expected
        else:
            ok = expected in (buttons.nth(idx).inner_text() or "")
        check(f"image:toolbar-item-{idx}-{expected}", ok)

    # Batch 225 语义更新: 内容图片选中无 PromptEditor (2026-09-25 源站实测:
    # 内容媒体节点只显示富工具条; 面板仅空节点显示)
    check(
        "regression:content-image-no-prompt-editor",
        page.locator(".frameos-prompt-editor").count() == 0
        or not page.locator(".frameos-prompt-editor").first.is_visible(),
    )

    # 2) 移除内容 → 工具条消失
    page.evaluate(
        """(() => {
          const s = window.__frameos_store.getState();
          s.updateNodeData('image-2', { imageUrl: null });
        })()"""
    )
    page.wait_for_timeout(400)
    empty_node = page.locator(".react-flow__node-image").last
    empty_node.click(position={"x": 60, "y": 80})
    page.wait_for_timeout(400)
    check(
        "empty-image:toolbar-hidden",
        page.locator(".frameos-floating-toolbar-new").count() == 0
        or not page.locator(".frameos-floating-toolbar-new").first.is_visible(),
    )
    check(
        "regression:empty-image-prompt-editor",
        page.locator(".frameos-prompt-editor").is_visible(),
    )

    # 3) 文本节点工具条回归: 恰好 [全屏查看, 下载]
    text = page.locator(".react-flow__node-text").first
    text.click()
    page.wait_for_timeout(400)
    tb2 = page.locator(".frameos-floating-toolbar-new")
    check("text:toolbar-opens", tb2.is_visible())
    tbtns = tb2.locator("button")
    check("text:toolbar-two-buttons", tbtns.count() == 2)
    check(
        "text:toolbar-fullscreen-view",
        tbtns.nth(0).get_attribute("aria-label") == "全屏查看",
    )
    check(
        "text:toolbar-download",
        tbtns.nth(1).get_attribute("aria-label") == "下载",
    )

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 220, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch220: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
