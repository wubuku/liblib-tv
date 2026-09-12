"""Jimeng clone batch 41 verifier — model dropdown in the generation panel.

SOURCE_FACT (batch 41): the gen panel model selector opens a dropdown with
8 models (name + description), extracted from the source site.
Contract: selecting the empty node, clicking the model selector opens the
list; picking 即梦 Seedance 2.0 mini updates the selector text and closes.
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

        page.locator('.react-flow__node[data-id="video-empty-1"]').click(
            position={"x": 200, "y": 100}
        )
        page.wait_for_timeout(700)
        page.locator('button[aria-label="选择模型"]').click()
        page.wait_for_timeout(600)

        menu = page.evaluate(
            """() => {
                const list = document.querySelector('[role="listbox"][aria-label="模型列表"]');
                if (!list) return null;
                return [...list.querySelectorAll('[role="option"]')].map(o => ({
                    name: o.querySelector('span')?.textContent.trim(),
                    desc: o.textContent.includes('最强模型'),
                }));
            }"""
        )
        if not menu:
            failures.append("model dropdown did not open")
        else:
            names = [m["name"] for m in menu]
            want = [
                "即梦 Seedance 2.5", "即梦 Seedance 2.0 mini",
                "即梦 Seedance 2.0 Fast VIP", "即梦 Seedance 2.0 VIP",
                "即梦 Seedance 1.0 Fast", "MiniMax H3",
                "HappyHorse 1.1", "Wan 3.0",
            ]
            if names != want:
                failures.append(f"model names: {names}")
        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch41-model-menu-1680.png")
        )

        # pick mini → selector text updates, menu closes
        page.locator('[role="option"]', has_text="即梦 Seedance 2.0 mini").click()
        page.wait_for_timeout(500)
        after = page.evaluate(
            """() => ({
                text: !!document.querySelector('button[aria-label="选择模型"]')
                    ?.textContent.includes('即梦 Seedance 2.0 mini'),
                closed: !document.querySelector('[role="listbox"][aria-label="模型列表"]'),
            })"""
        )
        if not after["text"]:
            failures.append("model text did not update")
        if not after["closed"]:
            failures.append("model dropdown did not close")

        ctx.close()

    if failures:
        print("FAIL")
        for f in failures:
            print(" -", f)
        raise SystemExit(1)
    print("PASS: jimeng batch 41 model dropdown contract")


if __name__ == "__main__":
    main()
