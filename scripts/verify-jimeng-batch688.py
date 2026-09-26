"""Jimeng clone batch 688 verifier — 引用参考 @ autocomplete popover.

Contract (SOURCE_FACT 2026-09-27, batch 791 deep-dive; supersedes the
batch-688 inline strip which was a CLONE_DECISION): clicking the
引用参考 chip in the empty-video-node generation panel inserts "@" into
the prompt and opens the 可能@的内容 popover — candidate section +
添加参考 section with 主体/图片/视频/音频 drill rows; clicking again
closes it.
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

        # collapse the always-on AI drawer so it stops intercepting
        # pointer events over the panel's right-side chips
        collapse = page.locator('button[aria-label="收起"]')
        if collapse.count() == 1:
            collapse.click()
            page.wait_for_timeout(400)

        # open the gen panel on the empty node
        page.locator('.react-flow__node[data-id="video-empty-1"]').click(
            position={"x": 200, "y": 100}
        )
        page.wait_for_timeout(700)

        prompt = page.locator('textarea[placeholder*="上传参考图"]')
        if prompt.count() != 1:
            failures.append("prompt textarea not found before popover open")

        # scope to the gen panel chip: only ours carries aria-pressed
        # (the AI drawer has its own 引用参考 button)
        ref_btn = page.locator('button[aria-label="引用参考"][aria-pressed]')
        if ref_btn.count() != 1:
            failures.append(f"引用参考 button count {ref_btn.count()} != 1")

        if page.locator('[data-testid="ref-menu"]').count() != 0:
            failures.append("ref popover should be closed initially")

        # toggle open
        ref_btn.click()
        page.wait_for_timeout(400)

        menu = page.locator('[data-testid="ref-menu"]')
        if menu.count() != 1:
            failures.append("ref popover did not open")
        else:
            if menu.get_by_text("可能@的内容").count() != 1:
                failures.append("可能@的内容 header missing")
            if menu.get_by_text("添加参考", exact=True).count() != 1:
                failures.append("添加参考 section header missing")
            for cat in ["主体", "图片", "视频", "音频"]:
                if menu.locator(f'button[aria-pressed]:has-text("{cat}")').count() != 1:
                    failures.append(f"category row {cat} missing")
            value = prompt.input_value()
            if not value.endswith("@"):
                failures.append(f"prompt should end with @ after toggle, got {value!r}")

        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch688-ref-strip-1680.png")
        )

        # toggle close
        ref_btn.click()
        page.wait_for_timeout(400)
        if page.locator('[data-testid="ref-menu"]').count() != 0:
            failures.append("ref popover did not close")
        if page.locator('button[aria-label="上传参考图"]').count() != 1:
            failures.append("upload tile not present after close")

        ctx.close()

    if failures:
        print("FAIL")
        for f in failures:
            print(" -", f)
        raise SystemExit(1)
    print("PASS: jimeng batch 688 reference popover contract")


if __name__ == "__main__":
    main()
