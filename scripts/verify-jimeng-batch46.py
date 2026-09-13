"""Jimeng clone batch 46 verifier — ⌘A select all + Escape deselect.

Contract: ⌘A selects every node on the canvas (all carry .selected);
Escape clears the selection (no .selected remains).
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

        total = page.evaluate(
            "() => document.querySelectorAll('.react-flow__node').length"
        )

        # click a node first (focus the canvas), then ⌘A
        page.locator('.react-flow__node[data-id="video-local-1"]').click(
            position={"x": 100, "y": 50}
        )
        page.wait_for_timeout(300)
        page.keyboard.press("Meta+a")
        page.wait_for_timeout(500)
        selected = page.evaluate(
            "() => document.querySelectorAll('.react-flow__node.selected').length"
        )
        if selected != total:
            failures.append(f"⌘A selected: {selected} (want {total})")
        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch46-select-all-1680.png")
        )

        # Escape clears selection
        page.keyboard.press("Escape")
        page.wait_for_timeout(400)
        after = page.evaluate(
            "() => document.querySelectorAll('.react-flow__node.selected').length"
        )
        if after != 0:
            failures.append(f"nodes still selected after Escape: {after}")

        ctx.close()

    if failures:
        print("FAIL")
        for f in failures:
            print(" -", f)
        raise SystemExit(1)
    print("PASS: jimeng batch 46 select all + escape contract")


if __name__ == "__main__":
    main()
