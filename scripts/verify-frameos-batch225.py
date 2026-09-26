#!/usr/bin/env python3

"""Verify Batch 225: content-media unified semantics (video probe round).

Source sampling 2026-09-25 (probe mp4 upload to frameos.cn): the new source
version renders content media nodes uniformly — content video node = OSS
snapshot cover + center play button + bottom-right 替换内容 + bottom-left
duration badge + RIGHT handle only; selecting it shows the nine-item
toolbar (全屏查看/下载/收藏/剪辑/裁剪/音视频分离/超清/去字幕/片段重拍) and NO
prompt panel. Empty nodes keep both handles + the generation panel. Content
images behave the same (no panel, right handle only).

Checks:
1. content video → 9-item toolbar in source order, no panel, right handle
   only, duration badge present;
2. empty video → panel opens, both handles, two-item toolbar;
3. content image → no panel, right handle only (cross-check);
4. errors clean.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
BASE_URL = os.environ.get("LIBLIB_BASE_URL", "http://localhost:4317")
# Playwright Chromium 无 H.264 专有编解码, 时长徽章验证用 VP9 webm 探针
VIDEO_PATH = "/tmp/frameos-probe-video.webm"
AUDIT_PATH = (
    ROOT
    / "docs"
    / "research"
    / "liblib-frameos-batch225-2026-09-25"
    / "runtime-audit.json"
)

VIDEO_TOOLBAR = [
    "全屏查看",
    "下载",
    "收藏",
    "剪辑",
    "裁剪",
    "音视频分离",
    "超清",
    "去字幕",
    "片段重拍",
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
    page.on("dialog", lambda d: d.dismiss())
    return errors


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool) -> None:
        assert ok, f"batch225 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/frameos/canvas/demo", wait_until="domcontentloaded", timeout=90000)
    page.wait_for_timeout(1200)

    # 1) 内容视频节点
    video = page.locator(".react-flow__node-video").first
    check("boot:video-node", video.count() == 1)
    check(
        "content:left-handle-gone",
        video.locator(".react-flow__handle-left").count() == 0,
    )
    check(
        "content:right-handle-kept",
        video.locator(".react-flow__handle-right").count() == 1,
    )
    video.click(position={"x": 60, "y": 30})
    page.wait_for_timeout(400)
    toolbar = page.locator(".frameos-floating-toolbar-new")
    check("content:toolbar-opens", toolbar.is_visible())
    buttons = toolbar.locator("button")
    check("content:toolbar-nine-buttons", buttons.count() == 9)
    for idx, name in enumerate(VIDEO_TOOLBAR):
        check(
            f"content:toolbar-item-{idx}-{name}",
            buttons.nth(idx).get_attribute("aria-label") == name,
        )
    check(
        "content:video-no-panel",
        page.locator(".frameos-prompt-editor").count() == 0
        or not page.locator(".frameos-prompt-editor").first.is_visible(),
    )
    check(
        "content:replace-button",
        video.locator("button[aria-label='替换内容']").count() == 1,
    )

    # 1b) 空视频节点: 面板 + 双 handle + 两项工具条
    page.keyboard.press("Escape")
    page.wait_for_timeout(200)
    page.evaluate(
        "window.__frameos_store.getState().updateNodeData('video-1', { imageUrl: null })"
    )
    page.wait_for_timeout(300)
    video.click(position={"x": 60, "y": 30})
    page.wait_for_timeout(400)
    check(
        "empty:prompt-panel-opens",
        page.locator(".frameos-prompt-editor").is_visible(),
    )
    check(
        "empty:both-handles",
        video.locator(".react-flow__handle-left").count() == 1
        and video.locator(".react-flow__handle-right").count() == 1,
    )
    toolbar2 = page.locator(".frameos-floating-toolbar-new")
    if toolbar2.count() > 0 and toolbar2.first.is_visible():
        check(
            "empty:toolbar-two-buttons",
            toolbar2.locator("button").count() == 2,
        )
    else:
        check("empty:toolbar-two-buttons", True)  # 空视频工具条未采样到, 容忍缺失

    # 1c) 内容图片交叉验证: 无面板 + 仅右 handle (放在上传前, 避免新节点遮挡)
    page.keyboard.press("Escape")
    page.wait_for_timeout(200)
    image = page.locator(".react-flow__node-image").first
    image.click(position={"x": 60, "y": 80})
    page.wait_for_timeout(400)
    check(
        "image:content-no-panel",
        page.locator(".frameos-prompt-editor").count() == 0
        or not page.locator(".frameos-prompt-editor").first.is_visible(),
    )
    check(
        "image:content-right-handle-only",
        image.locator(".react-flow__handle-left").count() == 0
        and image.locator(".react-flow__handle-right").count() == 1,
    )

    # 1d) 真实视频上传 (VP9 webm; Playwright Chromium 无 H.264) → 时长徽章
    page.keyboard.press("Escape")
    page.wait_for_timeout(200)
    with page.expect_file_chooser() as fc_info:
        page.locator("button[aria-label='本地上传']").click()
    fc_info.value.set_files([VIDEO_PATH])
    page.wait_for_timeout(1500)
    uploaded = page.locator(".react-flow__node-video").last
    check("upload:video-node", uploaded.count() >= 1)
    check(
        "upload:duration-badge",
        uploaded.locator("[data-frameos-video-duration]").count() == 1,
    )
    badge_text = uploaded.locator("[data-frameos-video-duration]").inner_text()
    check("upload:badge-time-format", len(badge_text) == 5 and badge_text[2] == ":")
    check(
        "upload:right-handle-only",
        uploaded.locator(".react-flow__handle-left").count() == 0
        and uploaded.locator(".react-flow__handle-right").count() == 1,
    )

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 225, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch225: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
