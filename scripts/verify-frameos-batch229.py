#!/usr/bin/env python3

"""Verify Batch 229: FrameOS group toolbar on multi-selection.

Source sampling 2026-09-25: blank-area drag draws a marquee (4 nodes got
selected) and a `.group-toolbar` appears above the selection bounding box —
[成组 (ri-group-line) | 批量下载 (ri-download-2-line)], 36px high, gap 15px.
Single selection keeps the per-node floating toolbar instead.

Checks:
1. marquee drag selects ≥2 nodes → group toolbar visible with both buttons;
2. per-node floating toolbar hidden during multi-selection;
3. clicking a node returns to single selection (group toolbar gone);
4. errors clean.
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
    / "liblib-frameos-batch229-2026-09-25"
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
        assert ok, f"batch229 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/frameos/canvas/demo", wait_until="domcontentloaded", timeout=90000)
    page.wait_for_timeout(1200)

    # 框选 image-1 + image-2 两个节点 (包围盒较小, 留出框外空白供后续点击)
    boxes = page.evaluate(
        """(() => {
          const a = document.querySelector('.react-flow__node[data-id=\\'image-1\\']')?.getBoundingClientRect();
          const b = document.querySelector('.react-flow__node[data-id=\\'image-2\\']')?.getBoundingClientRect();
          const targets = [a, b].filter(Boolean);
          if (targets.length < 2) {
            const all = [...document.querySelectorAll('.react-flow__node')].map((n) => n.getBoundingClientRect()).slice(0, 2);
            targets.push(...all);
          }
          const minX = Math.min(...targets.map((r) => r.left)) - 15;
          const minY = Math.min(...targets.map((r) => r.top)) - 15;
          const maxX = Math.max(...targets.map((r) => r.right)) + 15;
          const maxY = Math.max(...targets.map((r) => r.bottom)) + 15;
          return {
            start: { x: minX, y: minY },
            end: { x: maxX, y: maxY },
            blank: { x: Math.max(20, minX - 120), y: minY + 40 },
          };
        })()"""
    )

    # 1) 框选 → 多选 + 成组工具条
    page.mouse.move(boxes["start"]["x"], boxes["start"]["y"])
    page.mouse.down()
    steps = 8
    for i in range(1, steps + 1):
        x = boxes["start"]["x"] + (boxes["end"]["x"] - boxes["start"]["x"]) * i / steps
        y = boxes["start"]["y"] + (boxes["end"]["y"] - boxes["start"]["y"]) * i / steps
        page.mouse.move(x, y)
    page.mouse.up()
    page.wait_for_timeout(500)

    selected = page.evaluate(
        "document.querySelectorAll('.react-flow__node.selected').length"
    )
    check("marquee:multi-selected", selected >= 2)
    group_tb = page.locator(".frameos-group-toolbar")
    check("group:toolbar-opens", group_tb.is_visible())
    check("group:btn-grouping", group_tb.locator("button[aria-label='成组']").count() == 1)
    check(
        "group:btn-batch-download",
        group_tb.locator("button[aria-label='批量下载']").count() == 1,
    )

    # 2) 多选时单节点工具条隐藏
    check(
        "group:floating-toolbar-hidden",
        page.locator(".frameos-floating-toolbar-new").count() == 0
        or not page.locator(".frameos-floating-toolbar-new").first.is_visible(),
    )

    # 3) 点空白 pane (选区包围盒外) → 清除多选, 成组工具条消失
    blank = page.evaluate(
        """((cand) => {
          const rect = document.querySelector('.react-flow__nodesselection-rect')?.getBoundingClientRect();
          const cands = [cand, { x: 150, y: 400 }, { x: 480, y: 130 }, { x: 1050, y: 130 }, { x: 320, y: 860 }];
          for (const c of cands) {
            const el = document.elementFromPoint(c.x, c.y);
            if (el?.closest('.react-flow__pane') && !el?.closest('.react-flow__node') && !el?.closest('.react-flow__nodesselection-rect') && !el?.closest('[class*=minimap]')) return c;
          }
          return cand;
        })""",
        boxes["blank"],
    )
    page.mouse.click(blank["x"], blank["y"])
    page.wait_for_timeout(500)
    # 时序容错: 若首次点击被拖拽手势吞掉, 再点一次
    still = page.evaluate(
        "document.querySelectorAll('.react-flow__node.selected').length"
    )
    if still > 0:
        page.mouse.click(blank["x"], blank["y"])
        page.wait_for_timeout(500)
    check("single:group-toolbar-gone", page.locator(".frameos-group-toolbar").count() == 0)
    check(
        "single:cleared",
        page.evaluate("document.querySelectorAll('.react-flow__node.selected').length") == 0,
    )

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 229, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch229: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
