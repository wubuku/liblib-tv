#!/usr/bin/env python3

"""Verify Batch 82 Director local model materialization and lifecycle."""

from __future__ import annotations

import base64
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
    / "liblib-canvas-batch82-2026-08-29"
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
        "(owner) => JSON.stringify(window.__director_store.getState().projectOwner) === JSON.stringify({route: 'libtv', canvasId: owner.canvasId, sourceNodeId: owner.sourceNodeId})",
        arg=fixture,
    )
    return fixture


def read_resource(page: Page, resource_id: str) -> dict:
    return page.evaluate(
        """(resourceId) => {
          const resource =
            window.__director_store.getState().localModelResources[resourceId];
          if (!resource) throw new Error(`resource missing: ${resourceId}`);
          return resource;
        }""",
        resource_id,
    )


def main() -> None:
    obj = "\n".join(
        [
            "o batch82-triangle",
            "v -0.6 0 0",
            "v 0.6 0 0",
            "v 0 1.2 0",
            "f 1 2 3",
        ]
    )
    valid_data_url = "data:text/plain;base64," + base64.b64encode(
        obj.encode("utf-8")
    ).decode("ascii")
    invalid_data_url = "data:text/plain;base64," + base64.b64encode(
        b"this is not an obj mesh"
    ).decode("ascii")

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
        fixture = open_director(page)

        valid_item = {
            "id": "batch82-valid-obj",
            "categoryId": "my-models",
            "name": "Batch 82 triangle",
            "fileName": "batch82-triangle.obj",
            "dataUrl": valid_data_url,
            "mimeType": "text/plain",
            "sizeBytes": len(obj.encode("utf-8")),
            "lastModified": 1,
            "visual": "box",
            "color": "#7db5d8",
        }
        invalid_item = {
            **valid_item,
            "id": "batch82-invalid-obj",
            "name": "Batch 82 invalid",
            "fileName": "batch82-invalid.obj",
            "dataUrl": invalid_data_url,
        }
        unsupported_item = {
            **valid_item,
            "id": "batch82-unsupported",
            "name": "Batch 82 unsupported",
            "fileName": "batch82-unsupported.gltf",
        }

        phase[0] = "valid-materialization"
        valid_object_id = page.evaluate(
            """(item) => {
              const state = window.__director_store.getState();
              state.addLocalModelLibraryItem(item);
              return state.addModelLibraryObject(item);
            }""",
            valid_item,
        )
        page.wait_for_function(
            """(resourceId) =>
              window.__director_store.getState().localModelResources[resourceId]?.status === "ready" &&
              window.__director_store.getState().localModelResources[resourceId]?.attempt === 1""",
            arg=valid_item["id"],
        )
        valid_resource = read_resource(page, valid_item["id"])
        assert valid_resource["descriptor"]["extension"] == "obj"
        assert valid_resource["descriptor"]["sizeBytes"] == valid_item["sizeBytes"]
        assert valid_resource["status"] == "ready"
        assert valid_object_id in page.evaluate(
            "() => window.__director_store.getState().authoredObjects.map((object) => object.id)"
        )

        page.evaluate(
            """() => {
              const button = document.querySelector(
                '[data-director-transform-mode="translate"]'
              );
              if (!(button instanceof HTMLElement)) return;
              button.click();
            }"""
        )
        page.locator("[data-director-model-library-trigger]").click()
        page.locator('[data-director-model-library-tab="my-models"]').click()
        page.locator(
            f'[data-director-model-library-local-status="ready"]'
        ).wait_for(state="visible")

        phase[0] = "parse-failure"
        invalid_object_id = page.evaluate(
            """(item) => {
              const state = window.__director_store.getState();
              state.addLocalModelLibraryItem(item);
              return state.addModelLibraryObject(item);
            }""",
            invalid_item,
        )
        page.wait_for_function(
            """(resourceId) =>
              window.__director_store.getState().localModelResources[resourceId]?.status === "failed" &&
              window.__director_store.getState().localModelResources[resourceId]?.error === "PARSE_FAILED" """,
            arg=invalid_item["id"],
        )
        invalid_resource = read_resource(page, invalid_item["id"])
        assert invalid_resource["status"] == "failed"
        assert invalid_object_id in page.evaluate(
            "() => window.__director_store.getState().authoredObjects.map((object) => object.id)"
        )
        page.locator(
            f'[data-director-model-library-local-retry][data-director-model-library-local-asset-id="{invalid_item["id"]}"]'
        ).click()
        page.wait_for_function(
            """(resourceId) =>
              window.__director_store.getState().localModelResources[resourceId]?.status === "failed" &&
              window.__director_store.getState().localModelResources[resourceId]?.attempt >= 2""",
            arg=invalid_item["id"],
        )

        phase[0] = "invalid-input"
        before_invalid = page.evaluate(
            "() => ({ library: window.__director_store.getState().localModelLibrary.length, resources: Object.keys(window.__director_store.getState().localModelResources).length })"
        )
        page.evaluate(
            """(item) => window.__director_store.getState().addLocalModelLibraryItem(item)""",
            unsupported_item,
        )
        after_invalid = page.evaluate(
            "() => ({ library: window.__director_store.getState().localModelLibrary.length, resources: Object.keys(window.__director_store.getState().localModelResources).length })"
        )
        assert after_invalid == before_invalid

        phase[0] = "cancel-release"
        cancel_resource_id = "batch82-cancel-only"
        cancel_item = {
            **valid_item,
            "id": cancel_resource_id,
            "name": "Batch 82 cancel only",
            "fileName": "batch82-cancel.obj",
        }
        page.evaluate(
            """(item) => window.__director_store.getState().addLocalModelLibraryItem(item)""",
            cancel_item,
        )
        request_id = page.evaluate(
            """(resourceId) =>
              window.__director_store.getState().startLocalModelResourceLoad(resourceId)""",
            cancel_resource_id,
        )
        assert request_id
        assert page.evaluate(
            """([resourceId, requestId]) =>
              window.__director_store.getState().cancelLocalModelResourceLoad(
                resourceId,
                requestId
              )""",
            [cancel_resource_id, request_id],
        )
        canceled_resource = read_resource(page, cancel_resource_id)
        assert canceled_resource["status"] == "canceled"
        page.evaluate(
            """(resourceId) =>
              window.__director_store.getState().releaseLocalModelResource(resourceId)""",
            cancel_resource_id,
        )
        assert read_resource(page, cancel_resource_id)["status"] == "released"

        phase[0] = "close"
        page.evaluate(
            """(owner) => {
              window.__director_store.getState().closeSession(owner);
              window.__libtv_ui_store.getState().closeDirectorDesk();
            }""",
            fixture,
        )
        page.locator("[data-director-workspace]").wait_for(state="hidden")
        browser.close()

    audit = {
        "batch": 82,
        "status": "SCRIPT_RECORDED_PASS",
        "baseUrl": BASE_URL,
        "contract": {
            "scope": "clone-owned Director local model resource lifecycle",
            "sourceExact": False,
            "remoteSync": False,
            "durableAsset": False,
        },
        "desktop": {
            "validObjMaterialization": True,
            "descriptorProvenance": True,
            "failedParseKeepsObject": True,
            "retryCreatesNewAttempt": True,
            "unsupportedExtensionZeroMutation": True,
            "cancelAndRelease": True,
            "uiStatusFeedback": True,
        },
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
