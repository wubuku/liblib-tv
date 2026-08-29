#!/usr/bin/env python3

"""Verify Batch 80 durable Director tombstone and resource cleanup."""

from __future__ import annotations

import json
import os
from pathlib import Path

from playwright.sync_api import Page, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
BASE_URL = os.environ.get("LIBLIB_BASE_URL", "http://localhost:4317")
AUDIT_PATH = (
    ROOT
    / "docs"
    / "research"
    / "liblib-canvas-batch80-2026-08-28"
    / "runtime-audit.json"
)
LOCAL_MODEL_KEY = "liblib-tv-director-local-model-library-v1"


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


def main() -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()
        errors, phase = attach_errors(page)
        page.goto(BASE_URL, wait_until="domcontentloaded")
        wait_for_app(page)

        phase[0] = "reset"
        page.evaluate(
            """(modelKey) => {
              for (const key of Object.keys(localStorage)) {
                if (key.startsWith("liblib-tv-director-project-v1:")) {
                  localStorage.removeItem(key);
                }
              }
              localStorage.removeItem(modelKey);
            }""",
            LOCAL_MODEL_KEY,
        )
        page.reload(wait_until="domcontentloaded")
        wait_for_app(page)
        page.evaluate(
            "() => window.__director_store.getState().hydrateLocalModelLibrary()"
        )

        phase[0] = "prepare"
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
              canvasState.addNodeAtPosition(
                "script-execution",
                { x: 1800, y: -187 },
                { title: "Batch80 second Director owner" }
              );
              return { canvasId: canvas.id, sourceNodeId: source.id };
            }"""
        )
        page.wait_for_function(
            """(canvasId) => {
              const canvas = window.__libtv_store.getState().canvases.find(
                (item) => item.id === canvasId
              );
              return (canvas?.nodes || []).filter(
                (node) => node.type === "script-execution"
              ).length >= 2;
            }""",
            arg=fixture["canvasId"],
        )
        fixture["secondNodeId"] = page.evaluate(
            """(fixture) => {
              const canvas = window.__libtv_store.getState().canvases.find(
                (item) => item.id === fixture.canvasId
              );
              return canvas?.nodes.find(
                (node) =>
                  node.type === "script-execution" &&
                  node.id !== fixture.sourceNodeId
              )?.id || null;
            }""",
            fixture,
        )
        assert fixture["secondNodeId"], fixture

        local_item = {
            "id": "batch80-shared-local-model",
            "categoryId": "my-models",
            "name": "Batch 80 shared model",
            "fileName": "batch80-shared.obj",
            "dataUrl": "data:text/plain;base64,byBiYXRjaDgwLXNoYXJlZAp2IDAgMCAwCnYgMSAwIDAKdiAwIDEgMApmIDEgMiAzCg==",
            "visual": "box",
            "color": "#7db5d8",
        }
        page.evaluate(
            """(item) =>
              window.__director_store.getState().addLocalModelLibraryItem(item)""",
            local_item,
        )

        owner_a = {
            "route": "libtv",
            "canvasId": fixture["canvasId"],
            "sourceNodeId": fixture["sourceNodeId"],
        }
        owner_b = {
            "route": "libtv",
            "canvasId": fixture["canvasId"],
            "sourceNodeId": fixture["secondNodeId"],
        }

        phase[0] = "author-source-a"
        page.evaluate(
            """(owner) => {
              window.__libtv_ui_store.getState().openDirectorDesk(
                owner.sourceNodeId,
                owner.canvasId
              );
            }""",
            owner_a,
        )
        page.locator("[data-director-workspace]").wait_for(state="visible")
        page.wait_for_function(
            "(owner) => JSON.stringify(window.__director_store.getState().projectOwner) === JSON.stringify(owner)",
            arg=owner_a,
        )
        page.evaluate(
            """(item) => {
              const state = window.__director_store.getState();
              state.addModelLibraryObject(item);
              const object = window.__director_store.getState().authoredObjects.find(
                (candidate) => candidate.libraryAssetId === item.id
              );
              if (!object) throw new Error("source local model object missing");
              state.updateObject(object.id, { name: "Batch80 source A authored" });
              const current = window.__director_store.getState();
              const camera = current.authoredObjects.find(
                (candidate) => candidate.id === current.activeCameraId
              );
              current.addCapture({
                id: "batch80-capture-a",
                dataUrl: "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=",
                cameraId: current.activeCameraId,
                cameraName: camera?.name || "Main camera",
                aspectRatio: current.aspectRatio,
                width: 1280,
                height: 720,
                createdAt: "2026-08-28T12:10:00.000Z",
              });
            }""",
            local_item,
        )
        source_a_before_close = page.evaluate(
            """() => {
              const state = window.__director_store.getState();
              return {
                projectId: state.projectId,
                objectCount: state.authoredObjects.length,
                localResourceRefs: state.authoredObjects.filter(
                  (object) => object.libraryAssetId === "batch80-shared-local-model"
                ).length,
                captureCount: state.captures.length,
                historyPast: state.history.past.length,
              };
            }"""
        )
        page.evaluate(
            """(owner) => {
              window.__director_store.getState().closeSession(owner);
              window.__libtv_ui_store.getState().closeDirectorDesk();
            }""",
            owner_a,
        )
        page.locator("[data-director-workspace]").wait_for(state="hidden")

        phase[0] = "author-source-b"
        page.evaluate(
            """(owner) => {
              window.__libtv_ui_store.getState().openDirectorDesk(
                owner.sourceNodeId,
                owner.canvasId
              );
            }""",
            owner_b,
        )
        page.locator("[data-director-workspace]").wait_for(state="visible")
        page.wait_for_function(
            "(owner) => JSON.stringify(window.__director_store.getState().projectOwner) === JSON.stringify(owner)",
            arg=owner_b,
        )
        page.evaluate(
            """(item) => {
              const state = window.__director_store.getState();
              state.addModelLibraryObject(item);
              const object = window.__director_store.getState().authoredObjects.find(
                (candidate) => candidate.libraryAssetId === item.id
              );
              if (!object) throw new Error("source B local model object missing");
              state.updateObject(object.id, { name: "Batch80 source B authored" });
              state.closeSession();
              window.__libtv_ui_store.getState().closeDirectorDesk();
            }""",
            local_item,
        )
        page.locator("[data-director-workspace]").wait_for(state="hidden")

        authored = page.evaluate(
            """(owners) => {
              const registry = window.__director_project_registry_snapshot();
              return owners.map((owner) => {
                const record = registry.records.find(
                  (candidate) =>
                    JSON.stringify(candidate.identity.owner) === JSON.stringify(owner)
                );
                return record
                  ? {
                      owner: record.identity.owner,
                      projectId: record.identity.projectId,
                      lifecycle: record.lifecycle,
                      localRefs: record.document.resourceRefs
                        .filter((resource) => resource.source === "local")
                        .map((resource) => resource.id),
                      captures: record.memory.captures.length,
                    }
                  : null;
              });
            }""",
            [owner_a, owner_b],
        )
        assert authored[0] and authored[1], authored
        assert authored[0]["projectId"] != authored[1]["projectId"], authored
        assert authored[0]["captures"] == 1, authored
        assert authored[0]["localRefs"] == [local_item["id"]], authored
        assert authored[1]["localRefs"] == [local_item["id"]], authored

        phase[0] = "delete-active-owner"
        page.evaluate(
            """(owner) => {
              window.__libtv_ui_store.getState().openDirectorDesk(
                owner.sourceNodeId,
                owner.canvasId
              );
            }""",
            owner_a,
        )
        page.locator("[data-director-workspace]").wait_for(state="visible")
        page.wait_for_function(
            "(owner) => JSON.stringify(window.__director_store.getState().projectOwner) === JSON.stringify(owner)",
            arg=owner_a,
        )
        page.evaluate(
            """(owner) => {
              window.__libtv_store.getState().removeNode(owner.sourceNodeId);
            }""",
            owner_a,
        )
        page.wait_for_function(
            """() =>
              window.__director_store.getState().projectId === null &&
              window.__director_store.getState().sessionId === null &&
              window.__director_store.getState().localModelLibrary.some(
                (item) => item.id === "batch80-shared-local-model"
              )"""
        )
        page.locator("[data-director-workspace]").wait_for(state="hidden")

        after_active_delete = page.evaluate(
            """(owner) => {
              const registry = window.__director_project_registry_snapshot();
              const persistence = window.__director_project_persistence_snapshot();
              const record = registry.records.find(
                (candidate) =>
                  JSON.stringify(candidate.identity.owner) === JSON.stringify(owner)
              );
              const persisted = persistence.records.find(
                (candidate) =>
                  JSON.stringify(candidate.owner) === JSON.stringify(owner)
              );
              const canvasState = window.__libtv_store.getState();
              const canvas = canvasState.canvases.find(
                (item) => item.id === owner.canvasId
              );
              const history = canvasState.historyByCanvas[owner.canvasId] || {
                past: [],
                future: [],
              };
              return {
                registry: record
                  ? {
                      lifecycle: record.lifecycle,
                      memoryCaptureCount: record.memory.captures.length,
                      generation: record.identity.generation,
                    }
                  : null,
                persistence: persisted
                  ? {
                      status: persisted.status,
                      reason: persisted.reason,
                      generation: persisted.generation,
                    }
                  : null,
                localModelIds: window.__director_store
                  .getState()
                  .localModelLibrary.map((item) => item.id),
                remainingDirectorNodes: (canvas?.nodes || [])
                  .filter((node) => node.type === "script-execution")
                  .map((node) => node.id),
                graphHistoryPast: history.past.length,
                directorHistoryPast: window.__director_store.getState().history.past.length,
                activeSession: registry.activeSession,
              };
            }""",
            owner_a,
        )
        assert after_active_delete["registry"]["lifecycle"] == "TOMBSTONED", after_active_delete
        assert after_active_delete["registry"]["memoryCaptureCount"] == 0, after_active_delete
        assert after_active_delete["persistence"]["status"] == "TOMBSTONED", after_active_delete
        assert local_item["id"] in after_active_delete["localModelIds"], after_active_delete
        assert owner_b["sourceNodeId"] in after_active_delete["remainingDirectorNodes"], after_active_delete
        assert after_active_delete["graphHistoryPast"] >= 1, after_active_delete
        assert after_active_delete["directorHistoryPast"] == 0, after_active_delete
        assert after_active_delete["activeSession"] is None, after_active_delete

        phase[0] = "delete-inactive-owner"
        page.evaluate(
            """(owner) => {
              window.__libtv_store.getState().removeNode(owner.sourceNodeId);
            }""",
            owner_b,
        )
        page.wait_for_function(
            """() =>
              !window.__director_store.getState().localModelLibrary.some(
                (item) => item.id === "batch80-shared-local-model"
              )"""
        )
        after_inactive_delete = page.evaluate(
            """(owner) => {
              const registry = window.__director_project_registry_snapshot();
              const persistence = window.__director_project_persistence_snapshot();
              const record = registry.records.find(
                (candidate) =>
                  JSON.stringify(candidate.identity.owner) === JSON.stringify(owner)
              );
              const persisted = persistence.records.find(
                (candidate) =>
                  JSON.stringify(candidate.owner) === JSON.stringify(owner)
              );
              const rawModel = localStorage.getItem(
                "liblib-tv-director-local-model-library-v1"
              );
              const canvas = window.__libtv_store.getState().canvases.find(
                (item) => item.id === owner.canvasId
              );
              const history =
                window.__libtv_store.getState().historyByCanvas[owner.canvasId] || {
                  past: [],
                  future: [],
                };
              return {
                registry: record
                  ? {
                      lifecycle: record.lifecycle,
                      memoryCaptureCount: record.memory.captures.length,
                    }
                  : null,
                persistence: persisted
                  ? {
                      status: persisted.status,
                      reason: persisted.reason,
                    }
                  : null,
                modelStorage: rawModel,
                remainingNodes: (canvas?.nodes || []).filter(
                  (node) => node.type === "script-execution"
                ).length,
                graphHistoryPast: history.past.length,
              };
            }""",
            owner_b,
        )
        assert after_inactive_delete["registry"]["lifecycle"] == "TOMBSTONED", after_inactive_delete
        assert after_inactive_delete["registry"]["memoryCaptureCount"] == 0, after_inactive_delete
        assert after_inactive_delete["persistence"]["status"] == "TOMBSTONED", after_inactive_delete
        assert after_inactive_delete["modelStorage"] in (None, "[]"), after_inactive_delete
        assert after_inactive_delete["remainingNodes"] == 0, after_inactive_delete
        assert after_inactive_delete["graphHistoryPast"] >= 2, after_inactive_delete

        phase[0] = "reload-reopen-guard"
        page.reload(wait_until="domcontentloaded")
        wait_for_app(page)
        page.evaluate(
            "() => window.__director_store.getState().hydrateLocalModelLibrary()"
        )
        reopen_a = page.evaluate(
            """(owner) =>
              window.__director_store.getState().openSession(owner)""",
            owner_a,
        )
        reopen_b = page.evaluate(
            """(owner) =>
              window.__director_store.getState().openSession(owner)""",
            owner_b,
        )
        assert reopen_a["disposition"] == "REJECTED", reopen_a
        assert reopen_a["reason"] == "PROJECT_TOMBSTONED", reopen_a
        assert reopen_b["disposition"] == "REJECTED", reopen_b
        assert reopen_b["reason"] == "PROJECT_TOMBSTONED", reopen_b
        after_reload = page.evaluate(
            """() => ({
              localModelLibrary: window.__director_store.getState()
                .localModelLibrary,
              persistence: window.__director_project_persistence_snapshot(),
              errors: [],
            })"""
        )
        assert after_reload["localModelLibrary"] == [], after_reload
        assert not errors, errors

        phase[0] = "complete"
        audit = {
            "batch": 80,
            "status": "SCRIPT_RECORDED_PASS",
            "baseUrl": BASE_URL,
            "owners": {
                "sourceA": owner_a,
                "sourceB": owner_b,
                "sourceAProjectId": authored[0]["projectId"],
                "sourceBProjectId": authored[1]["projectId"],
            },
            "activeOwnerCleanup": {
                "tombstoned": True,
                "memoryCaptureArchiveCleared": after_active_delete["registry"][
                    "memoryCaptureCount"
                ]
                == 0,
                "sharedLocalResourceRetained": local_item["id"]
                in after_active_delete["localModelIds"],
                "activeSessionCleared": after_active_delete["activeSession"] is None,
                "directorHistoryUnaffected": after_active_delete["directorHistoryPast"]
                == 0,
            },
            "inactiveOwnerCleanup": {
                "tombstoned": True,
                "unreferencedLocalResourceReleased": after_inactive_delete[
                    "modelStorage"
                ]
                in (None, "[]"),
                "graphHistoryPreserved": after_inactive_delete["graphHistoryPast"]
                >= 2,
            },
            "reload": {
                "bothDurableTombstonesRejectReopen": True,
                "localModelLibraryEmpty": after_reload["localModelLibrary"] == [],
            },
            "errors": errors,
        }
        AUDIT_PATH.write_text(
            json.dumps(audit, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        assert not errors, errors
        print(json.dumps(audit, ensure_ascii=False, separators=(",", ":")))
        context.close()
        browser.close()


if __name__ == "__main__":
    main()
