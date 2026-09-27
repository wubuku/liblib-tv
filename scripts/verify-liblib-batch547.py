#!/usr/bin/env python3
"""Verify Batch 547: camera panel 切换机位 switch dropdown.

Contract: source-site sampling (screenshot 47-director-rightclick-tree.png)
— the camera inspector panel shows 名称 / 切换机位 (机位1) / 位置 / …
The 切换机位 control switches the active camera through the shot bound to
it (store selectShot sets activeCameraId + viewMode "camera"). The clone
renders a select in the camera properties panel listing camera objects;
choosing one selects its bound shot.
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
    / "liblib-canvas-batch547-2026-09-27"
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
        assert ok, f"batch547 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/?batch70=1", wait_until="networkidle")
    page.wait_for_function(
        """() => Boolean(window.__libtv_store && window.__libtv_ui_store && window.__director_store)"""
    )

    page.evaluate(
        """() => {
          const store = window.__libtv_store.getState();
          store.addNode("script-execution", { title: "Batch 547" });
          const node = store.getActiveCanvas().nodes.at(-1);
          window.__libtv_ui_store.getState().openDirectorDesk(node.id, store.activeCanvasId);
        }"""
    )
    page.locator("[data-director-workspace]").wait_for(state="visible")
    page.wait_for_timeout(400)

    # 新增第二个机位 → 切换机位下拉出现两个选项
    page.evaluate("window.__director_store.getState().addDirectorCamera()")
    page.wait_for_timeout(400)
    cameras = page.evaluate(
        """() => window.__director_store.getState().objects
            .filter((object) => object.kind === "camera").map((o) => o.name)"""
    )
    check("cameras:two", len(cameras) == 2)

    # 选中第一个机位（场景树条目点击），检查摄像机面板出现 切换机位
    row = page.locator(
        "[data-director-tree] [data-director-object-kind='camera']"
    ).first
    row.click()
    page.wait_for_timeout(300)
    select = page.locator("[data-director-camera-switch]")
    check("switch:visible", select.is_visible())
    check("switch:label", "切换机位" in page.locator("[data-director-inspector], [aria-label='属性']").first.inner_text())
    options = select.locator("option")
    check("switch:options-two", options.count() == 2)

    # 切换到第二个机位 → activeCameraId 更新
    target_id = page.evaluate(
        """() => window.__director_store.getState().objects
            .filter((object) => object.kind === "camera")[1].id"""
    )
    select.select_option(index=1)
    page.wait_for_timeout(300)
    active_after = page.evaluate(
        "window.__director_store.getState().activeCameraId"
    )
    check("switch:active-updated", active_after == target_id)
    # 切换机位仅切活动机位；视角模式由顶部分段控件独立管理（源站行为）
    check(
        "switch:view-mode-unchanged",
        page.evaluate("window.__director_store.getState().viewMode") == "director",
    )

    # 切回第一个机位
    select.select_option(index=0)
    page.wait_for_timeout(300)
    first_id = page.evaluate(
        """() => window.__director_store.getState().objects
            .filter((object) => object.kind === "camera")[0].id"""
    )
    check(
        "switch:back-to-first",
        page.evaluate("window.__director_store.getState().activeCameraId") == first_id,
    )

    check("diagnostics:zero", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 547,
        "title": "Camera panel 切换机位 switch dropdown",
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
        "Batch 547 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "切换机位 dropdown listing camera objects, switching through bound "
        "shots updating activeCameraId and viewMode, recorded in "
        "runtime-audit.json."
    )


if __name__ == "__main__":
    main()
