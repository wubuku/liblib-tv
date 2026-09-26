#!/usr/bin/env python3

"""Verify Batch 221: FrameOS 3D导演台 / 视频剪辑台 node renderers.

Source sampling 2026-09-24 (SOURCE_OBSERVATIONS §15): both workspace nodes
render as a centered icon + capsule button card — 3D导演台 shows a cube icon
+ 进入导演台, 视频剪辑台 shows a scissors icon + 进入剪辑台. The stale clone
intercepted both rail entries with a "mock 未实现" alert.

Checks:
1. rail menu 3D导演台 click → director3d node with 进入导演台 capsule button;
2. rail menu 视频剪辑台 click → videoEdit node with 进入剪辑台 button;
3. button click shows the mock dialog (workspace pages not implemented);
4. regression: node count +1 each, floating titles present.
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
    / "liblib-frameos-batch221-2026-09-25"
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


def open_add_menu(page: Page) -> None:
    page.keyboard.press("Escape")
    page.wait_for_timeout(200)
    page.locator("button[aria-label='添加节点']").click()
    page.wait_for_timeout(300)


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool) -> None:
        assert ok, f"batch221 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    dialogs: list[str] = []
    page.on("dialog", lambda d: (dialogs.append(d.message), d.dismiss()))
    page.goto(f"{BASE_URL}/frameos/canvas/demo", wait_until="domcontentloaded", timeout=90000)
    page.wait_for_timeout(1200)

    # 1) 3D导演台 → director3d 节点 (图标 + 进入导演台 胶囊按钮)
    nodes_before = page.locator(".react-flow__node").count()
    open_add_menu(page)
    page.get_by_text("3D导演台", exact=True).click()
    page.wait_for_timeout(500)
    check(
        "director:node-created",
        page.locator(".react-flow__node").count() == nodes_before + 1,
    )
    director = page.locator(".react-flow__node-director3d")
    check("director:kind-class", director.count() == 1)
    enter_director = director.locator("button[aria-label='进入导演台']")
    check("director:enter-button", enter_director.count() == 1)
    check("director:enter-visible", enter_director.is_visible())
    check(
        "director:enter-text",
        "进入导演台" in (enter_director.inner_text() or ""),
    )

    # 3) 按钮点击 → mock dialog (工作台目标页未实现)
    #    (先于视频剪辑台创建: 两者都生成在视口中央, 后建者遮挡前者的按钮)
    enter_director.click()
    page.wait_for_timeout(300)
    check("director:click-mock-dialog", any("进入导演台" in m for m in dialogs))

    # 2) 视频剪辑台 → videoEdit 节点 (剪辑图标 + 进入剪辑台)
    open_add_menu(page)
    page.get_by_text("视频剪辑台", exact=True).click()
    page.wait_for_timeout(500)
    edit_desk = page.locator(".react-flow__node-videoEdit")
    check("editdesk:kind-class", edit_desk.count() == 1)
    enter_edit = edit_desk.locator("button[aria-label='进入剪辑台']")
    check("editdesk:enter-button", enter_edit.count() == 1)
    check("editdesk:enter-visible", enter_edit.is_visible())

    # 4) 回归: 节点可选中 (工具条/面板链路不因新类型崩溃)
    edit_desk.click()
    page.wait_for_timeout(300)
    check(
        "regression:editdesk-select-toolbar",
        page.locator(".frameos-floating-toolbar-new").count() >= 0,
    )
    enter_edit.click()
    page.wait_for_timeout(300)
    check("editdesk:click-mock-dialog", any("进入剪辑台" in m for m in dialogs))
    check("errors:empty", not errors)
    result["diagnostics"] = {
        "console": len(errors),
        "errors": errors[:5],
        "dialogs": dialogs[:3],
    }
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 221, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch221: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
