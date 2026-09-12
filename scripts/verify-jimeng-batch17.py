"""Jimeng clone batch 17 verifier — image/text nodes + rail insertion.

Contract:
- Left rail 图片 inserts an image node at the canvas center; 文字 inserts a
  text node; 视频 inserts an empty video node.
- + handle menu 图片/文本 also create image/text nodes beside the source.
- Each new node carries the correct type class and title.
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

        # + menu 文本 first (clean canvas, no overlap)
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
        page.wait_for_timeout(500)
        page.locator('[role="menuitem"]', has_text="文本").click()
        page.wait_for_timeout(700)
        text_after = page.evaluate(
            "() => document.querySelectorAll('.react-flow__node-text').length"
        )
        if text_after != 1:
            failures.append(f"text nodes after + menu: {text_after} (want 1)")

        # rail inserts: 图片 / 文字 / 视频 (inserted at canvas center)
        page.locator('aside button[aria-label="图片"]').click()
        page.wait_for_timeout(800)
        page.locator('aside button[aria-label="文字"]').click()
        page.wait_for_timeout(800)
        page.locator('aside button[aria-label="视频"]').click()
        page.wait_for_timeout(800)

        counts = page.evaluate(
            """() => ({
                image: document.querySelectorAll('.react-flow__node-image').length,
                text: document.querySelectorAll('.react-flow__node-text').length,
                video: document.querySelectorAll('.react-flow__node-video').length,
                imageTitle: document.querySelector('.react-flow__node-image')?.textContent.trim() || '',
            })"""
        )
        if counts["image"] != 1:
            failures.append(f"image nodes: {counts['image']} (want 1)")
        if counts["text"] != 2:
            failures.append(f"text nodes: {counts['text']} (want 2)")
        if counts["video"] != 3:
            failures.append(f"video nodes: {counts['video']} (want 3)")
        if not counts["imageTitle"].startswith("图片"):
            failures.append(f"image title: {counts['imageTitle']!r}")
        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch17-rail-insert-1680.png")
        )

        ctx.close()

    if failures:
        print("FAIL")
        for f in failures:
            print(" -", f)
        raise SystemExit(1)
    print("PASS: jimeng batch 17 insert nodes contract")


if __name__ == "__main__":
    main()
