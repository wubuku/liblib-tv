#!/usr/bin/env python3

"""Verify Batch 83 Director command feedback projection."""

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
    / "liblib-canvas-batch83-2026-08-29"
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


def open_director(page: Page) -> None:
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


def box(page: Page, selector: str) -> dict[str, float]:
    value = page.locator(selector).bounding_box()
    if value is None:
        raise AssertionError(f"missing box: {selector}")
    return value


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
        open_director(page)

        workspace = page.locator("[data-director-workspace]")
        feedback = page.locator("[data-director-command-feedback]")
        assert feedback.get_attribute("role") == "status"
        assert feedback.get_attribute("aria-live") == "polite"
        assert feedback.get_attribute("aria-atomic") == "true"
        assert workspace.get_attribute(
            "data-director-last-disposition"
        ) in ("", "COMMITTED")

        initial_history = page.evaluate(
            "() => window.__director_store.getState().history.past.length"
        )

        phase[0] = "rejected"
        page.evaluate(
            """() => window.__director_store.getState().updateObjectTransform(
              "director-character-lead", "position", 0, Number.NaN
            )"""
        )
        page.wait_for_function(
            """() => document.querySelector(
              '[data-director-command-feedback]'
            )?.getAttribute('data-director-command-feedback-disposition') ===
            'REJECTED'"""
        )
        assert feedback.inner_text() == "输入值无效，未应用修改"
        assert feedback.get_attribute("data-director-command-feedback-reason") == (
            "DIRECTOR_INVALID_VALUE"
        )
        assert (
            page.evaluate(
                "() => window.__director_store.getState().history.past.length"
            )
            == initial_history
        )

        phase[0] = "committed"
        page.evaluate(
            """() => window.__director_store.getState().updateObjectTransform(
              "director-character-lead", "position", 0, 0.25
            )"""
        )
        page.wait_for_function(
            """() => document.querySelector(
              '[data-director-command-feedback]'
            )?.getAttribute('data-director-command-feedback-disposition') ===
            'hidden'"""
        )
        assert (
            page.evaluate(
                "() => window.__director_store.getState().history.past.length"
            )
            == initial_history + 1
        )

        phase[0] = "noop"
        page.evaluate(
            """() => window.__director_store.getState().updateObjectTransform(
              "director-character-lead", "position", 0, 0.25
            )"""
        )
        page.wait_for_function(
            """() => document.querySelector(
              '[data-director-command-feedback]'
            )?.getAttribute('data-director-command-feedback-disposition') ===
            'NOOP'"""
        )
        assert feedback.inner_text() == "内容未发生变化"
        assert (
            page.evaluate(
                "() => window.__director_store.getState().history.past.length"
            )
            == initial_history + 1
        )

        phase[0] = "mobile-geometry"
        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(50)
        header = box(page, "[data-director-header]")
        feedback_box = box(page, "[data-director-command-feedback]")
        assert feedback_box["x"] >= header["x"]
        assert feedback_box["x"] + feedback_box["width"] <= header["x"] + header["width"]
        assert feedback_box["y"] >= header["y"]
        assert feedback_box["y"] + feedback_box["height"] <= header["y"] + header["height"]

        phase[0] = "diagnostics"
        audit = {
            "batch": 83,
            "status": "SCRIPT_RECORDED_PASS",
            "baseUrl": BASE_URL,
            "contract": {
                "scope": "clone-owned Director command outcome feedback",
                "sourceExact": False,
                "genericCommittedSuccess": False,
                "feedbackInHistory": False,
            },
            "desktop": {
                "ariaStatusSurface": True,
                "rejectedVisible": True,
                "committedHidden": True,
                "noopVisible": True,
                "zeroHistoryResidue": True,
            },
            "mobile": {"feedbackWithinHeader": True},
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
        assert audit["diagnostics"] == {
            "consoleErrors": 0,
            "pageErrors": 0,
            "requestFailures": 0,
            "details": [],
        }
        AUDIT_PATH.write_text(
            json.dumps(audit, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        browser.close()


if __name__ == "__main__":
    main()
