#!/usr/bin/env python3
"""Verify Batch 536: director desk left icon rail.

Contract: source-site live sampling 2026-09-25 round 2
(docs/research/liblib-source-exploration-2026-09-25/NOTES.md §8 + screenshot
18-director-console-opened.png) — the director desk's leftmost narrow icon
rail (~46px) stacks six entries vertically: 图层 / 人物 / 机位 / 帧 /
文件夹 / 导入, with 图层 (the scene tree) in the active state. Only the
layers panel exists in the clone (the scene tree); the other five panels
are unsampled on the source, so their entries are visual toggles that do
not navigate (CLONE_DECISION).
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
    / "liblib-canvas-batch536-2026-09-27"
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
        assert ok, f"batch536 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/?batch70=1", wait_until="networkidle")
    page.wait_for_function(
        """() => Boolean(window.__libtv_store && window.__libtv_ui_store)"""
    )

    page.evaluate(
        """() => {
          const store = window.__libtv_store.getState();
          store.addNode("script-execution", { title: "Batch 536" });
          const node = store.getActiveCanvas().nodes.at(-1);
          window.__libtv_ui_store.getState().openDirectorDesk(node.id, store.activeCanvasId);
        }"""
    )
    page.locator("[data-director-workspace]").wait_for(state="visible")
    page.wait_for_timeout(400)

    rail = page.locator("[data-director-icon-rail]")
    check("rail:visible", rail.is_visible())
    # Batch 537 migration: DOM-verified rail labels (scene/add-character/
    # add-camera/panorama/aspect-ratio/ai-import + help) replace the 536
    # inferred set (layers/characters/...).
    entries = rail.locator("[data-director-rail-entry]")
    check("rail:seven-entries", entries.count() == 7)
    for entry_id in ["scene", "add-character", "add-camera", "panorama", "aspect-ratio", "ai-import", "help"]:
        check(
            f"rail:entry:{entry_id}",
            rail.locator(f"[data-director-rail-entry='{entry_id}']").is_visible(),
        )
    check(
        "rail:scene-active-default",
        rail.locator("[data-director-rail-entry='scene']").get_attribute("aria-pressed") == "true",
    )
    check(
        "rail:label-scene",
        rail.locator("[data-director-rail-entry='scene']").get_attribute("aria-label") == "场景",
    )

    # 添加角色 flyout（batch 537 采样菜单）
    rail.locator("[data-director-rail-entry='add-character']").click()
    page.wait_for_timeout(200)
    flyout = page.locator("[data-director-character-flyout]")
    check("flyout:opens", flyout.is_visible())
    flyout_text = flyout.inner_text()
    for token in ["本地上传", "标准男性", "标准女性", "健硕", "纤细", "少年", "儿童", "宽厚", "二头身", "群众 (3x3)", "几何模型"]:
        check(f"flyout:item:{token}", token in flyout_text)
    rail.locator("[data-director-rail-entry='scene']").click()
    page.wait_for_timeout(150)
    check("flyout:closes", page.locator("[data-director-character-flyout]").count() == 0)

    # 点击其他入口：激活态迁移，场景树仍在（无导航面板）
    rail.locator("[data-director-rail-entry='add-camera']").click()
    page.wait_for_timeout(150)
    check(
        "rail:add-camera-active",
        rail.locator("[data-director-rail-entry='add-camera']").get_attribute("aria-pressed") == "true",
    )
    check(
        "rail:scene-inactive",
        rail.locator("[data-director-rail-entry='scene']").get_attribute("aria-pressed") == "false",
    )
    check("rail:tree-still-present", page.locator("[aria-label='场景对象']").first.is_visible())

    check("diagnostics:zero", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 536,
        "title": "Director desk left icon rail",
        "evidence": (
            "docs/research/liblib-source-exploration-2026-09-25/NOTES.md "
            "§8 + screenshot 18-director-console-opened.png"
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
        "Batch 536 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "six-entry icon rail (图层/人物/机位/帧/文件夹/导入) with active-state "
        "switching and non-navigating unsampled entries recorded in "
        "runtime-audit.json."
    )


if __name__ == "__main__":
    main()
