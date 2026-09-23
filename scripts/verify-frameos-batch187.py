#!/usr/bin/env python3

"""Verify Batch 187: FrameOS empty-canvas state (empty-canvas CTA alignment).

2026-09-23 source evidence (manual SOURCE_OBSERVATIONS section 1.1 /
screenshot 01): an empty canvas shows the title "选择一种方式开始创作" with
six CTAs (文本/图片/视频/音频/3D导演台/上传文件); clicking 文本 creates a
text node and clears the empty state. The clone lacked the empty state
entirely. Verifies: switching to the empty mock canvas shows the state,
clicking 文本 creates a node and dismisses it, and the state returns when
the canvas is emptied again.
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
    / "liblib-frameos-batch187-2026-09-24"
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
        assert ok, f"batch187 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/frameos/canvas/demo", wait_until="domcontentloaded")
    page.wait_for_timeout(1200)

    # 切到空的 画布 3 (通过面包屑: 画布下拉列出 画布 3)
    page.locator("button.breadcrumb-switcher", has_text="画布 1").click()
    page.wait_for_timeout(300)
    page.locator("[data-frameos-canvas-option='画布 3']").click()
    page.wait_for_timeout(700)
    empty = page.locator("[data-frameos-empty-state]")
    check("empty:state-shows", empty.is_visible())
    check(
        "empty:title",
        "选择一种方式开始创作" in empty.inner_text(),
    )
    for cta in ["文本", "图片", "视频", "音频", "3D导演台", "上传文件"]:
        check(
            f"empty:cta:{cta}",
            empty.locator(f"[data-frameos-empty-cta='{cta}']").is_visible(),
        )

    # 点击 文本 → 创建节点, 空态消失
    empty.locator("[data-frameos-empty-cta='文本']").click()
    page.wait_for_timeout(700)
    check(
        "empty:text-created-disappears",
        page.locator("[data-frameos-empty-state]").count() == 0
        and page.locator(".react-flow__node-text").count() == 1,
    )

    # 撤销 → 画布回到空 → 空态回归
    page.keyboard.press("Meta+z")
    page.wait_for_timeout(500)
    check(
        "empty:returns-after-undo",
        page.locator("[data-frameos-empty-state]").is_visible(),
    )

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 187, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch187: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
