import json
import os
from pathlib import Path

from playwright.sync_api import Page, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
URL = os.environ.get("LIBLIB_BASE_URL", "http://localhost:4317")
AUDIT_PATH = (
    ROOT
    / "docs"
    / "research"
    / "liblib-canvas-batch60-2026-08-26"
    / "runtime-audit.json"
)
IMAGE_A = "i-vxeeCnxySa"
IMAGE_B = "i-dnwoZQ7jsG"
IMAGE_WORLD_WIDTH = 700


def box(locator):
    value = locator.bounding_box()
    assert value is not None
    return value


def center_x(rect):
    return rect["x"] + rect["width"] / 2


def close_enough(actual, expected, tolerance=1):
    assert abs(actual - expected) <= tolerance, (actual, expected)


def errors_for(page: Page):
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
            selectedNodeIds: state.selectedNodeIds,
            selectedNodeId: state.selectedNodeId,
            pastLength: history.past.length,
            futureLength: history.future.length,
          };
        }"""
    )


def prepare(page: Page):
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(450)
    page.keyboard.press("Alt+Shift+f")
    page.wait_for_timeout(320)


def image(page: Page, node_id: str):
    return page.locator(f'.react-flow__node[data-id="{node_id}"]')


def select_image(page: Page, node_id: str):
    image(page, node_id).click(force=True)
    page.wait_for_timeout(160)


def assert_standard_owner(page: Page, node_id: str):
    node_box = box(image(page, node_id))
    toolbar = page.locator("[data-image-toolbar]")
    panel = page.locator("[data-image-edit-panel]")
    assert toolbar.count() == 1
    assert panel.count() == 1
    assert toolbar.get_attribute("data-owner-node-id") == node_id
    assert panel.get_attribute("data-owner-node-id") == node_id
    assert page.locator("[data-image-toolbar]").count() == 1
    assert page.locator("[data-image-edit-panel]").count() == 1

    toolbar_box = box(toolbar)
    panel_box = box(panel)
    zoom = node_box["width"] / IMAGE_WORLD_WIDTH
    close_enough(center_x(toolbar_box), center_x(node_box))
    close_enough(center_x(panel_box), center_x(node_box))
    close_enough(
        node_box["y"] - (toolbar_box["y"] + toolbar_box["height"]),
        10 + 24 * zoom,
    )
    close_enough(
        panel_box["y"] - (node_box["y"] + node_box["height"]),
        16 * zoom,
    )
    close_enough(toolbar_box["width"], 1092.5)
    close_enough(toolbar_box["height"], 49)
    close_enough(panel_box["width"], 660)
    return {
        "node": node_box,
        "toolbar": toolbar_box,
        "panel": panel_box,
        "zoom": zoom,
    }


def assert_pointer_contract(page: Page):
    result = page.evaluate(
        """() => {
          const panel = document.querySelector('[data-image-edit-panel]');
          const section = panel?.querySelector('section');
          const textarea = panel?.querySelector('textarea');
          const button = panel?.querySelector('button');
          return {
            panelPointerEvents: panel ? getComputedStyle(panel).pointerEvents : null,
            sectionPointerEvents: section ? getComputedStyle(section).pointerEvents : null,
            textareaPointerEvents: textarea ? getComputedStyle(textarea).pointerEvents : null,
            buttonPointerEvents: button ? getComputedStyle(button).pointerEvents : null,
          };
        }"""
    )
    assert result == {
        "panelPointerEvents": "none",
        "sectionPointerEvents": "none",
        "textareaPointerEvents": "auto",
        "buttonPointerEvents": "auto",
    }
    return result


def run_desktop(page: Page):
    errors = errors_for(page)
    prepare(page)
    before = graph_state(page)

    select_image(page, IMAGE_A)
    first = assert_standard_owner(page, IMAGE_A)
    pointer_contract = assert_pointer_contract(page)

    # The lower portion of the neighboring image remains visible below A's
    # panel, giving the selection transition a stable content hit target while
    # preserving the real overlap relationship.
    second_node = image(page, IMAGE_B)
    second_box = box(second_node)
    page.mouse.click(
        second_box["x"] + second_box["width"] / 2,
        second_box["y"] + second_box["height"] - 8,
    )
    page.wait_for_timeout(160)
    assert page.locator(".react-flow__node.selected").get_attribute("data-id") == IMAGE_B
    second = assert_standard_owner(page, IMAGE_B)

    # Panel controls remain interactive after the pass-through boundary.
    select_image(page, IMAGE_A)
    textarea = page.get_by_label("图片生成提示词")
    textarea.fill("Batch 60 interaction")
    assert textarea.input_value() == "Batch 60 interaction"
    page.get_by_label("生成图片").click()
    page.wait_for_timeout(60)
    assert page.get_by_text("已创建本地生成任务").count() == 1

    # Active authoring mode replaces the standard pair; it does not add a
    # third node-bound standard overlay.
    page.locator('[data-testid="image-toolbar-annotate"]').click(force=True)
    page.locator("[data-image-annotate-toolbar]").wait_for(state="visible")
    assert page.locator("[data-image-toolbar]").count() == 0
    assert page.locator("[data-image-edit-panel]").count() == 0
    page.keyboard.press("Escape")
    page.locator("[data-image-toolbar]").wait_for(state="visible")
    page.locator("[data-image-edit-panel]").wait_for(state="visible")
    assert_standard_owner(page, IMAGE_A)

    page.locator(".react-flow__pane").click(position={"x": 760, "y": 700})
    page.wait_for_timeout(100)
    assert page.locator("[data-image-toolbar]").count() == 0
    assert page.locator("[data-image-edit-panel]").count() == 0
    assert page.locator(".react-flow__node.selected").count() == 0
    assert graph_state(page) == before
    assert page.evaluate(
        "() => document.documentElement.scrollWidth <= document.documentElement.clientWidth"
    )
    assert page.evaluate(
        "() => document.body.scrollWidth <= document.body.clientWidth"
    )
    assert errors == [], json.dumps(errors, ensure_ascii=False, indent=2)

    return {
        "initial_graph": before,
        "first_owner": IMAGE_A,
        "second_owner": IMAGE_B,
        "first": first,
        "second": second,
        "pointer_contract": pointer_contract,
        "graph_unchanged": True,
        "no_overflow": True,
    }


def run_mobile(page: Page):
    errors = errors_for(page)
    prepare(page)
    select_image(page, IMAGE_A)
    metrics = assert_standard_owner(page, IMAGE_A)
    assert_pointer_contract(page)
    page.keyboard.press("Escape")
    assert page.locator("[data-image-toolbar]").count() == 0
    assert page.locator("[data-image-edit-panel]").count() == 0
    assert page.evaluate(
        "() => document.documentElement.scrollWidth <= document.documentElement.clientWidth"
    )
    assert page.evaluate(
        "() => document.body.scrollWidth <= document.body.clientWidth"
    )
    assert errors == [], json.dumps(errors, ensure_ascii=False, indent=2)
    return {"metrics": metrics, "no_overflow": True}


def main():
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        desktop_page = browser.new_page(
            viewport={"width": 929, "height": 874},
            device_scale_factor=1,
        )
        desktop = run_desktop(desktop_page)
        desktop_page.close()

        mobile_page = browser.new_page(
            viewport={"width": 390, "height": 844},
            device_scale_factor=1,
        )
        mobile = run_mobile(mobile_page)
        mobile_page.close()
        browser.close()

    audit = {
        "batch": 60,
        "status": "SCRIPT_RECORDED_PASS",
        "contract": {
            "scope": "clone-owned standard image double-overlay owner and hit-testing boundary",
            "source_exact_pointer_hit_testing": False,
            "toolbar_top_gap": "10 + 24 * zoom",
            "panel_bottom_gap": "16 * zoom",
            "graph_mutation": False,
        },
        "desktop": desktop,
        "mobile": mobile,
        "errors": {"console": [], "page": [], "request": []},
    }
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    print(
        "Batch 60 Playwright verification passed: standard image overlay owner "
        "continuity, geometry invariants, pointer boundary, panel controls, "
        "active-tool replacement, selection cleanup, mobile bounds and diagnostics."
    )


if __name__ == "__main__":
    main()
