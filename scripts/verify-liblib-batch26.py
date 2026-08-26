from pathlib import Path

from PIL import Image, ImageDraw
from playwright.sync_api import Locator, Page, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "docs" / "design-references"
URL = "http://localhost:3000"
DEFAULT_SCREENSHOT = (
    REFERENCE_DIR
    / "liblib-clone-batch26-continuation-default-929-2026-08-25.png"
)
ADJUSTED_SCREENSHOT = (
    REFERENCE_DIR
    / "liblib-clone-batch26-continuation-adjusted-929-2026-08-25.png"
)
TARGET_SCREENSHOT = (
    REFERENCE_DIR
    / "liblib-clone-batch26-continuation-target-929-2026-08-25.png"
)
MOBILE_SCREENSHOT = (
    REFERENCE_DIR
    / "liblib-clone-batch26-continuation-mobile-390-2026-08-25.png"
)
CONTACT_SHEET = (
    REFERENCE_DIR
    / "liblib-clone-batch26-continuation-contact-sheet-2026-08-25.png"
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


def open_selector(page: Page):
    page.get_by_role("button", name="智能续写", exact=True).click()
    selector = page.locator("[data-video-continuation-selector]")
    selector.wait_for(state="visible")
    assert page.locator("[data-video-generation-panel]").count() == 0
    assert page.locator("[data-segment-reshoot-panel]").count() == 0
    return selector


def read_range(page: Page):
    duration = page.locator("[data-video-continuation-duration]")
    return (
        float(duration.get_attribute("data-start-seconds") or "nan"),
        float(duration.get_attribute("data-end-seconds") or "nan"),
    )


def assert_selector_structure(
    page: Page,
    source: Locator,
    selector: Locator,
):
    source_box = box(source)
    selector_box = box(selector)
    timeline_box = box(page.locator("[data-video-continuation-timeline]"))
    start_box = box(page.locator("[data-video-continuation-start]"))
    end_box = box(page.locator("[data-video-continuation-end]"))
    close_box = box(page.locator("[data-video-continuation-close]"))
    confirm_box = box(page.locator("[data-video-continuation-confirm]"))
    zoom = source_box["width"] / 512

    assert_close(selector_box["width"], 660)
    assert_close(selector_box["height"], 56)
    assert_close(timeline_box["height"], 48)
    assert_close(start_box["width"], 16)
    assert_close(end_box["width"], 16)
    assert_close(close_box["width"], 32)
    assert_close(close_box["height"], 32)
    assert_close(confirm_box["height"], 32)
    assert_close(center_x(selector_box), center_x(source_box))
    assert_close(
        selector_box["y"] - (source_box["y"] + source_box["height"]),
        8 * zoom,
    )
    assert page.locator(
        "[data-video-continuation-timeline]"
    ).get_attribute("aria-label") == "请截取续写前置视频"
    classes = (selector.get_attribute("class") or "").split()
    assert {"nodrag", "nowheel", "nopan"}.issubset(classes)
    return source_box, selector_box


def drag_to(page: Page, locator: Locator, target_x: float):
    locator_box = box(locator)
    start = (
        locator_box["x"] + locator_box["width"] / 2,
        locator_box["y"] + locator_box["height"] / 2,
    )
    page.mouse.move(*start)
    page.mouse.down()
    page.mouse.move((start[0] + target_x) / 2, start[1], steps=4)
    page.mouse.move(target_x, start[1], steps=4)
    page.mouse.up()
    page.wait_for_timeout(120)


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


def zoom_to_50(page: Page):
    trigger = page.get_by_role("button", name="缩放选项")
    trigger.click()
    page.get_by_role("button", name="缩放至50%", exact=True).click()
    page.wait_for_timeout(240)
    if page.locator('[data-liblib-overlay="zoom-menu"]').is_visible():
        trigger.click()


def run_selector_interaction(page: Page):
    errors = attach_errors(page)
    switch_to_empty_canvas(page)
    source, _ = add_ready_video(page)
    selector = open_selector(page)
    source_box, selector_box = assert_selector_structure(page, source, selector)

    start_seconds, end_seconds = read_range(page)
    assert_close(start_seconds, 0)
    assert_close(end_seconds, 30)
    assert page.locator(
        "[data-video-continuation-duration]"
    ).inner_text() == "30.00 秒"
    page.screenshot(path=str(DEFAULT_SCREENSHOT))

    timeline_box = box(page.locator("[data-video-continuation-timeline]"))
    drag_to(
        page,
        page.locator("[data-video-continuation-end]"),
        timeline_box["x"] + timeline_box["width"] * 0.02,
    )
    start_seconds, end_seconds = read_range(page)
    assert_close(start_seconds, 0)
    assert_close(end_seconds, 4)

    drag_to(
        page,
        page.locator("[data-video-continuation-end]"),
        timeline_box["x"] + timeline_box["width"] * 0.6,
    )
    start_seconds, end_seconds = read_range(page)
    assert_close(start_seconds, 0)
    assert_close(end_seconds, 18, 0.15)

    drag_to(
        page,
        page.locator("[data-video-continuation-start]"),
        timeline_box["x"] + timeline_box["width"] * 0.2,
    )
    start_seconds, end_seconds = read_range(page)
    assert_close(start_seconds, 6, 0.15)
    assert_close(end_seconds, 18, 0.15)
    selected_duration = end_seconds - start_seconds

    drag_by(page, page.locator("[data-video-continuation-region]"), 50)
    moved_start, moved_end = read_range(page)
    assert moved_start > start_seconds
    assert moved_end > end_seconds
    assert_close(moved_end - moved_start, selected_duration, 0.02)
    assert 0 <= moved_start < moved_end <= 30
    assert 4 <= moved_end - moved_start <= 30
    page.screenshot(path=str(ADJUSTED_SCREENSHOT))

    zoom_to_50(page)
    zoom_source_before, zoom_selector_before = assert_selector_structure(
        page,
        source,
        selector,
    )
    assert_close(zoom_source_before["width"], 256)
    drag_by(page, source, 42, 26)
    zoom_source_after, zoom_selector_after = assert_selector_structure(
        page,
        source,
        selector,
    )
    assert_same_delta(
        zoom_source_before,
        zoom_source_after,
        zoom_selector_before,
        zoom_selector_after,
    )

    page.mouse.move(180, 120)
    page.mouse.wheel(70, 45)
    page.wait_for_timeout(180)
    pan_source, pan_selector = assert_selector_structure(page, source, selector)
    assert_same_delta(
        zoom_source_after,
        pan_source,
        zoom_selector_after,
        pan_selector,
    )

    page.get_by_role("button", name="添加节点").click()
    page.locator('[data-add-node-entry="text"]').click()
    assert page.locator("[data-video-continuation-selector]").count() == 0
    source.click(position={"x": 12, "y": 12}, modifiers=["Meta"], force=True)
    page.wait_for_timeout(160)
    assert page.locator(".react-flow__node.selected").count() == 2
    assert page.locator("[data-video-continuation-selector]").count() == 0
    assert_no_overflow(page)
    assert not errors, errors


def assert_target_contract(
    page: Page,
    source: Locator,
    source_id: str,
    target: Locator,
    target_id: str,
):
    assert target.count() == 1
    assert "selected" in (target.get_attribute("class") or "")
    assert "续写 视频节点 5-片段重拍" in target.inner_text()
    assert page.locator("[data-video-continuation-empty]").count() == 1
    assert "等待续写内容" in target.inner_text()
    edge = page.locator(
        f'.react-flow__edge[aria-label="Edge from {source_id} to {target_id}"]'
    )
    assert edge.count() == 1

    context = page.locator("[data-video-continuation-context]")
    assert context.count() == 1
    assert "对 视频节点 5-片段重拍 的" in context.inner_text()
    assert "片段进行续写：" in context.inner_text()
    range_label = page.locator("[data-video-continuation-range]").inner_text()
    assert range_label.endswith("s")
    assert "-" in range_label
    prompt = page.get_by_label("视频生成提示词")
    assert prompt.get_attribute("placeholder") == "请输入需要续写的内容"
    assert page.locator("[data-video-continuation-source]").count() == 1
    assert "智能续写仅支持 Seedance 2.5 的全能参考模式" in target.inner_text()
    assert page.locator("[data-video-continuation-exit]").inner_text() == (
        "退出续写模式"
    )

    model = page.locator("[data-video-model-trigger]")
    mode = page.locator("[data-video-mode-trigger]")
    assert model.inner_text().strip() == "2.5"
    assert mode.inner_text().strip() == "全能参考"
    assert model.is_disabled()
    assert mode.is_disabled()
    assert model.get_attribute("data-video-continuation-locked") == "true"
    assert mode.get_attribute("data-video-continuation-locked") == "true"

    source_box = box(source)
    target_box = box(target)
    zoom = target_box["width"] / 512
    assert_close(
        target_box["x"] - source_box["x"],
        source_box["width"] + 120 * zoom,
        1.3,
    )
    assert_close(target_box["y"], source_box["y"], 1.3)
    panel_box = box(page.locator("[data-video-generation-panel]"))
    assert_close(panel_box["width"], 660)
    assert_close(panel_box["height"], 274)
    assert_close(center_x(panel_box), center_x(target_box))
    assert_close(
        panel_box["y"] - (target_box["y"] + target_box["height"]),
        16 * zoom,
    )


def run_graph_lifecycle(page: Page):
    errors = attach_errors(page)
    switch_to_empty_canvas(page)
    source, source_id = add_ready_video(page)
    selector = open_selector(page)

    page.locator("[data-video-continuation-close]").click()
    assert page.locator("[data-video-continuation-selector]").count() == 0
    assert page.locator("[data-video-generation-panel]").count() == 1
    selector = open_selector(page)
    page.keyboard.press("Escape")
    assert page.locator("[data-video-continuation-selector]").count() == 0
    assert page.locator("[data-video-generation-panel]").count() == 1
    assert "selected" in (source.get_attribute("class") or "")

    selector = open_selector(page)
    timeline_box = box(page.locator("[data-video-continuation-timeline]"))
    drag_to(
        page,
        page.locator("[data-video-continuation-start]"),
        timeline_box["x"] + timeline_box["width"] * 0.2,
    )
    start_seconds, end_seconds = read_range(page)
    assert_close(start_seconds, 6, 0.15)
    assert_close(end_seconds, 30)

    assert page.locator(".react-flow__node").count() == 1
    assert page.locator(".react-flow__edge").count() == 0
    page.locator("[data-video-continuation-confirm]").click()
    page.wait_for_timeout(240)
    assert page.locator(".react-flow__node").count() == 2
    assert page.locator(".react-flow__edge").count() == 1
    target = page.locator(".react-flow__node-video.selected")
    target_id = target.get_attribute("data-id")
    assert target_id and target_id != source_id
    assert_target_contract(page, source, source_id, target, target_id)

    page.keyboard.press("Meta+0")
    page.wait_for_timeout(320)
    target = page.locator(f'.react-flow__node[data-id="{target_id}"]')
    assert_target_contract(page, source, source_id, target, target_id)
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
    page.wait_for_timeout(120)
    assert page.locator("[data-video-continuation-context]").count() == 1

    page.locator("[data-video-continuation-exit]").click()
    page.wait_for_timeout(140)
    assert page.locator(".react-flow__node").count() == 2
    assert page.locator(".react-flow__edge").count() == 0
    assert page.locator(f'.react-flow__node[data-id="{target_id}"]').count() == 1
    assert page.locator("[data-video-continuation-context]").count() == 0
    assert page.locator("[data-video-continuation-exit]").count() == 0
    assert not page.locator("[data-video-model-trigger]").is_disabled()
    assert not page.locator("[data-video-mode-trigger]").is_disabled()

    page.keyboard.press("Meta+z")
    page.wait_for_timeout(160)
    assert page.locator(".react-flow__edge").count() == 1
    target.click(position={"x": 12, "y": 12}, force=True)
    page.wait_for_timeout(100)
    assert page.locator("[data-video-continuation-context]").count() == 1

    page.keyboard.press("Meta+Shift+z")
    page.wait_for_timeout(160)
    assert page.locator(".react-flow__edge").count() == 0
    target.click(position={"x": 12, "y": 12}, force=True)
    page.wait_for_timeout(100)
    assert page.locator("[data-video-continuation-context]").count() == 0
    assert page.locator(f'.react-flow__node[data-id="{target_id}"]').count() == 1
    assert_no_overflow(page)
    assert not errors, errors


def run_mobile(page: Page):
    errors = attach_errors(page)
    switch_to_empty_canvas(page)
    source, _ = add_ready_video(page)
    page.get_by_role("button", name="智能续写", exact=True).evaluate(
        "(element) => element.click()"
    )
    selector = page.locator("[data-video-continuation-selector]")
    selector.wait_for(state="visible")
    assert_selector_structure(page, source, selector)
    selector_box = box(selector)
    assert selector_box["x"] < 0
    assert selector_box["x"] + selector_box["width"] > 390
    assert_no_overflow(page)
    page.screenshot(path=str(MOBILE_SCREENSHOT))
    assert not errors, errors


def save_contact_sheet():
    default = Image.open(DEFAULT_SCREENSHOT).convert("RGB")
    adjusted = Image.open(ADJUSTED_SCREENSHOT).convert("RGB")
    target = Image.open(TARGET_SCREENSHOT).convert("RGB")
    mobile = Image.open(MOBILE_SCREENSHOT).convert("RGB")
    label_height = 28
    gutter = 12
    first_row_width = default.width + adjusted.width + gutter
    second_row_width = target.width + mobile.width + gutter
    width = max(first_row_width, second_row_width)
    first_row_height = max(default.height, adjusted.height)
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
    draw.text((8, 8), "default 0-30s 929x874", fill="#ededed")
    draw.text(
        (default.width + gutter + 8, 8),
        "adjusted handles + region 929x874",
        fill="#ededed",
    )
    sheet.paste(default, (0, label_height))
    sheet.paste(adjusted, (default.width + gutter, label_height))
    second_y = label_height + first_row_height + gutter
    draw.text((8, second_y + 8), "continuation target 929x874", fill="#ededed")
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
        interaction = browser.new_page(
            viewport={"width": 929, "height": 874},
            device_scale_factor=1,
        )
        run_selector_interaction(interaction)
        interaction.close()
        lifecycle = browser.new_page(
            viewport={"width": 929, "height": 874},
            device_scale_factor=1,
        )
        run_graph_lifecycle(lifecycle)
        lifecycle.close()
        mobile = browser.new_page(
            viewport={"width": 390, "height": 844},
            device_scale_factor=1,
        )
        run_mobile(mobile)
        mobile.close()
        browser.close()
    save_contact_sheet()
    print(
        "Batch26 Playwright verification passed: 660x56 continuation selector, "
        "8*zoom anchor, 0-30s initial range, handle/region constraints, close/"
        "Escape, target node/edge transaction, continuation Prompt contract, "
        "fixed model/mode, exit preservation, create/clear undo-redo, zoom/drag/"
        "pan following, multi-selection hiding, mobile clipping, screenshots "
        "and zero browser errors."
    )


if __name__ == "__main__":
    main()
