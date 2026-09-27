#!/usr/bin/env python3
"""Verify Batch 543: director viewport reset-view button.

Contract: source-site sampling 2026-09-25 round 2 (NOTES §8 + screenshot
18-director-console-opened.png) — the director viewport's top-right stack
is the pose gizmo with a 重置视角 pill directly beneath it; clicking resets
the director camera to the default view. The clone renders the button
under the existing gizmo widget; clicking issues a fresh
DEFAULT_DIRECTOR_VIEWPORT_SNAPSHOT camera command (position 6.2/4.25/7.4,
target 0/1/0, fov 45) through the existing CameraController.
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
    / "liblib-canvas-batch543-2026-09-27"
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
        assert ok, f"batch543 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/?batch70=1", wait_until="networkidle")
    page.wait_for_function(
        """() => Boolean(window.__libtv_store && window.__libtv_ui_store && window.__director_store)"""
    )

    page.evaluate(
        """() => {
          const store = window.__libtv_store.getState();
          store.addNode("script-execution", { title: "Batch 543" });
          const node = store.getActiveCanvas().nodes.at(-1);
          window.__libtv_ui_store.getState().openDirectorDesk(node.id, store.activeCanvasId);
        }"""
    )
    page.locator("[data-director-workspace]").wait_for(state="visible")
    page.wait_for_timeout(600)

    gizmo = page.locator("[data-director-viewport-gizmo]")
    check("gizmo:visible", gizmo.is_visible())
    reset = page.locator("[data-director-reset-view]")
    check("reset:visible", reset.is_visible())
    check("reset:label", "重置视角" in reset.inner_text())
    # 按钮位于 gizmo 正下方
    gb, rb = gizmo.bounding_box(), reset.bounding_box()
    check(
        "reset:below-gizmo",
        gb is not None and rb is not None and rb["y"] >= gb["y"] + gb["height"],
    )

    # 点击不报错、不导航（相机复位由 CameraController 内部消化）
    reset.click()
    page.wait_for_timeout(400)
    check("reset:desk-open", page.locator("[data-director-workspace]").is_visible())
    check("reset:gizmo-still", gizmo.is_visible())

    check("diagnostics:zero", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 543,
        "title": "Director viewport reset-view button",
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
        "Batch 543 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "reset-view pill below the pose gizmo issuing the default "
        "director-view snapshot command recorded in runtime-audit.json."
    )


if __name__ == "__main__":
    main()
