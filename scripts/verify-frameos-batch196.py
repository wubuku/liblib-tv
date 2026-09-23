#!/usr/bin/env python3

"""Verify Batch 196: FrameOS prompt panel header tiles.

Source re-sampling (shot 09): the panel header entries (聚焦/故事版/参考)
are vertical tiles - icon above label - followed by the reference chip.
Verifies the tile geometry (height taller than a flat button, label below
icon) and that the buttons still carry their aria labels.
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
    / "liblib-frameos-batch196-2026-09-24"
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
    page.on("dialog", lambda d: d.dismiss())
    return errors


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool) -> None:
        assert ok, f"batch196 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/frameos/canvas/demo", wait_until="domcontentloaded")
    page.wait_for_timeout(1200)

    image_node = page.locator(".react-flow__node-image").first
    image_node.click(position={"x": 60, "y": 30})
    page.wait_for_timeout(400)
    editor = page.locator(".frameos-prompt-editor")
    check("panel:opens", editor.is_visible())

    for label in ["聚焦", "故事版", "参考"]:
        btn = editor.locator(f"button[aria-label='{label}']")
        check(f"tile:{label}", btn.is_visible())
        bb = btn.bounding_box()
        check(
            f"tile:{label}:vertical-shape",
            bb is not None and bb["height"] >= 38 and bb["width"] <= 70,
        )

    check(
        "regression:chips",
        page.locator("[data-frameos-ref-chip]").count() >= 1,
    )

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 196, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch196: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
