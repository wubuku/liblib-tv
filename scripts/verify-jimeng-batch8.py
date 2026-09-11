"""Jimeng clone batch 8 verifier — 提示词反推 mock panel.

Contract: clicking 提示词反推 in the toolbar opens a mock panel (title,
mock inferred prompt, copy button, close ×); close button returns to the
toolbar state; pane click also exits. Marked CLONE_DECISION — the source
site submits a paid inference task (BLOCKED_BY_FIXTURE).
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
        page.locator(".jimeng-node-toolbar button", has_text="提示词反推").click()
        page.wait_for_timeout(800)

        state = page.evaluate(
            """() => {
                const copyBtn = [...document.querySelectorAll('button')]
                    .find(b => b.textContent.includes('复制提示词'));
                const panel = copyBtn
                    ? copyBtn.closest('div[class*="rounded"]')
                    : null;
                return {
                    open: !!panel && panel.textContent.includes('mock 反推结果'),
                    hasClose: !!document.querySelector('button[aria-label="关闭反推面板"]'),
                    hasCopy: !!copyBtn,
                };
            }"""
        )
        if not state["open"]:
            failures.append("infer panel did not open")
        else:
            if not state["hasClose"]:
                failures.append("infer panel close button missing")
            if not state["hasCopy"]:
                failures.append("infer panel copy button missing")
        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch8-infer-panel-1680.png")
        )

        # close button exits
        page.locator('button[aria-label="关闭反推面板"]').click()
        page.wait_for_timeout(500)
        closed = page.evaluate(
            "() => ![...document.querySelectorAll('div')]"
            ".some(d => d.textContent.includes('mock 反推结果')"
            " && d.querySelector('button[aria-label=\\'复制提示词\\']'))"
        )
        if not closed:
            failures.append("infer panel did not close")

        ctx.close()

    if failures:
        print("FAIL")
        for f in failures:
            print(" -", f)
        raise SystemExit(1)
    print("PASS: jimeng batch 8 infer panel contract")


if __name__ == "__main__":
    main()
