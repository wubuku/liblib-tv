#!/usr/bin/env python3
"""Verify Batch 548: scene display settings extension.

Contract: source-site sampling (screenshot 18-director-console-opened.png /
45-director-rightclick-viewport.png) — the 3D 场景 panel's display section
includes 天空颜色 (#060608), 角色标签 toggle (on), 网格吸附 toggle (off),
高斯地面吸附 toggle (on) and 地面透明度 slider (0.40). The clone's scene
schema gains these fields additively (old V1 documents decode without
them and fall back to createDefaultScene values). Values persist through
updateScene and round-trip via store snapshot.
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
    / "liblib-canvas-batch548-2026-09-27"
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
        assert ok, f"batch548 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/?batch70=1", wait_until="networkidle")
    page.wait_for_function(
        """() => Boolean(window.__libtv_store && window.__libtv_ui_store && window.__director_store)"""
    )

    page.evaluate(
        """() => {
          const store = window.__libtv_store.getState();
          store.addNode("script-execution", { title: "Batch 548" });
          const node = store.getActiveCanvas().nodes.at(-1);
          window.__libtv_ui_store.getState().openDirectorDesk(node.id, store.activeCanvasId);
        }"""
    )
    page.locator("[data-director-workspace]").wait_for(state="visible")
    page.wait_for_timeout(400)

    # 清空选择 → 场景属性面板
    page.evaluate(
        "window.__director_store.getState().selectObject(null)"
    )
    page.wait_for_timeout(300)

    check(
        "defaults:sky-color",
        page.evaluate(
            "window.__director_store.getState().scene.skyColor"
        ) == "#060608",
    )
    check(
        "defaults:labels-on",
        page.evaluate(
            "window.__director_store.getState().scene.showCharacterLabels"
        ) is True,
    )
    check(
        "defaults:snap-off",
        page.evaluate(
            "window.__director_store.getState().scene.snapToGrid"
        ) is False,
    )
    check(
        "defaults:gaussian-on",
        page.evaluate(
            "window.__director_store.getState().scene.gaussianGroundSnap"
        ) is True,
    )
    check(
        "defaults:opacity",
        page.evaluate(
            "window.__director_store.getState().scene.groundOpacity"
        ) == 0.4,
    )

    # 控件渲染 + 切换持久化
    toggles = {
        "character-labels": ("showCharacterLabels", True),
        "snap-to-grid": ("snapToGrid", False),
        "gaussian-snap": ("gaussianGroundSnap", True),
    }
    for data_key, (field, _initial) in toggles.items():
        page.locator(f"[data-director-scene-{data_key}]").click()
        page.wait_for_timeout(150)
        check(
            f"toggle:{data_key}",
            page.evaluate(
                f"window.__director_store.getState().scene.{field}"
            )
            == (not _initial),
        )
        page.locator(f"[data-director-scene-{data_key}]").click()
        page.wait_for_timeout(150)

    page.locator("[data-director-scene-ground-opacity]").evaluate(
        """(el) => {
          const setter = Object.getOwnPropertyDescriptor(
            window.HTMLInputElement.prototype, 'value'
          ).set;
          setter.call(el, '0.75');
          el.dispatchEvent(new Event('input', { bubbles: true }));
          el.dispatchEvent(new Event('change', { bubbles: true }));
        }"""
    )
    page.wait_for_timeout(200)
    check(
        "opacity:persistent",
        page.evaluate(
            "window.__director_store.getState().scene.groundOpacity"
        ) == 0.75,
    )

    check("diagnostics:zero", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 548,
        "title": "Scene display settings extension",
        "evidence": (
            "docs/research/liblib-source-exploration-2026-09-25/NOTES.md "
            "§8 + screenshots 18/45"
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
        "Batch 548 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "scene defaults (skyColor/labels/snap/gaussian/opacity) and "
        "persistent toggles recorded in runtime-audit.json."
    )


if __name__ == "__main__":
    main()
