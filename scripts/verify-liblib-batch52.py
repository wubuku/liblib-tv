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
    / "liblib-canvas-batch52-2026-08-26"
    / "runtime-audit.json"
)
IMAGE_ID = "i-vxeeCnxySa"
IMAGE_WORLD_WIDTH = 700

ACTION_CONTRACT = [
    ("image-toolbar-portrait-texture", "人像质感调节", 178, False),
    ("image-toolbar-panorama-slash", "全景", 62, False),
    ("image-toolbar-angle", "多角度", 75, False),
    ("image-toolbar-light", "打光", 62, False),
    ("image-toolbar-nine-grid", "九宫格", 91, False),
    ("image-editor-primary-tool-trigger", "高清", 78, False),
    ("image-toolbar-interactive-edit", "元素编辑", 88, True),
    ("image-toolbar-layer-separation", "图层分离", 88, True),
    ("image-toolbar-grid-split", "宫格切分", 104, False),
    ("image-toolbar-annotate", "标注", 32, False),
    ("image-toolbar-rotate", "旋转", 32, True),
    ("image-toolbar-download", "下载", 32, True),
    ("image-toolbar-preview", "预览", 32, False),
]


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
    zoom_label = page.get_by_role("button", name="缩放选项").inner_text()
    assert zoom_label.endswith("%")
    return zoom_label


def graph_signature(page: Page):
    return page.evaluate(
        """() => ({
          nodes: [...document.querySelectorAll('.react-flow__node')].map((node) => ({
            id: node.getAttribute('data-id'),
            transform: node.style.transform,
            text: node.textContent,
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


def assert_toolbar(page: Page):
    node_box = box(node(page))
    toolbar = page.locator("[data-image-toolbar]")
    toolbar_box = box(toolbar)
    panel_box = box(page.locator("[data-image-edit-panel]"))
    zoom = node_box["width"] / IMAGE_WORLD_WIDTH

    assert_close(toolbar_box["width"], 1092.5)
    assert_close(toolbar_box["height"], 49)
    assert_close(center_x(toolbar_box), center_x(node_box))
    assert_close(
        node_box["y"] - (toolbar_box["y"] + toolbar_box["height"]),
        10 + 24 * zoom,
    )
    assert_close(center_x(panel_box), center_x(node_box))
    assert_close(
        panel_box["y"] - (node_box["y"] + node_box["height"]),
        16 * zoom,
    )

    buttons = toolbar.locator("button")
    assert buttons.count() == len(ACTION_CONTRACT)
    action_metrics = []
    for index, (test_id, label, expected_width, expected_disabled) in enumerate(
        ACTION_CONTRACT
    ):
        button = buttons.nth(index)
        assert button.get_attribute("data-testid") == test_id
        button_box = box(button)
        assert_close(button_box["width"], expected_width)
        assert_close(button_box["height"], 32)
        assert button.is_disabled() == expected_disabled
        if index < 9:
            assert label in button.inner_text()
        else:
            assert button.get_attribute("aria-label") == label
        action_metrics.append(
            {
                "index": index,
                "test_id": test_id,
                "label": label,
                "rect": button_box,
                "disabled": expected_disabled,
            }
        )

    return {
        "node": node_box,
        "toolbar": toolbar_box,
        "panel": panel_box,
        "zoom": zoom,
        "actions": action_metrics,
    }


def assert_preview_geometry(page: Page, viewport_width: int, viewport_height: int):
    overlay_box = box(page.locator("[data-image-preview-overlay]"))
    content_box = box(page.locator("[data-image-preview-content]"))
    media_box = box(page.locator("[data-image-preview-media]"))
    watermark_box = box(page.locator("[data-image-preview-watermark]"))
    close_box = box(page.locator("[data-image-preview-close]"))

    assert_close(overlay_box["x"], 0)
    assert_close(overlay_box["y"], 0)
    assert_close(overlay_box["width"], viewport_width)
    assert_close(overlay_box["height"], viewport_height)

    assert_close(content_box["width"], viewport_width * 0.85)
    assert_close(content_box["height"], viewport_height * 0.8)
    assert_close(center_x(content_box), viewport_width / 2)
    assert_close(center_y(content_box), viewport_height / 2)

    expected_media_width = min(content_box["width"], content_box["height"] * 2)
    assert_close(media_box["width"], expected_media_width)
    assert_close(media_box["height"], expected_media_width / 2)
    assert_close(center_x(media_box), center_x(content_box))
    assert_close(center_y(media_box), center_y(content_box))

    assert_close(watermark_box["x"], media_box["x"] + 10)
    assert_close(watermark_box["y"], media_box["y"] + 10)
    assert_close(watermark_box["width"], 48)
    assert_close(watermark_box["height"], 23)

    assert_close(close_box["x"] + close_box["width"], content_box["x"] + content_box["width"] + 12)
    assert_close(close_box["y"], content_box["y"] - 12)
    assert_close(close_box["width"], 32)
    assert_close(close_box["height"], 32)

    assert page.locator("[data-image-preview-close]").evaluate(
        "(element) => document.activeElement === element"
    )
    return {
        "overlay": overlay_box,
        "content": content_box,
        "media": media_box,
        "watermark": watermark_box,
        "close": close_box,
    }


def open_preview(page: Page, *, clipped=False):
    trigger = page.locator('[data-testid="image-toolbar-preview"]')
    if clipped:
        trigger_box = box(trigger)
        assert trigger_box["x"] >= page.viewport_size["width"]
        trigger.evaluate("(element) => element.click()")
    else:
        trigger.click(force=True)
    page.locator("[data-image-preview-overlay]").wait_for(state="visible")
    page.wait_for_timeout(120)


def run_desktop(page: Page):
    errors = collect_errors(page)
    organize(page)
    node(page).click(force=True)
    page.wait_for_timeout(180)
    toolbar_metrics = assert_toolbar(page)
    graph_before = graph_signature(page)
    prompt_before = page.get_by_label("图片生成提示词").input_value()

    page.screenshot(
        path=str(
            REFERENCE_DIR
            / "liblib-clone-batch52-current-image-toolbar-929-2026-08-26.png"
        )
    )

    open_preview(page)
    preview_metrics = assert_preview_geometry(page, 929, 874)
    assert graph_signature(page) == graph_before
    assert page.get_by_label("图片生成提示词").input_value() == prompt_before

    page.locator("[data-image-preview-overlay]").focus()
    page.keyboard.down("Space")
    assert page.locator("[data-temporary-pan='true']").count() == 0
    page.keyboard.up("Space")
    page.keyboard.press("Delete")
    page.keyboard.press("Control+z")
    page.keyboard.press("Tab")
    assert graph_signature(page) == graph_before
    assert page.locator("[data-image-preview-overlay]").count() == 1

    page.screenshot(
        path=str(
            REFERENCE_DIR
            / "liblib-clone-batch52-image-preview-929-2026-08-26.png"
        )
    )

    page.keyboard.press("Escape")
    page.locator("[data-image-preview-overlay]").wait_for(state="detached")
    assert graph_signature(page) == graph_before
    assert page.get_by_label("图片生成提示词").input_value() == prompt_before
    assert page.locator("[data-image-toolbar]").count() == 1
    assert page.locator("[data-image-edit-panel]").count() == 1

    open_preview(page)
    page.locator("[data-image-preview-close]").click()
    page.locator("[data-image-preview-overlay]").wait_for(state="detached")
    assert graph_signature(page) == graph_before
    assert not errors, errors
    return {"toolbar": toolbar_metrics, "preview": preview_metrics}


def run_mobile(page: Page):
    errors = collect_errors(page)
    organize(page)
    node(page).click(force=True)
    page.wait_for_timeout(180)
    assert_toolbar(page)
    graph_before = graph_signature(page)
    open_preview(page, clipped=True)
    preview_metrics = assert_preview_geometry(page, 390, 844)
    assert page.evaluate(
        "document.documentElement.scrollWidth <= document.documentElement.clientWidth"
    )
    assert page.evaluate("document.body.scrollWidth <= document.body.clientWidth")
    page.screenshot(
        path=str(
            REFERENCE_DIR
            / "liblib-clone-batch52-image-preview-mobile-390-2026-08-26.png"
        )
    )
    page.locator("[data-image-preview-close]").click()
    assert graph_signature(page) == graph_before
    assert not errors, errors
    return preview_metrics


def main():
    REFERENCE_DIR.mkdir(parents=True, exist_ok=True)
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

    AUDIT_PATH.write_text(
        json.dumps(
            {
                "url": URL,
                "node_id": IMAGE_ID,
                "contract": {
                    "toolbar_size": [1092.5, 49],
                    "action_count": 13,
                    "preview_content": ["85vw", "80vh"],
                    "preview_media_ratio": "2:1",
                    "graph_mutation": "none",
                },
                "desktop": desktop,
                "mobile_preview": mobile,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )

    print(
        "Batch 52 Playwright verification passed: current 13-action image "
        "toolbar, source-sized button geometry, page-level preview, watermark "
        "and close geometry, keyboard isolation, unchanged graph/selection, "
        "responsive bounds, and browser errors."
    )


if __name__ == "__main__":
    main()
