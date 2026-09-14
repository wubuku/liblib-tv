"""Jimeng clone batch 71 verifier — group counts as a node in the top bar.

Contract (SOURCE_FACT 63-after-group.png: 节点 3 = 2 cards + 1 group):
- baseline 节点 2; create group → 节点 3; ungroup → 节点 2.
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

        def topbar_count():
            return page.evaluate(
                """() => {
                    const m = document.body.innerText.match(/节点(\\d+)/);
                    return m ? parseInt(m[1], 10) : null;
                }"""
            )

        def center(node_id):
            return page.evaluate(
                """(id) => { const n = document.querySelector(`[data-id="${id}"]`);
                    const r = n.getBoundingClientRect();
                    return {x: r.x + 60, y: r.y + 20}; }""",
                node_id,
            )

        if topbar_count() != 2:
            failures.append(f"baseline count: {topbar_count()} want 2")

        # group the two nodes via the multi toolbar
        for _ in range(3):
            page.mouse.click(300, 750)
            page.wait_for_timeout(300)
            c1 = center("video-local-1")
            c2 = center("video-empty-1")
            page.mouse.click(c1["x"] + 60, c1["y"] + 60)
            page.wait_for_timeout(300)
            page.keyboard.down("Shift")
            page.mouse.click(c2["x"] + 60, c2["y"] + 60)
            page.keyboard.up("Shift")
            page.wait_for_timeout(700)
            if page.evaluate(
                "() => document.querySelectorAll('.react-flow__node.selected').length"
            ) == 2:
                break
        if page.evaluate(
            "() => document.querySelectorAll('.react-flow__node.selected').length"
        ) != 2:
            failures.append("multi-select failed")
        page.locator('[data-testid="jimeng-multi-toolbar"] [data-testid="multi-group"]').click()
        page.wait_for_timeout(800)
        if topbar_count() != 3:
            failures.append(f"after group count: {topbar_count()} want 3")
        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch71-group-count.png")
        )

        # ungroup → back to 2
        page.keyboard.press("Meta+Shift+g")
        page.wait_for_timeout(700)
        if topbar_count() != 2:
            failures.append(f"after ungroup count: {topbar_count()} want 2")

        ctx.close()

    if failures:
        print("FAIL")
        for f in failures:
            print(" -", f)
        raise SystemExit(1)
    print("PASS: jimeng batch 71 group node count contract")


if __name__ == "__main__":
    main()
