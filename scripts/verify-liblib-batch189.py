#!/usr/bin/env python3

"""Verify Batch 189: ratio tile glyphs use the sampled source structure.

Source evidence (2026-09-08 CDP, source-ratio-tiles.json): each ratio tile's
glyph is a 17px centering box wrapping a `rounded-[2px] border-[1.5px]
border-current` rect with exact per-ratio dimensions — Auto 12x9, 16:9 16x9,
4:3 12x9, 1:1 12x12, 3:4 9x12, 9:16 9x16, 21:9 16x7. The clone's
AspectRatioGlyph now matches this structure and dims.

Open question recorded: today's normal-mode menu shows SEVEN tiles including
Auto (fresh 2.5 node) vs Batch 175's six-tile sample (2.0-model day) — a
model-dependency hypothesis that could not be confirmed (model menu stopped
opening via JS); the clone grid stays per Batch 175/176.
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
    / "liblib-canvas-batch189-2026-09-08"
    / "runtime-audit.json"
)

EXPECTED_DIMS = {
    "16:9": (16, 9),
    "4:3": (12, 9),
    "1:1": (12, 12),
    "3:4": (9, 12),
    "9:16": (9, 16),
    "21:9": (16, 7),
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
        assert ok, f"batch189 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(BASE_URL, wait_until="networkidle")
    page.wait_for_timeout(500)

    page.locator('.react-flow__node[data-id="v-UGQZzZOpbv"]').click(force=True)
    page.wait_for_timeout(400)
    page.locator("[data-video-params-trigger]").click(force=True)
    page.wait_for_timeout(400)

    menu = page.locator("[data-video-params-menu]")
    check("menu:open", menu.count() == 1)

    for label, (w, h) in EXPECTED_DIMS.items():
        tile = menu.locator(f'[data-video-ratio-option="{label}"]')
        glyph = tile.locator("span").first
        cls = glyph.get_attribute("class") or ""
        check(f"tile:{label}:box-17", "size-[17px]" in cls)
        inner = glyph.locator("span").first
        style = inner.get_attribute("style") or ""
        check(f"tile:{label}:dims", f"width: {w}px" in style and f"height: {h}px" in style)
        check(f"tile:{label}:border-1-5", "border-[1.5px]" in (inner.get_attribute("class") or ""))

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 189, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch189: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
