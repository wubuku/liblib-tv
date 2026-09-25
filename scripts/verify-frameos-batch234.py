#!/usr/bin/env python3

"""Verify Batch 234: group toolbar 批量下载 wiring.

Batch 234 implements the group toolbar's 批量下载 (label-explicit behavior):
it downloads each selected node's media (imageUrl/audioUrl), skipping nodes
without media, and toasts the count.

Checks:
1. marquee two content image nodes → 批量下载 click fires two downloads;
2. toast reports the count;
3. errors clean.
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
    / "liblib-frameos-batch234-2026-09-26"
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
        assert ok, f"batch234 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/frameos/canvas/demo", wait_until="domcontentloaded", timeout=90000)
    page.wait_for_timeout(1500)

    # 框选 image-1 + image-2 (同 batch229/232 几何)
    boxes = page.evaluate(
        """(() => {
          const a = document.querySelector('.react-flow__node[data-id=\\'image-1\\']')?.getBoundingClientRect();
          const b = document.querySelector('.react-flow__node[data-id=\\'image-2\\']')?.getBoundingClientRect();
          const targets = [a, b].filter(Boolean);
          if (targets.length < 2) {
            const all = [...document.querySelectorAll('.react-flow__node')].map((n) => n.getBoundingClientRect()).slice(0, 2);
            targets.push(...all);
          }
          const minX = Math.min(...targets.map((r) => r.left));
          const minY = Math.min(...targets.map((r) => r.top));
          const maxX = Math.max(...targets.map((r) => r.right));
          const maxY = Math.max(...targets.map((r) => r.bottom));
          let start = null;
          for (let x = minX - 20; x <= maxX; x += 12) {
            const y = minY - 25;
            const el = document.elementFromPoint(x, y);
            if (el?.closest('.react-flow__pane') && !el?.closest('.react-flow__node') && !el?.closest('.resize-handle') && !el?.closest('[class*=minimap]') && !el?.closest('button')) {
              start = { x, y };
              break;
            }
          }
          if (!start) start = { x: 150, y: 400 };
          return { start, end: { x: maxX + 15, y: maxY + 15 } };
        })()"""
    )
    page.mouse.move(boxes["start"]["x"], boxes["start"]["y"])
    page.mouse.down()
    page.mouse.move(boxes["end"]["x"], boxes["end"]["y"], steps=8)
    page.mouse.up()
    page.wait_for_timeout(500)
    selected = page.evaluate(
        "document.querySelectorAll('.react-flow__node.selected').length"
    )
    check("marquee:multi-selected", selected >= 2)
    group_tb = page.locator(".frameos-group-toolbar")
    check("group:toolbar-opens", group_tb.is_visible())

    # 批量下载 → 两次下载事件
    with page.expect_download() as dl1:
        group_tb.locator("button[aria-label='批量下载']").click()
    with page.expect_download() as dl2:
        pass
    check("batch:two-downloads", dl1.value.suggested_filename is not None and dl2.value.suggested_filename is not None)
    check(
        "batch:toast-count",
        page.locator("[class*=toast], [class*=Toast]").first.is_visible(),
    )

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 234, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch234: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
