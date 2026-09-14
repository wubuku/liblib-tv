"""Jimeng clone batch 76 verifier — subject tab content in asset dialog.

Contract (SOURCE_FACT batch 76, 76-subject-deep.json / 76-subject-tab.png):
- 主体 tab replaces the 图片/视频/音频/文档 filter row with a single
  active 全部 filter; empty state text is 没有可用主体 (white/35);
- footer 确认 stays disabled; 资产 tab becomes inactive (white/70);
- 文档 filter in the 资产 tab shows 暂无文档素材 (confirms the batch 75
  extrapolation).
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

        def empty_text():
            return page.locator('[data-testid="assets-empty"]').inner_text()

        # 文档 filter empty text (batch 75 extrapolation confirmed)
        page.locator('[data-testid="assets-filter-文档"]').click()
        page.wait_for_timeout(300)
        if empty_text() != "暂无文档素材":
            failures.append(f"文档 empty: {empty_text()!r} want 暂无文档素材")

        # 主体 tab
        page.locator('[data-testid="assets-tab-主体"]').click()
        page.wait_for_timeout(500)
        if empty_text() != "没有可用主体":
            failures.append(f"主体 empty: {empty_text()!r} want 没有可用主体")
        if not page.locator('[data-testid="assets-filter-全部"]').count():
            failures.append("主体 tab missing 全部 filter")
        for f in ["图片", "视频", "音频", "文档"]:
            if page.locator(f'[data-testid="assets-filter-{f}"]').count():
                failures.append(f"主体 tab still shows {f} filter")
        # 资产 tab inactive (white/70 text)
        zc = page.evaluate(
            """() => { const b = [...document.querySelectorAll('button')]
                .find(e => e.textContent.trim() === '资产');
                return b ? getComputedStyle(b).color : null; }"""
        )
        # headless chrome 可能返回 oklab 格式，比对 alpha 0.7 即可
        if not zc or "0.7" not in zc:
            failures.append(f"资产 tab inactive color: {zc}")
        # 确认 still disabled
        if not page.locator('[data-testid="assets-confirm"]').is_disabled():
            failures.append("确认 should stay disabled in 主体 tab")
        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch76-subject-tab.png")
        )

        # back to 资产 → filters restored
        page.locator('[data-testid="assets-tab-资产"]').click()
        page.wait_for_timeout(400)
        if not page.locator('[data-testid="assets-filter-图片"]').count():
            failures.append("资产 tab did not restore 图片 filter")
        if page.locator('[data-testid="assets-filter-全部"]').count():
            failures.append("资产 tab should not show 全部 filter")

        ctx.close()

    if failures:
        print("FAIL")
        for f in failures:
            print(" -", f)
        raise SystemExit(1)
    print("PASS: jimeng batch 76 subject tab contract")


if __name__ == "__main__":
    main()
