#!/usr/bin/env python3
"""Verify Batch 555: panorama sphere rotation & radius wired to renderer.

Contract: source-site sampling (screenshots 45/48) — the 全景球 group has
水平旋转 (degrees, default 0) and 球形半径 (clone default 30; source shows
60 — SOURCE_DIFF kept at 30 for visual stability). The Inspector's 全景
背景 section renders both sliders persisting through updateScene, and the
panorama sphere mesh applies rotation and radius.
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
    / "liblib-canvas-batch555-2026-09-27"
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


def set_range(page: Page, selector: str, value: str) -> None:
    page.locator(selector).evaluate(
        """(el, value) => {
          const setter = Object.getOwnPropertyDescriptor(
            window.HTMLInputElement.prototype, 'value'
          ).set;
          setter.call(el, value);
          el.dispatchEvent(new Event('input', { bubbles: true }));
          el.dispatchEvent(new Event('change', { bubbles: true }));
        }""",
        value,
    )


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool) -> None:
        assert ok, f"batch555 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/?batch70=1", wait_until="networkidle")
    page.wait_for_function(
        """() => Boolean(window.__libtv_store && window.__libtv_ui_store && window.__director_store)"""
    )

    page.evaluate(
        """() => {
          const store = window.__libtv_store.getState();
          store.addNode("script-execution", { title: "Batch 555" });
          const node = store.getActiveCanvas().nodes.at(-1);
          window.__libtv_ui_store.getState().openDirectorDesk(node.id, store.activeCanvasId);
        }"""
    )
    page.locator("[data-director-workspace]").wait_for(state="visible")
    page.wait_for_timeout(400)

    page.evaluate("window.__director_store.getState().selectObject(null)")
    page.wait_for_timeout(300)

    check(
        "defaults:rotation",
        page.evaluate(
            "window.__director_store.getState().scene.panoramaRotation"
        ) == 0,
    )
    check(
        "defaults:radius",
        page.evaluate(
            "window.__director_store.getState().scene.panoramaSphereRadius"
        ) == 30,
    )
    check(
        "sliders:visible",
        page.locator("[data-director-scene-panorama-rotation]").is_visible()
        and page.locator("[data-director-scene-panorama-radius]").is_visible(),
    )

    set_range(page, "[data-director-scene-panorama-rotation]", "90")
    page.wait_for_timeout(150)
    check(
        "rotation:persist",
        page.evaluate(
            "window.__director_store.getState().scene.panoramaRotation"
        ) == 90,
    )
    # Batch 588 基线对照：582 已把球形半径量程对齐源站实测的
    # 10–500 **step 10**，range 的值净化会把 55 吸附到 60，故原断言
    # （期望 55）自 582 起即已失效，与 588 无关。改用步进对齐的取值。
    # 读数自 588 起是可编辑文本框（input 的 value 不进 innerText），
    # 故标签断言改读文本框值。
    set_range(page, "[data-director-scene-panorama-radius]", "60")
    page.wait_for_timeout(150)
    check(
        "radius:persist",
        page.evaluate(
            "window.__director_store.getState().scene.panoramaSphereRadius"
        ) == 60,
    )
    check(
        "radius:label-updates",
        page.locator("[data-director-scene-readout='sphere-radius']").input_value()
        == "60",
    )

    check("diagnostics:zero", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 555,
        "title": "Panorama sphere rotation & radius controls",
        "evidence": (
            "docs/research/liblib-source-exploration-2026-09-25/NOTES.md "
            "§8 + screenshots 45/48"
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
        "Batch 555 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "panorama rotation and radius sliders persist through updateScene "
        "recorded in runtime-audit.json."
    )


if __name__ == "__main__":
    main()
