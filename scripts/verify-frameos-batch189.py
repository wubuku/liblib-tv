#!/usr/bin/env python3

"""Verify Batch 189: FrameOS node resize via the drag handle.

The source text/image nodes expose a resize handle (拖拽调整大小); the
clone's handle was a visual stub. Batch 189 wires it: dragging the handle
grows/shrinks the node (min 200x120) and one undo restores the original
size (single history entry per gesture).
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
    / "liblib-frameos-batch189-2026-09-24"
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
        assert ok, f"batch189 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/frameos/canvas/demo", wait_until="domcontentloaded", timeout=90000)
    page.wait_for_timeout(1200)

    node = page.locator(".react-flow__node-text").first
    box = node.bounding_box()
    check("boot:node", box is not None)
    if not box:
        raise RuntimeError("node missing")
    w0 = page.evaluate(
        "window.__frameos_store.getState().nodes.find((n) => n.id === 'text-1').style.width"
    )

    # 按住右下角 resize 手柄拖大 (+100, +80)
    handle = node.locator(".resize-handle")
    hb = handle.bounding_box()
    if not hb:
        raise RuntimeError("resize handle missing")
    page.mouse.move(hb["x"] + hb["width"] / 2, hb["y"] + hb["height"] / 2)
    page.mouse.down()
    for i in range(1, 7):
        page.mouse.move(
            hb["x"] + hb["width"] / 2 + 100 * i / 6,
            hb["y"] + hb["height"] / 2 + 80 * i / 6,
        )
    page.mouse.up()
    page.wait_for_timeout(500)

    size_after = page.evaluate(
        """(() => {
          const n = window.__frameos_store.getState().nodes.find((n) => n.id === 'text-1');
          return { w: n.style.width, h: n.style.height };
        })()"""
    )
    check(
        "resize:grows",
        size_after["w"] > w0 and size_after["h"] > 200,
    )

    # 撤销 → 恢复原尺寸 (一次撤销完成整个手势)
    page.keyboard.press("Meta+z")
    page.wait_for_timeout(400)
    size_undo = page.evaluate(
        """(() => {
          const n = window.__frameos_store.getState().nodes.find((n) => n.id === 'text-1');
          return { w: n.style.width, h: n.style.height };
        })()"""
    )
    check(
        "resize:undo-restores",
        size_undo["w"] == w0 and size_undo["h"] == 200,
    )

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 189, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch189: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
