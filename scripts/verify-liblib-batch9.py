from pathlib import Path

from playwright.sync_api import Page, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "docs" / "design-references"
URL = "http://localhost:3000"

STORYBOARD_IMAGE_ID = "i-YDfWhFlthe"
LEFT_IMAGE_ID = "i-dnwoZQ7jsG"
VIDEO_GROUP_ID = "g-EFbbHpwq5w"
VIDEO_ID = "v-UGQZzZOpbv"

IMAGE_WORLD_WIDTH = 622
VIDEO_WORLD_WIDTH = 622


def node(page: Page, node_id: str):
    return page.locator(f'.react-flow__node[data-id="{node_id}"]')


def box(locator):
    value = locator.bounding_box()
    assert value is not None
    return value


def center_x(rect):
    return rect["x"] + rect["width"] / 2


def assert_close(actual: float, expected: float, tolerance: float = 1):
    assert abs(actual - expected) <= tolerance, (actual, expected)


def assert_same_delta(before_a, after_a, before_b, after_b, tolerance: float = 1):
    assert_close(after_a["x"] - before_a["x"], after_b["x"] - before_b["x"], tolerance)
    assert_close(after_a["y"] - before_a["y"], after_b["y"] - before_b["y"], tolerance)


def drag(page: Page, start, dx: float, dy: float):
    page.mouse.move(*start)
    page.mouse.down()
    page.mouse.move(start[0] + dx / 2, start[1] + dy / 2, steps=4)
    page.mouse.move(start[0] + dx, start[1] + dy, steps=4)
    page.mouse.up()
    page.wait_for_timeout(200)


def attach_error_collection(page: Page):
    errors = []
    page.on(
        "console",
        lambda message: errors.append(f"console:{message.type}:{message.text}")
        if message.type == "error"
        else None,
    )
    page.on("pageerror", lambda error: errors.append(f"pageerror:{error}"))
    return errors


def organize(page: Page):
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(400)
    page.keyboard.press("Alt+Shift+f")
    page.wait_for_timeout(300)
    assert page.get_by_role("button", name="缩放选项").inner_text() == "28%"


def deselect(page: Page):
    page.locator(".react-flow__pane").click(position={"x": 260, "y": 120}, force=True)
    page.wait_for_timeout(120)


def assert_image_anchor(page: Page, node_id: str, expected_panel_height: float):
    node_box = box(node(page, node_id))
    toolbar_box = box(page.locator("[data-image-toolbar]"))
    panel_box = box(page.locator("[data-image-edit-panel]"))
    zoom = node_box["width"] / IMAGE_WORLD_WIDTH

    assert_close(center_x(toolbar_box), center_x(node_box))
    assert_close(node_box["y"] - (toolbar_box["y"] + toolbar_box["height"]), 16)
    assert_close(toolbar_box["width"], 900.5)
    assert_close(toolbar_box["height"], 49)

    assert_close(center_x(panel_box), center_x(node_box))
    assert_close(panel_box["y"] - (node_box["y"] + node_box["height"]), 16 * zoom)
    assert_close(panel_box["width"], 660)
    assert_close(panel_box["height"], expected_panel_height)

    classes = (page.locator("[data-image-edit-panel]").get_attribute("class") or "").split()
    assert {"nodrag", "nowheel", "nopan"}.issubset(classes)
    return node_box, toolbar_box, panel_box


def assert_video_anchor(page: Page):
    node_box = box(node(page, VIDEO_ID))
    panel_box = box(page.locator("[data-video-generation-panel]"))
    zoom = node_box["width"] / VIDEO_WORLD_WIDTH

    assert_close(center_x(panel_box), center_x(node_box))
    assert_close(panel_box["y"] - (node_box["y"] + node_box["height"]), 16 * zoom)
    assert_close(panel_box["width"], 660)
    assert_close(panel_box["height"], 274)

    classes = (page.locator("[data-video-generation-panel]").get_attribute("class") or "").split()
    assert {"nodrag", "nowheel", "nopan"}.issubset(classes)
    return node_box, panel_box


def run_image_anchor(page: Page):
    errors = attach_error_collection(page)
    organize(page)

    node(page, STORYBOARD_IMAGE_ID).click(force=True)
    page.wait_for_timeout(180)
    image_box, _, _ = assert_image_anchor(page, STORYBOARD_IMAGE_ID, 274)
    page.screenshot(
        path=str(REFERENCE_DIR / "liblib-clone-batch9-image-anchor-929-2026-08-25.png")
    )

    viewport_before = page.locator(".react-flow__viewport").get_attribute("style")
    textarea = page.get_by_label("图片生成提示词")
    textarea.click()
    textarea.press("End")
    textarea.press_sequentially(".")
    page.mouse.wheel(0, 120)
    page.wait_for_timeout(180)
    assert page.locator(".react-flow__viewport").get_attribute("style") == viewport_before
    assert_close(box(node(page, STORYBOARD_IMAGE_ID))["x"], image_box["x"])
    assert_close(box(node(page, STORYBOARD_IMAGE_ID))["y"], image_box["y"])

    deselect(page)
    node(page, LEFT_IMAGE_ID).click(position={"x": 20, "y": 20}, force=True)
    page.wait_for_timeout(180)
    _, toolbar_box, panel_box = assert_image_anchor(page, LEFT_IMAGE_ID, 211)
    assert toolbar_box["x"] < 0
    assert panel_box["x"] < 0
    assert not errors, errors


def run_video_anchor(page: Page):
    errors = attach_error_collection(page)
    organize(page)
    node(page, VIDEO_ID).click(force=True)
    page.wait_for_timeout(180)

    initial_group = box(node(page, VIDEO_GROUP_ID))
    initial_video, initial_panel = assert_video_anchor(page)
    page.screenshot(
        path=str(REFERENCE_DIR / "liblib-clone-batch9-video-anchor-929-2026-08-25.png")
    )

    drag(page, (initial_group["x"] + 8, initial_group["y"] + 8), 54, 27)
    parent_group = box(node(page, VIDEO_GROUP_ID))
    parent_video = box(node(page, VIDEO_ID))
    assert_same_delta(initial_group, parent_group, initial_video, parent_video)
    assert page.locator("[data-video-generation-panel]").count() == 0

    node(page, VIDEO_ID).click(force=True)
    page.wait_for_timeout(180)
    parent_video, parent_panel = assert_video_anchor(page)
    assert_same_delta(initial_video, parent_video, initial_panel, parent_panel)

    drag(
        page,
        (
            parent_video["x"] + parent_video["width"] / 2,
            parent_video["y"] + parent_video["height"] / 2,
        ),
        35,
        20,
    )
    child_group = box(node(page, VIDEO_GROUP_ID))
    child_video, child_panel = assert_video_anchor(page)
    assert_same_delta(parent_group, child_group, parent_group, parent_group)
    assert_same_delta(parent_video, child_video, parent_panel, child_panel)

    page.get_by_role("button", name="缩放选项").click()
    page.get_by_role("button", name="放大", exact=True).click()
    page.wait_for_timeout(250)
    zoom_video, zoom_panel = assert_video_anchor(page)
    assert page.get_by_role("button", name="缩放选项").inner_text() == "38%"

    page.mouse.move(250, 120)
    page.mouse.wheel(80, 45)
    page.wait_for_timeout(250)
    pan_video, pan_panel = assert_video_anchor(page)
    assert_same_delta(zoom_video, pan_video, zoom_panel, pan_panel)
    page.screenshot(
        path=str(
            REFERENCE_DIR
            / "liblib-clone-batch9-video-parent-child-follow-2026-08-25.png"
        )
    )
    assert not errors, errors


def run_multi_selection_lifecycle(page: Page):
    errors = attach_error_collection(page)
    organize(page)
    node(page, VIDEO_ID).click(force=True)
    page.wait_for_timeout(160)
    assert page.locator("[data-video-generation-panel]").count() == 1

    node(page, LEFT_IMAGE_ID).click(
        position={"x": 12, "y": 12}, modifiers=["Meta"], force=True
    )
    page.wait_for_timeout(180)
    assert node(page, VIDEO_ID).locator("xpath=self::*[contains(@class, 'selected')]").count() == 1
    assert (
        node(page, LEFT_IMAGE_ID)
        .locator("xpath=self::*[contains(@class, 'selected')]")
        .count()
        == 1
    )
    assert page.locator("[data-image-toolbar]").count() == 0
    assert page.locator("[data-image-edit-panel]").count() == 0
    assert page.locator("[data-video-generation-panel]").count() == 0
    assert not errors, errors


def main():
    REFERENCE_DIR.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)

        image_page = browser.new_page(
            viewport={"width": 929, "height": 874}, device_scale_factor=1
        )
        run_image_anchor(image_page)
        image_page.close()

        video_page = browser.new_page(
            viewport={"width": 929, "height": 874}, device_scale_factor=1
        )
        run_video_anchor(video_page)
        video_page.close()

        multi_page = browser.new_page(
            viewport={"width": 929, "height": 874}, device_scale_factor=1
        )
        run_multi_selection_lifecycle(multi_page)
        multi_page.close()

        browser.close()

    print(
        "Batch9 Playwright verification passed: image toolbar/editor anchors, "
        "unclamped edge behavior, parented video follow, pan/zoom, input gesture "
        "isolation, multi-selection lifecycle, console."
    )


if __name__ == "__main__":
    main()
