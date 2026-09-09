#!/usr/bin/env python3
"""Verify Batch 249: OmniHuman 1.5 special panel.

Source evidence (2026-09-09, docs/research/liblib-canvas-batch248-2026-09-09/
omnihuman.png): switching to OmniHuman 1.5 replaces the standard panel —
no toolbar pills (requirement slots instead: 图片 1/1 satisfied + 音频 0/1
missing + 请提供音频 warning), mode trigger equals the model name, settings
chip reads 自适应 · 1个 (no ratio/resolution/duration), credits 28, and the
advanced rows become 快速模式 + 智能引用 AutoLink."""

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
    / "liblib-canvas-batch249-2026-09-09"
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
        assert ok, f"batch249 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto("http://localhost:4317", wait_until="networkidle")
    page.wait_for_timeout(500)

    # fresh video node + first-frame chip (the sampled OmniHuman state carried
    # an attached first-frame reference)
    page.get_by_role("button", name="添加节点").click()
    page.wait_for_timeout(300)
    page.locator("[data-liblib-overlay='add-node']").get_by_role("button", name="视频", exact=True).click()
    page.wait_for_timeout(1000)
    page.locator('[data-video-attempt="首帧生成视频"]').click()
    page.wait_for_timeout(300)

    model_trigger = page.locator("[data-video-model-trigger]")
    params_trigger = page.locator("[data-video-params-trigger]")
    credits = page.locator("[data-video-credits]")
    toolbar = page.locator("[data-video-toolbar]")

    # switch to OmniHuman 1.5
    model_trigger.click()
    page.locator('[data-video-model-option="OmniHuman 1.5"]').click()
    page.wait_for_timeout(300)

    check("omni:mode-trigger", model_trigger.inner_text().strip() == "OmniHuman 1.5")
    check("omni:chip-adaptive", params_trigger.inner_text().strip() == "自适应 · 1个")
    check("omni:credits-28", credits.inner_text().strip().endswith("28"))

    # requirement slots replace pills and the prompt textarea
    check("omni:image-slot", page.locator("[data-omnihuman-image-slot]").count() == 1)
    check("omni:audio-slot", page.locator("[data-omnihuman-audio-slot]").count() == 1)
    check(
        "omni:audio-warning",
        page.locator("[data-omnihuman-audio-warning]").inner_text().strip() == "请提供音频",
    )
    pill_texts = [
        t.strip()
        for t in toolbar.locator("button").all_inner_texts()
        if t.strip() in ("参考", "标记", "特效", "替换", "角色库", "运镜")
    ]
    check("omni:no-pills", len(pill_texts) == 0)
    check(
        "omni:no-textarea",
        page.locator("textarea[aria-label='视频生成提示词']").count() == 0,
    )

    # advanced rows: 快速模式 + AutoLink (no 高级设置 title rows)
    check(
        "omni:fast-mode-row",
        page.locator("[data-video-advanced-inline]").get_by_text("快速模式", exact=True).count() == 1,
    )
    check(
        "omni:no-network-search",
        page.locator("[data-video-advanced-inline]").get_by_text("联网搜索", exact=True).count() == 0,
    )

    # switching back to 2.5 restores the standard panel
    model_trigger.click()
    page.locator('[data-video-model-option="2.5"]').click()
    page.wait_for_timeout(300)
    check(
        "back25:chip-standard",
        params_trigger.inner_text().strip().endswith("· 1个 ·")
        and "自适应" not in params_trigger.inner_text(),
    )
    check(
        "back25:pills-restored",
        len(pill_labels(toolbar)) == 5,
    )
    check(
        "back25:advanced-restored",
        page.locator("[data-video-advanced-inline]").get_by_text("联网搜索", exact=True).count() == 1,
    )

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def pill_labels(toolbar: Any) -> list[str]:
    return [
        t.strip()
        for t in toolbar.locator("button").all_inner_texts()
        if t.strip() in ("参考", "标记", "特效", "替换", "角色库", "运镜")
    ]


def main() -> None:
    audit: dict[str, Any] = {"batch": 249, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch249: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
