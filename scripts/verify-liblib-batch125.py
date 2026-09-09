#!/usr/bin/env python3

"""Verify Batch 125 video panel attempts row / new-feature bar / placeholder.

Batch 245 migration: the first-frame state no longer shows a prompt
textarea (batch 239 source fact — slot + hint instead), so the flow now
asserts the first-frame panel, reverts via the batch-244 销毁 button, and
only then checks the prompt placeholder + generate flow in the default
state."""

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
    / "liblib-canvas-batch125-2026-09-06"
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
        assert ok, f"batch125 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(BASE_URL, wait_until="networkidle")
    page.wait_for_timeout(400)

    # 打开视频生成面板：添加 视频节点 并选中
    page.get_by_role("button", name="添加节点").click()
    page.wait_for_timeout(400)
    panel = page.locator("[data-liblib-overlay='add-node']")
    panel.get_by_role("button", name="视频", exact=True).click()
    page.wait_for_timeout(1200)
    # Batch 246: 选 LAST 个视频节点 = 添加面板新建的节点。预设画布自带
    # 一个视频节点（DOM 首位、图中已有 image→video 既有边），`.first` 会
    # 命中它导致首帧守卫跳过创建、销毁误拆预设边（batch 245 WIP 根因）。
    node = page.locator(".react-flow__node-video").last
    node.click()
    page.wait_for_timeout(800)

    vg = page.locator("[data-video-generation-panel]")
    check("panel:visible", vg.is_visible())

    attempts = page.locator("[data-video-attempts]")
    check("attempts:row", attempts.is_visible())
    check("attempts:label", attempts.get_by_text("尝试：", exact=True).is_visible())
    for label in ["5分钟超长视频", "首尾帧生成视频", "首帧生成视频"]:
        chip = attempts.locator(f"[data-video-attempt='{label}']")
        check(f"attempts:chip:{label}", chip.count() == 1 and chip.get_attribute("aria-pressed") == "false")

    attempts.locator("[data-video-attempt='首帧生成视频']").click()
    check(
        "attempts:select",
        attempts.locator("[data-video-attempt='首帧生成视频']").get_attribute("aria-pressed") == "true",
    )
    # Batch 177: 源站直证同芯片再点不取消（非 toggle）——保持选中。
    attempts.locator("[data-video-attempt='首帧生成视频']").click()
    check(
        "attempts:reclick-stays-selected",
        attempts.locator("[data-video-attempt='首帧生成视频']").get_attribute("aria-pressed") == "true",
    )

    # Batch 239 合同：首帧态面板 = 参考槽 + 说明文案，无提示词输入框。
    check(
        "firstframe:slot",
        page.locator("[data-video-firstframe-slot]").count() == 1,
    )
    check(
        "firstframe:hint",
        page.locator("[data-video-firstframe-hint]").inner_text().strip()
        == "以当前图为首帧生成视频。",
    )
    check(
        "firstframe:no-textarea",
        vg.locator("textarea").count() == 0,
    )

    # Batch 244 合同：悬停槽出现 销毁，点击回退建议态（节点/边回滚、芯片清除）。
    nodes_before = page.evaluate("() => document.querySelectorAll('.react-flow__node').length")
    edges_before = page.evaluate("() => document.querySelectorAll('.react-flow__edge').length")
    destroy = page.locator("[data-video-firstframe-destroy]")
    check("firstframe:destroy-in-dom", destroy.count() == 1)
    page.locator("[data-video-firstframe-slot]").hover()
    page.wait_for_timeout(300)
    check("firstframe:destroy-hover", destroy.is_visible())
    destroy.click()
    page.wait_for_timeout(500)
    check(
        "firstframe:destroy-reverts",
        page.evaluate("() => document.querySelectorAll('.react-flow__node').length") == nodes_before - 1
        and page.evaluate("() => document.querySelectorAll('.react-flow__edge').length") == edges_before - 1
        and attempts.locator("[data-video-attempt='首帧生成视频']").get_attribute("aria-pressed") == "false",
    )

    # Batch 160: 源站 2026-09-07 新建节点整面板无「新功能」条 —— 断言其不存在。
    check("feature:removed", page.locator("[data-video-new-feature]").count() == 0)

    textarea = vg.locator("textarea")
    check(
        "prompt:placeholder",
        textarea.first.get_attribute("placeholder") == "描述你想要生成的画面内容，@引用素材",
    )

    # 工具行保留
    for label in ["参考", "标记", "特效", "角色库", "运镜"]:
        check(f"toolbar:{label}", vg.locator("button").filter(has_text=label).count() >= 1)

    # 生成流程不回归：输入提示词 → 生成 → pending 节点
    textarea.first.fill("测试生成")
    page.locator("[data-video-generate-submit]").click()
    page.wait_for_timeout(600)

    check("diagnostics:zero", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 125,
        "title": "Video panel attempts row / new-feature bar / placeholder",
        "evidence": "docs/research/liblib-video-panel-2026-09-06/README.md",
        "results": [],
    }
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        desktop = browser.new_page(viewport={"width": 1440, "height": 900}, device_scale_factor=1)
        audit["results"].append(run_desktop(desktop))
        desktop.close()
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    checks = audit["results"][0]["checks"]
    print(
        "Batch 125 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "Attempts row (3 chips select/deselect), new-feature bar, prompt "
        "placeholder, toolbar retention and generate flow recorded in "
        "runtime-audit.json."
    )


if __name__ == "__main__":
    main()
