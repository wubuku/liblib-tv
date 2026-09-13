"""Jimeng clone batch 56 verifier — blank left-drag = marquee selection.

SOURCE_FACT (batch 56 extraction): the source's blank left-drag draws a
thin-bordered marquee rect and releases select contained nodes (1 node
selected in extraction) — this is why blank-drag does not pan.
Contract: plain left-drag on blank canvas draws the marquee; on release the
nodes inside the rect are selected (both nodes); middle-drag still pans.
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

        # blank left-drag marquee covering both nodes
        page.mouse.move(300, 750)
        page.mouse.down()
        page.mouse.move(1250, 250, steps=12)
        page.mouse.up()
        page.wait_for_timeout(600)
        selected = page.evaluate(
            "() => document.querySelectorAll('.react-flow__node.selected').length"
        )
        if selected < 2:
            failures.append(f"marquee selected: {selected} (want ≥2)")
        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch56-marquee-1680.png")
        )

        # deselect
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)

        # middle-drag still pans (panOnDrag=[1])
        before = page.evaluate(
            "() => getComputedStyle(document.querySelector('.react-flow__viewport')).transform"
        )
        page.mouse.move(600, 400)
        page.mouse.down(button="middle")
        page.mouse.move(500, 350, steps=6)
        page.mouse.up(button="middle")
        page.wait_for_timeout(400)
        after = page.evaluate(
            "() => getComputedStyle(document.querySelector('.react-flow__viewport')).transform"
        )
        if before == after:
            failures.append("middle-drag did not pan")

        ctx.close()

    if failures:
        print("FAIL")
        for f in failures:
            print(" -", f)
        raise SystemExit(1)
    print("PASS: jimeng batch 56 marquee + pan contract")


if __name__ == "__main__":
    main()
