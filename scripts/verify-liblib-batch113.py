#!/usr/bin/env python3

"""Verify Batch 113 uniform character strip spacing against the 2026-09-05 source rhythm."""

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
    / "liblib-canvas-batch113-2026-09-05"
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
        assert ok, f"batch113 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(BASE_URL, wait_until="networkidle")
    page.wait_for_timeout(400)

    page.get_by_role("button", name="角色库").click()
    modal = page.locator('[data-liblib-overlay="primary:character"]')
    assert modal.is_visible()

    gaps = modal.evaluate("""() => {
      const cards = Array.from(modal_query());
      function modal_query() {
        return document.querySelectorAll("[data-character-strip-card]");
      }
      const xs = Array.from(document.querySelectorAll("[data-character-strip-card]")).map((el) => el.getBoundingClientRect().x);
      const deltas = [];
      for (let i = 1; i < Math.min(xs.length, 6); i++) deltas.push(Math.round(xs[i] - xs[i - 1]));
      return deltas;
    }""")
    check("strip:cards-visible", len(gaps) >= 4)
    check("strip:uniform-pitch", len(set(gaps)) == 1)

    check("diagnostics:zero", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 113,
        "title": "Uniform character strip spacing",
        "evidence": "docs/research/liblib-live-2026-09-05/original-character-library-modal.png",
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
        "Batch 113 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "Uniform strip card pitch recorded in runtime-audit.json."
    )


if __name__ == "__main__":
    main()
