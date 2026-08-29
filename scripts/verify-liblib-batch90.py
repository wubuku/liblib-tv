#!/usr/bin/env python3

"""Verify Batch 90 Director session diagnostics and scene command workflow."""

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
    / "liblib-canvas-batch90-2026-08-29"
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


def clear_persistence(page: Page) -> None:
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
        """(owner) => {
          const state = window.__director_store.getState();
          return state.projectOwner?.canvasId === owner.canvasId &&
            state.projectOwner?.sourceNodeId === owner.sourceNodeId &&
            state.projectId !== null &&
            state.sessionId !== null &&
            state.generation !== null &&
            state.projectLifecycle === "ACTIVE";
        }""",
        arg=fixture,
    )
    page.locator('canvas[data-director-webgl-canvas="true"]').wait_for(
        state="visible"
    )
    page.wait_for_timeout(250)
    return fixture


def director_state(page: Page) -> dict[str, Any]:
    return page.evaluate(
        """() => {
          const state = window.__director_store.getState();
          return {
            scene: state.scene,
            projectId: state.projectId,
            sessionId: state.sessionId,
            generation: state.generation,
            lifecycle: state.projectLifecycle,
            outcome: state.sessionOutcome,
            historyPast: state.history.past.length,
            historyFuture: state.history.future.length,
            lastCommand: state.lastCommandResult,
            persisted: window.__director_project_persistence_snapshot(),
          };
        }"""
    )


def assert_no_horizontal_overflow(page: Page, selector: str) -> None:
    overflow = page.locator(selector).evaluate(
        """(element) => ({
          scrollWidth: element.scrollWidth,
          clientWidth: element.clientWidth
        })"""
    )
    assert overflow["scrollWidth"] <= overflow["clientWidth"] + 1, overflow


def run_browser_verifier(page: Page) -> dict[str, Any]:
    errors, phase = attach_errors(page)
    page.goto(f"{BASE_URL}/?batch90=1", wait_until="networkidle")
    wait_for_app(page)
    clear_persistence(page)
    fixture = open_director(page)

    phase[0] = "session-diagnostics"
    workspace = page.locator("[data-director-workspace]")
    baseline = director_state(page)
    assert workspace.get_attribute("data-director-project-lifecycle") == "ACTIVE"
    assert workspace.get_attribute("data-director-session-disposition") in (
        "CREATED",
        "RESTORED",
        "FOCUSED",
    )
    assert workspace.get_attribute("data-director-project-id") == baseline["projectId"]
    assert workspace.get_attribute("data-director-session-id") == baseline["sessionId"]
    assert workspace.get_attribute("data-director-generation") == str(
        baseline["generation"]
    )

    page.locator("[data-director-selection-action='clear']").click()
    page.locator("[data-director-scene-settings]").wait_for(state="visible")

    phase[0] = "scene-draft"
    name_input = page.locator("[data-director-scene-name]")
    original_name = baseline["scene"]["name"]
    history_before_draft = director_state(page)["historyPast"]
    name_input.fill("Batch 90 draft")
    draft_state = director_state(page)
    assert draft_state["scene"]["name"] == original_name
    assert draft_state["historyPast"] == history_before_draft
    assert name_input.input_value() == "Batch 90 draft"

    phase[0] = "scene-commit"
    name_input.press("Enter")
    page.wait_for_function(
        "() => window.__director_store.getState().scene.name === 'Batch 90 draft'"
    )
    committed = director_state(page)
    assert committed["historyPast"] == history_before_draft + 1
    assert committed["lastCommand"]["commandKind"] == "UPDATE_SCENE"
    assert committed["lastCommand"]["disposition"] == "COMMITTED"
    assert committed["lastCommand"]["historyEntries"] == 1
    assert any(
        record["projectId"] == committed["projectId"]
        and record["status"] == "SAVED"
        for record in committed["persisted"]["records"]
    )

    phase[0] = "scene-noop-and-invalid"
    page.evaluate(
        "() => window.__director_store.getState().updateScene({ name: 'Batch 90 draft' })"
    )
    noop = director_state(page)
    assert noop["lastCommand"]["disposition"] == "NOOP"
    assert noop["lastCommand"]["reason"] == "DIRECTOR_COMMAND_NO_CHANGE"
    assert noop["historyPast"] == committed["historyPast"]
    page.evaluate(
        "() => window.__director_store.getState().updateScene({ name: '' })"
    )
    invalid = director_state(page)
    assert invalid["lastCommand"]["disposition"] == "REJECTED"
    assert invalid["lastCommand"]["reason"] == "DIRECTOR_INVALID_VALUE"
    assert invalid["historyPast"] == committed["historyPast"]
    assert invalid["scene"]["name"] == "Batch 90 draft"

    phase[0] = "scene-fields"
    page.locator("[data-director-scene-show-ground]").uncheck()
    page.wait_for_function(
        "() => window.__director_store.getState().scene.showGround === false"
    )
    after_toggle = director_state(page)
    assert after_toggle["historyPast"] == committed["historyPast"] + 1
    page.locator("[data-director-scene-background-color]").fill("#4a4f56")
    page.wait_for_function(
        "() => window.__director_store.getState().scene.backgroundColor === '#4a4f56'"
    )
    after_color = director_state(page)
    assert after_color["historyPast"] == after_toggle["historyPast"] + 1

    phase[0] = "undo-redo"
    page.evaluate("() => window.__director_store.getState().undoDirector()")
    page.wait_for_function(
        "() => window.__director_store.getState().scene.backgroundColor !== '#4a4f56'"
    )
    undone = director_state(page)
    assert undone["scene"]["showGround"] is False
    assert undone["scene"]["backgroundColor"] != "#4a4f56"
    page.evaluate("() => window.__director_store.getState().redoDirector()")
    page.wait_for_function(
        "() => window.__director_store.getState().scene.backgroundColor === '#4a4f56'"
    )
    redone = director_state(page)
    assert redone["scene"]["backgroundColor"] == "#4a4f56"
    assert redone["scene"]["showGround"] is False

    phase[0] = "mobile"
    page.set_viewport_size({"width": 390, "height": 844})
    page.wait_for_timeout(200)
    page.locator("button[aria-label='打开属性面板']").click()
    page.locator("[data-director-scene-settings]").wait_for(state="visible")
    assert_no_horizontal_overflow(page, "[data-director-inspector]")

    return {
        "fixture": fixture,
        "baseline": baseline,
        "draft": draft_state,
        "committed": committed,
        "noop": noop,
        "invalid": invalid,
        "afterToggle": after_toggle,
        "afterColor": after_color,
        "undo": undone,
        "redo": redone,
        "mobileNoHorizontalOverflow": True,
        "diagnostics": {
            "consoleErrors": len(
                [entry for entry in errors if ":console:error:" in entry]
            ),
            "pageErrors": len(
                [entry for entry in errors if ":pageerror:" in entry]
            ),
            "requestFailures": len(
                [entry for entry in errors if ":requestfailed:" in entry]
            ),
            "details": errors,
        },
    }


def main() -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        context = browser.new_context(viewport={"width": 1440, "height": 1000})
        page = context.new_page()
        result = run_browser_verifier(page)
        browser.close()

    assert result["diagnostics"]["consoleErrors"] == 0, result["diagnostics"]
    assert result["diagnostics"]["pageErrors"] == 0, result["diagnostics"]
    assert result["diagnostics"]["requestFailures"] == 0, result["diagnostics"]

    AUDIT_PATH.write_text(
        json.dumps(
            {
                "batch": 90,
                "status": "SCRIPT_RECORDED_PASS",
                "baseUrl": BASE_URL,
                "sourceExact": False,
                **result,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print("Batch 90 Director session and scene command verification passed.")


if __name__ == "__main__":
    main()
