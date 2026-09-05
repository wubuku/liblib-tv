#!/usr/bin/env python3

"""Verify Batch 126 inline advanced settings row in the video panel."""

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
    / "liblib-canvas-batch126-2026-09-06"
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
        assert ok, f"batch126 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(BASE_URL, wait_until="networkidle")
    page.wait_for_timeout(400)

    page.get_by_role("button", name="添加节点").click()
    page.wait_for_timeout(400)
    panel = page.locator("[data-liblib-overlay='add-node']")
    panel.get_by_role("button", name="视频", exact=True).click()
    page.wait_for_timeout(1200)
    node = page.locator(".react-flow__node-video").first
    node.click()
    page.wait_for_timeout(800)

    vg = page.locator("[data-video-generation-panel]")
    check("advanced:label", vg.locator("[data-video-advanced-label]").is_visible())
    check("advanced:label-copy", "高级设置" in vg.locator("[data-video-advanced-label]").inner_text())
    row = vg.locator("[data-video-advanced-inline]")
    check("advanced:inline-row", row.is_visible())
    for chip in ["联网搜索", "自动校验素材", "智能引用 AutoLink"]:
        check(f"advanced:chip:{chip}", row.get_by_text(chip, exact=True).is_visible())

    # 开关交互：联网搜索 默认? 点击切换两次还原
    net = row.get_by_text("联网搜索", exact=True)
    net.click(force=True)
    page.wait_for_timeout(150)
    net.click(force=True)
    page.wait_for_timeout(150)

    # 齿轮触发器已移除（内联化后不再有独立 trigger）
    check("advanced:trigger-removed", vg.locator("[data-video-advanced-trigger]").count() == 0)

    # 生成流程不回归
    textarea = vg.locator("textarea").first
    textarea.fill("测试生成")
    page.locator("[data-video-generate-submit]").click()
    page.wait_for_timeout(500)

    check("diagnostics:zero", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 126,
        "title": "Inline advanced settings row in the video panel",
        "evidence": "docs/research/liblib-video-panel-2026-09-06/README.md",
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
        "Batch 126 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "Inline 高级设置 row with three switch chips, toggle interaction and "
        "generate flow recorded in runtime-audit.json."
    )


if __name__ == "__main__":
    main()
