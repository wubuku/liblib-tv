"""Jimeng clone batch 51 verifier — generated node toolbar behavior.

Contract: after the generation flow completes, selecting the new node shows
the full selection toolbar (7 items + divider + fullscreen/download), the
title row carries the Tag icon (media marker), and the gen panel no longer
renders (the node is now a content node). ⌘Z on the generation completion
restores the empty placeholder (generateInto completion is a history
mutation via applyTrim-style data write — mock scope: completion is not in
history, so ⌘Z does not revert it; documented).
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

        page.locator('.react-flow__node[data-id="video-empty-1"]').click(
            position={"x": 200, "y": 100}
        )
        page.wait_for_timeout(700)
        page.locator(
            'textarea[placeholder*="上传参考图"]'
        ).fill("一只柯基在草地上奔跑，阳光明媚")
        page.locator('button[aria-label="生成"]').last.click()
        page.wait_for_timeout(3600)  # 3s mock completion

        # select the generated node
        page.locator('.react-flow__node[data-id="video-empty-1"]').click(
            position={"x": 200, "y": 100}
        )
        page.wait_for_timeout(700)

        state = page.evaluate(
            """() => {
                const tb = [...document.querySelectorAll('.jimeng-node-toolbar')]
                    .find(t => t.textContent.includes('局部重拍'));
                const labels = ['局部重拍','智能超清','视频编辑','截取帧','补帧','视频修剪','提示词反推'];
                const missing = labels.filter(l => !tb || !tb.textContent.includes(l));
                const genPanel = [...document.querySelectorAll('form')].some(f =>
                    f.textContent.includes('上传参考图') && f.textContent.includes('即梦 Seedance'));
                const node = document.querySelector('.react-flow__node[data-id="video-empty-1"]');
                const hasTagIcon = !!node?.querySelector('button[aria-label="节点颜色标记"]');
                const time = node?.textContent.match(/(\\d\\d:\\d\\d) \\/ (\\d\\d:\\d\\d)/);
                return {
                    toolbar: !!tb,
                    missing,
                    divider: !!tb?.querySelector('.jimeng-node-toolbar-divider'),
                    genPanelGone: !genPanel,
                    tagIcon: hasTagIcon,
                    nodeSelected: node?.classList.contains('selected'),
                    time: time ? `${time[1]} / ${time[2]}` : null,
                };
            }"""
        )
        if not state["toolbar"]:
            failures.append("generated node toolbar did not appear on select")
        else:
            if state["missing"]:
                failures.append(f"toolbar items missing: {state['missing']}")
            if not state["divider"]:
                failures.append("toolbar divider missing")
            if not state["tagIcon"]:
                failures.append("color tag icon missing on generated node")
            if not state["genPanelGone"]:
                failures.append("gen panel still visible on generated node")
            if not state["nodeSelected"]:
                failures.append("generated node not selected")
        if state["time"] != "00:00 / 00:06":
            failures.append(f"time row: {state['time']!r}")
        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch51-generated-toolbar-1680.png")
        )

        ctx.close()

    if failures:
        print("FAIL")
        for f in failures:
            print(" -", f)
        raise SystemExit(1)
    print("PASS: jimeng batch 51 generated node toolbar contract")


if __name__ == "__main__":
    main()
