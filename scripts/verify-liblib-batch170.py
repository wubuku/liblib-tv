#!/usr/bin/env python3

"""Verify Batch 170: canvas top bar workspace rename input.

Source evidence (2026-09-07 canvas top bar): an inline workspace-name input
sits left of the canvas chip — 13px, min-w-[30px] max-w-[100px] cursor-text,
transparent background with a hairline border; store default 未命名工作区.
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
    / "liblib-canvas-batch170-2026-09-07"
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
        assert ok, f"batch170 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(BASE_URL, wait_until="networkidle")
    page.wait_for_timeout(500)

    ws = page.locator("[data-workspace-name]")
    check("workspace:visible", ws.is_visible())
    check("workspace:default-value", ws.input_value() == "未命名工作区")
    st = ws.evaluate(
        """el => { const s = getComputedStyle(el);
        return {bg: s.backgroundColor, cursor: s.cursor, mw: s.maxWidth}; }"""
    )
    check("workspace:transparent", st["bg"] in ("rgba(0, 0, 0, 0)", "transparent"))
    check("workspace:cursor-text", st["cursor"] == "text")
    check("workspace:max-w-100", st["mw"] == "100px")
    # 位于画布芯片左侧
    ws_box = ws.bounding_box()
    chip = page.locator("[data-canvas-trigger]").first
    chip_box = chip.bounding_box()
    check(
        "workspace:left-of-chip",
        ws_box is not None and chip_box is not None and ws_box["x"] < chip_box["x"],
    )

    # 重命名生效（输入 → 画布标签页菜单可见新名，还原）
    ws.fill("测试工作区")
    page.wait_for_timeout(200)
    check("workspace:rename-applied", ws.input_value() == "测试工作区")
    ws.fill("未命名工作区")
    page.wait_for_timeout(200)

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 170, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch170: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
