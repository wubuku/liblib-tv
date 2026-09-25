#!/usr/bin/env python3

"""Verify Batch 238: empty video node has NO toolbar (new-version source).

Source sampling 2026-09-26: creating a 视频 node via the rail menu on
frameos.cn and selecting it shows NO floating toolbar (same as empty
images) — only the generation panel. The old [全屏查看, 下载] two-button
toolbar was a 2026-09-23 pre-update sample; Batch 238 removes it.

Checks:
1. empty video selected → no floating toolbar;
2. empty video keeps panel + both handles (regression);
3. content video keeps the nine-item toolbar (regression);
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
AUDIT_PATH = (
    ROOT
    / "docs"
    / "research"
    / "liblib-frameos-batch238-2026-09-26"
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
        assert ok, f"batch238 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/frameos/canvas/demo", wait_until="domcontentloaded", timeout=90000)
    page.wait_for_timeout(1500)

    # 清空 demo 视频封面 → 空视频
    page.evaluate(
        "window.__frameos_store.getState().updateNodeData('video-1', { imageUrl: null })"
    )
    page.wait_for_timeout(400)
    video = page.locator(".react-flow__node-video").first
    video.click(position={"x": 60, "y": 30})
    page.wait_for_timeout(400)
    check(
        "empty-video:no-toolbar",
        page.locator(".frameos-floating-toolbar-new").count() == 0
        or not page.locator(".frameos-floating-toolbar-new").first.is_visible(),
    )
    check(
        "empty-video:panel-opens",
        page.locator(".frameos-prompt-editor").is_visible(),
    )
    check(
        "empty-video:both-handles",
        video.locator(".react-flow__handle-left").count() == 1
        and video.locator(".react-flow__handle-right").count() == 1,
    )

    # 回归: 内容视频仍有九项工具条
    page.keyboard.press("Escape")
    page.wait_for_timeout(200)
    page.evaluate(
        """(() => {
          const s = window.__frameos_store.getState();
          s.addNode('video', { panX: 0, panY: 0, zoom: 1, viewportWidth: 1440, viewportHeight: 900 });
        })()"""
    )
    page.wait_for_timeout(500)
    content_video = page.locator(".react-flow__node-video").last
    content_video.click(position={"x": 60, "y": 30})
    page.wait_for_timeout(400)
    check(
        "content-video:toolbar-nine",
        page.locator(".frameos-floating-toolbar-new button").count() == 9,
    )

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 238, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch238: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
