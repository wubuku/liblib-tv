"""Jimeng clone batch 75 verifier — asset dialog empty text follows filter.

Contract (SOURCE_FACT batch 75, 75-assets-deep.json):
- 资产 tab: switching filters updates the empty text — 图片 → 暂无图片素材,
  视频 → 暂无视频素材, 音频 → 暂无音频素材 (文档 not captured, extrapolated);
- 主体 tab: 暂无主体素材 regardless of filter.
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

        expectations = [("图片", "暂无图片素材"), ("视频", "暂无视频素材"),
                        ("音频", "暂无音频素材"), ("文档", "暂无文档素材"),
                        ("图片", "暂无图片素材")]
        for filter_name, want in expectations:
            page.locator(f'[data-testid="assets-filter-{filter_name}"]').click()
            page.wait_for_timeout(300)
            got = empty_text()
            if got != want:
                failures.append(f"filter {filter_name}: {got!r} want {want!r}")
        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch75-filter-empty.png")
        )

        # 主体 tab (batch 76 SOURCE_FACT): 筛选为单个 全部，空态 没有可用主体
        page.locator('[data-testid="assets-tab-主体"]').click()
        page.wait_for_timeout(300)
        if empty_text() != "没有可用主体":
            failures.append(f"主体 tab empty: {empty_text()!r}")
        if not page.locator('[data-testid="assets-filter-全部"]').count():
            failures.append("主体 tab missing 全部 filter")
        if page.locator('[data-testid="assets-filter-图片"]').count():
            failures.append("主体 tab should not show 资产 filters")

        ctx.close()

    if failures:
        print("FAIL")
        for f in failures:
            print(" -", f)
        raise SystemExit(1)
    print("PASS: jimeng batch 75 asset filter empty text contract")


if __name__ == "__main__":
    main()
