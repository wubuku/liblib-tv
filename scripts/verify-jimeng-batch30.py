"""Jimeng clone batch 30 verifier — slider drag-follow + preview mute sync.

Contract:
- dragging on the slider track snaps to the nearest stop (pointer down near
  the last stop → credits 27690, same as clicking);
- stop buttons still work with the drag handler mounted;
- the fullscreen preview mute icon reflects the node muted state
  (default muted → volume-x; clicking → volume-2).
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

        # ── member modal: drag-follow on slider track ──
        page.locator('button[aria-label="会员订阅"]').click()
        page.wait_for_timeout(800)

        track = page.evaluate(
            """() => {
                const stops = [...document.querySelectorAll('button[aria-label^="积分档位"]')];
                const first = stops[0].getBoundingClientRect();
                const last = stops[stops.length - 1].getBoundingClientRect();
                return {x0: first.x + first.width/2, x1: last.x + last.width/2,
                        y: first.y + first.height/2};
            }"""
        )
        # drag from stop-0 to stop-3 (last)
        page.mouse.move(track["x0"], track["y"])
        page.mouse.down()
        page.mouse.move(track["x1"], track["y"], steps=10)
        page.mouse.up()
        page.wait_for_timeout(500)
        credits = page.evaluate(
            """() => [...document.querySelectorAll('[data-testid="plan-credits"]')]
                .map(e => e.textContent.match(/(\\d+)积分每月/)?.[1])"""
        )
        if len(credits) < 3 or credits[2] != "27690":
            failures.append(f"credits after drag: {credits}")

        # stop buttons still work (click stop-0 → 6160)
        page.locator('button[aria-label="积分档位 6.2K"]').click()
        page.wait_for_timeout(400)
        credits2 = page.evaluate(
            """() => [...document.querySelectorAll('[data-testid="plan-credits"]')]
                .map(e => e.textContent.match(/(\\d+)积分每月/)?.[1])"""
        )
        if len(credits2) < 3 or credits2[2] != "6160":
            failures.append(f"credits after stop click: {credits2}")
        page.keyboard.press("Escape")
        page.wait_for_timeout(400)

        # ── preview mute sync ──
        node1 = page.locator(".react-flow__node-video").first
        node1.click(position={"x": 200, "y": 100})
        page.wait_for_timeout(500)
        page.locator('.jimeng-node-toolbar button[aria-label="全屏预览"]').click()
        page.wait_for_timeout(700)
        mute0 = page.evaluate(
            """() => {
                const d = document.querySelector('[aria-label="视频全屏预览"]');
                const b = d?.querySelector('button[aria-label*="静音"]');
                return b ? b.querySelector('svg')?.getAttribute('class')
                    ?.match(/lucide-volume-[x2]/)?.[0] : null;
            }"""
        )
        if mute0 != "lucide-volume-x":
            failures.append(f"preview default mute icon: {mute0} (want volume-x)")
        page.locator('[aria-label="视频全屏预览"] button[aria-label*="静音"]').click()
        page.wait_for_timeout(400)
        mute1 = page.evaluate(
            """() => {
                const d = document.querySelector('[aria-label="视频全屏预览"]');
                const b = d?.querySelector('button[aria-label*="静音"]');
                return b ? b.querySelector('svg')?.getAttribute('class')
                    ?.match(/lucide-volume-[x2]/)?.[0] : null;
            }"""
        )
        if mute1 != "lucide-volume-2":
            failures.append(f"preview mute after click: {mute1} (want volume-2)")
        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch30-slider-mute-1680.png")
        )

        ctx.close()

    if failures:
        print("FAIL")
        for f in failures:
            print(" -", f)
        raise SystemExit(1)
    print("PASS: jimeng batch 30 slider drag + mute sync contract")


if __name__ == "__main__":
    main()
