"""Jimeng clone batch 33 verifier — trim confirm applies to node data.

Contract: open 视频修剪, drag the end handle toward the middle (duration
label decreases), confirm — the node's time row shows the trimmed duration
(00:00 / ~00:03) and the trim panel closes; ⌘Z restores the original 6s
duration (trim is an undoable graph mutation).
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

        node1 = page.locator('.react-flow__node[data-id="video-local-1"]')
        node1.click(position={"x": 200, "y": 100})
        page.wait_for_timeout(500)
        page.locator(".jimeng-node-toolbar button", has_text="视频修剪").click()
        page.wait_for_timeout(800)

        # drag end handle to the middle
        handle = page.evaluate(
            """() => {
                const h = document.querySelector('[aria-label="修剪终点"]');
                const r = h.getBoundingClientRect();
                return {x: r.x + r.width/2, y: r.y + r.height/2};
            }"""
        )
        page.mouse.move(handle["x"], handle["y"])
        page.mouse.down()
        page.mouse.move(handle["x"] - 165, handle["y"], steps=10)
        page.mouse.up()
        page.wait_for_timeout(500)
        label = page.evaluate(
            "() => document.querySelector('[data-testid=\"trim-duration\"]')?.textContent"
        )
        if not label or not (2.0 <= float(label.replace("s", "")) <= 4.5):
            failures.append(f"trimmed label after drag: {label}")

        # confirm
        page.locator("button", has_text="确认").last.click()
        page.wait_for_timeout(800)
        node_time = page.evaluate(
            """() => {
                const n = document.querySelector('.react-flow__node[data-id="video-local-1"]');
                const m = n.textContent.match(/00:00 \\/ (\\d\\d:\\d\\d)/);
                return m ? m[1] : null;
            }"""
        )
        if not node_time:
            failures.append(f"node time row after confirm: {node_time}")
        else:
            minutes, secs = node_time.split(":")
            total = int(minutes) * 60 + int(secs)
            if not (2.0 <= total <= 4.5):
                failures.append(f"node duration after trim: {node_time}")
        panel_closed = page.evaluate(
            "() => !document.querySelector('[data-testid=\"trim-duration\"]')"
        )
        if not panel_closed:
            failures.append("trim panel did not close on confirm")
        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch33-trim-applied-1680.png")
        )

        # ⌘Z restores the original duration
        page.keyboard.press("Meta+z")
        page.wait_for_timeout(600)
        restored = page.evaluate(
            """() => {
                const n = document.querySelector('.react-flow__node[data-id="video-local-1"]');
                return n.textContent.includes("00:06");
            }"""
        )
        if not restored:
            failures.append("⌘Z did not restore original 6s duration")

        ctx.close()

    if failures:
        print("FAIL")
        for f in failures:
            print(" -", f)
        raise SystemExit(1)
    print("PASS: jimeng batch 33 trim apply contract")


if __name__ == "__main__":
    main()
