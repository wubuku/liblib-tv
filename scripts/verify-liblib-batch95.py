#!/usr/bin/env python3

"""Verify the Batch 95 Director canvas-media ingress slice."""

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
    / "liblib-canvas-batch95-2026-08-29"
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


def open_director(page: Page, query: str) -> None:
    page.goto(f"{BASE_URL}/{query}", wait_until="networkidle")
    wait_for_app(page)
    clear_director_persistence(page)
    page.reload(wait_until="networkidle")
    wait_for_app(page)
    page.locator("[data-open-director]").first.click()
    page.locator("[data-director-workspace]").wait_for(state="visible")
    page.locator('canvas[data-director-webgl-canvas="true"]').wait_for(
        state="visible"
    )
    page.wait_for_timeout(240)


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


def open_scene_inspector(page: Page, mobile: bool = False) -> None:
    page.evaluate("() => window.__director_store.getState().selectObject(null)")
    if mobile:
        page.locator("button[aria-label='打开属性面板']").click()
        page.locator("[aria-label='属性'][data-director-mobile-panel-state='open']").wait_for(
            state="visible"
        )
    page.locator("[data-director-panorama-source]").wait_for(state="visible")


def director_export_scene_keys(page: Page) -> list[str]:
    return page.evaluate(
        """() => {
          const raw = window.__director_store.getState().exportDirectorProject();
          if (!raw) return [];
          return Object.keys(JSON.parse(raw).scene);
        }"""
    )


def run_desktop(page: Page) -> dict[str, Any]:
    errors, phase = attach_errors(page)
    phase[0] = "desktop-bootstrap"
    open_director(page, "?batch95=desktop")
    open_scene_inspector(page)
    assert_no_horizontal_overflow(page, "Batch 95 desktop bootstrap")

    source = page.locator("[data-director-panorama-source]")
    option_count = source.locator("option").count()
    assert option_count >= 2, "expected empty option plus at least one image input"
    state = page.locator("[data-director-panorama-runtime]")
    page.wait_for_function(
        """() => document.querySelector(
          "[data-director-panorama-runtime]"
        )?.getAttribute("data-director-panorama-state") === "ready" """
    )
    selected_id = state.get_attribute("data-director-panorama-source-id")
    assert selected_id, "default panorama input should select a source node"
    assert source.input_value() == selected_id
    assert state.get_attribute("data-director-panorama-state") == "ready"

    scene_keys = director_export_scene_keys(page)
    assert "panorama" not in scene_keys, scene_keys

    phase[0] = "desktop-switch-clear"
    second_value = source.locator("option").nth(2).get_attribute("value")
    assert second_value and second_value != selected_id
    source.select_option(second_value)
    page.wait_for_function(
        """(expected) => document.querySelector(
          "[data-director-panorama-runtime]"
        )?.getAttribute("data-director-panorama-source-id") === expected""",
        arg=second_value,
    )
    page.wait_for_function(
        """() => document.querySelector(
          "[data-director-panorama-runtime]"
        )?.getAttribute("data-director-panorama-state") === "ready" """
    )
    page.locator("[data-director-panorama-clear]").click()
    page.wait_for_function(
        """() => document.querySelector(
          "[data-director-panorama-runtime]"
        )?.getAttribute("data-director-panorama-state") === "empty" """
    )
    assert state.get_attribute("data-director-panorama-source-id") == ""

    phase[0] = "desktop-stale-source"
    source_ids = page.evaluate(
        """() => [...document.querySelectorAll(
          "[data-director-panorama-source-option]"
        )].map((element) => element.getAttribute("value")).filter(Boolean)"""
    )
    assert source_ids
    source.select_option(source_ids[0])
    page.wait_for_function(
        """() => document.querySelector(
          "[data-director-panorama-runtime]"
        )?.getAttribute("data-director-panorama-state") === "ready" """
    )
    page.evaluate(
        """(ids) => {
          for (const id of ids) {
            window.__libtv_store.getState().updateNodeData(id, {
              imageUrl: null,
            });
          }
        }""",
        source_ids,
    )
    page.wait_for_function(
        """() => document.querySelector(
          "[data-director-panorama-runtime]"
        )?.getAttribute("data-director-panorama-state") === "empty" """
    )
    assert state.get_attribute("data-director-panorama-source-id") == ""

    return {
        "viewport": {"width": 1440, "height": 900},
        "directImageInputCount": option_count - 1,
        "defaultProjection": True,
        "switchProjection": True,
        "clearProjection": True,
        "staleSourceClears": True,
        "projectExportExcludesSessionProjection": True,
        "noHorizontalOverflow": True,
        "diagnostics": {
            "consoleErrors": len([item for item in errors if ":console:" in item]),
            "pageErrors": len([item for item in errors if ":pageerror:" in item]),
            "requestFailures": len(
                [item for item in errors if ":requestfailed:" in item]
            ),
            "details": errors,
        },
    }


def run_mobile(page: Page) -> dict[str, Any]:
    errors, phase = attach_errors(page)
    phase[0] = "mobile-bootstrap"
    open_director(page, "?batch95=mobile")
    open_scene_inspector(page, mobile=True)
    assert_no_horizontal_overflow(page, "Batch 95 mobile bootstrap")
    source = page.locator("[data-director-panorama-source]")
    assert source.is_visible()
    page.wait_for_function(
        """() => document.querySelector(
          "[data-director-panorama-runtime]"
        )?.getAttribute("data-director-panorama-state") === "ready" """
    )
    assert_no_horizontal_overflow(page, "Batch 95 mobile projection")

    return {
        "viewport": {"width": 390, "height": 844},
        "sceneInspectorInputDiscoverable": True,
        "environmentReady": True,
        "noHorizontalOverflow": True,
        "diagnostics": {
            "consoleErrors": len([item for item in errors if ":console:" in item]),
            "pageErrors": len([item for item in errors if ":pageerror:" in item]),
            "requestFailures": len(
                [item for item in errors if ":requestfailed:" in item]
            ),
            "details": errors,
        },
    }


def run_texture_error(page: Page) -> dict[str, Any]:
    errors, phase = attach_errors(page)
    phase[0] = "texture-error-isolation"
    open_director(page, "?batch95=texture-error")
    open_scene_inspector(page)
    source_ids = page.evaluate(
        """() => [...document.querySelectorAll(
          "[data-director-panorama-source-option]"
        )].map((element) => element.getAttribute("value")).filter(Boolean)"""
    )
    assert source_ids
    object_count = page.evaluate(
        "() => window.__director_store.getState().objects.length"
    )
    page.evaluate(
        """(id) => window.__libtv_store.getState().updateNodeData(id, {
          imageUrl: "data:image/png;base64,not-valid",
        })""",
        source_ids[0],
    )
    state = page.locator("[data-director-panorama-runtime]")
    page.wait_for_function(
        """() => document.querySelector(
          "[data-director-panorama-runtime]"
        )?.getAttribute("data-director-panorama-state") === "error" """
    )
    assert page.locator("[data-director-panorama-status]").get_attribute(
        "data-director-panorama-state"
    ) == "error"
    assert page.locator("[data-director-panorama-status]").inner_text().startswith(
        "环境图片加载失败"
    )
    assert page.evaluate(
        "() => window.__director_store.getState().objects.length"
    ) == object_count
    assert page.locator("[data-director-workspace]").is_visible()
    assert_no_horizontal_overflow(page, "Batch 95 texture error")

    console_errors = [item for item in errors if ":console:" in item]
    page_errors = [item for item in errors if ":pageerror:" in item]
    request_failures = [item for item in errors if ":requestfailed:" in item]
    assert not page_errors, page_errors
    assert not request_failures, request_failures
    assert not console_errors, console_errors
    return {
        "objectCountPreserved": True,
        "workspacePreserved": True,
        "visibleFailureFeedback": True,
        "diagnostics": {
            "consoleErrors": len(console_errors),
            "pageErrors": len(page_errors),
            "requestFailures": len(request_failures),
            "details": errors,
            "consoleErrorsExpected": False,
            "consoleErrorReason": "malformed base64 data URL rejected before TextureLoader",
        },
    }


def verify_static_contract() -> dict[str, bool]:
    ingress_source = (
        ROOT / "src/lib/directorCanvasMediaIngress.ts"
    ).read_text(encoding="utf-8")
    desk_source = (
        ROOT / "src/components/director/DirectorDesk.tsx"
    ).read_text(encoding="utf-8")
    inspector_source = (
        ROOT / "src/components/director/DirectorInspector.tsx"
    ).read_text(encoding="utf-8")
    viewport_source = (
        ROOT / "src/components/director/DirectorViewport.tsx"
    ).read_text(encoding="utf-8")
    media_url_source = (
        ROOT / "src/lib/mediaUrl.ts"
    ).read_text(encoding="utf-8")
    assertions = {
        "typedIngress": "DirectorCanvasMediaInputV1" in ingress_source
        and "collectDirectorCanvasMediaInputs" in ingress_source,
        "directImageBoundary": "edge.target !== directorNodeId" in ingress_source
        and 'node.type !== "image"' in ingress_source,
        "sessionProjection": "selectedPanoramaSourceId" in desk_source
        and "panoramaInput={selectedPanoramaInput}" in desk_source,
        "inspectorSurface": "data-director-panorama-source" in inspector_source
        and "data-director-panorama-clear" in inspector_source,
        "textureLifecycle": "TextureLoader" in viewport_source
        and "loadedTexture.dispose()" in viewport_source,
        "invalidDataUrlPreflight": "isMalformedBase64DataImageUrl" in viewport_source
        and "payload.length % 4 === 1" in media_url_source,
        "nonInteractiveEnvironment": "raycast={() => undefined}" in viewport_source,
        "visibleStatus": "data-director-panorama-status" in inspector_source
        and "环境图片加载失败，其他场景对象仍可用" in inspector_source,
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

        error_context = browser.new_context(
            viewport={"width": 1440, "height": 900}
        )
        error_result = run_texture_error(error_context.new_page())
        error_context.close()
        browser.close()

    for result in (desktop_result, mobile_result):
        assert result["diagnostics"]["consoleErrors"] == 0, result["diagnostics"]
        assert result["diagnostics"]["pageErrors"] == 0, result["diagnostics"]
        assert result["diagnostics"]["requestFailures"] == 0, result["diagnostics"]
    assert (
        error_result["diagnostics"]["consoleErrors"] == 0
    ), error_result["diagnostics"]
    assert error_result["diagnostics"]["pageErrors"] == 0, error_result["diagnostics"]
    assert (
        error_result["diagnostics"]["requestFailures"] == 0
    ), error_result["diagnostics"]

    audit = {
        "batch": 95,
        "date": "2026-08-29",
        "status": "SCRIPT_RECORDED_PASS",
        "baseUrl": BASE_URL,
        "sourceExact": False,
        "contract": {
            "scope": "clone-owned Director canvas image ingress and session-only panorama preview",
            "screenshotsWritten": False,
            "screenshotRecognition": False,
            "remoteUpload": False,
            "projectDocumentMutation": False,
        },
        "staticContract": static_contract,
        "desktop": desktop_result,
        "mobile": mobile_result,
        "textureErrorIsolation": error_result,
    }
    AUDIT_PATH.write_text(
        json.dumps(audit, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(audit, ensure_ascii=False, separators=(",", ":")))


if __name__ == "__main__":
    main()
