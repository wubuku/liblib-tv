#!/usr/bin/env python3

"""Verify Batch 180: attempt chip icons use source iconify glyphs.

Source evidence (2026-09-08 CDP, source-chip-icons.json): the three attempt
chips lead with 14x14 iconify (libtv set) SVGs whose viewBoxes are
`0 0 16 16` (5分钟超长视频), `0 0 20.05 22` (首尾帧生成视频) and `0 0 22 22`
(首帧生成视频); the clone now embeds the harvested path data verbatim.
"""

from __future__ import annotations

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
    / "liblib-canvas-batch180-2026-09-08"
    / "runtime-audit.json"
)

EXPECTED_VIEWBOXES = {
    "5分钟超长视频": "0 0 16 16",
    "首尾帧生成视频": "0 0 20.05 22",
    "首帧生成视频": "0 0 22 22",
}


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


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool) -> None:
        assert ok, f"batch180 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(BASE_URL, wait_until="networkidle")
    page.wait_for_timeout(500)

    page.get_by_role("button", name="添加节点").click()
    page.wait_for_timeout(300)
    page.locator("[data-liblib-overlay='add-node']").get_by_role("button", name="视频", exact=True).click()
    page.wait_for_timeout(1000)

    for label, viewbox in EXPECTED_VIEWBOXES.items():
        svg = page.locator(f"[data-video-attempt='{label}'] svg").first
        check(f"icon:{label}:viewbox", svg.get_attribute("viewBox") == viewbox)
        d = svg.locator("path").first.get_attribute("d") or ""
        check(f"icon:{label}:path-harvested", len(d) > 40)

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 180, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch180: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
