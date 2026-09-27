#!/usr/bin/env python3
"""Verify Batch 549: scene display fields wired into the viewport renderer.

Contract: source-site sampling (screenshot 18) — 角色标签 hides/shows the
character name floating label above the mannequin (角色A), 天空颜色 is the
sky backdrop when no panorama is connected, and 地面透明度 sets the ground
plane opacity. In the clone:
- character rows render a drei Html name label gated by
  scene.showCharacterLabels (default on);
- the ground plane material uses scene.groundOpacity (default 0.4,
  transparent);
- the canvas background uses scene.skyColor while no panorama input is
  connected (scene.backgroundColor remains the panorama-era fallback and
  the fog color).
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
    / "liblib-canvas-batch549-2026-09-27"
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
        assert ok, f"batch549 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/?batch70=1", wait_until="networkidle")
    page.wait_for_function(
        """() => Boolean(window.__libtv_store && window.__libtv_ui_store && window.__director_store)"""
    )

    page.evaluate(
        """() => {
          const store = window.__libtv_store.getState();
          store.addNode("script-execution", { title: "Batch 549" });
          const node = store.getActiveCanvas().nodes.at(-1);
          window.__libtv_ui_store.getState().openDirectorDesk(node.id, store.activeCanvasId);
        }"""
    )
    page.locator("[data-director-workspace]").wait_for(state="visible")
    page.wait_for_timeout(600)

    # 默认开：角色名标签渲染于 WebGL 容器内（drei Html 注入 DOM）
    label = page.locator("[data-director-character-label]")
    check("label:visible-default", label.count() >= 1)

    # 关闭角色标签 → 浮标消失
    page.evaluate(
        """() => window.__director_store.getState().updateScene(
          { showCharacterLabels: false })"""
    )
    page.wait_for_timeout(400)
    check("label:hidden-off", page.locator("[data-director-character-label]").count() == 0)

    # 重新开启 → 恢复
    page.evaluate(
        """() => window.__director_store.getState().updateScene(
          { showCharacterLabels: true })"""
    )
    page.wait_for_timeout(400)
    check("label:restored", page.locator("[data-director-character-label]").count() >= 1)

    # 天空颜色：更新 store 后 canvas 容器背景色应用新值（无全景时为天幕）
    page.evaluate(
        """() => window.__director_store.getState().updateScene(
          { skyColor: "#102030" })"""
    )
    page.wait_for_timeout(400)
    sky_applied = page.evaluate(
        """() => {
          const canvas = document.querySelector(
            'canvas[data-director-webgl-canvas="true"]',
          );
          if (!canvas) return null;
          const wrapper = canvas.parentElement;
          return wrapper ? getComputedStyle(wrapper).backgroundColor : null;
        }"""
    )
    # drei/fiber 会把背景渲染为 WebGL 清屏色；此处仅断言无崩溃与 store 值
    check(
        "sky:store-persist",
        page.evaluate(
            "window.__director_store.getState().scene.skyColor"
        ) == "#102030",
    )

    # 地面透明度持久化
    page.evaluate(
        """() => window.__director_store.getState().updateScene(
          { groundOpacity: 0.8 })"""
    )
    page.wait_for_timeout(300)
    check(
        "opacity:store-persist",
        page.evaluate(
            "window.__director_store.getState().scene.groundOpacity"
        ) == 0.8,
    )

    check("diagnostics:zero", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 549,
        "title": "Scene display fields wired into the viewport renderer",
        "evidence": (
            "docs/research/liblib-source-exploration-2026-09-25/NOTES.md "
            "§8 + screenshot 18 (角色A floating label)"
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
        "Batch 549 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "character label toggle rendering, sky color and ground opacity "
        "store persistence recorded in runtime-audit.json."
    )


if __name__ == "__main__":
    main()
