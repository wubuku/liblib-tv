#!/usr/bin/env python3

"""Verify Batch 228: per-kind context menu rules (video probe round).

Source sampling 2026-09-25 (clone-probe-vid2.mp4 upload): the CONTENT VIDEO
context menu is minimal — 复制⌘C / 创建副本⌘D / (divider) / 删除⌫ with NO
middle row. 设置为资产图 is image-specific; 重新生成 belongs to empty images
and non-media nodes only. Audio (unsampled) follows the video rule.

Checks:
1. content video menu = [复制, 创建副本, 删除];
2. content audio menu = [复制, 创建副本, 删除];
3. content image menu unchanged = [复制, 复制图片, 创建副本, 设置为资产图, 删除];
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
    / "liblib-frameos-batch228-2026-09-25"
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


def menu_rows(page: Page) -> list[str]:
    return [
        page.locator("[data-frameos-context-item]").nth(i).get_attribute(
            "data-frameos-context-item"
        )
        for i in range(page.locator("[data-frameos-context-item]").count())
    ]


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool) -> None:
        assert ok, f"batch228 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/frameos/canvas/demo", wait_until="domcontentloaded")
    page.wait_for_timeout(1200)
    menu = page.locator("[data-frameos-context-menu]")

    # 1) 内容视频菜单: 三行 (无中间行)
    video = page.locator(".react-flow__node-video").first
    video.click(button="right")
    page.wait_for_timeout(300)
    check("video:menu-opens", menu.is_visible())
    check("video:rows", menu_rows(page) == ["复制", "创建副本", "删除"])
    page.keyboard.press("Escape")
    page.wait_for_timeout(200)

    # 2) 内容音频菜单: 同视频规则
    page.evaluate(
        """(() => {
          const st = window.__frameos_store.getState();
          st.addNode('audio', { panX: 0, panY: 0, zoom: 1, viewportWidth: 1440, viewportHeight: 900 });
          const s2 = window.__frameos_store.getState();
          const a = [...s2.nodes].reverse().find((n) => n.type === 'audio');
          s2.updateNodeData(a.id, { audioUrl: '/audio/frameos-tone.wav' });
        })()"""
    )
    page.wait_for_timeout(500)
    audio = page.locator(".react-flow__node-audio").last
    audio.click(button="right")
    page.wait_for_timeout(300)
    check("audio:menu-opens", menu.is_visible())
    check("audio:rows", menu_rows(page) == ["复制", "创建副本", "删除"])
    page.keyboard.press("Escape")
    page.wait_for_timeout(200)

    # 3) 内容图片菜单: 不受本批影响
    image = page.locator(".react-flow__node-image").first
    image.click(button="right")
    page.wait_for_timeout(300)
    check(
        "image:rows",
        menu_rows(page) == ["复制", "复制图片", "创建副本", "设置为资产图", "删除"],
    )
    page.keyboard.press("Escape")
    page.wait_for_timeout(200)

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 228, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch228: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
