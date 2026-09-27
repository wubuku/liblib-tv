#!/usr/bin/env python3
"""Verify Batch 541: character flyout preset items local-equivalent actions.

Contract: source-site sampling (screenshot 44-director-rail-23, batch 537)
— the 添加角色 flyout lists 本地上传, eight preset body types and two
submenu rows. On the source, presets spawn 3D character variants; the
clone has no per-variant 3D spawning, so:
- 群众 (3x3) runs the local-equivalent addCrowdArray({3,3,1.2}) — the
  same action the DirectorViewport crowd panel uses — and flashes a
  local acknowledgement;
- preset body types flash a 本地等效占位 acknowledgement (no 3D model
  generated, no cloud action);
- 本地上传/几何模型 close the flyout silently.
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
    / "liblib-canvas-batch541-2026-09-27"
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
        assert ok, f"batch541 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/?batch70=1", wait_until="networkidle")
    page.wait_for_function(
        """() => Boolean(window.__libtv_store && window.__libtv_ui_store && window.__director_store)"""
    )

    page.evaluate(
        """() => {
          const store = window.__libtv_store.getState();
          store.addNode("script-execution", { title: "Batch 541" });
          const node = store.getActiveCanvas().nodes.at(-1);
          window.__libtv_ui_store.getState().openDirectorDesk(node.id, store.activeCanvasId);
        }"""
    )
    page.locator("[data-director-workspace]").wait_for(state="visible")
    page.wait_for_timeout(400)

    objects_before = page.evaluate(
        "window.__director_store.getState().objects.length"
    )

    rail = page.locator("[data-director-icon-rail]")
    rail.locator("[data-director-rail-entry='add-character']").click()
    page.wait_for_timeout(200)
    flyout = page.locator("[data-director-character-flyout]")
    check("flyout:opens", flyout.is_visible())

    # 群众 (3x3) → 本地等效 addCrowdArray：对象数增加 + ack 回显
    flyout.locator("[data-director-character-option='crowd-3x3']").click()
    page.wait_for_timeout(300)
    objects_after = page.evaluate(
        "window.__director_store.getState().objects.length"
    )
    check("crowd:objects-increase", objects_after > objects_before)
    ack = page.locator("[data-director-character-ack]")
    check("crowd:ack", "已加入群众 (3x3)" in ack.inner_text())
    check("crowd:flyout-closes", flyout.count() == 0)

    # 预设体型 → 本地等效占位回显（无 3D 生成，对象数不变）
    rail.locator("[data-director-rail-entry='add-character']").click()
    page.wait_for_timeout(200)
    before_preset = page.evaluate(
        "window.__director_store.getState().objects.length"
    )
    flyout.locator("[data-director-character-option='standard-male']").click()
    page.wait_for_timeout(250)
    check("preset:ack", "本地等效占位" in ack.inner_text())
    check(
        "preset:no-3d-spawn",
        page.evaluate("window.__director_store.getState().objects.length") == before_preset,
    )
    check("preset:flyout-closes", flyout.count() == 0)

    # ack 自动淡出
    page.wait_for_timeout(2200)
    check("ack:auto-dismiss", page.locator("[data-director-character-ack]").count() == 0)

    check("diagnostics:zero", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 541,
        "title": "Character flyout presets local-equivalent actions",
        "evidence": (
            "docs/research/liblib-source-exploration-2026-09-25/NOTES.md "
            "§8 + screenshot 44-director-rail-23 (batch 537)"
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
        "Batch 541 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "crowd 3x3 runs the shared addCrowdArray local equivalent with "
        "acknowledgement, preset types flash a local-equivalent notice "
        "without spawning 3D models, recorded in runtime-audit.json."
    )


if __name__ == "__main__":
    main()
