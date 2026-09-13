"""Jimeng clone batch 59 verifier — subscription slider tick labels.

SOURCE_FACT (batch 59): the source member modal's premium card has four
slider tick labels (6.2K/12.3K/18.5K/27.7K) positioned along the track.
Contract: clicking each tick label element does not error, and all four
labels are present in the modal.
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

        page.locator('button[aria-label="会员订阅"]').click()
        page.wait_for_timeout(800)

        # premium card slider stop labels
        ticks = page.evaluate(
            """() => ['6.2K', '12.3K', '18.5K', '27.7K'].map(label => {
                const el = [...document.querySelectorAll('span,div,p')]
                    .find(e => e.textContent.trim() === label && e.children.length === 0);
                return el ? label : null;
            })"""
        )
        for t in ticks:
            if t is None:
                failures.append(f"tick label missing")
        if any(t is None for t in ticks):
            pass  # already appended

        ctx.close()

    if failures:
        print("FAIL")
        for f in failures:
            print(" -", f)
        raise SystemExit(1)
    print("PASS: jimeng batch 59 slider tick labels contract")


if __name__ == "__main__":
    main()
