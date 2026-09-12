"""Jimeng clone batch 27 verifier — fullscreen video preview (source-extracted).

SOURCE_FACT (batch 27): clicking the card's fullscreen icon opens a
full-viewport player: black backdrop, media filling the screen, bottom-left
play/pause + time, bottom-right mute + exit; no canvas chrome; Esc exits.

Contract: selecting the media node and clicking 全屏预览 in the toolbar opens
the overlay; Esc closes it.
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

        node1 = page.locator(".react-flow__node-video").first
        node1.click(position={"x": 200, "y": 100})
        page.wait_for_timeout(600)
        page.locator(
            '.jimeng-node-toolbar button[aria-label="全屏预览"]'
        ).click()
        page.wait_for_timeout(700)

        state = page.evaluate(
            """() => {
                const d = document.querySelector('[aria-label="视频全屏预览"]');
                if (!d) return null;
                const r = d.getBoundingClientRect();
                return {
                    full: r.width >= window.innerWidth - 2 && r.height >= window.innerHeight - 2,
                    bg: getComputedStyle(d).backgroundColor,
                    time: d.textContent.includes('00:02 / 00:06'),
                    exit: !!d.querySelector('button[aria-label="退出全屏预览"]'),
                    play: !!d.querySelector('button[aria-label="全屏播放"], button[aria-label="全屏暂停"]'),
                    mute: !!d.querySelector('button[aria-label="静音"]'),
                };
            }"""
        )
        if not state:
            failures.append("fullscreen preview did not open")
        else:
            if not state["full"]:
                failures.append("preview is not full-viewport")
            if state["bg"] != "rgb(0, 0, 0)":
                failures.append(f"backdrop: {state['bg']}")
            if not state["time"]:
                failures.append("time readout missing")
            if not (state["exit"] and state["play"] and state["mute"]):
                failures.append(f"controls missing: {state}")
        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch27-fullscreen-1680.png")
        )

        page.keyboard.press("Escape")
        page.wait_for_timeout(400)
        closed = page.evaluate(
            "() => !document.querySelector('[aria-label=\"视频全屏预览\"]')"
        )
        if not closed:
            failures.append("preview did not close on Escape")

        ctx.close()

    if failures:
        print("FAIL")
        for f in failures:
            print(" -", f)
        raise SystemExit(1)
    print("PASS: jimeng batch 27 fullscreen preview contract")


if __name__ == "__main__":
    main()
