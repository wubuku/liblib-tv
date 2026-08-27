#!/usr/bin/env python3

"""Verify the Batch 72 Director reference-aware delete authority."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from playwright.sync_api import Page, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
BASE_URL = os.environ.get("LIBLIB_BASE_URL", "http://localhost:3000")
STORAGE_KEY = "liblib-tv-director-local-model-library-v1"
AUDIT_PATH = (
    ROOT
    / "docs"
    / "research"
    / "liblib-canvas-batch72-2026-08-27"
    / "runtime-audit.json"
)


def run_pure_verifier() -> dict:
    completed = subprocess.run(
        [
            "node",
            "--disable-warning=MODULE_TYPELESS_PACKAGE_JSON",
            "--experimental-strip-types",
            "scripts/verify-liblib-batch72.mjs",
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
          const registry = window.__director_project_registry_snapshot();
          const record = registry.records.find(
            (candidate) => candidate.identity.projectId === state.projectId,
          );
          const latest = state.history.past.at(-1) || null;
          return {
            projectId: state.projectId,
            activeCameraId: state.activeCameraId,
            objectIds: state.authoredObjects.map((object) => object.id),
            cameras: state.authoredObjects
              .filter((object) => object.kind === "camera")
              .map((object) => ({
                id: object.id,
                lookAtMode: object.camera?.lookAtMode ?? null,
                lookAtObjectId: object.camera?.lookAtObjectId ?? null,
                followTargetId: object.camera?.followTargetId ?? null,
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
              memberOffsetIds:
                track.kind === "group" ? Object.keys(track.memberOffsets) : [],
              motionPathId: track.motionPathId ?? null,
            })),
            pathIds: state.timeline.motionPaths.map((path) => path.id),
            captures: state.captures.map((capture) => ({
              id: capture.id,
              cameraId: capture.cameraId,
              sentNodeId: capture.sentNodeId ?? null,
            })),
            localAssetIds: state.localModelLibrary.map((item) => item.id),
            selectedObjectId: state.selectedObjectId,
            selectedObjectIds: state.selectedObjectIds,
            selectedGroupId: state.selectedGroupId,
            phone: {
              status: state.phoneVcam.status,
              importedCameraId: state.phoneVcam.importedCameraId,
              importedTrackId: state.phoneVcam.importedTrackId,
            },
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
                  resourceEffects: state.lastCommandResult.resourceEffects,
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


def open_director(
    page: Page,
    scenario: str,
    *,
    clear_local_storage: bool = False,
) -> tuple[dict, dict]:
    page.goto(f"{BASE_URL}/?batch72={scenario}", wait_until="networkidle")
    page.wait_for_function(
        """() => Boolean(
          window.__libtv_store &&
          window.__libtv_ui_store &&
          window.__director_store &&
          window.__director_project_registry_snapshot
        )"""
    )
    if clear_local_storage:
        page.evaluate(
            "(key) => localStorage.removeItem(key)",
            STORAGE_KEY,
        )
    fixture = page.evaluate(
        """(scenarioName) => {
          const store = window.__libtv_store.getState();
          const canvasId = store.activeCanvasId;
          const before = new Set(
            store.getActiveCanvas()?.nodes.map((node) => node.id) || [],
          );
          store.addNode("script-execution", {
            title: `Batch 72 ${scenarioName}`,
          });
          const nodes = store.getActiveCanvas()?.nodes || [];
          const nodeId = nodes.find((node) => !before.has(node.id))?.id;
          if (!nodeId) throw new Error("Batch 72 fixture creation failed");
          window.__libtv_ui_store.getState().openDirectorDesk(nodeId, canvasId);
          return { canvasId, nodeId };
        }""",
        scenario,
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
    page.wait_for_timeout(160)
    return fixture, graph_state(page)


def assert_graph_unchanged(page: Page, baseline: dict) -> None:
    assert graph_state(page) == baseline


def run_keyboard_delete(page: Page) -> dict:
    _, graph_baseline = open_director(page, "keyboard-delete")
    before = director_state(page)
    assert before["selectedObjectId"] == "director-character-lead"
    assert page.locator(
        '[data-director-delete-object="director-character-lead"]'
    ).count() == 1

    page.locator("[data-director-workspace]").focus()
    page.keyboard.press("Delete")
    page.wait_for_function(
        """() => !window.__director_store.getState().authoredObjects.some(
          (object) => object.id === "director-character-lead"
        )"""
    )
    deleted = director_state(page)
    assert deleted["history"]["past"] == before["history"]["past"] + 1
    assert deleted["lastCommand"] == {
        "commandKind": "DELETE_OBJECTS",
        "disposition": "COMMITTED",
        "reason": None,
        "historyEntries": 1,
        "resourceEffects": [],
    }
    assert deleted["documentFingerprint"] == deleted["latestHistory"]["after"]

    page.evaluate("() => window.__director_store.getState().undoDirector()")
    undone = director_state(page)
    assert "director-character-lead" in undone["objectIds"]
    assert undone["documentFingerprint"] == deleted["latestHistory"]["before"]
    assert undone["history"]["future"] == 1

    page.evaluate("() => window.__director_store.getState().redoDirector()")
    redone = director_state(page)
    assert "director-character-lead" not in redone["objectIds"]
    assert redone["documentFingerprint"] == deleted["latestHistory"]["after"]
    assert_graph_unchanged(page, graph_baseline)
    return {
        "historyDelta": 1,
        "undoRedo": "exact-document",
        "keyboard": "Delete",
    }


def run_last_camera_rejection(page: Page) -> dict:
    _, graph_baseline = open_director(page, "last-camera")
    before = director_state(page)
    page.locator(
        '[data-director-delete-object="director-camera-main"]'
    ).click()
    page.wait_for_timeout(80)
    after = director_state(page)
    assert after["objectIds"] == before["objectIds"]
    assert after["activeCameraId"] == "director-camera-main"
    assert after["history"] == before["history"]
    assert after["lastCommand"] == {
        "commandKind": "DELETE_OBJECT",
        "disposition": "REJECTED",
        "reason": "DIRECTOR_LAST_CAMERA_REQUIRED",
        "historyEntries": 0,
        "resourceEffects": [],
    }
    assert after["documentFingerprint"] == before["documentFingerprint"]
    assert_graph_unchanged(page, graph_baseline)
    return {
        "historyDelta": 0,
        "reason": "DIRECTOR_LAST_CAMERA_REQUIRED",
        "partialMutation": False,
    }


def run_reference_closure(page: Page) -> dict:
    _, _ = open_director(page, "reference-closure")
    fixture = page.evaluate(
        """() => {
          const store = window.__director_store.getState();
          const groupId = store.addCrowdArray({
            rows: 1,
            columns: 2,
            spacing: 1,
          });
          if (!groupId) throw new Error("Batch 72 crowd group missing");
          store.selectGroup(groupId);
          store.addTimelineTrack();
          const group = window.__director_store
            .getState()
            .groups.find((item) => item.id === groupId);
          const memberId = group?.characterIds[0];
          if (!memberId) throw new Error("Batch 72 group member missing");
          store.selectObject(memberId);
          store.addTimelineTrack(memberId);
          const memberTrack = window.__director_store
            .getState()
            .timeline.tracks.find(
              (track) =>
                track.objectId === memberId && track.kind === "transform",
            );
          if (!memberTrack) throw new Error("Batch 72 member track missing");
          store.createMotionPath("line", memberTrack.id);
          const pathId = window.__director_store
            .getState()
            .timeline.tracks.find(
              (track) => track.id === memberTrack.id,
            )?.motionPathId;
          store.updateCamera("director-camera-main", {
            lookAtMode: "object",
            lookAtObjectId: memberId,
            followTargetId: memberId,
          });
          return { groupId, memberId, trackId: memberTrack.id, pathId };
        }"""
    )
    page.wait_for_timeout(80)
    graph_baseline = graph_state(page)
    before = director_state(page)
    page.locator("[data-director-workspace]").focus()
    page.keyboard.press("Delete")
    page.wait_for_function(
        """(memberId) =>
          !window.__director_store.getState().authoredObjects.some(
            (object) => object.id === memberId
          )""",
        arg=fixture["memberId"],
    )
    after = director_state(page)
    group = next(item for item in after["groups"] if item["id"] == fixture["groupId"])
    assert fixture["memberId"] not in group["characterIds"]
    group_track = next(
        track
        for track in after["tracks"]
        if track["kind"] == "group" and track["groupId"] == fixture["groupId"]
    )
    assert group_track["memberOffsetIds"] == group["characterIds"]
    assert fixture["trackId"] not in {track["id"] for track in after["tracks"]}
    assert fixture["pathId"] not in after["pathIds"]
    camera = next(item for item in after["cameras"] if item["id"] == "director-camera-main")
    assert camera["lookAtMode"] == "coordinate"
    assert camera["lookAtObjectId"] is None
    assert camera["followTargetId"] is None
    assert fixture["memberId"] not in after["selectedObjectIds"]
    assert after["history"]["past"] == before["history"]["past"] + 1
    assert after["documentFingerprint"] == after["latestHistory"]["after"]

    page.evaluate("() => window.__director_store.getState().undoDirector()")
    undone = director_state(page)
    assert undone["documentFingerprint"] == after["latestHistory"]["before"]
    page.evaluate("() => window.__director_store.getState().redoDirector()")
    redone = director_state(page)
    assert redone["documentFingerprint"] == after["latestHistory"]["after"]
    assert_graph_unchanged(page, graph_baseline)
    return {
        "historyDelta": 1,
        "groupRepair": "member-offsets",
        "cameraRepair": "coordinate-detach",
        "trackPathClosure": "pass",
    }


def run_camera_capture_graph(page: Page) -> dict:
    fixture, _ = open_director(page, "camera-capture")
    setup = page.evaluate(
        """({ sourceNodeId }) => {
          const store = window.__director_store.getState();
          if (!store.connectPhoneVcamLocal()) {
            throw new Error("Batch 72 phone vcam connect failed");
          }
          if (!store.startPhoneVcamRecording()) {
            throw new Error("Batch 72 phone vcam recording failed");
          }
          const current = window.__director_store.getState();
          const baseline = current.phoneVcam.baselineCamera;
          if (!baseline) throw new Error("Batch 72 camera baseline missing");
          const imported = current.importPhoneVcamTake([
            { time: 0, value: baseline },
            {
              time: 1,
              value: {
                transform: {
                  ...baseline.transform,
                  position: [
                    baseline.transform.position[0] + 0.4,
                    baseline.transform.position[1],
                    baseline.transform.position[2],
                  ],
                },
                target: baseline.target,
                fov: baseline.fov,
              },
            },
          ]);
          if (!imported) throw new Error("Batch 72 camera import failed");
          const capture = {
            id: "batch72-capture",
            dataUrl:
              "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJ" +
              "AAAADUlEQVR42mNk+M/wHwAF/gL+XQ2mWQAAAABJRU5ErkJggg==",
            cameraId: imported.cameraId,
            cameraName: "Batch 72 camera",
            aspectRatio: "16:9",
            width: 1280,
            height: 720,
            createdAt: "2026-08-27T18:00:00.000Z",
          };
          current.addCapture(capture);
          const graphNodeId = window.__libtv_store.getState().createDirectorCapture(
            sourceNodeId,
            capture,
          );
          if (!graphNodeId) {
            throw new Error("Batch 72 capture graph projection failed");
          }
          current.markCaptureSent(capture.id, graphNodeId);
          return {
            cameraId: imported.cameraId,
            trackId: imported.trackId,
            captureId: capture.id,
            graphNodeId,
          };
        }""",
        {"sourceNodeId": fixture["nodeId"]},
    )
    page.wait_for_timeout(100)
    graph_baseline = graph_state(page)
    before = director_state(page)
    assert before["activeCameraId"] == setup["cameraId"]

    page.evaluate(
        """(cameraId) => window.__director_store.getState().deleteDirectorEntity({
          kind: "DELETE_OBJECT",
          objectId: cameraId,
        })""",
        setup["cameraId"],
    )
    after_camera_delete = director_state(page)
    assert after_camera_delete["activeCameraId"] == "director-camera-main"
    assert setup["cameraId"] not in after_camera_delete["objectIds"]
    capture = next(
        item
        for item in after_camera_delete["captures"]
        if item["id"] == setup["captureId"]
    )
    assert capture["cameraId"] is None
    assert capture["sentNodeId"] == setup["graphNodeId"]
    assert after_camera_delete["phone"] == {
        "status": "idle",
        "importedCameraId": None,
        "importedTrackId": None,
    }
    assert after_camera_delete["history"]["past"] == before["history"]["past"] + 1
    assert_graph_unchanged(page, graph_baseline)

    page.evaluate(
        "(captureId) => window.__director_store.getState().removeCapture(captureId)",
        setup["captureId"],
    )
    after_capture_delete = director_state(page)
    assert after_capture_delete["captures"] == []
    assert (
        after_capture_delete["history"]["past"]
        == after_camera_delete["history"]["past"] + 1
    )
    assert_graph_unchanged(page, graph_baseline)
    return {
        "cameraHistoryDelta": 1,
        "captureHistoryDelta": 1,
        "fallbackCamera": "director-camera-main",
        "graphNodePreserved": "ordinary-canvas-result-node",
    }


def run_local_resource(page: Page) -> dict:
    _, _ = open_director(
        page,
        "local-resource",
        clear_local_storage=True,
    )
    fixture = page.evaluate(
        """() => {
          const store = window.__director_store.getState();
          const item = {
            id: "batch72-local-resource",
            categoryId: "my-models",
            name: "Batch 72 local model",
            fileName: "batch72.glb",
            dataUrl: "data:model/gltf-binary;base64,QkFUQ0g3Mg==",
            visual: "chair",
            color: "#8296a8",
          };
          store.addLocalModelLibraryItem(item);
          const objectId = store.addModelLibraryObject(item);
          store.addTimelineTrack(objectId);
          const track = window.__director_store
            .getState()
            .timeline.tracks.find(
              (candidate) =>
                candidate.objectId === objectId &&
                candidate.kind === "transform",
            );
          if (!track) throw new Error("Batch 72 local track missing");
          store.createMotionPath("line", track.id);
          const pathId = window.__director_store
            .getState()
            .timeline.tracks.find(
              (candidate) => candidate.id === track.id,
            )?.motionPathId;
          return { assetId: item.id, objectId, trackId: track.id, pathId };
        }"""
    )
    page.wait_for_timeout(80)
    graph_baseline = graph_state(page)
    before = director_state(page)
    page.evaluate(
        "(assetId) => window.__director_store.getState().removeLocalModelLibraryItem(assetId)",
        fixture["assetId"],
    )
    blocked = director_state(page)
    assert blocked["objectIds"] == before["objectIds"]
    assert blocked["localAssetIds"] == before["localAssetIds"]
    assert blocked["history"] == before["history"]
    assert blocked["lastCommand"]["disposition"] == "REJECTED"
    assert blocked["lastCommand"]["reason"] == "DIRECTOR_RESOURCE_IN_USE"

    page.evaluate(
        """(assetId) =>
          window.__director_store
            .getState()
            .removeLocalModelLibraryItem(assetId, "CASCADE")""",
        fixture["assetId"],
    )
    cascaded = director_state(page)
    assert fixture["objectId"] not in cascaded["objectIds"]
    assert fixture["trackId"] not in {track["id"] for track in cascaded["tracks"]}
    assert fixture["pathId"] not in cascaded["pathIds"]
    assert fixture["assetId"] not in cascaded["localAssetIds"]
    assert cascaded["history"]["past"] == before["history"]["past"] + 1
    assert cascaded["lastCommand"]["resourceEffects"] == [
        {
            "kind": "descriptor-deleted",
            "resourceId": fixture["assetId"],
        }
    ]
    persisted = page.evaluate(
        "(key) => JSON.parse(localStorage.getItem(key) || '[]')",
        STORAGE_KEY,
    )
    assert all(item["id"] != fixture["assetId"] for item in persisted)
    assert_graph_unchanged(page, graph_baseline)
    return {
        "blockReason": "DIRECTOR_RESOURCE_IN_USE",
        "cascadeHistoryDelta": 1,
        "storageDescriptorRemoved": True,
    }


def run_browser_verifier() -> dict:
    scenarios = [
        ("keyboardDelete", run_keyboard_delete),
        ("lastCameraRejection", run_last_camera_rejection),
        ("referenceClosure", run_reference_closure),
        ("cameraCaptureGraph", run_camera_capture_graph),
        ("localResource", run_local_resource),
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
        "batch": 72,
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
