import json
import os
from pathlib import Path

from playwright.sync_api import Page, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
URL = os.environ.get("LIBLIB_BASE_URL", "http://localhost:4317")
REFERENCE_DIR = ROOT / "docs" / "design-references"
AUDIT_PATH = ROOT / "docs" / "research" / "liblib-canvas-batch54-2026-08-26" / "runtime-audit.json"
IMAGE_ID = "i-vxeeCnxySa"


def node(page: Page):
    return page.locator(f'.react-flow__node[data-id="{IMAGE_ID}"]')


def box(locator):
    value = locator.bounding_box()
    assert value is not None
    return value


def center_x(rect):
    return rect["x"] + rect["width"] / 2


def assert_close(actual: float, expected: float, tolerance: float = 1):
    assert abs(actual - expected) <= tolerance, (actual, expected)


def collect_errors(page: Page):
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


def graph_signature(page: Page):
    return page.evaluate(
        """() => ({
          nodes: [...document.querySelectorAll('.react-flow__node')].map((node) => ({
            id: node.getAttribute('data-id'),
            transform: node.style.transform,
          })),
          edges: [...document.querySelectorAll('.react-flow__edge')].map((edge) =>
            edge.getAttribute('data-id')
          ),
          selected: [...document.querySelectorAll('.react-flow__node.selected')].map((node) =>
            node.getAttribute('data-id')
          ),
          viewport: document.querySelector('.react-flow__viewport')?.getAttribute('style'),
        })"""
    )


def organize(page: Page):
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(400)
    page.keyboard.press("Alt+Shift+f")
    page.wait_for_timeout(300)
    return page.get_by_role("button", name="缩放选项").inner_text()


def click_toolbar_button(page: Page, selector: str):
    trigger = page.locator(selector)
    trigger_box = box(trigger)
    viewport_width = page.viewport_size["width"]
    viewport_height = page.viewport_size["height"]
    hit_test_blocked = page.evaluate(
        """({selector, rect}) => {
          const pointX = Math.max(0, Math.min(window.innerWidth - 1, rect.x + rect.width / 2));
          const pointY = Math.max(0, Math.min(window.innerHeight - 1, rect.y + rect.height / 2));
          const hit = document.elementFromPoint(pointX, pointY);
          const target = document.querySelector(selector);
          return !hit || !target || (hit !== target && !target.contains(hit));
        }""",
        {"selector": selector, "rect": trigger_box},
    )
    if (
        trigger_box["x"] < 0
        or trigger_box["x"] + trigger_box["width"] > viewport_width
        or trigger_box["y"] < 0
        or trigger_box["y"] + trigger_box["height"] > viewport_height
        or hit_test_blocked
    ):
        trigger.evaluate("(element) => element.click()")
    else:
        trigger.click()


def open_element_edit(page: Page):
    click_toolbar_button(page, '[data-testid="image-toolbar-interactive-edit"]')
    page.locator("[data-image-element-edit-toolbar]").wait_for(state="visible")
    page.locator("[data-image-element-edit-stage]").wait_for(state="visible")
    page.locator("[data-image-element-edit-record-panel]").wait_for(state="visible")
    page.wait_for_timeout(180)


def assert_element_edit(page: Page, graph_before):
    image_node = node(page)
    node_box = box(image_node)
    media_box = box(image_node.locator("[data-image-node-media]"))
    toolbar = page.locator("[data-image-element-edit-toolbar]")
    toolbar_box = box(toolbar)
    mode = page.locator("[data-image-element-edit-mode]")
    mode_box = box(mode)
    stage = page.locator("[data-image-element-edit-stage]")
    stage_box = box(stage)
    panel = page.locator("[data-image-element-edit-record-panel]")
    panel_box = box(panel)

    assert page.locator("[data-image-toolbar]").count() == 0
    assert page.locator("[data-image-edit-panel]").count() == 0
    assert_close(toolbar_box["width"], 272)
    assert_close(toolbar_box["height"], 44)
    assert_close(center_x(toolbar_box), center_x(node_box))
    assert_close(node_box["y"] - (toolbar_box["y"] + toolbar_box["height"]), 52)

    for key in ("x", "y", "width", "height"):
        assert_close(stage_box[key], media_box[key], 1)
    assert_close(panel_box["width"], 400)
    assert_close(panel_box["height"], 50)
    assert_close(center_x(panel_box), center_x(stage_box))
    assert_close(panel_box["y"] - (stage_box["y"] + stage_box["height"]), 12)
    assert_close(mode_box["height"], stage_box["height"] + 12 + panel_box["height"])

    assert page.get_by_text("标记你想要修改的对象", exact=True).count() == 1
    assert page.get_by_text("编辑内容待添加", exact=True).count() == 1
    assert page.locator("[data-image-element-edit-mask]").count() == 1
    assert page.locator('[data-image-element-edit-tool="point"]').get_attribute("data-active") == "true"
    assert page.locator('[data-image-element-edit-tool="box"]').get_attribute("data-active") == "false"
    assert page.locator('[data-image-element-edit-tool="brush"]').get_attribute("data-active") == "false"
    assert page.locator("[data-image-element-edit-undo]").is_disabled()
    assert page.locator("[data-image-element-edit-generate]").is_disabled()

    brush_size = page.locator('[data-image-element-edit-brush-size] input')
    assert brush_size.get_attribute("min") == "1"
    assert brush_size.get_attribute("max") == "40"
    assert brush_size.input_value() == "4"
    click_toolbar_button(page, '[data-image-element-edit-tool="box"]')
    assert page.locator("[data-image-element-edit-stage]").get_attribute("data-image-element-edit-active-tool") == "box"
    click_toolbar_button(page, '[data-image-element-edit-tool="brush"]')
    assert page.locator("[data-image-element-edit-stage]").get_attribute("data-image-element-edit-active-tool") == "brush"
    brush_size.fill("12")
    assert brush_size.input_value() == "12"
    click_toolbar_button(page, '[data-image-element-edit-tool="point"]')
    assert page.locator("[data-image-element-edit-stage]").get_attribute("data-image-element-edit-active-tool") == "point"

    page.keyboard.press("Delete")
    page.keyboard.press("Control+z")
    page.keyboard.press("Control+y")
    page.keyboard.press("Control+d")
    page.keyboard.press("Tab")
    page.keyboard.down("Space")
    page.keyboard.up("Space")
    assert graph_signature(page) == graph_before
    assert page.locator("[data-image-element-edit-toolbar]").count() == 1
    assert page.locator("[data-image-element-edit-record-panel]").count() == 1

    return {
        "node": node_box,
        "media": media_box,
        "toolbar": toolbar_box,
        "mode": mode_box,
        "stage": stage_box,
        "record_panel": panel_box,
        "brush_size": brush_size.input_value(),
        "tool": page.locator("[data-image-element-edit-stage]").get_attribute("data-image-element-edit-active-tool"),
    }


def run_desktop(page: Page):
    errors = collect_errors(page)
    zoom_label = organize(page)
    image_node = node(page)
    image_node.click(force=True)
    page.wait_for_timeout(180)
    assert page.locator("[data-image-toolbar]").count() == 1
    assert page.locator("[data-image-edit-panel]").count() == 1
    graph_before = graph_signature(page)
    prompt_before = page.get_by_label("图片生成提示词").input_value()

    open_element_edit(page)
    metrics = assert_element_edit(page, graph_before)
    page.screenshot(
        path=str(
            REFERENCE_DIR
            / "liblib-clone-batch54-image-element-edit-active-929-2026-08-26.png"
        )
    )

    page.keyboard.press("Escape")
    page.locator("[data-image-element-edit-toolbar]").wait_for(state="detached")
    assert page.locator("[data-image-element-edit-mode]").count() == 0
    assert page.locator("[data-image-toolbar]").count() == 1
    assert page.locator("[data-image-edit-panel]").count() == 1
    assert graph_signature(page) == graph_before
    assert page.get_by_label("图片生成提示词").input_value() == prompt_before

    open_element_edit(page)
    click_toolbar_button(page, "[data-image-element-edit-close]")
    page.locator("[data-image-element-edit-toolbar]").wait_for(state="detached")
    assert graph_signature(page) == graph_before
    assert not errors, errors
    return {"zoom": zoom_label, "element_edit": metrics}


def run_mobile(page: Page):
    errors = collect_errors(page)
    organize(page)
    node(page).click(force=True)
    page.wait_for_timeout(180)
    graph_before = graph_signature(page)
    open_element_edit(page)
    metrics = assert_element_edit(page, graph_before)
    assert page.evaluate("document.documentElement.scrollWidth <= document.documentElement.clientWidth")
    assert page.evaluate("document.body.scrollWidth <= document.body.clientWidth")
    page.screenshot(
        path=str(
            REFERENCE_DIR
            / "liblib-clone-batch54-image-element-edit-mobile-390-2026-08-26.png"
        )
    )
    click_toolbar_button(page, "[data-image-element-edit-close]")
    page.locator("[data-image-element-edit-toolbar]").wait_for(state="detached")
    assert graph_signature(page) == graph_before
    assert page.locator("[data-image-toolbar]").count() == 1
    assert page.locator("[data-image-edit-panel]").count() == 1
    assert not errors, errors
    return metrics


def main():
    REFERENCE_DIR.mkdir(parents=True, exist_ok=True)
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)

        desktop_page = browser.new_page(viewport={"width": 929, "height": 874}, device_scale_factor=1)
        desktop = run_desktop(desktop_page)
        desktop_page.close()

        mobile_page = browser.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=1)
        mobile = run_mobile(mobile_page)
        mobile_page.close()

        browser.close()

    AUDIT_PATH.write_text(
        json.dumps(
            {
                "url": URL,
                "node_id": IMAGE_ID,
                "contract": {
                    "toolbar_size": [272, 44],
                    "toolbar_to_stage_gap": 52,
                    "stage_to_record_gap": 12,
                    "record_panel_size": [400, 50],
                    "default_tool": "point",
                    "empty_history": "undo_disabled",
                    "standard_surfaces": "absent_while_active",
                    "graph_mutation": "none",
                },
                "desktop": desktop,
                "mobile": mobile,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )

    print(
        "Batch 54 Playwright verification passed: element-edit toolbar replacement, "
        "node-local stage and mask/guide, 400x50 empty record panel, point/box/brush "
        "state, brush-size control, empty undo/generate disabled, keyboard isolation, "
        "Escape/close recovery, graph immutability and mobile overflow."
    )


if __name__ == "__main__":
    main()
