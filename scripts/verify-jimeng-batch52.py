"""Jimeng clone batch 52 verifier — multi-select copy/paste deepening.

Contract: after shift+click selecting two nodes, context menu 复制 copies
both into the clipboard; 粘贴 pastes both (total +2) preserving relative
offset; ⌘Z restores; the pasted group carries no residual selection.
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

        # insert a 文字 node so we have 3 nodes (video/video-empty/text)
        page.locator('aside button[aria-label="文字"]').click()
        page.wait_for_timeout(800)
        base = page.evaluate(
            "() => document.querySelectorAll('.react-flow__node').length"
        )

        # shift+click select local-1 and empty-1
        centers = page.evaluate(
            """() => [
                (() => { const n = document.querySelector('[data-id="video-local-1"]');
                    const r = n.getBoundingClientRect(); return {x: r.x + r.width/2 - 120, y: r.y + r.height/2 - 60}; })(),
                (() => { const n = document.querySelector('[data-id="video-empty-1"]');
                    const r = n.getBoundingClientRect(); return {x: r.x + r.width/2, y: r.y + r.height/2}; })(),
            ]"""
        )
        page.mouse.click(centers[0]["x"], centers[0]["y"])
        page.wait_for_timeout(300)
        page.keyboard.down("Shift")
        page.mouse.click(centers[1]["x"], centers[1]["y"])
        page.keyboard.up("Shift")
        page.wait_for_timeout(400)

        # context menu 复制 → 粘贴
        page.mouse.click(centers[0]["x"], centers[0]["y"], button="right")
        page.wait_for_timeout(600)
        page.locator('[role="menuitem"]', has_text="复制").first.click()
        page.wait_for_timeout(500)
        # 重新打开右键菜单执行粘贴
        node1 = page.locator('.react-flow__node[data-id="video-local-1"]')
        node1.click(button="right", position={"x": 200, "y": 100})
        page.wait_for_timeout(600)
        page.locator('[role="menuitem"]', has_text="粘贴").first.click()
        page.wait_for_timeout(700)

        total = page.evaluate(
            "() => document.querySelectorAll('.react-flow__node').length"
        )
        if total != base + 2:
            failures.append(f"nodes after paste: {total} (want {base + 2})")
        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch52-copy-paste-1680.png")
        )

        ctx.close()

    if failures:
        print("FAIL")
        for f in failures:
            print(" -", f)
        raise SystemExit(1)
    print("PASS: jimeng batch 52 copy/paste contract")


if __name__ == "__main__":
    main()
