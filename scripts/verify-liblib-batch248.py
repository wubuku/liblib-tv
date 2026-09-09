#!/usr/bin/env python3
"""Verify Batch 248: per-model toolbar pill sets in the first-frame state.

Source evidence (2026-09-09, docs/research/liblib-canvas-batch248-2026-09-09/
sample-log.json): with a first-frame reference attached, the toolbar pill
set varies by model — Happy Horse 1.1/1.0 show only +参考, Wan 2.6 shows
参考/标记/特效, while 2.5 keeps the full five-pill row (OmniHuman 1.5 is a
special multi-input panel: mode = model name, requirement slots 图片 1/1 +
音频 0/1 + 请提供音频, settings chip 自适应 · 1个, credits 28 — recorded,
not cloned)."""

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
    / "liblib-canvas-batch248-2026-09-09"
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
        assert ok, f"batch248 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto("http://localhost:4317", wait_until="networkidle")
    page.wait_for_timeout(500)

    # fresh video node + first-frame chip (2.5 default state)
    page.get_by_role("button", name="添加节点").click()
    page.wait_for_timeout(300)
    page.locator("[data-liblib-overlay='add-node']").get_by_role("button", name="视频", exact=True).click()
    page.wait_for_timeout(1000)
    page.locator('[data-video-attempt="首帧生成视频"]').click()
    page.wait_for_timeout(300)

    toolbar = page.locator("[data-video-toolbar]")
    model_trigger = page.locator("[data-video-model-trigger]")

    def pill_labels() -> list[str]:
        return [
            t.strip()
            for t in toolbar.locator("button").all_inner_texts()
            if t.strip() in ("参考", "标记", "特效", "替换", "角色库", "运镜")
        ]

    # ---- 2.5: full five-pill row (batch 237 a1 contract)
    labels = pill_labels()
    check("pills25:all-five", len(labels) == 5 and "角色库" in labels and "运镜" in labels)

    def switch_model(option: str) -> None:
        model_trigger.click()
        page.locator(f'[data-video-model-option="{option}"]').click()
        page.wait_for_timeout(300)

    # ---- Happy Horse 1.1: single 参考 pill
    switch_model("Happy Horse 1.1")
    labels = pill_labels()
    check("hh11:only-cankao", labels == ["参考"])

    # ---- Wan 2.6: 参考/标记/特效 (no 角色库, no 运镜)
    switch_model("Wan 2.6")
    labels = pill_labels()
    check(
        "wan26:three-pills",
        "参考" in labels and "标记" in labels and ("特效" in labels or "替换" in labels)
        and "角色库" not in labels and "运镜" not in labels,
    )

    # ---- back to 2.5: full row restored
    switch_model("2.5")
    labels = pill_labels()
    check("back25:all-five", len(labels) == 5 and "角色库" in labels and "运镜" in labels)

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 248, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch248: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
