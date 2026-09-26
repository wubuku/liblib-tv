#!/usr/bin/env python3

"""Verify Batch 161: FrameOS focus mode (聚焦模式).

2026-09-23 source re-sampling (docs/user-manual/frameos-canvas
SOURCE_OBSERVATIONS.md §13.4 / screenshot 19): clicking 聚焦 on the image
prompt panel header enters focus mode — the node is covered by an overlay
reading 聚焦模式 / 请选择一张图像进行「局部框选」操作 / 按 ESC 键可退出当前
模式, plus a top bar 请在图片上框选聚焦区域 with 返回节点 / 退出 buttons.
Esc also exits. Verifies entry, all three exit paths, and the batch-158
text-node guard regression.
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
    / "liblib-frameos-batch161-2026-09-23"
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


def enter_focus_mode(page: Page) -> None:
    page.locator(".react-flow__node-image").first.click()
    page.wait_for_timeout(300)
    page.get_by_role("button", name="聚焦").click()
    page.wait_for_timeout(300)


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool) -> None:
        assert ok, f"batch161 check failed: {name}"
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

    # 进入聚焦模式
    enter_focus_mode(page)
    overlay = page.locator("[data-frameos-focus-mode]")
    topbar = page.locator("[data-frameos-focus-topbar]")
    check("focus:overlay-opens", overlay.is_visible())
    check("focus:topbar-opens", topbar.is_visible())
    check(
        "focus:overlay-copy",
        "聚焦模式" in overlay.inner_text()
        and "局部框选" in overlay.inner_text()
        and "ESC" in overlay.inner_text(),
    )
    check(
        "focus:topbar-buttons",
        topbar.get_by_role("button", name="返回节点").is_visible()
        and topbar.get_by_role("button", name="退出").is_visible(),
    )

    # 退出按钮
    topbar.get_by_role("button", name="退出").click()
    page.wait_for_timeout(300)
    check("focus:exit-closes", overlay.count() == 0 and topbar.count() == 0)

    # 重新进入 → Esc 退出
    enter_focus_mode(page)
    check("focus:re-enter", overlay.is_visible())
    page.keyboard.press("Escape")
    page.wait_for_timeout(300)
    check("focus:esc-closes", overlay.count() == 0 and topbar.count() == 0)

    # 重新进入 → 返回节点关闭
    enter_focus_mode(page)
    topbar.get_by_role("button", name="返回节点").click()
    page.wait_for_timeout(300)
    check("focus:back-closes", overlay.count() == 0 and topbar.count() == 0)

    # 回归: 文本节点不渲染 prompt 面板 (batch158)
    text_node = page.locator(".react-flow__node-text").first
    if text_node.count() == 0:
        pane = page.locator(".react-flow__pane")
        pane.click(button="right", position={"x": 700, "y": 480})
        page.wait_for_timeout(300)
        page.locator("[data-frameos-context-item='添加文本节点']").click()
        page.wait_for_timeout(600)
    page.locator(".react-flow__node-text").first.click()
    page.wait_for_timeout(300)
    check("regression:text-guard", page.locator(".frameos-prompt-editor").count() == 0)

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 161, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch161: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
