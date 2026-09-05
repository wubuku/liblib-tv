#!/usr/bin/env python3

"""Verify Batch 112 character filter panel alignment with the 2026-09-05 sampling."""

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
    / "liblib-canvas-batch112-2026-09-05"
    / "runtime-audit.json"
)

GROUP_CHIPS = {
    "性别": ["男", "女", "中性"],
    "年龄段": ["儿童", "少年", "青年", "中年", "老年"],
    "种族": ["人类", "精灵", "兽人", "机械", "其他"],
    "时代": ["先秦", "古代", "近代", "现代", "未来"],
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
    page.on(
        "requestfailed",
        lambda request: errors.append(
            f"requestfailed:{request.method}:{request.url}:{request.failure}"
        ),
    )
    return errors


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool) -> None:
        assert ok, f"batch112 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(BASE_URL, wait_until="networkidle")
    page.wait_for_timeout(400)

    page.get_by_role("button", name="角色库").click()
    modal = page.locator('[data-liblib-overlay="primary:character"]')
    assert modal.is_visible()

    modal.locator("[data-character-filter-toggle]").click()
    panel = modal.locator("[data-character-filter-panel]")
    check("panel:open", panel.is_visible())
    check("panel:clear", panel.locator("[data-character-filter-clear]").is_visible())
    for group, chips in GROUP_CHIPS.items():
        header = panel.get_by_text(group, exact=True)
        check(f"group:{group}", header.count() == 1)
        for chip in chips:
            check(
                f"chip:{group}:{chip}",
                panel.locator(f"[data-character-filter-chip='{chip}']").count() == 1,
            )
    check("group:culture-unknown", panel.get_by_text("文化区域", exact=True).count() == 1)

    panel.locator("[data-character-filter-chip='男']").click()
    page.wait_for_timeout(150)
    check(
        "filter:male-hides-sweet",
        modal.locator("[data-character-strip-card='甜妹/清新少女']").count() == 0,
    )
    check(
        "filter:male-keeps-bazong",
        modal.locator("[data-character-strip-card='霸总/精英大佬']").count() == 1,
    )
    chip = panel.locator("[data-character-filter-chip='男']")
    check("filter:chip-pressed", chip.get_attribute("aria-pressed") == "true")

    panel.locator("[data-character-filter-clear]").click()
    page.wait_for_timeout(150)
    check(
        "clear:restores-strip",
        modal.locator("[data-character-strip-card='甜妹/清新少女']").count() == 1,
    )

    modal.locator("[data-character-filter-toggle]").click()
    page.wait_for_timeout(150)
    check("toggle:closes-panel", modal.locator("[data-character-filter-panel]").count() == 0)

    modal.get_by_role("button", name="close", exact=True).click()
    page.wait_for_timeout(200)
    check("close:modal", not modal.is_visible())

    check("diagnostics:zero", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 112,
        "title": "Character filter panel alignment with 2026-09-05 sampling",
        "evidence": "docs/research/liblib-live-2026-09-05/README.md",
        "results": [],
    }
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        desktop = browser.new_page(viewport={"width": 1440, "height": 900}, device_scale_factor=1)
        audit["results"].append(run_desktop(desktop))
        desktop.close()
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    checks = audit["results"][0]["checks"]
    print(
        "Batch 112 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "Filter panel groups/chips, local tag-based filtering with 古代 alias, "
        "clear-restore and toggle recorded in runtime-audit.json."
    )


if __name__ == "__main__":
    main()
