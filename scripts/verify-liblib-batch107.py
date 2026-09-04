#!/usr/bin/env python3

"""Verify Batch 107 skill headline rotation against the 2026-09-05 source observations."""

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
    / "liblib-canvas-batch107-2026-09-05"
    / "runtime-audit.json"
)

HEADLINES = [
    "选一个 Skill，让创作更快一步",
    "让 Skill 帮你迈出第一步",
    "一个 Skill，慢慢打磨你的故事",
]


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
        assert ok, f"batch107 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(BASE_URL, wait_until="networkidle")
    page.wait_for_timeout(400)

    page.get_by_role("button", name="Agent", exact=True).click()
    agent = page.locator('[data-liblib-overlay="agent"]')
    assert agent.is_visible()

    for expected_index in range(len(HEADLINES)):
        headline = HEADLINES[expected_index]
        check(
            f"headline:{expected_index}",
            agent.get_by_text(headline, exact=True).is_visible(),
        )
        agent.locator("[data-agent-refresh]").click()
        page.wait_for_timeout(120)

    check("headline:wraps", agent.get_by_text(HEADLINES[0], exact=True).is_visible())
    check("skills:still-4", agent.locator("[data-agent-skill]").count() == 4)

    check("diagnostics:zero", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 107,
        "title": "Skill headline rotation per 2026-09-05 source observations",
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
        "Batch 107 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "Three source-observed headlines rotate with 换一批 and wrap "
        "recorded in runtime-audit.json."
    )


if __name__ == "__main__":
    main()
