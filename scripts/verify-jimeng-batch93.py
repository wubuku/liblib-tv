"""Jimeng clone batch 93 verifier — dock edge-visibility toggle.

Contract (SOURCE_FACT batch 93, dock aria dump):
- dock buttons = [选择工具][小地图][显示连线][缩放];
- clicking 显示连线 hides all edge paths; clicking again restores them.
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

        labels = page.evaluate(
            """() => [...document.querySelectorAll('.jimeng-bottom-dock button')]
                .map(b => b.getAttribute('aria-label'))"""
        )
        if labels != ["选择工具", "小地图", "显示连线", "缩放"]:
            failures.append(f"dock buttons: {labels}")

        # need an edge: create one via capture-frame? simpler — use upload flow?
        # Use the video node's + handle insert (视频) → adds node + edge.
        c = page.evaluate(
            """() => { const n = document.querySelector('[data-id="video-local-1"]');
                const r = n.getBoundingClientRect();
                return {x: r.x + 60, y: r.y + 20}; }"""
        )
        page.mouse.click(c["x"], c["y"])
        page.wait_for_timeout(600)
        # hover the card to reveal right "+" then click it
        c2 = page.evaluate(
            """() => { const n = document.querySelector('[data-id="video-local-1"]');
                const r = n.getBoundingClientRect();
                return {x: r.x + r.width + 2, y: r.y + r.height/2}; }"""
        )
        page.mouse.move(c2["x"], c2["y"])
        page.wait_for_timeout(400)
        page.mouse.click(c2["x"], c2["y"])
        page.wait_for_timeout(600)
        # pick 视频 from the insert menu
        page.evaluate(
            """() => [...document.querySelectorAll('button')]
            .find(b => b.textContent.trim() === '视频' && b.getBoundingClientRect().height < 50)
            ?.click()"""
        )
        page.wait_for_timeout(1200)
        edges0 = page.evaluate("() => document.querySelectorAll('.react-flow__edge').length")
        if edges0 < 1:
            failures.append(f"setup: no edge created ({edges0})")

        # toggle 显示连线 → edges hidden
        page.locator('.jimeng-bottom-dock button[aria-label="显示连线"]').click()
        page.wait_for_timeout(500)
        edges_hidden = page.evaluate(
            "() => document.querySelectorAll('.react-flow__edge').length"
        )
        if edges_hidden != 0:
            failures.append(f"edges still rendered after hide: {edges_hidden}")
        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch93-edges-hidden.png")
        )
        # toggle back → visible
        page.locator('.jimeng-bottom-dock button[aria-label="显示连线"]').click()
        page.wait_for_timeout(500)
        edges_shown = page.evaluate(
            "() => document.querySelectorAll('.react-flow__edge').length"
        )
        if edges_shown != edges0:
            failures.append(f"edges not restored: {edges_shown} want {edges0}")

        ctx.close()

    if failures:
        print("FAIL")
        for f in failures:
            print(" -", f)
        raise SystemExit(1)
    print("PASS: jimeng batch 93 edge visibility toggle contract")


if __name__ == "__main__":
    main()
