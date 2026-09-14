#!/usr/bin/env python3
"""Verify Batch 504: VR-018 catalog completeness — project menu local
status line carries an explicit disposition tone.

Contract: docs/research/LIBTV_COMMAND_OUTCOME_FEEDBACK_CONTRACT.md §16 /
§2.2 inventory spirit — every ordinary LibTV command surface presenting
command outcomes joins the catalog with a stable disposition. The project
menu's prototype-unavailable items (回到主页/创建新项目/删除项目) project
rejected → diagnostic; 全部项目 navigates and presents no feedback.

Scenes:
- project_item_diagnostic: 回到主页 / 创建新项目 surface
  data-status-tone="diagnostic" with the existing prototype copy;
- nav_item_silent: 全部项目 closes the menu, navigates to /project, and
  leaves no command feedback (unmount clears the local status).
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
URL = os.environ.get("LIBLIB_BASE_URL", "http://localhost:4317")
AUDIT_PATH = (
    ROOT
    / "docs"
    / "research"
    / "liblib-canvas-batch504-2026-09-14"
    / "runtime-audit.json"
)
SCREENSHOT_PATH = (
    ROOT
    / "docs"
    / "design-references"
    / "liblib-clone-batch504-project-menu-tones-929-2026-09-14.png"
)


def attach_errors(page: Page):
    errors = []
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


def menu_status(page: Page):
    return page.evaluate(
        """() => {
          const el = document.querySelector('[data-project-menu-status]');
          return el ? { text: el.innerText, tone: el.dataset.statusTone } : null;
        }"""
    )


def open_menu(page: Page):
    page.locator("[data-project-menu-trigger]").click()
    page.locator("[data-project-menu]").wait_for(state="visible")


def main():
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    SCREENSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)

    errors = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(
            viewport={"width": 929, "height": 874}, device_scale_factor=1
        )
        errors.extend(attach_errors(page))
        page.goto(URL, wait_until="networkidle")
        page.wait_for_timeout(450)

        # Scene 1: prototype-unavailable items → diagnostic.
        open_menu(page)
        page.locator('[data-project-menu-item="回到主页"]').click()
        page.wait_for_timeout(120)
        home_status = menu_status(page)
        assert home_status == {
            "text": "本地原型：回到主页未接入",
            "tone": "diagnostic",
        }, home_status

        page.locator('[data-project-menu-item="创建新项目"]').click()
        page.wait_for_timeout(120)
        create_status = menu_status(page)
        assert create_status == {
            "text": "本地原型：创建新项目未接入",
            "tone": "diagnostic",
        }, create_status

        page.screenshot(path=str(SCREENSHOT_PATH))

        # Scene 2: the navigating item closes silently (menu is still open
        # from scene 1 — unavailable-item clicks do not dismiss it).
        page.locator('[data-project-menu-item="全部项目"]').click()
        page.wait_for_url("**/project", timeout=8000)
        page.wait_for_timeout(300)
        nav_state = {
            "menuVisible": page.locator("[data-project-menu]").count() > 0,
            "statusElement": page.evaluate(
                "!!document.querySelector('[data-project-menu-status]')"
            ),
            "path": page.evaluate("window.location.pathname"),
        }
        assert nav_state["path"] == "/project", nav_state
        assert not nav_state["menuVisible"], nav_state
        assert not nav_state["statusElement"], nav_state

        browser.close()
    assert not errors, errors

    audit = {
        "url": URL,
        "status": "SCRIPT_RECORDED_PASS",
        "slice": "VR-018 catalog completeness — project menu status line "
        "carries explicit disposition tones; nav item stays silent",
        "scenes": {
            "project_home_diagnostic": home_status,
            "project_create_diagnostic": create_status,
            "project_list_silent_nav": nav_state,
        },
        "errors": {"console": [], "page": [], "request": []},
    }
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    print(
        "Batch 504 verification passed: project menu status projects "
        "diagnostic tones via the VR-018 catalog; 全部项目 navigates "
        "silently; recorded in runtime-audit.json."
    )


if __name__ == "__main__":
    main()
