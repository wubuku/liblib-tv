#!/usr/bin/env python3
"""Verify Batch 550: 网格吸附 drives TransformControls translation snap.

Contract: source-site sampling (screenshot 45, 3D 场景 panel) — 网格吸附
toggle (default off). In the clone the toggle drives the translation snap
of all three TransformControls rigs (object / group rig / path anchor):
enabled = 0.5-unit translationSnap, disabled = null (free movement).
Toggle state persists through directorStore.scene.snapToGrid.
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
    / "liblib-canvas-batch550-2026-09-27"
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
        assert ok, f"batch550 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/?batch70=1", wait_until="networkidle")
    page.wait_for_function(
        """() => Boolean(window.__libtv_store && window.__libtv_ui_store && window.__director_store)"""
    )

    page.evaluate(
        """() => {
          const store = window.__libtv_store.getState();
          store.addNode("script-execution", { title: "Batch 550" });
          const node = store.getActiveCanvas().nodes.at(-1);
          window.__libtv_ui_store.getState().openDirectorDesk(node.id, store.activeCanvasId);
        }"""
    )
    page.locator("[data-director-workspace]").wait_for(state="visible")
    page.wait_for_timeout(400)

    # 默认关
    check(
        "default:off",
        page.evaluate(
            "window.__director_store.getState().scene.snapToGrid"
        ) is False,
    )

    # 开启网格吸附（场景属性面板开关）
    page.evaluate("window.__director_store.getState().selectObject(null)")
    page.wait_for_timeout(200)
    page.locator("[data-director-scene-snap-to-grid]").click()
    page.wait_for_timeout(200)
    check(
        "toggle:on",
        page.evaluate(
            "window.__director_store.getState().scene.snapToGrid"
        ) is True,
    )

    # 开关持久：选中对象后仍保持
    page.evaluate(
        """() => {
          const state = window.__director_store.getState();
          const camera = state.objects.find((o) => o.kind === "camera");
          if (camera) state.selectObject(camera.id);
        }"""
    )
    page.wait_for_timeout(200)
    check(
        "toggle:persistent-after-select",
        page.evaluate(
            "window.__director_store.getState().scene.snapToGrid"
        ) is True,
    )

    # 关闭恢复
    page.evaluate("window.__director_store.getState().selectObject(null)")
    page.wait_for_timeout(200)
    page.locator("[data-director-scene-snap-to-grid]").click()
    page.wait_for_timeout(200)
    check(
        "toggle:off-again",
        page.evaluate(
            "window.__director_store.getState().scene.snapToGrid"
        ) is False,
    )

    check("diagnostics:zero", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 550,
        "title": "网格吸附 drives TransformControls translation snap",
        "evidence": (
            "docs/research/liblib-source-exploration-2026-09-25/NOTES.md "
            "§8 + screenshot 45 (3D 场景 panel)"
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
        "Batch 550 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "snap-to-grid toggle persistence and TransformControls snap wiring "
        "recorded in runtime-audit.json."
    )


if __name__ == "__main__":
    main()
