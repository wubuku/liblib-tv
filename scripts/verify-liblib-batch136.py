#!/usr/bin/env python3

"""Verify Batch 136 recycle bin selection counter and batch restore."""

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
    / "liblib-canvas-batch136-2026-09-06"
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
        assert ok, f"batch136 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/project", wait_until="domcontentloaded")
    page.wait_for_timeout(600)
    page_root = page.locator("[data-project-list-page]")
    page_root.locator("[data-project-recycle]").click()
    page.wait_for_timeout(300)
    panel = page.locator("[data-recycle-panel]")
    check("panel:empty", panel.locator("[data-recycle-empty]").is_visible())

    # 删除 画布 2 制造回收站条目
    page.goto(f"{BASE_URL}", wait_until="domcontentloaded")
    page.wait_for_timeout(600)
    open_dd = page.locator("[data-liblib-overlay='canvas-dropdown']")
    if not open_dd.is_visible():
        page.get_by_role("button", name="画布 2", exact=True).first.click()
        page.wait_for_timeout(400)
    dd = page.locator("[data-liblib-overlay='canvas-dropdown']")
    row2 = dd.locator("[data-canvas-row='canvas-2']")
    row2.hover()
    page.wait_for_timeout(250)
    row2.locator("button[aria-label='更多操作']").click(force=True)
    page.wait_for_timeout(300)
    dd.get_by_text("删除画布", exact=True).click()
    page.wait_for_timeout(400)
    page.locator("[data-canvas-delete-confirm]").get_by_text("确认", exact=True).click()
    page.wait_for_timeout(700)

    # 客户端导航回 /project
    page.locator("[data-project-menu-trigger]").click()
    page.wait_for_timeout(300)
    page.evaluate("""() => {
      const items = Array.from(document.querySelectorAll("[data-project-menu-item]")).filter((b) => b.textContent.trim() === "全部项目");
      items[0].click();
    }""")
    page.wait_for_timeout(900)
    page_root = page.locator("[data-project-list-page]")
    page_root.locator("[data-project-recycle]").click()
    page.wait_for_timeout(300)

    counter = page_root.locator("[data-recycle-selection]")
    print("DEBUG:", page.evaluate("""() => ({
      url: location.href.slice(0, 80),
      pageMounted: Boolean(document.querySelector('[data-project-list-page]')),
      panel: Boolean(document.querySelector('[data-recycle-panel]')),
      counter: Boolean(document.querySelector('[data-recycle-selection]')),
      removed: window.__libtv_store.getState().removedCanvases.map((c) => c.name),
    })"""))
    check("selection:zero", "已选择 0 项" in counter.inner_text())
    row2_check = page_root.locator("[data-recycle-check='canvas-2']")
    check("checkbox:present", row2_check.count() == 1)
    row2_check.click(force=True)
    page.wait_for_timeout(200)
    check("selection:one", "已选择 1 项" in counter.inner_text())
    restore_selected = page_root.locator("[data-recycle-restore-selected]")
    check("batch:button", restore_selected.is_visible() and "恢复所选 1 项" in restore_selected.inner_text())
    restore_selected.click()
    page.wait_for_timeout(700)
    check(
        "batch:restored-to-list",
        page.evaluate(
            "() => Array.from(document.querySelectorAll('[data-project-card]')).map((e) => e.getAttribute('data-project-card')).includes('canvas-2')",
        ),
    )
    # Batch 136: 恢复唯一条目后回收站为空，计数器随非空分支一起消失。
    check(
        "batch:selection-cleared",
        page.locator("[data-recycle-empty]").is_visible(),
    )

    check("diagnostics:zero", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 136,
        "title": "Recycle bin selection counter and batch restore",
        "evidence": "docs/research/liblib-projects-page-2026-09-06/README.md",
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
        "Batch 136 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "Selection counter, checkbox, batch restore button and state cleanup "
        "recorded in runtime-audit.json."
    )


if __name__ == "__main__":
    main()
