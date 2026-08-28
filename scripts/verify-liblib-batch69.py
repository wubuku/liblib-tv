#!/usr/bin/env python3

"""Verify the Batch 69 Director authored/runtime projection boundary."""

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
    / "liblib-canvas-batch69-2026-08-27"
    / "runtime-audit.json"
)


def run_pure_verifier() -> dict:
    completed = subprocess.run(
        [
            "node",
            "--disable-warning=MODULE_TYPELESS_PACKAGE_JSON",
            "--experimental-strip-types",
            "scripts/verify-liblib-batch69.mjs",
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
            owner: state.projectOwner,
            projectId: state.projectId,
            sessionId: state.sessionId,
            generation: state.generation,
            lifecycle: state.projectLifecycle,
            authoredFingerprint: JSON.stringify(state.authoredObjects),
            authoredObjects: state.authoredObjects.map((object) => ({
              id: object.id,
              kind: object.kind,
              position: object.transform.position,
              rotation: object.transform.rotation,
              scale: object.transform.scale,
              fov: object.camera?.fov ?? null,
              target: object.camera?.target ?? null,
              pose: object.characterRig ?? null,
            })),
            runtimeFingerprint: JSON.stringify(state.objects),
            runtimeObjects: state.objects.map((object) => ({
              id: object.id,
              position: object.transform.position,
              rotation: object.transform.rotation,
              scale: object.transform.scale,
              fov: object.camera?.fov ?? null,
              target: object.camera?.target ?? null,
              pose: object.characterRig ?? null,
            })),
            timeline: {
              currentTime: state.timeline.currentTime,
              isPlaying: state.timeline.isPlaying,
              tracks: state.timeline.tracks.map((track) => ({
                id: track.id,
                kind: track.kind,
                keyframes: track.keyframes.length,
                motionPathId: track.motionPathId || null,
              })),
              motionPaths: state.timeline.motionPaths.map((path) => ({
                id: path.id,
                anchors: path.anchors.length,
                enabled: path.enabled,
              })),
            },
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
          store.addNode("script-execution", { title: "Batch 69 A" });
          const afterA = store.getActiveCanvas()?.nodes || [];
          const nodeA = afterA.find((node) => !before.has(node.id))?.id;
          const beforeB = new Set(afterA.map((node) => node.id));
          store.addNode("script-execution", { title: "Batch 69 B" });
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
            typeof state.projectId === "string" &&
            typeof state.sessionId === "string"
          );
        }""",
        arg={"canvasId": canvas_id, "nodeId": node_id},
    )
    page.locator("[data-director-workspace]").wait_for(state="visible")
    return director_state(page)


def run_browser_verifier(page: Page) -> dict:
    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/?batch69=1", wait_until="networkidle")
    page.wait_for_function(
        """() =>
          Boolean(
            window.__libtv_store &&
            window.__libtv_ui_store &&
            window.__director_store &&
            window.__director_project_registry_snapshot
          )"""
    )
    fixture = prepare_two_director_nodes(page)
    graph_after_fixture = graph_state(page)

    initial = open_owner(page, fixture["canvasId"], fixture["nodeA"])
    authored_baseline = initial["authoredFingerprint"]
    initial_character = next(
        item for item in initial["authoredObjects"] if item["kind"] == "character"
    )
    initial_camera = next(
        item for item in initial["authoredObjects"] if item["kind"] == "camera"
    )
    transform_track = next(
        track
        for track in initial["timeline"]["tracks"]
        if track["kind"] == "transform"
    )
    camera_track = next(
        track
        for track in initial["timeline"]["tracks"]
        if track["kind"] == "camera"
    )

    page.evaluate(
        """({ transformTrackId, cameraTrackId, characterId }) => {
          const state = window.__director_store.getState();
          state.setTimelineTime(2);
          state.setTimelineTime(6);
          state.selectTimelineKeyframe(
            transformTrackId,
            state.timeline.tracks
              .find((track) => track.id === transformTrackId)
              .keyframes[1].id,
          );
          state.seekTimelineKeyframe(1);
          state.setTrackSpeedCurvePreset(transformTrackId, "ease-in-out");
          state.setTrackSpeedCurveControl(transformTrackId, 1, [0.22, 0.08]);
          state.createMotionPath("line", transformTrackId);
          const path = window.__director_store.getState().timeline.motionPaths.at(-1);
          if (!path) throw new Error("Motion path was not created");
          state.updateMotionPathAnchorPosition(
            path.id,
            path.anchors[0].id,
            [0.8, 0, -0.2],
          );
          state.toggleMotionPathEnabled(path.id);
          state.toggleMotionPathOrient(path.id);
          state.applyCameraMotionPreset("orbit", "replace", cameraTrackId);
          state.setTimelineTime(3);
          state.setTimelinePlaying(true);
          state.advanceTimeline(1.25);
          state.setTimelinePlaying(false);
          state.selectObject(characterId);
        }""",
        {
            "transformTrackId": transform_track["id"],
            "cameraTrackId": camera_track["id"],
            "characterId": initial_character["id"],
        },
    )
    sampled = director_state(page)
    assert sampled["authoredFingerprint"] == authored_baseline
    assert sampled["runtimeFingerprint"] != authored_baseline

    page.evaluate(
        """({ characterId, cameraId }) => {
          const state = window.__director_store.getState();
          state.setTimelineTime(3);
          state.updateObjectTransform(characterId, "position", 0, 1.75);
          state.updateCamera(cameraId, {
            fov: 61,
            target: [0.4, 1.1, 0.2],
          });
          state.updateCharacterPoseControl(characterId, "head.yaw", 18);
        }""",
        {
            "characterId": initial_character["id"],
            "cameraId": initial_camera["id"],
        },
    )
    edited = director_state(page)
    assert edited["authoredFingerprint"] != authored_baseline
    edited_authored_fingerprint = edited["authoredFingerprint"]
    edited_character = next(
        item
        for item in edited["authoredObjects"]
        if item["id"] == initial_character["id"]
    )
    edited_camera = next(
        item
        for item in edited["authoredObjects"]
        if item["id"] == initial_camera["id"]
    )
    assert edited_character["position"][0] == 1.75
    assert edited_character["pose"]["controls"]["head.yaw"] == 18
    assert edited_camera["fov"] == 61

    close_result = page.evaluate(
        """({ canvasId, nodeId }) => {
          const result = window.__director_store.getState().closeSession({
            route: "libtv",
            canvasId,
            sourceNodeId: nodeId,
          });
          window.__libtv_ui_store.getState().closeDirectorDesk();
          return result.disposition;
        }""",
        {"canvasId": fixture["canvasId"], "nodeId": fixture["nodeA"]},
    )
    assert close_result == "CLOSED"
    page.locator("[data-director-workspace]").wait_for(state="hidden")

    restored = open_owner(page, fixture["canvasId"], fixture["nodeA"])
    assert restored["authoredFingerprint"] == edited_authored_fingerprint
    assert restored["timeline"]["currentTime"] == 0

    state_b = open_owner(page, fixture["canvasId"], fixture["nodeB"])
    assert state_b["projectId"] != restored["projectId"]
    assert state_b["authoredFingerprint"] != restored["authoredFingerprint"]
    state_b_authored = state_b["authoredFingerprint"]
    page.evaluate(
        "() => window.__director_store.getState().setTimelineTime(5)"
    )
    state_b_sampled = director_state(page)
    assert state_b_sampled["authoredFingerprint"] == state_b_authored

    state_a_again = open_owner(page, fixture["canvasId"], fixture["nodeA"])
    assert state_a_again["projectId"] == restored["projectId"]
    assert state_a_again["authoredFingerprint"] == edited_authored_fingerprint
    assert graph_state(page) == graph_after_fixture
    assert errors == [], json.dumps(errors, ensure_ascii=False, indent=2)

    return {
        "seekPlaybackPathProjection": "pass",
        "authoredFingerprintStableDuringSampling": "pass",
        "objectCameraPoseAuthoring": "pass",
        "closeReopenAuthoredRestore": "pass",
        "ownerIsolation": "pass",
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
        "batch": 69,
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
