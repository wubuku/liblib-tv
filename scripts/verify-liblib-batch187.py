#!/usr/bin/env python3

"""Verify Batch 187: footer doc-sparkle/settings2 buttons are click-inert.

Source evidence (2026-09-08 CDP, empty fresh node): clicking the
doc-sparkle (0 0 20 20) and settings2 (0 0 24 24) footer buttons opens no
popover, toggles no state (class diff is hover noise only) and mounts no
new layer — consistent with the clone's inert placeholders (their real
semantics stay unsampled). This verifier pins that inertness in the clone:
clicking either button opens no menu/popover and leaves the panel state
intact.
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
    / "liblib-canvas-batch187-2026-09-08"
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
        assert ok, f"batch187 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(BASE_URL, wait_until="networkidle")
    page.wait_for_timeout(500)

    page.locator('.react-flow__node[data-id="v-UGQZzZOpbv"]').click(force=True)
    page.wait_for_timeout(400)

    panel = page.locator("[data-video-generation-panel]")
    check("panel:open", panel.count() == 1)

    sparkle = panel.locator("button[data-footer-icon='doc-sparkle']")
    settings2 = panel.locator("button[data-footer-icon='settings2']")
    check("buttons:present", sparkle.count() == 1 and settings2.count() == 1)

    for name, btn in (("sparkle", sparkle), ("settings2", settings2)):
        btn.click(force=True)
        page.wait_for_timeout(350)
        check(
            f"{name}:no-menu",
            page.locator("[data-canvas-context-menu]").count() == 0
            and page.locator("[data-video-model-menu]").count() == 0
            and page.locator("[data-video-params-menu]").count() == 0
            and page.locator("[data-video-mode-menu]").count() == 0,
        )
        check(f"{name}:panel-intact", panel.count() == 1)

    # settings stay unchanged after both clicks
    label = page.locator("[data-video-params-trigger]").inner_text()
    check("state:params-unchanged", "16:9 · 720P · 5s · 1个" in label)
    check("state:credits-visible", panel.locator("[data-video-credits]").count() == 1)

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 187, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch187: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
