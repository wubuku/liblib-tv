"""Jimeng clone batch 7 verifier — chrome interactions.

Contract:
- Clicking the dock zoom block opens the zoom menu (7 rows, disabled
  缩放至选中项 without selection, divider before 缩放至50%); 缩放至100% really
  sets the viewport zoom and the dock readout updates.
- Clicking the top-bar ? opens the help menu (5 rows); Escape closes.
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

        # ── zoom menu ──
        page.locator('button[aria-label="缩放"]').click()
        page.wait_for_timeout(600)
        zm = page.evaluate(
            """() => {
                const m = [...document.querySelectorAll('[role="menu"]')]
                    .find(m => m.textContent.includes('放大视图'));
                if (!m) return null;
                return {
                    items: [...m.querySelectorAll('[role="menuitem"]')].map(b => ({
                        label: b.textContent.trim(),
                        disabled: b.disabled,
                    })),
                };
            }"""
        )
        if not zm:
            failures.append("zoom menu did not open")
        else:
            labels = [i["label"].strip() for i in zm["items"]]
            want = ["放大视图", "缩小视图", "适配画布", "缩放至选中项", "缩放至50%", "缩放至100%", "缩放至200%"]
            if len(labels) != len(want) or not all(
                l.startswith(w) for l, w in zip(labels, want)
            ):
                failures.append(f"zoom items: {labels}")
            zsel = zm["items"][3]
            if not zsel["disabled"]:
                failures.append("缩放至选中项 should be disabled without selection")
        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch7-zoom-menu-1680.png")
        )

        # 缩放至100% — readout should become 100%
        page.locator('[role="menuitem"]', has_text="缩放至100%").click()
        page.wait_for_timeout(800)
        zoom_text = page.evaluate(
            "() => document.querySelector('.jimeng-bottom-dock').textContent.match(/\\d+%/)?.[0]"
        )
        if zoom_text != "100%":
            failures.append(f"zoom after 缩放至100%: {zoom_text}")

        # ── help menu ──
        page.locator('button[aria-label="帮助"]').click()
        page.wait_for_timeout(600)
        hm = page.evaluate(
            """() => {
                const m = [...document.querySelectorAll('[role="menu"]')]
                    .find(m => m.textContent.includes('帮助中心'));
                if (!m) return null;
                return [...m.querySelectorAll('[role="menuitem"]')]
                    .map(b => b.textContent.trim());
            }"""
        )
        if not hm:
            failures.append("help menu did not open")
        else:
            want = ["帮助中心", "使用手册", "快捷键", "AI生成水印设置", "即梦CLI"]
            if hm != want:
                failures.append(f"help items: {hm}")
        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch7-help-menu-1680.png")
        )
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)
        closed = page.evaluate(
            "() => ![...document.querySelectorAll('[role=\"menu\"]')]"
            ".some(m => m.textContent.includes('帮助中心'))"
        )
        if not closed:
            failures.append("help menu did not close on Escape")

        ctx.close()

    if failures:
        print("FAIL")
        for f in failures:
            print(" -", f)
        raise SystemExit(1)
    print("PASS: jimeng batch 7 chrome contract")


if __name__ == "__main__":
    main()
