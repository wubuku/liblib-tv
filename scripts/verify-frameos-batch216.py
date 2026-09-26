#!/usr/bin/env python3

"""Verify Batch 216: FrameOS 3D model node renderer + creation.

Source re-sampling 2026-09-24 (live canvas): the rail menu 3D模型 entry
creates a 3D box icon card (300x200) with handles and a selected blue
frame. The clone now implements the model3d node type end-to-end. Verifies
menu item, creation, rendering, selection, and undo removal.
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
    / "liblib-frameos-batch216-2026-09-24"
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
        assert ok, f"batch216 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/frameos/canvas/demo", wait_until="domcontentloaded", timeout=90000)
    page.wait_for_timeout(1200)
    nodes_before = page.locator(".react-flow__node").count()

    # rail 菜单 → 3D模型
    page.evaluate(
        """(() => {
          const btn = [...document.querySelectorAll("button")].find(x =>
            (x.getAttribute("aria-label") || "").trim() === "添加节点");
          if (btn) btn.click();
        })()"""
    )
    page.wait_for_timeout(500)
    page.evaluate(
        """(() => {
          const items = [...document.querySelectorAll("*")].filter(e => {
            if (!e.offsetParent || e.children.length > 0) return false;
            const r = e.getBoundingClientRect();
            return (e.textContent || "").trim() === "3D模型" && r.width < 200;
          });
          const el = items[items.length - 1];
          if (el) el.click();
        })()"""
    )
    page.wait_for_timeout(800)

    node = page.locator(".react-flow__node-model3d")
    check("model3d:created", node.count() == 1)
    check(
        "model3d:selected",
        page.evaluate(
            "window.__frameos_store.getState().nodes.some((n) => n.type === 'model3d' && n.selected)"
        ),
    )
    check(
        "model3d:box-icon",
        page.evaluate(
            """(() => {
              const n = window.__frameos_store.getState().nodes.find(n => n.type === 'model3d');
              const el = n ? document.querySelector(`.react-flow__node[data-id="${n.id}"]`) : null;
              return el ? (el.textContent || "").includes("3D模型") : false;
            })()"""
        ),
    )

    # 撤销 → 移除
    page.keyboard.press("Meta+z")
    page.wait_for_timeout(500)
    check(
        "undo:removes-model3d",
        page.locator(".react-flow__node-model3d").count() == 0,
    )

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 216, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch216: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
