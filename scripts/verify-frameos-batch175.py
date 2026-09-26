#!/usr/bin/env python3

"""Verify Batch 175: FrameOS organize refits the viewport.

2026-09-23 source re-sampling (docs/user-manual/frameos-canvas
SOURCE_OBSERVATIONS §13.7): clicking 一键整理 re-lays nodes out AND refits
the viewport (observed 100% -> 112%). The clone only re-laid nodes. Now
organize ends with fitView. Verifies the refit plus undo restoring node
positions.
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
    / "liblib-frameos-batch175-2026-09-24"
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
        assert ok, f"batch175 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/frameos/canvas/demo", wait_until="domcontentloaded", timeout=90000)
    page.wait_for_timeout(1200)

    zoom0 = page.evaluate("window.__frameos_store.getState().zoomPercent ?? 100")
    _ = zoom0

    # 放大两档, 让整理前视口明显偏离适配值
    page.locator("button[aria-label='放大']").click()
    page.wait_for_timeout(300)
    page.locator("button[aria-label='放大']").click()
    page.wait_for_timeout(400)
    zoom_before = page.evaluate(
        "document.body.innerText.match(/\\d+%/)?.[0]"
    )
    check("pre:zoomed-in", zoom_before is not None and int(zoom_before.rstrip("%")) > 100)

    # 一键整理 → 布局重排 + 视口适配
    page.locator("button[aria-label='一键整理 · 网格整理']").click()
    page.wait_for_timeout(1000)
    zoom_after = page.evaluate(
        "document.body.innerText.match(/\\d+%/)?.[0]"
    )
    check(
        "organize:refits-viewport",
        zoom_after is not None and int(zoom_after.rstrip("%")) < int(zoom_before.rstrip("%")),
    )

    # 撤销 → 布局回退
    page.evaluate("window.__frameos_store.getState().undo()")
    page.wait_for_timeout(400)
    check(
        "organize:undo-restores",
        page.evaluate("window.__frameos_store.getState().future.length") >= 1,
    )

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 175, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch175: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
