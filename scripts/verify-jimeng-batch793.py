"""Jimeng clone batch 793 verifier — 添加参考 three-option menu + canvas picking.

Contract (SOURCE_FACT 2026-09-27, batch 791 deep-dive): the chip-row
添加参考 button opens a three-option menu — 上传参考内容 (file upload
via panel input) / 从资产库添加 (opens the assets modal) / 从画布选择
(canvas picking mode: blue inset ring on the canvas + top pill banner
「从画布选择 ×」); clicking a canvas node in picking mode inserts it as
a reference chip and shows the 添加完成 toast.
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

PNG_1PX = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4nGP4z8DwHwAFAAH/q842iQAAAABJRU5ErkJggg=="
)
UPLOAD_NAME = "batch793-ref-source.png"


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

        # open the gen panel + create a chip via the ref popover so the
        # chip row (with 添加参考) is visible
        page.locator('.react-flow__node[data-id="video-empty-1"]').click(
            position={"x": 200, "y": 100}
        )
        page.wait_for_timeout(500)
        page.locator('[data-testid="rail-upload-input"]').set_input_files(
            files=[{"name": UPLOAD_NAME, "mimeType": "image/png", "buffer": PNG_1PX}]
        )
        page.wait_for_timeout(800)
        page.locator('button[aria-label="引用参考"][aria-pressed]').click()
        page.wait_for_timeout(300)
        page.locator('[data-testid="ref-menu"] button[aria-pressed]:has-text("视频")').click()
        page.wait_for_timeout(300)
        page.locator(f'[data-testid="ref-submenu"] button:has-text("{UPLOAD_NAME}")').click()
        page.wait_for_timeout(400)

        add_ref = page.locator('button[aria-label="添加参考"]')
        if add_ref.count() != 1:
            failures.append(f"添加参考 button count {add_ref.count()} != 1")
        if page.locator('[data-testid="addref-menu"]').count() != 0:
            failures.append("addref menu should be closed initially")

        # open the three-option menu
        add_ref.click()
        page.wait_for_timeout(400)
        menu = page.locator('[data-testid="addref-menu"]')
        if menu.count() != 1:
            failures.append("addref menu did not open")
        else:
            for label in ["上传参考内容", "从资产库添加", "从画布选择"]:
                if menu.locator(f'button:has-text("{label}")').count() != 1:
                    failures.append(f"addref option {label} missing")

        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch793-addref-menu-1680.png")
        )

        # 从资产库添加 → assets modal; its own 关闭 button closes it
        # (Escape would deselect the node and unmount the panel)
        menu.locator('button:has-text("从资产库添加")').click()
        page.wait_for_timeout(500)
        if page.locator('[data-testid="jimeng-assets-modal"]').count() != 1:
            failures.append("assets modal did not open from 从资产库添加")
        page.locator('[data-testid="assets-close"]').click()
        page.wait_for_timeout(400)
        if page.locator('[data-testid="jimeng-assets-modal"]').count() != 0:
            failures.append("assets modal did not close")

        # 上传参考内容 → panel file input works (adds a node)
        nodes_before = page.locator(".react-flow__node").count()
        add_ref.click()
        page.wait_for_timeout(300)
        page.locator('[data-testid="panel-upload-input"]').set_input_files(
            files=[{"name": "batch793-uploaded.png", "mimeType": "image/png", "buffer": PNG_1PX}]
        )
        page.wait_for_timeout(800)
        nodes_after = page.locator(".react-flow__node").count()
        if nodes_after != nodes_before + 1:
            failures.append(f"panel upload node count {nodes_before} -> {nodes_after}")
        # the menu is still open from the upload step; close it so the
        # next 添加参考 click opens fresh
        add_ref.click()
        page.wait_for_timeout(300)
        if page.locator('[data-testid="addref-menu"]').count() != 0:
            failures.append("addref menu did not close after second toggle")

        # 从画布选择 → picking mode: banner + blue ring; Escape cancels
        add_ref.click()
        page.wait_for_timeout(300)
        menu.locator('button:has-text("从画布选择")').click()
        page.wait_for_timeout(400)
        banner = page.locator('[data-testid="canvas-pick-banner"]')
        if banner.count() != 1:
            failures.append("canvas pick banner missing")
        else:
            if banner.get_by_text("从画布选择").count() != 1:
                failures.append("banner text 从画布选择 missing")
            if page.locator('button[aria-label="取消从画布选择"]').count() != 1:
                failures.append("banner cancel button missing")
        canvas_cls = page.evaluate(
            """() => document.querySelector('.jimeng-canvas')?.className ?? ''"""
        )
        if "ring-[#0A5CD6]" not in canvas_cls:
            failures.append(f"canvas picking ring missing, cls={canvas_cls!r}")

        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch793-canvas-picking-1680.png")
        )

        # cancel picking via the banner's own button (Escape would
        # deselect the node and unmount the panel)
        page.locator('button[aria-label="取消从画布选择"]').click()
        page.wait_for_timeout(400)
        if page.locator('[data-testid="canvas-pick-banner"]').count() != 0:
            failures.append("picking mode did not cancel via banner button")

        # pick a node: re-enter picking, click 视频 1 (the empty node)
        add_ref.click()
        page.wait_for_timeout(300)
        menu.locator('button:has-text("从画布选择")').click()
        page.wait_for_timeout(400)
        page.locator('.react-flow__node[data-id="video-empty-1"]').click(
            position={"x": 200, "y": 100}
        )
        page.wait_for_timeout(600)
        if page.locator('[data-testid="canvas-pick-banner"]').count() != 0:
            failures.append("picking mode did not exit after node pick")
        chip = page.locator('[aria-label="Reference material: 视频 1"]')
        if chip.count() != 1:
            failures.append(f"picked-node chip count {chip.count()} != 1")

        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch793-picked-chip-1680.png")
        )

        ctx.close()

    if failures:
        print("FAIL")
        for f in failures:
            print(" -", f)
        raise SystemExit(1)
    print("PASS: jimeng batch 793 addref menu + canvas picking contract")


if __name__ == "__main__":
    main()
