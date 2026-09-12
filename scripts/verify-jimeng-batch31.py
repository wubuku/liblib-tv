"""Jimeng clone batch 31 verifier — node color tag picker + trim handle drag.

SOURCE_FACT (batch 31): the title-row Tag icon opens a color marker picker
(ban/clear + cyan/blue/purple/orange/yellow); picking a color marks the node.
Contract:
- clicking the tag icon opens the palette; picking purple sets tagColor
  (title icon becomes a colored dot); clearing restores the Tag icon.
- the trim panel right handle drags left and the duration label decreases.
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
        page.wait_for_timeout(2500)

        # ── color tag picker ──
        node1 = page.locator('.react-flow__node[data-id="video-local-1"]')
        node1.click(position={"x": 200, "y": 100})
        page.wait_for_timeout(500)
        node1.locator('button[aria-label="节点颜色标记"]').click()
        page.wait_for_timeout(500)
        palette = page.evaluate(
            """() => {
                const items = [...document.querySelectorAll('[role="menu"]')]
                    .filter(m => m.querySelector('button[aria-label="清除颜色标记"]'));
                const m = items[items.length - 1];
                if (!m) return null;
                return [...m.querySelectorAll('button')].map(b =>
                    b.getAttribute('aria-label'));
            }"""
        )
        if not palette:
            failures.append("color palette did not open")
        else:
            want = ["清除颜色标记", "颜色标记 #3BE8E8", "颜色标记 #3D7BFF",
                    "颜色标记 #9C5BFF", "颜色标记 #F79022", "颜色标记 #FFE14D"]
            if palette != want:
                failures.append(f"palette items: {palette}")

        page.locator('button[aria-label="颜色标记 #9C5BFF"]').click()
        page.wait_for_timeout(500)
        marked = page.evaluate(
            """() => {
                const n = document.querySelector('.react-flow__node[data-id="video-local-1"]');
                const dot = [...n.querySelectorAll('span')].find(s =>
                    (s.getAttribute('style') || '').includes('rgb(156, 91, 255)'));
                return !!dot;
            }"""
        )
        if not marked:
            failures.append("color dot not shown after picking purple")
        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch31-color-tag-1680.png")
        )

        # clear
        node1.locator('button[aria-label="节点颜色标记"]').click()
        page.wait_for_timeout(400)
        page.locator('button[aria-label="清除颜色标记"]').click()
        page.wait_for_timeout(400)

        # ── trim handle drag ──
        node1.click(position={"x": 200, "y": 100})
        page.wait_for_timeout(500)
        page.locator(".jimeng-node-toolbar button", has_text="视频修剪").click()
        page.wait_for_timeout(800)
        d0 = page.evaluate(
            "() => document.querySelector('[data-testid=\"trim-duration\"]')?.textContent"
        )
        # drag the end handle left by ~120px
        handle = page.evaluate(
            """() => {
                const h = document.querySelector('[aria-label="修剪终点"]');
                const r = h.getBoundingClientRect();
                return {x: r.x + r.width/2, y: r.y + r.height/2};
            }"""
        )
        page.mouse.move(handle["x"], handle["y"])
        page.mouse.down()
        page.mouse.move(handle["x"] - 120, handle["y"], steps=10)
        page.mouse.up()
        page.wait_for_timeout(500)
        d1 = page.evaluate(
            "() => document.querySelector('[data-testid=\"trim-duration\"]')?.textContent"
        )
        if not d0 or not d1 or float(d1.replace("s", "")) >= float(d0.replace("s", "")):
            failures.append(f"trim duration did not decrease: {d0} → {d1}")
        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch31-trim-drag-1680.png")
        )

        ctx.close()

    if failures:
        print("FAIL")
        for f in failures:
            print(" -", f)
        raise SystemExit(1)
    print("PASS: jimeng batch 31 color tag + trim drag contract")


if __name__ == "__main__":
    main()
