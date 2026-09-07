#!/usr/bin/env python3

"""Verify Batch 192: effect card click spawns a material node + edge.

Source evidence (2026-09-08 CDP screenshot + DOM): clicking an effect card
closes the gallery and spawns a new canvas node labeled 素材 - 特效 - <名>
(with the effect thumbnail) to the lower-left of the video node, connected
by an edge flowing into the video node; credits unchanged (135). The clone
implements this via addNodeAtPosition (image, filename 素材 - 特效 - <名>)
+ addEdge (material → video); the thumbnail art is the clone's default
placeholder (recorded simplification).
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
    / "liblib-canvas-batch192-2026-09-08"
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
        assert ok, f"batch192 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(BASE_URL, wait_until="networkidle")
    page.wait_for_timeout(500)

    # fresh video node (drag clear of presets)
    page.get_by_role("button", name="添加节点").click()
    page.wait_for_timeout(300)
    page.locator("[data-liblib-overlay='add-node']").get_by_role("button", name="视频", exact=True).click()
    page.wait_for_timeout(1000)
    created = page.locator(".react-flow__node-video").last
    cb = created.bounding_box()
    sx, sy = cb["x"] + cb["width"] / 2, cb["y"] + 12
    page.mouse.move(sx, sy)
    page.mouse.down()
    page.mouse.move(sx - 180, sy - 200, steps=8)
    page.mouse.up()
    page.wait_for_timeout(400)

    nodes_before = page.locator(".react-flow__node").count()
    edges_before = page.locator(".react-flow__edge").count()

    # open gallery and click the first card
    page.locator("[data-effects-trigger]").click()
    page.wait_for_timeout(350)
    check("gallery:open", page.locator("[data-effects-gallery]").count() == 1)
    page.locator("[data-effects-card='试妆特写']").click()
    page.wait_for_timeout(600)

    check("gallery:closes", page.locator("[data-effects-gallery]").count() == 0)
    check("node:spawned", page.locator(".react-flow__node").count() == nodes_before + 1)
    check("edge:spawned", page.locator(".react-flow__edge").count() == edges_before + 1)
    check("node:filename", page.get_by_text("素材 - 特效 - 试妆特写", exact=True).count() >= 1)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 192, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch192: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
