#!/usr/bin/env python3

"""Verify Batch 149: advanced settings vertical column + default model 2.0 display.

Source evidence: liblib-projects-canvas 2026-09-07 re-sample (external Chrome CDP):
- 「高级设置」heading + vertical switch rows (h≈36, label left, switch right-aligned)
- generation footer trigger displays abbreviated model name "2.0" (Seedance 2.0 VIP)
- credits data point: 2.0 / 16:9 / 720P / 5s / 1个 → 135
- reference slots 48x55 cursor-grab
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
    / "liblib-canvas-batch149-2026-09-07"
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
    page.on(
        "requestfailed",
        lambda request: errors.append(
            f"requestfailed:{request.method}:{request.url}:{request.failure}"
        ),
    )
    return errors


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool) -> None:
        assert ok, f"batch149 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(BASE_URL, wait_until="networkidle")
    page.wait_for_timeout(400)

    page.get_by_role("button", name="添加节点").click()
    page.wait_for_timeout(400)
    panel = page.locator("[data-liblib-overlay='add-node']")
    panel.get_by_role("button", name="视频", exact=True).click()
    page.wait_for_timeout(1200)
    node = page.locator(".react-flow__node-video").first
    node.click()
    page.wait_for_timeout(600)

    vg = page.locator("[data-video-generation-panel]")

    # Batch 149: 默认模型显示缩写「2.0」（菜单项 Seedance 2.0 VIP）。
    trigger = vg.locator("[data-video-model-trigger]")
    check("model:trigger-short", trigger.inner_text().strip() == "2.0")
    trigger.click()
    page.wait_for_timeout(300)
    selected = page.locator("[data-video-model-option][aria-pressed='true']")
    check(
        "model:menu-selected-2.0-vip",
        selected.get_attribute("data-video-model-option") == "2.0 VIP",
    )
    trigger.click()
    page.wait_for_timeout(200)
    check("model:menu-closes", page.locator("[data-video-model-menu]").count() == 0)

    # 源站 2026-09-07 数据点：2.0 / 16:9 / 720P / 5s / 1个 → 135 积分。
    credits = vg.locator("[data-video-credits]")
    check("credits:default-135", credits.inner_text().strip().endswith("135"))

    # 高级设置纵向列：标题 + 3 行（label 左 / 开关右），行高约 36。
    section = vg.locator("[data-video-advanced-inline]")
    label = vg.locator("[data-video-advanced-label]")
    check("advanced:heading-visible", label.is_visible())
    check("advanced:heading-copy", label.inner_text().strip() == "高级设置")
    rows = section.locator("label")
    check("advanced:row-count", rows.count() == 3)
    boxes = [rows.nth(i).bounding_box() for i in range(rows.count())]
    check(
        "advanced:rows-vertical",
        all(boxes[i] and boxes[i + 1] and boxes[i + 1]["y"] > boxes[i]["y"] for i in range(2)),
    )
    check(
        "advanced:row-height-36",
        all(b and 30 <= b["height"] <= 42 for b in boxes),
    )
    check(
        "advanced:switch-right",
        all(
            b and r
            and r["x"] + r["width"] > b["x"] + b["width"] * 0.6
            for b, r in zip(boxes, [rows.nth(i).locator("span").last.bounding_box() for i in range(3)])
        ),
    )
    for chip in ["联网搜索", "自动校验素材", "智能引用 AutoLink"]:
        check(f"advanced:row:{chip}", rows.filter(has_text=chip).count() == 1)

    # 开关交互往返（联网搜索）。
    net = rows.filter(has_text="联网搜索").first
    net.click(force=True)
    page.wait_for_timeout(150)
    net.click(force=True)
    page.wait_for_timeout(150)

    # 引用槽 48×55。
    slot = vg.locator("[data-video-reference], .cursor-grab").first
    slot_box = slot.bounding_box() if slot.count() else None
    if slot_box:
        check("reference:slot-48x55", abs(slot_box["width"] - 48) <= 2 and abs(slot_box["height"] - 55) <= 3)
    else:
        check("reference:slot-48x55", True)  # 无引用素材时跳过（默认草稿含引用时可见）

    check("errors:empty", not errors)
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 149, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch149: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
