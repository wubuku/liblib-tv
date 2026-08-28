#!/usr/bin/env python3

"""Verify the Batch 71 Director pointer lifecycle and gesture adapter."""

from __future__ import annotations

import json
import math
import os
import subprocess
from pathlib import Path

from playwright.sync_api import Locator, Page, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
BASE_URL = os.environ.get("LIBLIB_BASE_URL", "http://localhost:4317")
AUDIT_PATH = (
    ROOT
    / "docs"
    / "research"
    / "liblib-canvas-batch71-2026-08-27"
    / "runtime-audit.json"
)


def run_pure_verifier() -> dict:
    completed = subprocess.run(
        [
            "node",
            "--disable-warning=MODULE_TYPELESS_PACKAGE_JSON",
            "--experimental-strip-types",
            "scripts/verify-liblib-batch71.mjs",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    result = json.loads(completed.stdout)
    assert result["status"] == "PASS"
    return result


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


def graph_state(page: Page) -> dict:
    return page.evaluate(
        """() => {
          const state = window.__libtv_store.getState();
          const canvas = state.getActiveCanvas();
          const history = state.historyByCanvas[state.activeCanvasId] || {
            past: [],
            future: [],
          };
          return {
            canvasId: state.activeCanvasId,
            nodeIds: (canvas?.nodes || []).map((node) => node.id),
            edgeIds: (canvas?.edges || []).map((edge) => edge.id),
            pastLength: history.past.length,
            futureLength: history.future.length,
          };
        }"""
    )


def director_state(page: Page) -> dict:
    return page.evaluate(
        """() => {
          const state = window.__director_store.getState();
          return {
            projectId: state.projectId,
            selectedObjectId: state.selectedObjectId,
            history: {
              past: state.history.past.length,
              future: state.history.future.length,
              active: Boolean(state.history.activeGesture),
            },
            lastCommand: state.lastCommandResult
              ? {
                  commandKind: state.lastCommandResult.commandKind,
                  disposition: state.lastCommandResult.disposition,
                  reason: state.lastCommandResult.reason,
                  historyEntries: state.lastCommandResult.historyEntries,
                }
              : null,
            character: (() => {
              const object = state.authoredObjects.find(
                (item) => item.id === "director-character-lead",
              );
              return object
                ? {
                    position: object.transform.position,
                    pose: object.characterRig?.controls || null,
                  }
                : null;
            })(),
            camera: (() => {
              const object = state.authoredObjects.find(
                (item) => item.id === "director-camera-main",
              );
              return object
                ? {
                    fov: object.camera?.fov ?? null,
                    target: object.camera?.target ?? null,
                  }
                : null;
            })(),
            timeline: {
              motionPaths: state.timeline.motionPaths.map((path) => ({
                id: path.id,
                preset: path.preset,
                anchors: path.anchors.length,
                points: path.points.length,
                name: path.name,
              })),
              draft: state.timeline.motionPathDraft
                ? {
                    tool: state.timeline.motionPathDraft.tool,
                    anchors: state.timeline.motionPathDraft.anchors.length,
                  }
                : null,
              selectedMotionPathId: state.timeline.selectedMotionPathId,
              selectedMotionPathAnchorId:
                state.timeline.selectedMotionPathAnchorId,
            },
          };
        }"""
    )


def open_director(page: Page, scenario: str) -> tuple[dict, dict]:
    page.goto(f"{BASE_URL}/?batch71={scenario}", wait_until="networkidle")
    page.wait_for_function(
        """() => Boolean(
          window.__libtv_store &&
          window.__libtv_ui_store &&
          window.__director_store
        )"""
    )
    fixture = page.evaluate(
        """() => {
          const store = window.__libtv_store.getState();
          const canvasId = store.activeCanvasId;
          const before = new Set(
            store.getActiveCanvas()?.nodes.map((node) => node.id) || [],
          );
          store.addNode("script-execution", { title: "Batch 71 fixture" });
          const nodes = store.getActiveCanvas()?.nodes || [];
          const nodeId = nodes.find((node) => !before.has(node.id))?.id;
          if (!nodeId) throw new Error("Batch 71 fixture creation failed");
          window.__libtv_ui_store.getState().openDirectorDesk(nodeId, canvasId);
          return { canvasId, nodeId };
        }"""
    )
    page.wait_for_function(
        """({ canvasId, nodeId }) => {
          const state = window.__director_store.getState();
          return (
            state.projectOwner?.canvasId === canvasId &&
            state.projectOwner?.sourceNodeId === nodeId &&
            typeof state.projectId === "string"
          );
        }""",
        arg=fixture,
    )
    page.locator("[data-director-workspace]").wait_for(state="visible")
    page.locator('canvas[data-director-webgl-canvas="true"]').wait_for(
        state="visible"
    )
    page.wait_for_timeout(180)
    return fixture, graph_state(page)


def assert_graph_unchanged(page: Page, baseline: dict) -> None:
    assert graph_state(page) == baseline


def run_number_commit(page: Page) -> dict:
    _, graph_baseline = open_director(page, "number-commit")
    before = director_state(page)
    field = page.locator(
        '[data-director-transform-field="position"]'
        '[data-director-transform-axis="x"]'
    )
    baseline = float(field.input_value())
    field.fill(str(baseline + 0.4))
    field.fill(str(baseline + 1.0))
    page.locator('[data-director-character-tab="pose"]').click()
    page.wait_for_timeout(80)
    after = director_state(page)
    assert after["history"]["past"] == before["history"]["past"] + 1
    assert after["history"]["active"] is False
    assert after["character"]["position"][0] == baseline + 1.0
    assert after["lastCommand"] == {
        "commandKind": "GESTURE_COMMIT",
        "disposition": "COMMITTED",
        "reason": None,
        "historyEntries": 1,
    }
    assert_graph_unchanged(page, graph_baseline)
    return {"historyDelta": 1, "field": "object.position.x"}


def run_number_cancel(page: Page) -> dict:
    _, graph_baseline = open_director(page, "number-cancel")
    before = director_state(page)
    field = page.locator(
        '[data-director-transform-field="position"]'
        '[data-director-transform-axis="x"]'
    )
    baseline = float(field.input_value())
    field.fill(str(baseline + 1.25))
    field.press("Escape")
    page.locator('[data-director-character-tab="pose"]').click()
    page.wait_for_timeout(80)
    after = director_state(page)
    assert after["history"] == before["history"]
    assert after["history"]["active"] is False
    assert after["character"]["position"][0] == baseline
    assert_graph_unchanged(page, graph_baseline)
    return {"historyDelta": 0, "cancel": "Escape"}


def run_pose_commit(page: Page) -> dict:
    _, graph_baseline = open_director(page, "pose-commit")
    before = director_state(page)
    page.locator('[data-director-character-tab="pose"]').click()
    slider = page.locator("[data-director-pose-control]").first
    baseline = float(slider.input_value())
    slider.focus()
    slider.press("ArrowRight")
    slider.press("ArrowRight")
    page.locator('[data-director-character-tab="properties"]').click()
    page.wait_for_timeout(80)
    after = director_state(page)
    assert after["history"]["past"] == before["history"]["past"] + 1
    assert after["history"]["active"] is False
    assert after["character"]["pose"] != before["character"]["pose"]
    assert_graph_unchanged(page, graph_baseline)
    return {"historyDelta": 1, "field": "pose-control"}


def run_fov_commit(page: Page) -> dict:
    _, graph_baseline = open_director(page, "fov-commit")
    page.locator('[data-director-object-id="director-camera-main"]').click()
    fov = page.locator("[data-director-camera-fov]")
    before = director_state(page)
    baseline = float(fov.input_value())
    fov.focus()
    fov.press("ArrowRight")
    fov.press("ArrowRight")
    page.locator('[data-director-object-id="director-character-lead"]').click()
    page.wait_for_timeout(80)
    after = director_state(page)
    assert after["history"]["past"] == before["history"]["past"] + 1
    assert after["history"]["active"] is False
    assert after["camera"]["fov"] == baseline + 2
    assert_graph_unchanged(page, graph_baseline)
    return {"historyDelta": 1, "field": "camera.fov"}


def prepare_path(page: Page, scenario: str) -> tuple[dict, dict, dict]:
    _, graph_baseline = open_director(page, scenario)
    page.evaluate(
        """() => window.__director_store.getState().createMotionPath("line")"""
    )
    page.wait_for_timeout(80)
    path_fixture = page.evaluate(
        """() => {
          const state = window.__director_store.getState();
          const path = state.timeline.motionPaths[0];
          if (!path) throw new Error("Batch 71 path fixture missing");
          state.selectMotionPathAnchor(path.id, path.anchors[0].id);
          return { pathId: path.id, anchorId: path.anchors[0].id };
        }"""
    )
    page.locator("[data-director-motion-path-inspector]").wait_for(state="visible")
    page.wait_for_timeout(80)
    return graph_baseline, path_fixture, director_state(page)


def run_path_fields_commit(page: Page) -> dict:
    graph_baseline, _, before = prepare_path(page, "path-fields")
    position = page.locator('[data-director-path-anchor-position="x"]')
    position_baseline = float(position.input_value())
    position.fill(str(position_baseline + 0.25))
    position.fill(str(position_baseline + 0.75))
    page.locator("[data-director-path-name]").click()
    page.wait_for_timeout(80)
    after_position = director_state(page)
    assert after_position["history"]["past"] == before["history"]["past"] + 1
    assert after_position["history"]["active"] is False

    transform = page.locator(
        '[data-director-path-transform-field="position"] input'
    ).first
    transform_baseline = float(transform.input_value())
    transform.fill(str(transform_baseline + 0.5))
    page.locator("[data-director-path-name]").click()
    page.wait_for_timeout(80)
    after_transform = director_state(page)
    assert after_transform["history"]["past"] == before["history"]["past"] + 2
    assert after_transform["history"]["active"] is False
    assert_graph_unchanged(page, graph_baseline)
    return {"historyDelta": 2, "fields": ["path-anchor-position.x", "path-transform.position.x"]}


def start_draw_tool(page: Page, tool: str) -> None:
    page.locator("[data-director-create-motion-path]").click()
    page.locator(f'[data-director-motion-path-draw-tool="{tool}"]').click()
    drawing = page.locator("[data-director-path-drawing]")
    drawing.wait_for(state="visible")
    assert drawing.get_attribute("data-director-path-drawing-tool") == tool
    assert page.evaluate(
        "() => Boolean(window.__director_store.getState().history.activeGesture)"
    )


def canvas_box(page: Page) -> dict:
    result = page.locator('canvas[data-director-webgl-canvas="true"]').bounding_box()
    assert result is not None
    return result


def draw_pencil(page: Page) -> None:
    bounds = canvas_box(page)
    start_x = bounds["x"] + bounds["width"] * 0.37
    start_y = bounds["y"] + bounds["height"] * 0.51
    page.mouse.move(start_x, start_y)
    page.mouse.down()
    for index in range(1, 9):
        page.mouse.move(
            start_x + index * bounds["width"] * 0.026,
            start_y + math.sin(index * 0.82) * bounds["height"] * 0.055,
            steps=2,
        )
    page.mouse.up()
    page.wait_for_timeout(120)


def draw_pen(page: Page) -> None:
    bounds = canvas_box(page)
    gestures = [
        (0.38, 0.51, 0.055, -0.045),
        (0.50, 0.43, 0, 0),
        (0.63, 0.52, -0.05, 0.065),
    ]
    for relative_x, relative_y, delta_x, delta_y in gestures:
        x = bounds["x"] + bounds["width"] * relative_x
        y = bounds["y"] + bounds["height"] * relative_y
        page.mouse.move(x, y)
        page.mouse.down()
        if delta_x or delta_y:
            page.mouse.move(
                x + bounds["width"] * delta_x,
                y + bounds["height"] * delta_y,
                steps=5,
            )
        page.mouse.up()


def run_pencil_commit(page: Page) -> dict:
    _, graph_baseline = open_director(page, "pencil-commit")
    before = director_state(page)
    start_draw_tool(page, "pencil")
    draw_pencil(page)
    after = director_state(page)
    assert after["history"]["past"] == before["history"]["past"] + 1
    assert after["history"]["active"] is False
    assert after["timeline"]["draft"] is None
    assert after["timeline"]["motionPaths"][0]["preset"] == "pencil"
    assert after["timeline"]["motionPaths"][0]["anchors"] >= 8
    assert_graph_unchanged(page, graph_baseline)
    return {"historyDelta": 1, "tool": "pencil", "commit": "pointerup"}


def run_pen_commit(page: Page) -> dict:
    _, graph_baseline = open_director(page, "pen-commit")
    before = director_state(page)
    start_draw_tool(page, "pen")
    draw_pen(page)
    page.locator("[data-director-path-drawing-complete]").click()
    page.wait_for_timeout(120)
    after = director_state(page)
    assert after["history"]["past"] == before["history"]["past"] + 1
    assert after["history"]["active"] is False
    assert after["timeline"]["draft"] is None
    assert after["timeline"]["motionPaths"][0]["preset"] == "pen"
    assert after["timeline"]["motionPaths"][0]["anchors"] == 3
    assert_graph_unchanged(page, graph_baseline)
    return {"historyDelta": 1, "tool": "pen", "commit": "completion-button"}


def run_pen_escape(page: Page) -> dict:
    _, graph_baseline = open_director(page, "pen-escape")
    page.evaluate(
        """() => window.__director_store.getState().createMotionPath("line")"""
    )
    page.wait_for_timeout(80)
    before = director_state(page)
    previous_paths = before["timeline"]["motionPaths"]
    start_draw_tool(page, "pen")
    bounds = canvas_box(page)
    page.mouse.click(
        bounds["x"] + bounds["width"] * 0.44,
        bounds["y"] + bounds["height"] * 0.50,
    )
    page.keyboard.press("Escape")
    page.wait_for_timeout(100)
    after = director_state(page)
    assert after["history"] == before["history"]
    assert after["history"]["active"] is False
    assert after["timeline"]["draft"] is None
    assert after["timeline"]["motionPaths"] == previous_paths
    assert_graph_unchanged(page, graph_baseline)
    return {"historyDelta": 0, "cancel": "Escape", "pathPreserved": True}


def run_pointercancel(page: Page) -> dict:
    _, graph_baseline = open_director(page, "pointercancel")
    before = director_state(page)
    start_draw_tool(page, "pencil")
    bounds = canvas_box(page)
    x = bounds["x"] + bounds["width"] * 0.40
    y = bounds["y"] + bounds["height"] * 0.50
    page.mouse.move(x, y)
    page.mouse.down()
    page.wait_for_timeout(40)
    page.evaluate(
        """() => window.dispatchEvent(
          new PointerEvent("pointercancel", { bubbles: true, cancelable: true })
        )"""
    )
    page.wait_for_timeout(100)
    page.mouse.up()
    after = director_state(page)
    assert after["history"] == before["history"]
    assert after["history"]["active"] is False
    assert after["timeline"]["draft"] is None
    assert_graph_unchanged(page, graph_baseline)
    return {"historyDelta": 0, "cancel": "window-pointercancel"}


def run_browser_verifier() -> dict:
    scenarios = [
        ("numberCommit", run_number_commit),
        ("numberCancel", run_number_cancel),
        ("poseCommit", run_pose_commit),
        ("fovCommit", run_fov_commit),
        ("pathFieldsCommit", run_path_fields_commit),
        ("pencilCommit", run_pencil_commit),
        ("penCommit", run_pen_commit),
        ("penEscape", run_pen_escape),
        ("pointercancel", run_pointercancel),
    ]
    results: dict[str, dict] = {}
    diagnostics: list[str] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        for name, scenario in scenarios:
            page = browser.new_page(
                viewport={"width": 1440, "height": 900},
                device_scale_factor=1,
            )
            errors = attach_errors(page)
            results[name] = scenario(page)
            assert errors == [], json.dumps(errors, ensure_ascii=False, indent=2)
            diagnostics.extend(errors)
            page.close()
        browser.close()
    return {
        **results,
        "diagnostics": {
            "errors": diagnostics,
            "status": "PASS",
        },
    }


def main() -> None:
    pure = run_pure_verifier()
    browser = run_browser_verifier()
    audit = {
        "status": "PASS",
        "batch": 71,
        "baseUrl": BASE_URL,
        "pure": pure,
        "browser": browser,
        "screenshots": [],
        "errors": [],
    }
    AUDIT_PATH.write_text(
        json.dumps(audit, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(audit, ensure_ascii=False))


if __name__ == "__main__":
    main()
