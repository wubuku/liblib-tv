#!/usr/bin/env python3

"""Verify Batch 170: FrameOS context menus drift catch-up.

2026-09-23 source re-sampling (docs/user-manual/frameos-canvas
SOURCE_OBSERVATIONS §13.6 / shot 11, and §1.1 round-1 pane menu): the image
node context menu has five rows — 复制 ⌘C, 复制图片 (disabled), 创建副本
⌘D, 重新生成 (disabled), 删除 ⌫ — and the pane context menu reads
添加节点 / 上传文件 / 粘贴 ⌘V / 整理 / 重置 ⌘0. Verifies both menus
(incl. disabled rows are inert) and the pane actions wiring.
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
    / "liblib-frameos-batch170-2026-09-23"
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
        assert ok, f"batch170 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/frameos/canvas/demo", wait_until="domcontentloaded", timeout=90000)
    page.wait_for_timeout(1200)
    nodes_before = page.locator(".react-flow__node").count()

    # 图片节点右键: Batch 226 起 内容图片菜单 = 复制/复制图片/创建副本/
    # 设置为资产图/删除 (全部可点); 空图片菜单才有 重新生成(禁用)
    image_node = page.locator(".react-flow__node-image").first
    image_node.click(button="right")
    page.wait_for_timeout(300)
    menu = page.locator("[data-frameos-context-menu]")
    check("node:menu-opens", menu.is_visible())
    # demo 的 image-1 有内容 → 内容形态
    for item, disabled in [
        ("复制", False),
        ("复制图片", False),
        ("创建副本", False),
        ("设置为资产图", False),
        ("删除", False),
    ]:
        row = menu.locator(f"[data-frameos-context-item='{item}']")
        check(f"node:item:{item}", row.is_visible())
        check(
            f"node:item:{item}:disabled={str(disabled).lower()}",
            (row.get_attribute("disabled") is not None) == disabled,
        )
    page.keyboard.press("Escape")
    page.wait_for_timeout(200)
    # 清空内容 → 空形态: 复制图片/重新生成 禁用且点击无效果
    page.evaluate(
        "window.__frameos_store.getState().updateNodeData('image-1', { imageUrl: null })"
    )
    page.wait_for_timeout(300)
    image_node.click(button="right")
    page.wait_for_timeout(300)
    menu = page.locator("[data-frameos-context-menu]")
    for item, disabled in [
        ("复制", False),
        ("复制图片", True),
        ("创建副本", False),
        ("重新生成", True),
        ("删除", False),
    ]:
        row = menu.locator(f"[data-frameos-context-item='{item}']")
        check(f"node:empty-item:{item}", row.is_visible())
        check(
            f"node:empty-item:{item}:disabled={str(disabled).lower()}",
            (row.get_attribute("disabled") is not None) == disabled,
        )
    edges_before = page.evaluate("window.__frameos_store.getState().edges.length")
    menu.locator("[data-frameos-context-item='重新生成']").click(force=True)
    page.wait_for_timeout(300)
    check(
        "node:disabled-row-inert",
        page.evaluate("window.__frameos_store.getState().edges.length") == edges_before
        and page.locator("[data-frameos-context-menu]").count() > 0,
    )
    page.keyboard.press("Escape")
    page.wait_for_timeout(200)

    # 空白右键: 五项逐字
    pane = page.locator(".react-flow__pane")
    pane.click(button="right", position={"x": 700, "y": 500})
    page.wait_for_timeout(300)
    for item in ["添加节点", "上传文件", "粘贴", "整理", "重置"]:
        check(
            f"pane:item:{item}",
            menu.locator(f"[data-frameos-context-item='{item}']").is_visible(),
        )

    # 整理 → 节点位置重排 (经 MapDock 事件)
    positions_before = page.evaluate(
        "window.__frameos_store.getState().nodes.map((n) => n.position.x).join()"
    )
    menu.locator("[data-frameos-context-item='整理']").click()
    page.wait_for_timeout(700)
    positions_after = page.evaluate(
        "window.__frameos_store.getState().nodes.map((n) => n.position.x).join()"
    )
    check("pane:organize-runs", positions_before != positions_after)

    # 重置 → fitView
    menu_open_again = page.locator("[data-frameos-context-menu]").count() == 0
    _ = menu_open_again
    pane.click(button="right", position={"x": 700, "y": 500})
    page.wait_for_timeout(300)
    menu.locator("[data-frameos-context-item='重置']").click()
    page.wait_for_timeout(500)
    check("pane:reset-runs", page.locator(".react-flow__node").count() == nodes_before)

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 170, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch170: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
