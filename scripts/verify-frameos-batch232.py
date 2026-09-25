#!/usr/bin/env python3

"""Verify Batch 232: multi-selection group drag.

Source sampling 2026-09-26: with 3 nodes marquee-selected, dragging one
selected node moves ALL of them together (same delta); ⌘Z restores.

The clone relies on xyflow's native selection drag; this verifies it end to
end after the Batch 229 selection-sync change (select changes bypass the
single-selection re-apply).

Checks:
1. marquee two nodes → both selected;
2. dragging one selected node moves BOTH by the same delta;
3. ⌘Z restores the pre-drag positions;
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
    / "liblib-frameos-batch232-2026-09-26"
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


def node_positions(page: Page) -> dict:
    return page.evaluate(
        """(() => {
          const pos = {};
          [...document.querySelectorAll('.react-flow__node')].forEach((n) => {
            pos[n.getAttribute('data-id')] = {
              x: Math.round(n.getBoundingClientRect().left),
              y: Math.round(n.getBoundingClientRect().top),
            };
          });
          return pos;
        })"""
    )


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool) -> None:
        assert ok, f"batch232 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/frameos/canvas/demo", wait_until="domcontentloaded", timeout=90000)
    page.wait_for_timeout(1500)

    # 框选 image-1 + image-2 (同 batch229 几何)
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
    selected_ids = page.evaluate(
        """[...document.querySelectorAll('.react-flow__node.selected')].map((n) => n.getAttribute('data-id'))"""
    )
    check("marquee:multi-selected", len(selected_ids) >= 2)

    before = node_positions(page)

    # 拖拽其中一个选中节点 (顶部边缘避开替换按钮/handle)
    drag_from = page.evaluate(
        """((ids) => {
          const n = document.querySelector(`.react-flow__node[data-id='${ids[0]}']`);
          const r = n.getBoundingClientRect();
          return { x: Math.round(r.left + 40), y: Math.round(r.top + 15) };
        })""",
        selected_ids,
    )
    page.mouse.move(drag_from["x"], drag_from["y"])
    page.mouse.down()
    page.mouse.move(drag_from["x"] + 25, drag_from["y"] + 25, steps=3)
    page.mouse.move(drag_from["x"] + 50, drag_from["y"] + 50, steps=3)
    page.mouse.up()
    page.wait_for_timeout(600)

    after = node_positions(page)
    deltas = []
    for nid in selected_ids:
        dx = after[nid]["x"] - before[nid]["x"]
        dy = after[nid]["y"] - before[nid]["y"]
        deltas.append((dx, dy))
    check(
        "drag:both-moved",
        all(dx > 30 and dy > 30 for dx, dy in deltas),
    )
    check(
        "drag:same-delta",
        len(set(deltas)) == 1,
    )

    # ⌘Z 恢复
    page.keyboard.press("Meta+z")
    page.wait_for_timeout(600)
    restored = node_positions(page)
    check(
        "undo:restores-positions",
        all(
            restored[nid] == before[nid] for nid in selected_ids
        ),
    )

    # 清理选择
    page.evaluate("window.__frameos_store.setState({ selectedNodeId: null })")

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 232, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch232: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
