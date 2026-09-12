"""Jimeng clone batch 13 verifier — 生成历史 dropdown + 会员 subscription modal.

Contract:
- ⌕ button opens 生成历史 dropdown (tabs 全部/图片/视频/音频 with active
  underline, empty state 暂无生成历史).
- 会员 pill opens the full-screen subscription modal (account header with
  积分详情 745, 购买积分/订阅管理, 4 billing tabs, 4 pricing cards
  ¥188/¥568/¥1959/¥8189); × closes it.
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

        # ── history dropdown ──
        page.locator('button[aria-label="生成历史"]').click()
        page.wait_for_timeout(600)
        hist = page.evaluate(
            """() => {
                const d = document.querySelector('div[aria-label="生成历史"]');
                if (!d) return null;
                return {
                    tabs: [...d.querySelectorAll('button')].map(b => b.textContent.trim()),
                    empty: d.textContent.includes('暂无生成历史'),
                };
            }"""
        )
        if not hist:
            failures.append("history dropdown did not open")
        else:
            if hist["tabs"] != ["全部", "图片", "视频", "音频"]:
                failures.append(f"history tabs: {hist['tabs']}")
            if not hist["empty"]:
                failures.append("history empty state missing")
        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch13-history-1680.png")
        )
        page.keyboard.press("Escape")
        page.wait_for_timeout(400)

        # ── member modal ──
        page.locator('button[aria-label="会员订阅"]').click()
        page.wait_for_timeout(800)
        modal = page.evaluate(
            """() => {
                const m = document.querySelector('button[aria-label="关闭订阅页"]');
                if (!m) return null;
                const root = m.closest('div.fixed');
                const body = document.body.innerText;
                return {
                    close: true,
                    credits: body.includes('积分详情') && body.includes('745'),
                    buttons: body.includes('购买积分') && body.includes('订阅管理'),
                    tabs: body.includes('连续包年') && body.includes('连续包季'),
                    prices: ['188', '568', '1959', '8189'].every(p => body.includes(p)),
                };
            }"""
        )
        if not modal:
            failures.append("member modal did not open")
        else:
            if not modal["credits"]:
                failures.append("credits header missing")
            if not modal["buttons"]:
                failures.append("购买积分/订阅管理 missing")
            if not modal["tabs"]:
                failures.append("billing tabs missing")
            if not modal["prices"]:
                failures.append("pricing cards missing")
        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch13-member-modal-1680.png")
        )
        page.locator('button[aria-label="关闭订阅页"]').click()
        page.wait_for_timeout(400)
        closed = page.evaluate(
            "() => !document.querySelector('button[aria-label=\"关闭订阅页\"]')"
        )
        if not closed:
            failures.append("member modal did not close")

        ctx.close()

    if failures:
        print("FAIL")
        for f in failures:
            print(" -", f)
        raise SystemExit(1)
    print("PASS: jimeng batch 13 history + member contract")


if __name__ == "__main__":
    main()
