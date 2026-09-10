#!/usr/bin/env python3
"""Verify Batch 334: storyboard view rebuilt as the source's full-width
three-column resource overview (音频 | 图片 | 视频).

Source evidence (2026-09-11, docs/research/liblib-canvas-batch334-2026-09-11/):
- Storyboard mode renders three bordered panels side by side:
  audio (narrow), image (wide), video (flex). No key-elements sidebar,
  no return-to-workbench button — the workbench/storyboard switch lives
  in the top bar (aria-labels 工作流 / 故事板).
- Video header carries a 全部 ∨ filter and an expand icon; image header
  an expand icon; the image column body has a 对话 (dialog) button.
- Image cards show a dimension chip (e.g. 1080 x 1446) under the thumb;
  video cards show a status overlay (待确认后生成 / 生成失败 / 暂无预览
  / play for ready), a model chip, and reference thumbs.
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
    / "liblib-canvas-batch334-2026-09-11"
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
        assert ok, f"batch334 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto("http://localhost:4317", wait_until="networkidle")
    page.wait_for_timeout(600)

    # ---- switch to storyboard via the top-bar icon pair
    page.get_by_role("button", name="故事板").click()
    page.wait_for_timeout(400)
    board = page.locator("[data-storyboard-board]")
    check("board:visible", board.is_visible())

    # ---- three columns in source order: audio | image | video
    audio = page.locator("[data-storyboard-column='audio']")
    image = page.locator("[data-storyboard-column='image']")
    video = page.locator("[data-storyboard-column='video']")
    check("columns:audio-visible", audio.is_visible())
    check("columns:image-visible", image.is_visible())
    check("columns:video-visible", video.is_visible())
    audio_box = audio.bounding_box()
    image_box = image.bounding_box()
    video_box = video.bounding_box()
    check(
        "columns:order",
        bool(
            audio_box and image_box and video_box
            and audio_box["x"] < image_box["x"] < video_box["x"]
        ),
    )
    check(
        "columns:image-wider-than-audio",
        bool(audio_box and image_box and image_box["width"] > audio_box["width"]),
    )

    # ---- legacy batch-104 chrome is gone
    check("legacy:no-key-elements", page.locator("[data-storyboard-key-elements]").count() == 0)
    check("legacy:no-return", page.locator("[data-storyboard-return]").count() == 0)
    check("legacy:no-zoom-buttons", page.locator("[data-storyboard-zoom]").count() == 0)

    # ---- header controls
    check("video:filter-all", page.locator("[data-storyboard-filter='all']").inner_text().strip() == "全部")
    check("header:expand-buttons", page.locator("[data-storyboard-expand='image']").is_visible()
          and page.locator("[data-storyboard-expand='video']").is_visible())
    check("image:dialog-button", page.locator("[data-storyboard-dialog='image']").inner_text().strip() == "对话")

    # ---- cards driven by canvas nodes
    image_cards = page.locator("[data-storyboard-column='image'] [data-storyboard-card]")
    video_cards = page.locator("[data-storyboard-column='video'] [data-storyboard-card]")
    check("image:cards-present", image_cards.count() >= 1)
    check("video:cards-present", video_cards.count() >= 1)

    video_card = video_cards.first
    status = video_card.get_attribute("data-storyboard-video-status")
    check("video:status-attr", status in ("empty", "failed", "ready", "pending"))
    if video_card.get_attribute("data-storyboard-model"):
        check("video:model-chip-text", len(video_card.locator("[data-storyboard-model]").inner_text().strip()) > 0)

    if image_cards.count() > 0 and page.locator("[data-storyboard-dimension]").count() > 0:
        dim_text = page.locator("[data-storyboard-dimension]").first.inner_text().strip()
        check("image:dimension-format", " x " in dim_text)

    # ---- audio column: cards or explicit empty state
    audio_cards = page.locator("[data-storyboard-column='audio'] [data-storyboard-card]")
    if audio_cards.count() > 0:
        check("audio:duration-label", page.locator("[data-storyboard-audio-duration]").first.inner_text().strip() != "")
    else:
        check("audio:empty-state", page.locator("[data-storyboard-empty='audio']").is_visible())

    # ---- back to workbench: board hides, React Flow returns
    page.get_by_role("button", name="工作流").click()
    page.wait_for_timeout(400)
    check("workbench:board-hidden", board.count() == 0 or not board.is_visible())
    check("workbench:reactflow-visible", page.locator(".react-flow").is_visible())

    # ---- storyboard again for state persistence
    page.get_by_role("button", name="故事板").click()
    page.wait_for_timeout(400)
    check("storyboard:re-enter-visible", board.is_visible())

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 334, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch334: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
