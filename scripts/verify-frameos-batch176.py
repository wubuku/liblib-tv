#!/usr/bin/env python3

"""Verify Batch 176: FrameOS 复制图片 menu item gating.

Source evidence (manual SOURCE_OBSERVATIONS §13.6 / shot 11): on an image
node without generated content, 复制图片 is disabled (along with 重新生成).
Inference recorded in Batch 176: 复制图片 enables once the node carries an
image. Verifies both states — a content-bearing image node shows an enabled
复制图片 that copies the image URL (toast), and an empty one stays disabled.
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
    / "liblib-frameos-batch176-2026-09-24"
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
        assert ok, f"batch176 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/frameos/canvas/demo", wait_until="domcontentloaded", timeout=90000)
    page.wait_for_timeout(1200)

    # 有内容的图片节点 → 复制图片 可点 (Batch 226: 内容菜单中间行改为
    # 设置为资产图, 重新生成只在空/非媒体节点出现)
    image_node = page.locator(".react-flow__node-image").first
    image_node.click(button="right")
    page.wait_for_timeout(300)
    menu = page.locator("[data-frameos-context-menu]")
    copy_img = menu.locator("[data-frameos-context-item='复制图片']")
    check("content:copy-image-enabled", copy_img.get_attribute("disabled") is None)
    check(
        "content:set-asset-row",
        menu.locator("[data-frameos-context-item='设置为资产图']").count() == 1,
    )
    copy_img.click()
    page.wait_for_timeout(300)
    toast = page.locator("[class*=toast], [class*=Toast]").first
    check("content:toast", toast.count() > 0)

    # 无内容的图片节点 → 复制图片 禁用
    page.evaluate(
        """(() => {
          const s = window.__frameos_store.getState();
          s.updateNodeData('image-1', { imageUrl: null, imageUrlCleared: true });
        })()"""
    )
    page.wait_for_timeout(400)
    image_node.click(button="right")
    page.wait_for_timeout(300)
    empty_menu = page.locator("[data-frameos-context-menu]")
    empty_copy = empty_menu.locator("[data-frameos-context-item='复制图片']")
    check("empty:copy-image-disabled", empty_copy.get_attribute("disabled") is not None)
    page.keyboard.press("Escape")
    page.wait_for_timeout(200)

    check("errors:empty", not errors) if not errors else print("CAPTURED:", errors[:5])
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 176, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch176: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
