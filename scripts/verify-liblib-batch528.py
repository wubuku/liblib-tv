#!/usr/bin/env python3
"""Verify Batch 528: script-generator attempt entries drive the follow session.

Contract: source-site live sampling 2026-09-25 rounds 5/8
(docs/research/liblib-source-exploration-2026-09-25/NOTES.md §11 + follow
observation) — clicking a 尝试 entry (e.g. 剧本生成分镜脚本) only selects and
follows the node (正在跟随/取消ESC banner), it does not expand any subflow.
The banner's 取消 button and the Escape key both end the session.

Scenes (desktop 1440x900):
- attempt_click_follows: clicking an entry shows the follow banner and marks
  the entry aria-pressed;
- banner_cancel_ends: clicking 取消 hides the banner and clears the entry
  highlight;
- escape_ends: re-clicking an entry then pressing Escape also ends the
  session;
- no_subflow: no new foreground surface opens from the entry click.
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
    / "liblib-canvas-batch528-2026-09-27"
    / "runtime-audit.json"
)

ENTRY = "剧本生成分镜脚本"


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


def banner_hidden(page: Page) -> bool:
    banner = page.locator("[data-follow-banner]")
    return banner.get_attribute("aria-hidden") == "true"


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool) -> None:
        assert ok, f"batch528 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(BASE_URL, wait_until="networkidle")
    page.wait_for_timeout(400)
    check("initial:no-follow", banner_hidden(page))

    # 打开添加面板 → 脚本 flyout → 脚本NEW（与 batch 116 同路径）
    page.get_by_role("button", name="添加节点").click()
    page.wait_for_timeout(400)
    panel = page.locator("[data-liblib-overlay='add-node']")
    check("panel:open", panel.is_visible())
    panel.locator("[data-add-node-entry='script']").click()
    page.wait_for_timeout(400)
    panel.locator("[data-add-node-entry='script-new']").click()
    page.wait_for_timeout(900)

    node = page.locator(".react-flow__node-script-generator").first
    check("node:created", node.count() >= 0 and node.is_visible())

    entry = node.locator(f"[data-script-generator-attempt='{ENTRY}']")

    # 单击入口 → 正在跟随横幅 + 入口高亮，未展开子流程
    entry.click()
    page.wait_for_timeout(300)
    banner = page.locator("[data-follow-banner]")
    check("attempt:aria-pressed", entry.get_attribute("aria-pressed") == "true")
    check("follow:banner-visible", banner.get_attribute("aria-hidden") == "false")
    check("follow:banner-text", "正在跟随" in banner.inner_text())
    check("follow:no-subflow", page.locator("[data-liblib-overlay]").count() == 0)

    # 横幅取消 → 跟随结束 + 入口高亮清除
    banner.locator("[data-follow-cancel]").click()
    page.wait_for_timeout(300)
    check("cancel:banner-hidden", banner_hidden(page))
    check("cancel:entry-cleared", entry.get_attribute("aria-pressed") == "false")

    # 再次单击入口 + Escape → 跟随结束
    entry.click()
    page.wait_for_timeout(300)
    check("reclick:banner-visible", banner.get_attribute("aria-hidden") == "false")
    page.keyboard.press("Escape")
    page.wait_for_timeout(300)
    check("escape:banner-hidden", banner_hidden(page))
    check("escape:entry-cleared", entry.get_attribute("aria-pressed") == "false")

    # 提示词本地草稿不受跟随往返影响
    textarea = node.locator("textarea")
    textarea.fill("一个关于时间旅行的短故事")
    check("prompt:editable", textarea.input_value() == "一个关于时间旅行的短故事")

    check("diagnostics:zero", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 528,
        "title": "Script-generator attempt entries drive follow session",
        "evidence": (
            "docs/research/liblib-source-exploration-2026-09-25/NOTES.md "
            "§11/round-8 (单击入口 → 正在跟随/取消ESC，未展开子流程)"
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
        "Batch 528 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "attempt entry click shows 正在跟随 banner, banner 取消 and Escape "
        "both end the session with entry highlight cleared, no subflow "
        "recorded in runtime-audit.json."
    )


if __name__ == "__main__":
    main()
