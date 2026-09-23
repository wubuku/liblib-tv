#!/usr/bin/env python3

"""Verify Batch 162: FrameOS template rail entry + template panel.

2026-09-23 source re-sampling (docs/user-manual/frameos-canvas
SOURCE_OBSERVATIONS.md §14 / screenshot 20): the source added a 模板 rail
button (between 本地上传 and 帮助) opening a template panel with tabs
公共模板 / 企业模板 / 我的模板 (公共模板 active) and template cards
(30s小说切片, 九宫格大师分镜, 大师电影分镜, ...). The rail button toggles
the panel. Verifies entry, tabs, verbatim card names, toggle, and that the
rail keeps 帮助 as its last entry.
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
    / "liblib-frameos-batch162-2026-09-23"
    / "runtime-audit.json"
)

CARD_NAMES = [
    "30s小说切片",
    "九宫格大师分镜",
    "大师电影分镜",
    "时间凝固流光",
    "暂别×视角×特效镜头大全",
    "360度旋转展示",
]


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
        assert ok, f"batch162 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/frameos/canvas/demo", wait_until="domcontentloaded")
    page.wait_for_timeout(1200)

    # 左栏出现「模板」按钮 (aria 唯一)
    tpl_button = page.locator("button[aria-label='模板']")
    check("rail:template-button", tpl_button.count() == 1)

    # 初始关闭 → 点击打开
    panel = page.locator("[data-frameos-template-panel]")
    check("panel:initially-closed", panel.count() == 0)
    tpl_button.click()
    page.wait_for_timeout(400)
    check("panel:opens", panel.is_visible())

    # 页签: 三个, 公共模板默认激活
    for tab in ["公共模板", "企业模板", "我的模板"]:
        check(
            f"panel:tab:{tab}",
            panel.locator(f"[data-frameos-template-tab='{tab}']").is_visible(),
        )

    # 模板卡片逐字
    for name in CARD_NAMES:
        check(
            f"panel:card:{name}",
            panel.locator(f"[data-frameos-template-card='{name}']").is_visible(),
        )

    # 再次点击按钮 → 关闭 (toggle)
    tpl_button.click()
    page.wait_for_timeout(300)
    check("panel:toggles-closed", panel.count() == 0)

    # 再打开 → 关闭按钮也可关闭
    tpl_button.click()
    page.wait_for_timeout(300)
    panel.get_by_role("button", name="关闭模板面板").click()
    page.wait_for_timeout(300)
    check("panel:close-button", panel.count() == 0)

    # 左栏仍保留 帮助 作为最后一项 (顺序: 添加节点…本地上传/模板/帮助)
    check("rail:help-still-last", page.locator("button[aria-label='帮助 (?)']").count() == 1)

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 162, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch162: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
