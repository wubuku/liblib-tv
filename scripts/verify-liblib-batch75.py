#!/usr/bin/env python3

"""Verify Batch 75 Director clipboard identity remap."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from playwright.sync_api import Page, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
BASE_URL = os.environ.get("LIBLIB_BASE_URL", "http://localhost:4317")
AUDIT_PATH = (
    ROOT
    / "docs"
    / "research"
    / "liblib-canvas-batch75-2026-08-27"
    / "runtime-audit.json"
)


def run_pure_verifier() -> dict:
    completed = subprocess.run(
        [
            "node",
            "--disable-warning=MODULE_TYPELESS_PACKAGE_JSON",
            "--experimental-strip-types",
            "scripts/verify-liblib-batch75.mjs",
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
            selectedNodeId: state.selectedNodeId,
          };
        }"""
    )


def storage_entries(page: Page) -> dict[str, str]:
    return page.evaluate(
        """() => Object.fromEntries(
          Object.keys(localStorage)
            .filter((key) => key.startsWith("liblib-tv-director-project-v1:"))
            .map((key) => [key, localStorage.getItem(key) || ""])
        )"""
    )


def director_state(page: Page) -> dict:
    return page.evaluate(
        """() => {
          const state = window.__director_store.getState();
          const registry = window.__director_project_registry_snapshot();
          const record = registry.records.find(
            (candidate) => candidate.identity.projectId === state.projectId,
          );
          const latest = state.history.past.at(-1) || null;
          return {
            owner: state.projectOwner,
            projectId: state.projectId,
            generation: state.generation,
            activeCameraId: state.activeCameraId,
            objects: state.authoredObjects.map((object) => ({
              id: object.id,
              kind: object.kind,
              position: object.transform.position,
              lookAtMode: object.camera?.lookAtMode ?? null,
              lookAtObjectId: object.camera?.lookAtObjectId ?? null,
              followTargetId: object.camera?.followTargetId ?? null,
              target: object.camera?.target ?? null,
              assetId: object.libraryAssetId ?? null,
            })),
            groups: state.groups.map((group) => ({
              id: group.id,
              characterIds: group.characterIds,
            })),
            tracks: state.timeline.tracks.map((track) => ({
              id: track.id,
              kind: track.kind,
              objectId: track.objectId,
              groupId: track.kind === "group" ? track.groupId : null,
              motionPathId: track.motionPathId ?? null,
              keyframeIds: track.keyframes.map((keyframe) => keyframe.id),
            })),
            paths: state.timeline.motionPaths.map((path) => ({
              id: path.id,
              objectId: path.objectId,
              anchorIds: path.anchors.map((anchor) => anchor.id),
            })),
            selection: {
              objectId: state.selectedObjectId,
              objectIds: state.selectedObjectIds,
              groupId: state.selectedGroupId,
            },
            history: {
              past: state.history.past.length,
              future: state.history.future.length,
              active: Boolean(state.history.activeGesture),
            },
            clipboard: state.clipboard
              ? {
                  sourceProjectId: state.clipboard.sourceProjectId,
                  objectIds: state.clipboard.objects.map((object) => object.id),
                  groupIds: state.clipboard.groups.map((group) => group.id),
                  trackIds: state.clipboard.timeline.tracks.map(
                    (track) => track.id,
                  ),
                  pathIds: state.clipboard.timeline.motionPaths.map(
                    (path) => path.id,
                  ),
                  resourceIds: state.clipboard.resourceRefs.map(
                    (resource) => resource.id,
                  ),
                  serialized: JSON.stringify(state.clipboard),
                }
              : null,
            clipboardPasteCount: state.clipboardPasteCount,
            captures: state.captures.map((capture) => ({
              id: capture.id,
              sentNodeId: capture.sentNodeId ?? null,
            })),
            lastCommand: state.lastCommandResult
              ? {
                  commandKind: state.lastCommandResult.commandKind,
                  disposition: state.lastCommandResult.disposition,
                  reason: state.lastCommandResult.reason,
                  historyEntries: state.lastCommandResult.historyEntries,
                }
              : null,
            documentFingerprint: record
              ? JSON.stringify(record.document)
              : null,
            latestHistory: latest
              ? {
                  before: JSON.stringify(latest.before),
                  after: JSON.stringify(latest.after),
                  commandKind: latest.commandKind,
                }
              : null,
          };
        }"""
    )


def prepare_director_nodes(page: Page) -> dict:
    return page.evaluate(
        """() => {
          const store = window.__libtv_store.getState();
          const canvasId = store.activeCanvasId;
          const before = new Set(
            store.getActiveCanvas()?.nodes.map((node) => node.id) || [],
          );
          store.addNode("script-execution", { title: "Batch 75 A" });
          const afterA = store.getActiveCanvas()?.nodes || [];
          const nodeA = afterA.find((node) => !before.has(node.id))?.id;
          const beforeB = new Set(afterA.map((node) => node.id));
          store.addNode("script-execution", { title: "Batch 75 B" });
          const afterB = store.getActiveCanvas()?.nodes || [];
          const nodeB = afterB.find((node) => !beforeB.has(node.id))?.id;
          if (!nodeA || !nodeB) {
            throw new Error("Batch 75 Director fixture creation failed");
          }
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
    page.locator('canvas[data-director-webgl-canvas="true"]').wait_for(
        state="visible"
    )
    return director_state(page)


def press_workspace_shortcut(page: Page, shortcut: str) -> None:
    page.locator("[data-director-workspace]").focus()
    page.keyboard.press(shortcut)


def run_browser_verifier(page: Page) -> tuple[dict, dict]:
    page.goto(f"{BASE_URL}/?batch75=clipboard", wait_until="networkidle")
    page.wait_for_function(
        """() => Boolean(
          window.__libtv_store &&
          window.__libtv_ui_store &&
          window.__director_store &&
          window.__director_project_registry_snapshot &&
          window.__director_project_persistence_snapshot
        )"""
    )
    fixture = prepare_director_nodes(page)
    graph_baseline = graph_state(page)
    initial = open_owner(page, fixture["canvasId"], fixture["nodeA"])
    owner_a = initial["owner"]
    project_a = initial["projectId"]
    source_object = next(
        item for item in initial["objects"] if item["id"] == "director-character-lead"
    )
    assert initial["selection"]["objectId"] == source_object["id"]

    press_workspace_shortcut(page, "Control+c")
    page.wait_for_function(
        """() => window.__director_store.getState().lastCommandResult
          ?.commandKind === "COPY_SELECTION" """
    )
    copied = director_state(page)
    assert copied["documentFingerprint"] == initial["documentFingerprint"]
    assert copied["history"] == initial["history"]
    assert copied["clipboard"]["sourceProjectId"] == project_a
    assert copied["clipboard"]["objectIds"] == [source_object["id"]]
    assert copied["clipboardPasteCount"] == 0
    assert "data:image" not in copied["clipboard"]["serialized"]
    assert "sentNodeId" not in copied["clipboard"]["serialized"]
    assert copied["lastCommand"] == {
        "commandKind": "COPY_SELECTION",
        "disposition": "COMMITTED",
        "reason": None,
        "historyEntries": 0,
    }

    press_workspace_shortcut(page, "Control+v")
    page.wait_for_function(
        """(count) =>
          window.__director_store.getState().authoredObjects.length === count + 1""",
        arg=len(initial["objects"]),
    )
    first_paste = director_state(page)
    first_pasted_id = first_paste["selection"]["objectId"]
    first_pasted = next(
        item for item in first_paste["objects"] if item["id"] == first_pasted_id
    )
    assert first_pasted_id != source_object["id"]
    assert first_pasted["position"] == [
        round(source_object["position"][0] + 0.6, 6),
        source_object["position"][1],
        round(source_object["position"][2] + 0.6, 6),
    ]
    assert first_paste["activeCameraId"] == initial["activeCameraId"]
    assert first_paste["history"]["past"] == initial["history"]["past"] + 1
    assert first_paste["clipboardPasteCount"] == 1
    assert first_paste["lastCommand"] == {
        "commandKind": "PASTE_CLIPBOARD",
        "disposition": "COMMITTED",
        "reason": None,
        "historyEntries": 1,
    }
    assert first_paste["latestHistory"]["commandKind"] == "PASTE_CLIPBOARD"
    assert (
        first_paste["documentFingerprint"]
        == first_paste["latestHistory"]["after"]
    )

    page.evaluate("() => window.__director_store.getState().undoDirector()")
    undone = director_state(page)
    assert undone["documentFingerprint"] == first_paste["latestHistory"]["before"]
    assert undone["history"]["future"] == 1
    assert undone["clipboardPasteCount"] == 1
    page.evaluate("() => window.__director_store.getState().redoDirector()")
    redone = director_state(page)
    assert redone["documentFingerprint"] == first_paste["latestHistory"]["after"]
    assert redone["clipboardPasteCount"] == 1

    press_workspace_shortcut(page, "Control+v")
    page.wait_for_function(
        "() => window.__director_store.getState().clipboardPasteCount === 2"
    )
    second_paste = director_state(page)
    second_pasted = next(
        item
        for item in second_paste["objects"]
        if item["id"] == second_paste["selection"]["objectId"]
    )
    assert second_pasted["id"] not in {source_object["id"], first_pasted_id}
    assert second_pasted["position"] == [
        round(source_object["position"][0] + 1.2, 6),
        source_object["position"][1],
        round(source_object["position"][2] + 1.2, 6),
    ]

    page.evaluate(
        """() => {
          const workspace = document.querySelector("[data-director-workspace]");
          if (!workspace) throw new Error("Batch 75 workspace missing");
          const input = document.createElement("input");
          input.dataset.batch75NativeInput = "true";
          input.value = "native clipboard";
          workspace.append(input);
          input.focus();
          input.select();
        }"""
    )
    native_before = director_state(page)
    page.keyboard.press("Control+c")
    page.keyboard.press("Control+v")
    page.wait_for_timeout(60)
    native_after = director_state(page)
    assert native_after["documentFingerprint"] == native_before["documentFingerprint"]
    assert native_after["history"] == native_before["history"]
    assert native_after["clipboardPasteCount"] == native_before["clipboardPasteCount"]
    page.evaluate(
        """() => document.querySelector("[data-batch75-native-input]")?.remove()"""
    )

    composition_before = director_state(page)
    page.evaluate(
        """() => {
          const workspace = document.querySelector("[data-director-workspace]");
          if (!workspace) throw new Error("Batch 75 workspace missing");
          for (const key of ["c", "v"]) {
            workspace.dispatchEvent(new KeyboardEvent("keydown", {
              key,
              ctrlKey: true,
              isComposing: true,
              bubbles: true,
              cancelable: true,
            }));
          }
        }"""
    )
    composition_after = director_state(page)
    assert (
        composition_after["documentFingerprint"]
        == composition_before["documentFingerprint"]
    )
    assert composition_after["history"] == composition_before["history"]
    assert (
        composition_after["clipboardPasteCount"]
        == composition_before["clipboardPasteCount"]
    )

    conflict = page.evaluate(
        """() => {
          const state = window.__director_store.getState();
          state.beginDirectorGesture({
            commandKind: "BATCH75_ACTIVE_GESTURE",
            targetId: state.selectedObjectId,
            fieldScope: "position",
          });
          return window.__director_store.getState().pasteDirectorClipboard();
        }"""
    )
    assert conflict["disposition"] == "CONFLICT"
    assert conflict["reason"] == "DIRECTOR_HISTORY_CONFLICT"
    page.evaluate("() => window.__director_store.getState().cancelDirectorGesture()")

    page.evaluate(
        """() => {
          const state = window.__director_store.getState();
          window.__director_store.setState({
            phoneVcam: { ...state.phoneVcam, status: "recording" },
          });
        }"""
    )
    page.wait_for_function(
        "() => window.__director_store.getState().phoneVcam.status === 'recording'"
    )
    busy_before = director_state(page)
    press_workspace_shortcut(page, "Control+v")
    page.wait_for_timeout(60)
    busy_after = director_state(page)
    assert busy_after["documentFingerprint"] == busy_before["documentFingerprint"]
    assert busy_after["history"] == busy_before["history"]
    assert busy_after["clipboardPasteCount"] == busy_before["clipboardPasteCount"]
    page.evaluate(
        """() => {
          const state = window.__director_store.getState();
          window.__director_store.setState({
            phoneVcam: { ...state.phoneVcam, status: "idle" },
          });
        }"""
    )

    page.evaluate(
        """() => {
          const state = window.__director_store.getState();
          state.addCapture({
            id: "batch75-capture",
            dataUrl:
              "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJ" +
              "AAAADUlEQVR42mNk+M/wHwAF/gL+XQ2mWQAAAABJRU5ErkJggg==",
            cameraId: state.activeCameraId,
            cameraName: "Batch 75 camera",
            aspectRatio: "16:9",
            width: 1280,
            height: 720,
            createdAt: "2026-08-27T20:00:00.000Z",
          });
          window.__director_store.getState().selectCapture("batch75-capture");
        }"""
    )
    page.locator('[data-director-object-kind="camera"]').first.click()
    page.locator('[data-director-camera-tab="captures"]').click()
    page.locator(
        '[data-director-capture-item="batch75-capture"] '
        '[data-director-capture-view]'
    ).click()
    page.locator("[data-director-capture-viewer]").wait_for(state="visible")
    viewer_before = director_state(page)
    press_workspace_shortcut(page, "Control+v")
    page.wait_for_timeout(60)
    viewer_after = director_state(page)
    assert viewer_after["documentFingerprint"] == viewer_before["documentFingerprint"]
    assert viewer_after["history"] == viewer_before["history"]
    assert viewer_after["clipboardPasteCount"] == viewer_before["clipboardPasteCount"]
    page.locator("[data-director-capture-viewer-close]").click()
    page.evaluate("() => window.__director_store.getState().selectCapture(null)")

    state_b = open_owner(page, fixture["canvasId"], fixture["nodeB"])
    assert state_b["clipboard"]["sourceProjectId"] == project_a
    b_before = director_state(page)
    press_workspace_shortcut(page, "Control+v")
    page.wait_for_function(
        """() => window.__director_store.getState().lastCommandResult
          ?.reason === "DIRECTOR_CLIPBOARD_STALE" """
    )
    b_after = director_state(page)
    assert b_after["documentFingerprint"] == b_before["documentFingerprint"]
    assert b_after["history"] == b_before["history"]
    assert b_after["selection"] == b_before["selection"]
    assert b_after["clipboardPasteCount"] == b_before["clipboardPasteCount"]
    assert b_after["lastCommand"] == {
        "commandKind": "PASTE_CLIPBOARD",
        "disposition": "STALE",
        "reason": "DIRECTOR_CLIPBOARD_STALE",
        "historyEntries": 0,
    }

    state_a_again = open_owner(page, fixture["canvasId"], fixture["nodeA"])
    assert state_a_again["projectId"] == project_a
    assert state_a_again["clipboardPasteCount"] == 2
    press_workspace_shortcut(page, "Control+v")
    page.wait_for_function(
        "() => window.__director_store.getState().clipboardPasteCount === 3"
    )
    third_paste = director_state(page)
    assert third_paste["history"]["past"] == state_a_again["history"]["past"] + 1
    assert graph_state(page) == graph_baseline

    persisted = storage_entries(page)
    owner_a_entries = [
        raw
        for raw in persisted.values()
        if json.loads(raw)["owner"] == owner_a
    ]
    assert len(owner_a_entries) == 1
    persisted_a = owner_a_entries[0]
    assert '"clipboard"' not in persisted_a
    assert "clipboardPasteCount" not in persisted_a
    assert "data:image" not in persisted_a
    assert "sentNodeId" not in persisted_a

    browser_result = {
        "keyboard": {
            "copy": "Control+C",
            "paste": "Control+V",
            "oneHistory": True,
            "selectionTargetsPaste": True,
        },
        "identityAndOffset": {
            "firstPasteOffset": 0.6,
            "secondPasteOffset": 1.2,
            "thirdPasteOrdinal": third_paste["clipboardPasteCount"],
            "uniqueIds": len(
                {
                    source_object["id"],
                    first_pasted_id,
                    second_pasted["id"],
                    third_paste["selection"]["objectId"],
                }
            )
            == 4,
        },
        "history": {
            "undoExact": undone["documentFingerprint"]
            == first_paste["latestHistory"]["before"],
            "redoExact": redone["documentFingerprint"]
            == first_paste["latestHistory"]["after"],
        },
        "guards": {
            "editableNative": True,
            "compositionNative": True,
            "activeGestureConflict": conflict["reason"],
            "busyBlocked": True,
            "captureViewerBlocked": True,
        },
        "projectIsolation": {
            "staleReason": b_after["lastCommand"]["reason"],
            "aBAContinuity": third_paste["clipboardPasteCount"] == 3,
        },
        "boundaries": {
            "ordinaryGraphUnchanged": graph_state(page) == graph_baseline,
            "persistenceExcludesClipboard": True,
            "persistenceExcludesCaptureBytes": True,
        },
    }
    restore_expectation = {
        "owner": owner_a,
        "projectId": project_a,
        "objectCount": len(third_paste["objects"]),
        "documentFingerprint": json.dumps(
            json.loads(persisted_a)["document"],
            ensure_ascii=False,
            separators=(",", ":"),
        ),
    }
    return browser_result, restore_expectation


def verify_reload_boundary(
    page: Page,
    expectation: dict,
) -> dict:
    page.goto(f"{BASE_URL}/?batch75=reload", wait_until="networkidle")
    page.wait_for_function(
        """() => Boolean(
          window.__director_store &&
          window.__director_project_registry_snapshot
        )"""
    )
    page.evaluate(
        """(owner) => window.__director_store.getState().openSession(owner)""",
        expectation["owner"],
    )
    page.wait_for_function(
        """(projectId) =>
          window.__director_store.getState().projectId === projectId""",
        arg=expectation["projectId"],
    )
    restored = director_state(page)
    assert restored["clipboard"] is None
    assert restored["clipboardPasteCount"] == 0
    assert len(restored["objects"]) == expectation["objectCount"]
    assert restored["documentFingerprint"] == expectation["documentFingerprint"]
    assert restored["captures"] == []
    return {
        "documentRestored": True,
        "clipboardRestored": False,
        "pasteCountRestored": False,
        "sessionCaptureRestored": False,
        "objectCount": len(restored["objects"]),
    }


def main() -> None:
    pure = run_pure_verifier()
    errors: list[str] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        context = browser.new_context(viewport={"width": 1440, "height": 1000})
        page = context.new_page()
        errors.extend(attach_errors(page))
        browser_result, restore_expectation = run_browser_verifier(page)
        reload_page = context.new_page()
        errors.extend(attach_errors(reload_page))
        browser_result["reloadBoundary"] = verify_reload_boundary(
            reload_page,
            restore_expectation,
        )
        assert errors == [], json.dumps(errors, ensure_ascii=False, indent=2)
        context.close()
        browser.close()

    audit = {
        "status": "PASS",
        "batch": 75,
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
