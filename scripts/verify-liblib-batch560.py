#!/usr/bin/env python3
"""Verify Batch 559: scene transform (scale/translate/rotate) controls.

Contract: source-site sampling (screenshots 45/48, 3D 场景 panel top
section) — 场景缩放 slider (clone default 1 = 100%; source session showed
300%), 场景平移 XYZ inputs and 场景旋转 XYZ inputs. The Inspector renders
a 场景变换 section persisting through updateScene; the viewport wraps the
scene content (objects + groups) in a transform group applying scale /
translate / rotate. Ground, grid, lights and the panorama sphere are
helpers outside the group.
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
    / "liblib-canvas-batch560-2026-09-29"
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
        assert ok, f"batch560 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/?batch70=1", wait_until="networkidle")
    page.wait_for_function(
        """() => Boolean(window.__libtv_store && window.__libtv_ui_store && window.__director_store)"""
    )

    page.evaluate(
        """() => {
          const store = window.__libtv_store.getState();
          store.addNode("script-execution", { title: "Batch 560" });
          const node = store.getActiveCanvas().nodes.at(-1);
          window.__libtv_ui_store.getState().openDirectorDesk(node.id, store.activeCanvasId);
        }"""
    )
    page.locator("[data-director-workspace]").wait_for(state="visible")
    page.wait_for_timeout(400)

    page.evaluate("window.__director_store.getState().selectObject(null)")
    page.wait_for_timeout(300)

    section = page.locator("[data-director-scene-transform]")
    check("section:visible", section.is_visible())

    # 缩放滑杆：1.5 → 150%
    section.locator("[data-director-scene-scale]").evaluate(
        """(el) => {
          const setter = Object.getOwnPropertyDescriptor(
            window.HTMLInputElement.prototype, 'value'
          ).set;
          setter.call(el, '1.5');
          el.dispatchEvent(new Event('input', { bubbles: true }));
          el.dispatchEvent(new Event('change', { bubbles: true }));
        }"""
    )
    page.wait_for_timeout(150)
    check(
        "scale:persist",
        page.evaluate(
            "window.__director_store.getState().scene.sceneScale"
        ) == 1.5,
    )
    check("scale:label", "150%" in section.inner_text())

    # 平移 X 输入
    page.locator("[data-director-scene-translate='0']").fill("1.2")
    page.wait_for_timeout(150)
    check(
        "translate:persist",
        page.evaluate(
            "window.__director_store.getState().scene.sceneTranslate[0]"
        ) == 1.2,
    )

    # 旋转 Y 输入
    page.locator("[data-director-scene-rotate='1']").fill("45")
    page.wait_for_timeout(150)
    check(
        "rotate:persist",
        page.evaluate(
            "window.__director_store.getState().scene.sceneRotate[1]"
        ) == 45,
    )

    # 持久化后再断言其余轴默认值
    check(
        "translate:others-default",
        page.evaluate(
            "window.__director_store.getState().scene.sceneTranslate.slice(1)"
        ) == [0, 0],
    )

    check("diagnostics:zero", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 560,
        "title": "Scene transform (scale/translate/rotate) controls",
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
        "Batch 560 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "scene transform section (scale slider with % label, translate and "
        "rotate axis inputs) persisting through updateScene recorded in "
        "runtime-audit.json."
    )


if __name__ == "__main__":
    main()
