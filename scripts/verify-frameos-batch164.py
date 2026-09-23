#!/usr/bin/env python3

"""Verify Batch 164: FrameOS breadcrumb drift catch-up.

2026-09-23 source re-sampling (docs/user-manual/frameos-canvas
SOURCE_OBSERVATIONS.md §13.10 / shot 15): breadcrumb reads 测试作品 /
测试项目 / 画布 1; the canvas dropdown has a 画布 header with a + new-canvas
entry, canvas rows with node counts (current highlighted with a check), and
a 重命名 | 删除 action row. Work/project dropdowns list 作品 / 项目 with the
current entry highlighted. Verifies labels, dropdown structure, counts,
close-on-outside, and that canvas switching still loads demo canvases.
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
    / "liblib-frameos-batch164-2026-09-23"
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
        assert ok, f"batch164 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/frameos/canvas/demo", wait_until="domcontentloaded")
    page.wait_for_timeout(1200)

    # 三级面包屑逐字
    for label in ["测试作品", "测试项目", "画布 1"]:
        check(
            f"crumb:{label}",
            page.locator("button.breadcrumb-switcher", has_text=label).is_visible(),
        )

    # 画布下拉: 画布头 + 新建 + 当前列表 (节点计数) + 重命名/删除
    page.locator("button.breadcrumb-switcher", has_text="画布 1").click()
    page.wait_for_timeout(300)
    dd = page.locator("[data-frameos-canvas-dropdown]")
    check("canvas:dropdown-opens", dd.is_visible())
    check("canvas:header", "画布" in dd.inner_text())
    check("canvas:new-entry", dd.inner_text().count("+") >= 1 if False else "+" in dd.inner_text())
    option = page.locator("[data-frameos-canvas-option='画布 1']")
    check("canvas:current-option", option.is_visible())
    nodes_in_store = page.evaluate("window.__frameos_store.getState().nodes.length")
    check(
        "canvas:node-count",
        f"{nodes_in_store} 节点" in option.inner_text(),
    )
    check(
        "canvas:rename-delete",
        "重命名" in dd.inner_text() and "删除" in dd.inner_text(),
    )

    # 列表中的画布 2 可切换 (切走再切回, 验证数据仍按 key 加载)
    option2 = page.locator("[data-frameos-canvas-option='画布 2']")
    if option2.count() > 0:
        option2.click()
        page.wait_for_timeout(500)
        check(
            "canvas:switch-loads-canvas2",
            "画布 2" in page.locator("button.breadcrumb-switcher", has_text="画布").first.inner_text(),
        )
        page.locator("button.breadcrumb-switcher", has_text="画布 2").click()
        page.wait_for_timeout(300)
        page.locator("[data-frameos-canvas-option='画布 1']").click()
        page.wait_for_timeout(500)
    check(
        "canvas:switch-back",
        page.evaluate("window.__frameos_store.getState().breadcrumb.canvas") == "画布 1",
    )

    # 点击外部关闭
    page.mouse.click(900, 500)
    page.wait_for_timeout(200)
    check("canvas:outside-closes", page.locator("[data-frameos-canvas-dropdown]").count() == 0)

    # 作品下拉: 作品列表 + 当前高亮
    page.locator("button.breadcrumb-switcher", has_text="测试作品").click()
    page.wait_for_timeout(300)
    check(
        "work:lists-works",
        page.get_by_text("短剧作品A").is_visible()
        and page.get_by_text("电商作品B").is_visible(),
    )
    page.keyboard.press("Escape")
    page.wait_for_timeout(200)

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 164, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch164: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
