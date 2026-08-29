#!/usr/bin/env python3

"""Verify Batch 89 Director scene settings and add-camera workflow."""

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
    / "liblib-canvas-batch89-2026-08-29"
    / "runtime-audit.json"
)


def attach_errors(page: Page) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    phase = ["startup"]
    page.on(
        "console",
        lambda message: errors.append(
            f"{phase[0]}:console:{message.type}:{message.text}"
        )
        if message.type == "error"
        else None,
    )
    page.on(
        "pageerror",
        lambda error: errors.append(
            f"{phase[0]}:pageerror:{error}\n{error.stack or 'stack unavailable'}"
        ),
    )
    page.on(
        "requestfailed",
        lambda request: errors.append(
            f"{phase[0]}:requestfailed:{request.method}:{request.url}:"
            f"{request.failure}"
        ),
    )
    return errors, phase


def wait_for_app(page: Page) -> None:
    page.wait_for_function(
        "() => Boolean(window.__libtv_store && window.__director_store)"
    )
    page.wait_for_selector("[data-libtv-react-flow-host]")


def clear_persistence(page: Page) -> None:
    page.evaluate(
        """() => {
          for (const key of Object.keys(localStorage)) {
            if (key.startsWith("liblib-tv-director-project-v1:")) {
              localStorage.removeItem(key);
            }
          }
        }"""
    )


def open_director(page: Page) -> dict[str, str]:
    fixture = page.evaluate(
        """() => {
          const canvasState = window.__libtv_store.getState();
          const canvas = canvasState.canvases.find((item) =>
            item.nodes.some((node) => node.type === "script-execution")
          );
          if (!canvas) throw new Error("Director canvas fixture is missing");
          canvasState.setActiveCanvas(canvas.id);
          const source = canvas.nodes.find(
            (node) => node.type === "script-execution"
          );
          if (!source) throw new Error("Director source fixture is missing");
          return { canvasId: canvas.id, sourceNodeId: source.id };
        }"""
    )
    page.evaluate(
        """(owner) => {
          window.__libtv_ui_store.getState().openDirectorDesk(
            owner.sourceNodeId,
            owner.canvasId
          );
        }""",
        fixture,
    )
    page.locator("[data-director-workspace]").wait_for(state="visible")
    page.wait_for_function(
        """(owner) => JSON.stringify(
          window.__director_store.getState().projectOwner
        ) === JSON.stringify({
          route: "libtv",
          canvasId: owner.canvasId,
          sourceNodeId: owner.sourceNodeId
        })""",
        arg=fixture,
    )
    page.locator('canvas[data-director-webgl-canvas="true"]').wait_for(
        state="visible"
    )
    page.wait_for_timeout(300)
    return fixture


def director_snapshot(page: Page) -> dict[str, Any]:
    return page.evaluate(
        """() => {
          const state = window.__director_store.getState();
          const selectedTrack = state.timeline.tracks.find(
            (track) => track.id === state.timeline.selectedTrackId
          );
          const selected = state.objects.find(
            (object) => object.id === state.selectedObjectId
          );
          return {
            projectId: state.projectId,
            selectedObjectId: state.selectedObjectId,
            selectedObjectIds: state.selectedObjectIds,
            selectedObjectKind: selected?.kind ?? null,
            activeCameraId: state.activeCameraId,
            cameraCount: state.objects.filter(
              (object) => object.kind === "camera"
            ).length,
            selectedTrackId: state.timeline.selectedTrackId,
            selectedTrackKind: selectedTrack?.kind ?? null,
            selectedTrackObjectId: selectedTrack?.objectId ?? null,
            selectedTrackKeyframeCount: selectedTrack?.keyframes.length ?? 0,
            timelineCurrentTime: state.timeline.currentTime,
            sceneName: state.scene.name,
            historyPast: state.history.past.length,
            historyFuture: state.history.future.length,
            exported: state.exportDirectorProject(),
          };
        }"""
    )


def assert_no_horizontal_overflow(page: Page, selector: str) -> None:
    overflow = page.locator(selector).evaluate(
        """(element) => ({
          scrollWidth: element.scrollWidth,
          clientWidth: element.clientWidth
        })"""
    )
    assert overflow["scrollWidth"] <= overflow["clientWidth"] + 1, overflow


def run_browser_verifier(page: Page) -> dict[str, Any]:
    errors, phase = attach_errors(page)
    page.goto(f"{BASE_URL}/?batch89=1", wait_until="networkidle")
    wait_for_app(page)
    clear_persistence(page)
    fixture = open_director(page)

    phase[0] = "baseline"
    baseline = director_snapshot(page)
    assert baseline["cameraCount"] == 1
    assert page.locator("[data-director-scene-settings]").count() == 0
    assert page.locator("[data-director-add-camera]").count() == 1

    phase[0] = "scene-settings"
    page.locator("[data-director-selection-action='clear']").click()
    page.locator("[data-director-scene-settings]").wait_for(state="visible")
    assert page.locator("[data-director-scene-name]").input_value() == baseline[
        "sceneName"
    ]
    page.locator("[data-director-scene-name]").fill("Batch 89 场景")
    page.locator("[data-director-scene-show-ground]").uncheck()
    page.locator("[data-director-scene-show-grid]").uncheck()
    page.locator("[data-director-scene-ground-color]").fill("#4a4f56")
    page.wait_for_function(
        "() => window.__director_store.getState().scene.name === 'Batch 89 场景'"
    )
    scene_state = page.evaluate(
        """() => window.__director_store.getState().scene"""
    )
    assert scene_state["showGround"] is False
    assert scene_state["showGrid"] is False
    assert scene_state["groundColor"] == "#4a4f56"

    phase[0] = "add-camera"
    before_add = director_snapshot(page)
    page.locator("[data-director-tree] [data-director-add-camera]").click()
    page.wait_for_function(
        """(before) =>
          window.__director_store.getState().objects.filter(
            (object) => object.kind === "camera"
          ).length === before.cameraCount + 1""",
        arg=before_add,
    )
    after_add = director_snapshot(page)
    assert after_add["cameraCount"] == before_add["cameraCount"] + 1
    assert after_add["activeCameraId"] == after_add["selectedObjectId"]
    assert after_add["selectedObjectIds"] == [after_add["activeCameraId"]]
    assert after_add["selectedObjectKind"] == "camera"
    assert after_add["selectedTrackKind"] == "camera"
    assert after_add["selectedTrackObjectId"] == after_add["activeCameraId"]
    assert after_add["selectedTrackKeyframeCount"] >= 1
    assert after_add["historyPast"] == before_add["historyPast"] + 1
    assert after_add["historyFuture"] == 0

    camera_geometry = page.evaluate(
        """() => {
          const state = window.__director_store.getState();
          const active = state.objects.find(
            (object) => object.id === state.activeCameraId
          );
          const previous = state.objects.find(
            (object) => object.kind === "camera" && object.id !== state.activeCameraId
          );
          return {
            activePosition: active?.transform.position ?? null,
            previousPosition: previous?.transform.position ?? null,
            activeFollow: active?.camera?.followTargetId ?? null,
            activeLookAtObject: active?.camera?.lookAtObjectId ?? null,
          };
        }"""
    )
    assert camera_geometry["activePosition"] != camera_geometry["previousPosition"]
    assert camera_geometry["activeFollow"] is None
    assert camera_geometry["activeLookAtObject"] is None

    phase[0] = "undo-redo"
    page.evaluate("() => window.__director_store.getState().undoDirector()")
    page.wait_for_function(
        "(before) => window.__director_store.getState().objects.filter((object) => object.kind === 'camera').length === before.cameraCount",
        arg=before_add,
    )
    undone = director_snapshot(page)
    assert undone["cameraCount"] == before_add["cameraCount"]
    assert undone["activeCameraId"] == before_add["activeCameraId"]
    page.evaluate("() => window.__director_store.getState().redoDirector()")
    page.wait_for_function(
        "(after) => window.__director_store.getState().activeCameraId === after.activeCameraId",
        arg=after_add,
    )
    redone = director_snapshot(page)
    assert redone["cameraCount"] == after_add["cameraCount"]
    assert redone["activeCameraId"] == after_add["activeCameraId"]

    phase[0] = "portable-export"
    exported = json.loads(redone["exported"])
    assert exported["activeCameraId"] == redone["activeCameraId"]
    assert any(
        obj["id"] == redone["activeCameraId"] and obj["kind"] == "camera"
        for obj in exported["objects"]
    )
    assert any(
        track["objectId"] == redone["activeCameraId"]
        and track["kind"] == "camera"
        for track in exported["timeline"]["tracks"]
    )
    exported_json = json.dumps(exported)
    assert "selectedObjectId" not in exported_json
    assert "viewportPanelsCollapsed" not in exported_json
    assert "data:image" not in exported_json

    phase[0] = "mobile"
    page.set_viewport_size({"width": 390, "height": 844})
    page.wait_for_timeout(200)
    page.locator("button[aria-label='打开场景对象']").click()
    page.locator("[data-director-add-camera]").first.wait_for(state="visible")
    assert_no_horizontal_overflow(page, "[data-director-tree]")
    page.locator("button[aria-label='关闭移动端面板']").click()
    page.locator("button[aria-label='打开属性面板']").click()
    page.locator("[data-director-scene-settings]").count()
    assert_no_horizontal_overflow(page, "[data-director-inspector]")

    return {
        "fixture": fixture,
        "baseline": baseline,
        "afterAdd": after_add,
        "undo": undone,
        "redo": redone,
        "portableExport": True,
        "mobileNoHorizontalOverflow": True,
        "diagnostics": {
            "consoleErrors": len(
                [entry for entry in errors if ":console:error:" in entry]
            ),
            "pageErrors": len(
                [entry for entry in errors if ":pageerror:" in entry]
            ),
            "requestFailures": len(
                [entry for entry in errors if ":requestfailed:" in entry]
            ),
            "details": errors,
        },
    }


def main() -> None:
    result: dict[str, Any]
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        context = browser.new_context(viewport={"width": 1440, "height": 1000})
        page = context.new_page()
        result = run_browser_verifier(page)
        browser.close()

    assert result["diagnostics"]["consoleErrors"] == 0, result["diagnostics"]
    assert result["diagnostics"]["pageErrors"] == 0, result["diagnostics"]
    assert result["diagnostics"]["requestFailures"] == 0, result["diagnostics"]

    AUDIT_PATH.write_text(
        json.dumps(
            {
                "batch": 89,
                "status": "SCRIPT_RECORDED_PASS",
                "baseUrl": BASE_URL,
                "sourceExact": False,
                **result,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print("Batch 89 Director scene settings and add-camera verification passed.")


if __name__ == "__main__":
    main()
