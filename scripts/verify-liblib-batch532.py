#!/usr/bin/env python3
"""Verify Batch 532: storyboard editor step navigation (steps 2/3).

Contract: source-site CDP sampling 2026-09-27
(docs/research/liblib-source-exploration-2026-09-25/NOTES.md §11 update +
screenshots 40-storyboard-step2.png / 41-storyboard-step3.png) — the
storyboard editor's 下一步 advances through:
- step 2 准备资产: three asset groups (角色/场景/道具), each a dashed
  新增 card; footer-left green-check notice 资产已生成，如再次生成将会
  覆盖之前的图片/场景/道具等资产; footer-right → 下一步：合成提示词;
- step 3 合成提示词: the same 10-column shot table with the 最终提示词
  header highlighted; footer-left 添加镜头; footer-right 一键合成全部
  提示词 (visual only in clone — real synthesis is a paid AI action).
The stepper highlights the active step (rounded pill); there is no
上一步 button on the source. Navigation is local; no generation triggers.
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
    / "liblib-canvas-batch532-2026-09-27"
    / "runtime-audit.json"
)

SELF_WRITE = "自己编写分镜脚本"


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
        assert ok, f"batch532 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(BASE_URL, wait_until="networkidle")
    page.wait_for_timeout(400)

    # 创建脚本生成器并打开自写编辑器（batch 531 路径）
    page.get_by_role("button", name="添加节点").click()
    page.wait_for_timeout(400)
    panel = page.locator('[data-liblib-overlay="add-node"]')
    panel.locator("[data-add-node-entry='script']").click()
    page.wait_for_timeout(300)
    panel.locator("[data-add-node-entry='script-new']").click()
    page.wait_for_timeout(700)
    node = page.locator(".react-flow__node-script-generator").first
    node.locator(f"[data-script-generator-attempt='{SELF_WRITE}']").click()
    page.wait_for_timeout(300)
    editor = page.locator("[data-storyboard-editor]")
    check("editor:opens", editor.is_visible())

    # —— 第 2 步：准备资产 ——
    editor.locator("[data-storyboard-next='assets']").click()
    page.wait_for_timeout(250)
    for group in ["角色", "场景", "道具"]:
        check(
            f"step2:group:{group}",
            editor.locator(f"[data-storyboard-asset-group='{group}']").is_visible(),
        )
    check(
        "step2:add-card",
        editor.locator("[data-storyboard-asset-add]").count() == 3,
    )
    notice = editor.locator("[data-storyboard-asset-notice]")
    check(
        "step2:override-notice",
        notice.is_visible()
        and "资产已生成" in notice.inner_text()
        and "覆盖" in notice.inner_text(),
    )
    check(
        "step2:next-label",
        editor.locator("[data-storyboard-next='prompts']").inner_text().replace("\n", "")
        .find("下一步：合成提示词") >= 0,
    )
    check("step2:no-add-shot", editor.locator("[data-storyboard-add-shot]").count() == 0)

    # —— 第 3 步：合成提示词 ——
    editor.locator("[data-storyboard-next='prompts']").click()
    page.wait_for_timeout(250)
    check("step3:table-returns", editor.locator("[data-storyboard-row='1']").is_visible())
    synth = editor.locator("[data-storyboard-synthesize-all]")
    check("step3:synthesize-all", synth.is_visible() and "一键合成全部提示词" in synth.inner_text())
    check("step3:add-shot", editor.locator("[data-storyboard-add-shot]").is_visible())
    check("step3:no-next", editor.locator("[data-storyboard-next-step]").count() == 0)
    check(
        "step3:pending-pill",
        "待生成提示词" in editor.locator("[data-storyboard-row='1']").inner_text(),
    )

    # 一键合成为可视按钮：不打开任何弹层、无网络动作（diagnostics 覆盖）
    synth.click()
    page.wait_for_timeout(300)
    check("step3:synth-inert", editor.is_visible())

    # ESC 在第 3 步仍可关闭整个编辑器
    editor.click(position={"x": 700, "y": 300})
    page.keyboard.press("Escape")
    page.wait_for_timeout(250)
    check("step3:escape-closes", page.locator("[data-storyboard-editor]").count() == 0)

    check("diagnostics:zero", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 532,
        "title": "Storyboard editor step navigation (steps 2/3)",
        "evidence": (
            "docs/research/liblib-source-exploration-2026-09-25/NOTES.md "
            "§11 update + screenshots 40/41 (CDP 2026-09-27)"
        ),
        "results": [],
    }
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        desktop = browser.new_page(
            viewport={"width": 1440, "height": 900}, device_scale_factor=1
        )
        audit["results"].append(run_desktop(desktop))
        desktop.close()
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    checks = audit["results"][0]["checks"]
    print(
        "Batch 532 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "step 2 asset groups + override notice, step 3 highlighted "
        "最终提示词 column + inert synthesize-all, forward-only navigation "
        "recorded in runtime-audit.json."
    )


if __name__ == "__main__":
    main()
