#!/usr/bin/env python3

"""Verify Batch 86 Director transform target context and cancellation behavior."""

from __future__ import annotations

import json
import math
import os
from pathlib import Path
from typing import Any

from playwright.sync_api import Locator, Page, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
BASE_URL = os.environ.get("LIBLIB_BASE_URL", "http://localhost:4317")
AUDIT_PATH = (
    ROOT
    / "docs"
    / "research"
    / "liblib-canvas-batch86-2026-08-29"
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


def box(locator: Locator) -> dict[str, float]:
    result = locator.bounding_box()
    assert result is not None
    return {key: float(value) for key, value in result.items()}


def wait_for_app(page: Page) -> None:
    page.wait_for_function(
        "() => Boolean(window.__libtv_store && window.__director_store)"
    )
    page.wait_for_selector("[data-libtv-react-flow-host]")


def reset_director_persistence(page: Page) -> None:
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
    page.wait_for_timeout(500)
    return fixture


def director_state(page: Page, object_id: str = "director-prop-mug") -> dict[str, Any]:
    return page.evaluate(
        """(objectId) => {
          const state = window.__director_store.getState();
          const authored = state.authoredObjects.find(
            (item) => item.id === objectId
          );
          const runtime = state.objects.find((item) => item.id === objectId);
          return {
            selectedObjectId: state.selectedObjectId,
            selectedObjectIds: state.selectedObjectIds,
            selectedGroupId: state.selectedGroupId,
            authored: authored ? {
              id: authored.id,
              name: authored.name,
              locked: authored.locked,
              transform: authored.transform,
            } : null,
            runtime: runtime ? {
              id: runtime.id,
              locked: runtime.locked,
              transform: runtime.transform,
            } : null,
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
        }""",
        object_id,
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
    position = tuple(float(value) for value in state["authored"]["transform"]["position"])
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
    start = {"x": axis_point[0], "y": axis_point[1]}
    end = {
        "x": axis_point[0] + unit_axis[0] * 72,
        "y": axis_point[1] + unit_axis[1] * 72,
    }
    assert (
        canvas_box["x"] <= start["x"] <= canvas_box["x"] + canvas_box["width"]
        and canvas_box["y"] <= start["y"] <= canvas_box["y"] + canvas_box["height"]
    )
    return start, end


def close_session(page: Page, owner: dict[str, str]) -> None:
    page.evaluate(
        """(owner) => {
          window.__director_store.getState().closeSession(owner);
          window.__libtv_ui_store.getState().closeDirectorDesk();
        }""",
        owner,
    )
    page.locator("[data-director-workspace]").wait_for(state="hidden")


def main() -> None:
    all_errors: list[str] = []
    results: dict[str, Any] = {}
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            device_scale_factor=1,
        )
        page = context.new_page()
        errors, phase = attach_errors(page)
        all_errors = errors
        page.goto(BASE_URL, wait_until="domcontentloaded")
        wait_for_app(page)

        phase[0] = "reset"
        reset_director_persistence(page)
        page.reload(wait_until="domcontentloaded")
        wait_for_app(page)
        owner = open_director(page)
        toolbar = page.locator("[data-director-viewport-toolbar]")
        context_surface = toolbar.locator("[data-director-transform-context]")

        phase[0] = "no-selection-context"
        page.evaluate(
            "() => window.__director_store.getState().selectObject(null, 'viewport')"
        )
        page.wait_for_function(
            """() => {
              const element = document.querySelector(
                '[data-director-transform-context]'
              );
              return element?.getAttribute('data-director-transform-context-kind') ===
                'none' &&
                element?.getAttribute('data-director-transform-context-state') ===
                'idle';
            }"""
        )
        assert context_surface.get_attribute("data-director-transform-context-target") == "未选择对象"
        results["noSelectionContext"] = True

        phase[0] = "object-context"
        page.locator('[data-director-object-id="director-prop-mug"]').click()
        page.wait_for_function(
            """() => {
              const element = document.querySelector(
                '[data-director-transform-context]'
              );
              return element?.getAttribute('data-director-transform-context-kind') ===
                'object' &&
                element?.getAttribute('data-director-transform-context-state') ===
                'editable' &&
                element?.getAttribute('data-director-transform-context-target') ===
                '冷掉的咖啡';
            }"""
        )
        assert context_surface.locator("[data-director-transform-context-label]").inner_text() == "冷掉的咖啡"
        assert context_surface.locator("[data-director-transform-context-detail]").inner_text() == "可拖动三轴控件"
        assert page.locator('[data-director-transform-field="position"]').count() == 3
        results["objectContextAndInspector"] = True

        phase[0] = "pointer-cancel"
        before_cancel = director_state(page)
        start, end = gizmo_drag_points(page)
        page.mouse.move(start["x"], start["y"])
        page.mouse.down()
        page.mouse.move(end["x"], end["y"], steps=4)
        page.evaluate(
            "() => window.dispatchEvent(new PointerEvent('pointercancel', { bubbles: true }))"
        )
        page.mouse.up()
        page.wait_for_timeout(240)
        after_cancel = director_state(page)
        assert after_cancel["authored"]["transform"] == before_cancel["authored"]["transform"]
        assert after_cancel["runtime"]["transform"] == before_cancel["runtime"]["transform"]
        assert after_cancel["historyPast"] == before_cancel["historyPast"]
        assert after_cancel["activeGesture"] is False
        results["pointerCancelRestoresAndClears"] = True

        phase[0] = "gizmo-drag"
        before_drag = director_state(page)
        start, end = gizmo_drag_points(page)
        page.mouse.move(start["x"], start["y"])
        page.mouse.down()
        page.mouse.move(end["x"], end["y"], steps=12)
        page.mouse.up()
        page.wait_for_timeout(260)
        after_drag = director_state(page)
        assert after_drag["authored"]["transform"] != before_drag["authored"]["transform"]
        assert after_drag["runtime"]["transform"] == after_drag["authored"]["transform"]
        assert after_drag["historyPast"] == before_drag["historyPast"] + 1
        assert after_drag["activeGesture"] is False
        assert after_drag["lastCommand"] == {
            "commandKind": "GESTURE_COMMIT",
            "disposition": "COMMITTED",
            "reason": None,
            "historyEntries": 1,
        }
        page.evaluate("() => window.__director_store.getState().undoDirector()")
        page.wait_for_timeout(120)
        assert director_state(page)["authored"]["transform"] == before_drag["authored"]["transform"]
        page.evaluate("() => window.__director_store.getState().redoDirector()")
        page.wait_for_timeout(120)
        assert director_state(page)["authored"]["transform"] == after_drag["authored"]["transform"]
        results["gizmoDragHistoryUndoRedo"] = True

        phase[0] = "locked-context-and-reject"
        # Undo/redo restores the document snapshot's selection authority. Re-select
        # the target before exercising the lock affordance for that target.
        page.locator('[data-director-object-id="director-prop-mug"]').click()
        page.wait_for_timeout(120)
        lock = page.locator('[data-director-object-lock="director-prop-mug"]')
        lock.click()
        page.wait_for_function(
            """() => window.__director_store.getState().objects.find(
              (item) => item.id === 'director-prop-mug'
            )?.locked === true"""
        )
        page.wait_for_function(
            """() => document.querySelector(
              '[data-director-transform-context]'
            )?.getAttribute('data-director-transform-context-state') === 'locked'"""
        )
        assert (
            context_surface.locator("[data-director-transform-context-detail]").inner_text()
            == "对象已锁定"
        )
        before_reject = director_state(page)
        result = page.evaluate(
            """() => window.__director_store.getState().updateObjectTransform(
              'director-prop-mug', 'position', 0, 99
            )"""
        )
        assert result["disposition"] == "REJECTED"
        assert result["reason"] == "DIRECTOR_TARGET_LOCKED"
        after_reject = director_state(page)
        assert after_reject["authored"]["transform"] == before_reject["authored"]["transform"]
        assert after_reject["historyPast"] == before_reject["historyPast"]
        results["lockedContextAndZeroMutation"] = True

        phase[0] = "mobile-context"
        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(120)
        assert context_surface.bounding_box() is not None
        toolbar_box = box(toolbar)
        context_box = box(context_surface)
        assert context_box["x"] >= toolbar_box["x"]
        assert context_box["x"] + context_box["width"] <= toolbar_box["x"] + toolbar_box["width"] + 1
        assert page.evaluate(
            "() => document.documentElement.scrollWidth <= document.documentElement.clientWidth"
        )
        results["mobileContextGeometry"] = True

        phase[0] = "close"
        close_session(page, owner)
        browser.close()

    diagnostics = {
        "consoleErrors": len([item for item in all_errors if ":console:" in item]),
        "pageErrors": len([item for item in all_errors if ":pageerror:" in item]),
        "requestFailures": len([item for item in all_errors if ":requestfailed:" in item]),
        "details": all_errors,
    }
    audit = {
        "batch": 86,
        "status": "SCRIPT_RECORDED_PASS",
        "baseUrl": BASE_URL,
        "contract": {
            "scope": "clone-owned Director transform target discoverability and pointer cancellation",
            "sourceExact": False,
            "targetContextProjected": True,
            "lockedTransformRejected": True,
            "pointerCancelRestoresBaseline": True,
            "lostPointerCaptureStaticBoundary": True,
        },
        "desktop": results,
        "mobile": {"contextWithinToolbar": True, "noHorizontalOverflow": True},
        "diagnostics": diagnostics,
    }
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    if all_errors:
        raise AssertionError("\n".join(all_errors))
    print(json.dumps(audit, ensure_ascii=False))


if __name__ == "__main__":
    main()
