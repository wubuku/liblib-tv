"""Jimeng clone batch 53 verifier — mock task lifecycle completion.

Contract (CLONE_DECISION mock): 智能超清/补帧 tasks submitted via the
toolbar auto-complete after ~4s — the node's processing overlay clears
when the task is removed (no manual interaction needed).
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

        node1 = page.locator('.react-flow__node[data-id="video-local-1"]').first
        node1.click(position={"x": 200, "y": 100})
        page.wait_for_timeout(500)
        page.locator(".jimeng-node-toolbar button", has_text="智能超清").click()

        # overlay visible during the 4s task window
        page.wait_for_timeout(600)
        during = page.evaluate(
            """() => [...document.querySelectorAll('.react-flow__node')]
                .some(n => n.querySelector('.animate-spin'))"""
        )
        if not during:
            failures.append("processing overlay missing during task")
        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch53-task-mid-1680.png")
        )

        # after ~5s the task auto-completes and the overlay clears
        page.wait_for_timeout(5000)
        after = page.evaluate(
            """() => [...document.querySelectorAll('.react-flow__node')]
                .some(n => n.querySelector('.animate-spin'))"""
        )
        if after:
            failures.append("processing overlay still present after completion")
        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch53-task-done-1680.png")
        )

        ctx.close()

    if failures:
        print("FAIL")
        for f in failures:
            print(" -", f)
        raise SystemExit(1)
    print("PASS: jimeng batch 53 task lifecycle contract")


if __name__ == "__main__":
    main()
