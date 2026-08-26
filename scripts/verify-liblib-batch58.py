import json
import os
from pathlib import Path

from playwright.sync_api import Page, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
URL = os.environ.get("LIBLIB_BASE_URL", "http://localhost:3000")
REFERENCE_DIR = ROOT / "docs" / "design-references"
AUDIT_PATH = (
    ROOT
    / "docs"
    / "research"
    / "liblib-canvas-batch58-2026-08-27"
    / "runtime-audit.json"
)
IMAGE_ID = "i-vxeeCnxySa"


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


def assert_no_overflow(page: Page):
    assert page.evaluate(
        "() => document.documentElement.scrollWidth <= document.documentElement.clientWidth"
    )
    assert page.evaluate(
        "() => document.body.scrollWidth <= document.body.clientWidth"
    )


def graph_state(page: Page):
    return page.evaluate(
        """() => {
          const state = window.__libtv_store.getState();
          const canvas = state.getActiveCanvas();
          const history = state.historyByCanvas[state.activeCanvasId] || { past: [], future: [] };
          return {
            activeCanvasId: state.activeCanvasId,
            nodes: (canvas?.nodes || []).map((node) => ({ id: node.id, type: node.type })),
            edges: (canvas?.edges || []).map((edge) => ({
              id: edge.id,
              source: edge.source,
              target: edge.target,
            })),
            selectedNodeIds: state.selectedNodeIds,
            selectedNodeId: state.selectedNodeId,
            pastLength: history.past.length,
            futureLength: history.future.length,
          };
        }"""
    )


def all_graph_data(page: Page):
    return page.evaluate(
        """() => {
          const state = window.__libtv_store.getState();
          return {
            canvases: state.canvases.map((canvas) => ({
              id: canvas.id,
              nodes: canvas.nodes.map((node) => node.id),
              edges: canvas.edges.map((edge) => edge.id),
            })),
            historyByCanvas: Object.fromEntries(
              Object.entries(state.historyByCanvas).map(([id, history]) => [
                id,
                { past: history.past.length, future: history.future.length },
              ])
            ),
          };
        }"""
    )


def ui_state(page: Page):
    return page.evaluate(
        """() => {
          const state = window.__libtv_ui_store.getState();
          return {
            imagePreview: state.imagePreview,
            imageAnnotate: state.imageAnnotate,
            imageElementEdit: state.imageElementEdit,
            activeDirectorNodeId: state.activeDirectorNodeId,
            activeDirectorCanvasId: state.activeDirectorCanvasId,
          };
        }"""
    )


def organize(page: Page):
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(450)
    page.keyboard.press("Alt+Shift+f")
    page.wait_for_timeout(300)


def box(locator):
    result = locator.bounding_box()
    assert result is not None
    return result


def click_visible_or_dom(page: Page, locator):
    rect = box(locator)
    blocked = page.evaluate(
        """({selector, rect}) => {
          const x = Math.max(0, Math.min(window.innerWidth - 1, rect.x + rect.width / 2));
          const y = Math.max(0, Math.min(window.innerHeight - 1, rect.y + rect.height / 2));
          const hit = document.elementFromPoint(x, y);
          const target = document.querySelector(selector);
          return !hit || !target || (hit !== target && !target.contains(hit));
        }""",
        {"selector": locator.get_attribute("data-selector"), "rect": rect},
    )
    if (
        rect["x"] < 0
        or rect["x"] + rect["width"] > page.viewport_size["width"]
        or rect["y"] < 0
        or rect["y"] + rect["height"] > page.viewport_size["height"]
        or blocked
    ):
        locator.evaluate("(element) => element.click()")
    else:
        locator.click()


def click_selector(page: Page, selector: str):
    locator = page.locator(selector)
    assert locator.count() == 1, (selector, locator.count())
    locator.evaluate("(element, value) => element.setAttribute('data-selector', value)", selector)
    click_visible_or_dom(page, locator)


def open_image(page: Page):
    node = page.locator(f'.react-flow__node[data-id="{IMAGE_ID}"]')
    assert node.count() == 1
    node.click(force=True)
    page.wait_for_timeout(180)


def open_preview(page: Page):
    open_image(page)
    click_selector(page, '[data-testid="image-toolbar-preview"]')
    page.locator("[data-image-preview-overlay]").wait_for(state="visible")
    page.wait_for_timeout(120)


def open_annotate(page: Page):
    open_image(page)
    click_selector(page, '[data-testid="image-toolbar-annotate"]')
    page.locator("[data-image-annotate-toolbar]").wait_for(state="visible")
    page.locator("[data-image-annotate-surface]").wait_for(state="visible")
    page.wait_for_timeout(120)


def open_element_edit(page: Page):
    open_image(page)
    click_selector(page, '[data-testid="image-toolbar-interactive-edit"]')
    page.locator("[data-image-element-edit-toolbar]").wait_for(state="visible")
    page.locator("[data-image-element-edit-mode]").wait_for(state="visible")
    page.wait_for_timeout(120)


def open_director(page: Page):
    button = page.locator("[data-open-director]")
    assert button.count() == 1
    source_id = button.locator(
        "xpath=ancestor::div[contains(@class, 'react-flow__node')][1]"
    ).get_attribute("data-id")
    assert source_id
    button.click()
    page.locator("[data-director-workspace]").wait_for(state="visible")
    page.locator('canvas[data-director-webgl-canvas="true"]').wait_for(state="visible")
    page.wait_for_timeout(500)
    return source_id


def delete_owner(page: Page, node_id: str, owner_kind: str):
    before = graph_state(page)
    owner_before = ui_state(page)
    assert owner_before[owner_kind] is not None if owner_kind != "director" else owner_before["activeDirectorNodeId"]
    page.evaluate(
        "(nodeId) => window.__libtv_store.getState().removeNode(nodeId)",
        node_id,
    )
    page.wait_for_timeout(240)
    after = graph_state(page)
    owner_after = ui_state(page)

    assert len(after["nodes"]) == len(before["nodes"]) - 1
    assert after["pastLength"] == before["pastLength"] + 1
    assert after["futureLength"] == before["futureLength"]
    assert owner_after[owner_kind] is None if owner_kind != "director" else owner_after["activeDirectorNodeId"] is None
    assert page.locator(".react-flow__node").count() == len(after["nodes"])
    assert page.locator("[data-image-preview-overlay]").count() == 0
    assert page.locator("[data-image-annotate-toolbar]").count() == 0
    assert page.locator("[data-image-element-edit-toolbar]").count() == 0
    assert page.locator("[data-director-workspace]").count() == 0
    assert_no_overflow(page)

    return {
        "before": before,
        "after": after,
        "owner_before": owner_before,
        "owner_after": owner_after,
    }


def switch_canvas_with_owner(page: Page, open_owner, owner_kind: str):
    open_owner(page)
    before_graph_data = all_graph_data(page)
    before_ui = ui_state(page)
    page.evaluate(
        "() => window.__libtv_store.getState().setActiveCanvas('canvas-1')"
    )
    page.wait_for_timeout(260)
    after_graph_data = all_graph_data(page)
    after_ui = ui_state(page)

    assert after_graph_data == before_graph_data
    assert after_ui["imagePreview"] is None
    assert after_ui["imageAnnotate"] is None
    assert after_ui["imageElementEdit"] is None
    assert after_ui["activeDirectorNodeId"] is None
    assert after_ui["activeDirectorCanvasId"] is None
    assert page.locator("[data-image-preview-overlay]").count() == 0
    assert page.locator("[data-image-annotate-toolbar]").count() == 0
    assert page.locator("[data-image-element-edit-toolbar]").count() == 0
    assert page.locator("[data-director-workspace]").count() == 0
    assert_no_overflow(page)
    assert (
        before_ui[owner_kind] is not None
        if owner_kind != "activeDirectorNodeId"
        else before_ui["activeDirectorNodeId"] is not None
    )
    return {"owner_kind": owner_kind, "before_ui": before_ui, "after_ui": after_ui}


def run_pure(page: Page):
    result = page.evaluate(
        """() => {
          const reconcile = window.__libtv_reconcile_ui_owners;
          return {
            valid: reconcile({
              activeCanvasId: "canvas-a",
              activeNodeIds: ["node-1", "node-2"],
              owners: {
                imagePreview: { canvasId: "canvas-a", nodeId: "node-1" },
                imageAnnotate: { canvasId: "canvas-a", nodeId: "node-2" }
              }
            }),
            invalid: reconcile({
              activeCanvasId: "canvas-a",
              activeNodeIds: ["node-1"],
              owners: {
                imagePreview: { canvasId: "canvas-b", nodeId: "node-1" },
                imageAnnotate: { canvasId: "canvas-a", nodeId: "missing" },
                imageElementEdit: { canvasId: "canvas-a", nodeId: "node-1" },
                director: null
              }
            }),
            nullOnly: reconcile({
              activeCanvasId: "canvas-a",
              activeNodeIds: [],
              owners: {}
            })
          };
        }"""
    )
    assert result["valid"] == {
        "validOwners": ["imagePreview", "imageAnnotate"],
        "invalidOwners": [],
    }
    assert result["invalid"] == {
        "validOwners": ["imageElementEdit"],
        "invalidOwners": ["imagePreview", "imageAnnotate"],
    }
    assert result["nullOnly"] == {"validOwners": [], "invalidOwners": []}
    return result


def run_desktop():
    page_results = {}
    errors = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 929, "height": 874}, device_scale_factor=1)
        errors.extend(attach_errors(page))
        organize(page)
        page_results["pure"] = run_pure(page)
        page.close()

        page = browser.new_page(viewport={"width": 929, "height": 874}, device_scale_factor=1)
        errors.extend(attach_errors(page))
        organize(page)
        open_preview(page)
        page.screenshot(
            path=str(
                REFERENCE_DIR
                / "liblib-clone-batch58-owner-preview-desktop-929-2026-08-27.png"
            )
        )
        page_results["preview_delete"] = delete_owner(page, IMAGE_ID, "imagePreview")
        page.close()

        page = browser.new_page(viewport={"width": 929, "height": 874}, device_scale_factor=1)
        errors.extend(attach_errors(page))
        organize(page)
        open_annotate(page)
        page_results["annotate_delete"] = delete_owner(page, IMAGE_ID, "imageAnnotate")
        page.close()

        page = browser.new_page(viewport={"width": 929, "height": 874}, device_scale_factor=1)
        errors.extend(attach_errors(page))
        organize(page)
        open_element_edit(page)
        page_results["element_edit_delete"] = delete_owner(page, IMAGE_ID, "imageElementEdit")
        page.close()

        page = browser.new_page(viewport={"width": 929, "height": 874}, device_scale_factor=1)
        errors.extend(attach_errors(page))
        organize(page)
        director_id = open_director(page)
        page_results["director_delete"] = delete_owner(page, director_id, "activeDirectorNodeId")
        page.close()

        page = browser.new_page(viewport={"width": 929, "height": 874}, device_scale_factor=1)
        errors.extend(attach_errors(page))
        organize(page)
        page_results["preview_switch"] = switch_canvas_with_owner(
            page, open_preview, "imagePreview"
        )
        page.close()

        page = browser.new_page(viewport={"width": 929, "height": 874}, device_scale_factor=1)
        errors.extend(attach_errors(page))
        organize(page)
        page_results["annotate_switch"] = switch_canvas_with_owner(
            page, open_annotate, "imageAnnotate"
        )
        page.close()

        page = browser.new_page(viewport={"width": 929, "height": 874}, device_scale_factor=1)
        errors.extend(attach_errors(page))
        organize(page)
        page_results["element_edit_switch"] = switch_canvas_with_owner(
            page, open_element_edit, "imageElementEdit"
        )
        page.close()

        page = browser.new_page(viewport={"width": 929, "height": 874}, device_scale_factor=1)
        errors.extend(attach_errors(page))
        organize(page)
        page_results["director_switch"] = switch_canvas_with_owner(
            page, open_director, "activeDirectorNodeId"
        )
        page.close()
        browser.close()
    assert not errors, errors
    return page_results


def run_mobile():
    errors = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=1)
        errors.extend(attach_errors(page))
        organize(page)
        open_preview(page)
        page.screenshot(
            path=str(
                REFERENCE_DIR
                / "liblib-clone-batch58-owner-cleanup-mobile-390-2026-08-27.png"
            )
        )
        result = delete_owner(page, IMAGE_ID, "imagePreview")
        browser.close()
    assert not errors, errors
    return result


def main():
    REFERENCE_DIR.mkdir(parents=True, exist_ok=True)
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 929, "height": 874}, device_scale_factor=1)
        errors = attach_errors(page)
        organize(page)
        pure = run_pure(page)
        browser.close()

    desktop = run_desktop()
    mobile = run_mobile()
    assert not errors, errors

    audit = {
        "url": URL,
        "status": "SCRIPT_RECORDED_PASS",
        "contract": {
            "owner_identity": "canvas_id_plus_node_id",
            "invalid_owner": "canvas_mismatch_or_missing_node",
            "cleanup": "ui_only",
            "graph_history_mutation": "delete_only",
        },
        "pure": pure,
        "desktop": desktop,
        "mobile": mobile,
        "errors": {"console": [], "page": [], "request": []},
    }
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    print(
        "Batch 58 Playwright verification passed: pure owner reconciliation, "
        "preview/annotate/element-edit/Director delete cleanup, active-canvas "
        "switch cleanup, delete-only history mutation, desktop/mobile overflow "
        "and browser diagnostics."
    )


if __name__ == "__main__":
    main()
