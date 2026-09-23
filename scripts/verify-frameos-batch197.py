#!/usr/bin/env python3

"""Verify Batch 197: FrameOS reference-select mode (参考).

2026-09-24 source re-sampling: clicking 参考 on the image prompt panel
enters a reference-select mode — blue top bar 从画布选择参考 / 返回节点 / ×,
canvas outlined for selection. Clicking another node adds it as a reference
(creates the connection) and exits the mode. Verifies entry, node-click
creates the edge, exit paths, and undo removes the added edge.
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
    / "liblib-frameos-batch197-2026-09-24"
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
        assert ok, f"batch197 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/frameos/canvas/demo", wait_until="domcontentloaded")
    page.wait_for_timeout(1200)

    image_node = page.locator(".react-flow__node-image").first
    image_node.click(position={"x": 60, "y": 30})
    page.wait_for_timeout(400)
    editor = page.locator(".frameos-prompt-editor")
    check("panel:opens", editor.is_visible())

    # 进入参考选择模式
    ref_tile = editor.locator("button[aria-label='参考']")
    check("ref:tile", ref_tile.is_visible())
    ref_tile.click()
    page.wait_for_timeout(500)
    bar = page.locator("[data-frameos-ref-select-bar]")
    check("ref:bar-opens", bar.is_visible())
    check(
        "ref:bar-buttons",
        bar.locator("[data-frameos-ref-select-back]").is_visible(),
    )

    # 点击画布上的文本节点 → 加为参考 (创建连线) 并退出模式
    text_node = page.locator(".react-flow__node-text").first
    text_node.click(position={"x": 150, "y": 100})
    page.wait_for_timeout(600)
    edges_after = page.evaluate("window.__frameos_store.getState().edges.length")
    check("ref:edge-created", edges_after >= 2)
    check(
        "ref:mode-exits",
        page.evaluate("window.__frameos_store.getState().refSelectTargetId") is None,
    )

    # 撤销 → 移除新连线
    page.keyboard.press("Meta+z")
    page.wait_for_timeout(400)
    edges_undo = page.evaluate("window.__frameos_store.getState().edges.length")
    check("ref:undo-removes-edge", edges_undo == edges_after - 1)

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 197, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch197: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
