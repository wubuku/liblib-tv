"""Jimeng clone batch 37 verifier — progress bar drag scrub.

Contract: pressing on the progress bar and dragging scrubs the node
currentTime continuously (down at ~10% → move to ~75% → time reads ≈00:04
after release); a plain click still seeks (regression of batch 32).
"""

import os
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "docs" / "design-references" / "jimeng"
BASE_URL = os.environ.get("JIMENG_BASE_URL", "http://localhost:4317")

CANVAS_URL = f"{BASE_URL}/jimeng/canvas/demo"
VIEWPORT = {"width": 1680, "height": 826}


def bar_pos(page, frac: float) -> dict:
    return page.evaluate(
        """([frac]) => {
            const b = document.querySelector('[data-testid="video-progress"]');
            const r = b.getBoundingClientRect();
            return {x: r.x + r.width * frac, y: r.y + r.height / 2};
        }""",
        [frac],
    )


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

        # drag-scrub: down at 10% → move to 75% → up
        start = bar_pos(page, 0.10)
        page.mouse.move(start["x"], start["y"])
        page.mouse.down()
        mid = bar_pos(page, 0.45)
        page.mouse.move(mid["x"], mid["y"], steps=8)
        t_mid = read_time(page)
        end = bar_pos(page, 0.75)
        page.mouse.move(end["x"], end["y"], steps=8)
        page.mouse.up()
        page.wait_for_timeout(400)

        t_end = read_time(page)
        if t_end != "00:04":
            failures.append(f"after scrub to 75%: {t_end} (want 00:04)")
        # scrub updated continuously: mid-drag readout should not have stayed
        # at 00:00 (start) — accept 00:01..00:03
        if t_mid not in ("00:01", "00:02", "00:03"):
            failures.append(f"mid-drag time: {t_mid}")
        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch37-scrub-1680.png")
        )

        # plain click still seeks (regression of batch 32): click 100% edge
        point = bar_pos(page, 0.999)
        page.mouse.click(point["x"], point["y"])
        page.wait_for_timeout(400)
        t_click = read_time(page)
        if t_click not in ("00:05", "00:06"):
            failures.append(f"click seek regression: {t_click}")

        ctx.close()

    if failures:
        print("FAIL")
        for f in failures:
            print(" -", f)
        raise SystemExit(1)
    print("PASS: jimeng batch 37 drag scrub contract")


if __name__ == "__main__":
    main()
