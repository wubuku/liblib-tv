#!/usr/bin/env python3
"""Verify Batch 295: asset drawer search semantics.

Source evidence (2026-09-10, docs/research/liblib-canvas-batch295-2026-09-10/
search-nomatch.png): the drawer search filters the list live, and a
no-match query shows the dedicated message 当前画布没有相关搜索结果
(distinct from the no-nodes empty state)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = (
    ROOT
    / "docs"
    / "research"
    / "liblib-canvas-batch295-2026-09-10"
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
        assert ok, f"batch295 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto("http://localhost:4317", wait_until="networkidle")
    page.wait_for_timeout(500)

    page.get_by_text("资产管理", exact=True).click(force=True)
    page.wait_for_timeout(600)

    drawer = page.locator("[data-liblib-overlay='asset']")
    check("drawer:open", drawer.is_visible())

    search = page.locator("[data-asset-manager-search]")
    check("search:button", search.count() == 1)
    search.click()
    page.wait_for_timeout(300)
    inp = page.locator("[data-asset-manager-search-input]")
    check("search:input", inp.count() == 1)

    # no-match query shows the dedicated message
    inp.fill("不存在XYZ")
    page.wait_for_timeout(300)
    check(
        "search:no-match-message",
        drawer.get_by_text("当前画布没有相关搜索结果").count() == 1,
    )
    check(
        "search:no-match-hides-list",
        page.locator("[data-asset-manager-item]").count() == 0,
    )

    # clearing restores the list
    inp.fill("")
    page.wait_for_timeout(300)
    check("search:clear-restores", page.locator("[data-asset-manager-item]").count() > 0)

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 295, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        try:
            audit["results"].append(run_desktop(page))
        except Exception as exc:  # noqa: BLE001
            page.screenshot(path=str(AUDIT_PATH.parent / "fail.png"))
            print("EXC:", str(exc)[:300])
            raise
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch295: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
