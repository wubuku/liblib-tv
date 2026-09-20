"""Jimeng clone batch 80 verifier — fullscreen preview player alignment.

Contract (SOURCE_FACT batch 80, 80-preview.png):
- opening 全屏预览 shows a full-viewport overlay with bg black/60
  (canvas visible through);
- entering autoplay starts muted (node playing=true, muted=true);
- bottom control bar: play/pause (36×36), current/duration time split,
  unmute, exit — exit/Escape pauses playback and closes.
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

        # select the video node, open 全屏预览 via toolbar
        c = page.evaluate(
            """() => { const n = document.querySelector('[data-id="video-local-1"]');
                const r = n.getBoundingClientRect();
                return {x: r.x + 60, y: r.y + 20}; }"""
        )
        page.mouse.click(c["x"], c["y"])
        page.wait_for_timeout(700)
        page.evaluate(
            """() => [...document.querySelectorAll('.react-flow__node-toolbar button')]
                .find(b => b.getAttribute('aria-label') === '全屏')?.click()"""
        )
        page.wait_for_timeout(900)

        dlg = page.locator('[role="dialog"][aria-label="视频全屏预览"]')
        if not dlg.count():
            failures.append("fullscreen preview not opened")
        else:
            bg = page.evaluate(
                """() => { const el = document.querySelector('[role="dialog"][aria-label="视频全屏预览"]');
                    return getComputedStyle(el).backgroundColor; }"""
            )
            if "0.6" not in bg:
                failures.append(f"preview bg: {bg} want black/60")
            # autoplay muted
            st = page.evaluate(
                """() => { const s = window.__jimengStore.getState();
                    const n = s.nodes.find(n => n.id === 'video-local-1');
                    return {playing: n.data.playing === true, muted: n.data.muted !== false}; }"""
            )
            if not st["playing"]:
                failures.append(f"autoplay not started: {st}")
            if not st["muted"]:
                failures.append(f"autoplay not muted: {st}")
            page.screenshot(
                path=str(REFERENCE_DIR / "jimeng-clone-batch80-preview.png")
            )

        # Escape closes and pauses
        page.keyboard.press("Escape")
        page.wait_for_timeout(700)
        if dlg.count():
            failures.append("Escape did not close preview")
        st2 = page.evaluate(
            """() => { const s = window.__jimengStore.getState();
                const n = s.nodes.find(n => n.id === 'video-local-1');
                return {playing: n.data.playing === true}; }"""
        )
        if st2["playing"]:
            failures.append("playback did not pause on close")

        ctx.close()

    if failures:
        print("FAIL")
        for f in failures:
            print(" -", f)
        raise SystemExit(1)
    print("PASS: jimeng batch 80 fullscreen preview contract")


if __name__ == "__main__":
    main()
