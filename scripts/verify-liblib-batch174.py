#!/usr/bin/env python3

"""Verify Batch 174: model menu row system alignment.

Source evidence (2026-09-07 CDP, three-state direct measurement):
- every row is fixed 52px tall (selected / plain / hover — no growth);
- selected row background rgba(255,255,255,0.15), plain transparent,
  hovered plain row rgba(255,255,255,0.1);
- leading icon tile 34x34 rounded-lg; description text is present in every
  row's DOM, clipped by the 36px text column (no selected-only expansion);
- menu container stays 380 wide (rows 360 inside p-2).
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
    / "liblib-canvas-batch174-2026-09-07"
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
        assert ok, f"batch174 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(BASE_URL, wait_until="networkidle")
    page.wait_for_timeout(500)

    page.locator('.react-flow__node[data-id="v-UGQZzZOpbv"]').click(force=True)
    page.wait_for_timeout(300)
    page.locator("[data-video-model-trigger]").click(force=True)
    page.wait_for_timeout(400)
    menu = page.locator("[data-video-model-menu]")
    check("menu:open", menu.count() == 1)

    def row_height(model_id: str) -> float:
        b = page.locator(f'[data-video-model-option="{model_id}"]').bounding_box()
        return b["height"] if b else -1

    def row_alpha(model_id: str) -> str:
        return page.locator(f'[data-video-model-option="{model_id}"]').evaluate(
            "el => getComputedStyle(el).backgroundColor"
        )

    selected_id = page.locator('[data-video-model-option][aria-pressed="true"]').get_attribute(
        "data-video-model-option"
    )
    check("row:selected-fixed-52", abs(row_height(selected_id) - 52) <= 1)
    check("row:plain-fixed-52", abs(row_height("2.0 VIP") - 52) <= 1)
    check("row:late-fixed-52", abs(row_height("Kling O3") - 52) <= 1)

    sel_alpha = row_alpha(selected_id)
    check("row:selected-white-15", "0.15" in sel_alpha)
    check("row:plain-transparent", row_alpha("2.0 VIP") in ("rgba(0, 0, 0, 0)", "transparent"))

    # hover a plain row -> white/10
    target = page.locator('[data-video-model-option="2.0 VIP"]')
    target.hover()
    page.wait_for_timeout(250)
    check("row:hover-white-10", "0.1" in row_alpha("2.0 VIP"))
    page.mouse.move(700, 200)
    page.wait_for_timeout(250)

    tile = page.locator('[data-video-model-option="2.0 VIP"] > span').first
    tb = tile.bounding_box()
    check("row:icon-tile-34", tb is not None and abs(tb["width"] - 34) <= 1 and abs(tb["height"] - 34) <= 1)

    for model_id in ("2.5", "2.0 VIP"):
        desc = page.locator(f'[data-video-model-option="{model_id}"] [data-video-model-description]')
        check(f"row:description-in-dom-{model_id}", desc.count() == 1)

    page.keyboard.press("Escape")
    page.wait_for_timeout(200)
    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 174, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch174: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
