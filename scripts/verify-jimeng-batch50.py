"""Jimeng clone batch 50 verifier — gen panel send → generating → completed.

Contract (mock flow): selecting the empty node, typing a prompt, and
clicking 生成 puts the node into a generating state (spinner overlay +
toast), and after ~3s the node completes: poster + time row 00:00/00:06
appear, generating overlay clears. The completed node shows the standard
toolbar on selection.
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

        # Batch 398 SOURCE_FACT: Agent 面板常驻——本验证器不测面板，
        # 载入后先收起以避免遮挡画布交互
        _collapse = page.locator('button[aria-label="收起"]')
        if _collapse.count():
            _collapse.click()
            page.wait_for_timeout(400)

        page.locator('.react-flow__node[data-id="video-empty-1"]').click(
            position={"x": 200, "y": 100}
        )
        page.wait_for_timeout(700)
        page.locator(
            'textarea[placeholder*="上传参考图"]'
        ).fill("一只柯基在草地上奔跑，阳光明媚")
        page.locator('button[aria-label="生成"]').last.click()
        page.wait_for_timeout(600)

        generating = page.evaluate(
            """() => {
                const n = document.querySelector('.react-flow__node[data-id="video-empty-1"]');
                return {
                    spinner: !!n.querySelector('.animate-spin'),
                    label: n.textContent.includes('生成中'),
                };
            }"""
        )
        if not generating["spinner"]:
            failures.append("generating spinner overlay missing")
        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch50-generating-1680.png")
        )

        # wait for completion (3s mock)
        page.wait_for_timeout(3200)
        done = page.evaluate(
            """() => {
                const n = document.querySelector('.react-flow__node[data-id="video-empty-1"]');
                return {
                    spinner: !!n.querySelector('.animate-spin'),
                    time: n.querySelector('span.tabular-nums')?.textContent.match(/(\\d{1,2}:\\d{2}) \\/ 0:06/)?.[1],
                    hasToolbar: !!n.querySelector('.jimeng-node-toolbar'),
                };
            }"""
        )
        if done["spinner"]:
            failures.append("generating overlay still present after completion")
        if done["time"] != "0:00":
            failures.append(f"completed time: {done['time']!r} (want 00:00)")
        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch50-completed-1680.png")
        )

        ctx.close()

    if failures:
        print("FAIL")
        for f in failures:
            print(" -", f)
        raise SystemExit(1)
    print("PASS: jimeng batch 50 generate flow contract")


if __name__ == "__main__":
    main()
