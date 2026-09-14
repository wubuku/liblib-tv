"""Jimeng clone batch 70 verifier — live top-bar node count.

Contract (SOURCE_FACT batch 70, screenshots 62-multiselect / 63-after-group):
- top bar shows 节点{N} where N tracks the live canvas node count
  (baseline 2 → insert text → 3 → undo → 2 → capture-frame image → 3).
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

        # insert text → 3
        page.locator('aside button[aria-label="文本"]').click()
        page.wait_for_timeout(1000)
        if topbar_count() != 3:
            failures.append(f"after insert count: {topbar_count()} want 3")

        # undo → 2
        page.keyboard.press("Meta+z")
        page.wait_for_timeout(700)
        if topbar_count() != 2:
            failures.append(f"after undo count: {topbar_count()} want 2")

        # capture-frame → 3 (首帧 direct image)
        c1 = center("video-local-1")
        page.mouse.click(c1["x"], c1["y"])
        page.wait_for_timeout(600)
        cap = page.evaluate(
            """() => {
                const btn = [...document.querySelectorAll('.react-flow__node-toolbar button')]
                    .find(b => b.textContent.trim() === '截取帧');
                if (!btn) return null;
                const r = btn.getBoundingClientRect();
                return {x: r.x + r.width/2, y: r.y + r.height/2};
            }"""
        )
        if not cap:
            failures.append("截取帧 not found")
        else:
            page.mouse.click(cap["x"], cap["y"])
            page.wait_for_timeout(400)
            first = page.evaluate(
                """() => {
                    const btn = [...document.querySelectorAll('button')]
                        .find(b => b.textContent.trim() === '首帧'
                            && b.getBoundingClientRect().height < 50);
                    if (!btn) return null;
                    const r = btn.getBoundingClientRect();
                    return {x: r.x + r.width/2, y: r.y + r.height/2};
                }"""
            )
            if not first:
                failures.append("首帧 item missing")
            else:
                page.mouse.click(first["x"], first["y"])
                page.wait_for_timeout(700)
                if topbar_count() != 3:
                    failures.append(
                        f"after capture count: {topbar_count()} want 3"
                    )
                page.screenshot(
                    path=str(REFERENCE_DIR / "jimeng-clone-batch70-node-count.png")
                )
                # delete the image node via ⌘Z → 2
                page.keyboard.press("Meta+z")
                page.wait_for_timeout(700)
                if topbar_count() != 2:
                    failures.append(
                        f"after capture-undo count: {topbar_count()} want 2"
                    )

        ctx.close()

    if failures:
        print("FAIL")
        for f in failures:
            print(" -", f)
        raise SystemExit(1)
    print("PASS: jimeng batch 70 live node count contract")


if __name__ == "__main__":
    main()
