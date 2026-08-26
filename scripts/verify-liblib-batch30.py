from pathlib import Path

from PIL import Image, ImageDraw
from playwright.sync_api import Locator, Page, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "docs" / "design-references"
URL = "http://localhost:3000"
MENU_SCREENSHOT = (
    REFERENCE_DIR
    / "liblib-clone-batch30-picture-edit-menu-929-2026-08-25.png"
)
FEEDBACK_SCREENSHOT = (
    REFERENCE_DIR
    / "liblib-clone-batch30-duration-feedback-929-2026-08-25.png"
)
PANEL_SCREENSHOT = (
    REFERENCE_DIR / "liblib-clone-batch30-matting-panel-929-2026-08-25.png"
)
GRAPH_SCREENSHOT = (
    REFERENCE_DIR / "liblib-clone-batch30-matting-graph-929-2026-08-25.png"
)
MOBILE_SCREENSHOT = (
    REFERENCE_DIR / "liblib-clone-batch30-matting-mobile-390-2026-08-25.png"
)
CONTACT_SHEET = (
    REFERENCE_DIR
    / "liblib-clone-batch30-smart-matting-contact-sheet-2026-08-25.png"
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


def assert_close(actual: float, expected: float, tolerance: float = 0.9):
    assert abs(actual - expected) <= tolerance, (actual, expected)


def assert_no_overflow(page: Page):
    assert page.evaluate(
        "document.documentElement.scrollWidth <= document.documentElement.clientWidth"
    )
    assert page.evaluate(
        "document.body.scrollWidth <= document.body.clientWidth"
    )


def assert_processing_toolbar_anchor(page: Page, source: Locator):
    toolbar = page.locator(".react-flow__node-toolbar").first
    toolbar_box = box(toolbar)
    source_box = box(source)
    assert_close(toolbar_box["height"], 49)
    assert_close(center_x(toolbar_box), center_x(source_box))
    assert page.locator("[data-video-depth-motion-trigger]").count() == 1
    return toolbar_box


def switch_to_empty_canvas(page: Page):
    page.goto(URL, wait_until="networkidle")
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
    assert "视频节点 5-片段重拍" in source.inner_text()
    assert page.locator("[data-video-generation-panel]").count() == 1
    assert page.locator("[data-video-picture-edit-menu-trigger]").count() == 1
    return source, source_id


def menu_trigger(page: Page):
    return page.locator("[data-video-picture-edit-menu-trigger]")


def open_picture_edit_menu(page: Page, via_hover: bool = False):
    trigger = menu_trigger(page)
    assert trigger.inner_text().strip() == "主体消除"
    assert trigger.locator(".lucide-chevron-down").count() == 1
    if via_hover:
        trigger.hover()
        page.wait_for_timeout(70)
        assert page.locator('[data-video-toolbar-menu="picture-edit"]').count() == 0
        page.wait_for_timeout(70)
    else:
        trigger.click()

    menu = page.locator('[data-video-toolbar-menu="picture-edit"]')
    menu.wait_for(state="visible")
    items = menu.locator("[data-video-picture-edit-action]")
    assert items.all_inner_texts() == [
        "主体消除",
        "主体修改",
        "主体替换",
        "智能抠像",
    ]
    assert items.nth(0).get_attribute("data-video-picture-edit-action") == (
        "subjectRemove"
    )
    assert items.nth(1).get_attribute("data-video-picture-edit-action") == (
        "subjectModify"
    )
    assert items.nth(2).get_attribute("data-video-picture-edit-action") == (
        "subjectReplace"
    )
    assert items.nth(3).get_attribute("data-video-picture-edit-action") == (
        "matting"
    )

    trigger_box = box(trigger)
    menu_box = box(menu)
    assert_close(center_x(menu_box), center_x(trigger_box))
    assert_close(menu_box["width"], 160)
    assert_close(
        menu_box["y"] - (trigger_box["y"] + trigger_box["height"]),
        7,
    )
    audio_box = box(page.locator("[data-video-audio-menu-trigger]"))
    frame_box = box(page.locator("[data-video-frame-menu-trigger]"))
    download_box = box(page.get_by_role("link", name="下载视频封面"))
    assert audio_box["x"] < trigger_box["x"] < frame_box["x"] < download_box["x"]
    return trigger, menu


def assert_hover_close_delay(page: Page, menu: Locator):
    page.mouse.move(24, 720)
    page.wait_for_timeout(70)
    assert menu.count() == 1
    page.wait_for_timeout(70)
    assert page.locator('[data-video-toolbar-menu="picture-edit"]').count() == 0


def run_primary_flow(page: Page):
    errors = attach_errors(page)
    switch_to_empty_canvas(page)
    source, source_id = add_ready_video(page)

    trigger, menu = open_picture_edit_menu(page, via_hover=True)
    assert_processing_toolbar_anchor(page, source)
    page.screenshot(path=str(MENU_SCREENSHOT))
    assert_hover_close_delay(page, menu)

    for action in ("subjectRemove", "subjectModify", "subjectReplace"):
        _, menu = open_picture_edit_menu(page)
        menu.locator(f'[data-video-picture-edit-action="{action}"]').click()
        feedback = page.locator("[data-video-picture-edit-feedback]")
        assert feedback.inner_text() == "视频大于15秒，暂不支持该功能"
        assert page.locator(".react-flow__node").count() == 1
        assert page.locator(".react-flow__edge").count() == 0
        assert page.locator(".react-flow__node.selected").get_attribute(
            "data-id"
        ) == source_id
    page.screenshot(path=str(FEEDBACK_SCREENSHOT))

    _, menu = open_picture_edit_menu(page)
    menu.locator('[data-video-picture-edit-action="matting"]').click()
    panel = page.locator("[data-smart-matting-panel]")
    assert panel.count() == 1
    assert page.locator("[data-video-generation-panel]").count() == 0
    assert page.locator("[data-smart-matting-power]").inner_text().strip() == "--"
    panel_box = box(panel)
    source_box = box(source)
    assert_close(panel_box["width"], 512)
    assert_close(panel_box["height"], 48)
    assert_close(center_x(panel_box), center_x(source_box))
    assert_close(panel_box["y"] - (source_box["y"] + source_box["height"]), 16)
    page.screenshot(path=str(PANEL_SCREENSHOT))

    page.locator("[data-smart-matting-close]").click()
    assert page.locator("[data-smart-matting-panel]").count() == 0
    assert page.locator("[data-video-generation-panel]").count() == 1

    _, menu = open_picture_edit_menu(page)
    menu.locator('[data-video-picture-edit-action="matting"]').click()
    generate = page.locator("[data-smart-matting-generate]")
    generate.click()
    assert page.locator("[data-smart-matting-submitting]").count() == 1
    assert generate.is_disabled()
    page.wait_for_timeout(560)

    output = page.locator("[data-smart-matting-output]")
    assert output.count() == 1
    assert output.get_attribute("data-smart-matting-source-id") == source_id
    edge_id = output.get_attribute("data-smart-matting-edge-id")
    assert edge_id
    assert output.get_attribute("data-smart-matting-provider") == "volcano"
    assert output.get_attribute("data-smart-matting-model") == (
        "volcano-portrait-matting"
    )
    assert output.get_attribute("data-smart-matting-format") == "WEBM"
    assert output.get_attribute("data-smart-matting-width") == "1280"
    assert output.get_attribute("data-smart-matting-height") == "720"
    assert output.get_attribute("data-smart-matting-duration") == "30"
    assert "智能抠像结果" in output.inner_text()
    assert "智能抠像 · 等待媒体资源" in output.inner_text()

    output_shell = output.locator(
        "xpath=ancestor::div[contains(@class, 'react-flow__node')][1]"
    )
    output_id = output_shell.get_attribute("data-id")
    assert output_id
    assert "视频节点 5-片段重拍-智能抠像" in output_shell.inner_text()
    edge = page.locator(
        f'.react-flow__edge[aria-label="Edge from {source_id} to {output_id}"]'
    )
    assert edge.count() == 1
    assert edge.get_attribute("data-id") == edge_id
    assert page.locator(".react-flow__node").count() == 2
    assert page.locator(".react-flow__edge").count() == 1
    assert page.locator(".react-flow__node.selected").get_attribute(
        "data-id"
    ) == source_id
    assert page.locator("[data-smart-matting-panel]").count() == 0
    assert page.locator("[data-video-generation-panel]").count() == 1

    source_box = box(source)
    output_box = box(output_shell)
    zoom = source_box["width"] / 512
    assert_close(
        output_box["x"] - source_box["x"],
        source_box["width"] + 100 * zoom,
        1.5,
    )
    assert_close(output_box["y"], source_box["y"], 1.5)

    page.keyboard.press("Meta+z")
    page.wait_for_timeout(150)
    assert page.locator(".react-flow__node").count() == 1
    assert page.locator(".react-flow__edge").count() == 0
    assert page.locator(f'.react-flow__node[data-id="{output_id}"]').count() == 0

    page.keyboard.press("Meta+Shift+z")
    page.wait_for_timeout(150)
    assert page.locator(".react-flow__node").count() == 2
    assert page.locator(".react-flow__edge").count() == 1
    assert page.locator(f'.react-flow__node[data-id="{output_id}"]').count() == 1

    source.click(position={"x": 20, "y": 20}, force=True)
    _, menu = open_picture_edit_menu(page)
    menu.locator('[data-video-picture-edit-action="matting"]').click()
    page.locator("[data-smart-matting-generate]").click()
    page.wait_for_timeout(560)
    outputs = page.locator("[data-smart-matting-output]")
    assert outputs.count() == 2
    first_box = box(
        outputs.nth(0).locator(
            "xpath=ancestor::div[contains(@class, 'react-flow__node')][1]"
        )
    )
    second_box = box(
        outputs.nth(1).locator(
            "xpath=ancestor::div[contains(@class, 'react-flow__node')][1]"
        )
    )
    assert_close(second_box["x"], first_box["x"], 1.5)
    assert_close(
        second_box["y"] - first_box["y"],
        (288 + 48) * zoom,
        1.5,
    )
    assert page.locator(".react-flow__node.selected").get_attribute(
        "data-id"
    ) == source_id

    page.keyboard.press("Meta+0")
    page.wait_for_timeout(320)
    page.screenshot(path=str(GRAPH_SCREENSHOT))
    assert_no_overflow(page)
    assert not errors, errors
    return trigger


def run_multi_selection(page: Page):
    errors = attach_errors(page)
    switch_to_empty_canvas(page)
    source, _ = add_ready_video(page)
    page.get_by_role("button", name="添加节点").click()
    page.locator('[data-add-node-entry="text"]').click()
    source.click(position={"x": 12, "y": 12}, modifiers=["Meta"], force=True)
    page.wait_for_timeout(150)
    assert page.locator(".react-flow__node.selected").count() == 2
    assert page.locator("[data-video-picture-edit-menu-trigger]").count() == 0
    assert page.locator("[data-smart-matting-panel]").count() == 0
    assert page.locator(".react-flow__node-toolbar").count() == 0
    assert_no_overflow(page)
    assert not errors, errors


def run_mobile(page: Page):
    errors = attach_errors(page)
    switch_to_empty_canvas(page)
    source, _ = add_ready_video(page)
    toolbar_box = assert_processing_toolbar_anchor(page, source)
    assert toolbar_box["x"] < 0
    assert toolbar_box["x"] + toolbar_box["width"] > 390

    trigger = menu_trigger(page)
    trigger.evaluate("(element) => element.click()")
    menu = page.locator('[data-video-toolbar-menu="picture-edit"]')
    menu.locator('[data-video-picture-edit-action="matting"]').click()
    panel = page.locator("[data-smart-matting-panel]")
    page.wait_for_timeout(120)
    panel_box = box(panel)
    source_box = box(source)
    assert_close(panel_box["width"], 512)
    assert panel_box["x"] < 0
    assert_close(center_x(panel_box), center_x(source_box))
    assert_no_overflow(page)
    page.screenshot(path=str(MOBILE_SCREENSHOT))
    assert not errors, errors


def save_contact_sheet():
    menu = Image.open(MENU_SCREENSHOT).convert("RGB")
    feedback = Image.open(FEEDBACK_SCREENSHOT).convert("RGB")
    panel = Image.open(PANEL_SCREENSHOT).convert("RGB")
    graph = Image.open(GRAPH_SCREENSHOT).convert("RGB")
    mobile = Image.open(MOBILE_SCREENSHOT).convert("RGB")
    label_height = 28
    gutter = 12
    first_row_width = menu.width + feedback.width + gutter
    second_row_width = panel.width + graph.width + gutter
    width = max(first_row_width, second_row_width, mobile.width)
    first_row_height = max(menu.height, feedback.height)
    second_row_height = max(panel.height, graph.height)
    height = (
        label_height
        + first_row_height
        + gutter
        + label_height
        + second_row_height
        + gutter
        + label_height
        + mobile.height
    )
    sheet = Image.new("RGB", (width, height), "#141414")
    draw = ImageDraw.Draw(sheet)
    draw.text((8, 8), "source-order picture edit menu 929x874", fill="#ededed")
    draw.text(
        (menu.width + gutter + 8, 8),
        "30-second subject validation 929x874",
        fill="#ededed",
    )
    sheet.paste(menu, (0, label_height))
    sheet.paste(feedback, (menu.width + gutter, label_height))

    second_y = label_height + first_row_height + gutter
    draw.text(
        (8, second_y + 8),
        "node-bottom smart matting panel 929x874",
        fill="#ededed",
    )
    draw.text(
        (panel.width + gutter + 8, second_y + 8),
        "source -> repeated matting outputs 929x874",
        fill="#ededed",
    )
    sheet.paste(panel, (0, second_y + label_height))
    sheet.paste(graph, (panel.width + gutter, second_y + label_height))

    mobile_y = second_y + label_height + second_row_height + gutter
    draw.text(
        (8, mobile_y + 8),
        "mobile natural clipping 390x844",
        fill="#ededed",
    )
    sheet.paste(mobile, (0, mobile_y + label_height))
    sheet.save(CONTACT_SHEET)


def main():
    REFERENCE_DIR.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        desktop = browser.new_page(viewport={"width": 929, "height": 874})
        run_primary_flow(desktop)

        multi = browser.new_page(viewport={"width": 929, "height": 874})
        run_multi_selection(multi)

        mobile = browser.new_page(viewport={"width": 390, "height": 844})
        run_mobile(mobile)

        browser.close()

    save_contact_sheet()
    print(
        "Batch 30 verified: source-backed picture-edit menu, hover timing, "
        "duration guard, smart-matting panel, pending graph, metadata, "
        "selection/history, repeated slots, multi-select and mobile clipping."
    )


if __name__ == "__main__":
    main()
