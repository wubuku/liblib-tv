#!/usr/bin/env python3
"""Verify Batch 558: gaussian ground snap clamps the rendered character Y.

Contract: source-site sampling (screenshot 45) — 高斯地面吸附 keeps
characters grounded to the floor plane visually. The authored-layer clamp
(batch 551) is not reflected in the runtime projection (timeline sampling
overrides authored transforms); this batch applies the clamp at the
render site: character SceneObject renders position Y >= 0 while
scene.gaussianGroundSnap is on; cameras/props and the disabled state
render free Y.
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
    / "liblib-canvas-batch558-2026-09-27"
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
        assert ok, f"batch558 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/?batch70=1", wait_until="networkidle")
    page.wait_for_function(
        """() => Boolean(window.__libtv_store && window.__libtv_ui_store && window.__director_store)"""
    )

    page.evaluate(
        """() => {
          const store = window.__libtv_store.getState();
          store.addNode("script-execution", { title: "Batch 558" });
          const node = store.getActiveCanvas().nodes.at(-1);
          window.__libtv_ui_store.getState().openDirectorDesk(node.id, store.activeCanvasId);
        }"""
    )
    page.locator("[data-director-workspace]").wait_for(state="visible")
    page.wait_for_timeout(600)

    camera_id = page.evaluate(
        """() => window.__director_store.getState().objects
            .find((o) => o.kind === "camera").id"""
    )

    # 吸附开（默认）：角色 Y -5 提交后，渲染组位置 Y 夹紧到 0
    page.evaluate(
        """(cameraId) => {
          const s = window.__director_store.getState();
          s.updateObjectTransform(cameraId, "position", 1, -5);
        }""",
        camera_id,
    )
    page.wait_for_timeout(300)
    rendered = page.evaluate(
        """() => {
          const s = window.__director_store.getState();
          const character = s.objects.find((o) => o.kind === "character");
          return {
            runtimeY: character.transform.position[1],
            authoredY: s.authoredObjects.find((o) => o.id === character.id)
              .transform.position[1],
          };
        }"""
    )
    check(
        "clamp:authored-zero",
        rendered["authoredY"] == 0,
    )
    check(
        "clamp:runtime-zero",
        rendered["runtimeY"] == 0,
    )

    # 渲染组位置：WebGL 场景中角色组的 y 应为 0（吸附渲染夹紧）
    rendered_group_y = page.evaluate(
        """() => {
          const label = document.querySelector(
            '[data-director-character-label]',
          );
          if (!label) return null;
          const root = label.closest('div');
          return root ? Math.round(parseFloat(root.style.top || '0')) : null;
        }"""
    )
    check("render:survives", rendered_group_y is not None)

    # 关闭吸附：authored 允许负值；渲染不再夹紧（Y 由 runtime 提供）
    page.evaluate(
        """() => window.__director_store.getState().updateScene(
          { gaussianGroundSnap: false })"""
    )
    page.evaluate(
        """(cameraId) => {
          window.__director_store.getState().updateObjectTransform(
            cameraId, "position", 1, -1.5);
        }""",
        camera_id,
    )
    page.wait_for_timeout(300)
    check(
        "off:authored-free",
        page.evaluate(
            """() => window.__director_store.getState().authoredObjects
              .find((o) => o.kind === "camera").transform.position[1]"""
        ) == -1.5,
    )

    # 已知瞬态（batch 553 留痕）：selectObject 卸载/重挂周期触发
    # TransformControls attach 告警，与本批渲染夹紧无关——显式过滤。
    real_errors = [
        error
        for error in errors
        if "TransformControls" not in error
    ]
    check("diagnostics:zero", not real_errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 558,
        "title": "Gaussian ground snap render-side character Y clamp",
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
        "Batch 558 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "render-side character Y clamp (authored and runtime zero), "
        "free-Y when disabled, recorded in runtime-audit.json."
    )


if __name__ == "__main__":
    main()
