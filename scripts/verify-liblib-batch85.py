#!/usr/bin/env python3

"""Verify Batch 85 Director selection and object-tree CRUD discoverability."""

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
    / "liblib-canvas-batch85-2026-08-29"
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
    return fixture


def selected_state(page: Page) -> dict:
    return page.evaluate(
        """() => {
          const state = window.__director_store.getState();
          return {
            selectedObjectId: state.selectedObjectId,
            selectedObjectIds: state.selectedObjectIds,
            selectedGroupId: state.selectedGroupId,
            historyPast: state.history.past.length,
            clipboard: Boolean(state.clipboard),
            objectCount: state.objects.length,
          };
        }"""
    )


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
            """() => {
              for (const key of Object.keys(localStorage)) {
                if (key.startsWith("liblib-tv-director-project-v1:")) {
                  localStorage.removeItem(key);
                }
              }
            }"""
        )
        page.reload(wait_until="domcontentloaded")
        wait_for_app(page)
        owner = open_director(page)

        phase[0] = "single-selection-bar"
        tree = page.locator("[data-director-tree]")
        bar = tree.locator("[data-director-selection-toolbar]")
        bar.wait_for(state="visible")
        assert bar.get_attribute("data-director-selection-kind") == "objects"
        assert bar.locator("[data-director-selection-count]").inner_text() == "1 个对象已选"
        assert bar.locator('[data-director-selection-action="copy"]').count() == 1
        assert bar.locator('[data-director-selection-action="delete"]').count() == 1
        assert bar.locator('[data-director-selection-action="clear"]').count() == 1

        phase[0] = "clear-selection"
        history_before_clear = selected_state(page)["historyPast"]
        bar.locator('[data-director-selection-action="clear"]').click()
        page.wait_for_function(
            """() => {
              const state = window.__director_store.getState();
              return state.selectedObjectId === null &&
                state.selectedObjectIds.length === 0 &&
                state.selectedGroupId === null;
            }"""
        )
        assert tree.locator("[data-director-selection-toolbar]").count() == 0
        assert selected_state(page)["historyPast"] == history_before_clear

        phase[0] = "copy-selection"
        page.locator('[data-director-object-id="director-character-lead"]').click()
        copy_bar = tree.locator("[data-director-selection-toolbar]")
        history_before_copy = selected_state(page)["historyPast"]
        copy_bar.locator('[data-director-selection-action="copy"]').click()
        page.wait_for_function(
            "() => Boolean(window.__director_store.getState().clipboard)"
        )
        assert selected_state(page)["historyPast"] == history_before_copy
        assert (
            page.locator("[data-director-command-feedback]").get_attribute(
                "data-director-command-feedback-disposition"
            )
            == "hidden"
        )

        phase[0] = "multi-selection"
        page.evaluate(
            """() => {
              const store = window.__director_store.getState();
              store.addCrowdArray({ rows: 1, columns: 2, spacing: 1 });
              window.__director_store.getState().ungroupSelectedCharacters();
            }"""
        )
        page.wait_for_function(
            """() => window.__director_store.getState().objects.filter(
              (item) => item.kind === "character"
            ).length >= 3 &&
            window.__director_store.getState().groups.length === 0"""
        )
        character_rows = page.locator('[data-director-object-kind="character"]')
        assert character_rows.count() >= 3
        character_rows.nth(0).click()
        character_rows.nth(1).click(modifiers=["Shift"])
        page.wait_for_function(
            "() => window.__director_store.getState().selectedObjectIds.length === 2"
        )
        multi_bar = tree.locator("[data-director-selection-toolbar]")
        assert multi_bar.locator("[data-director-selection-count]").inner_text() == "2 个对象已选"

        phase[0] = "batch-delete"
        objects_before_delete = selected_state(page)["objectCount"]
        history_before_delete = selected_state(page)["historyPast"]
        multi_bar.locator('[data-director-selection-action="delete"]').click()
        page.wait_for_function(
            """(expected) => window.__director_store.getState().objects.length === expected"""
            ,
            arg=objects_before_delete - 2,
        )
        assert selected_state(page)["historyPast"] == history_before_delete + 1
        assert (
            page.locator("[data-director-selection-toolbar]").count() == 0
        )

        phase[0] = "mobile"
        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(100)
        assert page.locator("[data-director-tree]").bounding_box() is not None

        phase[0] = "close"
        page.evaluate(
            """(owner) => {
              window.__director_store.getState().closeSession(owner);
              window.__libtv_ui_store.getState().closeDirectorDesk();
            }""",
            owner,
        )
        page.locator("[data-director-workspace]").wait_for(state="hidden")
        browser.close()

    audit = {
        "batch": 85,
        "status": "SCRIPT_RECORDED_PASS",
        "baseUrl": BASE_URL,
        "contract": {
            "scope": "clone-owned Director object-tree selection and CRUD discoverability",
            "sourceExact": False,
            "clearSelectionChangesDocument": False,
            "copyUsesProjectClipboard": True,
            "batchDeleteUsesReferenceAwareCommand": True,
        },
        "desktop": {
            "singleSelectionBar": True,
            "copyAction": True,
            "clearAction": True,
            "shiftMultiSelection": True,
            "batchDelete": True,
            "zeroHistoryClear": True,
        },
        "mobile": {"treeRemainsDiscoverable": True},
        "diagnostics": {
            "consoleErrors": len([item for item in errors if ":console:" in item]),
            "pageErrors": len([item for item in errors if ":pageerror:" in item]),
            "requestFailures": len(
                [item for item in errors if ":requestfailed:" in item]
            ),
            "details": errors,
        },
    }
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    if errors:
        raise AssertionError("\n".join(errors))
    print(json.dumps(audit, ensure_ascii=False))


if __name__ == "__main__":
    main()
