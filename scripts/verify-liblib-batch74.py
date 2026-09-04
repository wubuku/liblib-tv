# AGED_GATE / HISTORICAL_CONTRACT（Batch 108 归因,2026-09-05）：
# 本 verifier 在基线 86673b6（Batch 96 收口）上同样失败，属既有漂移，
# 非 Batch 97-107 引入。已被 LIBTV_DIRECTOR_CURRENT_VERIFIER_MANIFEST /
# Batch 59、67-96 current gates 取代；处置见
# docs/research/LIBTV_VERIFIER_REPLACEMENT_MAP.md §4.z。
# 运行仍可用于历史快照对照，不能作为当前合同通过依据。
#!/usr/bin/env python3

"""Verify Batch 74 Director durable project persistence."""

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
    / "liblib-canvas-batch74-2026-08-27"
    / "runtime-audit.json"
)


def run_pure_verifier() -> dict:
    completed = subprocess.run(
        [
            "node",
            "--disable-warning=MODULE_TYPELESS_PACKAGE_JSON",
            "--experimental-strip-types",
            "scripts/verify-liblib-batch74.mjs",
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


def open_director(page: Page, query: str) -> None:
    page.goto(f"{BASE_URL}/?{query}", wait_until="networkidle")
    page.wait_for_function(
        """() => Boolean(
          window.__libtv_store &&
          window.__director_store &&
          window.__director_project_persistence_snapshot
        )"""
    )
    page.locator("[data-open-director]").first.click()
    page.locator("[data-director-workspace]").wait_for(state="visible")
    page.locator('canvas[data-director-webgl-canvas="true"]').wait_for(
        state="visible"
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
            nodeCount: canvas?.nodes.length || 0,
            edgeCount: canvas?.edges.length || 0,
            selectedNodeId: state.selectedNodeId,
            historyPast: history.past.length,
          };
        }"""
    )


def director_snapshot(page: Page) -> dict:
    return page.evaluate(
        """() => {
          const state = window.__director_store.getState();
          return {
            owner: state.projectOwner,
            projectId: state.projectId,
            generation: state.generation,
            scene: state.scene,
            authoredObjects: state.authoredObjects,
            objects: state.objects,
            timeline: state.timeline,
            phoneVcam: state.phoneVcam,
            selectedObjectId: state.selectedObjectId,
            viewportPanelsCollapsed: state.viewportPanelsCollapsed,
            persistence: window.__director_project_persistence_snapshot(),
          };
        }"""
    )


def storage_entries(page: Page) -> dict[str, str]:
    return page.evaluate(
        """() => Object.fromEntries(
          Object.keys(localStorage)
            .filter((key) => key.startsWith("liblib-tv-director-project-v1:"))
            .map((key) => [key, localStorage.getItem(key) || ""])
        )"""
    )


def wait_for_persistence_status(page: Page, status: str) -> None:
    page.wait_for_function(
        """(expected) => {
          const snapshot = window.__director_project_persistence_snapshot();
          return snapshot.records.some((record) => record.status === expected);
        }""",
        arg=status,
    )


def main() -> None:
    pure = run_pure_verifier()
    errors: list[str] = []
    browser_result: dict = {}
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        context = browser.new_context(viewport={"width": 1440, "height": 1000})
        page = context.new_page()
        errors.extend(attach_errors(page))
        open_director(page, "batch74=persistence")

        baseline_graph = graph_state(page)
        initial = director_snapshot(page)
        owner_a = initial["owner"]
        assert owner_a is not None
        page.evaluate(
            """() => window.__director_store.getState().updateScene({
              name: "Batch 74 persisted scene"
            })"""
        )
        page.wait_for_function(
            """() => window.__director_store.getState().scene.name ===
              "Batch 74 persisted scene" """
        )
        wait_for_persistence_status(page, "SAVED")
        edited = director_snapshot(page)
        entries_after_edit = storage_entries(page)
        assert len(entries_after_edit) == 1
        key_a, raw_a = next(iter(entries_after_edit.items()))
        envelope_a = json.loads(raw_a)
        assert envelope_a["owner"] == owner_a
        assert envelope_a["document"]["scene"]["name"] == (
            "Batch 74 persisted scene"
        )
        assert "currentTime" not in json.dumps(envelope_a)
        assert "isPlaying" not in json.dumps(envelope_a)
        assert "selectedObjectId" not in json.dumps(envelope_a)
        assert "viewportPanelsCollapsed" not in json.dumps(envelope_a)
        assert "phoneVcam" not in json.dumps(envelope_a)
        assert "data:image" not in raw_a
        assert "blob:" not in raw_a
        assert envelope_a["document"]["captureDescriptors"] == []

        page.reload(wait_until="networkidle")
        page.wait_for_function("() => Boolean(window.__director_store)")
        page.locator("[data-open-director]").first.click()
        page.locator("[data-director-workspace]").wait_for(state="visible")
        page.wait_for_function(
            """() => window.__director_store.getState().scene.name ===
              "Batch 74 persisted scene" """
        )
        restored = director_snapshot(page)
        assert restored["projectId"] == edited["projectId"]
        assert restored["generation"] > edited["generation"]
        assert restored["timeline"]["currentTime"] == 0
        assert restored["timeline"]["isPlaying"] is False
        assert restored["viewportPanelsCollapsed"] is False
        assert restored["phoneVcam"]["status"] == "idle"
        assert restored["phoneVcam"]["sampleCount"] == 0
        assert restored["phoneVcam"]["takeCount"] == 0

        owner_b = {
            "route": "libtv",
            "canvasId": owner_a["canvasId"],
            "sourceNodeId": f'{owner_a["sourceNodeId"]}-batch74-b',
        }
        page.evaluate(
            """(owner) => window.__director_store.getState().openSession(owner)""",
            owner_b,
        )
        page.evaluate(
            """() => window.__director_store.getState().updateScene({
              name: "Batch 74 owner B"
            })"""
        )
        page.wait_for_function(
            """() => window.__director_store.getState().scene.name ===
              "Batch 74 owner B" """
        )
        wait_for_persistence_status(page, "SAVED")
        entries_after_b = storage_entries(page)
        assert len(entries_after_b) == 2
        assert any(
            json.loads(raw)["owner"]["sourceNodeId"] == owner_b["sourceNodeId"]
            for raw in entries_after_b.values()
        )
        page.evaluate(
            """(owner) => window.__director_store.getState().openSession(owner)""",
            owner_a,
        )
        page.wait_for_function(
            """() => window.__director_store.getState().scene.name ===
              "Batch 74 persisted scene" """
        )
        assert graph_state(page) == baseline_graph

        page.evaluate(
            """(key) => localStorage.setItem(key, "{corrupt")""",
            key_a,
        )
        page.reload(wait_until="networkidle")
        page.wait_for_function("() => Boolean(window.__director_store)")
        page.locator("[data-open-director]").first.click()
        page.locator("[data-director-workspace]").wait_for(state="visible")
        page.wait_for_function(
            """() => window.__director_store.getState().scene.name !==
              "Batch 74 persisted scene" """
        )
        rejected = director_snapshot(page)
        assert any(
            record["status"] == "REJECTED"
            and record["reason"] == "CORRUPT_PAYLOAD"
            for record in rejected["persistence"]["records"]
        )
        assert page.evaluate(
            """(key) => localStorage.getItem(key) === "{corrupt" """,
            key_a,
        )

        browser_result["reload"] = {
            "sameProject": restored["projectId"] == edited["projectId"],
            "newSessionGeneration": restored["generation"] > edited["generation"],
            "authoredScene": restored["scene"]["name"],
            "runtimeTime": restored["timeline"]["currentTime"],
            "runtimePlaying": restored["timeline"]["isPlaying"],
        }
        browser_result["ownerIsolation"] = {
            "storageKeyCount": len(entries_after_b),
            "graphUnchanged": graph_state(page) == baseline_graph,
            "ownerBSourceNodeId": owner_b["sourceNodeId"],
        }
        browser_result["corruptPayload"] = {
            "rejectedWithoutReplacement": True,
            "rawPayloadPreserved": True,
        }
        browser_result["serializedBoundary"] = {
            "captureDescriptors": envelope_a["document"]["captureDescriptors"],
            "containsRuntimeOrUiFields": any(
                field in raw_a
                for field in [
                    "currentTime",
                    "isPlaying",
                    "selectedObjectId",
                    "viewportPanelsCollapsed",
                    "phoneVcam",
                    "data:image",
                    "blob:",
                ]
            ),
        }
        context.close()

        failing_context = browser.new_context(
            viewport={"width": 1440, "height": 1000}
        )
        failing_page = failing_context.new_page()
        errors.extend(attach_errors(failing_page))
        open_director(failing_page, "batch74=storage-failure")
        failing_page.evaluate(
            """() => {
              Object.defineProperty(Storage.prototype, "setItem", {
                configurable: true,
                value() { throw new Error("simulated quota"); }
              });
            }"""
        )
        failing_page.evaluate(
            """() => window.__director_store.getState().updateScene({
              name: "Batch 74 memory session"
            })"""
        )
        failing_page.wait_for_function(
            """() => window.__director_store.getState().scene.name ===
              "Batch 74 memory session" """
        )
        failing_snapshot = director_snapshot(failing_page)
        assert failing_snapshot["scene"]["name"] == "Batch 74 memory session"
        assert any(
            record["status"] == "SESSION_ONLY"
            for record in failing_snapshot["persistence"]["records"]
        )
        browser_result["storageFailure"] = {
            "memorySessionPreserved": True,
            "sessionOnly": True,
        }
        failing_context.close()
        browser.close()

    assert not errors, errors
    audit = {
        "status": "PASS",
        "batch": 74,
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
    print("Batch 74 Director persistence verification passed.")


if __name__ == "__main__":
    main()
