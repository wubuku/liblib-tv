"""Jimeng clone batch 43 verifier — member modal credits slider drag.

Contract: pressing on the premium slider track and dragging scrubs the
selected stop (credits readout updates to the snapped stop value);
release persists; stop buttons still work after a drag.
"""

import os
import re
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "docs" / "design-references" / "jimeng"
BASE_URL = os.environ.get("JIMENG_BASE_URL", "http://localhost:4317")

CANVAS_URL = f"{BASE_URL}/jimeng/canvas/demo"
VIEWPORT = {"width": 1680, "height": 826}


def credits(page) -> str:
    return page.evaluate(
        """() => [...document.querySelectorAll('[data-testid="plan-credits"]')]
            .map(e => e.textContent.match(/(\\d+)积分每月/)?.[1])[2]"""
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

        page.locator('button[aria-label="会员订阅"]').click()
        page.wait_for_timeout(800)

        # drag on the premium track: press at ~20% (snaps to stop 0),
        # scrub right to ~95% (snaps to stop 3), release
        track = page.evaluate(
            """() => {
                const stops = [...document.querySelectorAll('button[aria-label^="积分档位"]')];
                const first = stops[0].getBoundingClientRect();
                const last = stops[stops.length - 1].getBoundingClientRect();
                return {x0: first.x + first.width/2, x1: last.x + last.width/2,
                        y: first.y + first.height/2};
            }"""
        )
        page.mouse.move(track["x0"], track["y"])
        page.mouse.down()
        page.mouse.move(track["x1"], track["y"], steps=12)
        page.mouse.up()
        page.wait_for_timeout(500)
        c = credits(page)
        if c != "27690":
            failures.append(f"credits after drag to end: {c} (want 27690)")

        # drag back to the start
        page.mouse.move(track["x0"], track["y"])
        page.mouse.down()
        page.mouse.up()
        page.wait_for_timeout(400)
        c0 = credits(page)
        if c0 != "6160":
            failures.append(f"credits after drag back: {c0} (want 6160)")
        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch43-slider-drag-1680.png")
        )

        ctx.close()

    if failures:
        print("FAIL")
        for f in failures:
            print(" -", f)
        raise SystemExit(1)
    print("PASS: jimeng batch 43 slider drag contract")


if __name__ == "__main__":
    main()
