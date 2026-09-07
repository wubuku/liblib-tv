#!/usr/bin/env python3

"""Verify Batch 205: the type filter menu drives the asset node list.

Sampled source menu (Batch 204): ten type options. This batch wires the
menu to the list filter — selecting 图片 shows only image rows, 视频 only
video rows, 全部 restores everything. Verified on the preset canvas which
has both image and video nodes.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = (
    ROOT
    / "docs"
    / "research"
    / "liblib-canvas-batch205-2026-09-08"
    / "runtime-audit.json"
)


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool) -> None:
        assert ok, f"batch205 check failed: {name}"
        result["checks"].append(name)

    errors: list[str] = []
    page.on("pageerror", lambda error: errors.append(f"pageerror:{error}"))
    page.goto("http://localhost:4317", wait_until="networkidle")
    page.wait_for_timeout(400)

    page.get_by_role("button", name="资产管理").click()
    page.wait_for_timeout(400)
    panel = page.locator("[data-liblib-overlay='asset']")
    check("drawer:opens", panel.count() == 1)

    all_text = panel.inner_text()

    def open_menu_and_pick(label: str) -> None:
        panel.locator("[data-asset-manager-display]").click()
        page.wait_for_timeout(250)
        panel.locator(f"[data-asset-manager-type-option='{label}']").click()
        page.wait_for_timeout(300)

    # 图片 filter: image rows only (probe-verified preset content)
    open_menu_and_pick("图片")
    img_text = panel.inner_text()
    check("filter:image-shows-image", "咖啡" in img_text and "image_2026-06-15T11-22-00" in img_text)
    check("filter:image-hides-video", "分镜视频-#9" not in img_text)

    # 视频 filter: video rows only
    open_menu_and_pick("视频")
    vid_text = panel.inner_text()
    check("filter:video-shows-video", "分镜视频-#9" in vid_text)
    check("filter:video-hides-image", "image_2026-06-15T11-22-00" not in vid_text)

    # 全部 restores
    open_menu_and_pick("全部")
    all_text2 = panel.inner_text()
    check("filter:all-restores", "image_2026-06-15T11-22-00" in all_text2 and "分镜视频-#9" in all_text2)
    check("filter:trigger-label-all", panel.locator("[data-asset-manager-display]").inner_text().strip() == "展示设置")

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 205, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch205: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
