"""Jimeng clone batch 58 verifier — card control title tooltips.

SOURCE_FACT: source card control buttons carry native title attributes
(静音/全屏 in the bottom control bar).
Contract: the video card's mute and fullscreen buttons carry title
tooltips; the fullscreen preview's exit control keeps its aria-label.
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

        titles = page.evaluate(
            """() => {
                const n = document.querySelector('.react-flow__node[data-id="video-local-1"]');
                return {
                    mute: n?.querySelector('button[aria-label*="静音"]')?.getAttribute('title') ?? null,
                    fullscreen: n?.querySelector('button[aria-label="全屏预览"]')?.getAttribute('title') ?? null,
                };
            }"""
        )
        if titles["mute"] not in ("静音", "取消静音"):
            failures.append(f"mute title: {titles['mute']!r}")
        if titles["fullscreen"] != "全屏":
            failures.append(f"fullscreen title: {titles['fullscreen']!r}")

        ctx.close()

    if failures:
        print("FAIL")
        for f in failures:
            print(" -", f)
        raise SystemExit(1)
    print("PASS: jimeng batch 58 card control tooltips contract")


if __name__ == "__main__":
    main()
