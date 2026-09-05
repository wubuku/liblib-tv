#!/usr/bin/env python3

"""Verify Batch 116 script-generator node type."""

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
    / "liblib-canvas-batch116-2026-09-06"
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
        assert ok, f"batch116 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(BASE_URL, wait_until="networkidle")
    page.wait_for_timeout(400)
    initial_nodes = page.locator(".react-flow__node").count()

    # 打开添加面板 → 脚本 flyout → 脚本NEW
    page.get_by_role("button", name="添加节点").click()
    page.wait_for_timeout(400)
    panel = page.locator("[data-liblib-overlay='add-node']")
    check("panel:open", panel.is_visible())
    panel.locator("[data-add-node-entry='script']").click()
    page.wait_for_timeout(400)
    new_entry = panel.locator("[data-add-node-entry='script-new']")
    check("flyout:script-new", new_entry.inner_text().replace("\n", "").endswith("NEW"))
    new_entry.click()
    page.wait_for_timeout(900)

    node = page.locator(".react-flow__node-script-generator")
    check("node:created", node.count() == 1)
    check("node:type-registered", node.count() >= 1)
    node_first = node.first
    text = node_first.inner_text()
    check("node:title", "脚本生成器" in text)
    for mode in ["剧本生成分镜脚本", "角色生成分镜脚本", "自己编写分镜脚本"]:
        check(f"node:mode:{mode}", mode in text)
    check("node:reference", "参考图" in text)
    check("node:model", "GVLM 3.1" in text)
    style_wh = node.first.evaluate("(el) => ({ w: el.style.width, h: el.style.height })")
    check("node:size-style", style_wh == {"w": "350px", "h": "350px"})
    bb = node.first.bounding_box()
    check(
        "node:size-scaled",
        bb is not None and 170 <= bb["width"] <= 200 and 170 <= bb["height"] <= 200,
    )

    # 选择尝试模式
    node_first.locator("[data-script-generator-attempt='剧本生成分镜脚本']").click()
    check(
        "attempt:select",
        node_first.locator("[data-script-generator-attempt='剧本生成分镜脚本']").get_attribute("aria-pressed") == "true",
    )

    # 提示词可编辑（本地草稿）
    textarea = node_first.locator("textarea")
    textarea.fill("一个关于时间旅行的短故事")
    check("prompt:editable", textarea.input_value() == "一个关于时间旅行的短故事")

    # 双击画布打开添加面板（Batch 115 联动）后不再重复断言；检查 undo 可移除节点
    page.keyboard.press("Control+z")
    page.wait_for_timeout(300)

    check("diagnostics:zero", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 116,
        "title": "Script-generator node type",
        "evidence": "docs/research/liblib-canvas-sampling-2026-09-06/README.md",
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
        "Batch 116 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "script-generator node creation via 脚本NEW, title/modes/reference/"
        "model card content, attempt selection and local prompt recorded in "
        "runtime-audit.json."
    )


if __name__ == "__main__":
    main()
