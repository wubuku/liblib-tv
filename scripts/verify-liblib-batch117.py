#!/usr/bin/env python3

"""Verify Batch 117 director node card alignment with the 2026-09-06 sampling."""

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
    / "liblib-canvas-batch117-2026-09-06"
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
        assert ok, f"batch117 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(BASE_URL, wait_until="networkidle")
    page.wait_for_timeout(400)
    initial_nodes = page.locator(".react-flow__node").count()

    # 添加面板 → 导演台
    page.get_by_role("button", name="添加节点").click()
    page.wait_for_timeout(400)
    panel = page.locator("[data-liblib-overlay='add-node']")
    check("panel:open", panel.is_visible())
    entry = panel.locator("button").filter(has_text="导演台").first
    entry.click()
    page.wait_for_timeout(900)

    node = page.locator(".react-flow__node-script-execution").last
    check("node:created", node.count() >= 1)
    text = node.inner_text()
    check("card:title", "导演台" in text)
    check("card:description", "在3D空间中搭建场景并进行多视角截图" in text)
    check("card:cta", "打开导演台" in text)
    check("card:counts", "个场景对象" in text and "个机位" in text)

    # 点击 打开导演台 → R3F 工作区挂载
    node.locator("[data-open-director]").click()
    page.wait_for_timeout(4000)
    workspace = page.locator("[aria-label='3D导演台工作区']")
    check("workspace:opens", workspace.count() >= 1)
    check("workspace:r3f-canvas", page.locator("canvas").count() >= 1)

    # 退出工作区（batch50 同款 Escape 路径）
    page.keyboard.press("Escape")
    page.wait_for_timeout(2000)
    check("workspace:closes", page.locator("[aria-label='3D导演台工作区']").count() == 0)
    check(
        "nodes:preserved",
        page.locator(".react-flow__node").count() == initial_nodes + 1,
    )

    check("diagnostics:zero", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 117,
        "title": "Director node card alignment with 2026-09-06 sampling",
        "evidence": "docs/research/liblib-canvas-sampling-2026-09-06/README.md",
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
        "Batch 117 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "Director card copy (title/description/打开导演台), workspace entry via "
        "node button, close and node preservation recorded in runtime-audit.json."
    )


if __name__ == "__main__":
    main()
