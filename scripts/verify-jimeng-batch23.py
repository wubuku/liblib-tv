"""Jimeng clone batch 23 verifier — node drag persistence.

Contract: dragging a node by its card moves it on canvas (bounding rect
follows the drag delta), the node stays selectable, and the move does NOT
create undo history entries (position changes are not graph mutations).
"""

import os
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "docs" / "design-references" / "jimeng"
BASE_URL = os.environ.get("JIMENG_BASE_URL", "http://localhost:4317")

CANVAS_URL = f"{BASE_URL}/jimeng/canvas/demo"
VIEWPORT = {"width": 1680, "height": 826}


def node_rect(page) -> dict:
    return page.evaluate(
        """() => {
            const n = document.querySelector('[data-id="video-empty-1"]');
            const r = n.getBoundingClientRect();
            return {x: r.x, y: r.y};
        }"""
    )


def main() -> None:
    REFERENCE_DIR.mkdir(parents=True, exist_ok=True)
    failures: list[str] = []

    with sync_playwright() as p:
        ctx = p.chromium.launch(headless=True)
        page = ctx.new_page()
        page.set_viewport_size(VIEWPORT)  # type: ignore[arg-type]
        page.goto(CANVAS_URL, wait_until="domcontentloaded")
        page.wait_for_timeout(2500)

        r0 = node_rect(page)

        # drag empty node by +100/+60 (grab its card center-left, avoiding + handle)
        ex, ey = r0["x"] + 120, r0["y"] + 100
        page.mouse.move(ex, ey)
        page.mouse.down()
        page.mouse.move(ex + 100, ey + 60, steps=10)
        page.mouse.up()
        page.wait_for_timeout(600)

        r1 = node_rect(page)
        dx, dy = r1["x"] - r0["x"], r1["y"] - r0["y"]
        if abs(dx - 100) > 12 or abs(dy - 60) > 12:
            failures.append(f"drag delta: ({dx:.0f}, {dy:.0f}) (want ~100, ~60)")

        # position change is not an undo history entry: ⌘Z must NOT restore position
        page.keyboard.press("Meta+z")
        page.wait_for_timeout(500)
        r2 = node_rect(page)
        if abs(r2["x"] - r1["x"]) < 1 and abs(r2["y"] - r1["y"]) < 1:
            pass  # position preserved after undo — correct (no history entry)
        else:
            failures.append("⌘Z restored a drag position (drag must not enter history)")

        # node remains selectable after drag
        node = page.locator('.react-flow__node[data-id="video-empty-1"]')
        node.click(position={"x": 200, "y": 100})
        page.wait_for_timeout(500)
        selected = page.evaluate(
            "() => document.querySelector('.react-flow__node[data-id=\"video-empty-1\"]').classList.contains('selected')"
        )
        if not selected:
            failures.append("node not selectable after drag")
        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch23-drag-1680.png")
        )

        ctx.close()

    if failures:
        print("FAIL")
        for f in failures:
            print(" -", f)
        raise SystemExit(1)
    print("PASS: jimeng batch 23 drag persistence contract")


if __name__ == "__main__":
    main()
