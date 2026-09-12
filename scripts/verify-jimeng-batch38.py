"""Jimeng clone batch 38 verifier — multi-select delete + text node edit.

Contract:
- shift+click selects two nodes; context menu 删除 removes BOTH in one
  history entry; ⌘Z restores both.
- inserting a 文字 node via the rail shows the text content; double-click
  enters inline editing (textarea), Enter commits the new text locally.
"""

import os
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "docs" / "design-references" / "jimeng"
BASE_URL = os.environ.get("JIMENG_BASE_URL", "http://localhost:4317")

CANVAS_URL = f"{BASE_URL}/jimeng/canvas/demo"
VIEWPORT = {"width": 1680, "height": 826}


def node_centers(page) -> list:
    return page.evaluate(
        """() => [...document.querySelectorAll('.react-flow__node')]
            .map(n => { const r = n.getBoundingClientRect();
                return {id: n.getAttribute('data-id'),
                        x: r.x + r.width/2, y: r.y + r.height/2}; })"""
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

        # insert a 文字 node via rail (so we have 3 nodes: video/video-empty/text)
        page.locator('aside button[aria-label="文字"]').click()
        page.wait_for_timeout(800)
        base_count = page.evaluate(
            "() => document.querySelectorAll('.react-flow__node').length"
        )

        # ── multi-select delete ──
        centers = node_centers(page)
        page.mouse.click(centers[0]["x"], centers[0]["y"])
        page.wait_for_timeout(300)
        page.keyboard.down("Shift")
        page.mouse.click(centers[1]["x"], centers[1]["y"])
        page.keyboard.up("Shift")
        page.wait_for_timeout(400)
        selected = page.evaluate(
            "() => document.querySelectorAll('.react-flow__node.selected').length"
        )
        if selected != 2:
            failures.append(f"multi-selected: {selected} (want 2)")

        # right-click one of the selected nodes → 删除 removes both
        page.mouse.click(centers[0]["x"], centers[0]["y"], button="right")
        page.wait_for_timeout(600)
        page.locator('[role="menuitem"]', has_text="删除").click()
        page.wait_for_timeout(700)
        after = page.evaluate(
            "() => document.querySelectorAll('.react-flow__node').length"
        )
        if after != base_count - 2:
            failures.append(f"nodes after multi delete: {after}")

        # ⌘Z restores
        page.keyboard.press("Meta+z")
        page.wait_for_timeout(600)
        restored = page.evaluate(
            "() => document.querySelectorAll('.react-flow__node').length"
        )
        if restored != base_count:
            failures.append(f"nodes after ⌘Z: {restored} (want {assert_count})")
        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch38-multidelete-1680.png")
        )

        # ── text node inline edit ──
        text_node = page.evaluate(
            """() => {
                const n = document.querySelector('.react-flow__node-text');
                const r = n.getBoundingClientRect();
                return {x: r.x + r.width/2, y: r.y + r.height/2};
            }"""
        )
        page.mouse.dblclick(text_node["x"], text_node["y"])
        page.wait_for_timeout(500)
        editing = page.evaluate(
            "() => !!document.querySelector('.react-flow__node-text textarea')"
        )
        if not editing:
            failures.append("text node did not enter edit mode on dblclick")
        else:
            page.keyboard.press("ControlOrMeta+a")
            page.keyboard.type("春天，咖啡馆的相遇")
            page.keyboard.press("Enter")
            page.wait_for_timeout(400)
            shown = page.evaluate(
                """() => document.querySelector('.react-flow__node-text')
                    .textContent.includes('春天，咖啡馆的相遇')"""
            )
            if not shown:
                failures.append("text edit did not commit")
        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch38-text-edit-1680.png")
        )

        ctx.close()

    if failures:
        print("FAIL")
        for f in failures:
            print(" -", f)
        raise SystemExit(1)
    print("PASS: jimeng batch 38 multi-select + text edit contract")


if __name__ == "__main__":
    main()
