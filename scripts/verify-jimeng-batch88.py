"""Jimeng clone batch 88 verifier — rename across node types.

Contract (SOURCE_FACT batch 88): text/audio nodes support the same
click-title inline rename (source text node aria Rename 文本 1).
- insert a text node → click its title → rename → applied;
- insert an audio node → rename its title too;
- undo steps restore.
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

        def rename_last(selector: str, new_title: str):
            sel = page.locator(selector).last
            sel.wait_for(state="visible", timeout=5000)
            sel.locator('[data-testid="node-title-text"]').click()
            page.wait_for_timeout(400)
            inp = page.locator('[data-testid="node-rename-input"]').last
            page.keyboard.press("Meta+a")
            page.keyboard.type(new_title)
            page.keyboard.press("Enter")
            page.wait_for_timeout(600)
            return sel.locator('[data-testid="node-title-text"]').inner_text()

        # text node
        page.locator('aside button[aria-label="文本"]').click()
        page.wait_for_timeout(1000)
        got = rename_last(".react-flow__node-text", "说明文字")
        if got != "说明文字":
            failures.append(f"text rename: {got!r}")
        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch88-text-rename.png")
        )

        # audio node
        page.locator('aside button[aria-label="音频"]').click()
        page.wait_for_timeout(1000)
        got2 = rename_last(".react-flow__node-audio", "背景音乐")
        if got2 != "背景音乐":
            failures.append(f"audio rename: {got2!r}")

        # undo inserts + renames (each rename is also a history entry)
        for _ in range(6):
            n = page.evaluate("() => document.querySelectorAll('.react-flow__node').length")
            if n == 2:
                break
            page.keyboard.press("Meta+z")
            page.wait_for_timeout(600)
        n = page.evaluate("() => document.querySelectorAll('.react-flow__node').length")
        if n != 2:
            failures.append(f"undo did not restore: {n} nodes")

        ctx.close()

    if failures:
        print("FAIL")
        for f in failures:
            print(" -", f)
        raise SystemExit(1)
    print("PASS: jimeng batch 88 rename across node types contract")


if __name__ == "__main__":
    main()
