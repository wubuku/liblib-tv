#!/usr/bin/env python3

"""Verify Batch 96 Director multi-camera and Shot workflow."""

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
    / "liblib-canvas-batch96-2026-08-29"
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


def clear_director_persistence(page: Page) -> None:
    page.evaluate(
        """() => {
          for (const key of Object.keys(localStorage)) {
            if (key.startsWith("liblib-tv-director-project-v1:")) {
              localStorage.removeItem(key);
            }
          }
          localStorage.removeItem("liblib-tv-director-local-model-library-v1");
        }"""
    )


def open_director(page: Page, query: str) -> dict[str, str]:
    page.goto(f"{BASE_URL}/{query}", wait_until="networkidle")
    wait_for_app(page)
    clear_director_persistence(page)
    page.reload(wait_until="networkidle")
    wait_for_app(page)
    owner = page.evaluate(
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
        owner,
    )
    page.locator("[data-director-workspace]").wait_for(state="visible")
    page.wait_for_function(
        """(owner) => {
          const state = window.__director_store.getState();
          return state.projectOwner?.canvasId === owner.canvasId &&
            state.projectOwner?.sourceNodeId === owner.sourceNodeId &&
            state.projectId !== null &&
            state.sessionId !== null &&
            state.generation !== null &&
            state.projectLifecycle === "ACTIVE";
        }""",
        arg=owner,
    )
    page.locator('canvas[data-director-webgl-canvas="true"]').wait_for(
        state="visible"
    )
    return owner


def director_state(page: Page) -> dict[str, Any]:
    return page.evaluate(
        """() => {
          const state = window.__director_store.getState();
          const raw = state.exportDirectorProject();
          return {
            projectId: state.projectId,
            owner: state.projectOwner,
            activeCameraId: state.activeCameraId,
            activeShotId: state.activeShotId,
            authoredObjects: state.authoredObjects,
            objects: state.objects,
            shots: state.shots,
            captures: state.captures,
            timeline: state.timeline,
            historyPast: state.history.past.length,
            historyFuture: state.history.future.length,
            export: raw ? JSON.parse(raw) : null,
          };
        }"""
    )


def assert_no_horizontal_overflow(page: Page, label: str) -> None:
    dimensions = page.evaluate(
        """() => ({
          document: {
            scrollWidth: document.documentElement.scrollWidth,
            clientWidth: document.documentElement.clientWidth,
          },
          body: {
            scrollWidth: document.body.scrollWidth,
            clientWidth: document.body.clientWidth,
          },
        })"""
    )
    assert (
        dimensions["document"]["scrollWidth"]
        <= dimensions["document"]["clientWidth"] + 1
    ), f"{label} document overflow: {dimensions}"
    assert (
        dimensions["body"]["scrollWidth"] <= dimensions["body"]["clientWidth"] + 1
    ), f"{label} body overflow: {dimensions}"


def assert_reference_integrity(state: dict[str, Any]) -> None:
    object_ids = {item["id"] for item in state["authoredObjects"]}
    camera_ids = {
        item["id"] for item in state["authoredObjects"] if item["kind"] == "camera"
    }
    shot_ids = {item["id"] for item in state["shots"]}
    capture_ids = {item["id"] for item in state["captures"]}
    assert camera_ids
    assert {shot["cameraId"] for shot in state["shots"]} == camera_ids
    assert all(shot["cameraId"] in object_ids for shot in state["shots"])
    memberships: dict[str, str] = {}
    for shot in state["shots"]:
        for capture_id in shot["captureIds"]:
            assert capture_id in capture_ids
            assert capture_id not in memberships
            memberships[capture_id] = shot["id"]
    for capture in state["captures"]:
        if capture["shotId"] is not None:
            assert capture["shotId"] in shot_ids
            assert memberships.get(capture["id"]) == capture["shotId"]
            if capture["cameraId"] is not None:
                shot = next(item for item in state["shots"] if item["id"] == capture["shotId"])
                assert shot["cameraId"] == capture["cameraId"]


def run_desktop(page: Page) -> dict[str, Any]:
    errors, phase = attach_errors(page)
    owner = open_director(page, "?batch96=desktop")
    workspace = page.locator("[data-director-workspace]")
    shot_bar = page.locator("[data-director-shot-bar]")
    canvas = page.locator('canvas[data-director-webgl-canvas="true"]')
    assert shot_bar.is_visible()
    assert shot_bar.locator("[data-director-shot-option]").count() == 1
    assert canvas.evaluate(
        "(element) => element.width > 300 && element.height > 200"
    )
    assert_no_horizontal_overflow(page, "Batch 96 desktop bootstrap")

    phase[0] = "legacy-decode-and-export"
    baseline = director_state(page)
    assert baseline["export"]["shots"]
    assert baseline["export"]["shots"][0]["cameraId"] == baseline["activeCameraId"]
    legacy = dict(baseline["export"])
    legacy.pop("shots", None)
    legacy["scene"] = {**legacy["scene"], "name": "Batch 96 legacy decode"}
    legacy["captureDescriptors"] = [
        {key: value for key, value in item.items() if key != "shotId"}
        for item in legacy["captureDescriptors"]
    ]
    legacy_result = page.evaluate(
        """(raw) =>
          window.__director_store.getState().importDirectorProject(
            JSON.stringify(raw)
          )""",
        legacy,
    )
    assert legacy_result["disposition"] == "COMMITTED", legacy_result
    legacy_state = director_state(page)
    assert legacy_state["shots"]
    assert legacy_state["shots"][0]["startTime"] == 0
    assert legacy_state["shots"][0]["endTime"] == legacy_state["timeline"]["duration"]

    phase[0] = "create-switch-update-history"
    add_result = page.evaluate(
        "() => window.__director_store.getState().addDirectorCamera()"
    )
    assert add_result["disposition"] == "COMMITTED", add_result
    after_add = director_state(page)
    assert len(after_add["shots"]) == 2
    second_shot = next(
        shot for shot in after_add["shots"] if shot["cameraId"] != "director-camera-main"
    )
    assert shot_bar.locator("[data-director-shot-option]").count() == 2
    history_before_select = after_add["historyPast"]
    page.locator(
        f'[data-director-shot-option="{second_shot["id"]}"]'
    ).click()
    page.wait_for_function(
        """(shotId) =>
          window.__director_store.getState().activeShotId === shotId""",
        arg=second_shot["id"],
    )
    selected = director_state(page)
    assert selected["activeCameraId"] == second_shot["cameraId"]
    assert selected["historyPast"] == history_before_select
    assert selected["timeline"]["selectedTrackId"].endswith(
        second_shot["cameraId"]
    )

    history_before_update = selected["historyPast"]
    update_result = page.evaluate(
        """(shotId) =>
          window.__director_store.getState().updateShot(shotId, {
            name: "Batch 96 hero shot",
            startTime: 2,
            endTime: 4,
          })""",
        second_shot["id"],
    )
    assert update_result["disposition"] == "COMMITTED", update_result
    updated = director_state(page)
    updated_shot = next(
        shot for shot in updated["shots"] if shot["id"] == second_shot["id"]
    )
    assert updated_shot["name"] == "Batch 96 hero shot"
    assert updated_shot["startTime"] == 2
    assert updated_shot["endTime"] == 4
    assert updated["historyPast"] == history_before_update + 1
    assert updated["timeline"]["currentTime"] == 2
    no_op = page.evaluate(
        """(shot) => {
          const state = window.__director_store.getState();
          const same = state.updateShot(shot.id, {
            name: shot.name,
            startTime: shot.startTime,
            endTime: shot.endTime,
          });
          const invalid = state.updateShot(shot.id, {
            endTime: shot.startTime,
          });
          return { same, invalid, historyPast: state.history.past.length };
        }""",
        updated_shot,
    )
    assert no_op["same"]["disposition"] == "NOOP", no_op
    assert no_op["invalid"]["disposition"] == "REJECTED", no_op
    assert no_op["historyPast"] == updated["historyPast"]
    undo_result = page.evaluate(
        "() => window.__director_store.getState().undoDirector()"
    )
    assert undo_result["disposition"] == "COMMITTED", undo_result
    undone = director_state(page)
    assert next(shot for shot in undone["shots"] if shot["id"] == second_shot["id"])["name"] != "Batch 96 hero shot"
    redo_result = page.evaluate(
        "() => window.__director_store.getState().redoDirector()"
    )
    assert redo_result["disposition"] == "COMMITTED", redo_result
    assert next(
        shot for shot in director_state(page)["shots"] if shot["id"] == second_shot["id"]
    )["name"] == "Batch 96 hero shot"

    phase[0] = "capture-provenance-and-gallery"
    capture_id = "batch96-capture-desktop"
    page.evaluate(
        """(capture) => window.__director_store.getState().addCapture(capture)""",
        {
            "id": capture_id,
            "dataUrl": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=",
            "cameraId": second_shot["cameraId"],
            "shotId": second_shot["id"],
            "cameraName": "Batch 96 camera",
            "aspectRatio": "16:9",
            "width": 1,
            "height": 1,
            "createdAt": "2026-08-29T00:00:00.000Z",
        },
    )
    captured = director_state(page)
    capture = next(item for item in captured["captures"] if item["id"] == capture_id)
    assert capture["shotId"] == second_shot["id"]
    assert capture_id in updated_shot["captureIds"] or capture_id in next(
        shot for shot in captured["shots"] if shot["id"] == second_shot["id"]
    )["captureIds"]
    assert_reference_integrity(captured)
    page.locator(
        f'[data-director-object-id="{second_shot["cameraId"]}"]'
    ).click()
    page.locator('[data-director-camera-tab="captures"]').click()
    page.locator(
        f'[data-director-capture-group-shot="{second_shot["id"]}"]'
    ).wait_for(state="visible")
    assert page.locator(
        f'[data-director-capture-shot-id="{second_shot["id"]}"]'
    ).count() == 1

    phase[0] = "clipboard-and-delete-repair"
    page.evaluate(
        """(cameraId) => window.__director_store.getState().selectObject(cameraId)""",
        second_shot["cameraId"],
    )
    copied = page.evaluate(
        "() => window.__director_store.getState().copyDirectorSelection()"
    )
    assert copied["disposition"] == "COMMITTED", copied
    before_paste = director_state(page)
    pasted = page.evaluate(
        "() => window.__director_store.getState().pasteDirectorClipboard()"
    )
    assert pasted["disposition"] == "COMMITTED", pasted
    after_paste = director_state(page)
    assert len(after_paste["shots"]) == len(before_paste["shots"]) + 1
    assert len(
        [item for item in after_paste["authoredObjects"] if item["kind"] == "camera"]
    ) == len([item for item in before_paste["authoredObjects"] if item["kind"] == "camera"]) + 1
    assert_reference_integrity(after_paste)

    page.evaluate(
        """(cameraId) => window.__director_store.getState().deleteDirectorEntity({
          kind: "DELETE_OBJECT",
          objectId: cameraId,
        })""",
        second_shot["cameraId"],
    )
    after_delete = director_state(page)
    assert second_shot["cameraId"] not in {
        item["id"] for item in after_delete["authoredObjects"]
    }
    assert second_shot["id"] not in {item["id"] for item in after_delete["shots"]}
    deleted_capture = next(item for item in after_delete["captures"] if item["id"] == capture_id)
    assert deleted_capture["cameraId"] is None
    assert deleted_capture["shotId"] is None
    assert_reference_integrity(after_delete)
    pasted_camera_id = next(
        item["id"]
        for item in after_delete["authoredObjects"]
        if item["kind"] == "camera" and item["id"] != "director-camera-main"
    )
    pasted_delete = page.evaluate(
        """(cameraId) => window.__director_store.getState().deleteDirectorEntity({
          kind: "DELETE_OBJECT",
          objectId: cameraId,
        })""",
        pasted_camera_id,
    )
    assert pasted_delete["disposition"] == "COMMITTED", pasted_delete
    after_pasted_delete = director_state(page)
    assert len(
        [item for item in after_pasted_delete["authoredObjects"] if item["kind"] == "camera"]
    ) == 1
    assert_reference_integrity(after_pasted_delete)
    blocked = page.evaluate(
        """() => {
          const state = window.__director_store.getState();
          return state.deleteDirectorEntity({
            kind: "DELETE_OBJECT",
            objectId: state.activeCameraId,
          });
        }"""
    )
    assert blocked["disposition"] == "REJECTED", blocked
    assert blocked["reason"] == "DIRECTOR_LAST_CAMERA_REQUIRED", blocked

    phase[0] = "export-reload-and-duplicate"
    exported = director_state(page)["export"]
    assert exported["shots"]
    assert all(
        shot["cameraId"] in {item["id"] for item in exported["objects"]}
        for shot in exported["shots"]
    )
    page.locator("[data-close-director]").first.click()
    workspace.wait_for(state="hidden")
    duplicate = page.evaluate(
        """() => {
          const state = window.__libtv_store.getState();
          return state.duplicateCanvas(state.activeCanvasId);
        }"""
    )
    assert duplicate["disposition"] in ("COMMITTED", "COMMITTED_SESSION_ONLY"), duplicate
    assert duplicate["targetCanvasId"]
    assert duplicate["targetProjectIds"]
    duplicate_records = page.evaluate(
        """() => window.__director_project_registry_snapshot().records.map((record) => ({
          projectId: record.identity.projectId,
          shots: record.document.shots,
          objects: record.document.objects,
          owner: record.document.owner,
        }))"""
    )
    copied_records = [
        record for record in duplicate_records if record["projectId"] in duplicate["targetProjectIds"]
    ]
    assert copied_records
    assert all(record["shots"] for record in copied_records)
    assert all(
        shot["cameraId"] in {item["id"] for item in record["objects"]}
        for record in copied_records
        for shot in record["shots"]
    )

    page.evaluate(
        """(owner) => {
          const state = window.__libtv_store.getState();
          state.setActiveCanvas(owner.canvasId);
          window.__libtv_ui_store.getState().openDirectorDesk(
            owner.sourceNodeId,
            owner.canvasId
          );
        }""",
        owner,
    )
    page.locator("[data-director-workspace]").wait_for(state="visible")
    page.wait_for_function(
        "() => window.__director_store.getState().projectLifecycle === 'ACTIVE'"
    )
    reloaded = director_state(page)
    assert reloaded["shots"]
    assert_reference_integrity(reloaded)
    assert_no_horizontal_overflow(page, "Batch 96 desktop final")

    console_errors = [item for item in errors if ":console:" in item]
    page_errors = [item for item in errors if ":pageerror:" in item]
    request_failures = [item for item in errors if ":requestfailed:" in item]
    assert not console_errors, console_errors
    assert not page_errors, page_errors
    assert not request_failures, request_failures
    return {
        "viewport": {"width": 1440, "height": 900},
        "owner": owner,
        "legacyDecode": True,
        "normalizedExport": True,
        "createSwitchUpdate": True,
        "historyUndoRedo": True,
        "captureProvenanceGallery": True,
        "clipboardReferenceSafety": True,
        "cameraDeleteRepair": True,
        "lastCameraBlock": True,
        "wholeProjectDuplicate": True,
        "reloadRestore": True,
        "noHorizontalOverflow": True,
        "diagnostics": {
            "consoleErrors": len(console_errors),
            "pageErrors": len(page_errors),
            "requestFailures": len(request_failures),
            "details": errors,
        },
    }


def run_mobile(page: Page) -> dict[str, Any]:
    errors, phase = attach_errors(page)
    phase[0] = "mobile-bootstrap"
    open_director(page, "?batch96=mobile")
    shot_bar = page.locator("[data-director-shot-bar]")
    assert shot_bar.is_visible()
    assert page.locator("[data-director-shot-option]").count() == 1
    page.locator("button[aria-label='打开属性面板']").click()
    page.locator(
        "[aria-label='属性'][data-director-mobile-panel-state='open']"
    ).wait_for(state="visible")
    assert_no_horizontal_overflow(page, "Batch 96 mobile inspector")
    shot_bar.locator("[data-director-shot-option]").first.click()
    assert_no_horizontal_overflow(page, "Batch 96 mobile shot bar")
    console_errors = [item for item in errors if ":console:" in item]
    page_errors = [item for item in errors if ":pageerror:" in item]
    request_failures = [item for item in errors if ":requestfailed:" in item]
    assert not console_errors, console_errors
    assert not page_errors, page_errors
    assert not request_failures, request_failures
    return {
        "viewport": {"width": 390, "height": 844},
        "shotBar": True,
        "inspectorDrawer": True,
        "noHorizontalOverflow": True,
        "diagnostics": {
            "consoleErrors": len(console_errors),
            "pageErrors": len(page_errors),
            "requestFailures": len(request_failures),
            "details": errors,
        },
    }


def verify_static_contract() -> dict[str, bool]:
    document_source = (
        ROOT / "src/lib/directorProjectDocument.ts"
    ).read_text(encoding="utf-8")
    clipboard_source = (
        ROOT / "src/lib/directorClipboard.ts"
    ).read_text(encoding="utf-8")
    duplicate_source = (
        ROOT / "src/lib/directorWholeProjectDuplicate.ts"
    ).read_text(encoding="utf-8")
    delete_source = (
        ROOT / "src/lib/directorDeletePlanner.ts"
    ).read_text(encoding="utf-8")
    store_source = (ROOT / "src/store/directorStore.ts").read_text(encoding="utf-8")
    desk_source = (
        ROOT / "src/components/director/DirectorDesk.tsx"
    ).read_text(encoding="utf-8")
    inspector_source = (
        ROOT / "src/components/director/DirectorInspector.tsx"
    ).read_text(encoding="utf-8")
    assertions = {
        "portableShotDocument": "DirectorShotRecordV1" in document_source
        and "shots: DirectorShotRecordV1[]" in document_source
        and "deriveDefaultShots" in document_source,
        "legacyCompatibility": "record.shots === undefined" in document_source
        and '["shotId"]' in document_source,
        "clipboardShotRemap": 'kind: "shot"' in clipboard_source
        and "remapShot" in clipboard_source
        and "shots: mapToRecord(shotIds)" in clipboard_source,
        "duplicateShotRemap": "function mapShot" in duplicate_source
        and "shotMap" in duplicate_source
        and "shots: shots as DirectorShotRecordV1[]" in duplicate_source,
        "deleteShotRepair": "deletedShotIds" in delete_source
        and "working.deletedShotIds.add" in delete_source,
        "storeCommands": "selectShot" in store_source
        and "updateShot" in store_source
        and "activeShotId" in store_source,
        "shotBarSelectors": "data-director-shot-bar" in desk_source
        and "data-director-shot-option" in desk_source,
        "shotInspectorSelectors": "data-director-shot-name" in inspector_source
        and "data-director-shot-start" in inspector_source
        and "data-director-shot-end" in inspector_source,
        "shotGallerySelectors": "data-director-capture-group-shot" in inspector_source
        and "data-director-capture-shot-id" in inspector_source,
    }
    assert all(assertions.values()), assertions
    return assertions


def main() -> None:
    static_contract = verify_static_contract()
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        desktop_context = browser.new_context(
            viewport={"width": 1440, "height": 900}
        )
        desktop_result = run_desktop(desktop_context.new_page())
        desktop_context.close()

        mobile_context = browser.new_context(
            viewport={"width": 390, "height": 844}
        )
        mobile_result = run_mobile(mobile_context.new_page())
        mobile_context.close()
        browser.close()

    audit = {
        "batch": 96,
        "date": "2026-08-29",
        "status": "SCRIPT_RECORDED_PASS",
        "baseUrl": BASE_URL,
        "sourceExact": False,
        "contract": {
            "scope": "clone-owned Director multi-camera and Shot workflow",
            "screenshotsWritten": False,
            "screenshotRecognition": False,
            "remoteUpload": False,
            "captureBytesDurable": False,
        },
        "staticContract": static_contract,
        "desktop": desktop_result,
        "mobile": mobile_result,
    }
    AUDIT_PATH.write_text(
        json.dumps(audit, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(audit, ensure_ascii=False, separators=(",", ":")))


if __name__ == "__main__":
    main()
