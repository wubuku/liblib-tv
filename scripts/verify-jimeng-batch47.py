"""Jimeng clone batch 47 verifier — audio node playback interaction.

Contract (CLONE_DECISION mock): clicking the audio node's play button starts
static per batch 236/239 source sampling: the card shows only a centered
5-bar waveform glyph — no play button, no live playback (the old
playback contract was a mis-replication of the horizontal strip)
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
        page.wait_for_timeout(2200)

        page.locator('aside button[aria-label="音频"]').click()
        page.wait_for_timeout(900)

        state = page.evaluate(
            """() => {
                const n = document.querySelector('.react-flow__node-audio');
                if (!n) return null;
                return {
                    glyphBars: n.querySelectorAll('.flex.items-center.gap-1 > span.rounded-full').length,
                    playBtn: !!n.querySelector('button[aria-label="播放音频"], button[aria-label="暂停音频"]'),
                };
            }"""
        )
        if not state:
            failures.append("audio node missing")
        else:
            if state["glyphBars"] != 5:
                failures.append(f"waveform glyph bars: {state['glyphBars']} != 5")
            if state["playBtn"]:
                failures.append("play button must stay removed (batch 239)")

        ctx.close()

    if failures:
        print("FAIL")
        for f in failures:
            print(" -", f)
        raise SystemExit(1)
    print("PASS: jimeng batch 47 audio card static glyph contract")


if __name__ == "__main__":
    main()
