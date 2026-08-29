#!/usr/bin/env python3

"""Verify Batch 91 Director object, camera and group command boundaries."""

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
    / "liblib-canvas-batch91-2026-08-29"
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
        """(owner) => {
          const state = window.__director_store.getState();
          return state.projectOwner?.canvasId === owner.canvasId &&
            state.projectOwner?.sourceNodeId === owner.sourceNodeId &&
            state.projectId !== null &&
            state.sessionId !== null &&
            state.generation !== null &&
            state.projectLifecycle === "ACTIVE";
        }""",
        arg=fixture,
    )
    page.locator('canvas[data-director-webgl-canvas="true"]').wait_for(
        state="visible"
    )
    page.wait_for_timeout(250)
    return fixture


def read_state(page: Page) -> dict[str, Any]:
    return page.evaluate(
        """() => {
          const state = window.__director_store.getState();
          return {
            scene: state.scene,
            authoredObjects: state.authoredObjects,
            objects: state.objects,
            groups: state.groups,
            selectedObjectId: state.selectedObjectId,
            selectedObjectIds: state.selectedObjectIds,
            selectedGroupId: state.selectedGroupId,
            historyPast: state.history.past.length,
            historyFuture: state.history.future.length,
            lastCommand: state.lastCommandResult,
            persisted: window.__director_project_persistence_snapshot(),
          };
        }"""
    )


def run_browser_verifier(page: Page) -> dict[str, Any]:
    errors, phase = attach_errors(page)
    page.goto(f"{BASE_URL}/?batch91=1", wait_until="networkidle")
    wait_for_app(page)
    clear_persistence(page)
    page.reload(wait_until="networkidle")
    wait_for_app(page)
    fixture = open_director(page)
    state = read_state(page)

    character_id = next(
        item["id"] for item in state["authoredObjects"] if item["kind"] == "character"
    )
    camera_id = next(
        item["id"] for item in state["authoredObjects"] if item["kind"] == "camera"
    )

    phase[0] = "object-name-draft"
    name_input = page.locator("[data-director-object-name]")
    original_name = next(
        item["name"] for item in state["authoredObjects"] if item["id"] == character_id
    )
    history_before_draft = read_state(page)["historyPast"]
    name_input.fill("Batch 91 object")
    draft = read_state(page)
    assert draft["historyPast"] == history_before_draft
    assert next(
        item["name"] for item in draft["authoredObjects"] if item["id"] == character_id
    ) == original_name
    name_input.press("Enter")
    page.wait_for_function(
        """(objectId) =>
          window.__director_store.getState().authoredObjects.find(
            (object) => object.id === objectId
          )?.name === "Batch 91 object" """,
        arg=character_id,
    )
    object_name = read_state(page)
    assert object_name["historyPast"] == history_before_draft + 1
    assert object_name["lastCommand"]["commandKind"] == "UPDATE_OBJECT"
    assert object_name["lastCommand"]["disposition"] == "COMMITTED"

    phase[0] = "object-visibility"
    visibility_result = page.evaluate(
        """(objectId) =>
          window.__director_store.getState().updateObject(objectId, {
            visible: false
          })""",
        character_id,
    )
    assert visibility_result["disposition"] == "COMMITTED"
    after_visibility = read_state(page)
    assert after_visibility["historyPast"] == object_name["historyPast"] + 1
    assert next(
        item["visible"]
        for item in after_visibility["authoredObjects"]
        if item["id"] == character_id
    ) is False
    assert any(
        record["status"] == "SAVED"
        and record["projectId"] == after_visibility["lastCommand"]["projectId"]
        for record in after_visibility["persisted"]["records"]
    )

    phase[0] = "camera-command"
    page.evaluate(
        """(cameraId) => window.__director_store.getState().selectObject(cameraId)""",
        camera_id,
    )
    camera_before = read_state(page)
    camera_result = page.evaluate(
        """(cameraId) =>
          window.__director_store.getState().updateCamera(cameraId, {
            fov: 55
          })""",
        camera_id,
    )
    assert camera_result["disposition"] == "COMMITTED"
    camera_after = read_state(page)
    assert camera_after["historyPast"] == camera_before["historyPast"] + 1
    assert next(
        item["camera"]["fov"]
        for item in camera_after["authoredObjects"]
        if item["id"] == camera_id
    ) == 55
    assert any(
        record["status"] == "SAVED"
        and record["projectId"] == camera_result["projectId"]
        for record in camera_after["persisted"]["records"]
    )

    noop_result = page.evaluate(
        """(cameraId) =>
          window.__director_store.getState().updateCamera(cameraId, {
            fov: 55
          })""",
        camera_id,
    )
    noop_state = read_state(page)
    assert noop_result["disposition"] == "NOOP"
    assert noop_result["historyEntries"] == 0
    assert noop_state["historyPast"] == camera_after["historyPast"]

    invalid_reference = page.evaluate(
        """(cameraId) =>
          window.__director_store.getState().updateCamera(cameraId, {
            followTargetId: "batch91-missing-target"
          })""",
        camera_id,
    )
    invalid_state = read_state(page)
    assert invalid_reference["disposition"] == "REJECTED"
    assert invalid_reference["reason"] == "DIRECTOR_REFERENCE_INVALID"
    assert invalid_state["historyPast"] == noop_state["historyPast"]

    valid_reference = page.evaluate(
        """([cameraId, characterId]) =>
          window.__director_store.getState().updateCamera(cameraId, {
            followTargetId: characterId
          })""",
        [camera_id, character_id],
    )
    assert valid_reference["disposition"] == "COMMITTED"
    followed = read_state(page)
    assert next(
        item["camera"]["followTargetId"]
        for item in followed["authoredObjects"]
        if item["id"] == camera_id
    ) == character_id

    phase[0] = "group-command"
    crowd_group_id = page.evaluate(
        """() => window.__director_store.getState().addCrowdArray({
          rows: 1,
          columns: 2,
          spacing: 1
        })"""
    )
    page.wait_for_function(
        "(groupId) => window.__director_store.getState().groups.some((group) => group.id === groupId)",
        arg=crowd_group_id,
    )
    page.evaluate("() => window.__director_store.getState().ungroupSelectedCharacters()")
    page.wait_for_function(
        "(groupId) => !window.__director_store.getState().groups.some((group) => group.id === groupId)",
        arg=crowd_group_id,
    )
    before_group = read_state(page)
    created_group_id = page.evaluate(
        "() => window.__director_store.getState().groupSelectedCharacters()"
    )
    assert created_group_id
    page.wait_for_function(
        "(groupId) => window.__director_store.getState().groups.some((group) => group.id === groupId)",
        arg=created_group_id,
    )
    grouped = read_state(page)
    assert grouped["historyPast"] == before_group["historyPast"] + 1
    assert grouped["lastCommand"]["commandKind"] == "GROUP_CHARACTERS"
    assert grouped["lastCommand"]["disposition"] == "COMMITTED"

    phase[0] = "group-name-draft"
    group_name = page.locator("[data-director-group-name]")
    group_label = next(
        group["label"] for group in grouped["groups"] if group["id"] == created_group_id
    )
    group_history_before_draft = read_state(page)["historyPast"]
    group_name.fill("Batch 91 group")
    group_draft = read_state(page)
    assert group_draft["historyPast"] == group_history_before_draft
    assert next(
        group["label"] for group in group_draft["groups"] if group["id"] == created_group_id
    ) == group_label
    group_name.press("Enter")
    page.wait_for_function(
        """(groupId) =>
          window.__director_store.getState().groups.find(
            (group) => group.id === groupId
          )?.label === "Batch 91 group" """,
        arg=created_group_id,
    )
    renamed_group = read_state(page)
    assert renamed_group["historyPast"] == group_history_before_draft + 1
    assert renamed_group["lastCommand"]["commandKind"] == "UPDATE_GROUP"

    phase[0] = "group-transform"
    transform_result = page.evaluate(
        """(groupId) =>
          window.__director_store.getState().updateGroupTransform(groupId, {
            position: [0.5, 0, 0.8],
            rotation: [0, 0, 0],
            scale: [1, 1, 1]
          })""",
        created_group_id,
    )
    assert transform_result["disposition"] == "COMMITTED"
    transformed = read_state(page)
    assert transformed["historyPast"] == renamed_group["historyPast"] + 1
    assert transformed["lastCommand"]["commandKind"] == "UPDATE_GROUP_TRANSFORM"

    invalid_transform = page.evaluate(
        """(groupId) =>
          window.__director_store.getState().updateGroupTransform(groupId, {
            position: [0.5, 0, 0.8],
            rotation: [0, 0, 0],
            scale: [0, 0, 1]
          })""",
        created_group_id,
    )
    invalid_transform_state = read_state(page)
    assert invalid_transform["disposition"] == "REJECTED"
    assert invalid_transform["reason"] == "DIRECTOR_INVALID_VALUE"
    assert invalid_transform_state["historyPast"] == transformed["historyPast"]

    return {
        "batch": 91,
        "status": "SCRIPT_RECORDED_PASS",
        "baseUrl": BASE_URL,
        "sourceExact": False,
        "fixture": fixture,
        "desktop": {
            "objectNameDraftCommit": True,
            "objectVisibilityCommand": True,
            "cameraCommandPersistence": True,
            "cameraNoopZeroHistory": True,
            "cameraInvalidReferenceZeroMutation": True,
            "groupCreateCommand": True,
            "groupNameDraftCommit": True,
            "groupTransformCommand": True,
            "groupInvalidTransformZeroHistory": True,
        },
        "history": {
            "objectName": object_name["historyPast"],
            "objectVisibility": after_visibility["historyPast"],
            "camera": camera_after["historyPast"],
            "group": transformed["historyPast"],
        },
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
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print("Batch 91 Director object, camera and group verification passed.")


if __name__ == "__main__":
    main()
