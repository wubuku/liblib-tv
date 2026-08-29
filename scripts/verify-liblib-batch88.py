#!/usr/bin/env python3

"""Verify Batch 88 Director selection/timeline/transform authority."""

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
    / "liblib-canvas-batch88-2026-08-29"
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
    page.wait_for_timeout(300)
    return fixture


def state_snapshot(page: Page) -> dict[str, Any]:
    return page.evaluate(
        """() => {
          const state = window.__director_store.getState();
          const selectedTrack = state.timeline.tracks.find(
            (track) => track.id === state.timeline.selectedTrackId
          );
          const selectedPath = state.timeline.motionPaths.find(
            (path) => path.id === state.timeline.selectedMotionPathId
          );
          const selectedObject = state.objects.find(
            (object) => object.id === state.selectedObjectId
          );
          const trackOwnerMatchesSelection = selectedTrack
            ? selectedTrack.kind === "group"
              ? selectedTrack.groupId === state.selectedGroupId
              : state.selectedGroupId === null &&
                state.selectedObjectIds.length === 1 &&
                selectedTrack.objectId === state.selectedObjectId
            : true;
          const keyframeBelongsToTrack = selectedTrack
            ? !state.timeline.selectedKeyframeId ||
              selectedTrack.keyframes.some(
                (keyframe) => keyframe.id === state.timeline.selectedKeyframeId
              )
            : state.timeline.selectedKeyframeId === null;
          const pathBelongsToTrack = selectedPath
            ? selectedTrack?.motionPathId === selectedPath.id
            : state.timeline.selectedMotionPathId === null;
          const anchorBelongsToPath = selectedPath
            ? !state.timeline.selectedMotionPathAnchorId ||
              selectedPath.anchors.some(
                (anchor) =>
                  anchor.id === state.timeline.selectedMotionPathAnchorId
              )
            : state.timeline.selectedMotionPathAnchorId === null;
          return {
            selectedObjectId: state.selectedObjectId,
            selectedObjectIds: state.selectedObjectIds,
            selectedGroupId: state.selectedGroupId,
            selectedObjectKind: selectedObject?.kind ?? null,
            selectedTrackId: state.timeline.selectedTrackId,
            selectedKeyframeId: state.timeline.selectedKeyframeId,
            selectedMotionPathId: state.timeline.selectedMotionPathId,
            selectedMotionPathAnchorId:
              state.timeline.selectedMotionPathAnchorId,
            selectedTrackObjectId: selectedTrack?.objectId ?? null,
            selectedTrackGroupId:
              selectedTrack?.kind === "group" ? selectedTrack.groupId : null,
            selectedTrackKind: selectedTrack?.kind ?? null,
            selectedTrackPathId: selectedTrack?.motionPathId ?? null,
            selectedTrackKeyframeIds: selectedTrack?.keyframes.map(
              (keyframe) => keyframe.id
            ) ?? [],
            selectedPathAnchorIds: selectedPath?.anchors.map(
              (anchor) => anchor.id
            ) ?? [],
            trackOwnerMatchesSelection,
            keyframeBelongsToTrack,
            pathBelongsToTrack,
            anchorBelongsToPath,
            historyPast: state.history.past.length,
            historyFuture: state.history.future.length,
            document: state.exportDirectorProject(),
            objects: state.objects.map((object) => object.id),
            groups: state.groups.map((group) => ({
              id: group.id,
              characterIds: group.characterIds,
            })),
          };
        }"""
    )


def assert_selection_invariants(page: Page) -> dict[str, Any]:
    snapshot = state_snapshot(page)
    assert snapshot["trackOwnerMatchesSelection"]
    assert snapshot["keyframeBelongsToTrack"]
    assert snapshot["pathBelongsToTrack"]
    assert snapshot["anchorBelongsToPath"]
    if len(snapshot["selectedObjectIds"]) != 1 or snapshot["selectedGroupId"]:
        assert snapshot["selectedTrackId"] is None or snapshot["trackOwnerMatchesSelection"]
    return snapshot


def close_director(page: Page, owner: dict[str, str]) -> None:
    page.evaluate(
        """(owner) => {
          window.__director_store.getState().closeSession(owner);
          window.__libtv_ui_store.getState().closeDirectorDesk();
        }""",
        owner,
    )
    page.locator("[data-director-workspace]").wait_for(state="hidden")


def mobile_bounds(page: Page) -> dict[str, float]:
    return page.evaluate(
        """() => {
          const root = document.querySelector("[data-director-workspace]");
          if (!(root instanceof HTMLElement)) throw new Error("Director root missing");
          const rect = root.getBoundingClientRect();
          return {
            left: rect.left,
            right: rect.right,
            viewport: window.innerWidth,
            scrollWidth: root.scrollWidth,
            clientWidth: root.clientWidth,
          };
        }"""
    )


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

        phase[0] = "single-object-fallback"
        page.evaluate(
            """() => {
              const state = window.__director_store.getState();
              state.selectObject("director-prop-mug");
              state.addTimelineTrack("director-prop-mug");
              state.selectObject("director-prop-table");
            }"""
        )
        table_state = assert_selection_invariants(page)
        assert table_state["selectedObjectId"] == "director-prop-table"
        assert table_state["selectedTrackId"] is None
        assert table_state["selectedKeyframeId"] is None
        assert table_state["selectedMotionPathId"] is None
        results["objectSwitchClearsUnrelatedTrackContext"] = True

        phase[0] = "pose-track-preference"
        page.evaluate(
            """() => {
              const state = window.__director_store.getState();
              state.selectObject("director-character-lead");
              state.applyCharacterPosePreset(
                "director-character-lead",
                "neutral"
              );
            }"""
        )
        pose_state = assert_selection_invariants(page)
        assert pose_state["selectedObjectId"] == "director-character-lead"
        assert pose_state["selectedTrackKind"] == "pose"
        page.evaluate(
            """() => {
              const state = window.__director_store.getState();
              state.selectObject("director-prop-table");
              state.selectObject("director-character-lead");
            }"""
        )
        character_state = assert_selection_invariants(page)
        assert character_state["selectedObjectId"] == "director-character-lead"
        assert character_state["selectedTrackKind"] in ("transform", "pose")
        results["sameObjectPreservesCompatibleTrack"] = True

        phase[0] = "multi-selection"
        crowd_fixture = page.evaluate(
            """() => {
              const state = window.__director_store.getState();
              const groupId = state.addCrowdArray({
                rows: 1,
                columns: 2,
                spacing: 1,
              });
              if (!groupId) throw new Error("Crowd fixture missing");
              const group = window.__director_store.getState().groups.find(
                (item) => item.id === groupId
              );
              if (!group?.characterIds[0]) {
                throw new Error("Crowd member fixture missing");
              }
              return { groupId, memberId: group.characterIds[0] };
            }"""
        )
        page.evaluate(
            """(memberId) => {
              const state = window.__director_store.getState();
              state.selectObject("director-character-lead");
              state.toggleObjectSelection(memberId);
            }""",
            crowd_fixture["memberId"],
        )
        multi_state = assert_selection_invariants(page)
        assert multi_state["selectedObjectIds"] == [
            "director-character-lead",
            crowd_fixture["memberId"],
        ]
        assert multi_state["selectedTrackId"] is None
        assert multi_state["selectedKeyframeId"] is None
        assert multi_state["selectedMotionPathId"] is None
        assert page.locator(
            '[data-director-selection-count]'
        ).inner_text() == "2 个对象已选"
        results["multiSelectionClearsSingleTargetContext"] = True

        phase[0] = "timeline-reverse-authority"
        page.evaluate(
            """() => {
              const state = window.__director_store.getState();
              state.selectObject("director-prop-mug");
              state.addTimelineTrack("director-prop-mug");
            }"""
        )
        mug_track = page.evaluate(
            """() => {
              const state = window.__director_store.getState();
              const track = state.timeline.tracks.find(
                (item) => item.objectId === "director-prop-mug"
              );
              if (!track) throw new Error("Mug track missing");
              return {
                id: track.id,
                keyframeId: track.keyframes[0]?.id ?? null,
              };
            }"""
        )
        page.locator(
            f'[data-director-track-id="{mug_track["id"]}"]'
        ).click()
        track_state = assert_selection_invariants(page)
        assert track_state["selectedObjectId"] == "director-prop-mug"
        assert track_state["selectedTrackId"] == mug_track["id"]
        assert page.locator(
            f'[data-director-object-id="director-prop-mug"][data-director-object-selected="true"]'
        ).count() == 1
        assert page.locator(
            f'[data-director-inspector-track-id="{mug_track["id"]}"]'
        ).count() == 1
        assert page.locator(
            '[data-director-transform-context][data-director-transform-context-kind="object"]'
        ).count() == 1
        if mug_track["keyframeId"]:
            page.locator(
                f'[data-director-keyframe-id="{mug_track["keyframeId"]}"]'
            ).click()
            keyframe_state = assert_selection_invariants(page)
            assert keyframe_state["selectedKeyframeId"] == mug_track["keyframeId"]
            assert keyframe_state["selectedTrackId"] == mug_track["id"]
        results["timelineTrackAndKeyframeDriveAllSurfaces"] = True

        phase[0] = "group-track-authority"
        group_id = crowd_fixture["groupId"]
        page.evaluate(
            """(groupId) => {
              window.__director_store.getState().selectGroup(groupId);
            }""",
            group_id,
        )
        group_state = assert_selection_invariants(page)
        assert group_state["selectedGroupId"] == group_id
        assert group_state["selectedTrackId"] is None
        page.evaluate(
            """(groupId) => {
              window.__director_store.getState().addTimelineTrack(groupId);
            }""",
            group_id,
        )
        group_track = page.evaluate(
            """(groupId) => {
              const state = window.__director_store.getState();
              const track = state.timeline.tracks.find(
                (item) => item.kind === "group" && item.groupId === groupId
              );
              if (!track) throw new Error("Group track missing");
              return { id: track.id, memberCount: track.memberOffsets
                ? Object.keys(track.memberOffsets).length : 0 };
            }""",
            group_id,
        )
        page.locator(
            f'[data-director-track-id="{group_track["id"]}"]'
        ).click()
        grouped = assert_selection_invariants(page)
        assert grouped["selectedGroupId"] == group_id
        assert grouped["selectedTrackId"] == group_track["id"]
        assert grouped["selectedTrackKind"] == "group"
        assert page.locator('[data-director-inspector-kind="group"]').count() == 1
        assert page.locator(
            f'[data-director-inspector-track-id="{group_track["id"]}"]'
        ).count() == 1
        results["groupTrackDrivesGroupInspector"] = True

        phase[0] = "path-ownership"
        page.evaluate(
            """() => {
              const state = window.__director_store.getState();
              state.selectObject("director-prop-mug");
              const track = state.timeline.tracks.find(
                (item) => item.objectId === "director-prop-mug"
              );
              if (!track) throw new Error("Mug track missing for path");
              state.createMotionPath("line", track.id);
            }"""
        )
        path_state = assert_selection_invariants(page)
        assert path_state["selectedObjectId"] == "director-prop-mug"
        assert path_state["selectedTrackPathId"] == path_state["selectedMotionPathId"]
        path_anchor = page.evaluate(
            """() => {
              const state = window.__director_store.getState();
              const path = state.timeline.motionPaths.find(
                (item) => item.id === state.timeline.selectedMotionPathId
              );
              return path ? { pathId: path.id, anchorId: path.anchors[0]?.id } : null;
            }"""
        )
        assert path_anchor and path_anchor["anchorId"]
        page.evaluate(
            """(value) => {
              window.__director_store.getState().selectMotionPathAnchor(
                value.pathId,
                value.anchorId
              );
            }""",
            path_anchor,
        )
        anchored = assert_selection_invariants(page)
        assert anchored["selectedMotionPathId"] == path_anchor["pathId"]
        assert anchored["selectedMotionPathAnchorId"] == path_anchor["anchorId"]
        page.evaluate(
            """() => window.__director_store.getState().selectObject("director-prop-table")"""
        )
        switched_path = assert_selection_invariants(page)
        assert switched_path["selectedMotionPathId"] is None
        assert switched_path["selectedMotionPathAnchorId"] is None
        results["pathAndAnchorCannotCrossObjectSelection"] = True

        phase[0] = "finished-path-selection-authority"
        page.evaluate(
            """() => {
              const state = window.__director_store.getState();
              state.selectObject("director-prop-table");
              state.addTimelineTrack("director-prop-table");
              const next = window.__director_store.getState();
              const track = next.timeline.tracks.find(
                (item) => item.objectId === "director-prop-table"
              );
              if (!track) throw new Error("Table track missing for free path");
              next.startMotionPathDrawing("pen", track.id);
              next.appendMotionPathDraftAnchor([0, 0, 0]);
              next.appendMotionPathDraftAnchor([1, 0, 0]);
              next.finishMotionPathDrawing();
            }"""
        )
        finished_path_state = assert_selection_invariants(page)
        assert finished_path_state["selectedObjectId"] == "director-prop-table"
        assert finished_path_state["selectedObjectIds"] == ["director-prop-table"]
        assert finished_path_state["selectedGroupId"] is None
        assert finished_path_state["selectedMotionPathId"] is not None
        assert (
            finished_path_state["selectedTrackPathId"]
            == finished_path_state["selectedMotionPathId"]
        )
        results["finishedPathRestoresCompleteSelectionAuthority"] = True

        phase[0] = "delete-repair"
        page.evaluate(
            """() => {
              const state = window.__director_store.getState();
              state.selectObject("director-prop-mug");
              const track = state.timeline.tracks.find(
                (item) => item.objectId === "director-prop-mug"
              );
              if (!track) throw new Error("Mug track missing for delete");
              state.removeTimelineTrack(track.id);
            }"""
        )
        deleted_track_state = assert_selection_invariants(page)
        assert deleted_track_state["selectedTrackId"] is None
        assert deleted_track_state["selectedMotionPathId"] is None
        page.evaluate(
            """() => {
              const state = window.__director_store.getState();
              state.selectObject("director-prop-mug");
              state.deleteDirectorEntity({
                kind: "DELETE_OBJECT",
                objectId: "director-prop-mug",
              });
            }"""
        )
        deleted_object_state = assert_selection_invariants(page)
        assert "director-prop-mug" not in deleted_object_state["objects"]
        assert deleted_object_state["selectedObjectId"] != "director-prop-mug"
        assert deleted_object_state["selectedTrackId"] is None
        assert deleted_object_state["selectedMotionPathId"] is None
        results["deleteRemovesDanglingSelectionContext"] = True

        phase[0] = "locked-and-history-boundary"
        page.evaluate(
            """() => {
              const state = window.__director_store.getState();
              state.undoDirector();
              state.selectObject("director-prop-mug");
            }"""
        )
        page.wait_for_function(
            "() => window.__director_store.getState().objects.some((item) => item.id === 'director-prop-mug')"
        )
        page.evaluate(
            """() => {
              const state = window.__director_store.getState();
              state.toggleObjectLocked("director-prop-mug");
              state.selectObject("director-prop-mug");
            }"""
        )
        before_locked = state_snapshot(page)
        before_document = before_locked["document"]
        before_history = before_locked["historyPast"]
        page.evaluate(
            """() => {
              window.__director_store.getState().updateObjectTransform(
                "director-prop-mug",
                "position",
                0,
                99
              );
            }"""
        )
        after_locked = state_snapshot(page)
        last_command = page.evaluate(
            """() => {
              const result = window.__director_store.getState().lastCommandResult;
              return result ? {
                disposition: result.disposition,
                reason: result.reason,
              } : null;
            }"""
        )
        assert after_locked["document"] == before_document
        assert after_locked["historyPast"] == before_history
        assert last_command == {
            "disposition": "REJECTED",
            "reason": "DIRECTOR_TARGET_LOCKED",
        }
        results["lockedTargetPreservesDocumentAndHistory"] = True

        phase[0] = "portable-boundary"
        before_selection_only = state_snapshot(page)
        page.evaluate(
            """() => {
              const state = window.__director_store.getState();
              state.selectObject("director-character-lead");
              state.toggleObjectSelection("director-prop-table");
            }"""
        )
        after_selection_only = state_snapshot(page)
        portable = json.loads(after_selection_only["document"] or "{}")
        assert after_selection_only["historyPast"] == before_selection_only["historyPast"]
        assert all("selection" not in key.lower() for key in portable)
        results["selectionOnlyStaysOutsideDocumentHistory"] = True

        phase[0] = "mobile"
        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(150)
        mobile = mobile_bounds(page)
        assert mobile["left"] >= -1
        assert mobile["right"] <= mobile["viewport"] + 1
        results["mobileWorkspaceWithinViewport"] = True

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
        "batch": 88,
        "status": "SCRIPT_RECORDED_PASS",
        "baseUrl": BASE_URL,
        "contract": {
            "scope": "clone-owned Director selection/timeline/transform authority",
            "sourceExact": False,
            "singleSelectionTrackNormalization": True,
            "multiSelectionClearsSingleTargetContext": True,
            "groupTrackNormalization": True,
            "timelineReverseSelection": True,
            "deleteAndRestoreRepair": True,
            "lockedTargetZeroMutation": True,
            "portableDocumentExcludesSelection": True,
        },
        "desktop": results,
        "mobile": {
            "workspaceWithinViewport": results.get("mobileWorkspaceWithinViewport", False)
        },
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
