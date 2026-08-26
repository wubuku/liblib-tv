from pathlib import Path

from PIL import Image, ImageDraw
from playwright.sync_api import Locator, Page, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "docs" / "design-references"
BASE_URL = "http://localhost:3000"
DESKTOP_URL = f"{BASE_URL}/?duration=10"

GUARD_SCREENSHOT = (
    REFERENCE_DIR / "liblib-clone-batch31-duration-guard-929-2026-08-26.png"
)
EDITOR_SCREENSHOT = (
    REFERENCE_DIR / "liblib-clone-batch31-remove-editor-929-2026-08-26.png"
)
MODIFY_SCREENSHOT = (
    REFERENCE_DIR / "liblib-clone-batch31-modify-panel-929-2026-08-26.png"
)
GRAPH_SCREENSHOT = (
    REFERENCE_DIR / "liblib-clone-batch31-picture-edit-graph-929-2026-08-26.png"
)
MOBILE_SCREENSHOT = (
    REFERENCE_DIR / "liblib-clone-batch31-picture-edit-mobile-390-2026-08-26.png"
)
CONTACT_SHEET = (
    REFERENCE_DIR / "liblib-clone-batch31-picture-edit-contact-sheet-2026-08-26.png"
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


def assert_close(actual: float, expected: float, tolerance: float = 1.2):
    assert abs(actual - expected) <= tolerance, (actual, expected)


def assert_no_overflow(page: Page):
    assert page.evaluate(
        "document.documentElement.scrollWidth <= document.documentElement.clientWidth"
    )
    assert page.evaluate(
        "document.body.scrollWidth <= document.body.clientWidth"
    )


def switch_to_empty_canvas(page: Page, url: str = DESKTOP_URL):
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
    assert page.locator("[data-video-picture-edit-menu-trigger]").count() == 1
    return source, source_id


def open_picture_edit_menu(page: Page, action: str):
    trigger = page.locator("[data-video-picture-edit-menu-trigger]")
    trigger.click()
    item = page.locator(
        f'[data-video-picture-edit-action="{action}"]'
    )
    assert item.count() == 1
    item.click()


def overlay_point(page: Page, rel_x: float, rel_y: float):
    overlay = page.locator("[data-picture-edit-mark-overlay]")
    rect = box(overlay)
    return rect["x"] + rect["width"] * rel_x, rect["y"] + rect["height"] * rel_y


def add_point_mark(page: Page, rel_x: float = 0.4, rel_y: float = 0.4):
    x, y = overlay_point(page, rel_x, rel_y)
    page.mouse.click(x, y)


def add_drag_mark(
    page: Page,
    tool: str,
    start: tuple[float, float],
    end: tuple[float, float],
):
    page.locator(f'button[data-picture-edit-tool="{tool}"]').click()
    start_x, start_y = overlay_point(page, *start)
    end_x, end_y = overlay_point(page, *end)
    page.mouse.move(start_x, start_y)
    page.mouse.down()
    page.mouse.move(end_x, end_y, steps=6)
    page.mouse.up()


def run_guard(page: Page):
    errors = attach_errors(page)
    switch_to_empty_canvas(page, f"{BASE_URL}/")
    source, source_id = add_ready_video(page)

    for action in ("subjectRemove", "subjectModify", "subjectReplace"):
        open_picture_edit_menu(page, action)
        feedback = page.locator("[data-video-picture-edit-feedback]")
        assert feedback.inner_text() == "视频大于15秒，暂不支持该功能"
        assert page.locator(".react-flow__node").count() == 1
        assert page.locator(".react-flow__edge").count() == 0
        assert page.locator(".react-flow__node.selected").get_attribute(
            "data-id"
        ) == source_id

    page.screenshot(path=str(GUARD_SCREENSHOT))
    assert not errors, errors


def run_editor_and_graph(page: Page):
    errors = attach_errors(page)
    switch_to_empty_canvas(page)
    source, source_id = add_ready_video(page)

    open_picture_edit_menu(page, "subjectRemove")
    panel = page.locator("[data-picture-edit-panel]")
    overlay = page.locator("[data-picture-edit-mark-overlay]")
    assert panel.count() == 1
    assert overlay.count() == 1
    assert panel.locator('[data-picture-edit-mode="subjectRemove"]').count() == 1
    assert panel.locator('[data-picture-edit-count="0/4"]').count() == 1
    assert panel.locator("button[data-picture-edit-tool]").all_inner_texts() == [
        "点选",
        "框选",
        "画笔",
        "橡皮",
    ]
    assert page.locator("[data-picture-edit-submit]").is_disabled()
    assert page.locator("[data-picture-edit-submit-reason]").inner_text() == (
        "请先标记主体"
    )

    add_point_mark(page, 0.35, 0.36)
    assert page.locator('[data-picture-edit-count="1/4"]').count() == 1
    assert page.locator('[data-picture-edit-mark-tool="point"]').count() == 1
    assert page.locator('[data-picture-edit-mark-frame="0"]').count() == 1

    add_drag_mark(page, "box", (0.18, 0.18), (0.48, 0.55))
    assert page.locator('[data-picture-edit-count="2/4"]').count() == 1
    box_mark = page.locator('[data-picture-edit-mark-tool="box"]')
    assert box_mark.count() == 1
    assert box_mark.locator("[data-picture-edit-mark-handle]").count() == 4

    add_drag_mark(page, "brush", (0.62, 0.24), (0.82, 0.48))
    assert page.locator('[data-picture-edit-count="3/4"]').count() == 1
    assert page.locator('[data-picture-edit-mark-tool="brush"]').count() == 1
    assert page.locator("[data-picture-edit-mark-path]").count() == 1
    page.screenshot(path=str(EDITOR_SCREENSHOT))

    page.locator('button[data-picture-edit-tool="eraser"]').click()
    point_mark = page.locator('[data-picture-edit-mark-tool="point"]')
    point_box = box(point_mark)
    page.mouse.click(
        point_box["x"] + point_box["width"] / 2,
        point_box["y"] + point_box["height"] / 2,
    )
    assert page.locator('[data-picture-edit-count="2/4"]').count() == 1

    page.locator('[data-picture-edit-history="undo"]').click()
    assert page.locator('[data-picture-edit-count="3/4"]').count() == 1
    page.locator('[data-picture-edit-history="redo"]').click()
    assert page.locator('[data-picture-edit-count="2/4"]').count() == 1
    page.locator("[data-picture-edit-reset]").click()
    assert page.locator('[data-picture-edit-count="0/4"]').count() == 1
    assert page.locator("[data-picture-edit-submit]").is_disabled()

    page.locator('button[data-picture-edit-tool="point"]').click()
    add_point_mark(page, 0.4, 0.42)
    page.locator("[data-picture-edit-submit]").click()
    assert page.locator(
        '[data-picture-edit-submit-status="analyzing"]'
    ).count() == 1
    assert page.locator("[data-picture-edit-spinner]").count() == 1
    assert page.locator("[data-picture-edit-submit]").is_disabled()
    page.wait_for_timeout(680)

    first_output = page.locator("[data-picture-edit-output]").first
    assert first_output.count() == 1
    assert first_output.get_attribute("data-picture-edit-mode") == "subjectRemove"
    assert first_output.get_attribute("data-picture-edit-source-id") == source_id
    first_edge_id = first_output.get_attribute("data-picture-edit-edge-id")
    assert first_edge_id
    assert first_output.get_attribute("data-picture-edit-model") == (
        "volcano-picture-editor"
    )
    assert first_output.get_attribute("data-picture-edit-request-mode") == "Remove"
    assert first_output.get_attribute("data-picture-edit-mark-count") == "1"
    assert "主体消除结果" in first_output.inner_text()
    assert "主体编辑 · 等待媒体资源" in first_output.inner_text()
    assert page.locator("[data-picture-edit-panel]").count() == 0
    assert page.locator(".react-flow__node.selected").get_attribute(
        "data-id"
    ) == source_id

    first_shell = first_output.locator(
        "xpath=ancestor::div[contains(@class, 'react-flow__node')][1]"
    )
    first_output_id = first_shell.get_attribute("data-id")
    assert first_output_id
    edge = page.locator(
        f'.react-flow__edge[aria-label="Edge from {source_id} to {first_output_id}"]'
    )
    assert edge.count() == 1
    assert edge.get_attribute("data-id") == first_edge_id
    assert page.locator(".react-flow__node").count() == 2
    assert page.locator(".react-flow__edge").count() == 1

    source_box = box(source)
    first_box = box(first_shell)
    zoom = source_box["width"] / 512
    assert_close(
        first_box["x"] - source_box["x"],
        source_box["width"] + 100 * zoom,
        1.8,
    )
    assert_close(first_box["y"], source_box["y"], 1.8)

    page.keyboard.press("Meta+z")
    page.wait_for_timeout(150)
    assert page.locator("[data-picture-edit-output]").count() == 0
    assert page.locator(".react-flow__node").count() == 1
    assert page.locator(".react-flow__edge").count() == 0
    page.keyboard.press("Meta+Shift+z")
    page.wait_for_timeout(150)
    assert page.locator("[data-picture-edit-output]").count() == 1
    assert page.locator(".react-flow__edge").count() == 1

    source.click(position={"x": 20, "y": 20}, force=True)
    open_picture_edit_menu(page, "subjectModify")
    assert page.locator('[data-picture-edit-mode="subjectModify"]').count() == 1
    add_point_mark(page, 0.52, 0.48)
    modify_input = page.locator("[data-picture-edit-description]")
    assert modify_input.count() == 1
    assert page.locator("[data-picture-edit-submit]").is_disabled()
    modify_input.fill("改成白色外套")
    assert not page.locator("[data-picture-edit-submit]").is_disabled()
    page.screenshot(path=str(MODIFY_SCREENSHOT))
    page.locator("[data-picture-edit-submit]").click()
    page.wait_for_timeout(680)
    assert page.locator('[data-picture-edit-output][data-picture-edit-mode="subjectModify"]').count() == 1

    open_picture_edit_menu(page, "subjectReplace")
    assert page.locator('[data-picture-edit-mode="subjectReplace"]').count() == 1
    add_point_mark(page, 0.66, 0.42)
    assert page.locator("[data-picture-edit-submit]").is_disabled()
    page.locator('[data-picture-edit-replacement="upload"]').click()
    assert page.locator(
        '[data-picture-edit-replacement-selected="upload"]'
    ).count() == 1
    assert not page.locator("[data-picture-edit-submit]").is_disabled()
    page.locator("[data-picture-edit-submit]").click()
    page.wait_for_timeout(680)
    outputs = page.locator("[data-picture-edit-output]")
    assert outputs.count() == 3
    assert outputs.nth(2).get_attribute("data-picture-edit-mode") == "subjectReplace"
    assert outputs.nth(2).get_attribute("data-picture-edit-request-mode") == "Replace"
    assert outputs.nth(2).get_attribute("data-picture-edit-mark-count") == "1"

    shells = [
        outputs.nth(index).locator(
            "xpath=ancestor::div[contains(@class, 'react-flow__node')][1]"
        )
        for index in range(3)
    ]
    second_box = box(shells[1])
    third_box = box(shells[2])
    assert_close(second_box["x"], first_box["x"], 1.8)
    assert_close(third_box["x"], first_box["x"], 1.8)
    assert second_box["y"] > first_box["y"]
    assert third_box["y"] > second_box["y"]
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
    switch_to_empty_canvas(page)
    source, _ = add_ready_video(page)
    page.get_by_role("button", name="添加节点").click()
    page.locator('[data-add-node-entry="text"]').click()
    source.click(position={"x": 12, "y": 12}, modifiers=["Meta"], force=True)
    page.wait_for_timeout(150)
    assert page.locator(".react-flow__node.selected").count() == 2
    assert page.locator("[data-picture-edit-panel]").count() == 0
    assert page.locator("[data-video-picture-edit-menu-trigger]").count() == 0
    assert page.locator(".react-flow__node-toolbar").count() == 0
    assert_no_overflow(page)
    assert not errors, errors


def run_mobile(page: Page):
    errors = attach_errors(page)
    switch_to_empty_canvas(page, DESKTOP_URL)
    page.set_viewport_size({"width": 390, "height": 844})
    page.goto(DESKTOP_URL, wait_until="networkidle")
    page.locator("[data-canvas-trigger]").click()
    page.locator('[data-canvas-row="canvas-1"] button').first.click()
    page.wait_for_timeout(180)
    add_ready_video(page)
    open_picture_edit_menu(page, "subjectReplace")
    panel = page.locator("[data-picture-edit-panel]")
    panel_box = box(panel)
    assert panel_box["x"] < 0
    assert panel_box["x"] + panel_box["width"] > 390
    assert panel_box["width"] == 660
    add_point_mark(page, 0.4, 0.4)
    assert page.locator("[data-picture-edit-mark]").count() == 1
    assert_no_overflow(page)
    page.screenshot(path=str(MOBILE_SCREENSHOT))
    assert not errors, errors


def save_contact_sheet():
    images = [
        ("30s duration guard", Image.open(GUARD_SCREENSHOT).convert("RGB")),
        ("remove editor", Image.open(EDITOR_SCREENSHOT).convert("RGB")),
        ("modify panel", Image.open(MODIFY_SCREENSHOT).convert("RGB")),
        ("picture edit graph", Image.open(GRAPH_SCREENSHOT).convert("RGB")),
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
        (cell_width * columns + gutter * (columns - 1), (cell_height + label_height + gutter) * rows),
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
        run_editor_and_graph(desktop)

        multi = browser.new_page(viewport={"width": 929, "height": 874})
        run_multi_selection(multi)

        mobile = browser.new_page(viewport={"width": 390, "height": 844})
        run_mobile(mobile)
        browser.close()

    save_contact_sheet()
    print(
        "Batch 31 verified: subject-edit duration guard, shared picture editor, "
        "point/box/brush/eraser, mark history, modify/replace validation, "
        "pending graph, metadata, repeated slots, multi-selection and mobile clipping."
    )


if __name__ == "__main__":
    main()
