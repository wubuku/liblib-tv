#!/usr/bin/env python3
"""Verify Batch 545: scene-tree entry context menu.

Contract: source-site CDP sampling 2026-09-28 (screenshot
47-director-rightclick-tree.png) — right-clicking a scene-tree entry
(e.g. 机位1) opens a context menu with five items: 打组 / 显示/隐藏 /
锁定/解锁 / 创建副本 / 删除 (the last with a destructive tone). In the
clone the menu wires to the existing store actions: 打组 →
groupSelectedCharacters, 显示/隐藏 → updateObject visible flip, 锁定/解锁
→ toggleObjectLocked, 创建副本 → copyDirectorSelection +
pasteDirectorClipboard, 删除 → deleteDirectorEntity DELETE_OBJECT.
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
    / "liblib-canvas-batch545-2026-09-27"
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
        assert ok, f"batch545 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/?batch70=1", wait_until="networkidle")
    page.wait_for_function(
        """() => Boolean(window.__libtv_store && window.__libtv_ui_store && window.__director_store)"""
    )

    page.evaluate(
        """() => {
          const store = window.__libtv_store.getState();
          store.addNode("script-execution", { title: "Batch 545" });
          const node = store.getActiveCanvas().nodes.at(-1);
          window.__libtv_ui_store.getState().openDirectorDesk(node.id, store.activeCanvasId);
        }"""
    )
    page.locator("[data-director-workspace]").wait_for(state="visible")
    page.wait_for_timeout(400)

    row = page.locator("[data-director-tree] [data-director-object-id]").first
    object_id = row.get_attribute("data-director-object-id")
    check("row:present", object_id is not None)

    def open_menu() -> Any:
        row.click(button="right")
        page.wait_for_timeout(200)
        return page.locator("[data-director-tree-context-menu]")

    # 菜单五项
    menu = open_menu()
    check("menu:opens", menu.is_visible())
    for action in ["group", "visibility", "lock", "duplicate", "delete"]:
        check(
            f"menu:item:{action}",
            menu.locator(f"[data-director-tree-context-action='{action}']").is_visible(),
        )

    # 显示/隐藏：可见性翻转
    visible_before = row.get_attribute("data-director-object-visible")
    menu.locator("[data-director-tree-context-action='visibility']").click()
    page.wait_for_timeout(250)
    visible_after = page.locator(
        f"[data-director-object-id='{object_id}']"
    ).get_attribute("data-director-object-visible")
    check("visibility:toggles", visible_before != visible_after)

    # 锁定/解锁：锁定态翻转
    lock_row = page.locator(f"[data-director-object-id='{object_id}']")
    lock_row.click(button="right")
    page.wait_for_timeout(200)
    page.locator("[data-director-tree-context-action='lock']").click()
    page.wait_for_timeout(250)
    check(
        "lock:toggles",
        page.locator(f"[data-director-object-lock='{object_id}']").get_attribute(
            "data-director-object-locked"
        )
        == "true",
    )

    # 创建副本：对象数增加
    objects_before = page.evaluate(
        "window.__director_store.getState().objects.length"
    )
    page.locator(f"[data-director-object-id='{object_id}']").click(
        button="right", force=True
    )
    page.wait_for_timeout(200)
    page.locator("[data-director-tree-context-action='duplicate']").click()
    page.wait_for_timeout(400)
    objects_after = page.evaluate(
        "window.__director_store.getState().objects.length"
    )
    check("duplicate:objects-increase", objects_after == objects_before + 1)

    # ESC 关闭菜单
    page.locator(f"[data-director-object-id='{object_id}']").click(
        button="right", force=True
    )
    page.wait_for_timeout(200)
    page.keyboard.press("Escape")
    page.wait_for_timeout(200)
    check("escape:closes", page.locator("[data-director-tree-context-menu]").count() == 0)

    check("diagnostics:zero", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 544,
        "title": "Scene-tree entry context menu",
        "evidence": (
            "docs/research/liblib-source-exploration-2026-09-25/NOTES.md "
            "§8 + screenshot 47-director-rightclick-tree (CDP 2026-09-28)"
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
        "Batch 545 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "five-item context menu (打组/显示隐藏/锁定解锁/创建副本/删除) wired "
        "to store actions with visibility, lock, duplicate and ESC close "
        "recorded in runtime-audit.json."
    )


if __name__ == "__main__":
    main()
