#!/usr/bin/env python3

"""Verify Batch 185: Batch 172-178 surfaces at the mobile 390 breakpoint.

Covers surfaces added after the last mobile sweep (Batch 162/163):
- canvas context menus (pane + node variants) open inside the viewport;
- attempt chips render their glyph icons with the white/10 selected state
  without horizontal page overflow;
- the model menu keeps its 52px rows and slide classes at 390.
Source mobile form for the context menu is unsampled; this batch verifies
clone-side fit/no-overflow only.
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
    / "liblib-canvas-batch185-2026-09-08"
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


def no_horizontal_overflow(page: Page) -> bool:
    return page.evaluate(
        "document.documentElement.scrollWidth <= window.innerWidth + 1"
    )


def run_mobile(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "390x844", "checks": []}

    def check(name: str, ok: bool) -> None:
        assert ok, f"batch185 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(BASE_URL, wait_until="networkidle")
    page.wait_for_timeout(600)

    # create a video node and drag it clear of preset nodes
    page.get_by_role("button", name="添加节点").click()
    page.wait_for_timeout(300)
    page.locator("[data-liblib-overlay='add-node']").get_by_role("button", name="视频", exact=True).click()
    page.wait_for_timeout(1000)
    created = page.locator(".react-flow__node-video").last
    cb = created.bounding_box()
    sx, sy = cb["x"] + cb["width"] / 2, cb["y"] + 12
    page.mouse.move(sx, sy)
    page.mouse.down()
    page.mouse.move(max(sx - 180, 120), max(sy - 200, 200), steps=8)
    page.mouse.up()
    page.wait_for_timeout(400)

    # attempt chips: icon + selected white/10 + no page overflow
    attempts = page.locator("[data-video-attempts]")
    check("chips:visible", attempts.count() == 1)
    chip = attempts.locator("[data-video-attempt='5分钟超长视频']")
    chip.click()
    page.wait_for_timeout(350)
    check("chip:selected-alpha", "0.1" in chip.evaluate("el => getComputedStyle(el).backgroundColor"))
    check("chip:icon-svg", chip.locator("svg").count() == 1)
    check("page:no-h-overflow-1", no_horizontal_overflow(page))

    # node right-click menu inside viewport
    page.locator(".react-flow__node-video").last.click(button="right", position={"x": 40, "y": 12})
    page.wait_for_timeout(400)
    menu = page.locator("[data-canvas-context-menu]")
    check("menu:node-variant", menu.get_attribute("data-canvas-context-variant") == "node")
    mb = menu.bounding_box()
    check("menu:node-in-viewport", mb["x"] >= -1 and mb["x"] + mb["width"] <= 391 and mb["y"] + mb["height"] <= 845)
    page.keyboard.press("Escape")
    page.wait_for_timeout(250)

    # pane right-click menu inside viewport (deselect first so the in-card
    # panel of the created node stops covering the canvas; probe a live blank
    # pane point because the preset composition covers most of the 390 canvas)
    page.keyboard.press("Escape")
    page.wait_for_timeout(250)
    px, py = page.evaluate(
        """() => {
        const cands = [[195, 620], [60, 480], [30, 700], [330, 300], [60, 350], [200, 90]];
        for (const [x, y] of cands) {
          const el = document.elementFromPoint(x, y);
          if (el && el.classList && el.classList.contains('react-flow__pane')) return [x, y];
        }
        return [195, 620];
        }"""
    )
    page.mouse.click(px, py, button="right")
    page.wait_for_timeout(400)
    check("menu:pane-variant", menu.get_attribute("data-canvas-context-variant") == "pane")
    mb = menu.bounding_box()
    check("menu:pane-in-viewport", mb["x"] >= -1 and mb["x"] + mb["width"] <= 391 and mb["y"] + mb["height"] <= 845)
    page.keyboard.press("Escape")
    page.wait_for_timeout(250)
    check("page:no-h-overflow-2", no_horizontal_overflow(page))

    # model menu rows + slide classes at 390: fit the view first (batch22
    # mobile pattern) so the preset video node and its in-card panel are in
    # the viewport at the fit zoom
    page.keyboard.press("Meta+0")
    page.wait_for_timeout(500)
    page.locator('.react-flow__node[data-id="v-UGQZzZOpbv"]').click(force=True)
    page.wait_for_timeout(300)
    page.locator("[data-video-model-trigger]").click(force=True)
    page.wait_for_timeout(400)
    model_menu = page.locator("[data-video-model-menu]")
    mmb = model_menu.bounding_box()
    check("model:open", model_menu.count() == 1)
    check("model:within-viewport", mmb["x"] >= -1 and mmb["x"] + mmb["width"] <= 391)
    row = page.locator('[data-video-model-option="2.0 VIP"]')
    check("model:row-52", abs(row.bounding_box()["height"] - 52) <= 1)
    kid = row.locator("span[class*='translate-y-2']").first
    check("model:slide-class", "group-hover:translate-y-0" in (kid.get_attribute("class") or ""))
    page.keyboard.press("Escape")
    page.wait_for_timeout(200)

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 185, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 390, "height": 844})
        audit["results"].append(run_mobile(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch185: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
