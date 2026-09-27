#!/usr/bin/env python3

"""Verify Batch 257: ⌥拖拽复制 (alt-drag duplicate).

Source-sampled 2026-09-28 on frameos.cn (previously believed unsampleable):
holding ⌥ while dragging a node moves the original to the drop position and
creates an identically-titled duplicate offset by (+20, +15).

Checks (desktop 1440x900):
1. alt+drag a node → node count +1;
2. original sits at the drop position, duplicate at +20/+15 with same title;
3. duplicate is auto-selected;
4. ⌘Z removes the duplicate (history covers the copy), second ⌘Z reverts the move;
5. console/page errors clean.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright

from frameos_verify_common import attach_errors


ROOT = Path(__file__).resolve().parents[1]
BASE_URL = os.environ.get("LIBLIB_BASE_URL", "http://localhost:4317")
AUDIT_PATH = (
    ROOT
    / "docs"
    / "research"
    / "liblib-frameos-batch257-2026-09-28"
    / "runtime-audit.json"
)



def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool) -> None:
        assert ok, f"batch257 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/frameos/canvas/demo", wait_until="domcontentloaded", timeout=90000)
    page.wait_for_timeout(1500)

    count_before = page.evaluate("window.__frameos_store.getState().nodes.length")
    before_pos = page.evaluate(
        "window.__frameos_store.getState().nodes.find((n) => n.id === 'image-1').position"
    )
    center = page.evaluate(
        """(() => {
          const r = document.querySelector('.react-flow__node[data-id=\\'image-1\\']')?.getBoundingClientRect();
          return r ? { x: r.x + r.width / 2, y: r.y + r.height / 2 } : null;
        })()"""
    )
    check("setup:node-found", center is not None)

    # Alt + drag (+50, +40) via real input
    page.keyboard.down("Alt")
    page.mouse.move(center["x"], center["y"])
    page.mouse.down()
    steps = 8
    for i in range(1, steps + 1):
        page.mouse.move(center["x"] + 50 * i / steps, center["y"] + 40 * i / steps)
    page.mouse.up()
    page.keyboard.up("Alt")
    page.wait_for_timeout(600)

    after = page.evaluate(
        """(() => {
          const s = window.__frameos_store.getState();
          const orig = s.nodes.find((n) => n.id === 'image-1');
          const copies = s.nodes.filter((n) => n.id !== 'image-1' && n.data.title === orig.data.title);
          return {
            count: s.nodes.length,
            origPos: orig.position,
            copy: copies.length
              ? { id: copies[copies.length - 1].id, pos: copies[copies.length - 1].position, title: copies[copies.length - 1].data.title, selected: copies[copies.length - 1].selected }
              : null,
            selectedNodeId: s.selectedNodeId,
          };
        })()"""
    )
    check("alt:count-plus-one", after["count"] == count_before + 1)
    check("alt:copy-created", after["copy"] is not None)
    check(
        "alt:original-moved-to-drop",
        abs(after["origPos"]["x"] - before_pos["x"] - 50) < 15
        and abs(after["origPos"]["y"] - before_pos["y"] - 40) < 15,
    )
    check(
        "alt:copy-offset-20-15",
        after["copy"]
        and abs(after["copy"]["pos"]["x"] - after["origPos"]["x"] - 20) < 1
        and abs(after["copy"]["pos"]["y"] - after["origPos"]["y"] - 15) < 1,
    )
    check("alt:same-title", after["copy"] and after["copy"]["title"] == "图片节点1")
    check("alt:copy-selected", after["copy"] and after["selectedNodeId"] == after["copy"]["id"])

    # ⌘Z: remove the copy (history includes the duplicate step)
    page.keyboard.press("Meta+z")
    page.wait_for_timeout(400)
    undone = page.evaluate(
        """(() => {
          const s = window.__frameos_store.getState();
          return { count: s.nodes.length, hasCopy: s.nodes.some((n) => n.data.title === '图片节点1' && n.id !== 'image-1') };
        })()"""
    )
    check("undo:copy-removed", undone["count"] == count_before and not undone["hasCopy"])
    # second ⌘Z reverts the move
    page.keyboard.press("Meta+z")
    page.wait_for_timeout(400)
    reverted = page.evaluate(
        """(() => {
          const n = window.__frameos_store.getState().nodes.find((x) => x.id === 'image-1');
          return n.position;
        })()"""
    )
    check("undo:move-reverted", abs(reverted["x"] - before_pos["x"]) < 2 and abs(reverted["y"] - before_pos["y"]) < 2)

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 257, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch257: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
