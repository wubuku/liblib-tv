#!/usr/bin/env python3
"""Verify Batch 564: camera follow-target ↔ preset-motion linkage.

Contract: source-site sampling (screenshot 47/50, 摄像机 panel 跟随目标
field + timeline 预设运镜 trigger) — while a camera follows a target,
preset camera moves are unavailable (跟随目标时不可使用预设运镜); the
preset trigger is disabled and re-enables when the follow target is
cleared. Driven end-to-end through the real store actions
(updateCamera followTargetId set/clear).
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
    / "liblib-canvas-batch564-2026-09-27"
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
        assert ok, f"batch564 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/?batch70=1", wait_until="networkidle")
    page.wait_for_function(
        """() => Boolean(window.__libtv_store && window.__libtv_ui_store && window.__director_store)"""
    )

    page.evaluate(
        """() => {
          const store = window.__libtv_store.getState();
          store.addNode("script-execution", { title: "Batch 564" });
          const node = store.getActiveCanvas().nodes.at(-1);
          window.__libtv_ui_store.getState().openDirectorDesk(node.id, store.activeCanvasId);
        }"""
    )
    page.locator("[data-director-workspace]").wait_for(state="visible")
    page.wait_for_timeout(600)

    character_id = page.evaluate(
        """() => window.__director_store.getState().objects
            .find((o) => o.kind === "character")?.id"""
    )
    camera_id = page.evaluate(
        """() => window.__director_store.getState().objects
            .find((o) => o.kind === "camera")?.id"""
    )

    # 选中摄像机轨道（预设运镜作用对象）
    page.evaluate(
        """(cameraId) => {
          const s = window.__director_store.getState();
          const track = s.timeline.tracks.find(
            (t) => t.kind === "camera" && t.objectId === cameraId,
          );
          if (track) s.selectTimelineTrack(track.id);
        }""",
        camera_id,
    )
    page.wait_for_timeout(250)
    trigger = page.locator("[data-director-camera-preset-trigger]")
    check("preset:enabled-initial", trigger.is_enabled())

    # 设置跟随目标（真实 updateCamera 动作）
    page.evaluate(
        """([cameraId, characterId]) => {
          window.__director_store.getState().updateCamera(cameraId, {
            followTargetId: characterId,
          });
        }""",
        [camera_id, character_id],
    )
    page.wait_for_timeout(300)
    check(
        "follow:set",
        page.evaluate(
            """([cameraId]) => Boolean(
              window.__director_store.getState().objects
                .find((o) => o.id === cameraId).camera.followTargetId,
            )""",
            [camera_id, character_id],
        ),
    )
    check(
        "preset:disabled-while-following",
        trigger.is_disabled(),
    )
    check(
        "error:span-visible",
        page.locator("[data-director-camera-preset-error]").is_visible()
        and "跟随目标时不可使用预设运镜"
        in page.locator("[data-director-camera-preset-error]").inner_text(),
    )

    # 清除跟随目标 → 预设运镜恢复可用
    page.evaluate(
        """(cameraId) => {
          window.__director_store.getState().updateCamera(cameraId, {
            followTargetId: null,
          });
        }""",
        camera_id,
    )
    page.wait_for_timeout(300)
    check("preset:re-enabled", trigger.is_enabled())
    check(
        "error:span-gone",
        page.locator("[data-director-camera-preset-error]").count() == 0,
    )

    # 已知瞬态（batch 553/558 留痕）：TransformControls attach 告警
    real_errors = [
        error for error in errors if "TransformControls" not in error
    ]
    check("diagnostics:zero", not real_errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 564,
        "title": "Camera follow-target ↔ preset-motion linkage",
        "evidence": (
            "docs/research/liblib-source-exploration-2026-09-25/NOTES.md "
            "§12 + screenshot 47 (跟随目标 field)"
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
        "Batch 564 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "follow-target set disables the preset trigger with the "
        "跟随目标时不可使用预设运镜 span, clearing re-enables, recorded in "
        "runtime-audit.json."
    )


if __name__ == "__main__":
    main()
