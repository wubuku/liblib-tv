import json
import os
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageStat
from playwright.sync_api import Locator, Page, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
BASE_URL = os.environ.get("LIBLIB_BASE_URL", "http://localhost:3000")
AUDIT_PATH = (
    ROOT
    / "docs"
    / "research"
    / "liblib-canvas-batch59-2026-08-27"
    / "runtime-audit.json"
)


def attach_errors(page: Page):
    errors = []
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


def box(locator: Locator):
    result = locator.bounding_box()
    assert result is not None
    return result


def assert_inside(inner: Locator, outer: Locator):
    inner_box = box(inner)
    outer_box = box(outer)
    assert inner_box["x"] >= outer_box["x"] - 1
    assert inner_box["y"] >= outer_box["y"] - 1
    assert inner_box["x"] + inner_box["width"] <= (
        outer_box["x"] + outer_box["width"] + 1
    )
    assert inner_box["y"] + inner_box["height"] <= (
        outer_box["y"] + outer_box["height"] + 1
    )


def assert_no_overflow(page: Page):
    assert page.evaluate(
        "() => document.documentElement.scrollWidth <= document.documentElement.clientWidth"
    )
    assert page.evaluate(
        "() => document.body.scrollWidth <= document.body.clientWidth"
    )


def assert_nonblank_locator(locator: Locator, label: str):
    image = Image.open(BytesIO(locator.screenshot())).convert("RGB")
    stat = ImageStat.Stat(image)
    assert max(stat.stddev) > 8, f"{label} has insufficient variance: {stat.stddev}"
    assert max(
        maximum - minimum for minimum, maximum in stat.extrema
    ) > 80, f"{label} has insufficient range: {stat.extrema}"


def open_director(page: Page):
    page.goto(f"{BASE_URL}/?batch59=1", wait_until="networkidle")
    page.locator("[data-open-director]").click()
    page.locator("[data-director-workspace]").wait_for(state="visible")
    page.locator('canvas[data-director-webgl-canvas="true"]').wait_for(
        state="visible"
    )
    page.wait_for_timeout(700)


def director_state(page: Page):
    return page.evaluate(
        """() => {
          const state = window.__director_store.getState();
          return {
            objects: state.objects,
            selectedObjectId: state.selectedObjectId,
            selectedObjectIds: state.selectedObjectIds,
            selectedGroupId: state.selectedGroupId,
          };
        }"""
    )


def graph_state(page: Page):
    return page.evaluate(
        """() => {
          const state = window.__libtv_store.getState();
          const canvas = state.getActiveCanvas();
          const history = state.historyByCanvas[state.activeCanvasId] || {
            past: [],
            future: [],
          };
          return {
            nodes: (canvas?.nodes || []).map((node) => node.id),
            edges: (canvas?.edges || []).map((edge) => edge.id),
            pastLength: history.past.length,
            futureLength: history.future.length,
          };
        }"""
    )


def open_library(page: Page):
    trigger = page.locator("[data-director-model-library-trigger]")
    trigger.click()
    panel = page.locator("[data-director-model-library-panel]")
    panel.wait_for(state="visible")
    return panel


def run_desktop(page: Page):
    errors = attach_errors(page)
    open_director(page)
    canvas = page.locator('canvas[data-director-webgl-canvas="true"]')
    assert_nonblank_locator(canvas, "Batch 59 Director WebGL canvas")
    assert_no_overflow(page)
    initial_director = director_state(page)
    initial_graph = graph_state(page)

    panel = open_library(page)
    viewport = page.locator("[data-director-viewport]")
    assert_inside(panel, viewport)
    assert page.locator("[data-director-model-library-tab]").count() == 5
    assert page.locator("[data-director-model-library-card]").count() == 3
    assert (
        page.locator(
            "[data-director-model-library-preview-panel]"
        ).get_attribute("data-director-model-library-preview-asset-id")
        == "proxy-convenience-bottle"
    )

    page.locator("[data-director-model-library-tab='home']").click()
    assert page.locator("[data-director-model-library-card]").count() == 3
    search = page.locator("[data-director-model-library-search]")
    search.fill("台灯")
    assert page.locator("[data-director-model-library-card]").count() == 1
    assert (
        page.locator(
            "[data-director-model-library-card][data-director-model-library-asset-id='proxy-home-lamp']"
        ).count()
        == 1
    )
    assert (
        page.locator("[data-director-model-library-preview-panel]").get_attribute(
            "data-director-model-library-preview-asset-id"
        )
        == "proxy-home-lamp"
    )

    before_preview = director_state(page)
    preview_trigger = page.locator(
        "[data-director-model-library-preview-trigger][data-director-model-library-preview-asset-id='proxy-home-lamp']"
    )
    preview_trigger.click()
    assert page.locator("[data-director-model-library-panel]").count() == 1
    assert director_state(page) == before_preview
    assert (
        page.locator(
            "[data-director-model-library-preview-panel]"
        ).get_attribute("data-director-model-library-preview-asset-id")
        == "proxy-home-lamp"
    )
    preview_add = page.locator("[data-director-model-library-preview-add]")
    assert preview_add.get_attribute("aria-label") == "加入场景 台灯"
    preview_add.click()
    page.locator("[data-director-model-library-panel]").wait_for(state="hidden")
    page.wait_for_timeout(220)

    after_add = director_state(page)
    added_objects = [
        item
        for item in after_add["objects"]
        if item.get("libraryAssetId") == "proxy-home-lamp"
    ]
    assert len(added_objects) == 1
    assert after_add["selectedObjectId"] == added_objects[0]["id"]
    assert after_add["selectedObjectIds"] == [added_objects[0]["id"]]
    assert after_add["selectedGroupId"] is None
    added_id = added_objects[0]["id"]
    tree_row = page.locator(f"[data-director-object-id='{added_id}']")
    assert tree_row.count() == 1
    assert tree_row.get_attribute("data-director-object-selected") == "true"
    assert page.locator("[data-director-inspector]").get_attribute(
        "data-director-inspector-kind"
    ) == "prop"
    assert page.locator(
        '[data-director-transform-field="position"]'
    ).count() == 3
    assert graph_state(page) == initial_graph

    panel = open_library(page)
    page.locator("[data-director-model-library-tab='tools']").click()
    search = page.locator("[data-director-model-library-search]")
    search.fill("不存在的资源")
    assert page.locator("[data-director-model-library-card]").count() == 0
    assert page.locator("[data-director-model-library-no-results]").count() == 1
    assert page.locator("[data-director-model-library-preview-panel]").count() == 0
    search.fill("")
    assert page.locator("[data-director-model-library-card]").count() == 3
    assert page.locator("[data-director-model-library-preview-panel]").count() == 1
    page.keyboard.press("Escape")
    panel.wait_for(state="hidden")

    assert_no_overflow(page)
    assert errors == [], json.dumps(errors, ensure_ascii=False, indent=2)
    return {
        "initial_director_object_count": len(initial_director["objects"]),
        "final_director_object_count": len(after_add["objects"]),
        "added_asset_id": "proxy-home-lamp",
        "graph_unchanged": True,
        "search_and_preview": "pass",
        "empty_result": "pass",
    }


def run_mobile(page: Page):
    errors = attach_errors(page)
    open_director(page)
    canvas = page.locator('canvas[data-director-webgl-canvas="true"]')
    assert_nonblank_locator(canvas, "Batch 59 mobile Director WebGL canvas")
    panel = open_library(page)
    viewport = page.locator("[data-director-viewport]")
    assert_inside(panel, viewport)
    assert page.locator("[data-director-model-library-tab]").count() == 5
    assert page.locator("[data-director-model-library-search]").count() == 1
    assert page.locator("[data-director-model-library-preview-panel]").count() == 1
    assert_no_overflow(page)
    page.keyboard.press("Escape")
    panel.wait_for(state="hidden")
    assert errors == [], json.dumps(errors, ensure_ascii=False, indent=2)
    return {
        "panel_inside_viewport": True,
        "no_overflow": True,
    }


def verify_static_contract():
    catalog_source = (
        ROOT / "src/components/director/directorModelLibrary.ts"
    ).read_text()
    viewport_source = (
        ROOT / "src/components/director/DirectorViewport.tsx"
    ).read_text()
    for source, labels in [
        (
            catalog_source,
            [
                "DirectorModelLibraryQuery",
                "DirectorModelLibrarySelection",
                "filterDirectorModelLibraryItems",
            ],
        ),
        (
            viewport_source,
            [
                "data-director-model-library-search",
                "data-director-model-library-preview-trigger",
                "data-director-model-library-preview-add",
                "data-director-model-library-no-results",
            ],
        ),
    ]:
        for label in labels:
            assert label in source, label


def main():
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    verify_static_contract()
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        desktop = browser.new_page(
            viewport={"width": 1440, "height": 900},
            device_scale_factor=1,
        )
        desktop_result = run_desktop(desktop)
        mobile = browser.new_page(
            viewport={"width": 390, "height": 844},
            device_scale_factor=1,
        )
        mobile_result = run_mobile(mobile)
        browser.close()

    audit = {
        "batch": 59,
        "status": "SCRIPT_RECORDED_PASS",
        "contract": {
            "scope": "clone-owned Director asset library browser/preview/add slice",
            "source_exact": False,
            "real_asset_loading": False,
            "graph_history_mutation": False,
        },
        "desktop": desktop_result,
        "mobile": mobile_result,
        "errors": {"console": [], "page": [], "request": []},
    }
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    print(
        "Batch 59 Playwright verification passed: asset-library search, "
        "preview-only selection, explicit scene insertion, object-tree/Inspector "
        "continuity, empty results, mobile bounds, no-overflow and graph isolation."
    )


if __name__ == "__main__":
    main()
