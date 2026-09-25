#!/usr/bin/env python3

"""Verify Batch 239: video-specific generation panel for empty video nodes.

Source sampling 2026-09-26 (.bottom-generator.mode-video): the empty video
node's panel carries a 参考 tile, mode tabs [全能参考(active)|首尾帧|视频编辑],
placeholder 描述你想要的视频，@引用素材, model Wan 3.0, spec 16:9 · 720p · 5s,
credits 300. The clone previously showed the generic image panel.

Checks:
1. empty video selected → video panel opens with the three mode tabs;
2. placeholder is the video copy;
3. mode tabs switch active state;
4. Wan 3.0 + 300 credits + 生成视频 button present;
5. errors clean.
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
    / "liblib-frameos-batch239-2026-09-26"
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
        assert ok, f"batch239 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/frameos/canvas/demo", wait_until="domcontentloaded", timeout=90000)
    page.wait_for_timeout(1500)

    # 清空 demo 视频封面 → 空视频 → 选中
    page.evaluate(
        "window.__frameos_store.getState().updateNodeData('video-1', { imageUrl: null })"
    )
    page.wait_for_timeout(400)
    video = page.locator(".react-flow__node-video").first
    video.click(position={"x": 60, "y": 30})
    page.wait_for_timeout(500)
    panel = page.locator(".frameos-prompt-editor--video")
    check("video:panel-opens", panel.is_visible())

    # 模式 tabs
    for mode in ["全能参考", "首尾帧", "视频编辑"]:
        check(
            f"video:tab-{mode}",
            panel.locator(f"button[aria-label='视频模式 {mode}']").count() == 1,
        )

    # 切换模式 tab
    panel.locator("button[aria-label='视频模式 首尾帧']").click()
    page.wait_for_timeout(200)
    first_btn_style = panel.locator("button[aria-label='视频模式 首尾帧']").get_attribute("style") or ""
    check("video:tab-switches", "0.25" in first_btn_style and "59, 130, 246" in first_btn_style)

    # 占位文案
    textarea = panel.locator("textarea")
    check(
        "video:placeholder",
        textarea.get_attribute("placeholder") == "描述你想要的视频，@引用素材",
    )

    # 模型/规格/积分/生成按钮
    check("video:wan3-model", panel.locator("text=Wan 3.0").last.is_visible())
    check("video:spec", panel.locator("text=16:9 · 720p · 5s").first.is_visible())
    check("video:credits-300", panel.locator("text=300").first.is_visible())
    check(
        "video:generate-button",
        panel.locator("button[aria-label='生成视频']").count() == 1,
    )

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 239, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch239: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
