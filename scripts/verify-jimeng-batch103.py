"""Jimeng clone batch 103 verifier — text node editing toolbar (Batch 241).

Contract (SOURCE_FACT 241-source-text-edit.png): double-clicking a text
card enters inline editing and shows a rich-text toolbar above the card —
字体∨ / 无序列表 / 有序列表 / 加粗 / 删除线 / 斜体 / 下划线 / 展开编辑 —
8 mock buttons in a dark pill; the empty-state hint 双击编辑文本 is
replaced by the focused textarea; Escape exits editing.
"""

import os
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "docs" / "design-references" / "jimeng"
BASE_URL = os.environ.get("JIMENG_BASE_URL", "http://localhost:4317")

CANVAS_URL = f"{BASE_URL}/jimeng/canvas/demo"
VIEWPORT = {"width": 1680, "height": 826}

WANT_BUTTONS = [
    "字体",
    "无序列表",
    "有序列表",
    "加粗",
    "删除线",
    "斜体",
    "下划线",
    "展开编辑",
]


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

        card = page.locator(".react-flow__node-text")
        card.dblclick()
        page.wait_for_timeout(600)

        tb = page.evaluate(
            """() => {
                const bar = document.querySelector('[data-testid="text-format-toolbar"]');
                if (!bar) return null;
                return {
                    buttons: [...bar.querySelectorAll('button')]
                        .map(b => b.getAttribute('aria-label')),
                    hasTextarea: !!document.querySelector(
                        '.react-flow__node-text textarea'),
                    hintGone: ![...document.querySelectorAll(
                        '.react-flow__node-text p')]
                        .some(p => p.textContent.trim() === '双击编辑文本'),
                };
            }"""
        )
        if not tb:
            failures.append("text format toolbar missing in editing mode")
        else:
            if tb["buttons"] != WANT_BUTTONS:
                failures.append(f"toolbar buttons: {tb['buttons']}")
            if not tb["hasTextarea"]:
                failures.append("editing textarea missing")
            if not tb["hintGone"]:
                failures.append("双击编辑文本 hint still visible while editing")
        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch103-text-toolbar.png")
        )

        # Escape exits editing
        page.keyboard.press("Escape")
        page.wait_for_timeout(400)
        gone = page.evaluate(
            "() => !document.querySelector('[data-testid=\"text-format-toolbar\"]')"
        )
        if not gone:
            failures.append("Escape did not exit editing")

        ctx.close()

    if failures:
        print("FAIL batch 103:")
        for f in failures:
            print("  -", f)
        raise SystemExit(1)
    print("PASS batch 103: text editing rich-text toolbar (8 mock buttons)")


if __name__ == "__main__":
    main()
