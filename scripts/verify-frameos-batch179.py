#!/usr/bin/env python3

"""Verify Batch 179: FrameOS minimap drag pans the viewport.

2026-09-24 source re-sampling (live canvas): dragging inside the minimap
pans the canvas viewport (research lead + live sample). The clone minimap
was decorative; Batch 179 wires mouse drag on the minimap to viewport
panning (world point under the minimap cursor becomes the viewport center).
Verifies that a minimap drag changes the canvas viewport transform.
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
    / "liblib-frameos-batch179-2026-09-24"
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
        assert ok, f"batch179 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/frameos/canvas/demo", wait_until="domcontentloaded")
    page.wait_for_timeout(1200)

    vp_before = page.evaluate(
        "(() => { const t = document.querySelector('.react-flow__viewport'); return t ? t.style.transform : ''; })()"
    )

    minimap = page.locator(".minimap")
    check("minimap:visible", minimap.is_visible())
    box = minimap.bounding_box()
    check("minimap:box", box is not None and box["width"] > 100)

    # 在小地图内从右下拖到左上 (视口应随之平移)
    page.mouse.move(box["x"] + box["width"] * 0.7, box["y"] + box["height"] * 0.7)
    page.mouse.down()
    for i in range(1, 7):
        x = box["x"] + box["width"] * (0.7 - 0.4 * i / 6)
        y = box["y"] + box["height"] * (0.7 - 0.4 * i / 6)
        page.mouse.move(x, y)
    page.mouse.up()
    page.wait_for_timeout(600)

    vp_after = page.evaluate(
        "(() => { const t = document.querySelector('.react-flow__viewport'); return t ? t.style.transform : ''; })()"
    )
    check("viewport:changed", vp_before != vp_after)

    # 拖拽期间不产生节点变化 (纯视口操作)
    nodes_count = page.locator(".react-flow__node").count()
    check("nodes:intact", nodes_count >= 3)

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 179, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch179: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
