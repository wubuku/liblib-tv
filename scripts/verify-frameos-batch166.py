#!/usr/bin/env python3

"""Verify Batch 166: FrameOS help panel content drift catch-up.

2026-09-23 source re-sampling (docs/user-manual/frameos-canvas
SOURCE_OBSERVATIONS.md §13.9): the 快捷键 panel groups 创作/缩放/移动画布/
其他 and lists 26 verbatim rows incl. description-style rows (双击空白 →
双击空白处添加节点, 拖拽复制 → ⌥ 拖动节点, ...). The clone was missing
双击空白 / 双击节点 / 搜索节点 rows and listed a source-absent 全选 row.
Verifies all rows and group titles verbatim on the clone, open via ? key,
and × close.
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
    / "liblib-frameos-batch166-2026-09-23"
    / "runtime-audit.json"
)

ROWS = [
    "双击空白", "双击空白处添加节点", "复制", "剪切", "粘贴",
    "原地复制", "拖拽复制", "⌥ 拖动节点", "保存",
    "双击节点", "双击节点聚焦填满视口", "放大", "缩小", "重置视图",
    "触控板", "双指捏合", "鼠标滚轮", "⌘ 滚轮",
    "空格拖动", "左键拖动", "双指平移", "鼠标中键 / 右键拖动", "滚轮平移",
    "撤销", "重做", "删除", "搜索节点", "小地图", "帮助", "取消选中",
]

GROUPS = ["创作", "缩放", "移动画布", "其他"]


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
        assert ok, f"batch166 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/frameos/canvas/demo", wait_until="domcontentloaded", timeout=90000)
    page.wait_for_timeout(1200)

    # ? 键打开
    page.keyboard.press("?")
    page.wait_for_timeout(400)
    panel = page.locator(".frameos-shortcuts-panel")
    check("help:opens-with-question", panel.is_visible())
    check("help:title-快捷键", "快捷键" in panel.inner_text())

    text = panel.inner_text()
    for group in GROUPS:
        check(f"help:group:{group}", group in text)
    for row in ROWS:
        check(f"help:row:{row}", row in text)

    # 源站没有的 全选 行已被移除
    check("help:no-source-absent-全选", "全选" not in text)

    # × 关闭
    panel.get_by_role("button", name="关闭").click()
    page.wait_for_timeout(300)
    check("help:close-x", panel.count() == 0)

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 166, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch166: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
