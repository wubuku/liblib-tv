from pathlib import Path
import os

from PIL import Image, ImageDraw
from playwright.sync_api import Locator, Page, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "docs" / "design-references"
BASE_URL = os.environ.get("LIBLIB_BASE_URL", "http://localhost:4317")
TEST_URL = f"{BASE_URL}/?duration=10"

GUARD_SCREENSHOT = (
    REFERENCE_DIR / "liblib-clone-batch32-depth-guard-929-2026-08-26.png"
)
PANEL_720P_SCREENSHOT = (
    REFERENCE_DIR / "liblib-clone-batch32-depth-panel-720p-929-2026-08-26.png"
)
PANEL_1080P_SCREENSHOT = (
    REFERENCE_DIR / "liblib-clone-batch32-depth-panel-1080p-929-2026-08-26.png"
)
GRAPH_SCREENSHOT = (
    REFERENCE_DIR / "liblib-clone-batch32-depth-graph-929-2026-08-26.png"
)
MOBILE_SCREENSHOT = (
    REFERENCE_DIR / "liblib-clone-batch32-depth-mobile-390-2026-08-26.png"
)
CONTACT_SHEET = (
    REFERENCE_DIR
    / "liblib-clone-batch32-depth-motion-contact-sheet-2026-08-26.png"
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
    return errors


def box(locator: Locator):
    result = locator.bounding_box()
    assert result is not None
    return result


def center_x(rect):
    return rect["x"] + rect["width"] / 2


def assert_close(actual: float, expected: float, tolerance: float = 1.5):
    assert abs(actual - expected) <= tolerance, (actual, expected)


def assert_no_overflow(page: Page):
    assert page.evaluate(
        "document.documentElement.scrollWidth <= document.documentElement.clientWidth"
    )
    assert page.evaluate(
        "document.body.scrollWidth <= document.body.clientWidth"
    )


def switch_to_empty_canvas(page: Page, url: str):
    page.goto(url, wait_until="networkidle")
    page.locator("[data-canvas-trigger]").click()
    page.locator('[data-canvas-row="canvas-1"] button').first.click()
    page.wait_for_timeout(180)
    assert page.locator(".react-flow__node").count() == 0
    assert page.locator(".react-flow__edge").count() == 0


def add_ready_video(page: Page):
    page.get_by_role("button", name="添加节点").click()
    page.locator('[data-add-node-entry="video"]').click()
    source = page.locator(".react-flow__node-video.selected")
    assert source.count() == 1
    source_id = source.get_attribute("data-id")
    assert source_id
    source = page.locator(f'.react-flow__node[data-id="{source_id}"]')
    assert page.locator("[data-video-generation-panel]").count() == 1
    trigger = page.locator("[data-video-depth-motion-trigger]")
    assert trigger.count() == 1
    assert trigger.inner_text().strip() == "深度动作捕捉"
    return source, source_id, trigger


def open_depth_panel(page: Page):
    trigger = page.locator("[data-video-depth-motion-trigger]")
    trigger.click()
    panel = page.locator("[data-depth-motion-panel]")
    panel.wait_for(state="visible")
    assert page.locator("[data-video-generation-panel]").count() == 0
    assert page.locator("[data-depth-motion-title]").inner_text() == "深度动作捕捉"
    assert "提取视频深度信息" in page.locator(
        "[data-depth-motion-intro]"
    ).inner_text()
    return panel


def run_guard(page: Page):
    errors = attach_errors(page)
    switch_to_empty_canvas(page, BASE_URL)
    source, source_id, trigger = add_ready_video(page)
    trigger.click()
    feedback = page.locator("[data-video-depth-motion-feedback]")
    assert feedback.inner_text() == "视频时长超过处理上限，暂不支持深度动作捕捉"
    assert page.locator("[data-depth-motion-panel]").count() == 0
    assert page.locator(".react-flow__node").count() == 1
    assert page.locator(".react-flow__edge").count() == 0
    assert page.locator(".react-flow__node.selected").get_attribute(
        "data-id"
    ) == source_id
    assert page.locator("[data-video-picture-edit-feedback]").count() == 0
    assert_no_overflow(page)
    page.screenshot(path=str(GUARD_SCREENSHOT))
    assert source.count() == 1
    assert not errors, errors


def run_panel_and_graph(page: Page):
    errors = attach_errors(page)
    switch_to_empty_canvas(page, TEST_URL)
    source, source_id, _ = add_ready_video(page)

    panel = open_depth_panel(page)
    source_summary = page.locator("[data-depth-motion-source-summary]")
    assert source_summary.inner_text() == "视频节点 5-片段重拍\n10s · 1280 × 720"
    assert page.locator('[data-depth-motion-resolution-option="720P"]').get_attribute(
        "aria-pressed"
    ) == "true"
    assert page.locator('[data-depth-motion-resolution-option="1080P"]').get_attribute(
        "aria-pressed"
    ) == "false"
    assert page.locator("[data-depth-motion-submit-reason]").inner_text() == "确认提取"
    panel_box = box(panel)
    source_box = box(source)
    assert_close(panel_box["width"], 512)
    assert_close(center_x(panel_box), center_x(source_box))
    assert_close(panel_box["y"] - (source_box["y"] + source_box["height"]), 16)
    page.screenshot(path=str(PANEL_720P_SCREENSHOT))

    page.locator('[data-depth-motion-resolution-option="1080P"]').click()
    assert page.locator('[data-depth-motion-resolution-option="1080P"]').get_attribute(
        "aria-pressed"
    ) == "true"
    assert page.locator('[data-depth-motion-resolution-option="720P"]').get_attribute(
        "aria-pressed"
    ) == "false"
    page.screenshot(path=str(PANEL_1080P_SCREENSHOT))

    submit = page.locator("[data-depth-motion-submit]")
    submit.click()
    assert page.locator("[data-depth-motion-spinner]").count() == 1
    assert submit.is_disabled()
    assert page.locator("[data-depth-motion-submit-reason]").inner_text() == "提取中"
    page.wait_for_timeout(600)

    output = page.locator("[data-depth-motion-output]").first
    assert output.count() == 1
    assert output.get_attribute("data-depth-motion-source-id") == source_id
    first_edge_id = output.get_attribute("data-depth-motion-edge-id")
    assert first_edge_id
    assert output.get_attribute("data-depth-motion-resolution-value") == "1080P"
    assert output.get_attribute("data-depth-motion-duration") == "10"
    assert output.get_attribute("data-depth-motion-model") == "depth-motion-reference"
    assert output.get_attribute("data-depth-motion-request-mode") == "DepthMap"
    assert "深度动作捕捉参考" in output.inner_text()
    assert "1080P · 等待媒体资源" in output.inner_text()

    first_shell = output.locator(
        "xpath=ancestor::div[contains(@class, 'react-flow__node')][1]"
    )
    first_output_id = first_shell.get_attribute("data-id")
    assert first_output_id
    assert "深度动作捕捉-视频节点 5-片段重拍" in first_shell.inner_text()
    edge = page.locator(
        f'.react-flow__edge[aria-label="Edge from {source_id} to {first_output_id}"]'
    )
    assert edge.count() == 1
    assert edge.get_attribute("data-id") == first_edge_id
    assert page.locator(".react-flow__node").count() == 2
    assert page.locator(".react-flow__edge").count() == 1
    assert page.locator(".react-flow__node.selected").get_attribute(
        "data-id"
    ) == source_id

    source_box = box(source)
    first_box = box(first_shell)
    zoom = source_box["width"] / 512
    assert_close(
        first_box["x"] - source_box["x"],
        source_box["width"] + 100 * zoom,
    )
    assert_close(first_box["y"], source_box["y"])

    page.keyboard.press("Meta+z")
    page.wait_for_timeout(150)
    assert page.locator("[data-depth-motion-output]").count() == 0
    assert page.locator(".react-flow__node").count() == 1
    assert page.locator(".react-flow__edge").count() == 0

    page.keyboard.press("Meta+Shift+z")
    page.wait_for_timeout(150)
    assert page.locator("[data-depth-motion-output]").count() == 1
    assert page.locator(".react-flow__node").count() == 2
    assert page.locator(".react-flow__edge").count() == 1

    source.click(position={"x": 20, "y": 20}, force=True)
    panel = open_depth_panel(page)
    assert page.locator('[data-depth-motion-resolution-option="720P"]').get_attribute(
        "aria-pressed"
    ) == "true"
    panel.locator("[data-depth-motion-submit]").click()
    page.wait_for_timeout(600)
    outputs = page.locator("[data-depth-motion-output]")
    assert outputs.count() == 2
    second_shell = outputs.nth(1).locator(
        "xpath=ancestor::div[contains(@class, 'react-flow__node')][1]"
    )
    first_shell_box = box(first_shell)
    second_shell_box = box(second_shell)
    assert_close(second_shell_box["x"], first_shell_box["x"])
    assert_close(second_shell_box["y"] - first_shell_box["y"], (288 + 48) * zoom)
    assert page.locator(".react-flow__node.selected").get_attribute(
        "data-id"
    ) == source_id

    page.keyboard.press("Meta+0")
    page.wait_for_timeout(320)
    page.screenshot(path=str(GRAPH_SCREENSHOT))
    assert_no_overflow(page)
    assert not errors, errors


def run_multi_selection(page: Page):
    errors = attach_errors(page)
    switch_to_empty_canvas(page, TEST_URL)
    source, _, _ = add_ready_video(page)
    page.get_by_role("button", name="添加节点").click()
    page.locator('[data-add-node-entry="text"]').click()
    source.click(position={"x": 12, "y": 12}, modifiers=["Meta"], force=True)
    page.wait_for_timeout(150)
    assert page.locator(".react-flow__node.selected").count() == 2
    assert page.locator("[data-video-depth-motion-trigger]").count() == 0
    assert page.locator("[data-depth-motion-panel]").count() == 0
    assert page.locator(".react-flow__node-toolbar").count() == 0
    assert_no_overflow(page)
    assert not errors, errors


def run_mobile(page: Page):
    errors = attach_errors(page)
    switch_to_empty_canvas(page, TEST_URL)
    source, _, _ = add_ready_video(page)
    panel = open_depth_panel(page)
    panel_box = box(panel)
    source_box = box(source)
    assert panel_box["x"] < 0
    assert panel_box["x"] + panel_box["width"] > 390
    assert_close(center_x(panel_box), center_x(source_box))
    assert_no_overflow(page)
    page.screenshot(path=str(MOBILE_SCREENSHOT))
    assert not errors, errors


def save_contact_sheet():
    images = [
        ("30s guard", Image.open(GUARD_SCREENSHOT).convert("RGB")),
        ("720P panel", Image.open(PANEL_720P_SCREENSHOT).convert("RGB")),
        ("1080P panel", Image.open(PANEL_1080P_SCREENSHOT).convert("RGB")),
        ("pending graph", Image.open(GRAPH_SCREENSHOT).convert("RGB")),
        ("mobile clipping", Image.open(MOBILE_SCREENSHOT).convert("RGB")),
    ]
    label_height = 28
    gutter = 12
    cell_width = max(image.width for _, image in images)
    cell_height = max(image.height for _, image in images)
    columns = 2
    rows = (len(images) + columns - 1) // columns
    sheet = Image.new(
        "RGB",
        (
            cell_width * columns + gutter * (columns - 1),
            (cell_height + label_height + gutter) * rows,
        ),
        "#141414",
    )
    draw = ImageDraw.Draw(sheet)
    for index, (label, image) in enumerate(images):
        column = index % columns
        row = index // columns
        x = column * (cell_width + gutter)
        y = row * (cell_height + label_height + gutter)
        draw.text((x + 8, y + 8), label, fill="#ededed")
        sheet.paste(image, (x, y + label_height))
    sheet.save(CONTACT_SHEET)


def main():
    REFERENCE_DIR.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        guard = browser.new_page(viewport={"width": 929, "height": 874})
        run_guard(guard)

        desktop = browser.new_page(viewport={"width": 929, "height": 874})
        run_panel_and_graph(desktop)

        multi = browser.new_page(viewport={"width": 929, "height": 874})
        run_multi_selection(multi)

        mobile = browser.new_page(viewport={"width": 390, "height": 844})
        run_mobile(mobile)
        browser.close()

    save_contact_sheet()
    print(
        "Batch 32 verified: depth guard, node-anchored panel, source summary, "
        "resolution switch, busy state, pending graph metadata, direct edge, "
        "slot avoidance, graph history, multi-selection and mobile clipping."
    )


if __name__ == "__main__":
    main()
