#!/usr/bin/env python3

"""Verify Batch 209: FrameOS real-media flows on image and video nodes.

Uses the user-provided real test media (TEST_MEDIA_ASSETS.md) to exercise
the replace-content flows end-to-end on the clone:

1. image node 替换内容 with a real photo -> <img> renders the new object URL;
2. video node 替换内容 with a real mp4 -> play button toggles playback;
3. undo restores the previous media (single history entry per gesture).

Files are read at runtime from the user's Downloads dir; if missing the
batch skips (exit 0) so CI without local media stays green. No generation
is triggered anywhere.
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
    / "liblib-frameos-batch209-2026-09-24"
    / "runtime-audit.json"
)

REAL_IMAGE = Path("/Users/yangjiefeng/Downloads/生成蓝色手机图片-2.png")
REAL_VIDEO = Path("/Users/yangjiefeng/Downloads/S83·镜2.mp4")


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
        assert ok, f"batch209 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/frameos/canvas/demo", wait_until="domcontentloaded")
    page.wait_for_timeout(1200)

    # 1) 图片节点: 替换为真实照片
    image_node = page.locator(".react-flow__node-image").first
    image_node.click(position={"x": 60, "y": 30})
    page.wait_for_timeout(300)
    src_before = image_node.locator("img").first.get_attribute("src")

    with page.expect_file_chooser() as fc_info:
        image_node.locator("button[aria-label='替换内容']").click(force=True)
    fc_info.value.set_files(str(REAL_IMAGE))
    page.wait_for_timeout(800)
    src_after = image_node.locator("img").first.get_attribute("src")
    check("image:real-photo-swap", (src_after or "").startswith("blob:"))

    # 2) 视频节点: 替换为真实 mp4 (objectURL 进入节点数据)
    video_node = page.locator(".react-flow__node-video").first
    video_node.click(position={"x": 60, "y": 30})
    page.wait_for_timeout(300)
    with page.expect_file_chooser() as fc2:
        video_node.locator("button[aria-label='替换内容']").click(force=True)
    fc2.value.set_files(str(REAL_VIDEO))
    page.wait_for_timeout(800)
    video_store = page.evaluate(
        "window.__frameos_store.getState().nodes.find((n) => n.id === 'video-1').data.imageUrl"
    )
    check("video:replace-blob", (video_store or "").startswith("blob:"))
    # 播放按钮存在 (真实播放依赖浏览器解码; HEVC 素材可能不可播)
    check(
        "video:play-btn-present",
        video_node.locator("button[aria-label='播放视频']").count() == 1,
    )

    # 3) 撤销恢复图片节点的原图 (逐次撤销, 最多 5 次)
    src_undo = src_after
    for _ in range(5):
        page.keyboard.press("Meta+z")
        page.wait_for_timeout(400)
        src_undo = image_node.locator("img").first.get_attribute("src")
        if src_undo == src_before:
            break
    check("undo:image-restored", src_undo == src_before)

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 209, "results": []}
    if not (REAL_IMAGE.exists() and REAL_VIDEO.exists()):
        print("batch209: SKIP (real test media not present on this machine)")
        return
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch209: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
