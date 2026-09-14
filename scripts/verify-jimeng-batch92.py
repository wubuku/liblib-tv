"""Jimeng clone batch 92 verifier — minimap pan/zoom semantics.

Contract (SOURCE_FACT batch 92, 92-minimap-sem.json):
- dragging inside the minimap pans the canvas viewport;
- wheel-scrolling inside the minimap zooms the canvas viewport.
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

        page.locator('button[aria-label="小地图"]').click()
        page.wait_for_timeout(900)

        def vp_transform():
            return page.evaluate(
                """() => { const vp = document.querySelector('.react-flow__viewport');
                return vp ? vp.style.transform : null; }"""
            )

        panel = page.locator('[data-testid="jimeng-minimap-panel"]').bounding_box()
        if not panel:
            failures.append("minimap panel not open")
            raise SystemExit(1)
        mx = panel["x"] + panel["width"] / 2
        my = panel["y"] + panel["height"] / 2

        # drag inside minimap pans the canvas
        t0 = vp_transform()
        page.mouse.move(mx, my)
        page.mouse.down()
        page.mouse.move(mx + 40, my + 30, steps=8)
        page.mouse.up()
        page.wait_for_timeout(700)
        t1 = vp_transform()
        if t0 == t1:
            failures.append("minimap drag did not pan the canvas")

        # wheel inside minimap zooms the canvas
        z0 = vp_transform()
        page.mouse.move(mx, my)
        page.mouse.wheel(0, -240)
        page.wait_for_timeout(800)
        z1 = vp_transform()
        if z0 == z1:
            failures.append("minimap wheel did not zoom the canvas")
        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch92-minimap-sem.png")
        )

        ctx.close()

    if failures:
        print("FAIL")
        for f in failures:
            print(" -", f)
        raise SystemExit(1)
    print("PASS: jimeng batch 92 minimap pan/zoom contract")


if __name__ == "__main__":
    main()
