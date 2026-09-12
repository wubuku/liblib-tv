"""Jimeng clone batch 11 verifier — 智能超清/补帧 mock task flow (CLONE_DECISION).

Contract: clicking 智能超清 in the toolbar shows a toast (mock 任务已提交),
shows a processing overlay on the node (spinner + 处理中), and the overlay
persists (no auto-complete in mock). 补帧 behaves the same with its label.
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

        node1 = page.locator(".react-flow__node-video").first
        node1.click(position={"x": 200, "y": 100})
        page.wait_for_timeout(700)
        page.locator(".jimeng-node-toolbar button", has_text="智能超清").click()
        page.wait_for_timeout(600)

        state = page.evaluate(
            """() => {
                const toast = document.querySelector('[role="status"]');
                const overlay = [...document.querySelectorAll('.react-flow__node-video div')]
                    .find(d => d.textContent.includes('智能超清处理中'));
                const spinner = overlay ? overlay.querySelector('.animate-spin') : null;
                return {
                    toast: toast ? toast.textContent : null,
                    overlay: !!overlay,
                    spinner: !!spinner,
                };
            }"""
        )
        if not state["toast"] or "智能超清" not in (state["toast"] or ""):
            failures.append(f"toast missing/wrong: {state['toast']!r}")
        if not state["overlay"]:
            failures.append("processing overlay missing")
        if not state["spinner"]:
            failures.append("processing spinner missing")
        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch11-task-mock-1680.png")
        )

        # overlay persists (mock has no auto-complete)
        page.wait_for_timeout(3000)
        still = page.evaluate(
            "() => [...document.querySelectorAll('.react-flow__node-video div')]"
            ".some(d => d.textContent.includes('处理中'))"
        )
        if not still:
            failures.append("overlay disappeared (mock should persist)")

        ctx.close()

    if failures:
        print("FAIL")
        for f in failures:
            print(" -", f)
        raise SystemExit(1)
    print("PASS: jimeng batch 11 mock task contract")


if __name__ == "__main__":
    main()
