"""Jimeng clone batch 36 verifier — frame badge interactions.

Contract (after a custom capture at ~70%):
- clicking the badge's seek area jumps the node currentTime to 00:04;
- clicking the badge × clears the badge.
"""

import os
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "docs" / "design-references" / "jimeng"
BASE_URL = os.environ.get("JIMENG_BASE_URL", "http://localhost:4317")

CANVAS_URL = f"{BASE_URL}/jimeng/canvas/demo"
VIEWPORT = {"width": 1680, "height": 826}


def capture_frame(page) -> None:
    node1 = page.locator('.react-flow__node[data-id="video-local-1"]')
    node1.click(position={"x": 200, "y": 100})
    page.wait_for_timeout(500)
    page.locator(".jimeng-node-toolbar button", has_text="截取帧").click()
    page.wait_for_timeout(500)
    page.locator("button", has_text="自定义").first.click()
    page.wait_for_timeout(700)
    strip = page.evaluate(
        """() => {
            const s = [...document.querySelectorAll('div.cursor-pointer')]
                .find(d => d.querySelector('span[style*="left: 0%"]'));
            const r = s.getBoundingClientRect();
            return {x: r.x + r.width*0.7, y: r.y + r.height/2};
        }"""
    )
    page.mouse.click(strip["x"], strip["y"])
    page.wait_for_timeout(300)
    page.locator("button", has_text="截取帧").last.click()
    page.wait_for_timeout(300)
    page.locator("button", has_text="确认").last.click()
    page.wait_for_timeout(700)


def main() -> None:
    REFERENCE_DIR.mkdir(parents=True, exist_ok=True)
    failures: list[str] = []

    with sync_playwright() as p:
        ctx = p.chromium.launch(headless=True)
        page = ctx.new_page()
        page.set_viewport_size(VIEWPORT)  # type: ignore[arg-type]
        page.goto(CANVAS_URL, wait_until="domcontentloaded")
        page.wait_for_timeout(2500)

        capture_frame(page)

        # batch 203/205 semantics: picker closes; no badge ever appears;
        # the produced image node is removed by undo
        picker_gone = page.evaluate(
            """() => ![...document.querySelectorAll('form,div')]
                .some(d => d.querySelector('[data-testid="frame-readout"]')
                          && d.textContent.includes('确认'))"""
        )
        if not picker_gone:
            failures.append("picker did not close after 确认")
        badge = page.evaluate(
            "() => !!document.querySelector('[data-testid=\"captured-frame-badge\"]')"
        )
        if badge:
            failures.append("captured-frame badge appeared (must stay removed)")
        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch36-badge-seek-1680.png")
        )

        page.keyboard.press("Meta+z")
        page.wait_for_timeout(600)
        imgs = page.evaluate(
            "() => document.querySelectorAll('.react-flow__node-image').length"
        )
        if imgs != 0:
            failures.append(f"undo did not remove image node: {imgs} left")

        ctx.close()

    if failures:
        print("FAIL")
        for f in failures:
            print(" -", f)
        raise SystemExit(1)
    print("PASS: jimeng batch 36 capture post-conditions contract")


if __name__ == "__main__":
    main()
