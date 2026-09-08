#!/usr/bin/env python3
"""Verify Batch 236: model-switch resets long-video state; 4K on 2.0 VIP only;
model-aware Auto credits.

Source evidence (2026-09-09, docs/research/liblib-canvas-batch236-2026-09-09/):
- 2.5 + 超长视频 + Auto·720P·300s·1个 → 14700; switching to Seedance 2.0 VIP
  resets mode to 文生视频, duration 300→15s, clears the attempt chip highlight
  (p2-after-20vip.png), trigger relabels to "2.0", credits 405 (27/s).
- Switching back to 2.5 keeps 文生视频, credits 690 (46/s) — same params A/B.
- Resolution list: 2.0 VIP shows 480P/720P/1080P/4K (p3), 2.5 shows 3 options
  (p6). Ratio grid stays 7 tiles with Auto in both (reconfirms Batch 190).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = (
    ROOT
    / "docs"
    / "research"
    / "liblib-canvas-batch236-2026-09-09"
    / "runtime-audit.json"
)

NODE_ID = "v-UGQZzZOpbv"


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
        assert ok, f"batch236 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto("http://localhost:4317", wait_until="networkidle")
    page.wait_for_timeout(500)

    # fresh video node + long chip (batch176 recipe)
    page.get_by_role("button", name="添加节点").click()
    page.wait_for_timeout(300)
    page.locator("[data-liblib-overlay='add-node']").get_by_role("button", name="视频", exact=True).click()
    page.wait_for_timeout(1000)

    model_trigger = page.locator("[data-video-model-trigger]")
    mode_trigger = page.locator("[data-video-mode-trigger]")
    params_trigger = page.locator("[data-video-params-trigger]")
    credits = page.locator("[data-video-credits]")

    # ---- long-video state via attempt chip (batch 160/176 contract)
    page.locator('[data-video-attempt="5分钟超长视频"]').click()
    page.wait_for_timeout(300)
    check("long:model-25", model_trigger.inner_text().strip() == "2.5")
    check("long:mode", mode_trigger.inner_text().strip() == "超长视频")
    check("long:credits-14700", credits.inner_text().strip().endswith("14700"))
    check(
        "long:chip-selected",
        page.locator('[data-video-attempt="5分钟超长视频"]')
        .get_attribute("aria-pressed")
        == "true",
    )

    # ---- switch model 2.5 -> 2.0 VIP: state reset (source p2)
    model_trigger.click()
    page.locator('[data-video-model-option="2.0 VIP"]').click()
    page.wait_for_timeout(300)
    check("vip:trigger-20", model_trigger.inner_text().strip() == "2.0")
    check("vip:mode-reset", mode_trigger.inner_text().strip() == "文生视频")
    check(
        "vip:duration-15s",
        params_trigger.inner_text().strip() == "Auto · 720P · 15s · 1个 ·",
    )
    check("vip:credits-405", credits.inner_text().strip().endswith("405"))
    check(
        "vip:chip-cleared",
        page.locator('[data-video-attempt="5分钟超长视频"]')
        .get_attribute("aria-pressed")
        == "false",
    )

    # ---- params menu under 2.0 VIP: 4 resolutions incl 4K, ratio grid 7 with Auto
    params_trigger.click()
    page.wait_for_timeout(200)
    menu = page.locator("[data-video-params-menu]")
    check("vip:params-open", menu.count() == 1)
    res_options = page.locator("[data-video-resolution-option]")
    check("vip:4-resolutions", res_options.count() == 4)
    check("vip:has-4k", page.locator('[data-video-resolution-option="4K"]').count() == 1)
    ratio_options = page.locator("[data-video-ratio-option]")
    check("vip:ratio-7-tiles", ratio_options.count() == 7)
    check(
        "vip:ratio-auto-selected",
        page.locator('[data-video-ratio-option="Auto"]').get_attribute("aria-pressed")
        == "true",
    )
    params_trigger.click()
    page.wait_for_timeout(200)

    # ---- switch back to 2.5: stays 文生视频, Auto credits 46/s -> 690 (source p5)
    model_trigger.click()
    page.locator('[data-video-model-option="2.5"]').click()
    page.wait_for_timeout(300)
    check("back25:trigger", model_trigger.inner_text().strip() == "2.5")
    check("back25:mode-stays", mode_trigger.inner_text().strip() == "文生视频")
    check("back25:credits-690", credits.inner_text().strip().endswith("690"))

    # ---- params menu under 2.5: 3 resolutions, no 4K
    params_trigger.click()
    page.wait_for_timeout(200)
    check("back25:3-resolutions", page.locator("[data-video-resolution-option]").count() == 3)
    check(
        "back25:no-4k",
        page.locator('[data-video-resolution-option="4K"]').count() == 0,
    )
    params_trigger.click()
    page.wait_for_timeout(200)

    # ---- 4K clamp: pick 4K on 2.0 VIP, then switch to 2.5 -> clamps to 1080P
    model_trigger.click()
    page.locator('[data-video-model-option="2.0 VIP"]').click()
    page.wait_for_timeout(200)
    params_trigger.click()
    page.wait_for_timeout(200)
    page.locator('[data-video-resolution-option="4K"]').click()
    page.wait_for_timeout(200)
    check(
        "clamp:4k-selected",
        page.locator('[data-video-resolution-option="4K"]').get_attribute("aria-pressed")
        == "true",
    )
    params_trigger.click()
    page.wait_for_timeout(200)
    model_trigger.click()
    page.locator('[data-video-model-option="2.5"]').click()
    page.wait_for_timeout(300)
    check(
        "clamp:resolution-1080p",
        params_trigger.inner_text().strip() == "Auto · 1080P · 15s · 1个 ·",
    )
    # clamped non-16:9 ratio on 2.5 keeps 46/s: 15 * 46 = 690
    check("clamp:credits-690", credits.inner_text().strip().endswith("690"))

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 236, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch236: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
