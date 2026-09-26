#!/usr/bin/env python3

"""Verify Batch 204: FrameOS content-image hover mask + scale.

BEHAVIORS-documented visual (original sampling): hovering an image node
with content shows a dim mask and scales the card 1.02. Empty image nodes
have no hover UI (Batch 172). Verifies the mask element appears on hover
of a content node and disappears on leave.
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
    / "liblib-frameos-batch204-2026-09-24"
    / "runtime-audit.json"
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
    page.on("dialog", lambda d: d.dismiss())
    return errors


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool) -> None:
        assert ok, f"batch204 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/frameos/canvas/demo", wait_until="domcontentloaded", timeout=90000)
    page.wait_for_timeout(1200)

    image_node = page.locator(".react-flow__node-image").first
    check("boot:content-image", image_node.count() == 1)

    # hover 内容图片 → 蒙层出现
    image_node.hover()
    page.wait_for_timeout(400)
    mask = page.locator("[data-frameos-image-hover-mask]")
    check("hover:mask-appears", mask.count() == 1)

    # 移出 → 蒙层消失
    page.mouse.move(200, 600)
    page.wait_for_timeout(400)
    check("leave:mask-clears", page.locator("[data-frameos-image-hover-mask]").count() == 0)

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 204, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch204: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
