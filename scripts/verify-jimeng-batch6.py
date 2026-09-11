"""Jimeng clone batch 6 verifier — 视频编辑 (video edit) mode.

Contract: selecting the media node and clicking 视频编辑 enters edit mode —
title hidden, edit tool pill with 8 tools, edit prompt bar with placeholder
描述你如何调整视频, credits 120/260, disabled send; pane click exits.
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
        page.locator(".jimeng-node-toolbar button", has_text="视频编辑").click()
        page.wait_for_timeout(900)

        state = page.evaluate(
            """() => {
                const bar = [...document.querySelectorAll('form')]
                    .find(f => f.textContent.includes('描述你如何调整视频'));
                if (!bar) return {open: false};
                const tools = [...document.querySelectorAll('button[aria-label]')]
                    .map(b => b.getAttribute('aria-label'));
                const want = ['框选','套索','箭头','文字','橡皮擦','定位','撤销','重做'];
                const send = bar.querySelector('button[aria-label="生成"]');
                return {
                    open: true,
                    tools: want.filter(w => tools.includes(w)),
                    placeholder: bar.textContent.includes('描述你如何调整视频'),
                    credits: bar.textContent.includes('120') && bar.textContent.includes('260'),
                    sendDisabled: send ? send.disabled : null,
                };
            }"""
        )
        if not state.get("open"):
            failures.append("video edit mode did not open")
        else:
            if len(state["tools"]) != 8:
                failures.append(f"edit tools missing: {state['tools']}")
            if not state["placeholder"]:
                failures.append("edit prompt placeholder missing")
            if not state["credits"]:
                failures.append("credits 120/260 missing")
            if state["sendDisabled"] is not True:
                failures.append("send button should be disabled")
        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch6-video-edit-mode-1680.png")
        )

        # pane click exits
        page.mouse.click(300, 700)
        page.wait_for_timeout(600)
        exited = page.evaluate(
            "() => ![...document.querySelectorAll('form')]"
            ".some(f => f.textContent.includes('描述你如何调整视频'))"
        )
        if not exited:
            failures.append("edit mode did not exit on pane click")

        ctx.close()

    if failures:
        print("FAIL")
        for f in failures:
            print(" -", f)
        raise SystemExit(1)
    print("PASS: jimeng batch 6 video edit mode contract")
    print(f"screenshot: {REFERENCE_DIR / 'jimeng-clone-batch6-video-edit-mode-1680.png'}")


if __name__ == "__main__":
    main()
