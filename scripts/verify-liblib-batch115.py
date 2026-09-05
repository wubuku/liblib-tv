#!/usr/bin/env python3

"""Verify Batch 115 canvas double-click opens the add-node panel."""

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
    / "liblib-canvas-batch115-2026-09-06"
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
    page.on(
        "requestfailed",
        lambda request: errors.append(
            f"requestfailed:{request.method}:{request.url}:{request.failure}"
        ),
    )
    return errors


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool) -> None:
        assert ok, f"batch115 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(BASE_URL, wait_until="networkidle")
    page.wait_for_timeout(400)

    pane = page.locator(".react-flow__pane")
    box = pane.bounding_box()
    check("pane:present", box is not None)
    nodes_before = page.locator(".react-flow__node").count()

    # 双击空白画布 → 添加节点面板打开
    pane.dblclick(position={"x": box["width"] / 2, "y": box["height"] / 2})
    page.wait_for_timeout(600)
    panel = page.locator("[data-liblib-overlay='add-node']")
    check("dblclick:panel-opens", panel.is_visible())
    check("dblclick:creates-nothing", page.locator(".react-flow__node").count() == nodes_before)

    # 双击第二次（面板开着时再双击）→ 面板保持/不重复创建
    pane.dblclick(position={"x": box["width"] / 3, "y": box["height"] / 3})
    page.wait_for_timeout(500)
    check("dblclick:no-nodes", page.locator(".react-flow__node").count() == nodes_before)

    # Escape 关闭面板
    page.keyboard.press("Escape")
    page.wait_for_timeout(300)
    check("escape:closes-panel", not panel.is_visible())

    # 再次双击可重新打开（可重复触发）
    pane.dblclick(position={"x": box["width"] / 2, "y": box["height"] / 2})
    page.wait_for_timeout(500)
    check("dblclick:reopens", panel.is_visible())
    page.keyboard.press("Escape")

    check("diagnostics:zero", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 115,
        "title": "Canvas double-click opens add-node panel",
        "evidence": "docs/research/liblib-canvas-sampling-2026-09-06/README.md",
        "results": [],
    }
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        desktop = browser.new_page(viewport={"width": 1440, "height": 900}, device_scale_factor=1)
        audit["results"].append(run_desktop(desktop))
        desktop.close()
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    checks = audit["results"][0]["checks"]
    print(
        "Batch 115 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "Double-click opens the add-node panel without creating nodes, "
        "escape closes and re-trigger works recorded in runtime-audit.json."
    )


if __name__ == "__main__":
    main()
