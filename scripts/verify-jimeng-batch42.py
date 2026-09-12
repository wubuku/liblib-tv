"""Jimeng clone batch 42 verifier — gen panel ratio/reference/duration menus.

SOURCE_FACT (batch 42): the ratio button opens a combined menu with three
groups (选择比例 21:9/16:9/4:3/1:1/3:4/9:16, 选择分辨率 720P/1080P/4K,
选择生成数量 1/2/3/4); 全能参考 toggles 首尾帧/全能参考; 时长 4s/8s/12s
(8s/12s CLONE_DECISION).
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

        # ratio/resolution/count combined menu
        page.locator('button[aria-label="比例分辨率数量"]').click()
        page.wait_for_timeout(600)
        menu = page.evaluate(
            """() => {
                const m = document.querySelector('[role="listbox"][aria-label="比例分辨率数量"]');
                if (!m) return null;
                return m.textContent.replace(/\\s+/g, ' ');
            }"""
        )
        if not menu:
            failures.append("ratio menu did not open")
        else:
            for opt in ["选择比例", "21:9", "16:9", "4:3", "1:1", "3:4", "9:16",
                        "选择分辨率", "720P", "1080P", "4K",
                        "选择生成数量", "1", "2", "3", "4"]:
                if opt not in menu:
                    failures.append(f"ratio menu missing: {opt}")

        # pick 1080P → button text updates
        page.locator('[role="option"]', has_text="1080P").click()
        page.wait_for_timeout(400)
        btn_text = page.evaluate(
            """() => document.querySelector('button[aria-label="比例分辨率数量"]')
                ?.textContent.replace(/\\s+/g, ' ')"""
        )
        if "1080P" not in (btn_text or ""):
            failures.append(f"resolution not applied: {btn_text!r}")
        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch42-ratio-menu-1680.png")
        )

        # reference toggle
        page.locator('button[aria-label="参考模式"]').click()
        page.wait_for_timeout(500)
        page.locator('[role="option"]', has_text="首尾帧").click()
        page.wait_for_timeout(400)
        ref_text = page.evaluate(
            """() => document.querySelector('button[aria-label="参考模式"]')
                ?.textContent.trim()"""
        )
        if ref_text != "首尾帧":
            failures.append(f"reference toggle: {ref_text!r}")

        # duration menu
        page.locator('button[aria-label="时长"]').click()
        page.wait_for_timeout(500)
        page.locator('[role="option"]', has_text="8s").click()
        page.wait_for_timeout(400)
        dur_text = page.evaluate(
            """() => document.querySelector('button[aria-label="时长"]')
                ?.textContent.trim()"""
        )
        if dur_text != "8s":
            failures.append(f"duration: {dur_text!r} (want 8s)")
        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch42-duration-1680.png")
        )

        ctx.close()

    if failures:
        print("FAIL")
        for f in failures:
            print(" -", f)
        raise SystemExit(1)
    print("PASS: jimeng batch 42 gen panel menus contract")


if __name__ == "__main__":
    main()
