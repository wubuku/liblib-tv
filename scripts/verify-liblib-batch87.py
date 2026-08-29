#!/usr/bin/env python3

"""Verify Batch 87 Director selection repair across document restore paths."""

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
    / "liblib-canvas-batch87-2026-08-29"
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
    return fixture


def state_snapshot(page: Page) -> dict[str, Any]:
    return page.evaluate(
        """() => {
          const state = window.__director_store.getState();
          const selected = state.objects.find(
            (item) => item.id === state.selectedObjectId
          );
          const selectedTrack = state.timeline.tracks.find(
            (track) => track.id === state.timeline.selectedTrackId
          );
          return {
            selectedObjectId: state.selectedObjectId,
            selectedObjectIds: state.selectedObjectIds,
            selectedGroupId: state.selectedGroupId,
            selectedObjectKind: selected?.kind ?? null,
            selectedTrackId: state.timeline.selectedTrackId,
            selectedKeyframeId: state.timeline.selectedKeyframeId,
            selectedMotionPathId: state.timeline.selectedMotionPathId,
            selectedMotionPathAnchorId:
              state.timeline.selectedMotionPathAnchorId,
            selectedTrackObjectId: selectedTrack?.objectId ?? null,
            selectedTrackKind: selectedTrack?.kind ?? null,
            historyPast: state.history.past.length,
            historyFuture: state.history.future.length,
            authored: state.authoredObjects.map((object) => ({
              id: object.id,
              position: object.transform.position,
            })),
          };
        }"""
    )


def close_director(page: Page, owner: dict[str, str]) -> None:
    page.evaluate(
        """(owner) => {
          window.__director_store.getState().closeSession(owner);
          window.__libtv_ui_store.getState().closeDirectorDesk();
        }""",
        owner,
    )
    page.locator("[data-director-workspace]").wait_for(state="hidden")


def main() -> None:
    results: dict[str, bool] = {}
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            device_scale_factor=1,
        )
        page = context.new_page()
        errors, phase = attach_errors(page)
        page.goto(BASE_URL, wait_until="domcontentloaded")
        wait_for_app(page)

        phase[0] = "reset"
        reset_director_persistence(page)
        page.reload(wait_until="domcontentloaded")
        wait_for_app(page)
        owner = open_director(page)

        phase[0] = "select-prop-and-track"
        prop_row = page.locator('[data-director-object-id="director-prop-mug"]')
        prop_row.click()
        page.wait_for_function(
            "() => window.__director_store.getState().selectedObjectId === 'director-prop-mug'"
        )
        page.evaluate(
            """() => {
              const state = window.__director_store.getState();
              state.addTimelineTrack("director-prop-mug");
            }"""
        )
        page.wait_for_function(
            """() => {
              const state = window.__director_store.getState();
              return state.timeline.selectedTrackId !== null &&
                state.timeline.tracks.some(
                  (track) => track.objectId === 'director-prop-mug'
                );
            }"""
        )
        before_edit = state_snapshot(page)
        assert before_edit["selectedObjectId"] == "director-prop-mug"
        assert before_edit["selectedTrackObjectId"] == "director-prop-mug"
        assert before_edit["selectedTrackId"] is not None
        results["baselineObjectAndTimelineAuthority"] = True

        phase[0] = "document-edit"
        initial_x = next(
            item["position"][0]
            for item in before_edit["authored"]
            if item["id"] == "director-prop-mug"
        )
        history_before_edit = before_edit["historyPast"]
        page.evaluate(
            """(value) => {
              window.__director_store.getState().updateObjectTransform(
                'director-prop-mug', 'position', 0, value
              );
            }""",
            initial_x + 0.8,
        )
        page.wait_for_function(
            """(initial) => {
              const object = window.__director_store.getState().authoredObjects
                .find((item) => item.id === 'director-prop-mug');
              return object?.transform.position[0] === initial + 0.8;
            }""",
            arg=initial_x,
        )
        assert state_snapshot(page)["historyPast"] == history_before_edit + 1
        results["oneEntryDocumentMutation"] = True

        phase[0] = "undo-preserve-selection"
        page.evaluate("() => window.__director_store.getState().undoDirector()")
        page.wait_for_function(
            """() => {
              const state = window.__director_store.getState();
              return state.history.future.length === 1 &&
                state.selectedObjectId === 'director-prop-mug' &&
                state.timeline.selectedTrackId !== null;
            }"""
        )
        undone = state_snapshot(page)
        assert undone["selectedObjectId"] == "director-prop-mug"
        assert undone["selectedObjectIds"] == ["director-prop-mug"]
        assert undone["selectedTrackObjectId"] == "director-prop-mug"
        assert undone["selectedTrackKind"] != "pose"
        assert page.locator(
            '[data-director-object-id="director-prop-mug"][data-director-object-selected="true"]'
        ).count() == 1
        assert page.locator('[data-director-inspector-kind="prop"]').count() == 1
        assert page.locator(
            '[data-director-transform-context][data-director-transform-context-kind="object"]'
        ).count() == 1
        results["undoKeepsObjectTreeInspectorViewport"] = True

        phase[0] = "redo-preserve-selection"
        page.evaluate("() => window.__director_store.getState().redoDirector()")
        page.wait_for_function(
            """() => {
              const state = window.__director_store.getState();
              return state.history.future.length === 0 &&
                state.selectedObjectId === 'director-prop-mug' &&
                state.timeline.selectedTrackId !== null;
            }"""
        )
        redone = state_snapshot(page)
        assert redone["selectedObjectId"] == "director-prop-mug"
        assert redone["selectedTrackObjectId"] == "director-prop-mug"
        results["redoKeepsObjectTreeInspectorViewport"] = True

        phase[0] = "missing-selection-repair"
        page.evaluate(
            """() => {
              const state = window.__director_store.getState();
              window.__director_store.setState({
                selectedObjectId: 'missing-director-object',
                selectedObjectIds: ['missing-director-object'],
                selectedGroupId: 'missing-director-group',
                timeline: {
                  ...window.__director_store.getState().timeline,
                  selectedTrackId: 'missing-track',
                  selectedKeyframeId: 'missing-keyframe',
                  selectedMotionPathId: 'missing-path',
                  selectedMotionPathAnchorId: 'missing-anchor',
                  selectedMotionPathHandle: 'out',
                },
              });
            }"""
        )
        page.evaluate(
            """() => window.__director_store.getState().undoDirector()"""
        )
        repaired = state_snapshot(page)
        assert repaired["selectedObjectId"] == "director-character-lead"
        assert repaired["selectedObjectIds"] == ["director-character-lead"]
        assert repaired["selectedGroupId"] is None
        assert repaired["selectedTrackId"] is None
        assert repaired["selectedKeyframeId"] is None
        assert repaired["selectedMotionPathId"] is None
        assert repaired["selectedMotionPathAnchorId"] is None
        results["invalidSelectionCleared"] = True

        phase[0] = "explicit-empty-selection-preserved"
        page.evaluate(
            """() => {
              const state = window.__director_store.getState();
              state.selectObject(null);
              window.__director_store.setState({
                selectedObjectId: null,
                selectedObjectIds: [],
                selectedGroupId: null,
              });
            }"""
        )
        page.evaluate("() => window.__director_store.getState().redoDirector()")
        empty_selection = state_snapshot(page)
        assert empty_selection["selectedObjectId"] is None
        assert empty_selection["selectedObjectIds"] == []
        assert empty_selection["selectedGroupId"] is None
        results["explicitEmptySelectionPreserved"] = True

        phase[0] = "document-boundary"
        document_fingerprint = page.evaluate(
            """() => {
              const state = window.__director_store.getState();
              const document = JSON.parse(state.exportDirectorProject());
              return {
                keys: Object.keys(document).sort(),
                hasSelection: Object.keys(document).some((key) =>
                  key.toLowerCase().includes('selection')
                ),
              };
            }"""
        )
        assert document_fingerprint["hasSelection"] is False
        assert "objects" in document_fingerprint["keys"]
        assert "timeline" in document_fingerprint["keys"]
        results["portableDocumentExcludesSelection"] = True

        phase[0] = "close"
        close_director(page, owner)
        browser.close()

    diagnostics = {
        "consoleErrors": len([item for item in errors if ":console:" in item]),
        "pageErrors": len([item for item in errors if ":pageerror:" in item]),
        "requestFailures": len(
            [item for item in errors if ":requestfailed:" in item]
        ),
        "details": errors,
    }
    audit = {
        "batch": 87,
        "status": "SCRIPT_RECORDED_PASS",
        "baseUrl": BASE_URL,
        "contract": {
            "scope": "clone-owned Director restore selection authority",
            "sourceExact": False,
            "undoRedoPreserveCurrentSelection": True,
            "invalidSelectionRepair": True,
            "portableDocumentExcludesSelection": True,
            "timelineSelectionRepair": True,
        },
        "desktop": results,
        "diagnostics": diagnostics,
    }
    AUDIT_PATH.write_text(
        json.dumps(audit, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    if errors:
        raise AssertionError("\n".join(errors))
    print(json.dumps(audit, ensure_ascii=False))


if __name__ == "__main__":
    main()
