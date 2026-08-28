import json
import math
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw
from playwright.sync_api import Page, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "docs" / "design-references"
SOURCE_AUDIT = (
    ROOT
    / "docs"
    / "research"
    / "liblib-live-2026-08-25"
    / "image-node-state-audit.json"
)
URL = "http://localhost:4317"
PLACEHOLDER = "可直接文字生图，或上传图片输入文字指令对图片进行编辑，如：将背景改为雪夜"

SLUGS = {
    "i-1FQ9tErTcC": "male",
    "i-lBzmo67AHv": "female",
    "i-dnwoZQ7jsG": "coffee",
    "i-vxeeCnxySa": "cafe",
    "i-YDfWhFlthe": "storyboard",
}


def node(page: Page, node_id: str):
    return page.locator(f'.react-flow__node[data-id="{node_id}"]')


def box(locator):
    value = locator.bounding_box()
    assert value is not None
    return value


def assert_close(actual: float, expected: float, tolerance: float = 0.5):
    assert abs(actual - expected) <= tolerance, (actual, expected)


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


def top_control_texts(page: Page):
    return page.locator("[data-image-editor-control]").all_inner_texts()


def source_states():
    payload = json.loads(SOURCE_AUDIT.read_text())
    return {state["node"]["id"]: state for state in payload["states"]}


def expected_top_controls(state):
    labels = {"参考", "标记", "风格"}
    return [
        control["text"]
        for control in state["panel"]["controls"]
        if control["text"] in labels
    ]


def capture_panel_crop(page: Page, panel_box, slug: str):
    screenshot_bytes = page.screenshot(
        path=str(
            REFERENCE_DIR
            / f"liblib-clone-batch10-{slug}-929-2026-08-25.png"
        )
    )
    screenshot = Image.open(BytesIO(screenshot_bytes)).convert("RGB")
    panel_width = int(round(panel_box["width"]))
    panel_height = int(round(panel_box["height"]))
    crop = Image.new("RGB", (panel_width, panel_height), "#141414")

    left = math.floor(panel_box["x"])
    top = math.floor(panel_box["y"])
    right = math.ceil(panel_box["x"] + panel_box["width"])
    bottom = math.ceil(panel_box["y"] + panel_box["height"])
    visible_left = max(0, left)
    visible_top = max(0, top)
    visible_right = min(screenshot.width, right)
    visible_bottom = min(screenshot.height, bottom)

    if visible_right > visible_left and visible_bottom > visible_top:
        visible = screenshot.crop(
            (visible_left, visible_top, visible_right, visible_bottom)
        )
        crop.paste(
            visible,
            (visible_left - left, visible_top - top),
        )
    return crop


def run_state(page: Page, state):
    errors = attach_error_collection(page)
    organize(page)

    node_id = state["node"]["id"]
    node(page, node_id).click(force=True)
    page.wait_for_timeout(180)

    panel = page.locator("[data-image-edit-panel]")
    panel_box = box(panel)
    expected_height = round(state["panel"]["box"]["h"])
    assert_close(panel_box["width"], 660)
    assert_close(panel_box["height"], expected_height)

    textarea = page.get_by_label("图片生成提示词")
    prompt = textarea.input_value()
    assert prompt == state["panel"]["prompt"]
    assert len(prompt) == len(state["panel"]["prompt"])
    assert textarea.get_attribute("placeholder") == PLACEHOLDER

    assert top_control_texts(page) == expected_top_controls(state)
    for control_box in page.locator("[data-image-editor-control]").all():
        assert_close(box(control_box)["width"], 54)
        assert_close(box(control_box)["height"], 26)

    references = page.locator("[data-image-editor-reference]")
    assert references.count() == len(state["panel"]["references"])
    for reference in references.all():
        reference_box = box(reference)
        assert_close(reference_box["width"], 47)
        assert_close(reference_box["height"], 47)

    expected_settings = next(
        control["text"]
        for control in state["panel"]["controls"]
        if " · " in control["text"]
    )
    assert page.locator("[data-image-editor-settings]").inner_text() == expected_settings
    assert_close(box(page.locator("[data-image-editor-model]"))["height"], 32)
    assert_close(box(page.locator("[data-image-editor-settings]"))["height"], 32)
    for footer_icon in page.locator("[data-image-editor-footer-icon]").all():
        footer_box = box(footer_icon)
        assert_close(footer_box["width"], 32)
        assert_close(footer_box["height"], 32)

    top_text = page.locator("[data-image-editor-top-controls]").inner_text()
    assert "智能引用 AutoLink" not in top_text
    panel_text = panel.inner_text()
    assert "⌘" not in panel_text
    assert "▭" not in panel_text

    expected_autolink = bool(prompt.strip()) and not state["panel"]["references"]
    assert page.locator("[data-image-editor-autolink]").count() == int(
        expected_autolink
    )

    panel_crop = capture_panel_crop(page, panel_box, SLUGS[node_id])

    if node_id == "i-dnwoZQ7jsG":
        page.locator("[data-image-editor-autolink]").click()
        popover = page.locator("[data-image-editor-autolink-popover]")
        assert popover.count() == 1
        assert "匹配到陈默、咖啡 2 个画布素材" in popover.inner_text()
        popover.get_by_role("button", name="引用", exact=True).click()
        page.wait_for_timeout(120)
        assert page.locator("[data-image-editor-reference]").count() == 2
        assert top_control_texts(page) == ["参考", "标记", "风格"]
        assert page.locator("[data-image-editor-autolink]").count() == 0
        assert page.get_by_label("图片生成提示词").input_value().startswith(
            "@陈默（图片 1）、@咖啡（图片 2）。"
        )
        assert_close(box(panel)["height"], expected_height)

    assert not errors, errors
    return panel_crop


def save_contact_sheet(crops):
    tile_width = 660
    tile_height = 304
    columns = 2
    rows = math.ceil(len(crops) / columns)
    sheet = Image.new(
        "RGB",
        (tile_width * columns, tile_height * rows),
        "#101010",
    )
    draw = ImageDraw.Draw(sheet)

    for index, (slug, crop) in enumerate(crops):
        x = (index % columns) * tile_width
        y = (index // columns) * tile_height
        draw.text((x + 8, y + 7), slug, fill="#eeeeee")
        sheet.paste(crop, (x, y + 30))

    sheet.save(
        REFERENCE_DIR
        / "liblib-clone-batch10-image-editor-state-matrix-2026-08-25.png"
    )


def main():
    REFERENCE_DIR.mkdir(parents=True, exist_ok=True)
    states = source_states()
    crops = []

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        for node_id in SLUGS:
            page = browser.new_page(
                viewport={"width": 929, "height": 874},
                device_scale_factor=1,
            )
            crop = run_state(page, states[node_id])
            crops.append((SLUGS[node_id], crop))
            page.close()
        browser.close()

    save_contact_sheet(crops)
    print(
        "Batch10 Playwright verification passed: five source image-editor "
        "states, explicit heights, prompts, references, controls, footer "
        "geometry, AutoLink lifecycle, screenshots, console."
    )


if __name__ == "__main__":
    main()
