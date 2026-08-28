#!/usr/bin/env python3

"""Verify Batch 79 Director whole-project duplicate in a fresh browser context."""

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
    / "liblib-canvas-batch79-2026-08-28"
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


def main() -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()
        errors, phase = attach_errors(page)
        page.goto(BASE_URL, wait_until="domcontentloaded")
        page.wait_for_function("() => Boolean(window.__libtv_store)")
        page.wait_for_selector("[data-libtv-react-flow-host]")
        page.evaluate(
            """() => {
              for (const key of Object.keys(localStorage)) {
                if (key.startsWith("liblib-tv-director-project-v1:")) {
                  localStorage.removeItem(key);
                }
              }
            }"""
        )
        page.reload(wait_until="domcontentloaded")
        page.wait_for_function("() => Boolean(window.__libtv_store)")
        page.wait_for_selector("[data-libtv-react-flow-host]")

        phase[0] = "prepare-source"
        source = page.evaluate(
            """() => {
              const state = window.__libtv_store.getState();
              const canvas = state.canvases.find((item) =>
                item.nodes.some((node) => node.type === "script-execution")
              );
              const node = canvas?.nodes.find(
                (item) => item.type === "script-execution"
              );
              return canvas && node
                ? { canvasId: canvas.id, nodeId: node.id }
                : null;
            }"""
        )
        assert source is not None, "source Director node fixture is missing"
        page.evaluate(
            """(source) => {
              const canvas = window.__libtv_store.getState().canvases.find(
                (item) => item.id === source.canvasId
              );
              window.__libtv_store.getState().setActiveCanvas(source.canvasId);
              window.__libtv_ui_store.getState().openDirectorDesk(
                source.nodeId,
                source.canvasId
              );
              return canvas?.nodes.length ?? 0;
            }""",
            source,
        )
        page.locator("[data-director-workspace]").wait_for(state="visible")
        page.evaluate(
            """() => {
              const state = window.__director_store.getState();
              const object = state.authoredObjects.find(
                (item) => item.kind === "character"
              );
              if (!object) throw new Error("character fixture is missing");
              state.updateObject(object.id, { name: "Batch79 source authored" });
            }"""
        )
        page.wait_for_function(
            """() => window.__director_store.getState().authoredObjects.some(
              (item) => item.name === "Batch79 source authored"
            )"""
        )
        page.evaluate(
            """() => {
              window.__director_store.getState().closeSession();
              window.__libtv_ui_store.getState().closeDirectorDesk();
            }"""
        )
        page.locator("[data-director-workspace]").wait_for(state="hidden")

        source_before = page.evaluate(
            """(source) => {
              const state = window.__libtv_store.getState();
              const canvas = state.canvases.find(
                (item) => item.id === source.canvasId
              );
              return {
                canvasIds: state.canvases.map((item) => item.id),
                nodeIds: (canvas?.nodes || []).map((item) => item.id),
                edgeIds: (canvas?.edges || []).map((item) => item.id),
                nodeCount: canvas?.nodes.length ?? 0,
                edgeCount: canvas?.edges.length ?? 0,
              };
            }""",
            source,
        )

        phase[0] = "duplicate"
        result = page.evaluate(
            """(sourceCanvasId) =>
              window.__libtv_store.getState().duplicateCanvas(sourceCanvasId)""",
            source["canvasId"],
        )
        assert result["disposition"] in (
            "COMMITTED",
            "COMMITTED_SESSION_ONLY",
        ), result
        target_canvas_id = result["targetCanvasId"]
        assert target_canvas_id
        assert result["targetProjectIds"], result
        page.wait_for_function(
            "(targetId) => window.__libtv_store.getState().activeCanvasId === targetId",
            arg=target_canvas_id,
        )

        target_graph = page.evaluate(
            """(source) => {
              const state = window.__libtv_store.getState();
              const sourceCanvas = state.canvases.find(
                (item) => item.id === source.canvasId
              );
              const targetCanvas = state.canvases.find(
                (item) => item.id === state.activeCanvasId
              );
              const history = state.historyByCanvas[state.activeCanvasId] || {
                past: [],
                future: [],
              };
              return {
                sourceNodeIds: (sourceCanvas?.nodes || []).map((item) => item.id),
                targetNodeIds: (targetCanvas?.nodes || []).map((item) => item.id),
                sourceEdgeIds: (sourceCanvas?.edges || []).map((item) => item.id),
                targetEdgeIds: (targetCanvas?.edges || []).map((item) => item.id),
                selection: {
                  nodeIds: state.selectedNodeIds,
                  nodeId: state.selectedNodeId,
                  edgeIds: state.selectedEdgeIds,
                },
                targetHistory: {
                  past: history.past.length,
                  future: history.future.length,
                },
                targetDirectorNode: (targetCanvas?.nodes || []).find(
                  (item) => item.type === "script-execution"
                )?.id || null,
              };
            }""",
            source,
        )
        assert set(source_before["nodeIds"]) == set(target_graph["sourceNodeIds"])
        assert not set(target_graph["sourceNodeIds"]).intersection(
            target_graph["targetNodeIds"]
        )
        assert not set(target_graph["sourceEdgeIds"]).intersection(
            target_graph["targetEdgeIds"]
        )
        assert target_graph["selection"] == {"nodeIds": [], "nodeId": None, "edgeIds": []}
        assert target_graph["targetHistory"] == {"past": 0, "future": 0}
        assert target_graph["targetDirectorNode"]

        phase[0] = "target-open"
        page.evaluate(
            """(targetNodeId) => {
              const state = window.__libtv_store.getState();
              window.__libtv_ui_store.getState().openDirectorDesk(
                targetNodeId,
                state.activeCanvasId
              );
            }""",
            target_graph["targetDirectorNode"],
        )
        page.locator("[data-director-workspace]").wait_for(state="visible")
        page.wait_for_function(
            "(projectId) => window.__director_store.getState().projectId === projectId",
            arg=result["targetProjectIds"][0],
        )
        target_state = page.evaluate(
            """() => {
              const state = window.__director_store.getState();
              const registry = window.__director_project_registry_snapshot();
              const record = registry.records.find(
                (item) => item.identity.projectId === state.projectId
              );
              return {
                projectId: state.projectId,
                owner: state.projectOwner,
                sourceName: state.authoredObjects.find(
                  (item) => item.kind === "character"
                )?.name || null,
                historyPast: state.history.past.length,
                historyFuture: state.history.future.length,
                clipboard: Boolean(state.clipboard),
                lifecycle: state.projectLifecycle,
                documentObjectCount: record?.document.objects.length || 0,
              };
            }"""
        )
        assert target_state["projectId"] == result["targetProjectIds"][0]
        assert target_state["sourceName"] == "Batch79 source authored"
        assert target_state["historyPast"] == 0
        assert target_state["historyFuture"] == 0
        assert target_state["clipboard"] is False
        assert target_state["lifecycle"] == "ACTIVE"

        page.evaluate(
            """() => {
              const state = window.__director_store.getState();
              const object = state.authoredObjects.find(
                (item) => item.kind === "character"
              );
              if (!object) throw new Error("target character fixture is missing");
              state.updateObject(object.id, { name: "Batch79 target authored" });
              state.closeSession();
              window.__libtv_ui_store.getState().closeDirectorDesk();
            }"""
        )
        page.locator("[data-director-workspace]").wait_for(state="hidden")

        phase[0] = "source-isolation"
        page.evaluate(
            """(source) => {
              window.__libtv_store.getState().setActiveCanvas(source.canvasId);
              window.__libtv_ui_store.getState().openDirectorDesk(
                source.nodeId,
                source.canvasId
              );
            }""",
            source,
        )
        page.locator("[data-director-workspace]").wait_for(state="visible")
        source_state = page.evaluate(
            """() => {
              const state = window.__director_store.getState();
              return {
                projectId: state.projectId,
                owner: state.projectOwner,
                name: state.authoredObjects.find(
                  (item) => item.kind === "character"
                )?.name || null,
              };
            }"""
        )
        assert source_state["name"] == "Batch79 source authored"
        assert source_state["projectId"] != target_state["projectId"]
        assert source_state["owner"]["canvasId"] == source["canvasId"]

        persistence = page.evaluate(
            "() => window.__director_project_persistence_snapshot()"
        )
        target_persistence = [
            record
            for record in persistence["records"]
            if record["projectId"] == result["targetProjectIds"][0]
        ]
        assert target_persistence, persistence
        assert target_persistence[0]["owner"]["canvasId"] == target_canvas_id

        phase[0] = "complete"
        audit = {
            "batch": 79,
            "status": "SCRIPT_RECORDED_PASS",
            "baseUrl": BASE_URL,
            "sourceCanvasId": source["canvasId"],
            "targetCanvasId": target_canvas_id,
            "duplicate": result,
            "graph": {
                "sourceNodeCount": len(source_before["nodeIds"]),
                "targetNodeCount": len(target_graph["targetNodeIds"]),
                "sourceEdgeCount": len(source_before["edgeIds"]),
                "targetEdgeCount": len(target_graph["targetEdgeIds"]),
                "selectionCleared": target_graph["selection"]
                == {"nodeIds": [], "nodeId": None, "edgeIds": []},
                "targetHistoryEmpty": target_graph["targetHistory"]
                == {"past": 0, "future": 0},
            },
            "director": {
                "targetAuthoredCopied": target_state["sourceName"]
                == "Batch79 source authored",
                "targetHistoryEmpty": target_state["historyPast"] == 0
                and target_state["historyFuture"] == 0,
                "targetClipboardEmpty": not target_state["clipboard"],
                "sourceTargetIsolation": source_state["name"]
                == "Batch79 source authored",
                "independentProjectIds": source_state["projectId"]
                != target_state["projectId"],
            },
            "persistence": {
                "targetKeyPresent": bool(target_persistence),
                "targetOwnerIsDistinct": target_persistence[0]["owner"]["canvasId"]
                == target_canvas_id,
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
