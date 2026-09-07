#!/usr/bin/env python3

"""Verify Batch 169: character library modal tab chrome + Seedance consent gate mock.

Source evidence (2026-09-07, modal chrome sampled while the source window was
briefly unthrottled):
- 公共角色库 modal 1280x703, rounded-xl, header h-12 border-b with two tabs
  (公共角色库 / Seedance2.0&2.5合规素材库, gap-9, 14px).
- The 素材库 tab is gated by a Seedance2.0 承诺书 dialog (738px, 3 clauses,
  不同意 / 同意并使用). Clone replicates the gate as local-only state.
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
    / "liblib-canvas-batch169-2026-09-07"
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
        assert ok, f"batch169 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(BASE_URL, wait_until="networkidle")
    page.wait_for_timeout(400)

    # 打开角色库（左侧栏入口）
    page.get_by_role("button", name="角色库").first.click()
    page.wait_for_timeout(800)

    tabs = page.locator("[data-clib-tabs] button")
    check("tabs:count-2", tabs.count() == 2)
    check(
        "tabs:labels",
        [tabs.nth(i).inner_text().strip() for i in range(2)]
        == ["公共角色库", "Seedance2.0&2.5合规素材库"],
    )
    check(
        "tabs:public-active",
        page.locator("[data-clib-tab='public']").get_attribute("class").find("font-medium") != -1,
    )
    check("tabs:filters-visible", page.locator("[data-character-filter-toggle]").is_visible())

    # 点击素材库页签 → 承诺书门（本地模拟）
    page.locator("[data-clib-tab='library']").click()
    page.wait_for_timeout(300)
    gate = page.locator("[data-clib-consent]")
    check("consent:gate-open", gate.is_visible())
    check("consent:clauses", gate.get_by_text("1. 您对即将上传或使用的素材拥有充分合法权益").is_visible())
    check("consent:decline-visible", gate.locator("[data-clib-consent-decline]").is_visible())

    # 不同意 → 回到公共角色库
    gate.locator("[data-clib-consent-decline]").click()
    page.wait_for_timeout(300)
    check("consent:decline-closes", gate.count() == 0)
    check(
        "consent:still-public-tab",
        page.locator("[data-clib-tab='public']").get_attribute("class").find("font-medium") != -1,
    )

    # 再次进入 → 同意并使用 → 素材库空态（本地状态，无账号操作）
    page.locator("[data-clib-tab='library']").click()
    page.wait_for_timeout(200)
    page.locator("[data-clib-consent-accept]").click()
    page.wait_for_timeout(300)
    check("consent:accept-switches", page.locator("[data-clib-library-empty]").is_visible())
    check(
        "consent:library-tab-active",
        page.locator("[data-clib-tab='library']").get_attribute("class").find("font-medium") != -1,
    )

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 169, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch169: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
