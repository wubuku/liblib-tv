import json
import os
from pathlib import Path

from playwright.sync_api import Page, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
URL = os.environ.get("LIBLIB_BASE_URL", "http://localhost:4317")
REFERENCE_DIR = ROOT / "docs" / "design-references"
AUDIT_PATH = ROOT / "docs" / "research" / "liblib-canvas-batch53-2026-08-26" / "runtime-audit.json"
IMAGE_ID = "i-vxeeCnxySa"


def node(page: Page):
    return page.locator(f'.react-flow__node[data-id="{IMAGE_ID}"]')


def box(locator):
    value = locator.bounding_box()
    assert value is not None
    return value


def center_x(rect):
    return rect["x"] + rect["width"] / 2


def center_y(rect):
    return rect["y"] + rect["height"] / 2


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


def organize(page: Page):
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(400)
    page.keyboard.press("Alt+Shift+f")
    page.wait_for_timeout(300)
    return page.get_by_role("button", name="缩放选项").inner_text()


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


def open_annotate(page: Page):
    trigger = page.locator('[data-testid="image-toolbar-annotate"]')
    trigger_box = box(trigger)
    if trigger_box["x"] < 0 or trigger_box["x"] + trigger_box["width"] > page.viewport_size["width"]:
        trigger.evaluate("(element) => element.click()")
    else:
        trigger.click()
    page.locator("[data-image-annotate-toolbar]").wait_for(state="visible")
    page.locator("[data-image-annotate-canvas]").wait_for(state="visible")
    page.wait_for_timeout(180)


def click_toolbar_button(page: Page, selector: str):
    trigger = page.locator(selector)
    trigger_box = box(trigger)
    viewport_width = page.viewport_size["width"]
    if trigger_box["x"] < 0 or trigger_box["x"] + trigger_box["width"] > viewport_width:
        trigger.evaluate("(element) => element.click()")
    else:
        trigger.click()


def assert_annotate(page: Page, graph_before=None):
    image_node = node(page)
    node_box = box(image_node)
    media_box = box(image_node.locator("[data-image-node-media]"))
    toolbar = page.locator("[data-image-annotate-toolbar]")
    toolbar_box = box(toolbar)
    surface = page.locator("[data-image-annotate-surface]")
    surface_box = box(surface)
    canvas = page.locator("[data-image-annotate-canvas]")
    canvas_box = box(canvas)

    assert page.locator("[data-image-toolbar]").count() == 0
    assert page.locator("[data-image-edit-panel]").count() == 0
    assert_close(toolbar_box["width"], 536)
    assert_close(toolbar_box["height"], 49)
    assert_close(center_x(toolbar_box), center_x(node_box))
    assert_close(node_box["y"] - (toolbar_box["y"] + toolbar_box["height"]), 10, 1.5)
    for key in ("x", "y", "width", "height"):
        assert_close(surface_box[key], media_box[key], 1)
    assert_close(canvas_box["width"], media_box["width"], 1)
    assert_close(canvas_box["height"], media_box["height"], 1)
    assert_close(canvas.get_attribute("width") and float(canvas.get_attribute("width")), canvas_box["width"] * 2, 2)
    assert_close(canvas.get_attribute("height") and float(canvas.get_attribute("height")), canvas_box["height"] * 2, 2)

    buttons = toolbar.locator("button")
    assert buttons.count() == 8
    assert page.get_by_role("button", name="标注", exact=True).count() == 1
    assert page.get_by_role("button", name="保存", exact=True).count() == 1
    assert page.locator("[data-image-annotate-undo]").is_disabled()
    assert page.locator("[data-image-annotate-redo]").is_disabled()
    assert not page.locator("[data-image-annotate-close]").is_disabled()
    assert not page.locator("[data-image-annotate-save]").is_disabled()
    assert toolbar.locator("[data-image-annotate-control]").count() == 3
    assert page.locator("[data-image-annotate-color]").count() == 1
    assert page.locator("[data-image-annotate-line-width]").count() == 1
    line_width = page.locator("[data-image-annotate-line-width] input")
    assert line_width.get_attribute("min") == "1"
    assert line_width.get_attribute("max") == "40"
    assert line_width.input_value() == "4"
    assert page.locator("[data-image-annotate-surface]").get_attribute("data-image-annotate-tool") == "pencil"

    page.locator("[data-image-annotate-color]").click()
    colors = ["#ffcc00", "#ff7a00", "#ff2d55", "#ff0000", "#8e5cff", "#3a86ff", "#ffffff"]
    assert page.locator("[data-image-annotate-color-menu] button").count() == len(colors)
    for color in colors:
        assert page.locator(f'[data-image-annotate-color-menu] button[aria-label="{color}"]').count() == 1
    page.locator('[data-image-annotate-color-menu] button[aria-label="#3a86ff"]').click()
    assert page.locator("[data-image-annotate-color]").get_attribute("aria-expanded") == "false"

    line_width.fill("12")
    assert line_width.input_value() == "12"

    click_toolbar_button(page, '[data-image-annotate-control="rect"]')
    assert page.locator("[data-image-annotate-surface]").get_attribute("data-image-annotate-tool") == "rect"
    click_toolbar_button(page, '[data-image-annotate-control="text"]')
    assert page.locator("[data-image-annotate-surface]").get_attribute("data-image-annotate-tool") == "text"
    click_toolbar_button(page, '[data-image-annotate-control="pencil"]')
    assert page.locator("[data-image-annotate-surface]").get_attribute("data-image-annotate-tool") == "pencil"
    click_toolbar_button(page, "[data-image-annotate-save]")
    if graph_before is not None:
        assert graph_signature(page) == graph_before

    return {
        "node": node_box,
        "toolbar": toolbar_box,
        "media": media_box,
        "surface": surface_box,
        "canvas": canvas_box,
        "canvas_backing": [int(canvas.get_attribute("width")), int(canvas.get_attribute("height"))],
        "buttons": buttons.count(),
    }


def run_desktop(page: Page):
    errors = collect_errors(page)
    zoom_label = organize(page)
    page.locator(f'.react-flow__node[data-id="{IMAGE_ID}"]').click(force=True)
    page.wait_for_timeout(180)
    assert page.locator("[data-image-toolbar]").count() == 1
    assert page.locator("[data-image-edit-panel]").count() == 1
    graph_before = graph_signature(page)
    prompt_before = page.get_by_label("图片生成提示词").input_value()
    page.screenshot(path=str(REFERENCE_DIR / "liblib-clone-batch53-image-annotate-standard-929-2026-08-26.png"))

    open_annotate(page)
    annotate_metrics = assert_annotate(page, graph_before)
    page.keyboard.press("Delete")
    page.keyboard.press("Control+z")
    page.keyboard.down("Space")
    page.keyboard.up("Space")
    assert graph_signature(page) == graph_before
    assert page.locator("[data-image-annotate-toolbar]").count() == 1
    page.screenshot(path=str(REFERENCE_DIR / "liblib-clone-batch53-image-annotate-active-929-2026-08-26.png"))

    page.keyboard.press("Escape")
    page.locator("[data-image-annotate-toolbar]").wait_for(state="detached")
    assert page.locator("[data-image-annotate-surface]").count() == 0
    assert page.locator("[data-image-toolbar]").count() == 1
    assert page.locator("[data-image-edit-panel]").count() == 1
    assert graph_signature(page) == graph_before
    assert page.get_by_label("图片生成提示词").input_value() == prompt_before

    open_annotate(page)
    click_toolbar_button(page, "[data-image-annotate-close]")
    page.locator("[data-image-annotate-toolbar]").wait_for(state="detached")
    assert graph_signature(page) == graph_before
    assert not errors, errors
    return {"zoom": zoom_label, "annotate": annotate_metrics}


def run_mobile(page: Page):
    errors = collect_errors(page)
    organize(page)
    page.locator(f'.react-flow__node[data-id="{IMAGE_ID}"]').click(force=True)
    page.wait_for_timeout(180)
    graph_before = graph_signature(page)
    open_annotate(page)
    annotate_metrics = assert_annotate(page)
    assert page.evaluate("document.documentElement.scrollWidth <= document.documentElement.clientWidth")
    assert page.evaluate("document.body.scrollWidth <= document.body.clientWidth")
    page.screenshot(path=str(REFERENCE_DIR / "liblib-clone-batch53-image-annotate-mobile-390-2026-08-26.png"))
    click_toolbar_button(page, "[data-image-annotate-close]")
    page.locator("[data-image-annotate-toolbar]").wait_for(state="detached")
    assert graph_signature(page) == graph_before
    assert page.locator("[data-image-toolbar]").count() == 1
    assert not errors, errors
    return annotate_metrics


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
                    "toolbar_size": [536, 49],
                    "button_count": 8,
                    "canvas_dpr": 2,
                    "standard_panel": "absent_while_active",
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
        "Batch 53 Playwright verification passed: annotate toolbar replacement, "
        "standard panel removal, node-centered geometry, DPR2 canvas backing, "
        "empty-state undo/redo state, tool/color/line-width controls, keyboard isolation, "
        "Escape/close recovery, graph immutability and mobile overflow."
    )


if __name__ == "__main__":
    main()
