import json
import os
from pathlib import Path

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
BASE_URL = os.environ.get("LIBLIB_BASE_URL", "http://localhost:4317")
AUDIT_PATH = (
    ROOT
    / "docs"
    / "research"
    / "liblib-canvas-batch81-2026-08-29"
    / "runtime-audit.json"
)


def attach_errors(page):
    errors = []
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


def open_director(page):
    page.goto(f"{BASE_URL}/?batch81=1", wait_until="networkidle")
    page.locator("[data-open-director]").click()
    page.locator("[data-director-workspace]").wait_for(state="visible")
    page.locator('canvas[data-director-webgl-canvas="true"]').wait_for(
        state="visible"
    )
    page.wait_for_timeout(500)


def state_snapshot(page):
    return page.evaluate(
        """() => {
          const state = window.__director_store.getState();
          const graph = window.__libtv_store.getState();
          const canvas = graph.getActiveCanvas();
          const graphHistory = graph.historyByCanvas[graph.activeCanvasId] || {
            past: [], future: []
          };
          return {
            owner: state.projectOwner,
            projectId: state.projectId,
            objects: state.authoredObjects.map((item) => ({
              id: item.id,
              name: item.name,
              kind: item.kind,
              transform: item.transform,
            })),
            activeCameraId: state.activeCameraId,
            aspectRatio: state.aspectRatio,
            timelineDuration: state.timeline.duration,
            timelineTime: state.timeline.currentTime,
            isPlaying: state.timeline.isPlaying,
            captures: state.captures,
            historyPast: state.history.past.length,
            historyFuture: state.history.future.length,
            clipboard: state.clipboard,
            graphNodes: (canvas?.nodes || []).map((node) => node.id),
            graphEdges: (canvas?.edges || []).map((edge) => edge.id),
            graphHistoryPast: graphHistory.past.length,
            graphHistoryFuture: graphHistory.future.length,
          };
        }"""
    )


def run(page):
    errors = attach_errors(page)
    open_director(page)
    workspace = page.locator("[data-director-workspace]")
    assert page.locator("[data-director-project-export]").count() == 1
    assert page.locator("[data-director-project-import]").count() == 1
    assert page.locator("[data-director-project-import-input]").count() == 1

    page.evaluate(
        """() => window.__director_store.getState().updateObjectTransform(
          "director-character-lead", "position", 0, 4.5
        )"""
    )
    page.wait_for_timeout(120)
    original = state_snapshot(page)
    exported = page.evaluate(
        "() => window.__director_store.getState().exportDirectorProject()"
    )
    assert isinstance(exported, str)
    exported_document = json.loads(exported)
    assert exported_document["owner"] == original["owner"]
    assert all(
        "data:" not in json.dumps(item)
        and "blob:" not in json.dumps(item)
        for item in exported_document["resourceRefs"]
    )
    assert "data:" not in exported
    assert "blob:" not in exported

    page.evaluate(
        """() => window.__director_store.getState().openSession({
          route: "libtv",
          canvasId: "batch81-target-canvas",
          sourceNodeId: "batch81-target-node"
        })"""
    )
    page.wait_for_timeout(120)
    target_before = state_snapshot(page)
    assert target_before["owner"]["sourceNodeId"] == "batch81-target-node"

    result = page.evaluate(
        """(raw) => window.__director_store.getState().importDirectorProject(raw)""",
        exported,
    )
    assert result["disposition"] == "COMMITTED", result
    imported = state_snapshot(page)
    assert imported["owner"]["sourceNodeId"] == "batch81-target-node"
    assert imported["owner"]["canvasId"] == "batch81-target-canvas"
    assert imported["projectId"] == target_before["projectId"]
    assert imported["objects"] == original["objects"]
    assert imported["aspectRatio"] == original["aspectRatio"]
    assert imported["timelineDuration"] == original["timelineDuration"]
    assert imported["timelineTime"] == 0
    assert imported["isPlaying"] is False
    assert imported["captures"] == []
    assert imported["clipboard"] is None
    assert imported["historyPast"] == target_before["historyPast"] + 1
    assert imported["graphNodes"] == target_before["graphNodes"]
    assert imported["graphEdges"] == target_before["graphEdges"]
    assert imported["graphHistoryPast"] == target_before["graphHistoryPast"]
    assert page.locator(
        "[data-director-project-io-feedback]"
    ).count() == 1

    undo = page.evaluate(
        "() => window.__director_store.getState().undoDirector()"
    )
    assert undo["disposition"] == "COMMITTED", undo
    undone = state_snapshot(page)
    assert undone["objects"] != imported["objects"], json.dumps(
        {
            "target_before": target_before,
            "imported": imported,
            "undone": undone,
        },
        ensure_ascii=False,
        indent=2,
    )
    assert undone["historyFuture"] == 1

    redo = page.evaluate(
        "() => window.__director_store.getState().redoDirector()"
    )
    assert redo["disposition"] == "COMMITTED", redo
    redone = state_snapshot(page)
    assert redone["objects"] == imported["objects"]
    assert redone["captures"] == []

    ui_document = json.loads(exported)
    ui_document["scene"]["name"] = "Batch 81 UI import"
    ui_document["objects"][0]["transform"]["position"][0] = 7.25
    before_ui_import = state_snapshot(page)
    page.locator("[data-director-project-import-input]").set_input_files(
        {
            "name": "batch81-director-project.json",
            "mimeType": "application/json",
            "buffer": json.dumps(
                ui_document, ensure_ascii=False
            ).encode("utf-8"),
        }
    )
    page.wait_for_timeout(160)
    ui_imported = state_snapshot(page)
    assert (
        workspace.get_attribute("data-director-project-io-status")
        == "success"
    )
    assert (
        workspace.get_attribute("data-director-project-io-message")
        == "项目已导入"
    )
    assert ui_imported["objects"][0]["transform"]["position"][0] == 7.25
    assert ui_imported["historyPast"] == before_ui_import["historyPast"] + 1
    assert ui_imported["graphNodes"] == before_ui_import["graphNodes"]
    assert ui_imported["graphEdges"] == before_ui_import["graphEdges"]

    same_payload = page.evaluate(
        "() => window.__director_store.getState().exportDirectorProject()"
    )
    before_noop = state_snapshot(page)
    noop = page.evaluate(
        """(raw) => window.__director_store.getState().importDirectorProject(raw)""",
        same_payload,
    )
    assert noop["disposition"] == "NOOP", noop
    after_noop = state_snapshot(page)
    assert after_noop["historyPast"] == before_noop["historyPast"]
    assert after_noop["objects"] == before_noop["objects"]

    before_invalid = state_snapshot(page)
    invalid = page.evaluate(
        """() => window.__director_store.getState().importDirectorProject(
          JSON.stringify({ schemaVersion: 999 })
        )"""
    )
    assert invalid["disposition"] == "REJECTED", invalid
    after_invalid = state_snapshot(page)
    assert after_invalid["objects"] == before_invalid["objects"]
    assert after_invalid["projectId"] == before_invalid["projectId"]
    assert after_invalid["historyPast"] == before_invalid["historyPast"]
    assert after_invalid["graphNodes"] == before_invalid["graphNodes"]
    assert after_invalid["graphEdges"] == before_invalid["graphEdges"]

    with page.expect_download() as download_info:
        page.locator("[data-director-project-export]").click()
    download = download_info.value
    assert download.suggested_filename.endswith(".json")
    download_path = download.path()
    assert download_path is not None
    downloaded = Path(download_path).read_text()
    assert json.loads(downloaded)["schemaVersion"] == 1
    assert "data:" not in downloaded
    assert "blob:" not in downloaded

    assert workspace.get_attribute("data-director-project-io-status") in (
        "success",
        "error",
    )
    assert errors == [], json.dumps(errors, ensure_ascii=False, indent=2)
    return {
        "owner_rebound": True,
        "entity_ids_preserved": True,
        "capture_runtime_ui_excluded": True,
        "import_history_undo_redo": True,
        "file_input_workflow": True,
        "same_document_noop": True,
        "invalid_import_zero_partial": True,
        "download_round_trip": True,
        "ordinary_graph_unchanged": True,
    }


def main():
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(
            viewport={"width": 1440, "height": 900},
            device_scale_factor=1,
        )
        result = run(page)
        browser.close()

    audit = {
        "batch": 81,
        "status": "SCRIPT_RECORDED_PASS",
        "baseUrl": BASE_URL,
        "contract": {
            "scope": "clone-owned Director strict project JSON import/export",
            "source_exact": False,
            "remote_sync": False,
            "real_asset_materialization": False,
        },
        "desktop": result,
        "errors": [],
    }
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    print(
        "Batch 81 Playwright verification passed: strict Director project "
        "import/export, owner rebind, history undo/redo, invalid zero-partial, "
        "download round-trip and graph isolation."
    )


if __name__ == "__main__":
    main()
