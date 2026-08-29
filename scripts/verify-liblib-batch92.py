#!/usr/bin/env python3

"""Verify Batch 92 Director local-resource owner and release boundaries."""

from __future__ import annotations

import base64
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
    / "liblib-canvas-batch92-2026-08-29"
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


def read_resource(page: Page, resource_id: str) -> dict[str, Any]:
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
            "o batch92-triangle",
            "v -0.6 0 0",
            "v 0.6 0 0",
            "v 0 1.2 0",
            "f 1 2 3",
        ]
    ).encode("utf-8")
    data_url = "data:text/plain;base64," + base64.b64encode(obj).decode("ascii")

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
        open_director(page)

        item = {
            "id": "batch92-release-resource",
            "categoryId": "my-models",
            "name": "Batch 92 release",
            "fileName": "batch92-release.obj",
            "dataUrl": data_url,
            "mimeType": "text/plain",
            "sizeBytes": len(obj),
            "lastModified": 1,
            "visual": "box",
            "color": "#7db5d8",
        }

        phase[0] = "materialize-and-lease"
        object_id = page.evaluate(
            """(item) => {
              const state = window.__director_store.getState();
              state.addLocalModelLibraryItem(item);
              return state.addModelLibraryObject(item);
            }""",
            item,
        )
        page.wait_for_function(
            """(resourceId) =>
              window.__director_store.getState().localModelResources[resourceId]?.status === "ready" &&
              window.__director_store.getState().localModelResources[resourceId]?.leaseCount === 1 &&
              window.__director_store.getState().localModelResources[resourceId]?.leases.length === 1""",
            arg=item["id"],
        )
        ready = read_resource(page, item["id"])
        assert ready["activeRequestId"] is None, ready
        assert ready["activeRequestOwner"] is None, ready
        assert ready["leases"][0]["owner"]["projectId"] == page.evaluate(
            "() => window.__director_store.getState().projectId"
        )
        assert object_id in page.evaluate(
            "() => window.__director_store.getState().authoredObjects.map((object) => object.id)"
        )

        phase[0] = "deferred-release"
        page.evaluate(
            """(resourceId) => {
              const state = window.__director_store.getState();
              state.releaseLocalModelResource(resourceId);
            }""",
            item["id"],
        )
        deferred = read_resource(page, item["id"])
        assert deferred["status"] == "ready", deferred
        assert deferred["releaseRequested"] is True, deferred
        assert deferred["leaseCount"] == 1, deferred

        phase[0] = "delete-and-final-release"
        result = page.evaluate(
            """(resourceId) =>
              window.__director_store.getState().removeLocalModelLibraryItem(
                resourceId,
                "CASCADE"
              )""",
            item["id"],
        )
        assert result["disposition"] == "COMMITTED", result
        page.wait_for_function(
            """(resourceId) => {
              const state = window.__director_store.getState();
              const resource = state.localModelResources[resourceId];
              return !state.localModelLibrary.some((item) => item.id === resourceId) &&
                resource?.status === "released" &&
                resource.leaseCount === 0 &&
                resource.releaseRequested === true;
            }""",
            arg=item["id"],
        )
        released = read_resource(page, item["id"])
        assert released["status"] == "released", released
        assert released["leaseCount"] == 0, released
        assert released["leases"] == [], released
        assert object_id not in page.evaluate(
            "() => window.__director_store.getState().authoredObjects.map((object) => object.id)"
        )

        phase[0] = "close"
        page.evaluate(
            """() => {
              const state = window.__director_store.getState();
              if (state.projectOwner) state.closeSession(state.projectOwner);
              window.__libtv_ui_store.getState().closeDirectorDesk();
            }"""
        )
        page.locator("[data-director-workspace]").wait_for(state="hidden")

        audit = {
            "batch": 92,
            "status": "SCRIPT_RECORDED_PASS",
            "baseUrl": BASE_URL,
            "contract": {
                "scope": "clone-owned Director local-resource owner and release lifecycle",
                "sourceExact": False,
                "remoteSync": False,
                "portableBytes": False,
            },
            "desktop": {
                "readyCarriesLease": True,
                "deferredReleasePreservesLease": True,
                "deleteRemovesReference": True,
                "finalLeaseReleaseReachesReleased": True,
                "releasedStateHasNoLeases": True,
            },
            "diagnostics": {
                "consoleErrors": len(
                    [item for item in errors if ":console:" in item]
                ),
                "pageErrors": len(
                    [item for item in errors if ":pageerror:" in item]
                ),
                "requestFailures": len(
                    [item for item in errors if ":requestfailed:" in item]
                ),
                "details": errors,
            },
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
