#!/usr/bin/env python3

"""Verify Batch 172: canvas right-click context menu.

Source evidence (2026-09-07 CDP sample, liblib.tv canvas):
- full-screen transparent catcher + menu fixed at the click point;
  container `min-width: 196px; padding: 8px; gap: 4px; border-radius: 16px;
  background: #262626; border: 0.5px solid #363636`.
- six items in order: 上传 / 保存到我的资产 / 添加节点 / 撤销⌘Z / 重做⇧⌘Z /
  粘贴⌘V, with two 0.5px dividers (after 添加节点 and after 重做).
- blank canvas: 保存到我的资产, 撤销, 重做 disabled (opacity 0.3).
- same menu for blank-pane and node right-click (earlier source sample).
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
    / "liblib-canvas-batch172-2026-09-07"
    / "runtime-audit.json"
)

EXPECTED_ITEMS = ["上传", "保存到我的资产", "添加节点", "撤销", "重做", "粘贴"]


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


def blank_point(page: Page) -> tuple[int, int]:
    boxes = page.evaluate(
        """() => {
        const out = [];
        document.querySelectorAll('.react-flow__node').forEach(n => {
          const r = n.getBoundingClientRect();
          out.push([r.x, r.y, r.width, r.height]);
        });
        return out;
        }"""
    )
    for candidate in [(1000, 300), (1100, 350), (900, 600), (700, 250), (1150, 500)]:
        if all(
            not (x - 12 <= candidate[0] <= x + w + 12 and y - 12 <= candidate[1] <= y + h + 12)
            for x, y, w, h in boxes
        ):
            return candidate
    return (1000, 300)


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool) -> None:
        assert ok, f"batch172 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(BASE_URL, wait_until="networkidle")
    page.wait_for_timeout(500)

    menu = page.locator("[data-canvas-context-menu]")
    check("menu:closed-initial", menu.count() == 0)

    # --- blank-pane right click ---
    bx, by = blank_point(page)
    page.mouse.click(bx, by, button="right")
    page.wait_for_timeout(400)
    check("menu:opens-on-pane", menu.count() == 1)

    box = menu.bounding_box()
    check("menu:width-196", box is not None and abs(box["width"] - 196) <= 2)
    check("menu:position-at-click", box is not None and abs(box["x"] - bx) <= 2 and abs(box["y"] - by) <= 2)

    items = page.eval_on_selector_all(
        "[data-canvas-context-menu] [data-canvas-context-item]",
        "els => els.map(el => el.getAttribute('data-canvas-context-item'))",
    )
    check("menu:six-items-order", items == EXPECTED_ITEMS)

    shortcuts = menu.locator("span", has_text="⌘").all_inner_texts()
    check("menu:shortcuts", sorted(s.strip() for s in shortcuts) == sorted(["⌘Z", "⇧⌘Z", "⌘V"]))

    dividers = page.locator("[data-canvas-context-menu] > div").count()
    check("menu:two-dividers", dividers == 2)

    def item_state(label: str) -> tuple[bool, float]:
        handle = page.locator(f"[data-canvas-context-item='{label}']")
        disabled = handle.is_disabled()
        opacity = handle.evaluate("el => parseFloat(getComputedStyle(el).opacity)")
        return disabled, opacity

    up_disabled, _ = item_state("上传")
    save_disabled, save_opacity = item_state("保存到我的资产")
    add_disabled, _ = item_state("添加节点")
    undo_disabled, _ = item_state("撤销")
    redo_disabled, _ = item_state("重做")
    paste_disabled, _ = item_state("粘贴")
    check(
        "menu:blank-canvas-disabled",
        (not up_disabled)
        and save_disabled
        and (not add_disabled)
        and undo_disabled
        and redo_disabled
        and (not paste_disabled)
        and save_opacity < 0.4,
    )

    page.keyboard.press("Escape")
    page.wait_for_timeout(300)
    check("menu:escape-closes", menu.count() == 0)

    # --- 添加节点 item opens the add-node panel ---
    bx, by = blank_point(page)
    page.mouse.click(bx, by, button="right")
    page.wait_for_timeout(300)
    page.locator("[data-canvas-context-item='添加节点']").click()
    page.wait_for_timeout(400)
    check("menu:add-node-opens-panel", menu.count() == 0 and page.locator("[data-liblib-overlay='add-node']").count() == 1)
    page.mouse.click(150, 120)
    page.wait_for_timeout(300)

    # --- node right-click + undo wiring ---
    baseline_nodes = page.locator(".react-flow__node").count()
    page.get_by_role("button", name="添加节点").click()
    page.wait_for_timeout(300)
    page.locator("[data-liblib-overlay='add-node']").get_by_role("button", name="视频", exact=True).click()
    page.wait_for_timeout(1000)
    added_nodes = page.locator(".react-flow__node").count()
    check("node:created", added_nodes == baseline_nodes + 1)

    # Batch 173 errata: node right-click opens the 7-item node-variant menu
    # (asserted in batch173); undo is verified on the pane menu here.
    node = page.locator(".react-flow__node-video").first
    node.click(button="right")
    page.wait_for_timeout(400)
    check(
        "menu:opens-on-node",
        menu.count() == 1 and menu.get_attribute("data-canvas-context-variant") == "node",
    )
    page.keyboard.press("Escape")
    page.wait_for_timeout(300)

    bx, by = blank_point(page)
    page.mouse.click(bx, by, button="right")
    page.wait_for_timeout(400)
    check(
        "menu:pane-undo-enabled-after-change",
        menu.count() == 1 and not page.locator("[data-canvas-context-item='撤销']").is_disabled(),
    )
    page.locator("[data-canvas-context-item='撤销']").click()
    page.wait_for_timeout(500)
    check("undo:removes-node", page.locator(".react-flow__node").count() == baseline_nodes and menu.count() == 0)

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 172, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch172: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
