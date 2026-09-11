#!/usr/bin/env python3
"""Verify Batch 344: storyboard column expand toggles and the image
column 对话 feedback (CLONE_DECISION interactions, source sampling
blocked — see docs/research/liblib-canvas-batch344-2026-09-11/).

- expand icon on image/video columns toggles a widened state
  (data-storyboard-expanded, aria-expanded, 放大/还原 label swap,
  Minimize2 restore icon); widening one column narrows the other
- 对话 button toggles a local feedback hint (本地原型：对话未连接)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = (
    ROOT
    / "docs"
    / "research"
    / "liblib-canvas-batch344-2026-09-11"
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
    return errors


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool) -> None:
        assert ok, f"batch344 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto("http://localhost:4317", wait_until="networkidle")
    page.wait_for_timeout(600)

    page.get_by_role("button", name="故事板").click()
    page.wait_for_timeout(400)

    image_section = page.locator("[data-storyboard-column='image']")
    video_section = page.locator("[data-storyboard-column='video']")
    image_expand = page.locator("[data-storyboard-expand='image']")
    video_expand = page.locator("[data-storyboard-expand='video']")

    base_image_w = image_section.bounding_box()["width"]
    base_video_w = video_section.bounding_box()["width"]
    check("base:widths", base_image_w > 200 and base_video_w > 200)
    check("base:expand-image-label", image_expand.get_attribute("aria-label") == "放大图片栏")
    check("base:expand-video-label", video_expand.get_attribute("aria-label") == "放大视频栏")
    check(
        "base:no-expanded-attr",
        image_section.get_attribute("data-storyboard-expanded") is None
        and video_section.get_attribute("data-storyboard-expanded") is None,
    )

    # ---- expand image: image widens, video narrows
    image_expand.click()
    page.wait_for_timeout(350)
    wide_image_w = image_section.bounding_box()["width"]
    narrow_video_w = video_section.bounding_box()["width"]
    check("expand:image-wider", wide_image_w > base_image_w)
    check("expand:video-narrower", narrow_video_w < base_video_w)
    check("expand:image-attr", image_section.get_attribute("data-storyboard-expanded") == "true")
    check("expand:image-aria", image_expand.get_attribute("aria-expanded") == "true")
    check("expand:image-restore-label", image_expand.get_attribute("aria-label") == "还原图片栏")

    # ---- restore image
    image_expand.click()
    page.wait_for_timeout(350)
    check(
        "restore:image-width",
        abs(image_section.bounding_box()["width"] - base_image_w) <= 2,
    )

    # ---- expand video: video widens, image narrows
    video_expand.click()
    page.wait_for_timeout(350)
    check("expand:video-wider", video_section.bounding_box()["width"] > base_video_w)
    check("expand:image-narrower", image_section.bounding_box()["width"] < base_image_w)
    check("expand:video-attr", video_section.get_attribute("data-storyboard-expanded") == "true")
    check("expand:video-restore-label", video_expand.get_attribute("aria-label") == "还原视频栏")
    video_expand.click()
    page.wait_for_timeout(350)
    check(
        "restore:video-width",
        abs(video_section.bounding_box()["width"] - base_video_w) <= 2,
    )

    # ---- 对话 feedback toggle
    dialog = page.locator("[data-storyboard-dialog='image']")
    check("dialog:hint-hidden", page.locator("[data-storyboard-dialog-status]").count() == 0)
    dialog.click()
    page.wait_for_timeout(250)
    status = page.locator("[data-storyboard-dialog-status]")
    check("dialog:hint-visible", status.is_visible())
    check("dialog:hint-copy", "本地原型" in status.inner_text() and "对话未连接" in status.inner_text())
    check("dialog:aria-expanded", dialog.get_attribute("aria-expanded") == "true")
    dialog.click()
    page.wait_for_timeout(250)
    check("dialog:hint-toggles-off", page.locator("[data-storyboard-dialog-status]").count() == 0)

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 344, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch344: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
