"""Jimeng clone batch 78 verifier — asset dialog skeleton grid + icon tooltips.

Contract (SOURCE_FACT batch 78, 78-skeleton-hover.json):
- skeleton grid: 20 cells (5 cols × 4 rows), ~124×124 at zoom 1 (dialog
  is unzoomed), 2px gaps, bg white/4%, radius 2px;
- hovering the 时间/筛选 icon buttons shows tooltip pills below with the
  respective label (radix-tooltip style, 36px tall).
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

        page.locator('aside button[aria-label="资产库"]').click()
        page.wait_for_timeout(800)

        # ---- skeleton grid ----
        grid = page.evaluate(
            """() => {
                const cells = [...document.querySelectorAll('[data-testid="jimeng-assets-modal"] .grid > div')];
                if (!cells.length) return null;
                const r0 = cells[0].getBoundingClientRect();
                const r1 = cells[1].getBoundingClientRect();
                const cs = getComputedStyle(cells[0]);
                return {count: cells.length,
                        w: Math.round(r0.width), h: Math.round(r0.height),
                        gap: Math.round(r1.x - r0.x - r0.width),
                        bg: cs.backgroundColor, radius: cs.borderRadius};
            }"""
        )
        if not grid:
            failures.append("skeleton grid not found")
        else:
            if grid["count"] != 20:
                failures.append(f"skeleton cells: {grid['count']} want 20")
            if abs(grid["w"] - 124) > 6 or abs(grid["h"] - 124) > 6:
                failures.append(
                    f"skeleton cell size: {grid['w']}x{grid['h']} want ~124x124"
                )
            if abs(grid["gap"] - 2) > 1:
                failures.append(f"skeleton gap: {grid['gap']} want 2")
            if "0.04" not in grid["bg"]:
                failures.append(f"skeleton bg: {grid['bg']}")
            if grid["radius"] != "2px":
                failures.append(f"skeleton radius: {grid['radius']}")

        # ---- hover tooltips ----
        page.hover('[aria-label="时间"]')
        page.wait_for_timeout(400)
        tip1 = page.evaluate(
            """() => { const el = document.querySelector('[data-testid="assets-tip-时间"]');
                if (!el) return null;
                return {text: el.textContent.trim(),
                        visible: getComputedStyle(el).opacity === '1'}; }"""
        )
        if not tip1 or not tip1["visible"] or tip1["text"] != "时间":
            failures.append(f"时间 tooltip: {tip1}")
        page.hover('[aria-label="筛选"]')
        page.wait_for_timeout(400)
        tip2 = page.evaluate(
            """() => { const el = document.querySelector('[data-testid="assets-tip-筛选"]');
                if (!el) return null;
                return {text: el.textContent.trim(),
                        visible: getComputedStyle(el).opacity === '1'}; }"""
        )
        if not tip2 or not tip2["visible"] or tip2["text"] != "筛选":
            failures.append(f"筛选 tooltip: {tip2}")
        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch78-skeleton-tip.png")
        )

        ctx.close()

    if failures:
        print("FAIL")
        for f in failures:
            print(" -", f)
        raise SystemExit(1)
    print("PASS: jimeng batch 78 skeleton grid + tooltip contract")


if __name__ == "__main__":
    main()
