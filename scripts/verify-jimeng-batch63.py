"""Jimeng clone batch 63 verifier — layout menu + group card + 背景色 palette.

Contract (SOURCE_FACT batch 63):
- 布局 dropdown items are 宫格布局 / 智能布局; 智能布局 aligns selection
  into one row (y aligned), single undo step restores.
- 编组 click creates a group card: visible frame with 「编组 N」 title;
  toolbar switches to 解除编组 + 背景色 variant.
- 背景色 palette: 6 swatches (无颜色 + 5 colors); picking a color tints
  the group frame (data-group-tint), 无颜色 clears it.
- 解除编组 clears group ids and the frame disappears.
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

        # ---- multi-select (retry: known timing flake) ----
        selected = 0
        for _attempt in range(3):
            page.mouse.click(300, 750)
            page.wait_for_timeout(300)
            c1 = center("video-local-1")
            c2 = center("video-empty-1")
            page.mouse.click(c1["x"], c1["y"])
            page.wait_for_timeout(300)
            page.keyboard.down("Shift")
            page.mouse.click(c2["x"], c2["y"])
            page.keyboard.up("Shift")
            page.wait_for_timeout(800)
            selected = page.evaluate(
                "() => document.querySelectorAll('.react-flow__node.selected').length"
            )
            if selected == 2:
                break
        if selected != 2:
            failures.append(f"multi-select failed: selected={selected}")

        mt = page.locator('[data-testid="jimeng-multi-toolbar"]')

        # ---- 布局 menu: 宫格布局 / 智能布局 ----
        mt.locator('[data-testid="multi-layout"]').click()
        page.wait_for_timeout(400)
        if page.locator('[data-testid="multi-arrange-grid"]').count() != 1:
            failures.append("布局 menu missing 宫格布局")
        if page.locator('[data-testid="multi-arrange-smart"]').count() != 1:
            failures.append("布局 menu missing 智能布局")
        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch63-layout-menu.png")
        )

        # 智能布局 → row aligned; undo restores
        page.locator('[data-testid="multi-arrange-smart"]').click()
        page.wait_for_timeout(600)
        ys = page.evaluate(
            """() => [...document.querySelectorAll('.react-flow__node.selected')]
                .map(n => parseFloat(n.style.transform.match(/translate\\(([-\\d.]+)px,\\s*([-\\d.]+)px\\)/)[2]))"""
        )
        if len(ys) == 2 and abs(ys[0] - ys[1]) > 0.5:
            failures.append(f"智能布局 did not align y: {ys}")
        page.keyboard.press("Meta+z")
        page.wait_for_timeout(600)

        # ---- 编组 → group card + toolbar variant ----
        mt.locator('[data-testid="multi-group"]').click()
        page.wait_for_timeout(800)
        frame = page.evaluate(
            """() => {
                const el = document.querySelector('[data-group-frame]');
                if (!el) return null;
                const title = (el.textContent || '').trim();
                const r = el.getBoundingClientRect();
                return {gid: el.getAttribute('data-group-frame'), title,
                        w: Math.round(r.width), h: Math.round(r.height),
                        tint: el.getAttribute('data-group-tint')};
            }"""
        )
        if not frame:
            failures.append("group frame not rendered after 编组")
        else:
            if "编组" not in frame["title"]:
                failures.append(f"group title wrong: {frame['title']!r}")
            if frame["w"] < 1000 or frame["h"] < 350:
                failures.append(
                    f"group frame too small: {frame['w']}x{frame['h']}"
                )
        if mt.locator('[data-testid="multi-ungroup"]').count() != 1:
            failures.append("toolbar did not switch to 解除编组 variant")
        if mt.locator('[data-testid="multi-bgcolor"]').count() != 1:
            failures.append("grouped toolbar missing 背景色 button")
        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch63-group-card.png")
        )

        # ---- 背景色 palette ----
        mt.locator('[data-testid="multi-bgcolor"]').click()
        page.wait_for_timeout(400)
        palette = page.locator('[data-testid="multi-bgcolor-palette"]')
        if palette.count() != 1:
            failures.append("背景色 palette not rendered")
        else:
            swatches = page.evaluate(
                """() => [...document.querySelectorAll('[data-testid^="swatch-"]')].map(
                    s => s.getAttribute('data-testid'))"""
            )
            if len(swatches) != 6 or "swatch-none" not in swatches:
                failures.append(f"palette swatches wrong: {swatches}")
            # pick purple tint
            palette.locator('[data-testid="swatch-#B55CF8"]').click()
            page.wait_for_timeout(600)
            tint = page.evaluate(
                "() => document.querySelector('[data-group-frame]')?.getAttribute('data-group-tint')"
            )
            if tint != "#B55CF8":
                failures.append(f"group tint not applied: {tint!r}")
            page.screenshot(
                path=str(REFERENCE_DIR / "jimeng-clone-batch63-bgcolor.png")
            )
            # 无颜色 clears
            mt.locator('[data-testid="multi-bgcolor"]').click()
            page.wait_for_timeout(400)
            page.locator('[data-testid="swatch-none"]').click()
            page.wait_for_timeout(600)
            tint2 = page.evaluate(
                "() => document.querySelector('[data-group-frame]')?.getAttribute('data-group-tint')"
            )
            if tint2 != "":
                failures.append(f"无颜色 did not clear tint: {tint2!r}")

        # ---- 解除编组 ----
        mt.locator('[data-testid="multi-ungroup"]').click()
        page.wait_for_timeout(700)
        frames_left = page.evaluate(
            "() => document.querySelectorAll('[data-group-frame]').length"
        )
        if frames_left != 0:
            failures.append(f"group frame still rendered after 解除编组: {frames_left}")
        if mt.locator('[data-testid="multi-group"]').count() != 1:
            failures.append("toolbar did not restore 编组 variant after ungroup")
        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch63-ungroup.png")
        )

        ctx.close()

    if failures:
        print("FAIL")
        for f in failures:
            print(" -", f)
        raise SystemExit(1)
    print("PASS: jimeng batch 63 layout menu + group card + 背景色 contract")


if __name__ == "__main__":
    main()
