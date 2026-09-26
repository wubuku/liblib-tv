#!/usr/bin/env python3

"""Verify Batch 160: FrameOS prompt panel footer drift catch-up.

2026-09-23 source re-sampling (docs/user-manual/frameos-canvas
SOURCE_OBSERVATIONS.md §13.4): the image prompt panel footer is
模型下拉 (default Seedream 5.0 Pro) / 合并档位 chip "2K · 16:9" /
高级设置 + credits (coin 60 · 30 · 5折) + circular 生成 arrow button.
The clone still had 帧界 O2 default, separate 1K/16:9/更多参数 dropdowns,
and a bare "60". Verifies:

1. model dropdown defaults to Seedream 5.0 Pro;
2. combined "2K · 16:9" tier chip present, standalone 1K/16:9 chips gone;
3. 高级设置 button present;
4. credits row shows 60 / 30 / 5折;
5. circular 生成 button still fires startGeneration (running state disables it);
6. regression: header chips + text-node guard from batch 158/159 stay green.
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
    / "liblib-frameos-batch160-2026-09-23"
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
    page.goto(f"{BASE_URL}/frameos/canvas/demo", wait_until="domcontentloaded", timeout=90000)
    page.wait_for_timeout(1200)

    # Batch 225: 面板仅空图片节点显示 (2026-09-25 源站实测: 内容图片选中
    # 只显示富工具条无面板), 故先清空 image-1 内容再验证面板
    page.evaluate(
        "window.__frameos_store.getState().updateNodeData('image-1', { imageUrl: null })"
    )
    page.wait_for_timeout(300)

    image_node = page.locator(".react-flow__node-image").first
    check("boot:image-node", image_node.count() == 1)
    image_node.click()
    page.wait_for_timeout(400)
    editor = page.locator(".frameos-prompt-editor")
    check("image:editor-opens", editor.is_visible())

    # 模型下拉默认 Seedream 5.0 Pro
    model = editor.locator("select").first
    check("footer:model-seedream", model.input_value() == "Seedream 5.0 Pro")

    # 合并档位 chip "2K · 16:9"; 旧的独立 1K / 16:9 下拉移除
    footer_text = editor.locator(".prompt-bottom-controls").inner_text()
    check("footer:combined-tier", "2K · 16:9" in footer_text)
    check(
        "footer:no-legacy-dropdowns",
        editor.locator("select").count() == 2,
    )

    # 高级设置按钮
    check(
        "footer:advanced-settings",
        editor.get_by_role("button", name="高级设置").is_visible(),
    )

    # 积分行: 60 / 30 / 5折
    check(
        "footer:credits-60-30-5zhe",
        "60" in footer_text and "30" in footer_text and "5折" in footer_text,
    )

    # 生成按钮可点 → running 态禁用 (mock generation)
    gen = editor.get_by_role("button", name="生成")
    check("footer:generate-visible", gen.is_visible())
    editor.locator("textarea").fill("batch160 冒烟提示词")
    gen.click()
    page.wait_for_timeout(300)
    check("footer:generate-running-disables", gen.is_disabled())
    page.keyboard.press("Escape")

    # 回归: 头部芯片与文本节点守卫
    page.locator(".react-flow__node-image").first.click()
    page.wait_for_timeout(300)
    check("regression:header-chips", page.locator("[data-frameos-ref-chip]").count() >= 3)
    page.locator(".react-flow__node-text").first.click()
    page.wait_for_timeout(300)
    check("regression:text-guard", page.locator(".frameos-prompt-editor").count() == 0)

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
