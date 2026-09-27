#!/usr/bin/env python3
"""Verify Batch 534: storyboard session ↔ script-generator node conversion.

Contract: source-site CDP sampling 2026-09-27 (screenshot 39) — after a
self-write storyboard session the script generator card converts to the
progress-card form (①确认镜头—②准备资产—③合成提示词 + 打开脚本节点 →),
persistently (the canvas kept the progress card across reloads). In the
clone, clicking 自己编写分镜脚本 marks the node as the storyboard session
node (uiStore.storyboardSessionNodeId, intentionally not reset by other
panel toggles); the card renders the progress form and the button reopens
the editor. The two generate entries keep the batch-528 follow contract
and are gone after conversion (the source card shows no attempt entries
in progress form).
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
    / "liblib-canvas-batch534-2026-09-27"
    / "runtime-audit.json"
)

SELF_WRITE = "自己编写分镜脚本"
GEN_ENTRY = "剧本生成分镜脚本"


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


def add_script_generator(page: Page) -> Any:
    page.get_by_role("button", name="添加节点").click()
    page.wait_for_timeout(400)
    panel = page.locator('[data-liblib-overlay="add-node"]')
    panel.locator("[data-add-node-entry='script']").click()
    page.wait_for_timeout(300)
    panel.locator("[data-add-node-entry='script-new']").click()
    page.wait_for_timeout(700)
    return page.locator(".react-flow__node-script-generator").first


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool) -> None:
        assert ok, f"batch534 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(BASE_URL, wait_until="networkidle")
    page.wait_for_timeout(400)

    # 会话前：三入口卡（batch 116/528 形态），生成入口跟随可用
    node = add_script_generator(page)
    check("fresh:entries-visible", node.locator("[data-script-generator-attempt]").count() == 3)
    node.locator(f"[data-script-generator-attempt='{GEN_ENTRY}']").click()
    page.wait_for_timeout(200)
    banner = page.locator("[data-follow-banner]")
    check("fresh:follow-works", banner.get_attribute("aria-hidden") == "false")
    banner.locator("[data-follow-cancel]").click()
    page.wait_for_timeout(200)

    # 自写会话 → 转进度卡
    node.locator(f"[data-script-generator-attempt='{SELF_WRITE}']").click()
    page.wait_for_timeout(300)
    editor = page.locator("[data-storyboard-editor]")
    check("session:editor-opens", editor.is_visible())
    editor.click(position={"x": 700, "y": 300})
    page.keyboard.press("Escape")
    page.wait_for_timeout(250)
    check("session:editor-closed", page.locator("[data-storyboard-editor]").count() == 0)

    check("converted:entries-gone", node.locator("[data-script-generator-attempt]").count() == 0)
    check("converted:steps", all(t in node.inner_text() for t in ["确认镜头", "准备资产", "合成提示词"]))
    open_button = node.locator("[data-script-generator-open-storyboard]")
    check("converted:open-button", "打开脚本节点" in open_button.inner_text())

    # 转换持久：打开工具箱面板不回退（closedOverlayState 不重置会话标记）
    page.get_by_role("button", name="打开工具箱").click()
    page.wait_for_timeout(300)
    page.keyboard.press("Escape")
    page.wait_for_timeout(200)
    check("persistent:after-panel-toggle", node.locator("[data-script-generator-open-storyboard]").count() == 1)

    # 进度卡按钮重入编辑器
    open_button.click()
    page.wait_for_timeout(250)
    check("reentry:editor-opens", page.locator("[data-storyboard-editor]").is_visible())
    page.locator("[data-storyboard-close]").click()
    page.wait_for_timeout(250)
    check("reentry:close-button", page.locator("[data-storyboard-editor]").count() == 0)

    check("diagnostics:zero", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 534,
        "title": "Storyboard session ↔ script-generator node conversion",
        "evidence": (
            "docs/research/liblib-source-exploration-2026-09-25/NOTES.md "
            "§11 update + screenshot 39 (CDP 2026-09-27)"
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
        "Batch 534 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "self-write session converts the card to the persistent progress "
        "form, generate-entry follow still works pre-conversion and the "
        "progress button reopens the editor, recorded in runtime-audit.json."
    )


if __name__ == "__main__":
    main()
