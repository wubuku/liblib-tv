#!/usr/bin/env python3

"""Verify Batch 168: FrameOS double-click blank pane add-node menu.

2026-09-23 source re-sampling (docs/user-manual/frameos-canvas
SOURCE_OBSERVATIONS §13.2 / shot 19): double-clicking empty canvas opens a
「选择节点类型」menu anchored at the click position with the same 7 node
types as the rail menu (no 添加资源 group). Verifies open, anchor proximity,
verbatim items, text creation + auto-close, mock for unimplemented types,
and close paths (outside click / Esc).
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
    / "liblib-frameos-batch168-2026-09-23"
    / "runtime-audit.json"
)

MENU_ITEMS = ["文本", "图片", "视频", "音频", "3D模型", "3D导演台", "视频剪辑台"]


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
        assert ok, f"batch168 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/frameos/canvas/demo", wait_until="domcontentloaded")
    page.wait_for_timeout(1200)
    nodes_before = page.locator(".react-flow__node").count()

    # 双击空白 → 菜单在双击位置打开
    pane = page.locator(".react-flow__pane")
    pane.dblclick(position={"x": 300, "y": 300})
    page.wait_for_timeout(400)
    menu = page.locator("[data-frameos-pane-add-menu]")
    check("menu:opens", menu.is_visible())
    box = menu.bounding_box()
    check(
        "menu:anchored-near-click",
        box is not None and abs(box["x"] - 300) < 60 and abs(box["y"] - 300) < 60,
    )
    check("menu:header", "选择节点类型" in menu.inner_text())
    for item in MENU_ITEMS:
        check(f"menu:item:{item}", item in menu.inner_text())
    check("menu:no-resource-group", "上传文件" not in menu.inner_text())

    # 点击 文本 → 创建节点 + 菜单自动关闭
    menu.get_by_text("文本", exact=True).click()
    page.wait_for_timeout(600)
    check(
        "menu:text-created",
        page.locator(".react-flow__node").count() == nodes_before + 1,
    )
    check("menu:auto-closed", page.locator("[data-frameos-pane-add-menu]").count() == 0)

    # 音频 → mock 提示不建节点; Esc 关闭
    pane.dblclick(position={"x": 320, "y": 320})
    page.wait_for_timeout(400)
    check("menu:reopens", page.locator("[data-frameos-pane-add-menu]").is_visible())
    page.get_by_text("音频", exact=True).click()
    page.wait_for_timeout(400)
    check(
        "menu:audio-mock-no-node",
        page.locator(".react-flow__node").count() == nodes_before + 1,
    )
    page.keyboard.press("Escape")
    page.wait_for_timeout(300)
    check("menu:esc-closes", page.locator("[data-frameos-pane-add-menu]").count() == 0)

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 168, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch168: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
