"""Jimeng clone batch 72 verifier — asset library modal.

Contract (SOURCE_FACT batch 72, 72-assets-panel.png / 72-assets.json):
- left rail 资产库 opens a centered modal 800×620, bg rgb(26,26,26), r20;
- tabs 资产 (active white/8% pill) / 主体; filters 图片/视频/音频/文档 with
  active underline; 搜索 placeholder; 时间/筛选 icon buttons;
- empty state 暂无图片素材 white/35; footer 已选择 0 个素材 + disabled 确认
  (bg white/16% text white/20);
- × / Escape close; 主体 tab switches empty text to 暂无主体素材.
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
        modal = page.evaluate(
            """() => {
                const el = document.querySelector('[data-testid="jimeng-assets-modal"]');
                if (!el) return null;
                const r = el.getBoundingClientRect();
                const cs = getComputedStyle(el);
                return {w: Math.round(r.width), h: Math.round(r.height),
                        bg: cs.backgroundColor, radius: cs.borderRadius,
                        cx: r.x + r.width/2};
            }"""
        )
        if not modal:
            failures.append("assets modal not opened by rail click")
        else:
            if abs(modal["w"] - 800) > 8 or abs(modal["h"] - 620) > 8:
                failures.append(f"modal size: {modal['w']}x{modal['h']} want 800x620")
            if modal["bg"] != "rgb(26, 26, 26)":
                failures.append(f"modal bg: {modal['bg']}")
            if modal["radius"] != "20px":
                failures.append(f"modal radius: {modal['radius']}")
            if abs(modal["cx"] - VIEWPORT["width"] / 2) > 8:
                failures.append(f"modal not centered: cx={modal['cx']}")

            for sel, name in [
                ('[data-testid="assets-tab-资产"]', "资产 tab"),
                ('[data-testid="assets-tab-主体"]', "主体 tab"),
                ('[data-testid="assets-filter-图片"]', "图片 filter"),
                ('[data-testid="assets-filter-文档"]', "文档 filter"),
                ('[data-testid="assets-search"]', "search box"),
                ('[data-testid="assets-empty"]', "empty text"),
                ('[data-testid="assets-selected"]', "selected count"),
                ('[data-testid="assets-confirm"]', "confirm button"),
            ]:
                if not page.locator(sel).count():
                    failures.append(f"missing {name}")

            empty = page.locator('[data-testid="assets-empty"]').inner_text()
            if empty != "暂无图片素材":
                failures.append(f"empty text: {empty!r}")
            confirm = page.locator('[data-testid="assets-confirm"]')
            if not confirm.is_disabled():
                failures.append("确认 should be disabled")
            sel_text = page.locator('[data-testid="assets-selected"]').inner_text()
            if "已选择 0 个素材" not in sel_text:
                failures.append(f"footer text: {sel_text!r}")
            page.screenshot(
                path=str(REFERENCE_DIR / "jimeng-clone-batch72-assets-modal.png")
            )

            # 主体 tab → empty text switches (batch 76 SOURCE_FACT 修正:
            # 没有可用主体，非 暂无主体素材)
            page.locator('[data-testid="assets-tab-主体"]').click()
            page.wait_for_timeout(400)
            empty2 = page.locator('[data-testid="assets-empty"]').inner_text()
            if empty2 != "没有可用主体":
                failures.append(f"主体 empty text: {empty2!r}")
            page.locator('[data-testid="assets-tab-资产"]').click()
            page.wait_for_timeout(300)

        # Escape closes
        page.keyboard.press("Escape")
        page.wait_for_timeout(500)
        if page.locator('[data-testid="jimeng-assets-modal"]').count():
            failures.append("Escape did not close modal")

        # reopen via rail, close via ×
        page.locator('aside button[aria-label="资产库"]').click()
        page.wait_for_timeout(600)
        page.locator('[data-testid="assets-close"]').click()
        page.wait_for_timeout(500)
        if page.locator('[data-testid="jimeng-assets-modal"]').count():
            failures.append("× did not close modal")

        ctx.close()

    if failures:
        print("FAIL")
        for f in failures:
            print(" -", f)
        raise SystemExit(1)
    print("PASS: jimeng batch 72 asset library modal contract")


if __name__ == "__main__":
    main()
