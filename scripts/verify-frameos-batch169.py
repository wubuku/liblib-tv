#!/usr/bin/env python3

"""Verify Batch 169: FrameOS top-bar 使用教程 button + edge dashed style.

2026-09-23 source re-sampling (docs/user-manual/frameos-canvas
SOURCE_OBSERVATIONS §13.10): the top bar has a 使用教程 button (? icon +
text, left of undo/redo) that opens the external 飞书 doc (URL unsampled →
mock). Edges render dashed blue (§13.5). Verifies the button, its mock
dialog, the undo/redo pair still working, and the dashed edge style.
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
    / "liblib-frameos-batch169-2026-09-23"
    / "runtime-audit.json"
)


def attach_errors(page: Page) -> list[str]:
    errors: list[str] = []
    dialogs: list[str] = []
    page.on(
        "console",
        lambda message: errors.append(f"console:{message.type}:{message.text}")
        if message.type == "error"
        else None,
    )
    page.on("pageerror", lambda error: errors.append(f"pageerror:{error}"))
    page.on(
        "dialog",
        lambda d: (dialogs.append(d.message), d.dismiss()),
    )
    return errors, dialogs


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool) -> None:
        assert ok, f"batch169 check failed: {name}"
        result["checks"].append(name)

    errors, dialogs = attach_errors(page)
    page.goto(f"{BASE_URL}/frameos/canvas/demo", wait_until="domcontentloaded")
    page.wait_for_timeout(1200)

    # 使用教程按钮
    tut = page.locator("[data-frameos-tutorial-button]")
    check("tutorial:visible", tut.is_visible())
    check("tutorial:label", tut.get_attribute("aria-label") == "使用教程")

    # 点击 → mock 对话框
    tut.click()
    page.wait_for_timeout(300)
    check(
        "tutorial:mock-dialog",
        any("使用教程" in m for m in dialogs),
    )

    # 撤销/重做仍在且可用性符合历史
    can_undo = page.evaluate("window.__frameos_store.getState().past.length > 0")
    undo_btn = page.locator("button[aria-label='撤销 (Ctrl+Z)']")
    check(
        "regression:undo-state",
        undo_btn.is_disabled() == (not can_undo),
    )

    # 连线虚线样式 (可见路径的 computed style)
    dash = page.locator(".react-flow__edge-path").first.evaluate(
        "el => getComputedStyle(el).strokeDasharray"
    )
    check("edge:dashed", dash is not None and dash not in ("", "none"))

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
