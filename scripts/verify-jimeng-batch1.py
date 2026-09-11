"""Jimeng clone batch 1 verifier.

Requires the dev server on http://localhost:4317 (or JIMENG_BASE_URL).
Captures the /jimeng/canvas/demo workspace and asserts the batch 1 contract:
chrome layout, mock nodes, dot grid canvas, zoom readout.
Screenshots land in docs/design-references/jimeng/ for auditability.
"""

import os
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "docs" / "design-references" / "jimeng"
BASE_URL = os.environ.get("JIMENG_BASE_URL", "http://localhost:4317")

CANVAS_URL = f"{BASE_URL}/jimeng/canvas/demo"
VIEWPORT = {"width": 1680, "height": 826}  # 与源站提取时的 viewport 一致


def main() -> None:
    REFERENCE_DIR.mkdir(parents=True, exist_ok=True)
    failures: list[str] = []

    with sync_playwright() as p:
        ctx = p.chromium.launch(headless=True)
        page = ctx.new_page()
        page.set_viewport_size(VIEWPORT)  # type: ignore[arg-type]
        page.goto(CANVAS_URL, wait_until="domcontentloaded")
        page.wait_for_timeout(2500)

        # 合同断言 ── Batch 1
        checks = page.evaluate(
            """() => ({
                flow: !!document.querySelector('.jimeng-canvas .react-flow'),
                videoNodes: document.querySelectorAll('.react-flow__node-video').length,
                topBar: !!document.querySelector('header'),
                toolRailButtons: document.querySelectorAll('aside button').length,
                bottomDock: !!document.querySelector('.jimeng-bottom-dock'),
                aiButton: [...document.querySelectorAll('button')].some(b => b.textContent.includes('与 AI 对话')),
                zoomText: document.querySelector('.jimeng-bottom-dock')?.textContent.match(/\\d+%/)?.[0] ?? null,
                bodyBg: getComputedStyle(document.querySelector('.jimeng-canvas')).backgroundColor,
                paneGrid: getComputedStyle(document.querySelector('.react-flow__pane')).backgroundImage.includes('radial-gradient'),
            })"""
        )
        expect = {
            "flow": True,
            "videoNodes": 2,
            "topBar": True,
            "toolRailButtons": 9,
            "bottomDock": True,
            "aiButton": True,
            "zoomText": "73%",
            "bodyBg": "rgb(13, 13, 13)",
            "paneGrid": True,
        }
        for key, want in expect.items():
            got = checks.get(key)
            if got != want:
                failures.append(f"{key}: want {want!r}, got {got!r}")

        page.screenshot(path=str(REFERENCE_DIR / "jimeng-clone-batch1-default-1680.png"))
        ctx.close()

    if failures:
        print("FAIL")
        for f in failures:
            print(" -", f)
        raise SystemExit(1)
    print("PASS: jimeng batch 1 contract")
    print(f"screenshot: {REFERENCE_DIR / 'jimeng-clone-batch1-default-1680.png'}")


if __name__ == "__main__":
    main()
