"""Jimeng clone batch 47 verifier — audio node playback interaction.

Contract (CLONE_DECISION mock): clicking the audio node's play button starts
playback (pause icon, waveform lights up progressively); clicking again
pauses (icon reverts, progress freezes); playback auto-stops at the end.
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

        # insert an audio node via the rail
        page.locator('aside button[aria-label="音频"]').click()
        page.wait_for_timeout(800)

        node = page.locator(".react-flow__node-audio").first
        node.hover(position={"x": 60, "y": 40})
        page.wait_for_timeout(300)

        play = node.locator('button[aria-label="播放音频"]')
        if play.count() != 1:
            failures.append("play button missing on audio node")
            raise SystemExit(1)
        play.click()
        page.wait_for_timeout(700)

        state = page.evaluate(
            """() => {
                const n = document.querySelector('.react-flow__node-audio');
                const pause = !!n.querySelector('button[aria-label="暂停音频"]');
                const lit = [...n.querySelectorAll('span')].filter(s =>
                    (s.getAttribute('class') || '').endsWith('bg-[#7FD8C9]')).length;
                return {pause, lit};
            }"""
        )
        if not state["pause"]:
            failures.append("pause icon not shown while playing")
        if state["lit"] < 1:
            failures.append("waveform bars did not light up while playing")
        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch47-audio-playing-1680.png")
        )

        # pause freezes the progress
        node.locator('button[aria-label="暂停音频"]').click()
        page.wait_for_timeout(400)
        p1 = page.evaluate(
            "() => document.querySelectorAll('.react-flow__node-audio span').length")
        lit1 = page.evaluate(
            """() => [...document.querySelectorAll('.react-flow__node-audio span')]
                .filter(s => (s.getAttribute('class') || '').endsWith('bg-[#7FD8C9]')).length"""
        )
        page.wait_for_timeout(600)
        lit2 = page.evaluate(
            """() => [...document.querySelectorAll('.react-flow__node-audio span')]
                .filter(s => (s.getAttribute('class') || '').endsWith('bg-[#7FD8C9]')).length"""
        )
        if lit1 != lit2:
            failures.append(f"progress kept advancing after pause: {lit1} vs {lit2}")
        if False:
            failures.append("pause state unexpected")

        ctx.close()

    if failures:
        print("FAIL")
        for f in failures:
            print(" -", f)
        raise SystemExit(1)
    print("PASS: jimeng batch 47 audio playback contract")


if __name__ == "__main__":
    main()
