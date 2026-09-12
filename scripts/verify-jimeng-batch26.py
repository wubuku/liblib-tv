"""Jimeng clone batch 26 verifier — member modal promo countdown.

Contract: the subscription modal promo banner shows four white countdown
cards (天/小时/分钟/秒) with numeric values that tick down over time.
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

        page.locator('button[aria-label="会员订阅"]').click()
        page.wait_for_timeout(800)

        def countdown_state() -> dict:
            return page.evaluate(
                """() => {
                    const units = ['天','小时','分钟','秒'];
                    const cards = units.map(unit => {
                        const c = [...document.querySelectorAll('div')].find(d =>
                            d.querySelector('span:last-child')?.textContent.trim() === unit
                            && /^\\d\\d$/.test(d.querySelector('span')?.textContent.trim() || ''));
                        return c ? {
                            value: c.querySelector('span').textContent,
                            unit,
                        } : null;
                    }).filter(Boolean);
                    const sec = cards.find(c => c.unit === '秒');
                    return {cards, seconds: sec ? sec.value : null};
                }"""
            )

        c0 = countdown_state()
        if len(c0["cards"]) != 4:
            failures.append(f"countdown cards: {len(c0['cards'])} (want 4)")
        else:
            units = [c["unit"] for c in c0["cards"]]
            if units != ["天", "小时", "分钟", "秒"]:
                failures.append(f"countdown units: {units}")
            if c0["seconds"] != "11":
                failures.append(f"initial seconds: {c0['seconds']} (want 11)")

        page.wait_for_timeout(2500)
        c1 = countdown_state()
        if c1["seconds"] == c0["seconds"]:
            failures.append("countdown did not tick")

        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch26-countdown-1680.png")
        )

        ctx.close()

    if failures:
        print("FAIL")
        for f in failures:
            print(" -", f)
        raise SystemExit(1)
    print("PASS: jimeng batch 26 countdown contract")


if __name__ == "__main__":
    main()
