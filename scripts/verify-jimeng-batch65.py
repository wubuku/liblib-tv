"""Jimeng clone batch 65 verifier — group interaction semantics lock-in.

Source evidence (batch 65 extraction, read-only on the live canvas):
- clicking a member card of a group selects ONLY that member (not the
  whole group) — matches the clone's groupId model.
- dragging the group panel gap does NOT move group members.

Clone contracts locked here:
- group frame title numbering: first group 「编组 1」, next 「编组 2」
  (groupNames seq persists across ungroup).
- gap drag leaves node flow positions unchanged.
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

        def center(node_id):
            return page.evaluate(
                """(id) => { const n = document.querySelector(`[data-id="${id}"]`);
                    const r = n.getBoundingClientRect();
                    return {x: r.x + 60, y: r.y + 20}; }""",
                node_id,
            )

        def select_both_and_group():
            for _ in range(3):
                page.mouse.click(300, 750)
                page.wait_for_timeout(300)
                c1 = center("video-local-1")
                c2 = center("video-empty-1")
                page.mouse.click(c1["x"], c1["y"])
                page.wait_for_timeout(300)
                page.keyboard.down("Shift")
                page.mouse.click(c2["x"], c2["y"])
                page.keyboard.up("Shift")
                page.wait_for_timeout(700)
                if page.evaluate(
                    "() => document.querySelectorAll('.react-flow__node.selected').length"
                ) == 2:
                    break
            mt = page.locator('[data-testid="jimeng-multi-toolbar"]')
            mt.locator('[data-testid="multi-group"]').click()
            page.wait_for_timeout(700)
            page.mouse.click(300, 750)  # deselect
            page.wait_for_timeout(400)

        # ---- group 1: frame title 编组 1 ----
        select_both_and_group()
        title1 = page.evaluate(
            """() => document.querySelector('[data-group-frame]')?.textContent?.trim()"""
        )
        if title1 != "编组 1":
            failures.append(f"group 1 title: {title1!r} want '编组 1'")

        # ---- member click selects only that member ----
        c1 = center("video-local-1")
        page.mouse.click(c1["x"], c1["y"])
        page.wait_for_timeout(600)
        sel = page.evaluate(
            "() => [...document.querySelectorAll('.react-flow__node.selected')].map(n => n.getAttribute('data-id'))"
        )
        if sel != ["video-local-1"]:
            failures.append(f"member click selection: {sel} want ['video-local-1']")
        multi_tb = page.evaluate(
            "() => document.querySelector('[data-testid=\\'jimeng-multi-toolbar\\']') !== null"
        )
        if multi_tb:
            failures.append("multi toolbar visible for single member selection")

        # ---- gap drag does not move group members ----
        pos_before = page.evaluate(
            """() => ['video-local-1', 'video-empty-1'].map(id =>
                document.querySelector(`[data-id="${id}"]`).style.transform)"""
        )
        page.mouse.move(930, 447)
        page.wait_for_timeout(200)
        page.mouse.down()
        page.mouse.move(1050, 507, steps=10)
        page.mouse.up()
        page.wait_for_timeout(600)
        pos_after = page.evaluate(
            """() => ['video-local-1', 'video-empty-1'].map(id =>
                document.querySelector(`[data-id="${id}"]`).style.transform)"""
        )
        if pos_before != pos_after:
            failures.append(f"gap drag moved nodes: {pos_before} -> {pos_after}")
        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch65-group-interactions.png")
        )

        # ---- ungroup, regroup → 编组 2 ----
        c1 = center("video-local-1")
        c2 = center("video-empty-1")
        page.mouse.click(c1["x"], c1["y"])
        page.wait_for_timeout(300)
        page.keyboard.down("Shift")
        page.mouse.click(c2["x"], c2["y"])
        page.keyboard.up("Shift")
        page.wait_for_timeout(600)
        page.keyboard.press("Meta+Shift+g")
        page.wait_for_timeout(600)
        select_both_and_group()
        title2 = page.evaluate(
            """() => document.querySelector('[data-group-frame]')?.textContent?.trim()"""
        )
        if title2 != "编组 2":
            failures.append(f"group 2 title: {title2!r} want '编组 2'")

        ctx.close()

    if failures:
        print("FAIL")
        for f in failures:
            print(" -", f)
        raise SystemExit(1)
    print("PASS: jimeng batch 65 group interaction semantics contract")


if __name__ == "__main__":
    main()
