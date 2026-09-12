"""Jimeng clone batch 32 verifier — replay-at-end + progress bar seek.

Contract:
- with the video at its end (00:06/00:06, paused), clicking play restarts
  from 00:00 in the playing state;
- clicking the progress bar at ~50% seeks currentTime to ≈00:03;
- clicking the card center does not toggle selection-driven gen panel etc.
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
        page.wait_for_timeout(2500)

        # seek to end via progress bar right edge
        bar = page.evaluate(
            """() => {
                const n = document.querySelector('.react-flow__node-video');
                const b = n.querySelector('[data-testid="video-progress"]');
                const r = b.getBoundingClientRect();
                return {x: r.right - 2, y: r.y + r.height/2};
            }"""
        )
        page.locator('.react-flow__node[data-id="video-local-1"]').click(
            position={"x": 200, "y": 100}
        )
        page.wait_for_timeout(300)
        page.mouse.click(bar["x"], bar["y"])
        page.wait_for_timeout(400)
        t_end = read_time(page)
        if t_end not in ("00:05", "00:06"):
            failures.append(f"seek to end: {t_end} (want 00:05/00:06)")
        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch32-seek-end-1680.png")
        )

        # play at end → restart from 00:00
        node_center = page.evaluate(
            """() => {
                const n = document.querySelector('.react-flow__node-video');
                const r = n.getBoundingClientRect();
                return {x: r.x + r.width/2, y: r.y + r.height/2};
            }"""
        )
        page.mouse.click(node_center["x"], node_center["y"])
        page.wait_for_timeout(600)
        t0 = read_time(page)
        if t0 != "00:00":
            failures.append(f"replay at end: {t0} (want 00:00)")
        playing = page.evaluate(
            "() => !!document.querySelector('.react-flow__node-video button[aria-label=\"暂停\"]')"
        )
        if not playing:
            failures.append("not playing after replay")
        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch32-replay-1680.png")
        )

        # pause to freeze, then seek to 50% → ≈00:03
        page.mouse.click(node_center["x"], node_center["y"])
        page.wait_for_timeout(300)
        bar = page.evaluate(
            """() => {
                const n = document.querySelector('.react-flow__node-video');
                const b = n.querySelector('[data-testid="video-progress"]');
                const r = b.getBoundingClientRect();
                return {x: r.x + r.width/2, y: r.y + r.height/2};
            }"""
        )
        page.mouse.click(bar["x"], bar["y"])
        page.wait_for_timeout(400)
        t_mid = read_time(page)
        if t_mid not in ("00:02", "00:03"):
            failures.append(f"seek 50%: {t_mid} (want 00:02/00:03)")

        ctx.close()

    if failures:
        print("FAIL")
        for f in failures:
            print(" -", f)
        raise SystemExit(1)
    print("PASS: jimeng batch 32 replay + seek contract")


if __name__ == "__main__":
    main()
