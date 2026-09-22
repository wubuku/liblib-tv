"""Jimeng clone batch 8 verifier — 提示词反推 → AI drawer flow (batch 216).

Contract (updated per 216-source-infer.png): clicking 提示词反推 no longer
opens a mock panel — the node zooms in and the AI drawer opens with the
prefilled 视频反解 prompt「用 视频反解 反推出 {video title} 的提示词，并
创建文本节点，方便我拉片复刻」. Marked CLONE_DECISION where the drawer
mock does not submit anything.
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

        node1 = page.locator(".react-flow__node-video").first
        node1.click(position={"x": 200, "y": 100})
        page.wait_for_timeout(700)
        # Batch 484 SOURCE_FACT: 提示词反推 moved into 工具 dropdown
        page.locator(".jimeng-node-toolbar button", has_text="工具").click()
        page.wait_for_timeout(400)
        page.locator(".jimeng-node-toolbar button", has_text="提示词反推").click()
        page.wait_for_timeout(900)

        state = page.evaluate(
            """() => {
                const drawer = document.querySelector('aside[aria-label="AI 对话"]');
                const input = drawer?.querySelector('input');
                return {
                    drawerOpen: !!drawer,
                    prefill: input ? input.value : null,
                    noMockPanel: ![...document.querySelectorAll('form,div')]
                        .some(d => d.textContent.includes('mock 反推结果')),
                };
            }"""
        )
        if not state["drawerOpen"]:
            failures.append("AI drawer did not open on 提示词反推")
        else:
            if not state["prefill"] or "用 视频反解 反推出" not in state["prefill"]:
                failures.append(f"drawer prefill wrong: {state['prefill']!r}")
            if not state["noMockPanel"]:
                failures.append("old mock infer panel must stay removed")
        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch8-infer-panel-1680.png")
        )

        # Batch 398 SOURCE_FACT: Agent 面板常驻——Escape 不关闭面板
        page.keyboard.press("Escape")
        page.wait_for_timeout(500)
        still_open = page.evaluate(
            "() => !!document.querySelector('aside[aria-label=\"AI 对话\"]')"
        )
        if not still_open:
            failures.append("persistent AI drawer should stay open on Escape")

        ctx.close()

    if failures:
        print("FAIL")
        for f in failures:
            print(" -", f)
        raise SystemExit(1)
    print("PASS: jimeng batch 8 infer → AI drawer contract")


if __name__ == "__main__":
    main()
