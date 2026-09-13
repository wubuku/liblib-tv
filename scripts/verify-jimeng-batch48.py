"""Jimeng clone batch 48 verifier — text node edit commits to the store.

Contract: double-clicking a 文字 node enters inline editing; typed text
committed with Enter persists in the store — the text survives
deselect/reselect (the display reads store data, not local state).
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

        # insert a 文字 node and edit it
        page.locator('aside button[aria-label="文字"]').click()
        page.wait_for_timeout(800)
        text_node = page.locator(".react-flow__node-text").first
        text_node.dblclick(position={"x": 100, "y": 60})
        page.wait_for_timeout(500)
        page.locator(".react-flow__node-text textarea").fill("春天，咖啡馆的相遇")
        page.keyboard.press("Enter")
        page.wait_for_timeout(500)

        # deselect and reselect: the committed text must persist (store-backed)
        page.mouse.click(300, 750)
        page.wait_for_timeout(400)
        page.locator(".react-flow__node-text").first.click(position={"x": 80, "y": 40})
        page.wait_for_timeout(500)
        persisted = page.evaluate(
            """() => document.querySelector('.react-flow__node-text')
                .textContent.includes('春天，咖啡馆的相遇')"""
        )
        if not persisted:
            failures.append("edited text did not persist after reselect")
        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch48-text-commit-1680.png")
        )

        ctx.close()

    if failures:
        print("FAIL")
        for f in failures:
            print(" -", f)
        raise SystemExit(1)
    print("PASS: jimeng batch 48 text commit contract")


if __name__ == "__main__":
    main()
