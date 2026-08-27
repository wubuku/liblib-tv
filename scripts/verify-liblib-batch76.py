#!/usr/bin/env python3

"""Verify Batch 76 Director owner reachability reconciliation."""

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
    / "liblib-canvas-batch76-2026-08-27"
    / "runtime-audit.json"
)


def run_pure_verifier() -> dict:
    completed = subprocess.run(
        [
            "node",
            "--disable-warning=MODULE_TYPELESS_PACKAGE_JSON",
            "--experimental-strip-types",
            "scripts/verify-liblib-batch76.mjs",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    result = json.loads(completed.stdout)
    assert result["status"] == "PASS"
    return result


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


def owner_key(owner: dict) -> str:
    return json.dumps(
        [owner["route"], owner["canvasId"], owner["sourceNodeId"]],
        separators=(",", ":"),
    )


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
            canvasIds: state.canvases.map((item) => item.id),
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
            isCapturing: state.isCapturing,
            captureCount: state.captures.length,
            activeCaptureId: state.activeCaptureId,
            isPlaying: state.timeline.isPlaying,
            motionPathDraft: Boolean(state.timeline.motionPathDraft),
            activeGesture: Boolean(state.history.activeGesture),
            historyPast: state.history.past.length,
            historyFuture: state.history.future.length,
            clipboard: Boolean(state.clipboard),
            clipboardPasteCount: state.clipboardPasteCount,
            phoneStatus: state.phoneVcam.status,
            lastCommand: state.lastCommandResult
              ? {
                  commandKind: state.lastCommandResult.commandKind,
                  disposition: state.lastCommandResult.disposition,
                  reason: state.lastCommandResult.reason,
                }
              : null,
          };
        }"""
    )


def registry_snapshot(page: Page) -> dict:
    return page.evaluate(
        "() => window.__director_project_registry_snapshot()"
    )


def storage_entries(page: Page) -> dict[str, str]:
    return page.evaluate(
        """() => Object.fromEntries(
          Object.keys(localStorage)
            .filter((key) => key.startsWith("liblib-tv-director-project-v1:"))
            .map((key) => [key, localStorage.getItem(key) || ""])
        )"""
    )


def record_for_owner(snapshot: dict, owner: dict) -> dict:
    expected = owner_key(owner)
    return next(
        record
        for record in snapshot["records"]
        if owner_key(record["identity"]["owner"]) == expected
    )


def open_owner(page: Page, owner: dict) -> dict:
    current_owner = page.evaluate(
        """() => {
          const ui = window.__libtv_ui_store.getState();
          return ui.activeDirectorNodeId
            ? {
                canvasId: ui.activeDirectorCanvasId,
                sourceNodeId: ui.activeDirectorNodeId,
              }
            : null;
        }"""
    )
    if current_owner and (
        current_owner["canvasId"] != owner["canvasId"]
        or current_owner["sourceNodeId"] != owner["sourceNodeId"]
    ):
        page.evaluate(
            """() => {
              window.__director_store.getState().closeSession();
              window.__libtv_ui_store.getState().closeDirectorDesk();
            }"""
        )
        page.locator("[data-director-workspace]").wait_for(state="hidden")
        page.evaluate(
            """() => new Promise((resolve) =>
              requestAnimationFrame(() => requestAnimationFrame(resolve))
            )"""
        )
    page.evaluate(
        """(owner) => {
          window.__libtv_store.getState().setActiveCanvas(owner.canvasId);
        }""",
        owner,
    )
    page.wait_for_function(
        "(canvasId) => window.__libtv_store.getState().activeCanvasId === canvasId",
        arg=owner["canvasId"],
    )
    page.evaluate(
        """(owner) => {
          window.__libtv_ui_store
            .getState()
            .openDirectorDesk(owner.sourceNodeId, owner.canvasId);
        }""",
        owner,
    )
    page.wait_for_function(
        """(owner) => {
          const state = window.__director_store.getState();
          return (
            state.projectOwner?.canvasId === owner.canvasId &&
            state.projectOwner?.sourceNodeId === owner.sourceNodeId &&
            typeof state.projectId === "string" &&
            typeof state.sessionId === "string"
          );
        }""",
        arg=owner,
    )
    page.locator("[data-director-workspace]").wait_for(state="visible")
    return director_state(page)


def prepare_fixture(page: Page) -> dict:
    return page.evaluate(
        """() => {
          const store = window.__libtv_store.getState();
          const canvasA = store.activeCanvasId;
          const addNode = (title) => {
            const before = new Set(
              store.getActiveCanvas()?.nodes.map((node) => node.id) || [],
            );
            store.addNode("script-execution", { title });
            const created = window.__libtv_store
              .getState()
              .getActiveCanvas()
              ?.nodes.find((node) => !before.has(node.id));
            if (!created) throw new Error(`Failed to create ${title}`);
            return created.id;
          };
          const nodeA = addNode("Batch 76 active owner A");
          const nodeB = addNode("Batch 76 inactive owner B");
          const unrelatedNode = addNode("Batch 76 unrelated node");

          const beforeCanvases = new Set(store.canvases.map((canvas) => canvas.id));
          store.addCanvas("Batch 76 cross canvas");
          const canvasB = window.__libtv_store.getState().activeCanvasId;
          if (beforeCanvases.has(canvasB)) {
            throw new Error("Failed to create Batch 76 canvas B");
          }
          const nodeC = addNode("Batch 76 cross-canvas owner C");
          window.__libtv_store.getState().setActiveCanvas(canvasA);
          return {
            canvasA,
            canvasB,
            ownerA: { route: "libtv", canvasId: canvasA, sourceNodeId: nodeA },
            ownerB: { route: "libtv", canvasId: canvasA, sourceNodeId: nodeB },
            ownerC: { route: "libtv", canvasId: canvasB, sourceNodeId: nodeC },
            unrelatedNode,
          };
        }"""
    )


def wait_for_tombstone(page: Page, owner: dict) -> None:
    page.wait_for_function(
        """(owner) => {
          const record = window.__director_project_registry_snapshot().records.find(
            (candidate) =>
              candidate.identity.owner.canvasId === owner.canvasId &&
              candidate.identity.owner.sourceNodeId === owner.sourceNodeId,
          );
          return record?.lifecycle === "TOMBSTONED";
        }""",
        arg=owner,
    )


def run_browser_verifier(page: Page) -> dict:
    errors, phase = attach_errors(page)
    page.goto(f"{BASE_URL}/?batch76=1", wait_until="networkidle")
    page.wait_for_function(
        """() =>
          Boolean(
            window.__libtv_store &&
            window.__libtv_ui_store &&
            window.__director_store &&
            window.__director_project_registry_snapshot &&
            window.__director_project_persistence_snapshot
          )"""
    )
    fixture = prepare_fixture(page)

    phase[0] = "open-owner-b"
    state_b = open_owner(page, fixture["ownerB"])
    page.evaluate(
        "() => window.__director_store.getState().updateScene({ name: 'Batch 76 B' })"
    )
    phase[0] = "open-owner-c"
    state_c = open_owner(page, fixture["ownerC"])
    page.evaluate(
        "() => window.__director_store.getState().updateScene({ name: 'Batch 76 C' })"
    )
    phase[0] = "open-owner-a"
    state_a = open_owner(page, fixture["ownerA"])
    phase[0] = "prepare-active-runtime"
    page.evaluate(
        """() => {
          const state = window.__director_store.getState();
          state.updateScene({ name: "Batch 76 A" });
          state.copyDirectorSelection();
          state.addCapture({
            id: "batch76-capture-a",
            dataUrl: "data:image/png;base64,QQ==",
            cameraId: state.activeCameraId,
            cameraName: "Batch 76 camera",
            aspectRatio: state.aspectRatio,
            width: 1280,
            height: 720,
            createdAt: "2026-08-27T13:00:00.000Z",
          });
          state.selectCapture("batch76-capture-a");
          state.setCapturing(true);
          state.setTimelinePlaying(true);
          state.startMotionPathDrawing("pencil");
          state.beginDirectorGesture({
            commandKind: "BATCH76_ACTIVE_GESTURE",
            targetId: state.selectedObjectId,
          });
          state.connectPhoneVcamLocal();
          state.startPhoneVcamRecording();
        }"""
    )
    active_runtime = director_state(page)
    assert active_runtime["clipboard"] is True
    assert active_runtime["captureCount"] == 1
    assert active_runtime["activeGesture"] is True
    assert active_runtime["phoneStatus"] == "recording"

    registry_before = registry_snapshot(page)
    assert record_for_owner(registry_before, fixture["ownerA"])["lifecycle"] == "ACTIVE"
    assert record_for_owner(registry_before, fixture["ownerB"])["lifecycle"] == "CLOSED"
    assert record_for_owner(registry_before, fixture["ownerC"])["lifecycle"] == "CLOSED"
    storage_before = storage_entries(page)
    assert len(storage_before) >= 3

    phase[0] = "rename-canvases"
    page.evaluate(
        """({ canvasA, canvasB }) => {
          const store = window.__libtv_store.getState();
          store.renameCanvas(canvasA, "Batch 76 renamed A");
          store.renameCanvas(canvasB, "Batch 76 renamed B");
        }""",
        {"canvasA": fixture["canvasA"], "canvasB": fixture["canvasB"]},
    )
    registry_after_rename = registry_snapshot(page)
    assert record_for_owner(
        registry_after_rename, fixture["ownerA"]
    )["lifecycle"] == "ACTIVE"
    assert record_for_owner(
        registry_after_rename, fixture["ownerB"]
    )["lifecycle"] == "CLOSED"
    assert record_for_owner(
        registry_after_rename, fixture["ownerC"]
    )["lifecycle"] == "CLOSED"

    graph_before_b_delete = graph_state(page)
    generation_b_before = record_for_owner(
        registry_after_rename, fixture["ownerB"]
    )["identity"]["generation"]
    phase[0] = "delete-inactive-owner-b"
    page.evaluate(
        "(nodeId) => window.__libtv_store.getState().removeNode(nodeId)",
        fixture["ownerB"]["sourceNodeId"],
    )
    wait_for_tombstone(page, fixture["ownerB"])
    graph_after_b_delete = graph_state(page)
    assert graph_after_b_delete["pastLength"] == graph_before_b_delete["pastLength"] + 1
    assert page.locator("[data-director-workspace]").is_visible()
    state_after_b_delete = director_state(page)
    assert state_after_b_delete["projectId"] == state_a["projectId"]
    registry_after_b_delete = registry_snapshot(page)
    record_b = record_for_owner(registry_after_b_delete, fixture["ownerB"])
    assert record_b["identity"]["generation"] == generation_b_before + 1
    assert record_for_owner(
        registry_after_b_delete, fixture["ownerA"]
    )["lifecycle"] == "ACTIVE"

    phase[0] = "repeat-after-b"
    repeated_b = page.evaluate(
        """() => {
          const graph = window.__libtv_store.getState().canvases;
          const liveOwners = graph.flatMap((canvas) =>
            canvas.nodes.map((node) => ({
              route: "libtv",
              canvasId: canvas.id,
              sourceNodeId: node.id,
            })),
          );
          return window.__director_store
            .getState()
            .reconcileProjectOwners(liveOwners);
        }"""
    )
    assert repeated_b["tombstoneOwnerKeys"] == []
    assert repeated_b["appliedTombstoneOwnerKeys"] == []
    assert record_for_owner(
        registry_snapshot(page), fixture["ownerB"]
    )["identity"]["generation"] == record_b["identity"]["generation"]

    phase[0] = "delete-inactive-canvas"
    page.evaluate(
        "(canvasId) => window.__libtv_store.getState().removeCanvas(canvasId)",
        fixture["canvasB"],
    )
    wait_for_tombstone(page, fixture["ownerC"])
    registry_after_canvas_delete = registry_snapshot(page)
    assert record_for_owner(
        registry_after_canvas_delete, fixture["ownerC"]
    )["lifecycle"] == "TOMBSTONED"
    assert record_for_owner(
        registry_after_canvas_delete, fixture["ownerA"]
    )["lifecycle"] == "ACTIVE"
    assert fixture["canvasB"] not in graph_state(page)["canvasIds"]
    assert director_state(page)["projectId"] == state_a["projectId"]

    registry_before_unrelated = registry_snapshot(page)
    graph_before_unrelated = graph_state(page)
    phase[0] = "delete-unrelated-node"
    page.evaluate(
        "(nodeId) => window.__libtv_store.getState().removeNode(nodeId)",
        fixture["unrelatedNode"],
    )
    page.wait_for_function(
        "(nodeId) => !window.__libtv_store.getState().getActiveCanvas()?.nodes.some((node) => node.id === nodeId)",
        arg=fixture["unrelatedNode"],
    )
    graph_after_unrelated = graph_state(page)
    assert graph_after_unrelated["pastLength"] == graph_before_unrelated["pastLength"] + 1
    assert registry_snapshot(page) == registry_before_unrelated

    graph_before_a_delete = graph_state(page)
    generation_a_before = record_for_owner(
        registry_snapshot(page), fixture["ownerA"]
    )["identity"]["generation"]
    phase[0] = "delete-active-owner-a"
    page.evaluate(
        "(nodeId) => window.__libtv_store.getState().removeNode(nodeId)",
        fixture["ownerA"]["sourceNodeId"],
    )
    wait_for_tombstone(page, fixture["ownerA"])
    page.wait_for_function(
        """() =>
          window.__libtv_ui_store.getState().activeDirectorNodeId === null &&
          window.__director_store.getState().projectId === null"""
    )
    page.locator("[data-director-workspace]").wait_for(state="hidden")
    graph_after_a_delete = graph_state(page)
    assert graph_after_a_delete["pastLength"] == graph_before_a_delete["pastLength"] + 1
    record_a = record_for_owner(registry_snapshot(page), fixture["ownerA"])
    assert record_a["identity"]["generation"] == generation_a_before + 1

    cleared = director_state(page)
    assert cleared == {
        "owner": None,
        "projectId": None,
        "sessionId": None,
        "generation": None,
        "lifecycle": None,
        "sceneName": "第一集：咖啡馆对峙",
        "isCapturing": False,
        "captureCount": 0,
        "activeCaptureId": None,
        "isPlaying": False,
        "motionPathDraft": False,
        "activeGesture": False,
        "historyPast": 0,
        "historyFuture": 0,
        "clipboard": False,
        "clipboardPasteCount": 0,
        "phoneStatus": "idle",
        "lastCommand": None,
    }

    rejected_open = page.evaluate(
        "(owner) => window.__director_store.getState().openSession(owner)",
        fixture["ownerA"],
    )
    assert rejected_open["disposition"] == "REJECTED"
    assert rejected_open["reason"] == "PROJECT_TOMBSTONED"

    storage_after_delete = storage_entries(page)
    assert set(storage_after_delete) == set(storage_before)
    for owner in [fixture["ownerA"], fixture["ownerB"], fixture["ownerC"]]:
        assert any(
            owner["sourceNodeId"] in serialized
            for serialized in storage_after_delete.values()
        )

    phase[0] = "undo-active-owner-delete"
    page.evaluate("() => window.__libtv_store.getState().undo()")
    page.wait_for_function(
        "(nodeId) => window.__libtv_store.getState().getActiveCanvas()?.nodes.some((node) => node.id === nodeId)",
        arg=fixture["ownerA"]["sourceNodeId"],
    )
    assert record_for_owner(
        registry_snapshot(page), fixture["ownerA"]
    )["lifecycle"] == "TOMBSTONED"
    rejected_after_undo = page.evaluate(
        "(owner) => window.__director_store.getState().openSession(owner)",
        fixture["ownerA"],
    )
    assert rejected_after_undo["reason"] == "PROJECT_TOMBSTONED"

    phase[0] = "final-reconcile"
    final_reconcile = page.evaluate(
        """() => {
          const liveOwners = window.__libtv_store
            .getState()
            .canvases.flatMap((canvas) =>
              canvas.nodes.map((node) => ({
                route: "libtv",
                canvasId: canvas.id,
                sourceNodeId: node.id,
              })),
            );
          return window.__director_store
            .getState()
            .reconcileProjectOwners(liveOwners);
        }"""
    )
    assert final_reconcile["tombstoneOwnerKeys"] == []
    assert errors == [], json.dumps(errors, ensure_ascii=False, indent=2)

    return {
        "owners": {
            "active": fixture["ownerA"],
            "inactive": fixture["ownerB"],
            "crossCanvas": fixture["ownerC"],
        },
        "projects": {
            "active": state_a["projectId"],
            "inactive": state_b["projectId"],
            "crossCanvas": state_c["projectId"],
        },
        "inactiveSourceTombstone": "pass",
        "inactiveCanvasTombstone": "pass",
        "activeSourceCleanup": "pass",
        "renameSwitchPreservation": "pass",
        "unrelatedDeleteIsolation": "pass",
        "repeatedReconciliation": "pass",
        "tombstonedReopenRejected": "pass",
        "graphUndoDoesNotUntombstone": "pass",
        "persistenceEnvelopeRetained": "pass",
        "ordinaryDeleteHistory": "one-step",
    }


def verify_static_contract() -> None:
    planner_source = (
        ROOT / "src/lib/directorOwnerReconciliation.ts"
    ).read_text()
    store_source = (ROOT / "src/store/directorStore.ts").read_text()
    page_source = (ROOT / "src/app/page.tsx").read_text()
    for label in [
        "collectLiveDirectorProjectOwners",
        "createDirectorOwnerReachabilitySignature",
        "planDirectorOwnerReachability",
        "activeOwnerInvalidated",
        "alreadyTombstonedOwnerKeys",
    ]:
        assert label in planner_source, label
    for label in [
        "reconcileProjectOwners",
        "directorProjectRegistry.tombstone",
        "createInvalidatedDirectorSessionState",
        "clipboard: null",
    ]:
        assert label in store_source, label
    for label in [
        "directorOwnerReachabilitySignature",
        "collectLiveDirectorProjectOwners",
        "reconcileProjectOwners",
    ]:
        assert label in page_source, label
    assert "directorProjectPersistence.remove" not in store_source
    assert "useDirectorStore" not in (
        ROOT / "src/store/canvasStore.ts"
    ).read_text()


def main() -> None:
    verify_static_contract()
    pure_result = run_pure_verifier()
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            device_scale_factor=1,
        )
        page = context.new_page()
        browser_result = run_browser_verifier(page)
        context.close()
        browser.close()

    audit = {
        "batch": 76,
        "status": "OWNER_REACHABILITY_FOCUSED_PASS",
        "date": "2026-08-27",
        "contract": {
            "scope": "clone-owned in-memory Director owner reachability reconciliation",
            "sourceExact": False,
            "durableTombstone": False,
            "persistenceCleanup": False,
            "resourceCleanup": False,
            "graphUndoRestoresDirectorProject": False,
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
        "Batch 76 verification passed: all-canvas Director owner reachability, "
        "inactive source/canvas tombstones, active runtime cleanup, idempotency, "
        "tombstoned reopen rejection, graph undo boundary, retained persistence "
        "and ordinary graph-history isolation."
    )


if __name__ == "__main__":
    main()
