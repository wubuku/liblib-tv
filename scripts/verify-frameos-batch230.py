#!/usr/bin/env python3

"""Verify Batch 230: video fullscreen lightbox.

The video node's ⛶全屏查看 previously opened the fullscreen TEXT reading
overlay (a leftover from Batch 205) — wrong medium. Batch 230 routes it to
the Batch 227 lightbox family: real video sources (blob:/extension) render a
<video controls> player; image-cover sources render the cover image with
zoom controls. Source video lightbox itself is unsampled (family inference).

Checks:
1. content video (jpg cover) → ⛶ → lightbox shows cover image + zoom controls;
2. uploaded webm video → ⛶ → lightbox shows <video> player, no zoom buttons;
3. Esc closes; download button present in both;
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
VIDEO_PATH = "/tmp/frameos-probe-video.webm"
AUDIT_PATH = (
    ROOT
    / "docs"
    / "research"
    / "liblib-frameos-batch230-2026-09-26"
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
        assert ok, f"batch230 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/frameos/canvas/demo", wait_until="domcontentloaded", timeout=90000)
    page.wait_for_timeout(1500)

    # 1) 内容视频 (jpg 封面) → ⛶ → 封面图灯箱 + 缩放控件
    video = page.locator(".react-flow__node-video").first
    video.click(position={"x": 60, "y": 30})
    page.wait_for_timeout(400)
    page.locator(
        ".frameos-floating-toolbar-new button[aria-label='全屏查看']"
    ).click()
    page.wait_for_timeout(500)
    lightbox = page.locator("[data-frameos-image-lightbox]")
    check("cover:lightbox-opens", lightbox.is_visible())
    check("cover:image-mode", lightbox.locator("img").count() == 1)
    check("cover:video-absent", lightbox.locator("video").count() == 0)
    check(
        "cover:zoom-buttons",
        lightbox.locator("button[aria-label='放大']").count() == 1,
    )
    check(
        "cover:download-button",
        lightbox.locator("button[aria-label='下载']").count() == 1,
    )
    page.keyboard.press("Escape")
    page.wait_for_timeout(300)

    # 2) 上传真视频 → ⛶ → <video> 播放器, 无缩放按钮
    with page.expect_file_chooser() as fc_info:
        page.locator("button[aria-label='本地上传']").click()
    fc_info.value.set_files([VIDEO_PATH])
    page.wait_for_timeout(1200)
    uploaded = page.locator(".react-flow__node-video").last
    uploaded.click(position={"x": 60, "y": 30})
    page.wait_for_timeout(400)
    page.locator(
        ".frameos-floating-toolbar-new button[aria-label='全屏查看']"
    ).click()
    page.wait_for_timeout(600)
    lightbox2 = page.locator("[data-frameos-image-lightbox]")
    check("upload:lightbox-opens", lightbox2.is_visible())
    check("upload:video-player", lightbox2.locator("video").count() == 1)
    check("upload:img-absent", lightbox2.locator("img").count() == 0)
    check(
        "upload:no-zoom",
        lightbox2.locator("button[aria-label='放大']").count() == 0,
    )
    check(
        "upload:download-button",
        lightbox2.locator("button[aria-label='下载']").count() == 1,
    )
    page.keyboard.press("Escape")
    page.wait_for_timeout(300)
    check("esc:closes", page.locator("[data-frameos-image-lightbox]").count() == 0)

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 230, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch230: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
