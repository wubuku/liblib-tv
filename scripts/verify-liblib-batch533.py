#!/usr/bin/env python3
"""Verify Batch 533: script-v2 progress-card body and editor re-entry.

Contract: source-site CDP sampling 2026-09-27
(docs/research/liblib-source-exploration-2026-09-25/NOTES.md §11 update +
screenshot 39 / node DOM text) — after a storyboard session the script-v2
node body renders the progress form: ①确认镜头 — ②准备资产 — ③合成提示词
(circles with connecting lines and labels) plus a 打开脚本节点 → button
that reopens the full-screen storyboard editor. The fresh-state interior
was never sampled (batch 207 keeps the 脚本生成器 floating title); the
progress form is the only sampled interior, so the clone renders it as
the card body. Batch 533 does not click any generation control.
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
    / "liblib-canvas-batch533-2026-09-27"
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
        assert ok, f"batch533 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(BASE_URL, wait_until="networkidle")
    page.wait_for_timeout(400)

    # 成对创建（batch 207 路径）得到 script-v2 节点
    page.evaluate("window.__libtv_store.getState().createStoryScriptPair()")
    page.wait_for_timeout(700)
    node = page.locator(".react-flow__node-script-v2").first
    check("node:created", node.count() >= 1)
    text = node.inner_text()
    check("node:title-207-contract", "脚本生成器" in text)
    for token in ["确认镜头", "准备资产", "合成提示词", "1", "2", "3"]:
        check(f"node:step:{token}", token in text)

    # 打开脚本节点 → 全屏编辑器（batch 531 合同），ESC 关闭
    node.locator("[data-script-v2-open]").click()
    page.wait_for_timeout(300)
    editor = page.locator("[data-storyboard-editor]")
    check("open:editor", editor.is_visible())
    check("open:table", editor.locator("[data-storyboard-row='1']").is_visible())
    editor.click(position={"x": 700, "y": 300})
    page.keyboard.press("Escape")
    page.wait_for_timeout(250)
    check("escape:closes", page.locator("[data-storyboard-editor]").count() == 0)

    # 再次打开复现
    node.locator("[data-script-v2-open]").click()
    page.wait_for_timeout(250)
    check("reopen:editor", page.locator("[data-storyboard-editor]").is_visible())
    page.locator("[data-storyboard-close]").click()
    page.wait_for_timeout(250)
    check("close-button:closes", page.locator("[data-storyboard-editor]").count() == 0)

    check("diagnostics:zero", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 533,
        "title": "Script-v2 progress-card body and editor re-entry",
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
        "Batch 533 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "script-v2 progress-card body (three steps + labels), 打开脚本节点 "
        "editor re-entry and close recorded in runtime-audit.json."
    )


if __name__ == "__main__":
    main()
