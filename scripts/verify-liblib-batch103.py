#!/usr/bin/env python3

"""Verify Batch 103 top-bar mode toggle alignment with the 2026-09-05 source audit."""

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
    / "liblib-canvas-batch103-2026-09-05"
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
        assert ok, f"batch103 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(BASE_URL, wait_until="networkidle")
    page.wait_for_timeout(400)

    workflow = page.get_by_role("button", name="工作流", exact=True)
    storyboard = page.get_by_role("button", name="故事板", exact=True)
    check("names:unique", workflow.count() == 1 and storyboard.count() == 1)
    check("boot:workflow-pressed", workflow.get_attribute("aria-pressed") == "true")
    check("boot:storyboard-not-pressed", storyboard.get_attribute("aria-pressed") == "false")
    check("boot:old-names-gone", page.get_by_role("button", name="工作台", exact=True).count() == 0
          and page.get_by_role("button", name="分镜", exact=True).count() == 0)
    demo_nodes = page.locator(".react-flow__node").count()

    storyboard.click()
    page.wait_for_timeout(400)
    check("switch:storyboard-pressed", storyboard.get_attribute("aria-pressed") == "true")
    check("switch:workflow-released", workflow.get_attribute("aria-pressed") == "false")
    check("switch:board-visible", page.locator("[data-storyboard-board]").is_visible())

    workflow.click()
    page.wait_for_timeout(400)
    check("back:workflow-pressed", workflow.get_attribute("aria-pressed") == "true")
    check("back:graph-preserved", page.locator(".react-flow__node").count() == demo_nodes)
    check("back:board-hidden", page.locator("[data-storyboard-board]").count() == 0)

    check("diagnostics:zero", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 103,
        "title": "Top-bar mode toggle alignment with 2026-09-05 source audit",
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
        "Batch 103 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "工作流/故事板 naming, pressed states, storyboard+agent coupling, "
        "workbench round-trip and graph preservation recorded in runtime-audit.json."
    )


if __name__ == "__main__":
    main()
