from pathlib import Path

from PIL import Image, ImageDraw
from playwright.sync_api import Locator, Page, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "docs" / "design-references"
URL = "http://localhost:3000"
SMART_SCREENSHOT = (
    REFERENCE_DIR / "liblib-clone-batch27-subtitle-smart-929-2026-08-25.png"
)
REGION_SCREENSHOT = (
    REFERENCE_DIR / "liblib-clone-batch27-subtitle-region-929-2026-08-25.png"
)
TARGET_SCREENSHOT = (
    REFERENCE_DIR / "liblib-clone-batch27-subtitle-target-929-2026-08-25.png"
)
MOBILE_SCREENSHOT = (
    REFERENCE_DIR / "liblib-clone-batch27-subtitle-mobile-390-2026-08-25.png"
)
CONTACT_SHEET = (
    REFERENCE_DIR
    / "liblib-clone-batch27-subtitle-contact-sheet-2026-08-25.png"
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


def center_y(rect):
    return rect["y"] + rect["height"] / 2


def assert_close(actual: float, expected: float, tolerance: float = 0.9):
    assert abs(actual - expected) <= tolerance, (actual, expected)


def assert_same_delta(before_a, after_a, before_b, after_b, tolerance=1.2):
    assert_close(
        after_a["x"] - before_a["x"],
        after_b["x"] - before_b["x"],
        tolerance,
    )
    assert_close(
        after_a["y"] - before_a["y"],
        after_b["y"] - before_b["y"],
        tolerance,
    )


def assert_no_overflow(page: Page):
    assert page.evaluate(
        "document.documentElement.scrollWidth <= document.documentElement.clientWidth"
    )
    assert page.evaluate(
        "document.body.scrollWidth <= document.body.clientWidth"
    )


def switch_to_empty_canvas(page: Page):
    page.goto(URL, wait_until="domcontentloaded")
    page.wait_for_timeout(600)
    page.locator("[data-canvas-trigger]").click()
    page.locator('[data-canvas-row="canvas-1"] button').first.click()
    page.wait_for_timeout(180)
    assert page.locator(".react-flow__node").count() == 0


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
    return source, source_id


def open_subtitle_menu(page: Page):
    trigger = page.locator("[data-video-subtitle-menu-trigger]")
    assert trigger.get_attribute("title") == "AI一键去除视频字幕，仅支持中英文字幕"
    trigger.click()
    menu = page.locator('[data-video-toolbar-menu="subtitle"]')
    menu.wait_for(state="visible")
    assert menu.locator('[data-video-subtitle-mode="smart"]').inner_text() == "智能去字幕"
    assert menu.locator('[data-video-subtitle-mode="region"]').inner_text() == "框选去字幕"
    return menu


def open_subtitle_mode(page: Page, mode: str):
    menu = open_subtitle_menu(page)
    menu.locator(f'[data-video-subtitle-mode="{mode}"]').click()
    panel = page.locator("[data-subtitle-erase-panel]")
    panel.wait_for(state="visible")
    assert panel.locator("[data-subtitle-erase-mode]").get_attribute(
        "data-subtitle-erase-mode"
    ) == mode
    assert page.locator("[data-video-generation-panel]").count() == 0
    assert page.locator(".react-flow__node-toolbar").count() == 0
    return panel


def assert_panel_structure(page: Page, source: Locator, panel: Locator):
    source_box = box(source)
    panel_box = box(panel)
    close_box = box(page.locator("[data-subtitle-erase-close]"))
    submit_box = box(page.locator("[data-subtitle-erase-submit]"))
    zoom = source_box["width"] / 512

    assert_close(panel_box["height"], 48)
    assert_close(close_box["width"], 32)
    assert_close(close_box["height"], 32)
    assert_close(submit_box["width"], 28)
    assert_close(submit_box["height"], 28)
    assert_close(center_x(panel_box), center_x(source_box))
    assert_close(
        panel_box["y"] - (source_box["y"] + source_box["height"]),
        16 * zoom,
    )
    assert page.locator("[data-subtitle-erase-cost]").inner_text().strip() == "-"
    classes = (panel.get_attribute("class") or "").split()
    assert {"nodrag", "nowheel", "nopan"}.issubset(classes)
    return source_box, panel_box


def drag_by(page: Page, locator: Locator, dx: float, dy: float = 0):
    locator_box = box(locator)
    start = (
        locator_box["x"] + locator_box["width"] / 2,
        locator_box["y"] + locator_box["height"] / 2,
    )
    page.mouse.move(*start)
    page.mouse.down()
    page.mouse.move(start[0] + dx / 2, start[1] + dy / 2, steps=4)
    page.mouse.move(start[0] + dx, start[1] + dy, steps=4)
    page.mouse.up()
    page.wait_for_timeout(160)


def draw_region(
    page: Page,
    overlay: Locator,
    start: tuple[float, float],
    end: tuple[float, float],
):
    overlay_box = box(overlay)
    start_point = (
        overlay_box["x"] + overlay_box["width"] * start[0],
        overlay_box["y"] + overlay_box["height"] * start[1],
    )
    end_point = (
        overlay_box["x"] + overlay_box["width"] * end[0],
        overlay_box["y"] + overlay_box["height"] * end[1],
    )
    page.mouse.move(*start_point)
    page.mouse.down()
    page.mouse.move(
        (start_point[0] + end_point[0]) / 2,
        (start_point[1] + end_point[1]) / 2,
        steps=4,
    )
    page.mouse.move(*end_point, steps=4)
    page.mouse.up()
    page.wait_for_timeout(140)


def region_values(region: Locator):
    return {
        "x": float(region.get_attribute("data-rel-x") or "nan"),
        "y": float(region.get_attribute("data-rel-y") or "nan"),
        "width": float(region.get_attribute("data-rel-width") or "nan"),
        "height": float(region.get_attribute("data-rel-height") or "nan"),
    }


def zoom_to_50(page: Page):
    trigger = page.get_by_role("button", name="缩放选项")
    trigger.click()
    page.get_by_role("button", name="缩放至50%", exact=True).click()
    page.wait_for_timeout(240)
    if page.locator('[data-liblib-overlay="zoom-menu"]').is_visible():
        trigger.click()


def run_smart_panel_and_anchor(page: Page):
    errors = attach_errors(page)
    switch_to_empty_canvas(page)
    source, _ = add_ready_video(page)
    panel = open_subtitle_mode(page, "smart")
    assert_panel_structure(page, source, panel)
    assert page.locator("[data-subtitle-region-overlay]").count() == 0
    assert page.locator("[data-subtitle-erase-help]").count() == 0
    assert not page.locator("[data-subtitle-erase-submit]").is_disabled()
    page.screenshot(path=str(SMART_SCREENSHOT))

    page.locator("[data-subtitle-erase-close]").click()
    assert page.locator("[data-subtitle-erase-panel]").count() == 0
    assert page.locator("[data-video-generation-panel]").count() == 1
    assert page.locator(".react-flow__node-toolbar").count() == 1

    panel = open_subtitle_mode(page, "smart")
    page.keyboard.press("Escape")
    assert page.locator("[data-subtitle-erase-panel]").count() == 0
    assert page.locator("[data-video-generation-panel]").count() == 1
    assert "selected" in (source.get_attribute("class") or "")

    zoom_to_50(page)
    panel = open_subtitle_mode(page, "smart")
    source_before, panel_before = assert_panel_structure(page, source, panel)
    assert_close(source_before["width"], 256)
    drag_by(page, source, 42, 26)
    source_after, panel_after = assert_panel_structure(page, source, panel)
    assert_same_delta(source_before, source_after, panel_before, panel_after)

    page.mouse.move(180, 120)
    page.mouse.wheel(70, 45)
    page.wait_for_timeout(180)
    pan_source, pan_panel = assert_panel_structure(page, source, panel)
    assert_same_delta(source_after, pan_source, panel_after, pan_panel)

    page.get_by_role("button", name="添加节点").click()
    page.locator('[data-add-node-entry="text"]').click()
    assert page.locator("[data-subtitle-erase-panel]").count() == 0
    source.click(position={"x": 12, "y": 12}, modifiers=["Meta"], force=True)
    page.wait_for_timeout(160)
    assert page.locator(".react-flow__node.selected").count() == 2
    assert page.locator("[data-subtitle-erase-panel]").count() == 0
    assert_no_overflow(page)
    assert not errors, errors


def run_region_editor(page: Page):
    errors = attach_errors(page)
    switch_to_empty_canvas(page)
    source, _ = add_ready_video(page)
    zoom_to_50(page)
    assert_close(box(source)["width"], 256)

    panel = open_subtitle_mode(page, "region")
    page.wait_for_timeout(320)
    source_box, _ = assert_panel_structure(page, source, panel)
    assert_close(source_box["width"], 512)
    assert_close(center_x(source_box), 929 / 2, 1.5)
    assert_close(center_y(source_box), 874 / 2, 1.5)

    overlay = page.locator("[data-subtitle-region-overlay]")
    assert overlay.count() == 1
    assert overlay.get_attribute("data-drawing-enabled") == "true"
    submit = page.locator("[data-subtitle-erase-submit]")
    assert submit.is_disabled()
    assert submit.get_attribute("title") == "请选择字幕擦除区域"

    help_button = page.locator("[data-subtitle-erase-help]")
    help_button.hover()
    assert "在画面上拖拽鼠标,框选要擦除的区域" in panel.inner_text()
    assert "支持框选多个区域,所有框内文字将被擦除" in panel.inner_text()
    assert "擦除作用于整段视频,不仅是当前帧" in panel.inner_text()

    draw_region(page, overlay, (0.10, 0.64), (0.50, 0.82))
    assert page.locator("[data-subtitle-region]").count() == 1
    assert not submit.is_disabled()
    first_values = region_values(page.locator("[data-subtitle-region]").first)
    assert_close(first_values["x"], 0.10, 0.01)
    assert_close(first_values["y"], 0.64, 0.01)
    assert_close(first_values["width"], 0.40, 0.01)
    assert_close(first_values["height"], 0.18, 0.01)

    draw_region(page, overlay, (0.58, 0.12), (0.92, 0.30))
    regions = page.locator("[data-subtitle-region]")
    assert regions.count() == 2
    assert (
        regions.nth(1).get_attribute("data-subtitle-region-selected") == "true"
    )
    page.screenshot(path=str(REGION_SCREENSHOT))

    selected = regions.nth(1)
    before_move = region_values(selected)
    drag_by(page, selected, -35, 24)
    selected = page.locator('[data-subtitle-region-selected="true"]')
    after_move = region_values(selected)
    assert after_move["x"] < before_move["x"]
    assert after_move["y"] > before_move["y"]

    before_resize = region_values(selected)
    drag_by(page, selected.locator('[data-subtitle-region-handle="se"]'), 28, 18)
    selected = page.locator('[data-subtitle-region-selected="true"]')
    after_resize = region_values(selected)
    assert after_resize["width"] > before_resize["width"]
    assert after_resize["height"] > before_resize["height"]

    undo = page.locator("[data-subtitle-region-undo]")
    redo = page.locator("[data-subtitle-region-redo]")
    undo.click()
    page.wait_for_timeout(100)
    assert_close(
        region_values(page.locator("[data-subtitle-region]").nth(1))["width"],
        before_resize["width"],
        0.01,
    )
    undo.click()
    page.wait_for_timeout(100)
    assert_close(
        region_values(page.locator("[data-subtitle-region]").nth(1))["x"],
        before_move["x"],
        0.01,
    )
    undo.click()
    page.wait_for_timeout(100)
    assert page.locator("[data-subtitle-region]").count() == 1

    redo.click()
    page.wait_for_timeout(100)
    redo.click()
    page.wait_for_timeout(100)
    redo.click()
    page.wait_for_timeout(100)
    assert page.locator("[data-subtitle-region]").count() == 2
    assert_close(
        region_values(page.locator("[data-subtitle-region]").nth(1))["width"],
        after_resize["width"],
        0.01,
    )

    page.locator("[data-subtitle-region-reset]").click()
    page.wait_for_timeout(100)
    assert page.locator("[data-subtitle-region]").count() == 0
    assert submit.is_disabled()
    undo.click()
    page.wait_for_timeout(100)
    assert page.locator("[data-subtitle-region]").count() == 2

    page.locator("[data-subtitle-region-toggle]").click()
    assert overlay.get_attribute("data-drawing-enabled") == "false"
    draw_region(page, overlay, (0.20, 0.20), (0.35, 0.35))
    assert page.locator("[data-subtitle-region]").count() == 2
    page.locator("[data-subtitle-region-toggle]").click()
    assert_no_overflow(page)
    assert not errors, errors


def assert_target_contract(
    page: Page,
    source: Locator,
    source_id: str,
    mode: str,
):
    target = page.locator(".react-flow__node-video.selected")
    assert target.count() == 1
    target_id = target.get_attribute("data-id")
    assert target_id and target_id != source_id
    assert "视频一键去字幕-视频节点 5-片段重拍" in target.inner_text()
    expected_copy = (
        "点击生成自动去除字幕"
        if mode == "smart"
        else "框选区域生成去字幕视频"
    )
    assert page.locator("[data-subtitle-erase-pending-copy]").inner_text() == (
        expected_copy
    )
    target_body = page.locator("[data-subtitle-erase-target]")
    assert target_body.get_attribute("data-subtitle-erase-target-mode") == mode
    assert target_body.get_attribute("data-subtitle-erase-model") == (
        "volcano-subtitle-eraser"
    )
    assert target_body.get_attribute("data-subtitle-erase-request-mode") == (
        "Subtitle" if mode == "smart" else "Text"
    )
    assert page.locator("[data-video-generation-panel]").count() == 0
    assert page.locator(".react-flow__node-toolbar").count() == 0
    edge = page.locator(
        f'.react-flow__edge[aria-label="Edge from {source_id} to {target_id}"]'
    )
    assert edge.count() == 1

    source_box = box(source)
    target_box = box(target)
    zoom = target_box["width"] / 512
    assert_close(
        target_box["x"] - source_box["x"],
        source_box["width"] + 120 * zoom,
        1.3,
    )
    assert_close(target_box["y"], source_box["y"], 1.3)
    return target, target_id


def run_graph_lifecycle(page: Page, mode: str, save_target: bool = False):
    errors = attach_errors(page)
    switch_to_empty_canvas(page)
    source, source_id = add_ready_video(page)
    open_subtitle_mode(page, mode)
    if mode == "region":
        page.wait_for_timeout(260)
        overlay = page.locator("[data-subtitle-region-overlay]")
        draw_region(page, overlay, (0.12, 0.66), (0.52, 0.84))
        draw_region(page, overlay, (0.60, 0.10), (0.90, 0.28))

    assert page.locator(".react-flow__node").count() == 1
    assert page.locator(".react-flow__edge").count() == 0
    page.locator("[data-subtitle-erase-submit]").click()
    page.wait_for_timeout(240)
    assert page.locator(".react-flow__node").count() == 2
    assert page.locator(".react-flow__edge").count() == 1
    target, target_id = assert_target_contract(
        page,
        source,
        source_id,
        mode,
    )

    if save_target:
        page.keyboard.press("Meta+0")
        page.wait_for_timeout(320)
        target = page.locator(f'.react-flow__node[data-id="{target_id}"]')
        target.click(position={"x": 12, "y": 12}, force=True)
        page.wait_for_timeout(100)
        page.screenshot(path=str(TARGET_SCREENSHOT))

    page.keyboard.press("Meta+z")
    page.wait_for_timeout(160)
    assert page.locator(".react-flow__node").count() == 1
    assert page.locator(".react-flow__edge").count() == 0
    assert page.locator(f'.react-flow__node[data-id="{target_id}"]').count() == 0

    page.keyboard.press("Meta+Shift+z")
    page.wait_for_timeout(160)
    assert page.locator(".react-flow__node").count() == 2
    assert page.locator(".react-flow__edge").count() == 1
    target = page.locator(f'.react-flow__node[data-id="{target_id}"]')
    target.click(position={"x": 12, "y": 12}, force=True)
    page.wait_for_timeout(100)
    assert_target_contract(page, source, source_id, mode)
    assert_no_overflow(page)
    assert not errors, errors


def run_mobile(page: Page):
    errors = attach_errors(page)
    switch_to_empty_canvas(page)
    source, _ = add_ready_video(page)
    panel = open_subtitle_mode(page, "region")
    page.wait_for_timeout(300)
    assert_panel_structure(page, source, panel)
    panel_box = box(panel)
    assert panel_box["x"] < 0
    assert panel_box["x"] + panel_box["width"] > 390
    assert_no_overflow(page)
    page.screenshot(path=str(MOBILE_SCREENSHOT))
    assert not errors, errors


def save_contact_sheet():
    smart = Image.open(SMART_SCREENSHOT).convert("RGB")
    region = Image.open(REGION_SCREENSHOT).convert("RGB")
    target = Image.open(TARGET_SCREENSHOT).convert("RGB")
    mobile = Image.open(MOBILE_SCREENSHOT).convert("RGB")
    label_height = 28
    gutter = 12
    first_row_width = smart.width + region.width + gutter
    second_row_width = target.width + mobile.width + gutter
    width = max(first_row_width, second_row_width)
    first_row_height = max(smart.height, region.height)
    second_row_height = max(target.height, mobile.height)
    height = (
        label_height
        + first_row_height
        + gutter
        + label_height
        + second_row_height
    )
    sheet = Image.new("RGB", (width, height), "#141414")
    draw = ImageDraw.Draw(sheet)
    draw.text((8, 8), "smart compact panel 929x874", fill="#ededed")
    draw.text(
        (smart.width + gutter + 8, 8),
        "region overlay + panel 929x874",
        fill="#ededed",
    )
    sheet.paste(smart, (0, label_height))
    sheet.paste(region, (smart.width + gutter, label_height))
    second_y = label_height + first_row_height + gutter
    draw.text((8, second_y + 8), "pending target + edge 929x874", fill="#ededed")
    draw.text(
        (target.width + gutter + 8, second_y + 8),
        "mobile natural clipping 390x844",
        fill="#ededed",
    )
    sheet.paste(target, (0, second_y + label_height))
    sheet.paste(mobile, (target.width + gutter, second_y + label_height))
    sheet.save(CONTACT_SHEET)


def main():
    REFERENCE_DIR.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        smart = browser.new_page(
            viewport={"width": 929, "height": 874},
            device_scale_factor=1,
        )
        run_smart_panel_and_anchor(smart)
        smart.close()

        region = browser.new_page(
            viewport={"width": 929, "height": 874},
            device_scale_factor=1,
        )
        run_region_editor(region)
        region.close()

        smart_graph = browser.new_page(
            viewport={"width": 929, "height": 874},
            device_scale_factor=1,
        )
        run_graph_lifecycle(smart_graph, "smart")
        smart_graph.close()

        region_graph = browser.new_page(
            viewport={"width": 929, "height": 874},
            device_scale_factor=1,
        )
        run_graph_lifecycle(region_graph, "region", save_target=True)
        region_graph.close()

        mobile = browser.new_page(
            viewport={"width": 390, "height": 844},
            device_scale_factor=1,
        )
        run_mobile(mobile)
        mobile.close()
        browser.close()

    save_contact_sheet()
    print(
        "Batch27 Playwright verification passed: subtitle dropdown/tooltip, "
        "smart compact panel, region focus/overlay/multi-select/move/resize, "
        "atomic undo-redo-reset, submit guard, smart and region pending target "
        "transactions, request metadata, graph undo-redo, zoom/drag/pan "
        "anchoring, multi-selection hiding, mobile clipping, screenshots and "
        "zero browser errors."
    )


if __name__ == "__main__":
    main()
