#!/usr/bin/env python3
"""Verify Batch 237: first-frame chip shows 全能参考; per-model resolution
lists (Fast VIP 480P/720P only); Fast VIP Auto rate 22/s; trigger labels.

Source evidence (2026-09-09, docs/research/liblib-canvas-batch237-2026-09-09/):
- 首帧生成视频 chip → mode trigger 全能参考, Auto·720P·5s·1个, credits 230
  on 2.5 (a1-after-firstframe.png; auto-created image node + explanation
  text 以当前图为首帧生成视频。 are recorded but not cloned).
- Seedance 2.0 Fast VIP: trigger label "2.0 Fast", resolution list
  [480P, 720P] (p3-footer-25.json), Auto·5s credits 110 (22/s), and
  16:9·5s also 110 → ratio-independent within model.
- 2.0 VIP keeps 4K (batch 236); clamp generalizes to "highest ≤ current".
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
    / "liblib-canvas-batch237-2026-09-09"
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
        assert ok, f"batch237 check failed: {name}"
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
    mode_trigger = page.locator("[data-video-mode-trigger]")
    params_trigger = page.locator("[data-video-params-trigger]")
    credits = page.locator("[data-video-credits]")

    # ---- 首帧生成视频 chip → 全能参考 + Auto·5s + 230
    page.locator('[data-video-attempt="首帧生成视频"]').click()
    page.wait_for_timeout(300)
    check("firstframe:mode-全能参考", mode_trigger.inner_text().strip() == "全能参考")
    check(
        "firstframe:settings",
        params_trigger.inner_text().strip() == "Auto · 720P · 5s · 1个 ·",
    )
    check("firstframe:credits-230", credits.inner_text().strip().endswith("230"))
    check(
        "firstframe:chip-selected",
        page.locator('[data-video-attempt="首帧生成视频"]').get_attribute("aria-pressed")
        == "true",
    )

    # ---- switch to 2.0 Fast VIP: trigger "2.0 Fast", Auto credits 110 (22/s)
    model_trigger.click()
    page.locator('[data-video-model-option="2.0 Fast VIP"]').click()
    page.wait_for_timeout(300)
    check("fast:trigger-label", model_trigger.inner_text().strip() == "2.0 Fast")
    check("fast:credits-110", credits.inner_text().strip().endswith("110"))

    # ---- params menu under Fast VIP: 2 resolutions only, no 4K/1080P
    params_trigger.click()
    page.wait_for_timeout(200)
    res_options = page.locator("[data-video-resolution-option]")
    check("fast:2-resolutions", res_options.count() == 2)
    check(
        "fast:only-480-720",
        page.locator('[data-video-resolution-option="480P"]').count() == 1
        and page.locator('[data-video-resolution-option="720P"]').count() == 1
        and page.locator('[data-video-resolution-option="1080P"]').count() == 0
        and page.locator('[data-video-resolution-option="4K"]').count() == 0,
    )
    check(
        "fast:720p-selected",
        page.locator('[data-video-resolution-option="720P"]').get_attribute("aria-pressed")
        == "true",
    )
    params_trigger.click()
    page.wait_for_timeout(200)

    # ---- switch to 2.0 VIP: resolutions gain 4K (batch236 contract), credits 27/s
    model_trigger.click()
    page.locator('[data-video-model-option="2.0 VIP"]').click()
    page.wait_for_timeout(300)
    check("vip:credits-135", credits.inner_text().strip().endswith("135"))  # 27*5, Auto
    params_trigger.click()
    page.wait_for_timeout(200)
    check("vip:4-resolutions", page.locator("[data-video-resolution-option]").count() == 4)
    # pick 4K then leave → clamp to highest ≤ 4K = 1080P
    page.locator('[data-video-resolution-option="4K"]').click()
    page.wait_for_timeout(200)
    params_trigger.click()
    page.wait_for_timeout(200)
    model_trigger.click()
    page.locator('[data-video-model-option="2.5"]').click()
    page.wait_for_timeout(300)
    check(
        "clamp:4k-to-1080p",
        params_trigger.inner_text().strip() == "Auto · 1080P · 5s · 1个 ·",
    )
    # back on 2.5 Auto 5s → 230 (46/s)
    check("clamp:credits-230", credits.inner_text().strip().endswith("230"))

    # ---- Fast VIP clamp downward: 1080P → Fast VIP list lacks 1080P → 720P
    model_trigger.click()
    page.locator('[data-video-model-option="2.0 Fast VIP"]').click()
    page.wait_for_timeout(300)
    check(
        "clamp:1080p-to-720p",
        params_trigger.inner_text().strip() == "Auto · 720P · 5s · 1个 ·",
    )

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 237, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch237: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
