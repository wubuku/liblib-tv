#!/usr/bin/env python3

"""Verify Batch 193: 参考/标记 pills stay click-inert (incl. prompt state).

Source evidence (2026-09-08 CDP): both pills open no popover on an empty
node (Batch 191) NOR with a typed prompt (source-pill-precondition.json);
the precondition for their real popovers stays unsampled (likely requires
uploaded/generated reference content). The clone's pills are inert
placeholders — this pins that parity.
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
    / "liblib-canvas-batch193-2026-09-08"
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
        assert ok, f"batch193 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(BASE_URL, wait_until="networkidle")
    page.wait_for_timeout(500)

    page.locator('.react-flow__node[data-id="v-UGQZzZOpbv"]').click(force=True)
    page.wait_for_timeout(400)
    panel = page.locator("[data-video-generation-panel]")
    check("panel:open", panel.count() == 1)

    # type a prompt first (the sampled precondition state)
    ta = panel.locator("textarea").first
    ta.click()
    ta.fill("一只猫在窗台看雨")
    page.wait_for_timeout(200)

    for label in ("参考", "标记"):
        pill = panel.locator(f"[data-video-toolbar] button:has-text('{label}')").first
        pill.click()
        page.wait_for_timeout(300)
        check(
            f"{label}:inert",
            page.locator("[data-yunjing-menu]").count() == 0
            and page.locator("[data-effects-gallery]").count() == 0
            and page.locator("[data-canvas-context-menu]").count() == 0
            and panel.count() == 1,
        )
        check(f"{label}:prompt-preserved", ta.input_value() == "一只猫在窗台看雨")

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 193, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch193: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
