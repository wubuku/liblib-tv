#!/usr/bin/env python3
"""Verify Batch 252: first-last-frame chip flow.

Source evidence (2026-09-09, docs/research/liblib-canvas-batch251-2026-09-09/
a-firstlast.png): the 首尾帧生成视频 chip auto-creates TWO image nodes
(first + last, stacked left of the video node) joined by two edges into the
video node, the panel shows two reference slots + a prompt prefilled with
the sampled AI transition text, and the footer switches to 2.0 / 全能参考 /
16:9·720P·5s·1个 (source credits 155; clone formula gives 27×5 = 135 —
drift recorded in the batch 251 README)."""

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
    / "liblib-canvas-batch252-2026-09-09"
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
        assert ok, f"batch252 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto("http://localhost:4317", wait_until="networkidle")
    page.wait_for_timeout(500)

    # fresh video node (batch176 recipe)
    page.get_by_role("button", name="添加节点").click()
    page.wait_for_timeout(300)
    page.locator("[data-liblib-overlay='add-node']").get_by_role("button", name="视频", exact=True).click()
    page.wait_for_timeout(1000)

    def graph_state() -> dict[str, Any]:
        return page.evaluate(
            """() => ({
                total: document.querySelectorAll('.react-flow__node').length,
                edges: document.querySelectorAll('.react-flow__edge').length,
            })"""
        )

    before = graph_state()
    page.locator('[data-video-attempt="首尾帧生成视频"]').click()
    page.wait_for_timeout(600)
    after = graph_state()
    check("graph:two-nodes-added", after["total"] == before["total"] + 2)
    check("graph:two-edges-added", after["edges"] == before["edges"] + 2)

    model_trigger = page.locator("[data-video-model-trigger]")
    mode_trigger = page.locator("[data-video-mode-trigger]")
    params_trigger = page.locator("[data-video-params-trigger]")
    credits = page.locator("[data-video-credits]")

    # panel: two slots + prefilled prompt + footer state
    check("panel:two-slots", page.locator("[data-video-firstlast-slots] > div").count() == 2)
    textarea = page.locator("textarea[aria-label='视频生成提示词']")
    check("panel:textarea-present", textarea.count() == 1)
    check(
        "panel:prompt-prefilled",
        "青柠气泡水罐" in (textarea.input_value() or ""),
        ),
    check("footer:model-2-0", model_trigger.inner_text().strip() == "2.0")
    check("footer:mode-全能参考", mode_trigger.inner_text().strip() == "全能参考")
    check(
        "footer:chip-169-720p-5s",
        params_trigger.inner_text().strip() == "16:9 · 720P · 5s · 1个 ·",
    )
    # clone flat-rate formula: 2.0 → 27/s × 5s = 135 (source 155 drift recorded)
    check("footer:credits-135", credits.inner_text().strip().endswith("135"))

    # guard: re-click chip adds nothing
    page.locator('[data-video-attempt="首尾帧生成视频"]').click(force=True)
    page.wait_for_timeout(400)
    guarded = graph_state()
    check("guard:no-duplicates", guarded["total"] == after["total"] and guarded["edges"] == after["edges"])

    # switching model to 2.5 keeps slots/prompt, chip/format returns (light check)
    model_trigger.click()
    page.locator('[data-video-model-option="2.5"]').click()
    page.wait_for_timeout(300)
    check(
        "switch25:chip-169",
        params_trigger.inner_text().strip() == "16:9 · 720P · 5s · 1个 ·",
    )
    # 2.5 · 16:9 · 5s → 46*5 = 230 (source datapoint confirmed in batch 238)
    check("switch25:credits-230", credits.inner_text().strip().endswith("230"))

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 252, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch252: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
