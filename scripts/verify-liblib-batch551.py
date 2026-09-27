#!/usr/bin/env python3
"""Verify Batch 551: gaussian ground snap clamps object Y to the ground.

Contract: source-site sampling (screenshot 45, 3D 场景 panel) — 高斯地面
吸附 toggle (default on) snaps content to the ground plane. Source semantics
target gaussian-splat model bases; the clone's local equivalent (documented
in batch 548/550 notes) clamps object position Y to >= 0 through
updateObjectTransform while scene.gaussianGroundSnap is on. Turning the
toggle off restores free Y movement.
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
    / "liblib-canvas-batch551-2026-09-27"
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
        assert ok, f"batch551 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/?batch70=1", wait_until="networkidle")
    page.wait_for_function(
        """() => Boolean(window.__libtv_store && window.__libtv_ui_store && window.__director_store)"""
    )

    page.evaluate(
        """() => {
          const store = window.__libtv_store.getState();
          store.addNode("script-execution", { title: "Batch 551" });
          const node = store.getActiveCanvas().nodes.at(-1);
          window.__libtv_ui_store.getState().openDirectorDesk(node.id, store.activeCanvasId);
        }"""
    )
    page.locator("[data-director-workspace]").wait_for(state="visible")
    page.wait_for_timeout(400)
    # 等待会话异步恢复完成（过早更新会被 restore 覆盖）
    page.wait_for_timeout(600)

    character_id = page.evaluate(
        """() => window.__director_store.getState().authoredObjects
            .find((object) => object.kind === "character").id"""
    )

    # 默认开：Y 负值被夹到地面（y=0）
    check(
        "default:on",
        page.evaluate(
            "window.__director_store.getState().scene.gaussianGroundSnap"
        ) is True,
    )
    _result = page.evaluate(
        """(cameraId) => {
          const s = window.__director_store.getState();
          const r = s.updateObjectTransform(
            cameraId, "position", 1, -5);
          return { disp: r.disposition, reason: r.reason,
                   snap: s.scene.gaussianGroundSnap,
                   kind: s.authoredObjects.find((o) => o.id === cameraId)?.kind,
                   y: s.objects.find((o) => o.id === cameraId)?.transform.position[1] };
        }""",
        character_id,
    )
    page.wait_for_timeout(300)
    y_after_negative = page.evaluate(
        """(cameraId) => window.__director_store.getState().authoredObjects
            .find((object) => object.id === cameraId).transform.position[1]""",
    character_id,
    )
    check("clamp:negative-flattened", y_after_negative == 0)

    # 正值不受影响
    page.evaluate(
        """(cameraId) => {
          window.__director_store.getState().updateObjectTransform(
            cameraId, "position", 1, 2.5);
        }""",
        character_id,
    )
    page.wait_for_timeout(300)
    check(
        "clamp:positive-kept",
        page.evaluate(
            """(cameraId) => window.__director_store.getState().authoredObjects
              .find((object) => object.id === cameraId).transform.position[1]""",
        character_id,
        ) == 2.5,
    )

    # 关闭后自由移动
    page.evaluate(
        """() => window.__director_store.getState().updateScene(
          { gaussianGroundSnap: false })"""
    )
    page.evaluate(
        """(cameraId) => {
          window.__director_store.getState().updateObjectTransform(
            cameraId, "position", 1, -1.5);
        }""",
        character_id,
    )
    page.wait_for_timeout(300)
    check(
        "off:free-y",
        page.evaluate(
            """(cameraId) => window.__director_store.getState().authoredObjects
              .find((object) => object.id === cameraId).transform.position[1]""",
        character_id,
        ) == -1.5,
    )

    # 重新开启
    page.evaluate(
        """() => window.__director_store.getState().updateScene(
          { gaussianGroundSnap: true })"""
    )
    check(
        "toggle:restored",
        page.evaluate(
            "window.__director_store.getState().scene.gaussianGroundSnap"
        ) is True,
    )

    check("diagnostics:zero", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 551,
        "title": "Gaussian ground snap clamps object Y",
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
        "Batch 551 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "gaussian ground snap clamps negative Y to the ground plane, keeps "
        "positive Y, and frees Y when disabled, recorded in "
        "runtime-audit.json."
    )


if __name__ == "__main__":
    main()
