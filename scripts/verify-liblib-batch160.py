#!/usr/bin/env python3

"""Verify Batch 160: 5min chip selects long-video mode + panel empty-state alignment.

Source evidence (2026-09-07, fresh-node full-panel DOM dump):
- After the 5分钟超长视频 chip, the mode trigger shows 超长视频 and credits
  show 14700 = 300 x 49 (long-video formula) — the chip selects the whole
  long-video mode, not just Auto+300s.
- Fresh panel has NO reference slot row (toolbar feeds straight into the
  prompt) and NO 「新功能」 bar.
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
    / "liblib-canvas-batch160-2026-09-07"
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
        assert ok, f"batch160 check failed: {name}"
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
    check("panel:open", vg.is_visible())
    check("panel:no-new-feature", page.locator("[data-video-new-feature]").count() == 0)
    # 演示草稿带引用 → 槽行仍在（非空态）
    check("panel:slots-present", page.locator("[data-video-generation-panel] .cursor-grab").count() >= 1)

    # 5分钟超长视频芯片（节点卡内）→ mode 超长视频 + 积分 14700
    attempts = page.locator("[data-video-attempts]")
    attempts.locator("[data-video-attempt='5分钟超长视频']").click()
    page.wait_for_timeout(500)
    mode = vg.locator("[data-video-mode-trigger]")
    check("chip:mode-long", mode.inner_text().strip() == "超长视频")
    credits = vg.locator("[data-video-credits]")
    check("chip:credits-14700", credits.inner_text().strip().endswith("14700"))
    check(
        "chip:params-auto-300",
        "Auto · 720P · 300s" in (vg.locator("[data-video-params-trigger]").inner_text()),
    )

    # 取消芯片 → 回常规模式 + 时长钳制 ≤30
    attempts.locator("[data-video-attempt='5分钟超长视频']").click()
    page.wait_for_timeout(400)
    check("deselect:mode-back", mode.inner_text().strip() == "文生视频")
    label = vg.locator("[data-video-params-trigger]").inner_text()
    seconds = int(label.split("·")[2].strip().replace("s", ""))
    check("deselect:clamp-30", seconds <= 30)

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 160, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch160: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
