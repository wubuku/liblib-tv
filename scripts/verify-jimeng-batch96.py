"""Jimeng clone batch 96 verifier — top bar evolved structure.

Contract (SOURCE_FACT batch 96, 96 顶栏 dump):
- top bar pill = [搜索][生成历史]; standalone 帮助 button removed; avatar
  aria renamed 用户菜单;
- 搜索 opens a minimal search overlay (input placeholder 搜索 +
  暂无搜索结果 empty state; content BLOCKED_BY_FIXTURE);
- 生成历史 opens the history panel (title 生成历史);
- both close on Escape.
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

        labels = page.evaluate(
            """() => [...document.querySelectorAll(
                '.jimeng-chrome-pill button, [class*="jimeng-chrome-pill"] button')]
                .map(b => b.getAttribute('aria-label'))
                .filter(a => a)"""
        )
        for want in ["搜索", "生成历史", "用户菜单"]:
            if want not in labels:
                failures.append(f"top bar missing {want}: {labels}")
        if "帮助" in labels:
            failures.append(f"帮助 button should be removed: {labels}")

        # 搜索 overlay
        page.locator('[data-testid="topbar-search"]').click()
        page.wait_for_timeout(600)
        ov = page.evaluate(
            """() => {
                const el = document.querySelector('[data-testid="jimeng-search-overlay"]');
                if (!el) return null;
                return {input: !!el.querySelector('[data-testid="jimeng-search-input"]'),
                        empty: (el.querySelector('[data-testid="search-empty"]') || {}).textContent};
            }"""
        )
        if not ov or not ov["input"] or ov["empty"] != "暂无搜索结果":
            failures.append(f"search overlay wrong: {ov}")
        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch96-search-overlay.png")
        )
        page.keyboard.press("Escape")
        page.wait_for_timeout(500)
        if page.locator('[data-testid="jimeng-search-overlay"]').count():
            failures.append("Escape did not close search overlay")

        # 生成历史 panel
        page.locator('.jimeng-chrome-pill button[aria-label="生成历史"]').click()
        page.wait_for_timeout(700)
        hist = page.evaluate(
            """() => { const el = document.querySelector('[aria-label="生成历史"][role="dialog"]');
            return el ? (el.textContent||'').includes('生成历史') : false; }"""
        )
        if not hist:
            failures.append("history panel did not open")
        else:
            page.screenshot(
                path=str(REFERENCE_DIR / "jimeng-clone-batch96-history-panel.png")
            )

        # avatar renamed
        if not page.locator('button[aria-label="用户菜单"]').count():
            failures.append("avatar aria should be 用户菜单")

        ctx.close()

    if failures:
        print("FAIL")
        for f in failures:
            print(" -", f)
        raise SystemExit(1)
    print("PASS: jimeng batch 96 top bar structure contract")


if __name__ == "__main__":
    main()
