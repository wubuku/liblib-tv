"""Jimeng clone batch 688 verifier — 引用参考 inline reference strip.

Contract (SOURCE_FACT 2026-09-26): clicking the 引用参考 chip in the
empty-video-node generation panel toggles an inline reference strip —
添加参考 icon button + tabs 主体/图片/视频/音频 + search input
(placeholder 搜索主体、图片、视频); clicking again collapses it.
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

        # collapse the always-on AI drawer so it stops intercepting
        # pointer events over the panel's right-side chips
        collapse = page.locator('button[aria-label="收起"]')
        if collapse.count() == 1:
            collapse.click()
            page.wait_for_timeout(400)

        # open the gen panel on the empty node
        page.locator('.react-flow__node[data-id="video-empty-1"]').click(
            position={"x": 200, "y": 100}
        )
        page.wait_for_timeout(700)

        prompt = page.locator('textarea[placeholder*="上传参考图"]')
        if prompt.count() != 1:
            failures.append("prompt textarea not found before strip open")

        # scope to the gen panel chip: only ours carries aria-pressed
        # (the AI drawer has its own 引用参考 button)
        ref_btn = page.locator('button[aria-label="引用参考"][aria-pressed]')
        if ref_btn.count() != 1:
            failures.append(f"引用参考 button count {ref_btn.count()} != 1")

        if page.locator('[data-testid="ref-strip"]').count() != 0:
            failures.append("ref strip should be closed initially")

        # toggle open
        ref_btn.click()
        page.wait_for_timeout(400)

        strip = page.locator('[data-testid="ref-strip"]')
        if strip.count() != 1:
            failures.append("ref strip did not open")
        else:
            add_ref = page.locator('button[aria-label="添加参考"]')
            if add_ref.count() != 1:
                failures.append("添加参考 button missing in strip")
            for tab in ["主体", "图片", "视频", "音频"]:
                if page.locator(f'[data-testid="ref-strip"] button:text-is("{tab}")').count() != 1:
                    failures.append(f"tab {tab} missing")
            search = page.locator('input[placeholder="搜索主体、图片、视频"]')
            if search.count() != 1:
                failures.append("strip search input missing")

        # switch active tab
        page.locator('[data-testid="ref-strip"] button:text-is("图片")').click()
        page.wait_for_timeout(200)
        pressed = page.evaluate(
            """() => {
                const tabs = Array.from(document.querySelectorAll('[data-testid="ref-strip"] button[aria-pressed]'));
                const on = tabs.filter(b => b.getAttribute('aria-pressed') === 'true');
                return on.map(b => b.textContent.trim());
            }"""
        )
        if pressed != ["图片"]:
            failures.append(f"active tab after click {pressed!r} != ['图片']")

        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch688-ref-strip-1680.png")
        )

        # toggle collapse
        ref_btn.click()
        page.wait_for_timeout(400)
        if page.locator('[data-testid="ref-strip"]').count() != 0:
            failures.append("ref strip did not collapse")
        if page.locator('button[aria-label="上传参考图"]').count() != 1:
            failures.append("upload tile not restored after collapse")

        ctx.close()

    if failures:
        print("FAIL")
        for f in failures:
            print(" -", f)
        raise SystemExit(1)
    print("PASS: jimeng batch 688 reference strip contract")


if __name__ == "__main__":
    main()
