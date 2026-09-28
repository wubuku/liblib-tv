#!/usr/bin/env python3
"""Verify Batch 566: ground height field wired end-to-end.

Contract: source-site sampling (screenshot 52, 3D 场景 panel 地面 section)
— 地面 has 透明度 0.40 slider plus a 高度 0.0 slider (missed in batch
548). In the clone: scene.groundHeight (default 0), Inspector 地面高度
slider (-2..2, step 0.1) persisting through updateScene, and the ground
plane mesh positioned at groundHeight - 0.01 in the viewport.
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
    / "liblib-canvas-batch566-2026-09-29"
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
        assert ok, f"batch566 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/?batch70=1", wait_until="networkidle")
    page.wait_for_function(
        """() => Boolean(window.__libtv_store && window.__libtv_ui_store && window.__director_store)"""
    )

    page.evaluate(
        """() => {
          const store = window.__libtv_store.getState();
          store.addNode("script-execution", { title: "Batch 563" });
          const node = store.getActiveCanvas().nodes.at(-1);
          window.__libtv_ui_store.getState().openDirectorDesk(node.id, store.activeCanvasId);
        }"""
    )
    page.locator("[data-director-workspace]").wait_for(state="visible")
    page.wait_for_timeout(400)

    page.evaluate("window.__director_store.getState().selectObject(null)")
    page.wait_for_timeout(300)

    check(
        "defaults:zero",
        page.evaluate(
            "window.__director_store.getState().scene.groundHeight"
        ) == 0,
    )
    slider = page.locator("[data-director-scene-ground-height]")
    check("slider:visible", slider.is_visible())

    slider.evaluate(
        """(el) => {
          const setter = Object.getOwnPropertyDescriptor(
            window.HTMLInputElement.prototype, 'value'
          ).set;
          setter.call(el, '0.5');
          el.dispatchEvent(new Event('input', { bubbles: true }));
          el.dispatchEvent(new Event('change', { bubbles: true }));
        }"""
    )
    page.wait_for_timeout(200)
    check(
        "height:persist",
        page.evaluate(
            "window.__director_store.getState().scene.groundHeight"
        ) == 0.5,
    )
    check(
        "height:label",
        "0.5" in slider.locator("xpath=..").inner_text(),
    )

    # 负值也支持（-2..2 范围）
    slider.evaluate(
        """(el) => {
          const setter = Object.getOwnPropertyDescriptor(
            window.HTMLInputElement.prototype, 'value'
          ).set;
          setter.call(el, '-1');
          el.dispatchEvent(new Event('input', { bubbles: true }));
          el.dispatchEvent(new Event('change', { bubbles: true }));
        }"""
    )
    page.wait_for_timeout(200)
    check(
        "height:negative",
        page.evaluate(
            "window.__director_store.getState().scene.groundHeight"
        ) == -1,
    )

    check("diagnostics:zero", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 566,
        "title": "Ground height field wired end-to-end",
        "evidence": (
            "docs/research/liblib-source-exploration-2026-09-25/NOTES.md "
            "§8 + screenshot 52-director-trail-menu.png (地面 section)"
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
        "Batch 566 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "ground height slider persisting through updateScene (positive and "
        "negative values) recorded in runtime-audit.json."
    )


if __name__ == "__main__":
    main()
