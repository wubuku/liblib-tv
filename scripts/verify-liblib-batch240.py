#!/usr/bin/env python3
"""Verify Batch 240: extended per-model rate tables (720P base + 1080P
overrides), model default resolution, trigger label special case.

Source evidence (2026-09-09, docs/research/liblib-canvas-batch240-2026-09-09/):
- 16:9·720P·5s·1个 controlled readings (round-1 loop, chip-verified):
  Minimax H3 Max 60, Wan 3.0 Prime 45, Wan 2.7 65, Kling O3 55,
  Kling 3.0 Turbo 60, Vidu Q2 40, Vidu Q3 Pro 50, Hailuo 2.3 Fast 24,
  Hailuo 02 36.
- Resolution affects price: Seedance 1.5 Pro 720P=40 vs 1080P=90 (reversible
  A/B); Seedance 1.0 Pro 1080P=75; Seedance 1.0 Lite 1080P=30.
- Switching to Seedance 1.5 Pro resets resolution to 1080P (model default).
- Trigger label special case: Seedance 1.5 Pro shows "Seedance1.5".
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
    / "liblib-canvas-batch240-2026-09-09"
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
        assert ok, f"batch240 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto("http://localhost:4317", wait_until="networkidle")
    page.wait_for_timeout(500)

    # fresh video node + first-frame chip → panel (16:9·720P·5s·1个 baseline)
    page.get_by_role("button", name="添加节点").click()
    page.wait_for_timeout(300)
    page.locator("[data-liblib-overlay='add-node']").get_by_role("button", name="视频", exact=True).click()
    page.wait_for_timeout(1000)
    page.locator('[data-video-attempt="首帧生成视频"]').click()
    page.wait_for_timeout(300)

    model_trigger = page.locator("[data-video-model-trigger]")
    credits = page.locator("[data-video-credits]")
    params_trigger = page.locator("[data-video-params-trigger]")

    def switch_model(option: str) -> None:
        model_trigger.click()
        page.locator(f'[data-video-model-option="{option}"]').click()
        page.wait_for_timeout(300)

    # ---- 720P table readings (baseline chip 16:9·720P·5s·1个)
    switch_model("Minimax H3 Max")
    check("h3max:credits-60", credits.inner_text().strip().endswith("60"))
    switch_model("Wan 3.0 Prime")
    check("wan3prime:credits-45", credits.inner_text().strip().endswith("45"))
    switch_model("Kling O3")
    check("klingo3:credits-55", credits.inner_text().strip().endswith("55"))
    switch_model("Vidu Q2")
    check("viduq2:credits-40", credits.inner_text().strip().endswith("40"))
    switch_model("Hailuo 02")
    check("hailuo02:credits-36", credits.inner_text().strip().endswith("36"))
    switch_model("Hailuo 2.3 Fast")
    check("hailuofast:credits-24", credits.inner_text().strip().endswith("24"))

    # ---- fractional rate rounding: Hailuo 2.3 Fast at 15s → 4.8*15 = 72
    params_trigger.click()
    page.wait_for_timeout(200)
    duration = page.locator("[data-video-duration]")
    duration.fill("15")
    page.wait_for_timeout(200)
    check("hailuofast:15s-credits-72", credits.inner_text().strip().endswith("72"))
    duration.fill("5")
    page.wait_for_timeout(200)
    params_trigger.click()
    page.wait_for_timeout(200)

    # ---- Seedance 1.5 Pro: default resolution flips to 1080P, 18/s → 90
    switch_model("Seedance 1.5 Pro")
    check("s15:trigger-label", model_trigger.inner_text().strip() == "Seedance1.5")
    check(
        "s15:default-1080p",
        "1080P · 5s · 1个" in params_trigger.inner_text().strip(),
    )
    check("s15:credits-90", credits.inner_text().strip().endswith("90"))

    # ---- resolution A/B on 1.5 Pro: 720P → 40, back to 1080P → 90
    params_trigger.click()
    page.wait_for_timeout(200)
    page.locator('[data-video-resolution-option="720P"]').click()
    page.wait_for_timeout(200)
    check("s15:720p-credits-40", credits.inner_text().strip().endswith("40"))
    page.locator('[data-video-resolution-option="1080P"]').click()
    page.wait_for_timeout(200)
    check("s15:back-1080p-credits-90", credits.inner_text().strip().endswith("90"))
    params_trigger.click()
    page.wait_for_timeout(200)

    # ---- Seedance 1.0 Pro at 1080P: 15/s → 75
    switch_model("Seedance 1.0 Pro")
    check(
        "s10pro:default-1080p-kept",
        "1080P · 5s · 1个" in params_trigger.inner_text().strip(),
    )
    check("s10pro:credits-75", credits.inner_text().strip().endswith("75"))

    # ---- back to 2.5: 720P (clamped from 1080P? no — 2.5 keeps current 1080P)
    # batch238 contract: 2.5 Auto/16:9 at 1080P is untabled → falls back to the
    # 27/s default only when untabled; 2.5 is tabled at 46/s → 46*5 = 230
    switch_model("2.5")
    check("back25:credits-230", credits.inner_text().strip().endswith("230"))

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 240, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch240: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
