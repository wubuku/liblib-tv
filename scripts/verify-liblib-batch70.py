#!/usr/bin/env python3

"""Verify the Batch 70 Director command/history kernel."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from playwright.sync_api import Page, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
BASE_URL = os.environ.get("LIBLIB_BASE_URL", "http://localhost:3000")
AUDIT_PATH = (
    ROOT
    / "docs"
    / "research"
    / "liblib-canvas-batch70-2026-08-27"
    / "runtime-audit.json"
)


def run_pure_verifier() -> dict:
    completed = subprocess.run(
        [
            "node",
            "--disable-warning=MODULE_TYPELESS_PACKAGE_JSON",
            "--experimental-strip-types",
            "scripts/verify-liblib-batch70.mjs",
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
            owner: state.projectOwner,
            authoredFingerprint: JSON.stringify(state.authoredObjects),
            authoredObjects: state.authoredObjects.map((object) => ({
              id: object.id,
              position: object.transform.position,
              fov: object.camera?.fov ?? null,
            })),
            history: {
              past: state.history.past.length,
              future: state.history.future.length,
              gesture: state.history.activeGesture
                ? {
                    commandKind: state.history.activeGesture.commandKind,
                    targetId: state.history.activeGesture.targetId,
                  }
                : null,
            },
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


def prepare_two_director_nodes(page: Page) -> dict:
    return page.evaluate(
        """() => {
          const store = window.__libtv_store.getState();
          const canvasId = store.activeCanvasId;
          const before = new Set(
            store.getActiveCanvas()?.nodes.map((node) => node.id) || [],
          );
          store.addNode("script-execution", { title: "Batch 70 A" });
          const afterA = store.getActiveCanvas()?.nodes || [];
          const nodeA = afterA.find((node) => !before.has(node.id))?.id;
          const beforeB = new Set(afterA.map((node) => node.id));
          store.addNode("script-execution", { title: "Batch 70 B" });
          const afterB = store.getActiveCanvas()?.nodes || [];
          const nodeB = afterB.find((node) => !beforeB.has(node.id))?.id;
          if (!nodeA || !nodeB) throw new Error("Director fixture creation failed");
          return { canvasId, nodeA, nodeB };
        }"""
    )


def open_owner(page: Page, canvas_id: str, node_id: str) -> dict:
    page.evaluate(
        """({ canvasId, nodeId }) => {
          window.__libtv_ui_store.getState().openDirectorDesk(nodeId, canvasId);
        }""",
        {"canvasId": canvas_id, "nodeId": node_id},
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
        arg={"canvasId": canvas_id, "nodeId": node_id},
    )
    page.locator("[data-director-workspace]").wait_for(state="visible")
    return director_state(page)


def run_browser_verifier(page: Page) -> dict:
    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/?batch70=1", wait_until="networkidle")
    page.wait_for_function(
        """() => Boolean(
          window.__libtv_store &&
          window.__libtv_ui_store &&
          window.__director_store &&
          window.__director_project_registry_snapshot
        )"""
    )
    fixture = prepare_two_director_nodes(page)
    graph_after_fixture = graph_state(page)

    initial = open_owner(page, fixture["canvasId"], fixture["nodeA"])
    character = next(
        item for item in initial["authoredObjects"] if item["id"] == "director-character-lead"
    )
    initial_position = character["position"][0]
    assert initial["history"] == {"past": 0, "future": 0, "gesture": None}

    page.evaluate(
        """({ objectId, value }) => {
          window.__director_store.getState().updateObjectTransform(
            objectId,
            "position",
            0,
            value,
          );
        }""",
        {"objectId": character["id"], "value": initial_position + 1},
    )
    first_commit = director_state(page)
    assert first_commit["history"]["past"] == 1
    assert first_commit["history"]["future"] == 0
    assert first_commit["lastCommand"]["disposition"] == "COMMITTED"
    assert first_commit["lastCommand"]["historyEntries"] == 1

    page.evaluate(
        """({ objectId, value }) => {
          window.__director_store.getState().updateObjectTransform(
            objectId,
            "position",
            0,
            value,
          );
        }""",
        {"objectId": character["id"], "value": initial_position + 1},
    )
    noop = director_state(page)
    assert noop["history"]["past"] == 1
    assert noop["lastCommand"] == {
        "commandKind": "UPDATE_OBJECT_TRANSFORM",
        "disposition": "NOOP",
        "reason": "DIRECTOR_COMMAND_NO_CHANGE",
        "historyEntries": 0,
    }

    invalid = page.evaluate(
        """({ objectId }) => {
          return window.__director_store.getState().updateObjectTransform(
            objectId,
            "position",
            0,
            Number.NaN,
          );
        }""",
        {"objectId": character["id"]},
    )
    assert invalid["disposition"] == "REJECTED"
    assert invalid["reason"] == "DIRECTOR_INVALID_VALUE"
    assert director_state(page)["history"]["past"] == 1

    missing = page.evaluate(
        """() => {
          return window.__director_store.getState().updateObjectTransform(
            "missing-director-object",
            "position",
            0,
            1,
          );
        }"""
    )
    assert missing["disposition"] == "REJECTED"
    assert missing["reason"] == "DIRECTOR_TARGET_MISSING"
    assert director_state(page)["history"]["past"] == 1

    page.evaluate("() => window.__director_store.getState().undoDirector()")
    undone = director_state(page)
    assert undone["history"]["past"] == 0
    assert undone["history"]["future"] == 1
    undone_character = next(
        item for item in undone["authoredObjects"] if item["id"] == character["id"]
    )
    assert undone_character["position"][0] == initial_position
    assert undone["lastCommand"]["commandKind"] == "UNDO"

    page.evaluate("() => window.__director_store.getState().redoDirector()")
    redone = director_state(page)
    assert redone["history"]["past"] == 1
    assert redone["history"]["future"] == 0
    redone_character = next(
        item for item in redone["authoredObjects"] if item["id"] == character["id"]
    )
    assert redone_character["position"][0] == initial_position + 1

    page.evaluate("() => window.__director_store.getState().undoDirector()")
    page.evaluate(
        """({ objectId, value }) => {
          window.__director_store.getState().updateObjectTransform(
            objectId,
            "position",
            1,
            value,
          );
        }""",
        {"objectId": character["id"], "value": 0.6},
    )
    future_truncated = director_state(page)
    assert future_truncated["history"]["past"] == 1
    assert future_truncated["history"]["future"] == 0

    page.evaluate(
        """({ objectId }) => {
          const state = window.__director_store.getState();
          state.beginDirectorGesture({
            commandKind: "batch70-transform",
            targetId: objectId,
            fieldScope: "position",
          });
          state.updateObjectTransform(objectId, "position", 0, 2.1);
          state.updateObjectTransform(objectId, "position", 0, 2.2);
          state.updateObjectTransform(objectId, "position", 0, 2.3);
        }""",
        {"objectId": character["id"]},
    )
    during_gesture = director_state(page)
    assert during_gesture["history"]["past"] == 1
    assert during_gesture["history"]["gesture"]["commandKind"] == "batch70-transform"

    page.evaluate("() => window.__director_store.getState().commitDirectorGesture()")
    gesture_committed = director_state(page)
    assert gesture_committed["history"]["past"] == 2
    assert gesture_committed["history"]["future"] == 0
    assert gesture_committed["lastCommand"]["historyEntries"] == 1

    page.evaluate("() => window.__director_store.getState().undoDirector()")
    after_gesture_undo = director_state(page)
    assert after_gesture_undo["history"]["past"] == 1
    assert after_gesture_undo["history"]["future"] == 1
    page.evaluate("() => window.__director_store.getState().redoDirector()")
    after_gesture_redo = director_state(page)
    assert after_gesture_redo["history"]["past"] == 2
    assert after_gesture_redo["history"]["future"] == 0

    state_b = open_owner(page, fixture["canvasId"], fixture["nodeB"])
    assert state_b["history"]["past"] == 0
    page.evaluate(
        """() => {
          const state = window.__director_store.getState();
          const object = state.authoredObjects.find(
            (item) => item.id === "director-character-lead",
          );
          if (!object) throw new Error("B character missing");
          state.updateObjectTransform(
            object.id,
            "position",
            2,
            object.transform.position[2] + 0.4,
          );
        }"""
    )
    state_b_changed = director_state(page)
    assert state_b_changed["history"]["past"] == 1

    state_a_again = open_owner(page, fixture["canvasId"], fixture["nodeA"])
    assert state_a_again["history"]["past"] == 2
    assert state_a_again["history"]["future"] == 0
    generation_before_reopen = page.evaluate(
        "() => window.__director_store.getState().generation"
    )
    page.locator("[data-close-director]").click()
    page.locator("[data-director-workspace]").wait_for(state="detached")
    reopened = open_owner(page, fixture["canvasId"], fixture["nodeA"])
    generation_after_reopen = page.evaluate(
        "() => window.__director_store.getState().generation"
    )
    assert generation_after_reopen > generation_before_reopen
    assert reopened["history"]["past"] == 2
    page.evaluate("() => window.__director_store.getState().undoDirector()")
    reopened_undo = director_state(page)
    assert reopened_undo["history"]["past"] == 1
    assert reopened_undo["history"]["future"] == 1
    assert reopened_undo["lastCommand"]["disposition"] == "COMMITTED"
    assert graph_state(page) == graph_after_fixture
    assert errors == [], json.dumps(errors, ensure_ascii=False, indent=2)

    return {
        "semanticMutationOneEntry": "pass",
        "noopZeroEntry": "pass",
        "undoRedoRoundTrip": "pass",
        "futureTruncation": "pass",
        "gestureOneEntry": "pass",
        "ownerHistoryIsolation": "pass",
        "reopenHistoryContinuity": "pass",
        "ordinaryGraphIsolation": "pass",
    }


def main() -> None:
    pure = run_pure_verifier()
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        browser_result = run_browser_verifier(page)
        browser.close()

    audit = {
        "status": "PASS",
        "batch": 70,
        "baseUrl": BASE_URL,
        "pure": pure,
        "browser": browser_result,
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
