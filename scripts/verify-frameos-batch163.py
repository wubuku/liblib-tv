#!/usr/bin/env python3

"""Verify Batch 163: FrameOS node search (搜索节点).

2026-09-23 source re-sampling (docs/user-manual/frameos-canvas
SOURCE_OBSERVATIONS.md §13.7 / shot 12): the bottom toolbar has a 搜索节点
button (⌘F also works) opening a search input (placeholder 搜索节点名称)
that live-filters nodes by name, shows 无匹配节点 on no match, and clicking
a result selects the node and zoom-focuses the viewport (100% → 273%).
Verifies the button, ⌘F, live filtering, empty state, result click select +
zoom, and close paths.
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
    / "liblib-frameos-batch163-2026-09-23"
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
        assert ok, f"batch163 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/frameos/canvas/demo", wait_until="domcontentloaded")
    page.wait_for_timeout(1200)

    zoom0 = page.evaluate(
        "window.__frameos_store ? null : null"
    )  # placeholder; zoom read via toolbar text below
    _ = zoom0
    read_zoom = "document.body.innerText.match(/\\d+%/)?.[0]"

    # 工具条按钮打开搜索
    page.locator("button[aria-label='搜索节点']").click()
    page.wait_for_timeout(300)
    search = page.locator("[data-frameos-node-search]")
    check("search:opens", search.is_visible())
    input_box = page.locator("[data-frameos-node-search-input]")
    check(
        "search:placeholder",
        input_box.get_attribute("placeholder") == "搜索节点名称",
    )

    # 空查询无结果列表; 无匹配态
    input_box.fill("图片")
    page.wait_for_timeout(300)
    results = page.locator("[data-frameos-node-search-result]")
    check("search:filters", results.count() >= 1)

    input_box.fill("ZZZ不存在")
    page.wait_for_timeout(300)
    check(
        "search:no-match",
        page.locator("[data-frameos-node-search-empty]").is_visible(),
    )

    # 回到有效查询 → 点击结果 → 选中 + 缩放聚焦 (等待缩放动画)
    input_box.fill("图片")
    page.wait_for_timeout(300)
    results.first.click()
    page.wait_for_timeout(1400)
    selected_id = page.evaluate(
        "window.__frameos_store.getState().selectedNodeId"
    )
    check("search:result-selects", bool(selected_id))
    zoom_text = page.evaluate(read_zoom)
    check("search:zoom-focus", zoom_text is not None and int(zoom_text.rstrip("%")) > 200)

    # Esc 关闭
    page.keyboard.press("Escape")
    page.wait_for_timeout(300)
    check("search:esc-closes", page.locator("[data-frameos-node-search]").count() == 0)

    # ⌘F 打开
    page.keyboard.press("Meta+f")
    page.wait_for_timeout(300)
    check("search:cmdf-opens", page.locator("[data-frameos-node-search]").is_visible())
    page.keyboard.press("Escape")
    page.wait_for_timeout(200)

    # 回归: 适应画布把聚焦缩放拉回适配值 (不再保持聚焦放大)
    page.locator("button[aria-label='适应画布']").click()
    page.wait_for_timeout(700)
    zoom_fit = page.evaluate(read_zoom)
    check(
        "regression:fit-view",
        zoom_fit is not None and int(zoom_fit.rstrip("%")) < 200,
    )

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 163, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch163: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
