#!/usr/bin/env python3

"""Verify Batch 97 Agent drawer alignment with the 2026-09-05 source audit."""

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
    / "liblib-canvas-batch97-2026-09-05"
    / "runtime-audit.json"
)

SKILL_BATCH_ONE = {
    "pixar": ("皮克斯动画广告", "/pixar-animated-ad-creator"),
    "viral": ("爆款拉片复刻", "/viral-video-replicator"),
    "neo-china": ("新中式美学TVC", "/neo-chinese-aesthetic-tvc"),
    "wuxia": ("古典武侠电影全流程导演", "/hujinquanwuxia"),
}

IMAGE_MODELS = [
    "Lib Image",
    "General image Pro",
    "General image V2",
    "Seedream 5.0 Pro",
    "Style Image V8.2",
    "Style Image V8.1",
    "Style Image V7",
]

VIDEO_MODELS = [
    "Seedance 2.5",
    "Seedance 2.0 VIP",
    "Minimax H3",
    "Seedance 2.0 Fast VIP",
    "Wan 3.0 Prime",
    "Wan 3.0",
    "Kling O3",
    "Kling 3.0",
]

PREMIUM_VIDEO_COUNT = 6


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


def open_agent(page: Page) -> Any:
    page.get_by_role("button", name="Agent", exact=True).click()
    agent = page.locator('[data-liblib-overlay="agent"]')
    assert agent.is_visible()
    return agent


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool) -> None:
        assert ok, f"batch97 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(BASE_URL, wait_until="networkidle")
    page.wait_for_timeout(400)

    agent = open_agent(page)

    header_buttons = [
        ("当前已是新对话", True),
        ("历史对话", False),
        ("新对话无法分享", True),
        ("Agent 设置", False),
        ("CLI & Skill", False),
        ("关闭", False),
    ]
    for name, disabled in header_buttons:
        button = agent.get_by_role("button", name=name, exact=True)
        check(f"header:{name}", button.count() == 1 and button.is_disabled() == disabled)

    check(
        "skill:headline-workbench",
        agent.get_by_text("选一个 Skill，让创作更快一步").is_visible(),
    )

    for skill_id, (title, path) in SKILL_BATCH_ONE.items():
        card = agent.locator(f'[data-agent-skill="{skill_id}"]')
        check(
            f"skill:{skill_id}",
            card.count() == 1 and title in card.inner_text() and path in card.inner_text(),
        )

    pixar = agent.locator('[data-agent-skill="pixar"]')
    pixar.click()
    check("skill:prompt-fill", agent.locator("textarea").input_value() == "皮克斯动画广告")

    agent.locator("[data-agent-refresh]").click()
    check("skill:refresh", agent.locator('[data-agent-skill="character"]').count() == 1)
    check("skill:refresh-clears-batch-one", agent.locator('[data-agent-skill="pixar"]').count() == 0)
    agent.locator("[data-agent-refresh]").click()

    for name in ["添加附件", "选择模型", "Skill", "生成模式", "Send"]:
        check(
            f"composer:{name}",
            agent.get_by_role("button", name=name, exact=True).count() == 1,
        )

    model_button = agent.get_by_role("button", name="选择模型", exact=True)
    model_button.click()
    menu = page.locator("[data-agent-model-menu]")
    check("model-menu:open", menu.is_visible())
    check("model-menu:title", menu.get_by_text("选择模型", exact=True).is_visible())
    check(
        "model-menu:tab-image",
        menu.locator('[data-agent-model-tab="image"]').get_attribute("aria-selected") == "true",
    )
    check(
        "model-menu:tab-video",
        menu.locator('[data-agent-model-tab="video"]').get_attribute("aria-selected") == "false",
    )
    check("model-menu:section-image", menu.get_by_text("图片", exact=True).count() >= 1)
    check("model-menu:section-video", menu.get_by_text("视频", exact=True).count() >= 1)

    for model_name in IMAGE_MODELS:
        check(
            f"model-menu:image:{model_name}",
            menu.locator(f'[data-agent-model][aria-label="添加 {model_name}"]').count() == 1,
        )
    for model_name in VIDEO_MODELS:
        check(
            f"model-menu:video:{model_name}",
            menu.locator(f'[data-agent-model][aria-label="添加 {model_name}"]').count() == 1,
        )
    check(
        "model-menu:premium-count",
        menu.locator('[aria-label="premium"]').count() == PREMIUM_VIDEO_COUNT,
    )

    lib_image_toggle = menu.locator('[data-agent-model="lib-image"]')
    lib_image_toggle.click()
    check("model-menu:select", lib_image_toggle.get_attribute("aria-pressed") == "true")
    lib_image_toggle.click()
    check("model-menu:deselect", lib_image_toggle.get_attribute("aria-pressed") == "false")

    menu.locator('[data-agent-model-tab="video"]').click()
    page.wait_for_timeout(200)
    check(
        "model-menu:tab-switch",
        menu.locator('[data-agent-model-tab="video"]').get_attribute("aria-selected") == "true",
    )

    page.keyboard.press("Escape")
    page.wait_for_timeout(150)
    check("model-menu:escape-closes", page.locator("[data-agent-model-menu]").count() == 0)
    check("model-menu:escape-keeps-drawer", agent.is_visible())

    mode_button = agent.get_by_role("button", name="生成模式", exact=True)
    mode_button.click()
    mode_menu = page.locator("[data-agent-mode-menu]")
    check("mode-menu:open", mode_menu.is_visible())
    check(
        "mode-menu:manual-copy",
        "Agent 在每次生成前询问" in mode_menu.locator('[data-agent-mode="manual"]').inner_text(),
    )
    check(
        "mode-menu:auto-copy",
        "Agent 完全自动生成" in mode_menu.locator('[data-agent-mode="auto"]').inner_text(),
    )
    check(
        "mode-menu:default-auto",
        mode_menu.locator('[data-agent-mode="auto"]').get_attribute("aria-checked") == "true",
    )
    mode_menu.locator('[data-agent-mode="manual"]').click()
    page.wait_for_timeout(100)
    check(
        "mode-menu:switch-manual",
        mode_menu.locator('[data-agent-mode="manual"]').get_attribute("aria-checked") == "true"
        and mode_menu.locator('[data-agent-mode="auto"]').get_attribute("aria-checked") == "false",
    )
    mode_button.click()

    attach = agent.get_by_role("button", name="添加附件", exact=True)
    attach.click()
    check("composer:attach-status", "本地预览" in agent.locator("[data-agent-status]").inner_text())

    agent.locator("textarea").fill("检查当前画布的镜头连续性")
    agent.locator("[data-agent-send]").click()
    check("composer:send-status", "本地预览" in agent.locator("[data-agent-status]").inner_text())

    agent.get_by_role("button", name="关闭", exact=True).click()
    check("drawer:close", not agent.is_visible())

    check("diagnostics:zero", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 97,
        "title": "Agent drawer alignment with 2026-09-05 source audit",
        "evidence": "docs/research/liblib-live-2026-09-05/README.md",
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
    desktop_checks = audit["results"][0]["checks"]
    print(
        "Batch 97 verification passed: "
        f"{len(desktop_checks)} checks, 0 diagnostics. "
        "Agent header/disabled states, source-named skills, composer controls, "
        "model menu catalog (7 image + 8 video, premium badges), generation mode menu, "
        "escape layering and local status feedback recorded in runtime-audit.json."
    )


if __name__ == "__main__":
    main()
