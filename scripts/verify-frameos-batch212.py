#!/usr/bin/env python3

"""Verify Batch 212: FrameOS material library dialog aligned to source.

Source structure (manual SOURCE_OBSERVATIONS §13.10 / shot 17): title
选择素材 with subtitle 从素材库选择图片或视频作为生成参考; left directory
tree (测试项目 > 工具箱素材/画布素材/上传素材); search 搜索当前文件夹;
filter row 全部/图片/视频/音频/3D; 批量操作 + 本地上传 buttons; mock asset
cards; footer 已选 N 个 / 取消 / 添加参考素材. Generic folder names only.
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
    / "liblib-frameos-batch212-2026-09-24"
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
        assert ok, f"batch212 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/frameos/canvas/demo", wait_until="domcontentloaded")
    page.wait_for_timeout(1200)

    # 打开素材库 (左栏 从素材库选择 → 事件)
    page.locator("button[aria-label='从素材库选择']").click()
    page.wait_for_timeout(500)
    dialog = page.locator("[aria-label='素材库']")
    check("lib:opens", dialog.is_visible())

    text = dialog.inner_text()
    for k in [
        "选择素材",
        "从素材库选择图片或视频作为生成参考",
        "分类",
        "工具箱素材",
        "画布素材",
        "上传素材",
        "批量操作",
        "+ 本地上传",
        "添加参考素材",
        "取消",
    ]:
        check(f"lib:text:{k}", k in text)

    # 搜索框占位 (属性而非文本)
    ph = dialog.locator("input").first.get_attribute("placeholder")
    check("lib:search-placeholder", ph == "搜索当前文件夹")

    # 筛选行: 全部/图片/视频/音频/3D
    for f in ["全部", "图片", "视频", "音频", "3D"]:
        check(f"lib:filter:{f}", f in text)

    # mock 素材卡片渲染 (泛化名) + 点击选中 → 已选 1 个
    card = dialog.locator("[data-frameos-material-card]").first
    check("lib:cards-render", card.is_visible())
    card.click()
    page.wait_for_timeout(300)
    footer = dialog.inner_text()
    check("lib:footer-selected", "已选 1 个" in footer)

    # 取消关闭
    dialog.get_by_role("button", name="取消选择素材").click()
    page.wait_for_timeout(300)
    check("lib:closes", page.locator("[aria-label='素材库']").count() == 0)

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 212, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch212: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
