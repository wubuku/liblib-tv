"""Jimeng clone batch 44 verifier — trim START handle drag.

Contract: dragging the start handle right increases the left time readout
(from 00:00), decreases the selected duration label, and the selection
window's left edge follows. This completes the trim semantics validated in
batch 33 (which covered only the END handle).
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

        page.locator('.react-flow__node[data-id="video-local-1"]').click(
            position={"x": 200, "y": 100}
        )
        page.wait_for_timeout(500)
        page.locator(".jimeng-node-toolbar button", has_text="视频修剪").click()
        page.wait_for_timeout(900)

        d0 = page.evaluate(
            "() => document.querySelector('[data-testid=\"trim-duration\"]')?.textContent"
        )
        t0 = page.evaluate(
            """() => {
                const tb = [...document.querySelectorAll('.react-flow__node-toolbar')]
                    .find(t => t.textContent.includes('确认'));
                return tb?.textContent.match(/(\\d\\d:\\d\\d) \\/ /)?.[1];
            }"""
        )

        # drag the START handle right by ~120px
        h = page.evaluate(
            """() => {
                const n = document.querySelector('[data-id="video-local-1"]');
                const tb = [...document.querySelectorAll('.react-flow__node-toolbar')]
                    .find(t => t.textContent.includes('确认'));
                const h = tb.querySelector('[aria-label="修剪起点"]');
                const r = h.getBoundingClientRect();
                return {x: r.x + r.width/2, y: r.y + r.height/2};
            }"""
        )
        page.mouse.move(h["x"], h["y"])
        page.mouse.down()
        page.mouse.move(h["x"] + 120, h["y"], steps=10)
        page.mouse.up()
        page.wait_for_timeout(600)

        state = page.evaluate(
            """() => {
                const tb = [...document.querySelectorAll('.react-flow__node-toolbar')]
                    .find(t => t.textContent.includes('确认'));
                const dur = document.querySelector('[data-testid="trim-duration"]')?.textContent;
                const t = tb?.textContent.match(/(\\d\\d:\\d\\d) \\/ /)?.[1];
                const h = tb?.querySelector('[aria-label="修剪起点"]');
                return {dur, t, hx: h ? Math.round(h.getBoundingClientRect().x) : null};
            }"""
        )
        if d0 == state["dur"]:
            failures.append(f"duration label unchanged: {d0}")
        if state["t"] == "00:00" or state["t"] is None:
            failures.append(f"start time did not advance: {state['t']}")
        if state["hx"] is None:
            failures.append("start handle missing after drag")

        # confirm → node currentTime reflects the new start (>= 1s)
        page.locator("button", has_text="确认").last.click()
        page.wait_for_timeout(700)
        node_time = page.evaluate(
            """() => {
                const n = document.querySelector('.react-flow__node[data-id="video-local-1"]');
                const m = n.textContent.match(/(\\d\\d:\\d\\d) \\/ (\\d\\d:\\d\\d)/);
                return m ? {cur: m[1], dur: m[2]} : null;
            }"""
        )
        if not node_time:
            failures.append("node time row missing after confirm")
        elif node_time["cur"] == "00:00":
            failures.append("node start time should reflect the new start offset")
        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch44-start-handle-1680.png")
        )

        ctx.close()

    if failures:
        print("FAIL")
        for f in failures:
            print(" -", f)
        raise SystemExit(1)
    print("PASS: jimeng batch 44 start handle contract")


if __name__ == "__main__":
    main()
