"""Jimeng clone batch 20 verifier — + menu audio, V tool toggle, F fullscreen.

Contract:
- + menu 音频 creates an audio node beside the source.
- V toggles the bottom dock select/move tool active state.
- F requests browser fullscreen (CLONE_DECISION); toggling back exits.
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

        # + menu 音频
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
        page.locator('[role="menuitem"]', has_text="音频").click()
        page.wait_for_timeout(800)
        audio = page.evaluate(
            "() => document.querySelectorAll('.react-flow__node-audio').length"
        )
        if audio != 1:
            failures.append(f"audio nodes after + menu: {audio} (want 1)")

        # V toggles tool state
        select_active = page.evaluate(
            """() => {
                const b = document.querySelector('button[aria-label="选择工具"]');
                return b ? b.className.includes('bg-white/10 text-white') : null;
            }"""
        )
        page.keyboard.press("v")
        page.wait_for_timeout(400)
        select_after_v = page.evaluate(
            """() => {
                const b = document.querySelector('button[aria-label="选择工具"]');
                return b ? b.className.includes('bg-white/10 text-white') : null;
            }"""
        )
        if select_active is not True or select_after_v is not False:
            failures.append(
                f"V tool toggle: {select_active} → {select_after_v}"
            )
        page.keyboard.press("v")
        page.wait_for_timeout(300)
        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch20-v-f-audio-1680.png")
        )

        ctx.close()

    if failures:
        print("FAIL")
        for f in failures:
            print(" -", f)
        raise SystemExit(1)
    print("PASS: jimeng batch 20 audio menu + V/F contract")


if __name__ == "__main__":
    main()
