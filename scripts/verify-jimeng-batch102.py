"""Jimeng clone batch 102 verifier — card control-bar hover gating (Batch 209).

Contract (SOURCE_FACT 208-video-card.png): an unselected, idle video card
shows only its center play button — the bottom control bar (play/time/mute/
fullscreen) and progress are hidden until the card is hovered or selected.
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

        def bar_opacity() -> str | None:
            return page.evaluate(
                """() => {
                    const card = document.querySelector(
                        '[data-id="video-local-1"] .group');
                    const bar = card && card.querySelector(
                        '.absolute.inset-x-0.bottom-0');
                    return bar ? getComputedStyle(bar).opacity : null;
                }"""
            )

        # idle & unselected → hidden
        op = bar_opacity()
        if op != "0":
            failures.append(f"idle control bar opacity {op} != 0")

        # hover the card → visible
        box = page.evaluate(
            """() => {
                const el = document.querySelector('[data-id="video-local-1"]');
                const r = el.getBoundingClientRect();
                return {x: r.x + r.width / 2, y: r.y + r.height / 2};
            }"""
        )
        page.mouse.move(box["x"], box["y"])
        page.wait_for_timeout(400)
        op = bar_opacity()
        if op != "1":
            failures.append(f"hover control bar opacity {op} != 1")

        # move away → hidden again
        page.mouse.move(200, 750)
        page.wait_for_timeout(400)
        op = bar_opacity()
        if op != "0":
            failures.append(f"unhover control bar opacity {op} != 0")

        # select → visible
        page.mouse.click(box["x"] - 120, box["y"] + 40)
        page.wait_for_timeout(600)
        op = bar_opacity()
        if op != "1":
            failures.append(f"selected control bar opacity {op} != 1")

        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch102-card-hover.png")
        )
        ctx.close()

    if failures:
        print("FAIL batch 102:")
        for f in failures:
            print("  -", f)
        raise SystemExit(1)
    print("PASS batch 102: card control bar hover/selected gating")


if __name__ == "__main__":
    main()
