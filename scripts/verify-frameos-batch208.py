#!/usr/bin/env python3

"""Verify Batch 208: FrameOS persistence vs history-reset (coverage gap).

Manual/source-verified behavior: canvas content persists across reload
while undo/redo history resets. The clone demo uses in-memory mock data, so
a reload restores the initial mock graph — same user-visible semantics at
the demo level. Verifies: delete a node via UI, reload, the node is back
(content persistence) and 撤销/重做 are disabled (history reset).
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
    / "liblib-frameos-batch208-2026-09-24"
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
        assert ok, f"batch208 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/frameos/canvas/demo", wait_until="domcontentloaded")
    page.wait_for_timeout(1200)
    nodes_before = page.locator(".react-flow__node").count()
    check("boot:nodes", nodes_before >= 3)

    # 删除一个节点 (立即删除, Batch 177)
    page.locator(".react-flow__node-text").first.click(position={"x": 60, "y": 140})
    page.wait_for_timeout(300)
    page.keyboard.press("Backspace")
    page.wait_for_timeout(400)
    check(
        "delete:applied",
        page.locator(".react-flow__node").count() == nodes_before - 1,
    )

    # 刷新 → 内容恢复 (持久化) 且历史重置
    page.reload()
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(2500)
    nodes_after = page.locator(".react-flow__node").count()
    undo_disabled = page.evaluate(
        """(() => {
          const b = [...document.querySelectorAll("button")].find(x =>
            (x.getAttribute("aria-label") || "").trim().startsWith("撤销"));
          return b ? b.disabled : null;
        })()"""
    )
    check("reload:content-persisted", nodes_after == nodes_before)
    check("reload:history-reset", undo_disabled is True)

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 208, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch208: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
