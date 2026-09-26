#!/usr/bin/env python3

"""Verify Batch 185: FrameOS horizontal organize layers nodes left-to-right.

The clone implements 按连线横向 (layer nodes along connections, left to
right). With the demo graph text-1 -> image-1, running horizontal organize
must place the text node to the LEFT of the image node it feeds. Locks the
horizontal/vertical organize modes that Batch 175 only tested for grid.
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
    / "liblib-frameos-batch185-2026-09-24"
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
        assert ok, f"batch185 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/frameos/canvas/demo", wait_until="domcontentloaded", timeout=90000)
    page.wait_for_timeout(1200)

    # 切换整理方式为 按连线横向
    page.locator("button[aria-label='选择整理方式']").click()
    page.wait_for_timeout(300)
    opt = page.get_by_text("按连线横向", exact=True)
    check("menu:horizontal-option", opt.is_visible())
    opt.click()
    page.wait_for_timeout(300)

    # 先把 image-1 移到远处 (作为布置), 记录坐标
    page.evaluate(
        """(() => {
          const s = window.__frameos_store.getState();
          s.setNodes(s.nodes.map((n) => n.id === "image-1"
            ? { ...n, position: { x: 2000, y: n.position.y } }
            : n));
        })()"""
    )
    page.wait_for_timeout(300)
    x0 = page.evaluate(
        "window.__frameos_store.getState().nodes.find((n) => n.id === 'image-1').position.x"
    )

    # 一键整理 (横向) → image-1 被拉回分层位置
    page.locator("button[aria-label='一键整理 · 网格整理']").click()
    page.wait_for_timeout(1000)
    x1 = page.evaluate(
        "window.__frameos_store.getState().nodes.find((n) => n.id === 'image-1').position.x"
    )
    check("organize:pulls-image-into-layer", x1 < 1000)

    # 连线上游 (text-1) 应排在下游 (image-1) 左侧
    order = page.evaluate(
        """(() => {
          const s = window.__frameos_store.getState();
          const by = {};
          for (const n of s.nodes) by[n.id] = n.position.x;
          return { text: by["text-1"], image: by["image-1"] };
        })()"""
    )
    check(
        "organize:horizontal-layers-text-before-image",
        order["text"] is not None and order["image"] is not None and order["text"] < order["image"],
    )

    # 撤销 → 恢复布置前坐标
    page.evaluate("window.__frameos_store.getState().undo()")
    page.wait_for_timeout(400)
    x_undo = page.evaluate(
        "window.__frameos_store.getState().nodes.find((n) => n.id === 'image-1').position.x"
    )
    check("organize:undo-restores-x0", abs(x_undo - 2000) < 0.01)

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 185, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch185: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
