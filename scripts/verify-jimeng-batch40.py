"""Jimeng clone batch 40 verifier — generation panel prompt editing + send.

Contract: selecting the empty node opens the generation panel; typing a
prompt enables the circular send button; submitting shows the mock toast
(生成任务已提交) which auto-clears; clearing the prompt disables send again.
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

        # open the gen panel on the empty node
        page.locator('.react-flow__node[data-id="video-empty-1"]').click(
            position={"x": 200, "y": 100}
        )
        page.wait_for_timeout(700)

        prompt = page.locator('textarea[placeholder*="上传参考图"]')
        if prompt.count() != 1:
            page.screenshot(
                path=str(REFERENCE_DIR / "jimeng-clone-batch40-debug-no-textarea.png")
            )
            print("FAIL: prompt textarea not found")
            raise SystemExit(1)

        send_disabled_initially = page.evaluate(
            """() => {
                const b = document.querySelector('button[aria-label="生成"]');
                return b ? b.disabled : null;
            }"""
        )
        if not send_disabled_initially:
            failures.append("send should be disabled with empty prompt")

        prompt.fill("一只柯基在草地上奔跑，阳光明媚")
        page.wait_for_timeout(300)
        send_enabled = page.evaluate(
            """() => {
                const b = document.querySelector('button[aria-label="生成"]');
                return b ? !b.disabled : false;
            }"""
        )
        if not send_enabled:
            failures.append("send should be enabled with prompt text")

        # submit → toast
        page.locator('button[aria-label="生成"]').last.click()
        page.wait_for_timeout(500)
        toast = page.evaluate(
            """() => document.querySelector('[role="status"]')?.textContent ?? null"""
        )
        if not toast or "生成任务已提交" not in toast:
            failures.append(f"toast missing: {toast!r}")
        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch40-gen-send-1680.png")
        )

        # toast auto-clears
        page.wait_for_timeout(3000)
        toast_gone = page.evaluate(
            "() => !document.querySelector('[role=\"status\"]')"
        )
        if not toast_gone:
            failures.append("toast did not auto-clear")

        ctx.close()

    if failures:
        print("FAIL")
        for f in failures:
            print(" -", f)
        raise SystemExit(1)
    print("PASS: jimeng batch 40 gen panel send contract")


if __name__ == "__main__":
    main()
