"""Jimeng clone batch 61 verifier — gen model selection persists.

Contract: selecting the empty node opens the gen panel; picking a model
from the dropdown updates the button text; deselecting and re-selecting
the node restores the persisted model (store-backed, not local state).
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
        page.set_viewport_size(VIEWPORT)
        page.goto(CANVAS_URL, wait_until="domcontentloaded")
        page.wait_for_timeout(2500)

        page.locator('.react-flow__node[data-id="video-empty-1"]').click(
            position={"x": 200, "y": 100}
        )
        page.wait_for_timeout(700)
        page.locator('button[aria-label="选择模型: 即梦 Seedance 2.0 VIP, Standard-only model"]').click()
        page.wait_for_timeout(500)
        page.locator('[role="option"]', has_text="即梦 Seedance 2.0 mini").click()
        page.wait_for_timeout(500)

        # deselect
        page.mouse.click(300, 750)
        page.wait_for_timeout(400)

        # re-select
        page.locator('.react-flow__node[data-id="video-empty-1"]').click(
            position={"x": 200, "y": 100}
        )
        page.wait_for_timeout(700)
        model_text = page.evaluate(
            """() => {
                const btn = document.querySelector('button[aria-label="选择模型: 即梦 Seedance 2.0 VIP, Standard-only model"]');
                return btn?.textContent.trim() ?? null;
            }"""
        )
        if model_text != "即梦 Seedance 2.0 mini":
            failures.append(f"model after reopen: {model_text!r} (want mini)")

        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch61-model-persist-1680.png")
        )

        ctx.close()

    if failures:
        print("FAIL")
        for f in failures:
            print(" -", f)
        raise SystemExit(1)
    print("PASS: jimeng batch 61 model persistence contract")


if __name__ == "__main__":
    main()
