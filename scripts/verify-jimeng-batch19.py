"""Jimeng clone batch 19 verifier — audio node mock.

Contract: rail 音频 inserts an audio node (.react-flow__node-audio) with
waveform bars and a 00:15 duration label; the node carries the video-family
skeleton (title row + handles).
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
        page.wait_for_timeout(2200)

        page.locator('aside button[aria-label="音频"]').click()
        page.wait_for_timeout(800)

        state = page.evaluate(
            """() => {
                const n = document.querySelector('.react-flow__node-audio');
                if (!n) return null;
                const r = n.getBoundingClientRect();
                return {
                    title: n.textContent.includes('音频'),
                    bars: n.querySelectorAll('.flex.items-center.gap-1 > span.rounded-full').length,
                    handles: n.querySelectorAll('.react-flow__handle').length,
                    w: Math.round(r.width),
                    h: Math.round(r.height),
                    selected: n.classList.contains('selected'),
                    genPanel: [...document.querySelectorAll('form')]
                        .some(f => f.textContent.includes('请输入你想生成')),
                };
            }"""
        )
        if not state:
            failures.append("audio node did not appear")
        else:
            if not state["title"]:
                failures.append("audio title missing")
            # 批 239: 居中 5 柱波形图标 (旧横条播放器已按源站实测移除)
            if state["bars"] != 5:
                failures.append(f"waveform glyph bars: {state['bars']} != 5")
            if state["handles"] < 2:
                failures.append("handles missing")
            # 批 236: 世界 368×368 (0.7299 缩放下 ~269)
            if abs(state["w"] - 269) > 10 or abs(state["h"] - 269) > 10:
                failures.append(f"audio card size: {state['w']}x{state['h']} want ~269")
            if not state["selected"]:
                failures.append("inserted audio node should be selected")
            if not state["genPanel"]:
                failures.append("audio gen panel missing when selected")
        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch19-audio-node-1680.png")
        )

        ctx.close()

    if failures:
        print("FAIL")
        for f in failures:
            print(" -", f)
        raise SystemExit(1)
    print("PASS: jimeng batch 19 audio node contract")


if __name__ == "__main__":
    main()
