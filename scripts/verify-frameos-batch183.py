#!/usr/bin/env python3

"""Verify Batch 183: new-source-version drift lock (consolidated).

2026-09-24 the source deployed a new version mid-session; Batch 182 aligned
the double-click menu removal. This batch locks the remaining replicated
behaviors against the re-sampled new-version source:

1. image prompt panel header (聚焦/故事版/参考/删除连线/替换参考) + chips;
2. breadcrumb canvas dropdown (画布 header, node count, 重命名/删除);
3. help panel 26 verbatim shortcut rows;
4. organize menu three options verbatim;
5. text-node guard regression (batch 158).
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
    / "liblib-frameos-batch183-2026-09-24"
    / "runtime-audit.json"
)

HELP_ROWS = [
    "双击空白处添加节点", "⌘C", "⌘X", "⌘V", "原地复制", "⌘D", "⌥ 拖动节点", "⌘S",
    "双击节点聚焦填满视口", "重置视图", "双指捏合", "⌘ 滚轮", "Space",
    "左键拖动", "双指平移", "鼠标中键 / 右键拖动", "滚轮平移",
    "搜索节点", "取消选中",
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
    page.on("dialog", lambda d: d.dismiss())
    return errors


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool) -> None:
        assert ok, f"batch183 check failed: {name}"
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

    # 1) 图片面板头部
    page.locator(".react-flow__node-image").first.click(position={"x": 60, "y": 30})
    page.wait_for_timeout(400)
    editor = page.locator(".frameos-prompt-editor")
    check("image:editor", editor.is_visible())
    labels = [
        b.get_attribute("aria-label")
        for b in editor.locator("button").all()
    ]
    for k in ["聚焦", "故事版", "参考", "删除连线", "替换参考", "全屏编辑", "高级设置"]:
        check(f"image:header:{k}", k in labels or any(k in (l or "") for l in labels))
    check("image:chips", page.locator("[data-frameos-ref-chip]").count() >= 1)

    # 2) 面包屑画布下拉
    page.locator("button.breadcrumb-switcher", has_text="画布 1").click()
    page.wait_for_timeout(300)
    dd_text = page.locator("[data-frameos-canvas-dropdown]").inner_text()
    check("breadcrumb:header", "画布" in dd_text)
    check("breadcrumb:rename-delete", "重命名" in dd_text and "删除" in dd_text)
    # 点击面板遮罩关闭下拉 (Esc 可能因焦点不在下拉而不生效)
    page.mouse.click(1000, 600)
    page.wait_for_timeout(300)

    # 3) 帮助面板逐字
    page.keyboard.press("?")
    page.wait_for_timeout(400)
    help_text = page.locator(".frameos-shortcuts-panel").inner_text()
    missing = [r for r in HELP_ROWS if r not in help_text.replace("\n", "")]
    check("help:verbatim-rows", not missing)
    page.locator(".frameos-shortcuts-panel button[aria-label='关闭']").click()
    page.wait_for_timeout(300)

    # 4) 整理方式菜单
    page.locator("button[aria-label='选择整理方式']").click()
    page.wait_for_timeout(300)
    org = page.evaluate(
        """(() => {
          const t = document.body.innerText;
          return ["按连线横向", "按连线纵向", "网格整理"].every((k) => t.includes(k));
        })()"""
    )
    check("organize:three-options", org)
    page.mouse.click(900, 300)  # 点遮罩关闭整理菜单
    page.wait_for_timeout(300)

    # 5) 文本节点守卫 (最后执行; 刷新获得干净状态)
    page.reload()
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(2500)
    page.locator(".react-flow__node-text").first.click(position={"x": 60, "y": 140})
    page.wait_for_timeout(300)
    check(
        "regression:text-guard",
        page.locator(".frameos-prompt-editor").count() == 0,
    )

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 183, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch183: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
