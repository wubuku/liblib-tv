#!/usr/bin/env python3

"""Verify Batch 172: FrameOS image-node hover replace button gating.

2026-09-23 source re-sampling: hovering an EMPTY image node shows no hover
UI at all (no buttons, no scale). The clone rendered the 替换内容 button
unconditionally. Now the button renders only for image nodes that carry
content (imageUrl). Verifies both states and documents the stale
hover-mask row correction.
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
    / "liblib-frameos-batch172-2026-09-23"
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
        assert ok, f"batch172 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/frameos/canvas/demo", wait_until="domcontentloaded", timeout=90000)
    page.wait_for_timeout(1200)

    # 有内容的图片节点: hover → 替换内容按钮可见
    content_img = page.locator(".react-flow__node-image").first
    check("boot:content-image", content_img.count() == 1)
    content_img.hover()
    page.wait_for_timeout(300)
    check(
        "content-image:hover-replace-visible",
        content_img.locator("button[aria-label='替换内容']").is_visible(),
    )

    # 构造无内容图片节点 (store 移除 imageUrl) → hover → 无替换按钮
    page.evaluate(
        """(() => {
          const s = window.__frameos_store.getState();
          s.updateNodeData('image-2', { imageUrl: null, imageUrlCleared: true });
        })()"""
    )
    page.wait_for_timeout(400)
    empty_count = page.evaluate(
        """(() => {
          const s = window.__frameos_store.getState();
          return s.nodes.filter((n) => n.type === 'image' && !n.data.imageUrl).length;
        })()"""
    )
    check("boot:empty-image-prepared", empty_count >= 1)

    empty_node = page.locator(
        ".react-flow__node-image"
    ).last  # image-2 (已移除内容)
    empty_node.hover()
    page.wait_for_timeout(300)
    check(
        "empty-image:no-replace-button",
        empty_node.locator("button[aria-label='替换内容']").count() == 0,
    )

    # 回归: 选中空图片节点 → PromptEditor 打开 (图片节点守卫)
    empty_node.click()
    page.wait_for_timeout(300)
    check(
        "regression:empty-image-prompt-editor",
        page.locator(".frameos-prompt-editor").is_visible(),
    )

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 172, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch172: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
