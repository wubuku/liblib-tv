"""Jimeng clone batch 19 verifier — audio node mock.

Contract: rail 音频 inserts an audio node (.react-flow__node-audio) with
waveform bars and a 00:15 duration label; the node carries the video-family
skeleton (title row + handles).
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

        page.locator('aside button[aria-label="音频"]').click()
        page.wait_for_timeout(800)

        state = page.evaluate(
            """() => {
                const n = document.querySelector('.react-flow__node-audio');
                if (!n) return null;
                return {
                    title: n.textContent.includes('音频'),
                    duration: n.textContent.includes('00:15'),
                    bars: n.querySelectorAll('span.rounded-full').length,
                    handles: n.querySelectorAll('.react-flow__handle').length,
                };
            }"""
        )
        if not state:
            failures.append("audio node did not appear")
        else:
            if not state["title"]:
                failures.append("audio title missing")
            if not state["duration"]:
                failures.append("audio duration label missing")
            if state["bars"] < 20:
                failures.append(f"waveform bars: {state['bars']}")
            if state["handles"] < 2:
                failures.append("handles missing")
        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch19-audio-node-1680.png")
        )

        ctx.close()

    if failures:
        print("FAIL")
        for f in failures:
            print(" -", f)
        raise SystemExit(1)
    print("PASS: jimeng batch 19 audio node contract")


if __name__ == "__main__":
    main()
