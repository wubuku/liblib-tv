#!/usr/bin/env python3

"""Verify Batch 175: mode menu + params menu source alignment.

Source evidence (2026-09-07 CDP, rendering window):
- mode menu is a Mantine popover 161x229 (radius 16) anchored above the
  trigger, with the 视频生成模式 header and FIVE rows (h-8, one icon each):
  文生视频 (selected, bg white/15) / 全能参考 / 图生视频 / 首尾帧 /
  图片参考 — 超长视频 and 视频编辑 do NOT appear; on an empty node only
  文生视频 is enabled;
- params menu ratio grid measured 6 tiles (16:9/4:3/1:1/3:4/9:16/21:9,
  57x62, 4 per row) WITHOUT an Auto tile; resolution 480P/720P/1080P
  (73x32), audio 开启/关闭, count 1个/2个/4个, selected marker bg white/10;
  duration is a slider row (视频时长 label + numeric input with s suffix).
- Clone default mode stays omnireference (displays 文生视频) — account
  stateful default documented, not flipped.
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
    / "liblib-canvas-batch175-2026-09-07"
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
        assert ok, f"batch175 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(BASE_URL, wait_until="networkidle")
    page.wait_for_timeout(500)

    page.locator('.react-flow__node[data-id="v-UGQZzZOpbv"]').click(force=True)
    page.wait_for_timeout(300)

    # --- mode menu ---
    page.locator("[data-video-mode-trigger]").click(force=True)
    page.wait_for_timeout(300)
    items = page.eval_on_selector_all(
        "[data-video-mode-option]",
        "els => els.map(el => ({id: el.getAttribute('data-video-mode-option'), disabled: el.disabled, h: el.getBoundingClientRect().height}))",
    )
    check("mode:five-items", [i["id"] for i in items] == ["text", "omnireference", "image", "first-last", "image-reference"])
    check("mode:only-text-enabled", items[0]["disabled"] is False and all(i["disabled"] for i in items[1:]))
    check("mode:rows-h32", all(abs(i["h"] - 32) <= 1 for i in items))
    check("mode:no-long-video", page.locator('[data-video-mode-option="long-video"]').count() == 0)
    mode_menu_box = page.locator("[data-video-mode-trigger]").bounding_box()
    check("mode:trigger-visible", mode_menu_box is not None)

    # close mode menu, open params menu
    page.locator("[data-video-mode-trigger]").click(force=True)
    page.wait_for_timeout(200)
    page.locator("[data-video-params-trigger]").click(force=True)
    page.wait_for_timeout(300)
    check("params:open", page.locator("[data-video-params-menu]").count() == 1)
    # Batch 190: 模型切换复测否定 6 格采样——普通模式同样 7 格含 Auto。
    check("params:seven-ratio-tiles", page.locator("[data-video-ratio-option]").count() == 7)
    check("params:auto-tile-present", page.locator('[data-video-ratio-option="Auto"]').count() == 1)
    ids = page.eval_on_selector_all(
        "[data-video-ratio-option]",
        "els => els.map(el => el.getAttribute('data-video-ratio-option'))",
    )
    check("params:ratio-order", ids == ["Auto", "16:9", "4:3", "1:1", "3:4", "9:16", "21:9"])
    tile = page.locator('[data-video-ratio-option="16:9"]').bounding_box()
    check("params:tile-62", tile is not None and abs(tile["height"] - 62) <= 2)
    check("params:three-resolutions", page.locator("[data-video-resolution-option]").count() == 3)
    check("params:audio-count-controls", page.locator("[data-video-audio-option]").count() == 2 and page.locator("[data-video-count-option]").count() == 3)
    page.keyboard.press("Escape")
    page.wait_for_timeout(200)

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 175, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch175: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
