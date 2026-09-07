#!/usr/bin/env python3

"""Verify Batch 195: effects gallery anchor is static screen positioning.

Source evidence (2026-09-08 three-state sampling, node dragged to
top/middle/bottom): the gallery box is IDENTICAL in all states
[177, 444, 1567, 235] at a 1920 viewport — horizontally centered, top at
y≈444, independent of the trigger position (retracting Batch 194's
state-dependent-anchor finding, which was a locator artifact). The clone
anchors the gallery at fixed top-[444px], horizontally centered.
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
    / "liblib-canvas-batch195-2026-09-08"
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
    return errors


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool) -> None:
        assert ok, f"batch195 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(BASE_URL, wait_until="networkidle")
    page.wait_for_timeout(500)

    page.locator('.react-flow__node[data-id="v-UGQZzZOpbv"]').click(force=True)
    page.wait_for_timeout(400)

    boxes = []
    for tag in ("a", "b"):
        page.locator("[data-effects-trigger]").click()
        page.wait_for_timeout(350)
        gallery = page.locator("[data-effects-gallery]")
        check(f"gallery:open-{tag}", gallery.count() == 1)
        gb = gallery.bounding_box()
        check(f"gallery:top-444-{tag}", abs(gb["y"] - 444) <= 3)
        center_x = gb["x"] + gb["width"] / 2
        check(f"gallery:h-centered-{tag}", abs(center_x - 720) <= 4)
        boxes.append(gb)
        page.evaluate(
            """() => {
            const footer = document.querySelector('[data-video-generation-panel] footer');
            if (footer) footer.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }));
            }"""
        )
        page.wait_for_timeout(300)
    check("gallery:stable-across-opens", abs(boxes[0]["x"] - boxes[1]["x"]) <= 2 and abs(boxes[0]["y"] - boxes[1]["y"]) <= 2)

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 195, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch195: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
