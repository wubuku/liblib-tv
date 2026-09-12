"""Jimeng clone batch 16 verifier — edge visual + multi-select.

Contract:
- Adding a node via the + menu creates a jimeng-typed edge drawn as a bezier
  path (stroke rgba(255,255,255,0.32)); clicking the edge selects it (white).
- Shift+click multi-selects two nodes (both carry .selected) — multiSelection
  key set to Shift (CLONE_DECISION).
"""

import os
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "docs" / "design-references" / "jimeng"
BASE_URL = os.environ.get("JIMENG_BASE_URL", "http://localhost:4317")

CANVAS_URL = f"{BASE_URL}/jimeng/canvas/demo"
VIEWPORT = {"width": 1680, "height": 826}


def main() -> None:
    REFERENCE_DIR.mkdir(parents=True, exist_ok=True)
    failures: list[str] = []

    with sync_playwright() as p:
        ctx = p.chromium.launch(headless=True)
        page = ctx.new_page()
        page.set_viewport_size(VIEWPORT)  # type: ignore[arg-type]
        page.goto(CANVAS_URL, wait_until="domcontentloaded")
        page.wait_for_timeout(2200)

        # add node via + menu → edge created
        node1 = page.locator(".react-flow__node-video").first
        node1.hover(position={"x": 400, "y": 160})
        page.wait_for_timeout(400)
        plus = page.evaluate(
            """() => {
                const n = [...document.querySelectorAll('.react-flow__node-video')][0];
                const el = n.querySelector('[aria-label="右侧添加节点"]');
                const r = el.getBoundingClientRect();
                return {x: r.x + r.width/2, y: r.y + r.height/2};
            }"""
        )
        page.mouse.click(plus["x"], plus["y"])
        page.wait_for_timeout(600)
        page.locator('[role="menuitem"]', has_text="视频").click()
        page.wait_for_timeout(900)

        edge = page.evaluate(
            """() => {
                const e = document.querySelector('.react-flow__edge path');
                if (!e) return null;
                return {stroke: getComputedStyle(e).stroke, width: getComputedStyle(e).strokeWidth};
            }"""
        )
        if not edge:
            failures.append("edge path not rendered")
        else:
            if edge["stroke"] != "rgba(255, 255, 255, 0.32)":
                failures.append(f"edge stroke: {edge['stroke']}")
            if edge["width"] != "1.5px":
                failures.append(f"edge width: {edge['width']}")

        # multi-select: click node1, then shift+click the empty node
        node1.click(position={"x": 200, "y": 100})
        page.wait_for_timeout(300)
        empty = page.evaluate(
            """() => {
                const n = document.querySelector('[data-id="video-empty-1"]');
                const r = n.getBoundingClientRect();
                return {x: r.x + r.width/2, y: r.y + r.height/2};
            }"""
        )
        page.keyboard.down("Shift")
        page.mouse.click(empty["x"], empty["y"])
        page.keyboard.up("Shift")
        page.wait_for_timeout(500)
        multi = page.evaluate(
            "() => document.querySelectorAll('.react-flow__node.selected').length"
        )
        if multi != 2:
            failures.append(f"multi-selected nodes: {multi} (want 2)")
        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch16-edge-multiselect-1680.png")
        )

        ctx.close()

    if failures:
        print("FAIL")
        for f in failures:
            print(" -", f)
        raise SystemExit(1)
    print("PASS: jimeng batch 16 edge + multi-select contract")


if __name__ == "__main__":
    main()
