"""Jimeng clone batch 14 verifier — undo/redo history + keyboard shortcuts.

Contract: +菜单 视频 adds a node; ⌘Z undoes it; ⌘⇧Z redoes; ⌘C/⌘V duplicates;
Delete removes the selected node; context menu 撤销/重做 enable/disable with
history state.
"""

import os
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "docs" / "design-references" / "jimeng"
BASE_URL = os.environ.get("JIMENG_BASE_URL", "http://localhost:4317")

CANVAS_URL = f"{BASE_URL}/jimeng/canvas/demo"
VIEWPORT = {"width": 1680, "height": 826}


def node_count(page) -> int:
    return page.evaluate(
        "() => document.querySelectorAll('.react-flow__node-video').length"
    )


def add_video_via_menu(page) -> None:
    node1 = page.locator(".react-flow__node-video").first
    node1.hover(position={"x": 400, "y": 160})
    page.wait_for_timeout(400)
    plus = page.evaluate(
        """() => {
            const n = [...document.querySelectorAll('.react-flow__node-video')][0];
            const el = n.querySelector('[aria-label="右侧添加节点"]');
            const r = el.getBoundingClientRect();
            return {x: r.x + r.width/2, y: r.y + r.height/2};
        }"""
    )
    page.mouse.click(plus["x"], plus["y"])
    page.wait_for_timeout(600)
    page.locator('[role="menuitem"]', has_text="视频").click()
    page.wait_for_timeout(700)


def main() -> None:
    REFERENCE_DIR.mkdir(parents=True, exist_ok=True)
    failures: list[str] = []

    with sync_playwright() as p:
        ctx = p.chromium.launch(headless=True)
        page = ctx.new_page()
        page.set_viewport_size(VIEWPORT)  # type: ignore[arg-type]
        page.goto(CANVAS_URL, wait_until="domcontentloaded")
        page.wait_for_timeout(2200)

        assert node_count(page) == 2

        # add → 3 nodes
        add_video_via_menu(page)
        if node_count(page) != 3:
            failures.append(f"after add: {node_count(page)} (want 3)")

        # ⌘Z → 2
        page.keyboard.press("Meta+z")
        page.wait_for_timeout(500)
        if node_count(page) != 2:
            failures.append(f"after ⌘Z: {node_count(page)} (want 2)")

        # ⌘⇧Z → 3
        page.keyboard.press("Meta+Shift+z")
        page.wait_for_timeout(500)
        if node_count(page) != 3:
            failures.append(f"after ⌘⇧Z: {node_count(page)} (want 3)")

        # ⌘C / ⌘V on selection → 4
        node1 = page.locator(".react-flow__node-video").first
        node1.click(position={"x": 200, "y": 100})
        page.wait_for_timeout(400)
        page.keyboard.press("Meta+c")
        page.wait_for_timeout(200)
        page.keyboard.press("Meta+v")
        page.wait_for_timeout(600)
        if node_count(page) != 4:
            failures.append(f"after ⌘C/⌘V: {node_count(page)} (want 4)")

        # ⌘Z undoes the paste → 3
        page.keyboard.press("Meta+z")
        page.wait_for_timeout(600)
        if node_count(page) != 3:
            failures.append(f"after ⌘Z paste: {node_count(page)} (want 3)")

        # Delete key removes the selected node (local-1 center — no overlap)
        node1 = page.locator(".react-flow__node-video").first
        node1.click(position={"x": 200, "y": 100})
        page.wait_for_timeout(400)
        page.keyboard.press("Delete")
        page.wait_for_timeout(600)
        if node_count(page) != 2:
            failures.append(f"after Delete: {node_count(page)} (want 2)")

        # ⌘Z restores local-1 → 3
        page.keyboard.press("Meta+z")
        page.wait_for_timeout(600)
        if node_count(page) != 3:
            failures.append(f"after ⌘Z delete: {node_count(page)} (want 3)")

        # context menu undo/redo rows (right-click at empty-1 center; whichever
        # node is on top there, the menu content is node-agnostic)
        empty_center = page.evaluate(
            """() => {
                const n = document.querySelector('[data-id="video-empty-1"]');
                if (!n) return null;
                const r = n.getBoundingClientRect();
                return {x: r.x + r.width/2, y: r.y + r.height/2};
            }"""
        )
        page.mouse.click(empty_center["x"], empty_center["y"], button="right")
        page.wait_for_timeout(600)
        menu = page.evaluate(
            """() => {
                const m = [...document.querySelectorAll('[role="menu"]')]
                    .find(m => m.textContent.includes('撤销'));
                if (!m) return null;
                return [...m.querySelectorAll('[role="menuitem"]')]
                    .filter(b => /撤销|重做/.test(b.textContent))
                    .map(b => ({label: b.textContent.trim().slice(0, 2), disabled: b.disabled}));
            }"""
        )
        if not menu:
            failures.append("context menu missing undo/redo rows")
        else:
            undo_row = next((r for r in menu if r["label"] == "撤销"), None)
            redo_row = next((r for r in menu if r["label"] == "重做"), None)
            if not undo_row or undo_row["disabled"]:
                failures.append("撤销 should be enabled with history")
            if not redo_row or redo_row["disabled"]:
                failures.append("重做 should be enabled after an undo")
        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch14-undo-context-1680.png")
        )
        page.keyboard.press("Escape")

        ctx.close()

    if failures:
        print("FAIL")
        for f in failures:
            print(" -", f)
        raise SystemExit(1)
    print("PASS: jimeng batch 14 history + shortcuts contract")


if __name__ == "__main__":
    main()
