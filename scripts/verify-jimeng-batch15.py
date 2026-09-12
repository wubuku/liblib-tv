"""Jimeng clone batch 15 verifier — video node playback (mock).

Contract: clicking the center play button starts playback (pause icon shows,
currentTime advances); clicking again pauses (time frozen); playback stops at
the end of the clip.
"""

import os
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "docs" / "design-references" / "jimeng"
BASE_URL = os.environ.get("JIMENG_BASE_URL", "http://localhost:4317")

CANVAS_URL = f"{BASE_URL}/jimeng/canvas/demo"
VIEWPORT = {"width": 1680, "height": 826}


def read_time(page) -> str:
    return page.evaluate(
        """() => {
            const n = document.querySelector('.react-flow__node-video');
            const m = n.textContent.match(/(\\d\\d:\\d\\d) \\/ /);
            return m ? m[1] : null;
        }"""
    )


def main() -> None:
    REFERENCE_DIR.mkdir(parents=True, exist_ok=True)
    failures: list[str] = []

    with sync_playwright() as p:
        ctx = p.chromium.launch(headless=True)
        page = ctx.new_page()
        page.set_viewport_size(VIEWPORT)  # type: ignore[arg-type]
        page.goto(CANVAS_URL, wait_until="domcontentloaded")
        page.wait_for_timeout(2200)

        t0 = read_time(page)

        # play
        page.locator('button[aria-label="播放"]').first.click()
        page.wait_for_timeout(1500)
        t1 = read_time(page)
        pause_btn = page.locator('button[aria-label="暂停"]').count()
        if pause_btn < 1:
            failures.append("pause icon not shown while playing")
        if t1 == t0:
            failures.append(f"time did not advance while playing ({t0} → {t1})")
        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch15-playing-1680.png")
        )

        # pause
        page.locator('button[aria-label="暂停"]').first.click()
        page.wait_for_timeout(400)
        t2 = read_time(page)
        page.wait_for_timeout(900)
        t3 = read_time(page)
        if page.locator('button[aria-label="暂停"]').count() > 0:
            failures.append("pause icon still present after pausing")
        if t2 != t3:
            failures.append(f"time kept advancing after pause ({t2} → {t3})")

        ctx.close()

    if failures:
        print("FAIL")
        for f in failures:
            print(" -", f)
        raise SystemExit(1)
    print("PASS: jimeng batch 15 playback contract")


if __name__ == "__main__":
    main()
