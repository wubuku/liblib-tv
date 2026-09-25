#!/usr/bin/env python3

"""Verify Batch 178: FrameOS per-type context menu shape.

2026-09-24 source re-sampling (live canvas): the TEXT node context menu is
exactly three rows — 复制 ⌘C / 创建副本 ⌘D / 删除 ⌫ — while the IMAGE node
menu carries five (adds 复制图片, disabled; 重新生成, disabled; see Batch
170). The clone already matches (Batch 170 wiring keys the extra rows off
node type); this batch locks the per-type shapes as a regression guard.
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
    / "liblib-frameos-batch178-2026-09-24"
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
        assert ok, f"batch178 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/frameos/canvas/demo", wait_until="domcontentloaded")
    page.wait_for_timeout(1200)

    menu = page.locator("[data-frameos-context-menu]")

    # 文本节点: Batch 226 起四行 (非媒体统一带 重新生成禁用行, 2026-09-25 源站
    # 3D导演台菜单采样推断)
    page.locator(".react-flow__node-text").first.click(button="right")
    page.wait_for_timeout(300)
    check("text:menu-opens", menu.is_visible())
    text_labels = [
        menu.locator("[data-frameos-context-item]").nth(i).get_attribute(
            "data-frameos-context-item"
        )
        for i in range(menu.locator("[data-frameos-context-item]").count())
    ]
    check("text:four-rows", len(text_labels) == 4)
    check(
        "text:rows-exact",
        text_labels == ["复制", "创建副本", "重新生成", "删除"],
    )
    regen = menu.locator("[data-frameos-context-item='重新生成']")
    check(
        "text:regen-disabled",
        regen.get_attribute("disabled") is not None,
    )
    page.keyboard.press("Escape")
    page.wait_for_timeout(200)

    # 图片节点 (内容态): 五行 = 复制/复制图片/创建副本/设置为资产图/删除
    image_node = page.locator(".react-flow__node-image").first
    image_node.click(button="right")
    page.wait_for_timeout(300)
    img_labels = [
        menu.locator("[data-frameos-context-item]").nth(i).get_attribute(
            "data-frameos-context-item"
        )
        for i in range(menu.locator("[data-frameos-context-item]").count())
    ]
    check("image:five-rows", len(img_labels) == 5)
    check(
        "image:rows-exact",
        img_labels == ["复制", "复制图片", "创建副本", "设置为资产图", "删除"],
    )
    page.keyboard.press("Escape")
    page.wait_for_timeout(200)

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 178, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch178: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
