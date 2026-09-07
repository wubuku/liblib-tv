#!/usr/bin/env python3

"""Verify the final Batch 93 Director desktop/mobile regression boundary."""

from __future__ import annotations

import json
import os
from io import BytesIO
from pathlib import Path
from typing import Any

from PIL import Image, ImageStat
from playwright.sync_api import Locator, Page, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
BASE_URL = os.environ.get("LIBLIB_BASE_URL", "http://localhost:4317")
AUDIT_PATH = (
    ROOT
    / "docs"
    / "research"
    / "liblib-canvas-batch93-2026-08-29"
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
          localStorage.removeItem("liblib-tv-director-local-model-library-v1");
        }"""
    )


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
    page.wait_for_timeout(250)
    return owner


def box(locator: Locator) -> dict[str, float]:
    value = locator.bounding_box()
    assert value is not None, f"missing bounding box: {locator}"
    return value


def assert_nonblank_canvas(canvas: Locator, label: str) -> None:
    image = Image.open(BytesIO(canvas.screenshot())).convert("RGB")
    stat = ImageStat.Stat(image)
    assert max(stat.stddev) > 8, f"{label} has insufficient variance: {stat.stddev}"
    assert max(
        maximum - minimum for minimum, maximum in stat.extrema
    ) > 80, f"{label} has insufficient range: {stat.extrema}"


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


def assert_locator_no_overflow(locator: Locator, label: str) -> None:
    dimensions = locator.evaluate(
        """(element) => ({
          scrollWidth: element.scrollWidth,
          clientWidth: element.clientWidth,
        })"""
    )
    assert (
        dimensions["scrollWidth"] <= dimensions["clientWidth"] + 1
    ), f"{label} overflow: {dimensions}"


def director_snapshot(page: Page) -> dict[str, Any]:
    return page.evaluate(
        """() => {
          const state = window.__director_store.getState();
          return {
            projectId: state.projectId,
            sessionId: state.sessionId,
            generation: state.generation,
            lifecycle: state.projectLifecycle,
            objects: state.objects.length,
            groups: state.groups.length,
            tracks: state.timeline.tracks.length,
            currentTime: state.timeline.currentTime,
            historyPast: state.history.past.length,
            historyFuture: state.history.future.length,
          };
        }"""
    )


def run_desktop(page: Page) -> dict[str, Any]:
    errors, phase = attach_errors(page)
    phase[0] = "desktop-bootstrap"
    page.goto(f"{BASE_URL}/?batch93=desktop", wait_until="networkidle")
    wait_for_app(page)
    clear_persistence(page)
    page.reload(wait_until="networkidle")
    wait_for_app(page)
    owner = open_director(page)

    workspace = page.locator("[data-director-workspace]")
    canvas = page.locator('canvas[data-director-webgl-canvas="true"]')
    tree = page.locator("[data-director-tree]")
    inspector = page.locator("[data-director-inspector]")
    timeline = page.locator("[data-director-timeline]")
    assert workspace.get_attribute("data-director-project-lifecycle") == "ACTIVE"
    assert workspace.get_attribute("data-director-project-id")
    assert workspace.get_attribute("data-director-session-id")
    assert workspace.get_attribute("data-director-generation")
    assert canvas.count() == 1
    assert box(canvas)["width"] > 300
    assert box(canvas)["height"] > 200
    assert_nonblank_canvas(canvas, "Batch 93 desktop Director WebGL canvas")
    assert tree.count() == 1
    assert inspector.count() == 1
    assert timeline.count() == 1
    assert page.locator("[data-director-object-id]").count() >= 5
    assert page.locator("[data-director-track-id]").count() >= 2
    assert_no_horizontal_overflow(page, "Batch 93 desktop")
    desktop_snapshot = director_snapshot(page)

    phase[0] = "desktop-shell"
    toggle = page.locator("[data-director-panels-toggle]")
    toggle.click()
    page.wait_for_function(
        "() => window.__director_store.getState().viewportPanelsCollapsed === true"
    )
    assert workspace.get_attribute("data-director-panels-collapsed") == "true"
    toggle.click()
    page.wait_for_function(
        "() => window.__director_store.getState().viewportPanelsCollapsed === false"
    )
    assert workspace.get_attribute("data-director-panels-collapsed") == "false"

    phase[0] = "desktop-close-reopen"
    page.locator("[data-close-director]").first.click()
    workspace.wait_for(state="hidden")
    page.locator("[data-open-director]").first.click()
    workspace.wait_for(state="visible")
    page.locator('canvas[data-director-webgl-canvas="true"]').wait_for(
        state="visible"
    )
    reopened_snapshot = director_snapshot(page)
    assert reopened_snapshot["lifecycle"] == "ACTIVE"
    assert reopened_snapshot["objects"] == desktop_snapshot["objects"]
    assert reopened_snapshot["tracks"] == desktop_snapshot["tracks"]
    assert_no_horizontal_overflow(page, "Batch 93 desktop reopened")

    result = {
        "viewport": {"width": 1440, "height": 900},
        "owner": owner,
        "workspace": True,
        "webglNonblank": True,
        "objectTree": True,
        "inspector": True,
        "timeline": True,
        "panelsCollapseRestore": True,
        "closeReopen": True,
        "noHorizontalOverflow": True,
        "snapshot": reopened_snapshot,
        "diagnostics": {
            "consoleErrors": len([item for item in errors if ":console:" in item]),
            "pageErrors": len([item for item in errors if ":pageerror:" in item]),
            "requestFailures": len(
                [item for item in errors if ":requestfailed:" in item]
            ),
            "details": errors,
        },
    }
    page.locator("[data-close-director]").first.click()
    workspace.wait_for(state="hidden")
    return result


def run_mobile(page: Page) -> dict[str, Any]:
    errors, phase = attach_errors(page)
    phase[0] = "mobile-bootstrap"
    page.goto(f"{BASE_URL}/?batch93=mobile", wait_until="networkidle")
    wait_for_app(page)
    clear_persistence(page)
    page.reload(wait_until="networkidle")
    wait_for_app(page)
    owner = open_director(page)

    workspace = page.locator("[data-director-workspace]")
    canvas = page.locator('canvas[data-director-webgl-canvas="true"]')
    tree = page.locator("[data-director-tree]")
    inspector = page.locator("[data-director-inspector]")
    timeline = page.locator("[data-director-timeline]")
    assert workspace.get_attribute("data-director-project-lifecycle") == "ACTIVE"
    assert canvas.count() == 1
    assert_nonblank_canvas(canvas, "Batch 93 mobile Director WebGL canvas")
    assert tree.count() == 1
    assert inspector.count() == 1
    assert timeline.count() == 1
    assert page.locator(
        "[data-director-mobile-panel-state='closed']"
    ).count() >= 2
    assert_no_horizontal_overflow(page, "Batch 93 mobile bootstrap")
    assert_locator_no_overflow(tree, "Batch 93 mobile tree")
    assert_locator_no_overflow(inspector, "Batch 93 mobile inspector")

    phase[0] = "mobile-tree"
    page.locator("button[aria-label='打开场景对象']").click()
    page.locator(
        "[aria-label='场景对象'][data-director-mobile-panel-state='open']"
    ).wait_for(state="visible")
    assert_locator_no_overflow(tree, "Batch 93 mobile open tree")
    # Batch 156: 场景对象抽屉在左侧（w-[220px]），点击点取 x=320 避开抽屉与树行拦截（时序 flake）。
    page.locator("button[aria-label='关闭移动端面板']").click(
        position={"x": 320, "y": 400}
    )
    page.locator(
        "[aria-label='场景对象'][data-director-mobile-panel-state='closed']"
    ).wait_for(state="visible")

    phase[0] = "mobile-inspector"
    page.locator("button[aria-label='打开属性面板']").click()
    page.locator(
        "[aria-label='属性'][data-director-mobile-panel-state='open']"
    ).wait_for(state="visible")
    assert_locator_no_overflow(inspector, "Batch 93 mobile open inspector")
    assert_no_horizontal_overflow(page, "Batch 93 mobile open inspector")
    # Batch 156: 属性抽屉在右侧（w-72，x>=102），点击点取 x=56 避开抽屉与行拦截。
    page.locator("button[aria-label='关闭移动端面板']").click(
        position={"x": 56, "y": 400}
    )

    phase[0] = "mobile-close"
    page.locator("[data-close-director]").first.click()
    workspace.wait_for(state="hidden")

    return {
        "viewport": {"width": 390, "height": 844},
        "owner": owner,
        "workspace": True,
        "webglNonblank": True,
        "mobileTreeDrawer": True,
        "mobileInspectorDrawer": True,
        "timeline": True,
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


def verify_static_contract() -> dict[str, bool]:
    desk_source = (
        ROOT / "src/components/director/DirectorDesk.tsx"
    ).read_text(encoding="utf-8")
    tree_source = (
        ROOT / "src/components/director/DirectorObjectTree.tsx"
    ).read_text(encoding="utf-8")
    timeline_source = (
        ROOT / "src/components/director/DirectorTimeline.tsx"
    ).read_text(encoding="utf-8")
    viewport_source = (
        ROOT / "src/components/director/DirectorViewport.tsx"
    ).read_text(encoding="utf-8")
    lifecycle_source = (
        ROOT / "src/lib/directorLocalResourceLifecycle.ts"
    ).read_text(encoding="utf-8")
    assertions = {
        "workspaceDiagnosticSurface": "data-director-project-lifecycle" in desk_source,
        "mobilePanelStateSurface": "data-director-mobile-panel-state" in desk_source,
        "objectTreeSurface": "data-director-tree" in tree_source,
        "timelineSurface": "data-director-timeline" in timeline_source,
        "r3fEventSourceBinding": "eventSource={eventSourceRef}" in viewport_source,
        "ownerScopedResourceLease": "activeRequestOwner" in lifecycle_source
        and "releaseRequested" in lifecycle_source,
    }
    assert all(assertions.values()), assertions
    return assertions


def main() -> None:
    static_contract = verify_static_contract()
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        desktop_context = browser.new_context(viewport={"width": 1440, "height": 900})
        desktop = desktop_context.new_page()
        desktop_result = run_desktop(desktop)
        desktop_context.close()

        mobile_context = browser.new_context(viewport={"width": 390, "height": 844})
        mobile = mobile_context.new_page()
        mobile_result = run_mobile(mobile)
        mobile_context.close()
        browser.close()

    for result in (desktop_result, mobile_result):
        assert result["diagnostics"]["consoleErrors"] == 0, result["diagnostics"]
        assert result["diagnostics"]["pageErrors"] == 0, result["diagnostics"]
        assert result["diagnostics"]["requestFailures"] == 0, result["diagnostics"]

    audit = {
        "batch": 93,
        "status": "SCRIPT_RECORDED_PASS",
        "baseUrl": BASE_URL,
        "sourceExact": False,
        "contract": {
            "scope": "clone-owned Director final desktop/mobile regression",
            "screenshotsWritten": False,
            "screenshotRecognition": False,
            "remoteSync": False,
        },
        "staticContract": static_contract,
        "desktop": desktop_result,
        "mobile": mobile_result,
    }
    AUDIT_PATH.write_text(
        json.dumps(audit, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(audit, ensure_ascii=False, separators=(",", ":")))


if __name__ == "__main__":
    main()
