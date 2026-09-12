"""Jimeng clone batch 9 verifier — 截取帧自定义 frame picker.

Contract: from the toolbar 截取帧 dropdown, picking 自定义 opens the frame
picker (filmstrip + playhead, time row, 截取帧 capture button, disabled 确认);
clicking 截取帧 enables 确认; 确认 closes the picker.
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
        page.locator(".jimeng-node-toolbar button", has_text="截取帧").click()
        page.wait_for_timeout(500)
        page.locator("button", has_text="自定义").click()
        page.wait_for_timeout(800)

        state = page.evaluate(
            """() => {
                const confirm = [...document.querySelectorAll('button')]
                    .find(b => b.textContent.trim() === '确认');
                if (!confirm) return {open: false};
                const capture = [...document.querySelectorAll('button')]
                    .find(b => b.textContent.includes('截取帧'));
                const time = document.body.innerText.includes('00:00 / 00:06');
                return {
                    open: true,
                    confirmDisabled: confirm.disabled,
                    hasCapture: !!capture,
                    timeRow: time,
                };
            }"""
        )
        if not state["open"]:
            failures.append("frame picker did not open")
        else:
            if not state["confirmDisabled"]:
                failures.append("确认 should be disabled before capture")
            if not state["hasCapture"]:
                failures.append("截取帧 capture button missing")
            if not state["timeRow"]:
                failures.append("time row 00:00 / 00:06 missing")
        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch9-frame-picker-1680.png")
        )

        page.locator("button", has_text="截取帧").click()
        page.wait_for_timeout(500)
        confirm_enabled = page.evaluate(
            """() => {
                const confirm = [...document.querySelectorAll('button')]
                    .find(b => b.textContent.trim() === '确认');
                return confirm ? !confirm.disabled : false;
            }"""
        )
        if not confirm_enabled:
            failures.append("确认 still disabled after capture")
        page.locator("button", has_text="确认").click()
        page.wait_for_timeout(500)
        closed = page.evaluate(
            "() => ![...document.querySelectorAll('button')]"
            ".some(b => b.textContent.trim() === '确认')"
        )
        if not closed:
            failures.append("frame picker did not close on 确认")

        ctx.close()

    if failures:
        print("FAIL")
        for f in failures:
            print(" -", f)
        raise SystemExit(1)
    print("PASS: jimeng batch 9 frame picker contract")


if __name__ == "__main__":
    main()
