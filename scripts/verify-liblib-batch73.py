#!/usr/bin/env python3

"""Verify Batch 73 Director async authority and fresh-page integration."""

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
    / "liblib-canvas-batch73-2026-08-27"
    / "runtime-audit.json"
)


def run_pure_verifier() -> dict:
    completed = subprocess.run(
        [
            "node",
            "--disable-warning=MODULE_TYPELESS_PACKAGE_JSON",
            "--experimental-strip-types",
            "scripts/verify-liblib-batch73.mjs",
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


def open_director(page: Page) -> None:
    page.goto(f"{BASE_URL}/?batch73=async-authority", wait_until="networkidle")
    page.wait_for_function(
        """() => Boolean(
          window.__libtv_store &&
          window.__director_store &&
          window.__director_project_registry_snapshot &&
          window.__director_async_authority_snapshot
        )"""
    )
    page.locator("[data-open-director]").click()
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


def director_state(page: Page) -> dict:
    return page.evaluate(
        """() => {
          const state = window.__director_store.getState();
          const authority = window.__director_async_authority_snapshot();
          return {
            projectId: state.projectId,
            sessionId: state.sessionId,
            generation: state.generation,
            captureCount: state.captures.length,
            operationCount: authority.operations.length,
            operationKinds: authority.operations.map(
              (operation) => operation.descriptor.kind
            ),
            operationStatuses: authority.operations.map(
              (operation) => operation.status
            ),
            resourceCount: authority.resources.length,
          };
        }"""
    )


def main() -> None:
    pure = run_pure_verifier()
    browser: dict
    errors: list[str] = []
    with sync_playwright() as playwright:
        browser_instance = playwright.chromium.launch()
        page = browser_instance.new_page(viewport={"width": 1440, "height": 1000})
        errors = attach_errors(page)
        open_director(page)

        baseline_graph = graph_state(page)
        baseline_director = director_state(page)
        page.locator("[data-director-capture]").click()
        page.locator("[data-director-workspace-focus-owner]").wait_for(
            state="visible"
        )
        page.wait_for_function(
            """(before) => {
              const state = window.__director_store.getState();
              return state.captures.length > before;
            }""",
            arg=baseline_director["captureCount"],
        )

        after_capture_graph = graph_state(page)
        after_capture_director = director_state(page)
        assert after_capture_director["captureCount"] == 1
        assert after_capture_director["operationCount"] >= 1
        assert "capture" in after_capture_director["operationKinds"]
        assert "succeeded" in after_capture_director["operationStatuses"]
        assert after_capture_graph == baseline_graph

        page.locator("[data-director-export-trigger]").click()
        page.locator("[data-director-export-panel]").wait_for(state="visible")
        page.locator("[data-director-export-submit]").click()
        page.wait_for_function(
            """() => document.querySelector('[data-director-export-panel]')
              ?.getAttribute('data-director-export-status') === 'success'"""
        )
        exported_graph = graph_state(page)
        exported_director = director_state(page)
        assert exported_graph["nodeCount"] > baseline_graph["nodeCount"]
        assert exported_graph["edgeCount"] > baseline_graph["edgeCount"]
        assert exported_director["operationCount"] >= 2
        assert exported_director["operationKinds"].count("video-export") >= 1
        assert exported_director["resourceCount"] >= 1
        assert all(
            status == "succeeded"
            for status in exported_director["operationStatuses"]
            if status
        )

        browser = {
            "capture": {
                "captureCount": after_capture_director["captureCount"],
                "operationKinds": after_capture_director["operationKinds"],
                "ordinaryGraphUnchanged": after_capture_graph == baseline_graph,
            },
            "export": {
                "graphNodeDelta": exported_graph["nodeCount"]
                - baseline_graph["nodeCount"],
                "graphEdgeDelta": exported_graph["edgeCount"]
                - baseline_graph["edgeCount"],
                "resourceCount": exported_director["resourceCount"],
                "operationKinds": exported_director["operationKinds"],
            },
            "diagnostics": {
                "errors": errors,
                "status": "PASS" if not errors else "FAIL",
            },
        }
        browser_instance.close()

    assert not errors, errors
    audit = {
        "status": "PASS",
        "batch": 73,
        "baseUrl": BASE_URL,
        "pure": pure,
        "browser": browser,
        "screenshots": [],
        "errors": [],
    }
    AUDIT_PATH.write_text(
        json.dumps(audit, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print("Batch 73 Director async authority verification passed.")


if __name__ == "__main__":
    main()
