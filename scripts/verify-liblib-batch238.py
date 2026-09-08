#!/usr/bin/env python3
"""Verify Batch 238: model flat-rate pricing table.

Source evidence (2026-09-09, docs/research/liblib-canvas-batch238-2026-09-09/):
- Decisive in-session A/B (t4-decisive-169.png): 2.5·16:9·5s = 230 =
  2.5·Auto·5s — ratio does not change price within a model; pricing is a
  flat per-model rate (2.5→46/s, 2.0 VIP→27/s, 2.0 Fast VIP→22/s,
  2.0 Mini→16/s at 80/5s; long pipeline stays 49/s).
- Batch 130's 135 reading belongs to the 2.0 VIP state (27×5 exactly).
- Seedance 2.0 Mini: trigger label "2.0 Mini", resolution list [480P, 720P].
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
    / "liblib-canvas-batch238-2026-09-09"
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
        assert ok, f"batch238 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto("http://localhost:4317", wait_until="networkidle")
    page.wait_for_timeout(500)

    # fresh video node (batch176 recipe)
    page.get_by_role("button", name="添加节点").click()
    page.wait_for_timeout(300)
    page.locator("[data-liblib-overlay='add-node']").get_by_role("button", name="视频", exact=True).click()
    page.wait_for_timeout(1000)

    model_trigger = page.locator("[data-video-model-trigger]")
    params_trigger = page.locator("[data-video-params-trigger]")
    credits = page.locator("[data-video-credits]")

    # ---- default state: 2.5 / 16:9 / 5s / 1个 → 230 (was 135 under ratio-based formula)
    check("default:credits-230", credits.inner_text().strip().endswith("230"))

    # ---- ratio independence within 2.5: 21:9 also 230, back to 16:9 also 230
    params_trigger.click()
    page.wait_for_timeout(200)
    # ratio tiles sit at the params-menu top where the node toolbar can
    # z-overlap; force-click is the same target a user would hit
    page.locator('[data-video-ratio-option="21:9"]').click(force=True)
    page.wait_for_timeout(200)
    check("ratio:21x9-credits-230", credits.inner_text().strip().endswith("230"))
    page.locator('[data-video-ratio-option="16:9"]').click(force=True)
    page.wait_for_timeout(200)
    check("ratio:169-credits-230", credits.inner_text().strip().endswith("230"))
    params_trigger.click()
    page.wait_for_timeout(200)

    # ---- 2.0 Mini: rate 16/s → 80, 2 resolutions, trigger "2.0 Mini"
    model_trigger.click()
    page.locator('[data-video-model-option="2.0 Mini"]').click()
    page.wait_for_timeout(300)
    check("mini:trigger-label", model_trigger.inner_text().strip() == "2.0 Mini")
    check("mini:credits-80", credits.inner_text().strip().endswith("80"))
    params_trigger.click()
    page.wait_for_timeout(200)
    res_options = page.locator("[data-video-resolution-option]")
    check("mini:2-resolutions", res_options.count() == 2)
    check(
        "mini:only-480-720",
        page.locator('[data-video-resolution-option="480P"]').count() == 1
        and page.locator('[data-video-resolution-option="720P"]').count() == 1
        and page.locator('[data-video-resolution-option="1080P"]').count() == 0,
    )
    params_trigger.click()
    page.wait_for_timeout(200)

    # ---- 2.0 VIP: 27/s → 135 at 5s (batch130's reading re-homed)
    model_trigger.click()
    page.locator('[data-video-model-option="2.0 VIP"]').click()
    page.wait_for_timeout(300)
    check("vip:credits-135", credits.inner_text().strip().endswith("135"))

    # ---- back to 2.5: 230
    model_trigger.click()
    page.locator('[data-video-model-option="2.5"]').click()
    page.wait_for_timeout(300)
    check("back25:credits-230", credits.inner_text().strip().endswith("230"))

    # ---- Fast VIP: 22/s → 110
    model_trigger.click()
    page.locator('[data-video-model-option="2.0 Fast VIP"]').click()
    page.wait_for_timeout(300)
    check("fast:credits-110", credits.inner_text().strip().endswith("110"))

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 238, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch238: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
