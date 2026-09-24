#!/usr/bin/env python3

"""Verify Batch 198: FrameOS 故事板 mode toggle.

2026-09-24 source re-sampling: clicking 故事版 on the image prompt panel
switches the panel into storyboard mode — placeholder becomes the 分镜
template text, the model switches to 帧界 O2.5, and the credits display
100. Clicking again reverts. Verifies the mode toggle in the clone.
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
    / "liblib-frameos-batch198-2026-09-24"
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
        assert ok, f"batch198 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/frameos/canvas/demo", wait_until="domcontentloaded")
    page.wait_for_timeout(1200)

    # Batch 225: 面板仅空图片节点显示 (2026-09-25 源站实测: 内容图片选中
    # 只显示富工具条无面板), 故先清空 image-1 内容再验证面板
    page.evaluate(
        "window.__frameos_store.getState().updateNodeData('image-1', { imageUrl: null })"
    )
    page.wait_for_timeout(300)

    image_node = page.locator(".react-flow__node-image").first
    image_node.click(position={"x": 60, "y": 30})
    page.wait_for_timeout(400)
    editor = page.locator(".frameos-prompt-editor")
    check("panel:opens", editor.is_visible())

    story_tile = editor.locator("button[aria-label='故事版']")
    check("tile:visible", story_tile.is_visible())

    # 默认态: 标准占位 + Seedream 模型
    model = editor.locator("select").first
    check(
        "default:model",
        model.input_value() == "Seedream 5.0 Pro",
    )

    # 切换故事版
    story_tile.click()
    page.wait_for_timeout(500)
    ph = editor.locator("textarea").first.get_attribute("placeholder")
    check(
        "storyboard:placeholder",
        ph is not None and "小剧情片段" in ph and "分镜" in ph,
    )
    check(
        "storyboard:model",
        model.input_value() == "帧界 O2.5",
    )

    # 再点一次 → 回到标准
    story_tile.click()
    page.wait_for_timeout(500)
    check(
        "storyboard:reverts",
        page.evaluate("window.__frameos_store.getState().storyboardMode") is False,
    )

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 198, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch198: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
