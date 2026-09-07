#!/usr/bin/env python3

"""Verify Batch 191: effects gallery popover + pill inertness notes.

Source evidence (2026-09-08 CDP, source-pill-popovers.json /
source-effects-card.json):
- the 特效 pill opens a horizontally centered overlay of effect cards
  (185x235, square thumbnail, hover 收藏 button, name + 商用 badge +
  author + credits) — 8 cards on the source, 4 sampled and rendered in the
  clone with gradient thumbnail placeholders (only one remote webp URL was
  captured);
- 运镜/参考/标记 are click-INERT on an empty fresh node (the clone keeps
  its batch146 运镜 menu contract; the divergence is recorded).
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
    / "liblib-canvas-batch191-2026-09-08"
    / "runtime-audit.json"
)

EXPECTED_CARDS = ["试妆特写", "悬浮缓入", "微距推镜", "直升机揭幕"]


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
        assert ok, f"batch191 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(BASE_URL, wait_until="networkidle")
    page.wait_for_timeout(500)

    page.locator('.react-flow__node[data-id="v-UGQZzZOpbv"]').click(force=True)
    page.wait_for_timeout(400)

    gallery = page.locator("[data-effects-gallery]")
    check("gallery:closed-initial", gallery.count() == 0)

    page.locator("[data-effects-trigger]").click()
    page.wait_for_timeout(350)
    check("gallery:opens", gallery.count() == 1)
    cards = page.locator("[data-effects-gallery] [data-effects-card]")
    check("gallery:four-cards", cards.count() == 4)
    names = page.eval_on_selector_all(
        "[data-effects-gallery] [data-effects-card]",
        "els => els.map(el => el.getAttribute('data-effects-card'))",
    )
    check("gallery:card-names", names == EXPECTED_CARDS)
    first = cards.first
    check("gallery:card-width", abs(first.bounding_box()["width"] - 185) <= 2)
    check("gallery:badge", first.get_by_text("商用", exact=True).count() == 1)
    check("gallery:credits", first.get_by_text("185", exact=True).count() == 1)

    # closes on outside mousedown (the open gallery covers the trigger —
    # source-aligned behavior); click inside the panel prompt area so the
    # node stays selected
    page.evaluate(
        """() => {
        const footer = document.querySelector('[data-video-generation-panel] footer');
        footer.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }));
        }"""
    )
    page.wait_for_timeout(300)
    check("gallery:closes-on-outside", gallery.count() == 0)

    # 运镜 menu contract intact (batch146)
    page.locator("[data-yunjing-trigger]").click()
    page.wait_for_timeout(300)
    check("yunjing:menu-still-opens", page.locator("[data-yunjing-menu]").count() == 1)
    page.keyboard.press("Escape")
    page.wait_for_timeout(200)

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 191, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch191: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
