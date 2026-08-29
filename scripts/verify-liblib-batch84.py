#!/usr/bin/env python3

"""Verify Batch 84 Director lock/visibility/editability behavior."""

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
    / "liblib-canvas-batch84-2026-08-29"
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


def read_object(page: Page, object_id: str) -> dict:
    return page.evaluate(
        """(objectId) => {
          const object = window.__director_store.getState().objects.find(
            (item) => item.id === objectId
          );
          if (!object) throw new Error(`object missing: ${objectId}`);
          return object;
        }""",
        object_id,
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

        phase[0] = "lock-control"
        row = page.locator(
            '[data-director-object-id="director-character-lead"]'
        )
        row.click()
        lock = page.locator(
            '[data-director-object-lock="director-character-lead"]'
        )
        assert lock.get_attribute("data-director-object-locked") == "false"
        history_before_lock = page.evaluate(
            "() => window.__director_store.getState().history.past.length"
        )
        lock.click()
        page.wait_for_function(
            """() => window.__director_store.getState().objects.find(
              (item) => item.id === "director-character-lead"
            )?.locked === true"""
        )
        assert lock.get_attribute("data-director-object-locked") == "true"
        assert lock.get_attribute("aria-label").startswith("解锁")
        assert (
            page.evaluate(
                "() => window.__director_store.getState().history.past.length"
            )
            == history_before_lock + 1
        )

        phase[0] = "inspector-disabled"
        page.locator("[data-director-inspector]").wait_for(state="visible")
        page.locator("[data-director-locked-hint]").wait_for(state="visible")
        assert page.locator(
            '[data-director-transform-field="position"][disabled]'
        ).count() == 3
        assert page.locator(
            '[data-director-transform-field="rotation"][disabled]'
        ).count() == 3
        assert page.locator(
            '[data-director-transform-field="scale"][disabled]'
        ).count() == 3
        assert page.locator(
            '[data-director-inspector-lock]'
        ).get_attribute("aria-label") == "解锁对象"

        phase[0] = "direct-store-guard"
        before = read_object(page, "director-character-lead")
        history_before_reject = page.evaluate(
            "() => window.__director_store.getState().history.past.length"
        )
        result = page.evaluate(
            """() => window.__director_store.getState().updateObjectTransform(
              "director-character-lead", "position", 0, 99
            )"""
        )
        assert result["disposition"] == "REJECTED"
        assert result["reason"] == "DIRECTOR_TARGET_LOCKED"
        after = read_object(page, "director-character-lead")
        assert after["transform"] == before["transform"]
        assert (
            page.evaluate(
                "() => window.__director_store.getState().history.past.length"
            )
            == history_before_reject
        )

        phase[0] = "visibility-remains-editable"
        before_visible = before["visible"]
        page.locator(
            '[data-director-object-id="director-character-lead"] button[aria-label^="隐藏"],'
            '[data-director-object-id="director-character-lead"] button[aria-label^="显示"]'
        ).first.click()
        page.wait_for_function(
            """(expected) => window.__director_store.getState().objects.find(
              (item) => item.id === "director-character-lead"
            )?.visible === expected""",
            arg=not before_visible,
        )
        assert read_object(page, "director-character-lead")["locked"] is True

        phase[0] = "unlock-and-recover"
        lock.click()
        page.wait_for_function(
            """() => window.__director_store.getState().objects.find(
              (item) => item.id === "director-character-lead"
            )?.locked === false"""
        )
        recovered = page.evaluate(
            """() => window.__director_store.getState().updateObjectTransform(
              "director-character-lead", "position", 0, 0.75
            )"""
        )
        assert recovered["disposition"] == "COMMITTED"
        page.wait_for_function(
            """() => window.__director_store.getState().objects.find(
              (item) => item.id === "director-character-lead"
            )?.transform.position[0] === 0.75"""
        )

        phase[0] = "mobile-layout"
        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(100)
        assert lock.bounding_box() is not None

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
        "batch": 84,
        "status": "SCRIPT_RECORDED_PASS",
        "baseUrl": BASE_URL,
        "contract": {
            "scope": "clone-owned Director object lock/visibility/editability",
            "sourceExact": False,
            "lockedSelectionAllowed": True,
            "lockedVisibilityToggleAllowed": True,
            "lockedDeletionAllowed": True,
            "lockedEditingRejected": True,
        },
        "desktop": {
            "treeLockControl": True,
            "inspectorDisabledControls": True,
            "directStoreGuard": True,
            "zeroHistoryRejectedTransform": True,
            "visibilityRemainsEditable": True,
            "unlockRecovery": True,
        },
        "mobile": {"lockControlRemainsDiscoverable": True},
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
