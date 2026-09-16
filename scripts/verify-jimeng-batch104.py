"""Jimeng clone batch 104 verifier — text node selected toolbar (Batch 241b).

Contract (SOURCE_FACT 243-source-font-menu.png): a selected (non-editing)
text node shows its own toolbar — 背景色 (opens a 6-swatch palette:
无 + 青绿/靛蓝/紫/橙/黄) / 展开钮 / 下载. Picking a swatch applies the
card background; 无 resets to the default dark gradient.
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

        page.locator('aside button[aria-label="文本"]').click()
        page.wait_for_timeout(900)

        # selected toolbar present
        tb = page.evaluate(
            """() => {
                const btns = [...document.querySelectorAll('button')]
                    .filter(b => ['背景色', '展开文本面板', '下载'].includes(
                        b.getAttribute('aria-label')));
                return btns.map(b => b.getAttribute('aria-label'));
            }"""
        )
        if tb != ["背景色", "展开文本面板", "下载"]:
            failures.append(f"text toolbar buttons: {tb}")

        # open palette
        page.locator('button[aria-label="背景色"]').click()
        page.wait_for_timeout(400)
        swatches = page.evaluate(
            """() => [...document.querySelectorAll('[role="menu"][aria-label="背景色调色板"] button')]
                .map(b => b.getAttribute('aria-label'))"""
        )
        want = ["背景色 无", "背景色 青绿", "背景色 靛蓝", "背景色 紫", "背景色 橙", "背景色 黄"]
        if swatches != want:
            failures.append(f"palette swatches: {swatches}")
        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch104-text-palette.png")
        )

        # pick 紫 → card background updates
        page.locator('button[aria-label="背景色 紫"]').click()
        page.wait_for_timeout(400)
        bg = page.evaluate(
            """() => {
                const n = document.querySelector('.react-flow__node-text');
                const card = n.querySelector('.h-full.w-full');
                return getComputedStyle(card).backgroundColor;
            }"""
        )
        # #A46BFF → rgb(164, 107, 255)
        if "164" not in bg or "107" not in bg:
            failures.append(f"card background after 紫: {bg}")

        # 无 resets
        page.locator('button[aria-label="背景色"]').click()
        page.wait_for_timeout(300)
        page.locator('button[aria-label="背景色 无"]').click()
        page.wait_for_timeout(400)
        bg2 = page.evaluate(
            """() => {
                const n = document.querySelector('.react-flow__node-text');
                const card = n.querySelector('.h-full.w-full');
                return getComputedStyle(card).backgroundImage
                    || getComputedStyle(card).backgroundColor;
            }"""
        )
        if bg2 == "none" and "gradient" not in bg2:
            failures.append(f"card background after 无: {bg2}")

        ctx.close()

    if failures:
        print("FAIL batch 104:")
        for f in failures:
            print("  -", f)
        raise SystemExit(1)
    print("PASS batch 104: text node toolbar + background palette")


if __name__ == "__main__":
    main()
