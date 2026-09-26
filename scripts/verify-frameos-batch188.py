#!/usr/bin/env python3

"""Verify Batch 188: cmd-A on the canvas no longer selects page text.

The canvas is an editor surface: cmd-A outside inputs must not trigger the
browser's native select-all (which visually selects node labels). Inputs
keep native behavior.
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
    / "liblib-frameos-batch188-2026-09-24"
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
        assert ok, f"batch188 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/frameos/canvas/demo", wait_until="domcontentloaded", timeout=90000)
    page.wait_for_timeout(1200)

    # 画布空白处 ⌘A → 无文本选区
    page.mouse.click(700, 500)
    page.keyboard.press("Meta+a")
    page.wait_for_timeout(200)
    sel = page.evaluate("window.getSelection().toString()")
    check("canvas:cmd-a-no-selection", sel == "")

    # 输入框内 ⌘A 仍全选 (文本编辑不受影响): 打开搜索框输入后全选
    page.keyboard.press("Meta+f")
    page.wait_for_timeout(300)
    box = page.locator("[data-frameos-node-search-input]")
    box.fill("abc")
    page.keyboard.press("Meta+a")
    page.wait_for_timeout(200)
    sel_in_input = page.evaluate(
        """(() => {
          const input = document.querySelector("[data-frameos-node-search-input]");
          return input ? input.selectionStart === 0 && input.selectionEnd === input.value.length : null;
        })()"""
    )
    check("input:cmd-a-selects-all", sel_in_input is True)
    page.keyboard.press("Escape")
    page.wait_for_timeout(200)

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 188, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch188: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
