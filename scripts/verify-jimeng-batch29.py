"""Jimeng clone batch 29 verifier — project rename + card mute toggle.

Contract:
- clicking the top-bar project name turns it into an inline input; Enter
  commits via the store (top bar shows the new name); Escape cancels.
- the video card mute button toggles 静音/取消静音 (default muted,
  SOURCE_FACT card shows the muted icon).
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

        # ── project rename ──
        page.locator("header button", has_text="测试项目").click()
        page.wait_for_timeout(400)
        inp = page.locator('input[aria-label="项目名"]')
        if inp.count() != 1:
            failures.append("inline rename input did not appear")
        else:
            page.keyboard.press("Escape")  # cancel first
            page.wait_for_timeout(200)
            page.locator("header button", has_text="测试项目").click()
            page.wait_for_timeout(300)
            inp.fill("春季短片项目")
            page.keyboard.press("Enter")
            page.wait_for_timeout(500)
            renamed = page.evaluate(
                "() => document.querySelector('header').textContent.includes('春季短片项目')"
            )
            if not renamed:
                failures.append("project rename did not commit")
        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch29-rename-1680.png")
        )

        # ── card mute toggle ──
        node1 = page.locator(".react-flow__node-video").first
        node1.hover(position={"x": 200, "y": 100})
        page.wait_for_timeout(400)
        # default muted (SOURCE_FACT: card shows the muted icon);
        # 按钮标签描述动作: muted 时动作 = 取消静音
        mute0 = page.locator(
            '.react-flow__node-video button[aria-label="取消静音"] svg.lucide-volume-x'
        ).count()
        node1.locator('button[aria-label="取消静音"]').click()
        page.wait_for_timeout(400)
        unmute = page.locator(
            '.react-flow__node-video button[aria-label="静音"] svg.lucide-volume-2'
        ).count()
        if mute0 < 1:
            failures.append("default mute icon missing (should be volume-x)")
        if unmute < 1:
            failures.append("mute toggle did not switch icon to volume-2")
        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch29-mute-1680.png")
        )

        ctx.close()

    if failures:
        print("FAIL")
        for f in failures:
            print(" -", f)
        raise SystemExit(1)
    print("PASS: jimeng batch 29 rename + mute contract")


if __name__ == "__main__":
    main()
