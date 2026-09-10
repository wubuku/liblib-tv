#!/usr/bin/env python3
"""Verify Batch 332: controlled per-model rate retest — MODEL_RATES rewrite
and extension (26 models tabled at the 16:9·720P·5s·1个 baseline).

Source evidence (2026-09-11, docs/research/liblib-canvas-batch332-2026-09-11/):
- Normalized per-model readings (explicit 720P/5s reset before read, stable
  double-read): Wan 3.0 Prime 90 (480P A/B: 45), Wan 3.0 50, Wan 2.7 50,
  Wan 2.6 50, Wan 2.2 40, Wan 2.5 40, Minimax H3 110, Kling 3.0 55,
  Kling 2.6 50, Kling 2.5 25 (高品质; 标准 15 datapoint), Kling O1 35,
  Vidu Q2 45 (1080p 50), Vidu Q2 Pro 45, Vidu Q2 Turbo 80 (1080p tier),
  Happy Horse 1.1 75, Happy Horse 1.0 80, Hailuo 2.3 36.
- Keep-confirmed: Pixverse V5.5 60 (the 135 from batch 291/330 was a stale
  read of the default model 2.0), Pixverse V5 45, Kling O3 55,
  Kling 3.0 Turbo 60, Vidu Q3 Pro 50, Minimax H3 Max 60, Seedance 2.5 230.
- Resolution decides price: Wan 3.0 Prime 480P=45 vs 720P=90 (same session
  A/B). Batch 240's 45/13/8/120/192 readings were lower/higher-resolution
  states, not 720P rates.
- Hailuo 2.3 Fast row cannot be selected on the source (virtualized menu
  mis-targets adjacent rows) — clone keeps the batch 240 value 4.8/s.
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
    / "liblib-canvas-batch332-2026-09-11"
    / "runtime-audit.json"
)

# (model option, expected credits at 16:9·720P·5s·1个)
BASELINE_READINGS: list[tuple[str, str]] = [
    ("Minimax H3 Max", "60"),
    ("Minimax H3", "110"),
    ("Wan 3.0 Prime", "90"),
    ("Wan 3.0", "50"),
    ("Wan 2.7", "50"),
    ("Wan 2.6", "50"),
    ("Wan 2.2", "40"),
    ("Wan 2.5", "40"),
    ("Kling O3", "55"),
    ("Kling 3.0 Turbo", "60"),
    ("Kling 3.0", "55"),
    ("Kling 2.6", "50"),
    ("Kling 2.5", "25"),
    ("Kling O1", "35"),
    ("Vidu Q2", "45"),
    ("Vidu Q2 Pro", "45"),
    ("Vidu Q2 Turbo", "80"),
    ("Vidu Q3 Pro", "50"),
    ("Happy Horse 1.1", "75"),
    ("Happy Horse 1.0", "80"),
    ("Hailuo 2.3", "36"),
    ("Hailuo 2.3 Fast", "24"),
    ("Hailuo 02", "36"),
    ("Pixverse V5.5", "60"),
    ("Pixverse V5", "45"),
    ("2.5", "230"),
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
        assert ok, f"batch332 check failed: {name}"
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

    # ---- baseline sweep: 26 tabled models at 16:9·720P·5s·1个
    for option, expected in BASELINE_READINGS:
        switch_model(option)
        check(
            f"rate:{option}-credits-{expected}",
            credits.inner_text().strip().endswith(expected),
        )

    # ---- resolution decides price: source A/B shows Wan 3.0 Prime 480P=45
    # vs 720P=90. The clone tables only 720P/1080P tiers (SOURCE_CLONE_GAP:
    # 480P stays on the 720P rate), so 480P still renders 90 here.
    switch_model("Wan 3.0 Prime")
    params_trigger.click()
    page.wait_for_timeout(200)
    page.locator('[data-video-resolution-option="480P"]').click()
    page.wait_for_timeout(200)
    check("wan3prime:480p-credits-90-clone-gap", credits.inner_text().strip().endswith("90"))
    page.locator('[data-video-resolution-option="720P"]').click()
    page.wait_for_timeout(200)
    check("wan3prime:720p-credits-90", credits.inner_text().strip().endswith("90"))
    params_trigger.click()
    page.wait_for_timeout(200)

    # ---- fractional rate rounding: Hailuo 2.3 at 15s → 7.2*15 = 108
    switch_model("Hailuo 2.3")
    params_trigger.click()
    page.wait_for_timeout(200)
    duration = page.locator("[data-video-duration]")
    duration.fill("15")
    page.wait_for_timeout(200)
    check("hailuo23:15s-credits-108", credits.inner_text().strip().endswith("108"))
    duration.fill("5")
    page.wait_for_timeout(200)
    params_trigger.click()
    page.wait_for_timeout(200)
    check("hailuo23:back-5s-credits-36", credits.inner_text().strip().endswith("36"))

    # ---- default-model control: 2.0 VIP stays 27/s → 135
    switch_model("2.0 VIP")
    check("control:vip-credits-135", credits.inner_text().strip().endswith("135"))

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 332, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch332: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
