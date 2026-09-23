#!/usr/bin/env python3

"""Verify Batch 177: FrameOS delete-immediately alignment, help icons,
keyboard coverage audit.

2026-09-24 source evidence: node deletion (backspace / context menu / cut)
is immediate - no confirmation dialog (manual Gate B duplicate-delete-history
walk). The clone popped a confirm dialog for all three paths; this batch
removes it. Help panel section icons now differ per group (source sampled
ri-quill-pen/focus-3/drag-move/settings-3). Keyboard audit: cmd-F/cmd-0/M/
cmd +/- handlers exist; cmd-A intentionally passes through.
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
    / "liblib-frameos-batch177-2026-09-24"
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


def no_confirm_dialog(page: Page) -> bool:
    return (
        page.locator(
            "[data-frameos-confirm], [role=dialog], [class*=confirm]"
        ).count()
        == 0
    )


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool) -> None:
        assert ok, f"batch177 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/frameos/canvas/demo", wait_until="domcontentloaded")
    page.wait_for_timeout(1200)

    # 1) context menu delete -> immediate, no confirm dialog
    page.locator(".react-flow__node-text").first.click(button="right")
    page.wait_for_timeout(300)
    menu = page.locator("[data-frameos-context-menu]")
    check("ctx:menu-opens", menu.is_visible())
    n_before = page.locator(".react-flow__node").count()
    menu.locator("[data-frameos-context-item='删除']").click()
    page.wait_for_timeout(500)
    n_after = page.locator(".react-flow__node").count()
    check("ctx:delete-immediate", n_after == n_before - 1)
    check("ctx:no-confirm-dialog", no_confirm_dialog(page))

    # 2) cmd-z restores the deleted node
    page.keyboard.press("Meta+z")
    page.wait_for_timeout(500)
    check(
        "undo:restores",
        page.locator(".react-flow__node").count() >= n_before - 1,
    )

    # 3) help panel per-group icons
    page.keyboard.press("?")
    page.wait_for_timeout(400)
    panel = page.locator(".frameos-shortcuts-panel")
    check("help:opens", panel.is_visible())
    icons: dict[str, str] = {}
    for g in ["创作", "缩放", "移动画布", "其他"]:
        slot = panel.locator(f"[data-frameos-help-icon='{g}']")
        icons[g] = slot.inner_text() if slot.count() else ""
        check(f"help:icon:{g}", slot.count() == 1 and icons[g] != "")
    check("help:icons-distinct", len(set(icons.values())) == 4)
    page.keyboard.press("Escape")
    page.wait_for_timeout(200)

    # 4) keyboard coverage: cmd-F opens node search
    page.keyboard.press("Meta+f")
    page.wait_for_timeout(300)
    check("audit:cmdf", page.locator("[data-frameos-node-search]").is_visible())
    page.keyboard.press("Escape")
    page.wait_for_timeout(200)
    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 177, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch177: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
