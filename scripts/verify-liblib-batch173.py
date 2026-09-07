#!/usr/bin/env python3

"""Verify Batch 173: node right-click context menu + model menu selected bg.

Source evidence (2026-09-07 CDP samples):
- node right-click opens a DIFFERENT menu than the blank pane (Batch 172
  errata): 保存到我的资产 / 创建主体 (both disabled on an empty node) |
  复制节点⌘C / 创建副本⌘D / 粘贴⌘V / 删除⌘⌫ | 复制到剪贴板, with two 0.5px
  dividers and 14px "?" info glyphs after 复制节点/创建副本 labels.
- menu 删除 action removes the node without a confirm dialog (source, image
  and video nodes).
- model menu selected row background measured rgba(255,255,255,0.15)
  (container 360 wide, rows h-52; height system re-alignment deferred).
- source default model variance: fresh node showed Seedance 2.0 VIP today
  vs 2.5 earlier today (Batch 158) — account last-used state; clone keeps 2.5.
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
    / "liblib-canvas-batch173-2026-09-07"
    / "runtime-audit.json"
)

EXPECTED_NODE_ITEMS = [
    "保存到我的资产",
    "创建主体",
    "复制节点",
    "创建副本",
    "粘贴",
    "删除",
    "复制到剪贴板",
]


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
        assert ok, f"batch173 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(BASE_URL, wait_until="networkidle")
    page.wait_for_timeout(500)

    menu = page.locator("[data-canvas-context-menu]")
    baseline_nodes = page.locator(".react-flow__node").count()

    # create a video node
    page.get_by_role("button", name="添加节点").click()
    page.wait_for_timeout(300)
    page.locator("[data-liblib-overlay='add-node']").get_by_role("button", name="视频", exact=True).click()
    page.wait_for_timeout(1000)
    check("node:created", page.locator(".react-flow__node").count() == baseline_nodes + 1)

    # drag the created node aside (it spawns at flow center over preset nodes)
    created = page.locator(".react-flow__node-video").last
    cb = created.bounding_box()
    sx, sy = cb["x"] + cb["width"] / 2, cb["y"] + 12
    page.mouse.move(sx, sy)
    page.mouse.down()
    page.mouse.move(sx + 300, sy + 220, steps=8)
    page.mouse.up()
    page.wait_for_timeout(500)

    # right-click the video node -> node variant menu
    node = page.locator(".react-flow__node-video").last
    node.click(button="right")
    page.wait_for_timeout(400)
    check("menu:node-variant", menu.count() == 1 and menu.get_attribute("data-canvas-context-variant") == "node")

    items = page.eval_on_selector_all(
        "[data-canvas-context-menu] [data-canvas-context-item]",
        "els => els.map(el => el.getAttribute('data-canvas-context-item'))",
    )
    check("menu:seven-items-order", items == EXPECTED_NODE_ITEMS)

    shortcuts = menu.locator("span", has_text="⌘").all_inner_texts()
    check("menu:shortcuts", sorted(s.strip() for s in shortcuts) == sorted(["⌘C", "⌘D", "⌘V", "⌘⌫"]))

    dividers = page.locator("[data-canvas-context-menu] > div").count()
    check("menu:two-dividers", dividers == 2)

    def state(label: str) -> tuple[bool, int]:
        handle = page.locator(f"[data-canvas-context-item='{label}']")
        return handle.is_disabled(), handle.locator("svg").count()

    save_disabled, _ = state("保存到我的资产")
    subject_disabled, _ = state("创建主体")
    copy_disabled, copy_svg = state("复制节点")
    dup_disabled, dup_svg = state("创建副本")
    del_disabled, _ = state("删除")
    clip_disabled, _ = state("复制到剪贴板")
    check(
        "menu:disabled-and-glyphs",
        save_disabled
        and subject_disabled
        and (not copy_disabled)
        and (not dup_disabled)
        and (not del_disabled)
        and (not clip_disabled)
        and copy_svg == 1
        and dup_svg == 1,
    )

    page.keyboard.press("Escape")
    page.wait_for_timeout(300)
    check("menu:escape-closes", menu.count() == 0)

    # 创建副本 duplicates via store (use .last — topmost created node)
    page.locator(".react-flow__node-video").last.click(button="right")
    page.wait_for_timeout(300)
    page.locator("[data-canvas-context-item='创建副本']").click()
    page.wait_for_timeout(600)
    check("duplicate:adds-node", menu.count() == 0 and page.locator(".react-flow__node").count() == baseline_nodes + 2)

    # 删除 removes the right-clicked node
    page.locator(".react-flow__node-video").last.click(button="right")
    page.wait_for_timeout(300)
    page.locator("[data-canvas-context-item='删除']").click()
    page.wait_for_timeout(600)
    check("delete:removes-node", page.locator(".react-flow__node").count() == baseline_nodes + 1)

    # model menu selected row background (Batch 173 measured white/15%)
    page.locator('.react-flow__node[data-id="v-UGQZzZOpbv"]').click(force=True)
    page.wait_for_timeout(300)
    page.locator("[data-video-model-trigger]").click(force=True)
    page.wait_for_timeout(400)
    # Tailwind 4 compiles bg-white/[0.15] to an oklab() color; assert the
    # class plus the 0.15 alpha instead of an sRGB literal.
    sel_opt = page.locator('[data-video-model-option][aria-pressed="true"]')
    sel_class = sel_opt.get_attribute("class") or ""
    sel_bg = sel_opt.evaluate("el => getComputedStyle(el).backgroundColor")
    check("model-menu:selected-bg", "bg-white/[0.15]" in sel_class and "0.15" in sel_bg)
    page.keyboard.press("Escape")

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 173, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch173: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
