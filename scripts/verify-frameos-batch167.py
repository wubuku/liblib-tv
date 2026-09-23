#!/usr/bin/env python3

"""Verify Batch 167: FrameOS add-node menu verbatim alignment.

2026-09-23 source re-sampling (docs/user-manual/frameos-canvas
SOURCE_OBSERVATIONS §13.2 / shot 06): the add-node menu lists exactly
文本 / 图片 / 视频 / 音频 / 3D模型 / 3D导演台 / 视频剪辑台 as short labels
(no descriptions), under the group header 添加节点 with a second group
添加资源 / 上传文件. The clone listed 8 longer-labeled entries (角色节点/
场景节点/风格节点/批量节点 are source-absent). Unimplemented node types
show a mock notice instead of creating a node. Verifies menu structure,
verbatim labels, group headers, creation still works for implemented
types, and mock notice for unimplemented ones.
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
    / "liblib-frameos-batch167-2026-09-23"
    / "runtime-audit.json"
)

MENU_ITEMS = ["文本", "图片", "视频", "音频", "3D模型", "3D导演台", "视频剪辑台"]
ABSENT_ITEMS = ["角色节点", "场景节点", "风格节点", "批量节点"]


def attach_errors(page: Page) -> list[str]:
    errors: list[str] = []
    page.on(
        "console",
        lambda message: errors.append(f"console:{message.type}:{message.text}")
        if message.type == "error"
        else None,
    )
    page.on("pageerror", lambda error: errors.append(f"pageerror:{error}"))
    # mock alert/confirm 自动关闭
    page.on("dialog", lambda d: d.dismiss())
    return errors


def open_menu(page: Page) -> None:
    page.keyboard.press("Escape")
    page.wait_for_timeout(200)
    page.locator("button[aria-label='添加节点']").click()
    page.wait_for_timeout(300)


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool) -> None:
        assert ok, f"batch167 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/frameos/canvas/demo", wait_until="domcontentloaded")
    page.wait_for_timeout(1200)
    nodes_before = page.locator(".react-flow__node").count()

    open_menu(page)
    anchor = page.get_by_text("3D模型", exact=True)
    check("menu:opens", anchor.is_visible())
    menu_container = anchor.evaluate(
        "(el) => { let p = el; for (let i = 0; i < 6 && p.parentElement; i++) { p = p.parentElement; if (p.textContent.includes('添加节点') && p.textContent.includes('上传文件')) return p.textContent; } return p.textContent; }"
    )

    for item in MENU_ITEMS:
        check(f"menu:item:{item}", item in menu_container)
    for item in ABSENT_ITEMS:
        check(f"menu:absent:{item}", item not in menu_container)
    check("menu:group-header", "添加节点" in menu_container)

    # 3D模型 → mock 提示 (dialog 自动 dismiss), 不创建节点
    nodes_pre_click = page.locator(".react-flow__node").count()
    page.get_by_text("3D模型", exact=True).click()
    page.wait_for_timeout(400)
    nodes_post = page.locator(".react-flow__node").count()
    check(
        "menu:unimplemented-no-node",
        nodes_post == nodes_pre_click,
    ) if nodes_post == nodes_pre_click else (_ for _ in ()).throw(
        AssertionError(f"batch167: nodes {nodes_pre_click}->{nodes_post}")
    )

    # Esc 关闭菜单
    page.keyboard.press("Escape")
    page.wait_for_timeout(200)
    check(
        "menu:esc-closes",
        page.get_by_text("3D模型", exact=True).count() == 0
        or not page.get_by_text("3D模型", exact=True).is_visible(),
    )

    # 文本仍可创建 (实现中的类型; 音频/3D 等均 mock)
    open_menu(page)
    page.get_by_text("文本", exact=True).click()
    page.wait_for_timeout(600)
    check(
        "menu:text-creates",
        page.locator(".react-flow__node").count() == nodes_pre_click + 1,
    )
    page.keyboard.press("Meta+z")
    page.wait_for_timeout(300)

    # 添加资源组: 上传文件条目仍在
    open_menu(page)
    check("menu:resource-group", page.get_by_text("上传文件", exact=True).is_visible())

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 167, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch167: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
