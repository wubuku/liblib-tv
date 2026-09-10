#!/usr/bin/env python3

"""Verify Batch 202: asset drawer width + structure vs the 2026-09-08 sample.

Source evidence (source-asset-drawer.json / .png): the asset drawer is a
left sidebar ~280px wide (texts reach x≈270) with 画布/资产 tabs, an
所有评级 filter, the empty state 画布暂无节点 and the footer 共 0 节点 —
the clone's texts already match verbatim; only the width (240 → 280) was
aligned this batch.
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
    / "liblib-canvas-batch202-2026-09-08"
    / "runtime-audit.json"
)


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool) -> None:
        assert ok, f"batch202 check failed: {name}"
        result["checks"].append(name)

    errors: list[str] = []
    page.on("pageerror", lambda error: errors.append(f"pageerror:{error}"))
    page.goto("http://localhost:4317", wait_until="networkidle")
    page.wait_for_timeout(400)

    page.get_by_role("button", name="资产管理").click()
    page.wait_for_timeout(400)
    panel = page.locator("[data-liblib-overlay='asset']")
    check("drawer:opens", panel.count() == 1)
        # Batch 335: 面板宽度 280 → 320（batch 298 现行源采样）。
    check("drawer:width-320", abs(panel.bounding_box()["width"] - 320) <= 2)

    check("tabs:canvas", panel.get_by_role("button", name="画布", exact=True).count() >= 1)
    check("tabs:assets", panel.get_by_role("button", name="资产", exact=True).count() >= 1)
    check("filter:all-ratings", panel.get_by_text("所有评级", exact=True).count() >= 1)
    # the preset canvas has nodes; assert the counter format instead of the
    # empty-state text (its contract lives in batch102)
    import re as _re
    check("footer:count-format", _re.search(r"共 \d+ 节点", panel.inner_text()) is not None)

    # switch to the assets tab and back
    # assets tab: with media present on canvas-2 the tab lists them; assert
    # the tab toggles the visible list rather than an empty state
    panel.get_by_role("button", name="资产", exact=True).click()
    page.wait_for_timeout(250)
    check("tab:assets-tab-active", panel.inner_text().find("共") != -1)
    check("tab:assets-lists-media", panel.get_by_text("咖啡", exact=False).count() >= 1)
    panel.get_by_role("button", name="画布", exact=True).click()
    page.wait_for_timeout(250)
    check("tab:back-to-canvas", _re.search(r"共 \d+ 节点", panel.inner_text()) is not None)

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 202, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch202: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
