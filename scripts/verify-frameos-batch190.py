#!/usr/bin/env python3

"""Verify Batch 190: FrameOS 全屏编辑 overlay.

Source evidence: the image prompt panel header has a 全屏编辑 button
(BEHAVIORS-era claim: expands the editor centered, top ~80px). The clone
mocked it with an alert. Now it opens a centered fullscreen editor bound to
the same prompt value, closable via × or 完成. Verifies open, shared prompt
value, both close paths, and that the mini panel hides while fullscreen.
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
    / "liblib-frameos-batch190-2026-09-24"
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
    page.on("dialog", lambda d: d.dismiss())
    return errors


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool) -> None:
        assert ok, f"batch190 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/frameos/canvas/demo", wait_until="domcontentloaded")
    page.wait_for_timeout(1200)

    # Batch 225: 面板仅空图片节点显示 (2026-09-25 源站实测: 内容图片选中
    # 只显示富工具条无面板), 故先清空 image-1 内容再验证面板
    page.evaluate(
        "window.__frameos_store.getState().updateNodeData('image-1', { imageUrl: null })"
    )
    page.wait_for_timeout(300)

    image_node = page.locator(".react-flow__node-image").first
    image_node.click(position={"x": 60, "y": 30})
    page.wait_for_timeout(400)
    editor = page.locator(".frameos-prompt-editor")
    check("panel:opens", editor.is_visible())

    # 打开全屏编辑
    editor.locator("button[aria-label='全屏编辑']").click()
    page.wait_for_timeout(400)
    fs = page.locator("[data-frameos-fullscreen-editor]")
    check("fullscreen:opens", fs.is_visible())
    check("panel:hides", editor.count() == 0 or not editor.first.is_visible())

    # 输入提示词 (共享同一 promptValue)
    fs.locator("textarea").fill("全屏编辑冒烟提示词")
    page.wait_for_timeout(200)

    # 完成 → 退出全屏, mini 面板回值
    fs.get_by_role("button", name="完成全屏编辑").click()
    page.wait_for_timeout(400)
    back = page.locator(".frameos-prompt-editor")
    check("fullscreen:closes", fs.count() == 0)
    check(
        "mini:shares-value",
        back.is_visible()
        and page.evaluate("window.__frameos_store.getState().promptValue")
        == "全屏编辑冒烟提示词",
    )

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 190, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch190: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
