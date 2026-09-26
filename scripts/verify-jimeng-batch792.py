"""Jimeng clone batch 792 verifier — reference chip insert/remove flow.

Contract (SOURCE_FACT 2026-09-27, batch 791 deep-dive): the 可能@的内容
popover lists canvas media nodes as candidates; a category row (主体/
图片/视频/音频) drills into a submenu listing that category's nodes
(视频 rows carry a mm:ss duration badge, empty categories show
暂无相关节点); clicking a node row inserts a reference chip (48×48
thumbnail + Remove corner) into the asset row and strips the trailing
"@"; Remove deletes the chip and restores the upload tile.
"""

import base64
import os
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "docs" / "design-references" / "jimeng"
BASE_URL = os.environ.get("JIMENG_BASE_URL", "http://localhost:4317")

CANVAS_URL = f"{BASE_URL}/jimeng/canvas/demo"
VIEWPORT = {"width": 1680, "height": 826}

# 1×1 red PNG — rail upload titles the node after the file name
PNG_1PX = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4nGP4z8DwHwAFAAH/q842iQAAAABJRU5ErkJggg=="
)
UPLOAD_NAME = "batch792-ref-source.png"


def main() -> None:
    REFERENCE_DIR.mkdir(parents=True, exist_ok=True)
    failures: list[str] = []

    with sync_playwright() as p:
        ctx = p.chromium.launch(headless=True)
        page = ctx.new_page()
        page.set_viewport_size(VIEWPORT)  # type: ignore[arg-type]
        page.goto(CANVAS_URL, wait_until="domcontentloaded")
        page.wait_for_timeout(2500)

        collapse = page.locator('button[aria-label="收起"]')
        if collapse.count() == 1:
            collapse.click()
            page.wait_for_timeout(400)

        # select the empty node so the gen panel is open
        page.locator('.react-flow__node[data-id="video-empty-1"]').click(
            position={"x": 200, "y": 100}
        )
        page.wait_for_timeout(500)

        # upload a local file through the rail input (creates a media
        # node titled after the file, mock poster + 6s duration)
        page.locator('[data-testid="rail-upload-input"]').set_input_files(
            files=[{"name": UPLOAD_NAME, "mimeType": "image/png", "buffer": PNG_1PX}]
        )
        page.wait_for_timeout(800)

        ref_btn = page.locator('button[aria-label="引用参考"][aria-pressed]')
        ref_btn.click()
        page.wait_for_timeout(400)

        menu = page.locator('[data-testid="ref-menu"]')
        if menu.count() != 1:
            failures.append("ref popover did not open")
        else:
            # candidate section lists the uploaded node
            if menu.locator(f'button:has-text("{UPLOAD_NAME}")').count() < 1:
                failures.append("uploaded node missing from 可能@的内容 candidates")

        # drill into 视频 category — submenu lists the node with badge
        menu.locator('button[aria-pressed]:has-text("视频")').click()
        page.wait_for_timeout(300)
        submenu = page.locator('[data-testid="ref-submenu"]')
        if submenu.count() != 1:
            failures.append("视频 submenu did not open")
        else:
            if submenu.locator(f'button:has-text("{UPLOAD_NAME}")').count() != 1:
                failures.append("uploaded node missing from 视频 submenu")
            if submenu.get_by_text("00:06").count() < 1:
                failures.append("duration badge 00:06 missing in 视频 submenu")
            if page.locator('button[aria-label="展开视频生成器"]').count() != 1:
                failures.append("展开视频生成器 button missing in 视频 submenu")

        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch792-ref-submenu-1680.png")
        )

        # empty category: 图片 has no image-type nodes on this canvas
        menu.locator('button[aria-pressed]:has-text("图片")').click()
        page.wait_for_timeout(300)
        submenu = page.locator('[data-testid="ref-submenu"]')
        if submenu.count() != 1:
            failures.append("图片 submenu did not open")
        elif submenu.get_by_text("暂无相关节点").count() != 1:
            failures.append("图片 submenu empty state 暂无相关节点 missing")

        # pick from 视频 submenu → chip inserted, trailing @ stripped
        menu.locator('button[aria-pressed]:has-text("视频")').click()
        page.wait_for_timeout(300)
        page.locator(f'[data-testid="ref-submenu"] button:has-text("{UPLOAD_NAME}")').click()
        page.wait_for_timeout(400)

        chip_row = page.locator('[data-testid="ref-chip-row"]')
        if chip_row.count() != 1:
            failures.append("ref chip row did not appear after pick")
        else:
            chip = page.locator(f'[aria-label="Reference material: {UPLOAD_NAME}"]')
            if chip.count() != 1:
                failures.append("reference chip missing after pick")
        if page.locator('[data-testid="ref-menu"]').count() != 0:
            failures.append("ref popover should close after pick")
        value = page.locator('textarea[placeholder*="上传参考图"]').input_value()
        if value.endswith("@"):
            failures.append("trailing @ should be stripped after pick")

        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch792-ref-chip-1680.png")
        )

        # remove the chip → upload tile restored
        page.locator(f'button[aria-label="Remove {UPLOAD_NAME}"]').click()
        page.wait_for_timeout(400)
        if page.locator('[data-testid="ref-chip-row"]').count() != 0:
            failures.append("chip row should disappear after Remove")
        if page.locator('button[aria-label="上传参考图"]').count() != 1:
            failures.append("upload tile not restored after Remove")

        ctx.close()

    if failures:
        print("FAIL")
        for f in failures:
            print(" -", f)
        raise SystemExit(1)
    print("PASS: jimeng batch 792 reference chip contract")


if __name__ == "__main__":
    main()
