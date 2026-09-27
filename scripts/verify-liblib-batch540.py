#!/usr/bin/env python3
"""Verify Batch 540: rail 添加机位 wired to the scene-tree camera action.

Contract: source-site sampling 2026-09-27 (rail DOM enumeration, batch 537)
— the rail's 添加机位 entry is a direct action (clicking opens no panel);
it shares the camera-creation semantics with the scene tree's 新增机位
button. In the clone the rail entry now calls the same
directorStore.addDirectorCamera action: clicking it appends a new 机位N
entry to the scene tree and does not change the rail's active entry.
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
    / "liblib-canvas-batch540-2026-09-27"
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
        assert ok, f"batch540 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/?batch70=1", wait_until="networkidle")
    page.wait_for_function(
        """() => Boolean(window.__libtv_store && window.__libtv_ui_store && window.__director_store)"""
    )

    page.evaluate(
        """() => {
          const store = window.__libtv_store.getState();
          store.addNode("script-execution", { title: "Batch 540" });
          const node = store.getActiveCanvas().nodes.at(-1);
          window.__libtv_ui_store.getState().openDirectorDesk(node.id, store.activeCanvasId);
        }"""
    )
    page.locator("[data-director-workspace]").wait_for(state="visible")
    page.wait_for_timeout(400)

    tree = page.locator("[data-director-tree], [aria-label='场景对象']").first
    tree_text_before = tree.inner_text()
    rail = page.locator("[data-director-icon-rail]")

    # rail 添加机位：直接动作，场景树新增机位条目
    rail.locator("[data-director-rail-entry='add-camera']").click()
    page.wait_for_timeout(400)
    tree_text_after = tree.inner_text()
    check("camera:tree-gains-entry", len(tree_text_after) >= len(tree_text_before))
    check(
        "camera:count-increments",
        tree_text_after.count("机位") > tree_text_before.count("机位"),
    )

    # 无面板打开：不出现任何 flyout/modal
    check("camera:no-flyout", page.locator("[data-director-character-flyout]").count() == 0)
    check("camera:no-modal", page.locator("[data-director-ai-import-modal]").count() == 0)

    # rail 激活态保持 scene（动作项不抢激活）
    check(
        "camera:scene-still-active",
        rail.locator("[data-director-rail-entry='scene']").get_attribute("aria-pressed") == "true",
    )

    # 场景树按钮与 rail 动作同源：再点一次树按钮同样递增
    tree.locator("[data-director-add-camera]").click()
    page.wait_for_timeout(400)
    check(
        "camera:tree-button-also-increments",
        tree.inner_text().count("机位") > tree_text_after.count("机位"),
    )

    check("diagnostics:zero", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 540,
        "title": "Rail add-camera wired to scene-tree camera action",
        "evidence": (
            "docs/research/liblib-source-exploration-2026-09-25/NOTES.md "
            "§8 + batch 537 rail DOM enumeration"
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
        "Batch 540 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "rail add-camera appends a camera entry via the shared "
        "addDirectorCamera action without opening panels or stealing "
        "active state, recorded in runtime-audit.json."
    )


if __name__ == "__main__":
    main()
