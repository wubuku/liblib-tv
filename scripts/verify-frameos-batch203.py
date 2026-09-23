#!/usr/bin/env python3

"""Verify Batch 203: FrameOS image node replace button works end-to-end.

The 替换内容 button now opens a file picker and swaps the node image via an
object URL (prototype behavior — no backend). Uses Playwright's filechooser
event with a generated 1x1 PNG. Verifies the node's <img> source changes
and the swap is undoable.
"""

from __future__ import annotations

import base64
import json
import os
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
BASE_URL = os.environ.get("LIBLIB_BASE_URL", "http://localhost:4317")
AUDIT_PATH = (
    ROOT
    / "docs"
    / "research"
    / "liblib-frameos-batch203-2026-09-24"
    / "runtime-audit.json"
)

# 1x1 red PNG
PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4nGP4z8DwHwAFAAH/q842iQAAAABJRU5ErkJggg=="
)


def attach_errors(page: Page) -> list[str]:
    errors: list[str] = []
    page.on(
        "console",
        lambda message: errors.append(f"console:{message.type}:{message.text}")
        if message.type == "error"
        else None,
    )
    page.on("pageerror", lambda error: errors.append(f"pageerror:{error}"))
    return errors


def run_desktop(page: Page, png_path: Path) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool) -> None:
        assert ok, f"batch203 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/frameos/canvas/demo", wait_until="domcontentloaded")
    page.wait_for_timeout(1200)

    image_node = page.locator(".react-flow__node-image").first
    image_node.click(position={"x": 60, "y": 30})
    page.wait_for_timeout(400)

    src_before = image_node.locator("img").first.get_attribute("src")

    # 触发替换按钮 → filechooser → 选择生成的 PNG
    with page.expect_file_chooser() as fc_info:
        image_node.locator("button[aria-label='替换内容']").click(force=True)
    fc_info.value.set_files(str(png_path))
    page.wait_for_timeout(700)

    src_after = image_node.locator("img").first.get_attribute("src")
    check("replace:src-changed", src_before != src_after)
    check(
        "replace:object-url",
        (src_after or "").startswith("blob:"),
    )

    # 撤销 → 恢复原图
    page.keyboard.press("Meta+z")
    page.wait_for_timeout(500)
    src_undo = image_node.locator("img").first.get_attribute("src")
    check("undo:restores-image", src_undo == src_before)

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 203, "results": []}
    png_path = AUDIT_PATH.parent / "fixture-1x1.png"
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    png_path.write_bytes(PNG_1X1)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page, png_path))
        browser.close()
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch203: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
