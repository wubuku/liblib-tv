"""Jimeng clone batch 28 verifier — premium plan credits slider.

SOURCE_FACT (batch 27/13 screenshots): the 高级会员 card has a 4-stop slider
(6.2K/12.3K/18.5K/27.7K), default 12.3K = 12320积分每月.
Contract: the slider renders 4 stops in the premium card with default 12320
credits; clicking the last stop updates the credits readout (27690);
non-premium cards have no slider.
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

        page.locator('button[aria-label="会员订阅"]').click()
        page.wait_for_timeout(800)

        state = page.evaluate(
            """() => {
                const stops = [...document.querySelectorAll('button[aria-label^="积分档位"]')];
                const credits = [...document.querySelectorAll('[data-testid="plan-credits"]')]
                    .map(e => e.textContent.match(/(\\d+)积分每月/)?.[1]);
                const ticks = [...document.querySelectorAll('span')]
                    .filter(s => ['6.2K','12.3K','18.5K','27.7K'].includes(s.textContent.trim()))
                    .map(s => s.textContent.trim());
                return {stops: stops.length, credits, ticks};
            }"""
        )
        if state["stops"] != 4:
            failures.append(f"slider stops: {state['stops']} (want 4)")
        if state["ticks"] != ["6.2K", "12.3K", "18.5K", "27.7K"]:
            failures.append(f"tick labels: {state['ticks']}")
        # premium (高级会员, 3rd card) default credits = 12320
        if len(state["credits"]) < 3 or state["credits"][2] != "12320":
            failures.append(f"premium default credits: {state['credits']}")

        # click last stop → credits update to 27690
        page.locator('button[aria-label="积分档位 27.7K"]').click()
        page.wait_for_timeout(400)
        after = page.evaluate(
            """() => [...document.querySelectorAll('[data-testid="plan-credits"]')]
                .map(e => e.textContent.match(/(\\d+)积分每月/)?.[1])"""
        )
        if len(after) < 3 or after[2] != "27690":
            failures.append(f"credits after last stop: {after}")
        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch28-slider-1680.png")
        )

        ctx.close()

    if failures:
        print("FAIL")
        for f in failures:
            print(" -", f)
        raise SystemExit(1)
    print("PASS: jimeng batch 28 credits slider contract")


if __name__ == "__main__":
    main()
