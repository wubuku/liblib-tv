#!/usr/bin/env python3

"""Verify Batch 213: yunjing menu is a 23-card motion gallery.

Source evidence (source-yunjing-cards.json / source-yunjing-names.json):
the 运镜 pill opens a card gallery (grid-cols-4, cards with aspect-square
remote webp thumbnails from tool/movement/N.webp, centered names) with 23
motions — 固定镜头/跟随拍摄/盘旋抬升/…/手持拍摄. Selection toggles per card.
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
    / "liblib-canvas-batch213-2026-09-08"
    / "runtime-audit.json"
)

EXPECTED_FIRST = ["固定镜头", "跟随拍摄", "盘旋抬升", "盘旋下降"]
EXPECTED_TOTAL = 23


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
        assert ok, f"batch213 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto("http://localhost:4317", wait_until="networkidle")
    page.wait_for_timeout(500)

    page.locator('.react-flow__node[data-id="v-UGQZzZOpbv"]').click(force=True)
    page.wait_for_timeout(400)

    page.locator("[data-yunjing-trigger]").click()
    page.wait_for_timeout(400)
    menu = page.locator("[data-yunjing-menu]")
    check("menu:opens", menu.count() == 1)

    options = page.locator("[data-yunjing-option]")
    check("menu:23-cards", options.count() == EXPECTED_TOTAL)

    names = options.all_inner_texts()
    check("menu:starts-fixed", EXPECTED_FIRST[0] in names[0])
    check("menu:contains-follow", any("跟随拍摄" in n for n in names))
    check("menu:contains-handheld", any("手持拍摄" in n for n in names))

    imgs = options.locator("img")
    check("menu:cards-have-images", imgs.count() == EXPECTED_TOTAL)

    # select a card, menu closes
    options.nth(0).click()
    page.wait_for_timeout(300)
    check("menu:closes-on-select", menu.count() == 0)

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 213, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch213: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
