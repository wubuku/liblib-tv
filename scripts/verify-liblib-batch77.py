#!/usr/bin/env python3

"""Verify Batch 77 canvas navigation parity and Director gizmo pointer binding."""

from __future__ import annotations

import json
import math
import os
import re
from pathlib import Path
from typing import Any

from playwright.sync_api import Locator, Page, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
BASE_URL = os.environ.get("LIBLIB_BASE_URL", "http://localhost:3000")
AUDIT_PATH = (
    ROOT
    / "docs"
    / "research"
    / "liblib-canvas-batch77-2026-08-28"
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


def box(locator: Locator) -> dict[str, float]:
    result = locator.bounding_box()
    assert result is not None
    return {key: float(value) for key, value in result.items()}


def open_canvas(page: Page, scenario: str) -> Locator:
    page.goto(f"{BASE_URL}/?batch77={scenario}", wait_until="networkidle")
    page.wait_for_function(
        "() => Boolean(window.__libtv_store && window.__libtv_ui_store)"
    )
    host = page.locator("[data-libtv-react-flow-host]")
    host.wait_for(state="visible")
    page.wait_for_timeout(180)
    return host


def open_director(page: Page, scenario: str) -> Locator:
    page.goto(f"{BASE_URL}/?batch77={scenario}", wait_until="networkidle")
    page.wait_for_function(
        "() => Boolean(window.__libtv_store && window.__libtv_ui_store)"
    )
    page.locator("[data-open-director]").click()
    workspace = page.locator("[data-director-workspace]")
    workspace.wait_for(state="visible")
    page.locator('canvas[data-director-webgl-canvas="true"]').wait_for(
        state="visible"
    )
    page.wait_for_timeout(500)
    return workspace


def read_flow_viewport(page: Page) -> dict[str, float]:
    result = page.evaluate(
        """() => {
          const element = document.querySelector(".react-flow__viewport");
          if (!element) throw new Error("React Flow viewport missing");
          const transform = window.getComputedStyle(element).transform;
          const match = transform.match(/^matrix\\(([^)]+)\\)$/);
          if (match) {
            const values = match[1].split(",").map(Number);
            return { x: values[4], y: values[5], zoom: values[0] };
          }
          const state = window.__libtv_store.getState();
          return state.getActiveCanvas().viewport;
        }"""
    )
    assert isinstance(result, dict)
    return {
        "x": float(result["x"]),
        "y": float(result["y"]),
        "zoom": float(result["zoom"]),
    }


def graph_snapshot(page: Page) -> dict[str, Any]:
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


def find_blank_point(page: Page, host: Locator) -> dict[str, float]:
    host_box = box(host)
    candidates = [
        {
            "x": host_box["x"] + host_box["width"] * x_ratio,
            "y": host_box["y"] + host_box["height"] * y_ratio,
        }
        for x_ratio, y_ratio in (
            (0.88, 0.14),
            (0.92, 0.28),
            (0.82, 0.18),
            (0.72, 0.12),
            (0.84, 0.42),
        )
    ]
    point = page.evaluate(
        """(candidates) => candidates.find(({ x, y }) => {
          const element = document.elementFromPoint(x, y);
          return Boolean(element?.closest(".react-flow__pane"));
        }) || null""",
        candidates,
    )
    assert point is not None, "could not find a blank React Flow pane point"
    return {"x": float(point["x"]), "y": float(point["y"])}


def move_and_drag(
    page: Page,
    point: dict[str, float],
    *,
    dx: float,
    dy: float,
    button: str = "left",
) -> None:
    page.mouse.move(point["x"], point["y"])
    page.mouse.down(button=button)
    page.mouse.move(point["x"] + dx, point["y"] + dy, steps=8)
    page.mouse.up(button=button)
    page.wait_for_timeout(160)


def assert_no_overflow(page: Page) -> None:
    assert page.evaluate(
        "() => document.documentElement.scrollWidth <= document.documentElement.clientWidth"
    )
    assert page.evaluate(
        "() => document.body.scrollWidth <= document.body.clientWidth"
    )


def close_enough(left: float, right: float, tolerance: float = 2.0) -> bool:
    return abs(left - right) <= tolerance


def run_navigation_desktop(page: Page) -> dict[str, Any]:
    errors = attach_errors(page)
    host = open_canvas(page, "navigation-desktop")
    point = find_blank_point(page, host)
    baseline_graph = graph_snapshot(page)

    baseline = read_flow_viewport(page)
    page.mouse.move(point["x"], point["y"])
    page.mouse.wheel(0, 240)
    page.wait_for_timeout(180)
    vertical = read_flow_viewport(page)
    assert abs(vertical["y"] - baseline["y"]) >= 180
    assert close_enough(vertical["x"], baseline["x"])
    assert close_enough(vertical["zoom"], baseline["zoom"], 0.01)

    page.mouse.wheel(240, 0)
    page.wait_for_timeout(180)
    horizontal = read_flow_viewport(page)
    assert abs(horizontal["x"] - vertical["x"]) >= 180
    assert close_enough(horizontal["y"], vertical["y"])
    assert close_enough(horizontal["zoom"], vertical["zoom"], 0.01)

    before_modifier_zoom = read_flow_viewport(page)
    page.keyboard.down("Control")
    page.mouse.wheel(0, 120)
    page.keyboard.up("Control")
    page.wait_for_timeout(220)
    modifier_zoom = read_flow_viewport(page)
    assert abs(modifier_zoom["zoom"] - before_modifier_zoom["zoom"]) > 0.01

    page.keyboard.press("v")
    page.mouse.click(point["x"], point["y"])
    before_blank_drag = read_flow_viewport(page)
    move_and_drag(page, point, dx=90, dy=50)
    after_blank_drag = read_flow_viewport(page)
    assert close_enough(after_blank_drag["x"], before_blank_drag["x"])
    assert close_enough(after_blank_drag["y"], before_blank_drag["y"])
    assert close_enough(after_blank_drag["zoom"], before_blank_drag["zoom"], 0.01)
    assert page.locator(".react-flow__selection").count() == 0

    before_middle_drag = read_flow_viewport(page)
    move_and_drag(page, point, dx=90, dy=50, button="middle")
    after_middle_drag = read_flow_viewport(page)
    assert abs(after_middle_drag["x"] - before_middle_drag["x"]) >= 60
    assert abs(after_middle_drag["y"] - before_middle_drag["y"]) >= 30
    assert close_enough(after_middle_drag["zoom"], before_middle_drag["zoom"], 0.01)

    page.keyboard.press("h")
    assert host.get_attribute("data-canvas-tool") == "pan"
    before_h_drag = read_flow_viewport(page)
    move_and_drag(page, point, dx=90, dy=50)
    after_h_drag = read_flow_viewport(page)
    assert abs(after_h_drag["x"] - before_h_drag["x"]) >= 60
    assert abs(after_h_drag["y"] - before_h_drag["y"]) >= 30

    page.keyboard.press("v")
    assert host.get_attribute("data-canvas-tool") == "select"
    page.keyboard.down("Space")
    page.wait_for_timeout(60)
    assert host.get_attribute("data-temporary-pan") == "true"
    before_space_drag = read_flow_viewport(page)
    move_and_drag(page, point, dx=90, dy=50)
    page.keyboard.up("Space")
    page.wait_for_timeout(80)
    after_space_drag = read_flow_viewport(page)
    assert abs(after_space_drag["x"] - before_space_drag["x"]) >= 60
    assert abs(after_space_drag["y"] - before_space_drag["y"]) >= 30
    assert host.get_attribute("data-temporary-pan") == "false"
    assert host.get_attribute("data-canvas-tool") == "select"

    assert graph_snapshot(page) == baseline_graph
    assert errors == [], json.dumps(errors, ensure_ascii=False, indent=2)
    return {
        "plainWheelPan": True,
        "middleButtonPan": True,
        "modifierWheelZoom": True,
        "selectBlankDrag": "no-op",
        "persistentHand": True,
        "temporarySpaceHand": True,
        "graphUnchanged": True,
    }


def run_navigation_mobile(page: Page) -> dict[str, Any]:
    errors = attach_errors(page)
    host = open_canvas(page, "navigation-mobile")
    assert_no_overflow(page)
    point = find_blank_point(page, host)
    baseline = read_flow_viewport(page)
    page.mouse.move(point["x"], point["y"])
    page.mouse.wheel(0, 120)
    page.wait_for_timeout(180)
    after = read_flow_viewport(page)
    assert abs(after["y"] - baseline["y"]) >= 60
    assert_no_overflow(page)
    assert errors == [], json.dumps(errors, ensure_ascii=False, indent=2)
    return {
        "viewport": "390x844",
        "scrollPan": True,
        "noOverflow": True,
    }


def director_state(page: Page) -> dict[str, Any]:
    return page.evaluate(
        """() => {
          const state = window.__director_store.getState();
          const object = state.authoredObjects.find(
            (item) => item.id === "director-prop-mug"
          );
          const runtimeObject = state.objects.find(
            (item) => item.id === "director-prop-mug"
          );
          return {
            selectedObjectId: state.selectedObjectId,
            transformMode: state.transformMode,
            authoredPosition: object?.transform.position || null,
            runtimePosition: runtimeObject?.transform.position || null,
            historyPast: state.history.past.length,
            historyFuture: state.history.future.length,
            activeGesture: Boolean(state.history.activeGesture),
            lastCommand: state.lastCommandResult
              ? {
                  commandKind: state.lastCommandResult.commandKind,
                  disposition: state.lastCommandResult.disposition,
                  reason: state.lastCommandResult.reason,
                  historyEntries: state.lastCommandResult.historyEntries,
                }
              : null,
          };
        }"""
    )


def parse_vector(value: str | None) -> tuple[float, float, float]:
    assert value is not None
    parts = tuple(float(part) for part in value.split(","))
    assert len(parts) == 3
    return parts


def normalize(vector: tuple[float, float, float]) -> tuple[float, float, float]:
    length = math.sqrt(sum(value * value for value in vector))
    assert length > 0
    return tuple(value / length for value in vector)


def dot(
    left: tuple[float, float, float],
    right: tuple[float, float, float],
) -> float:
    return sum(left[index] * right[index] for index in range(3))


def cross(
    left: tuple[float, float, float],
    right: tuple[float, float, float],
) -> tuple[float, float, float]:
    return (
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    )


def project_world_point(
    point: tuple[float, float, float],
    camera_position: tuple[float, float, float],
    camera_target: tuple[float, float, float],
    viewport: dict[str, float],
    fov_degrees: float = 45.0,
) -> tuple[float, float]:
    forward = normalize(
        (
            camera_target[0] - camera_position[0],
            camera_target[1] - camera_position[1],
            camera_target[2] - camera_position[2],
        )
    )
    right = normalize(cross(forward, (0.0, 1.0, 0.0)))
    up = normalize(cross(right, forward))
    relative = (
        point[0] - camera_position[0],
        point[1] - camera_position[1],
        point[2] - camera_position[2],
    )
    depth = dot(relative, forward)
    assert depth > 0
    aspect = viewport["width"] / viewport["height"]
    tangent = math.tan(math.radians(fov_degrees) / 2)
    ndc_x = dot(relative, right) / (depth * tangent * aspect)
    ndc_y = dot(relative, up) / (depth * tangent)
    return (
        viewport["x"] + (ndc_x + 1) * viewport["width"] / 2,
        viewport["y"] + (1 - ndc_y) * viewport["height"] / 2,
    )


def gizmo_drag_points(page: Page) -> tuple[dict[str, float], dict[str, float]]:
    canvas = page.locator('canvas[data-director-webgl-canvas="true"]')
    canvas_box = box(canvas)
    camera_position = parse_vector(
        page.locator("[data-director-viewport-gizmo]").get_attribute(
            "data-director-viewport-gizmo-position"
        )
    )
    camera_target = parse_vector(
        page.locator("[data-director-viewport-gizmo]").get_attribute(
            "data-director-viewport-gizmo-target"
        )
    )
    state = director_state(page)
    position = tuple(float(value) for value in state["authoredPosition"])
    center = project_world_point(
        position,
        camera_position,
        camera_target,
        canvas_box,
    )
    axis_point = project_world_point(
        (position[0] + 0.45, position[1], position[2]),
        camera_position,
        camera_target,
        canvas_box,
    )
    axis_vector = (
        axis_point[0] - center[0],
        axis_point[1] - center[1],
    )
    axis_length = math.hypot(*axis_vector)
    assert axis_length > 8
    unit_axis = (axis_vector[0] / axis_length, axis_vector[1] / axis_length)
    start = {
        "x": axis_point[0],
        "y": axis_point[1],
    }
    end = {
        "x": axis_point[0] + unit_axis[0] * 80,
        "y": axis_point[1] + unit_axis[1] * 80,
    }
    assert (
        canvas_box["x"] <= start["x"] <= canvas_box["x"] + canvas_box["width"]
        and canvas_box["y"] <= start["y"] <= canvas_box["y"] + canvas_box["height"]
    )
    return start, end


def run_director_drag(page: Page) -> dict[str, Any]:
    errors = attach_errors(page)
    workspace = open_director(page, "director-drag")
    row = page.locator("[data-director-object-id='director-prop-mug']")
    row.click()
    page.wait_for_timeout(240)
    selected = director_state(page)
    assert selected["selectedObjectId"] == "director-prop-mug"
    assert selected["transformMode"] == "translate"
    assert workspace.locator("[data-director-viewport]").count() == 1
    graph_before = graph_snapshot(page)
    before = director_state(page)
    start, end = gizmo_drag_points(page)
    page.mouse.move(start["x"], start["y"])
    page.mouse.down()
    page.mouse.move(end["x"], end["y"], steps=12)
    page.mouse.up()
    page.wait_for_timeout(260)
    after = director_state(page)
    assert after["authoredPosition"] != before["authoredPosition"]
    assert after["runtimePosition"] == after["authoredPosition"]
    assert after["historyPast"] == before["historyPast"] + 1
    assert after["activeGesture"] is False
    assert after["lastCommand"] == {
        "commandKind": "GESTURE_COMMIT",
        "disposition": "COMMITTED",
        "reason": None,
        "historyEntries": 1,
    }
    assert graph_snapshot(page) == graph_before

    page.evaluate("() => window.__director_store.getState().undoDirector()")
    page.wait_for_timeout(120)
    undone = director_state(page)
    assert undone["authoredPosition"] == before["authoredPosition"]
    assert undone["runtimePosition"] == before["runtimePosition"]
    assert undone["historyFuture"] == after["historyFuture"] + 1
    assert undone["activeGesture"] is False

    page.evaluate("() => window.__director_store.getState().redoDirector()")
    page.wait_for_timeout(120)
    redone = director_state(page)
    assert redone["authoredPosition"] == after["authoredPosition"]
    assert redone["runtimePosition"] == after["runtimePosition"]
    assert redone["activeGesture"] is False
    assert graph_snapshot(page) == graph_before
    assert errors == [], json.dumps(errors, ensure_ascii=False, indent=2)
    return {
        "selectedObject": "director-prop-mug",
        "gizmoPointerDrag": True,
        "authoredRuntimeSynchronized": True,
        "directorHistoryDelta": 1,
        "undoRedo": True,
        "ordinaryGraphUnchanged": True,
    }


def run_director_noop_drag(page: Page) -> dict[str, Any]:
    errors = attach_errors(page)
    open_director(page, "director-noop-drag")
    page.locator("[data-director-object-id='director-prop-mug']").click()
    page.wait_for_timeout(220)
    before = director_state(page)
    start, _ = gizmo_drag_points(page)
    page.mouse.move(start["x"], start["y"])
    page.mouse.down()
    page.mouse.up()
    page.wait_for_timeout(220)
    after = director_state(page)
    assert after["authoredPosition"] == before["authoredPosition"]
    assert after["runtimePosition"] == before["runtimePosition"]
    assert after["historyPast"] == before["historyPast"]
    assert after["activeGesture"] is False
    assert errors == [], json.dumps(errors, ensure_ascii=False, indent=2)
    return {
        "zeroDistanceDrag": True,
        "historyUnchanged": True,
        "gestureCleared": True,
    }


def verify_static_contract() -> None:
    page_source = (ROOT / "src/app/page.tsx").read_text(encoding="utf-8")
    viewport_source = (
        ROOT / "src/components/director/DirectorViewport.tsx"
    ).read_text(encoding="utf-8")
    assert "panOnScrollSpeed={1}" in page_source
    assert "panOnDrag={effectivePan ? [0, 1] : [1]}" in page_source
    assert "selectionOnDrag={false}" in page_source
    assert viewport_source.count("object={transformTarget}") == 3
    assert "window.addEventListener(\"pointerup\", handlePointerUp)" in viewport_source
    assert "window.addEventListener(\"pointercancel\", cancelTransform)" in viewport_source


def main() -> None:
    verify_static_contract()
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        desktop = browser.new_page(
            viewport={"width": 1440, "height": 900},
            device_scale_factor=1,
        )
        navigation_desktop = run_navigation_desktop(desktop)
        desktop.close()

        mobile = browser.new_page(
            viewport={"width": 390, "height": 844},
            device_scale_factor=1,
        )
        navigation_mobile = run_navigation_mobile(mobile)
        mobile.close()

        director = browser.new_page(
            viewport={"width": 1440, "height": 900},
            device_scale_factor=1,
        )
        director_drag = run_director_drag(director)
        director.close()

        director_noop = browser.new_page(
            viewport={"width": 1440, "height": 900},
            device_scale_factor=1,
        )
        director_noop_drag = run_director_noop_drag(director_noop)
        director_noop.close()
        browser.close()

    audit = {
        "batch": 77,
        "status": "SCRIPT_RECORDED_PASS",
        "baseUrl": BASE_URL,
        "sourceEvidence": {
            "navigationAudit": "SOURCE_NAVIGATION_AUDIT_2026-08-28.md",
            "sourceExactDirectorGizmo": False,
            "sourceMutation": False,
        },
        "cloneContract": {
            "navigation": navigation_desktop,
            "mobile": navigation_mobile,
            "directorDrag": director_drag,
            "directorNoopDrag": director_noop_drag,
        },
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
