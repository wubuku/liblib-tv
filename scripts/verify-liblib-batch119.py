#!/usr/bin/env python3

"""Verify Batch 119 /project list page."""

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
    / "liblib-canvas-batch119-2026-09-06"
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
        assert ok, f"batch119 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/project", wait_until="networkidle")
    page.wait_for_timeout(500)

    page_root = page.locator("[data-project-list-page]")
    check("page:mounted", page_root.is_visible())
    check("header:back", page_root.locator("[data-project-back]").is_visible())
    check("header:title", page_root.get_by_text("全部项目", exact=True).is_visible())
    check("header:recycle", page_root.locator("[data-project-recycle]").is_visible())
    check("header:folder", page_root.locator("[data-project-new-folder]").is_visible())
    check("create:card", page_root.locator("[data-project-create-card]").is_visible())
    check(
        "create:copy",
        "开始创作" in page_root.locator("[data-project-create-card]").inner_text()
        and "创建新的视频项目" in page_root.locator("[data-project-create-card]").inner_text(),
    )

    page_root.locator("[data-project-recycle]").click()
    check("recycle:status", "本地原型" in page.locator("[data-project-list-status]").inner_text())

    # 创建卡 → 新建画布并回画布
    page_root.locator("[data-project-create-card]").click()
    page.wait_for_timeout(800)
    check(
        "create:navigates-to-canvas",
        page.url.rstrip("/").endswith(BASE_URL.split("//")[1].split("/")[0]) or "/project" not in page.url,
    )
    check(
        "create:new-canvas-active",
        page.get_by_role("button", name="画布 3", exact=True).count() == 1,
    )

    # logo 菜单 全部项目 → /project
    page.locator("[data-project-menu-trigger]").click()
    page.wait_for_timeout(400)
    page.evaluate("""() => {
      const items = Array.from(document.querySelectorAll("[data-project-menu-item]")).filter((b) => b.textContent.trim() === "全部项目");
      items[0].click();
    }""")
    page.wait_for_timeout(800)
    check(
        "menu:navigates-to-project",
        page.url.endswith("/project"),
    )
    check(
        "menu:page-visible",
        page.locator("[data-project-list-page]").is_visible(),
    )

    # 画布卡点击 → 激活并回画布
    page.evaluate("""() => {
      const card = document.querySelector("[data-project-card='canvas-1']");
      if (card) card.click();
    }""")
    page.wait_for_timeout(800)
    check(
        "card:navigates-back",
        not page.url.endswith("/project"),
    )
    check(
        "card:canvas-1-active",
        page.get_by_role("button", name="画布 1", exact=True).count() == 1,
    )

    check("diagnostics:zero", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 119,
        "title": "/project list page implementation",
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
        "Batch 119 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "Project page structure, recycle/folder local statuses, create-card "
        "canvas creation, card navigation and logo-menu routing recorded in "
        "runtime-audit.json."
    )


if __name__ == "__main__":
    main()
