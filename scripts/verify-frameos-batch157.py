#!/usr/bin/env python3

"""Verify Batch 157: FrameOS context menu (node right-click + pane right-click).

The component was already implemented and wired (page.tsx:534) but the
FrameOS behavior gap table still listed 右键菜单 as 未实现 — this batch
verifies the flow end-to-end and corrects the stale doc row.
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
    / "liblib-frameos-batch157-2026-09-07"
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
        assert ok, f"batch157 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/frameos/canvas/demo", wait_until="domcontentloaded")
    page.wait_for_timeout(1200)
    nodes_before = page.locator(".react-flow__node").count()
    check("boot:nodes", nodes_before >= 3)

    # 节点右键 → 菜单出现（复制/创建副本/删除）
    node = page.locator(".react-flow__node").first
    node.click(button="right")
    page.wait_for_timeout(300)
    menu = page.locator("[data-frameos-context-menu]")
    check("node:menu-open", menu.is_visible())
    for item in ["复制", "创建副本", "删除"]:
        check(f"node:item:{item}", menu.locator(f"[data-frameos-context-item='{item}']").is_visible())

    # 创建副本 → 节点数 +1、菜单关闭
    menu.locator("[data-frameos-context-item='创建副本']").click()
    page.wait_for_timeout(600)
    check("node:duplicate-added", page.locator(".react-flow__node").count() == nodes_before + 1)
    check("node:menu-closed", menu.count() == 0)
    page.keyboard.press("Meta+z")
    page.wait_for_timeout(400)

    # 画布空白右键 → 添加文本节点
    pane = page.locator(".react-flow__pane")
    pane.click(button="right", position={"x": 700, "y": 500})
    page.wait_for_timeout(300)
    check("pane:menu-open", menu.is_visible())
    check(
        "pane:item:add-text",
        menu.locator("[data-frameos-context-item='添加文本节点']").is_visible(),
    )
    menu.locator("[data-frameos-context-item='添加文本节点']").click()
    page.wait_for_timeout(600)
    check("pane:text-added", page.locator(".react-flow__node").count() == nodes_before + 1)
    page.keyboard.press("Meta+z")
    page.wait_for_timeout(400)

    # Esc 关闭
    node.click(button="right")
    page.wait_for_timeout(300)
    page.keyboard.press("Escape")
    page.wait_for_timeout(200)
    check("esc:closes-menu", page.locator("[data-frameos-context-menu]").count() == 0)

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 157, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch157: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
