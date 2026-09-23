#!/usr/bin/env python3

"""Verify Batch 181: FrameOS alignment guides render mid-drag (clone-side
behavior lock; source-side snapping could not be sampled — automation drag
limits, documented).

Flow: drag a node so its top edge aligns (within the 8px threshold) with
another node's top edge; while the drag is active the dashed guide element
([data-frameos-alignment-guide]) must be present; it must disappear after
mouse-up. The guide positions are converted from world coordinates to
screen coordinates (Batch 181 fix).
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
    / "liblib-frameos-batch181-2026-09-24"
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
        assert ok, f"batch181 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/frameos/canvas/demo", wait_until="domcontentloaded")
    page.wait_for_timeout(1200)

    # 取两个节点的屏幕位置 (默认视图 zoom=1, 世界≈屏幕)
    a = page.locator(".react-flow__node-text").first.bounding_box()
    b = page.locator(".react-flow__node").nth(1).bounding_box()
    check("boot:two-nodes", a is not None and b is not None)
    if not a or not b:
        raise RuntimeError("nodes missing")

    # 对齐目标: 节点A 的顶边 对齐 节点B 的顶边 (拖动 dy)
    dy = b["y"] - a["y"]
    dx = 0
    start = {"x": a["x"] + a["width"] / 2, "y": a["y"] + a["height"] / 2}

    page.mouse.move(start["x"], start["y"])
    page.mouse.down()
    # 分步移动到对齐位置
    for i in range(1, 7):
        page.mouse.move(
            start["x"] + dx * i / 6,
            start["y"] + dy * i / 6,
        )
    page.wait_for_timeout(300)
    guides = page.locator("[data-frameos-alignment-guide]")
    check("drag:guide-appears", guides.count() >= 1)

    # 松开 → 辅助线消失
    page.mouse.up()
    page.wait_for_timeout(300)
    check("drag:guide-clears-after-drop", page.locator("[data-frameos-alignment-guide]").count() == 0)

    # 恢复: 撤销拖拽造成的位移
    page.keyboard.press("Meta+z")
    page.wait_for_timeout(300)

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 181, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch181: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
