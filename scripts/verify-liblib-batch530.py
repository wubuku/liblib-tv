#!/usr/bin/env python3
"""Verify Batch 530: image node model trigger menu.

Contract: source-site live sampling 2026-09-25 round 1
(docs/research/liblib-source-exploration-2026-09-25/NOTES.md §3 + screenshot
03b-image-model-menu.png) — the image editor's footer model trigger opens a
menu anchored above the chip with 7 rows (Lib Image 2.5 Pro / 2.5 Fast /
Lib Image / General image Pro / General image V2 / Seedream 5.0 Pro /
Qwen image 3.0), each with a duration pill (30s/20s/60s/50s/25s/20s/60s),
Qwen image 3.0 carrying an 上新 badge; the selected row is highlighted and
shows its description. The closed chip shows the current model name
("Lib Image 2.5 Pro" default per 03b; migration from the historical
"Lib Image" static label which remains on the panorama variant, batch 20).
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
    / "liblib-canvas-batch530-2026-09-27"
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
    page.on(
        "requestfailed",
        lambda request: errors.append(
            f"requestfailed:{request.method}:{request.url}:{request.failure}"
        ),
    )
    return errors


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool) -> None:
        assert ok, f"batch530 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(BASE_URL, wait_until="networkidle")
    page.wait_for_timeout(400)
    initial_nodes = page.locator(".react-flow__node").count()

    # 创建图片节点并选中以打开编辑器
    page.get_by_role("button", name="添加节点").click()
    page.wait_for_timeout(400)
    panel = page.locator('[data-liblib-overlay="add-node"]')
    panel.locator('[data-add-node-entry="image"]').click()
    page.wait_for_timeout(700)
    check("node:created", page.locator(".react-flow__node").count() == initial_nodes + 1)
    node = page.locator(".react-flow__node-image").first
    node.click(position={"x": 20, "y": 20}, force=True)
    page.wait_for_timeout(300)
    editor = page.locator("[data-image-edit-panel]").first
    check("editor:open", editor.is_visible())

    chip = editor.locator("[data-image-editor-model]")
    # 闭合态展示当前模型名（截图 03b 当前源站合同；panorama 变体保持 batch 20 旧合同）
    check("chip:default-label", chip.inner_text().strip() == "Lib Image 2.5 Pro")
    check("chip:collapsed", chip.get_attribute("aria-expanded") == "false")

    # 打开菜单：7 行模型 + 时长胶囊 + 上新徽标 + 选中态描述
    chip.click()
    page.wait_for_timeout(200)
    menu = editor.locator("[data-image-model-menu]")
    check("menu:opens", menu.is_visible())
    options = menu.locator("[data-image-model-option]")
    check("menu:seven-models", options.count() == 7)
    check(
        "chip:expanded",
        chip.get_attribute("aria-expanded") == "true",
    )
    for model_id, duration in [
        ("lib-image-2-5-pro", "30s"),
        ("lib-image-2-5-fast", "20s"),
        ("lib-image", "60s"),
        ("general-image-pro", "50s"),
        ("general-image-v2", "25s"),
        ("seedream-5-0-pro", "20s"),
        ("qwen-image-3-0", "60s"),
    ]:
        text = menu.locator(f"[data-image-model-option='{model_id}']").inner_text()
        check(f"menu:duration:{model_id}", duration in text)
    qwen = menu.locator("[data-image-model-option='qwen-image-3-0']")
    check("menu:qwen-new-badge", "上新" in qwen.inner_text())
    selected = menu.locator("[data-image-model-option='lib-image-2-5-pro']")
    check(
        "menu:selected-description",
        selected.get_attribute("aria-pressed") == "true"
        and "精准生成与编辑，复杂指令稳定还原" in selected.inner_text(),
    )

    # 选择模型 → 菜单关闭 + 芯片更新
    menu.locator("[data-image-model-option='general-image-pro']").click()
    page.wait_for_timeout(200)
    check("select:menu-closes", menu.count() == 0)
    check("select:chip-updates", chip.inner_text().strip() == "General image Pro")

    # 再开切换回默认；随后点芯片先开再收（toggle 双向）
    chip.click()
    page.wait_for_timeout(200)
    menu = editor.locator("[data-image-model-menu]")
    check("reopen:menu", menu.is_visible())
    menu.locator("[data-image-model-option='lib-image-2-5-pro']").click()
    page.wait_for_timeout(200)
    check("restore:chip-default", chip.inner_text().strip() == "Lib Image 2.5 Pro")
    chip.click()
    page.wait_for_timeout(200)
    check("toggle:expand", editor.locator("[data-image-model-menu]").is_visible())
    chip.click()
    page.wait_for_timeout(200)
    check("toggle:collapse", editor.locator("[data-image-model-menu]").count() == 0)

    check("diagnostics:zero", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 530,
        "title": "Image node model trigger menu",
        "evidence": (
            "docs/research/liblib-source-exploration-2026-09-25/NOTES.md "
            "§3 + screenshot 03b-image-model-menu.png"
        ),
        "results": [],
    }
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        desktop = browser.new_page(
            viewport={"width": 1440, "height": 900}, device_scale_factor=1
        )
        audit["results"].append(run_desktop(desktop))
        desktop.close()
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    checks = audit["results"][0]["checks"]
    print(
        "Batch 530 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "model trigger menu with 7 sampled models, duration pills, Qwen "
        "上新 badge, selected-row description and chip label sync recorded "
        "in runtime-audit.json."
    )


if __name__ == "__main__":
    main()
