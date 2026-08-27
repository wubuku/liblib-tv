#!/usr/bin/env python3

"""Verify Batch 68 Director owner registry and session lifecycle."""

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
    / "liblib-canvas-batch68-2026-08-27"
    / "runtime-audit.json"
)


def run_pure_verifier() -> dict:
    completed = subprocess.run(
        [
            "node",
            "--disable-warning=MODULE_TYPELESS_PACKAGE_JSON",
            "--experimental-strip-types",
            "scripts/verify-liblib-batch68.mjs",
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
            sceneName: state.scene.name,
            captures: state.captures.map((capture) => ({
              id: capture.id,
              dataUrl: capture.dataUrl,
              sentNodeId: capture.sentNodeId || null,
            })),
            isPlaying: state.timeline.isPlaying,
            currentTime: state.timeline.currentTime,
            motionPathDraft: state.timeline.motionPathDraft,
            selectedObjectId: state.selectedObjectId,
            viewMode: state.viewMode,
            transformMode: state.transformMode,
            showThirds: state.showThirds,
            panelsCollapsed: state.viewportPanelsCollapsed,
            phoneStatus: state.phoneVcam.status,
          };
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
    workspace = page.locator("[data-director-workspace]")
    state = director_state(page)
    assert workspace.get_attribute("data-director-canvas-id") == canvas_id
    assert workspace.get_attribute("data-director-source-node-id") == node_id
    assert workspace.get_attribute("data-director-project-id") == state["projectId"]
    assert workspace.get_attribute("data-director-session-id") == state["sessionId"]
    assert workspace.get_attribute("data-director-generation") == str(
        state["generation"]
    )
    return state


def prepare_two_director_nodes(page: Page) -> dict:
    return page.evaluate(
        """() => {
          const store = window.__libtv_store.getState();
          const canvasId = store.activeCanvasId;
          const before = new Set(
            store.getActiveCanvas()?.nodes.map((node) => node.id) || [],
          );
          store.addNode("script-execution", { title: "Batch 68 A" });
          const afterA = store.getActiveCanvas()?.nodes || [];
          const nodeA = afterA.find((node) => !before.has(node.id))?.id;
          const beforeB = new Set(afterA.map((node) => node.id));
          store.addNode("script-execution", { title: "Batch 68 B" });
          const afterB = store.getActiveCanvas()?.nodes || [];
          const nodeB = afterB.find((node) => !beforeB.has(node.id))?.id;
          if (!nodeA || !nodeB) throw new Error("Director fixture creation failed");
          return { canvasId, nodeA, nodeB };
        }"""
    )


def run_browser_verifier(page: Page) -> dict:
    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/?batch68=1", wait_until="networkidle")
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

    state_a1 = open_owner(page, fixture["canvasId"], fixture["nodeA"])
    assert state_a1["sceneName"] == "第一集：咖啡馆对峙"
    page.evaluate(
        """() => {
          const state = window.__director_store.getState();
          state.updateScene({ name: "Batch 68 Scene A" });
          state.addCapture({
            id: "batch68-capture-a",
            dataUrl: "data:image/png;base64,QQ==",
            cameraId: state.activeCameraId,
            cameraName: "Batch 68 camera",
            aspectRatio: state.aspectRatio,
            width: 1280,
            height: 720,
            createdAt: "2026-08-27T11:00:00.000Z",
            sentNodeId: "batch68-graph-result-a",
          });
          state.setTimelineTime(2);
          state.startMotionPathDrawing("pencil");
          state.setTimelinePlaying(true);
          state.setViewMode("camera");
          state.setTransformMode("rotate");
          state.toggleThirds();
          state.setViewportPanelsCollapsed(true);
        }"""
    )
    edited_a = director_state(page)
    assert edited_a["sceneName"] == "Batch 68 Scene A"
    assert len(edited_a["captures"]) == 1
    assert edited_a["isPlaying"] is True

    state_b1 = open_owner(page, fixture["canvasId"], fixture["nodeB"])
    assert state_b1["projectId"] != state_a1["projectId"]
    assert state_b1["sceneName"] == "第一集：咖啡馆对峙"
    assert state_b1["captures"] == []
    assert state_b1["isPlaying"] is False
    assert state_b1["currentTime"] == 0
    assert state_b1["motionPathDraft"] is None
    assert state_b1["viewMode"] == "director"
    assert state_b1["transformMode"] == "translate"
    assert state_b1["showThirds"] is False
    assert state_b1["panelsCollapsed"] is False
    assert state_b1["phoneStatus"] == "idle"
    page.evaluate(
        """() =>
          window.__director_store.getState().updateScene({
            name: "Batch 68 Scene B",
          })"""
    )

    state_a2 = open_owner(page, fixture["canvasId"], fixture["nodeA"])
    assert state_a2["projectId"] == state_a1["projectId"]
    assert state_a2["sessionId"] != state_a1["sessionId"]
    assert state_a2["generation"] > state_a1["generation"]
    assert state_a2["sceneName"] == "Batch 68 Scene A"
    assert state_a2["captures"] == [
        {
            "id": "batch68-capture-a",
            "dataUrl": "data:image/png;base64,QQ==",
            "sentNodeId": "batch68-graph-result-a",
        }
    ]
    assert state_a2["isPlaying"] is False
    assert state_a2["currentTime"] == 0
    assert state_a2["motionPathDraft"] is None
    assert graph_state(page) == graph_after_fixture

    focus_result = page.evaluate(
        """({ canvasId, nodeId }) => {
          const store = window.__director_store.getState();
          const before = {
            projectId: store.projectId,
            sessionId: store.sessionId,
            generation: store.generation,
            sceneName: store.scene.name,
          };
          const result = store.openSession({
            route: "libtv",
            canvasId,
            sourceNodeId: nodeId,
          });
          const after = window.__director_store.getState();
          return {
            disposition: result.disposition,
            before,
            after: {
              projectId: after.projectId,
              sessionId: after.sessionId,
              generation: after.generation,
              sceneName: after.scene.name,
            },
          };
        }""",
        {"canvasId": fixture["canvasId"], "nodeId": fixture["nodeA"]},
    )
    assert focus_result["disposition"] == "FOCUSED"
    assert focus_result["before"] == focus_result["after"]

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
    closed_state = director_state(page)
    assert closed_state["projectId"] is None
    assert closed_state["sessionId"] is None
    state_a3 = open_owner(page, fixture["canvasId"], fixture["nodeA"])
    assert state_a3["projectId"] == state_a1["projectId"]
    assert state_a3["generation"] > state_a2["generation"]
    assert state_a3["sessionId"] != state_a2["sessionId"]
    assert state_a3["sceneName"] == "Batch 68 Scene A"

    cross_canvas = page.evaluate(
        """() => {
          const store = window.__libtv_store.getState();
          const before = new Set(store.canvases.map((canvas) => canvas.id));
          store.addCanvas("Batch 68 cross-canvas");
          const nextStore = window.__libtv_store.getState();
          const canvasId = nextStore.activeCanvasId;
          if (before.has(canvasId)) throw new Error("Canvas creation failed");
          const beforeNodes = new Set(
            nextStore.getActiveCanvas()?.nodes.map((node) => node.id) || [],
          );
          nextStore.addNode("script-execution", { title: "Batch 68 C" });
          const nodeId = window.__libtv_store
            .getState()
            .getActiveCanvas()
            ?.nodes.find((node) => !beforeNodes.has(node.id))?.id;
          if (!nodeId) throw new Error("Cross-canvas node creation failed");
          return { canvasId, nodeId };
        }"""
    )
    page.wait_for_function(
        "() => !document.querySelector('[data-director-workspace]')"
    )
    state_c = open_owner(
        page, cross_canvas["canvasId"], cross_canvas["nodeId"]
    )
    assert state_c["projectId"] != state_a1["projectId"]
    assert state_c["sceneName"] == "第一集：咖啡馆对峙"

    duplicate = page.evaluate(
        """({ canvasId, nodeId }) => {
          const store = window.__libtv_store.getState();
          store.setActiveCanvas(canvasId);
          const before = new Set(
            store.getActiveCanvas()?.nodes.map((node) => node.id) || [],
          );
          store.duplicateNode(nodeId, false);
          const copiedNodeId = store
            .getActiveCanvas()
            ?.nodes.find((node) => !before.has(node.id))?.id;
          if (!copiedNodeId) throw new Error("Director duplicate failed");
          return copiedNodeId;
        }""",
        {"canvasId": fixture["canvasId"], "nodeId": fixture["nodeA"]},
    )
    page.wait_for_function(
        "() => !document.querySelector('[data-director-workspace]')"
    )
    duplicate_state = open_owner(page, fixture["canvasId"], duplicate)
    assert duplicate_state["projectId"] != state_a1["projectId"]
    assert duplicate_state["sceneName"] == "第一集：咖啡馆对峙"
    assert duplicate_state["captures"] == []

    history_before_delete = graph_state(page)["pastLength"]
    page.evaluate(
        "(nodeId) => window.__libtv_store.getState().removeNode(nodeId)",
        duplicate,
    )
    page.wait_for_function(
        "() => !document.querySelector('[data-director-workspace]')"
    )
    deleted_state = director_state(page)
    assert deleted_state["projectId"] is None
    assert deleted_state["sessionId"] is None
    graph_after_delete = graph_state(page)
    assert graph_after_delete["pastLength"] == history_before_delete + 1
    registry_snapshot = page.evaluate(
        "() => window.__director_project_registry_snapshot()"
    )
    duplicate_record = next(
        record
        for record in registry_snapshot["records"]
        if record["identity"]["owner"]["canvasId"] == fixture["canvasId"]
        and record["identity"]["owner"]["sourceNodeId"] == duplicate
    )
    assert duplicate_record["lifecycle"] == "CLOSED"
    assert registry_snapshot["activeSession"] is None

    assert errors == [], json.dumps(errors, ensure_ascii=False, indent=2)
    return {
        "ownerIsolation": "pass",
        "sameOwnerFocus": "pass",
        "closeReopenGeneration": "pass",
        "crossCanvasIsolation": "pass",
        "duplicateResetPolicy": "pass",
        "activeDeleteClose": "pass",
        "memoryCaptureSidecar": "pass",
        "ordinaryGraphIsolation": "pass",
        "projectsObserved": len(registry_snapshot["records"]),
    }


def verify_static_contract() -> None:
    registry_source = (ROOT / "src/lib/directorProjectRegistry.ts").read_text()
    store_source = (ROOT / "src/store/directorStore.ts").read_text()
    desk_source = (
        ROOT / "src/components/director/DirectorDesk.tsx"
    ).read_text()
    page_source = (ROOT / "src/app/page.tsx").read_text()
    for label in [
        "createDirectorProjectOwnerKey",
        "DirectorProjectRegistry",
        "generation",
        "memory",
        "TOMBSTONED",
    ]:
        assert label in registry_source, label
    for label in [
        "projectOwner",
        "projectId",
        "sessionId",
        "closeSession",
        "restoreDirectorProjectState",
    ]:
        assert label in store_source, label
    for label in [
        "data-director-project-id",
        "data-director-session-id",
        "data-director-generation",
    ]:
        assert label in desk_source, label
    assert "useDirectorStore.getState().closeSession" in page_source


def main() -> None:
    verify_static_contract()
    pure_result = run_pure_verifier()
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(
            viewport={"width": 1440, "height": 900},
            device_scale_factor=1,
        )
        browser_result = run_browser_verifier(page)
        browser.close()

    audit = {
        "batch": 68,
        "status": "SCRIPT_RECORDED_PASS",
        "date": "2026-08-27",
        "contract": {
            "scope": "clone-owned Director owner registry and session lifecycle",
            "sourceExact": False,
            "browserPersistence": False,
            "authoredRuntimeSplit": False,
            "historyDelete": False,
        },
        "pure": pure_result,
        "browser": browser_result,
        "screenshots": [],
        "errors": {"console": [], "page": [], "request": []},
    }
    AUDIT_PATH.write_text(
        json.dumps(audit, ensure_ascii=False, indent=2) + "\n"
    )
    print(
        "Batch 68 verification passed: structured owner keys, project/session/"
        "generation lifecycle, A/B and cross-canvas isolation, memory capture "
        "sidecar, duplicate reset policy, active-delete close and ordinary graph "
        "isolation."
    )


if __name__ == "__main__":
    main()
