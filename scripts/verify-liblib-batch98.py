#!/usr/bin/env python3

"""Verify Batch 98 add-node panel alignment with the 2026-09-05 source audit."""

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
    / "liblib-canvas-batch98-2026-09-05"
    / "runtime-audit.json"
)

EXPECTED_LABELS = [
    "文本",
    "图片",
    "视频",
    "智能剪辑",
    "导演台",
    "逐帧拉片",
    "音频",
    "脚本",
    "素材库",
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
    page.on(
        "requestfailed",
        lambda request: errors.append(
            f"requestfailed:{request.method}:{request.url}:{request.failure}"
        ),
    )
    return errors


def open_add_node(page: Page) -> Any:
    page.get_by_role("button", name="添加节点").click()
    panel = page.locator('[data-liblib-overlay="add-node"]')
    assert panel.is_visible()
    return panel


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool) -> None:
        assert ok, f"batch98 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(BASE_URL, wait_until="networkidle")
    page.wait_for_timeout(400)
    initial_nodes = page.locator(".react-flow__node").count()
    initial_script_nodes = page.locator(".react-flow__node-script").count()

    panel = open_add_node(page)
    check("entries:count", panel.locator("[data-add-node-entry]").count() == 9)
    for label in EXPECTED_LABELS:
        check(
            f"entries:label:{label}",
            panel.locator("[data-add-node-entry]").filter(has_text=label).count() == 1,
        )
    check(
        "entries:badge:video-clip",
        panel.locator('[data-add-node-entry="video-clip"]').inner_text().replace("\n", "") == "智能剪辑Beta",
    )
    check(
        "entries:badge:director",
        "NEW" in panel.locator('[data-add-node-entry="script-execution"]').inner_text(),
    )
    check(
        "entries:badge:shot-breakdown",
        "SD 2.5" in panel.locator('[data-add-node-entry="shot-breakdown"]').inner_text(),
    )

    panel.locator("[data-add-node-search-toggle]").click()
    search = panel.locator("[data-add-node-search]")
    check("search:open", search.is_visible())
    search.fill("脚本")
    check("search:filter", panel.locator("[data-add-node-entry]").count() == 1)
    search.fill("不存在节点")
    check("search:empty-hint", panel.locator("[data-add-node-empty]").is_visible())
    search.fill("")
    check("search:clear-restores", panel.locator("[data-add-node-entry]").count() == 9)
    panel.locator("[data-add-node-search-toggle]").click()
    check("search:toggle-closes", panel.locator("[data-add-node-search]").count() == 0)

    panel.locator('[data-add-node-entry="script"]').click()
    script_menu = page.locator('[data-add-node-submenu="script"]')
    check("script-menu:open", script_menu.is_visible())
    check(
        "script-menu:new-entry",
        script_menu.locator('[data-add-node-entry="script-new"]').inner_text().replace("\n", "").endswith("NEW"),
    )
    check(
        "script-menu:legacy-entry",
        script_menu.locator('[data-add-node-entry="script-legacy"]').inner_text().replace("\n", "").endswith("Beta"),
    )
    # Batch 116: 源站脚本NEW已可创建节点（脚本生成器），断言随采样更新。
    script_menu.locator('[data-add-node-entry="script-new"]').click()
    page.wait_for_timeout(800)
    check(
        "script-menu:new-creates-generator",
        "脚本生成器"
        in page.locator(".react-flow__node-script-generator").first.inner_text(),
    )
    check(
        "panel:closes-on-create",
        not page.locator('[data-liblib-overlay="add-node"]').is_visible(),
    )
    panel = open_add_node(page)
    panel.locator('[data-add-node-entry="script"]').click()
    page.wait_for_timeout(400)
    script_menu = page.locator('[data-add-node-submenu="script"]')
    script_menu.locator('[data-add-node-entry="script-legacy"]').click()
    check(
        "script-menu:legacy-creates",
        page.locator(".react-flow__node-script").count() == initial_script_nodes + 1,
    )
    check("script-menu:legacy-closes-panel", not page.locator('[data-liblib-overlay="add-node"]').is_visible())
    # Batch 116: 脚本NEW 与 脚本（旧版） 各创建一个节点，共 +2。
    check(
        "script-menu:node-count",
        page.locator(".react-flow__node").count() == initial_nodes + 2,
    )

    panel = open_add_node(page)
    panel.locator('[data-add-node-entry="material"]').click()
    material_menu = page.locator('[data-add-node-submenu="material"]')
    check("material-menu:open", material_menu.is_visible())
    check("material-menu:style", material_menu.get_by_role("button", name="风格库").count() == 1)
    check("material-menu:effect", material_menu.get_by_role("button", name="特效库").count() == 1)
    material_menu.get_by_role("button", name="风格库").click()
    check("material-menu:opens-panel", page.locator('[data-liblib-overlay="primary:material"]').is_visible())
    page.keyboard.press("Escape")

    panel = open_add_node(page)
    panel.locator('[data-add-node-resource="upload"]').click()
    check("resource:upload-status", "上传服务未连接" in panel.locator("[data-add-node-status]").inner_text())
    panel.locator('[data-add-node-resource="history"]').click()
    check("resource:history-status", "生成历史未连接" in panel.locator("[data-add-node-status]").inner_text())

    check("diagnostics:zero", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 98,
        "title": "Add-node panel alignment with 2026-09-05 source audit",
        "evidence": "docs/research/liblib-live-2026-09-05/README.md",
        "results": [],
    }
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        desktop = browser.new_page(viewport={"width": 1440, "height": 900}, device_scale_factor=1)
        audit["results"].append(run_desktop(desktop))
        desktop.close()
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    checks = audit["results"][0]["checks"]
    print(
        "Batch 98 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "Entry labels/badges, search filter, script NEW/legacy flyout, "
        "material style/effect flyout and local resource statuses recorded "
        "in runtime-audit.json."
    )


if __name__ == "__main__":
    main()
