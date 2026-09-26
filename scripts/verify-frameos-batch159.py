#!/usr/bin/env python3

"""Verify Batch 159: FrameOS image-node prompt panel header drift catch-up.

2026-09-23 source re-sampling (docs/user-manual/frameos-canvas
SOURCE_OBSERVATIONS.md §13.4): the image prompt panel header row is
聚焦 / 故事版 / 参考 + one reference chip per upstream node (icon + remove ×)
+ 删除连线 / 替换参考 icons. 删除连线 removes the incoming reference edges
(the stale clone wired it to node deletion). Verifies:

1. header buttons 聚焦/故事版/参考/删除连线/替换参考 all render;
2. one chip per incoming edge, removable individually (edge count -1);
3. 删除连线 removes all incoming edges; ⌘Z restores them;
4. text-node guard regression stays green.
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
    / "liblib-frameos-batch159-2026-09-23"
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
        assert ok, f"batch159 check failed: {name}"
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
    check("boot:image-node", image_node.count() == 1)
    edges_before = page.evaluate(
        "window.__frameos_store ? window.__frameos_store.getState().edges.length : 0"
    )
    check("boot:edges-present", edges_before >= 3)

    # 选中图片节点 → 面板 + 头部工具行
    image_node.click()
    page.wait_for_timeout(400)
    editor = page.locator(".frameos-prompt-editor")
    check("image:editor-opens", editor.is_visible())
    actions = page.locator("[data-frameos-prompt-top-actions] button")
    labels = [actions.nth(i).get_attribute("aria-label") for i in range(actions.count())]
    for item in ["聚焦", "故事版", "参考", "删除连线", "替换参考"]:
        check(f"image:header:{item}", item in labels)

    # 每条入边一枚引用芯片 (demo 中 image-1 有 3 条入边)
    incoming_before = page.evaluate(
        """(() => {
          const s = window.__frameos_store.getState();
          return s.edges.filter((e) => e.target === s.selectedNodeId).length;
        })()"""
    )
    chips = page.locator("[data-frameos-ref-chip]")
    check("image:chips-match-incoming", chips.count() == incoming_before and chips.count() >= 3)

    # 单独移除一枚芯片 → 边数 -1
    chips.first.locator("[data-frameos-ref-remove]").click()
    page.wait_for_timeout(400)
    edges_after_remove = page.evaluate(
        "window.__frameos_store.getState().edges.length"
    )
    check(
        "chip:remove-deletes-edge",
        chips.count() == incoming_before - 1
        and edges_after_remove == edges_before - 1,
    )

    # 删除连线 → 清空全部入边 (其他无关边保留)
    page.get_by_role("button", name="删除连线").click()
    page.wait_for_timeout(400)
    incoming_after_clear = page.evaluate(
        """(() => {
          const s = window.__frameos_store.getState();
          return s.edges.filter((e) => e.target === s.selectedNodeId).length;
        })()"""
    )
    check(
        "delete-edges:clears-incoming",
        page.locator("[data-frameos-ref-chip]").count() == 0
        and incoming_after_clear == 0,
    )

    # ⌘Z 恢复被删除的连线
    for _ in range(edges_before):
        page.keyboard.press("Meta+z")
        page.wait_for_timeout(200)
    edges_restored = page.evaluate("window.__frameos_store.getState().edges.length")
    check("undo:edges-restored", edges_restored == edges_before)

    # 回归: 文本节点守卫仍生效
    text_node = page.locator(".react-flow__node-text").first
    if text_node.count() == 0:
        pane = page.locator(".react-flow__pane")
        pane.click(button="right", position={"x": 700, "y": 480})
        page.wait_for_timeout(300)
        page.locator("[data-frameos-context-item='添加文本节点']").click()
        page.wait_for_timeout(600)
    page.locator(".react-flow__node-text").first.click()
    page.wait_for_timeout(300)
    check("text:guard-still-on", page.locator(".frameos-prompt-editor").count() == 0)

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 159, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch159: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
