#!/usr/bin/env python3

"""Verify Batch 180: FrameOS prompt panel follows the selected node.

2026-09-23 source re-sampling (shots 07/09): the image prompt panel renders
directly BELOW the selected node (12px gap) and follows it as the node or
viewport moves. The clone docked the panel at the fixed bottom-right
corner. Batch 180 switches to node-following positioning (rAF + node rect,
clamped to viewport). Verifies the panel sits below the node and follows a
node drag, plus the batch-158 text guard.
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
    / "liblib-frameos-batch180-2026-09-24"
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
        assert ok, f"batch180 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/frameos/canvas/demo", wait_until="domcontentloaded", timeout=90000)
    page.wait_for_timeout(1200)

    # Batch 225: 面板仅空图片节点显示 (2026-09-25 源站实测: 内容图片选中
    # 只显示富工具条无面板), 故先清空 image-1 内容再验证面板
    page.evaluate(
        "window.__frameos_store.getState().updateNodeData('image-1', { imageUrl: null })"
    )
    page.wait_for_timeout(300)

    image_node = page.locator(".react-flow__node-image").first
    image_node.click(position={"x": 60, "y": 30})
    page.wait_for_timeout(500)
    editor = page.locator(".frameos-prompt-editor")
    check("panel:opens", editor.is_visible())

    node_box = image_node.bounding_box()
    editor_box = editor.bounding_box()
    check("panel:below-node", node_box is not None and editor_box is not None
          and editor_box["y"] >= node_box["y"] + node_box["height"] - 4)
    node_cx = node_box["x"] + node_box["width"] / 2
    panel_cx = editor_box["x"] + editor_box["width"] / 2
    check("panel:horizontally-near-node", abs(panel_cx - node_cx) < 60)

    # 拖动节点 → 面板跟随
    page.mouse.move(node_cx, node_box["y"] + 30)
    page.mouse.down()
    for i in range(1, 7):
        page.mouse.move(
            node_cx - 200 * i / 6,
            node_box["y"] + 30 - 120 * i / 6,
        )
    page.mouse.up()
    page.wait_for_timeout(700)
    node_box2 = image_node.bounding_box()
    editor_box2 = editor.bounding_box()
    check("node:moved", node_box2 is not None and node_box2["x"] < node_box["x"] - 100)
    check(
        "panel:follows",
        editor_box2 is not None and node_box2 is not None
        and abs((editor_box2["x"] + editor_box2["width"] / 2)
                - (node_box2["x"] + node_box2["width"] / 2)) < 60,
    )

    # 回归: 文本节点不渲染面板 (batch158)
    page.locator(".react-flow__node-text").first.click(position={"x": 60, "y": 30})
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
    audit: dict[str, Any] = {"batch": 180, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch180: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
