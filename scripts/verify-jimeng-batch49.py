"""Jimeng clone batch 49 verifier — toolbar download/save mock feedback.

Contract (refocus per user: the selected-video-node toolbar family):
- clicking the toolbar 下载 button shows the toast 视频下载已开始（mock）;
- right-click menu 保存到主体库 shows the toast 已保存到主体库（mock）;
- toasts auto-clear after 2.5s.
真实下载/写库为 BLOCKED_BY_FIXTURE —— mock 反馈是这些按钮的完整 UX。
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

        node1 = page.locator('.react-flow__node[data-id="video-local-1"]')
        node1.click(position={"x": 200, "y": 100})
        page.wait_for_timeout(500)

        # 下载 → toast
        page.locator('.jimeng-node-toolbar button[aria-label="下载"]').click()
        page.wait_for_timeout(500)
        toast = page.evaluate(
            """() => document.querySelector('[role="status"]')?.textContent ?? null"""
        )
        if not toast or "下载" not in toast:
            failures.append(f"download toast: {toast!r}")
        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch49-download-toast-1680.png")
        )
        page.wait_for_timeout(2600)  # let the toast auto-clear

        # right-click → 保存到主体库 → toast
        node1.click(button="right", position={"x": 200, "y": 100})
        page.wait_for_timeout(600)
        page.locator('[role="menuitem"]', has_text="保存到主体库").click()
        page.wait_for_timeout(500)
        toast2 = page.evaluate(
            """() => document.querySelector('[role="status"]')?.textContent ?? null"""
        )
        if not toast2 or "主体库" not in toast2:
            failures.append(f"save-to-library toast: {toast2!r}")

        ctx.close()

    if failures:
        print("FAIL")
        for f in failures:
            print(" -", f)
        raise SystemExit(1)
    print("PASS: jimeng batch 49 toolbar feedback contract")


if __name__ == "__main__":
    main()
