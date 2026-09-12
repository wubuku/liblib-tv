"""Jimeng clone batch 35 verifier — captured-frame badge on the node.

Contract: after capturing a frame in the custom picker (strip click at ~70%,
截取帧, 确认), the node card shows a badge with the camera icon and the
captured time (00:04).
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

        badge_before = page.evaluate(
            "() => !!document.querySelector('[data-testid=\"captured-frame-badge\"]')"
        )
        if badge_before:
            failures.append("badge visible before any capture")

        node1 = page.locator('.react-flow__node[data-id="video-local-1"]')
        node1.click(position={"x": 200, "y": 100})
        page.wait_for_timeout(500)
        page.locator(".jimeng-node-toolbar button", has_text="截取帧").click()
        page.wait_for_timeout(500)
        page.locator("button", has_text="自定义").first.click()
        page.wait_for_timeout(700)

        strip = page.evaluate(
            """() => {
                const s = [...document.querySelectorAll('div.cursor-pointer')]
                    .find(d => d.querySelector('span[style*="left: 0%"]'));
                const r = s.getBoundingClientRect();
                return {x: r.x + r.width*0.7, y: r.y + r.height/2};
            }"""
        )
        page.mouse.click(strip["x"], strip["y"])
        page.wait_for_timeout(300)
        page.locator("button", has_text="截取帧").last.click()
        page.wait_for_timeout(300)
        page.locator("button", has_text="确认").last.click()
        page.wait_for_timeout(700)

        badge = page.evaluate(
            """() => {
                const b = document.querySelector('[data-testid="captured-frame-badge"]');
                if (!b) return null;
                return {text: b.textContent.trim(),
                        cam: !!b.querySelector('svg')};
            }"""
        )
        if not badge:
            failures.append("captured-frame badge did not appear")
        else:
            if "00:04" not in badge["text"]:
                failures.append(f"badge text: {badge['text']!r} (want 00:04)")
            if not badge["cam"]:
                failures.append("badge camera icon missing")
        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch35-frame-badge-1680.png")
        )

        ctx.close()

    if failures:
        print("FAIL")
        for f in failures:
            print(" -", f)
        raise SystemExit(1)
    print("PASS: jimeng batch 35 frame badge contract")


if __name__ == "__main__":
    main()
