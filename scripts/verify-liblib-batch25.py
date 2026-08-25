from pathlib import Path

from PIL import Image, ImageDraw
from playwright.sync_api import Locator, Page, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "docs" / "design-references"
URL = "http://localhost:3000"
SOURCE_CONTEXT_SCREENSHOT = (
    REFERENCE_DIR
    / "liblib-clone-batch25-video-clip-source-context-929-2026-08-25.png"
)
DETAIL_SCREENSHOT = (
    REFERENCE_DIR
    / "liblib-clone-batch25-video-clip-detail-929-2026-08-25.png"
)
MOBILE_SCREENSHOT = (
    REFERENCE_DIR
    / "liblib-clone-batch25-video-clip-mobile-390-2026-08-25.png"
)
CONTACT_SHEET = (
    REFERENCE_DIR
    / "liblib-clone-batch25-video-clip-contact-sheet-2026-08-25.png"
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
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(350)
    page.locator("[data-canvas-trigger]").click()
    page.locator('[data-canvas-row="canvas-1"] button').first.click()
    page.wait_for_timeout(180)
    assert page.locator(".react-flow__node").count() == 0


def add_video_clip(page: Page):
    page.get_by_role("button", name="添加节点").click()
    page.locator('[data-add-node-entry="video-clip"]').click()
    node = page.locator(".react-flow__node-video-clip")
    assert node.count() == 1
    assert "selected" in (node.get_attribute("class") or "")
    node_id = node.get_attribute("data-id")
    assert node_id
    panel = page.locator("[data-video-clip-edit-panel]")
    panel.wait_for(state="visible")
    return node, node_id, panel


def assert_structure(
    page: Page,
    node: Locator,
    panel: Locator,
    expected_mode: str | None = None,
    expect_submit_disabled: bool = True,
):
    node_box = box(node)
    panel_box = box(panel)
    zoom = node_box["width"] / 350

    assert_close(node_box["width"], 350 * zoom)
    assert_close(node_box["height"], 350 * zoom)
    assert_close(panel_box["width"], 660)
    assert_close(panel_box["height"], 191)
    assert_close(center_x(panel_box), center_x(node_box))
    assert_close(
        panel_box["y"] - (node_box["y"] + node_box["height"]),
        16 * zoom,
    )

    empty = page.locator("[data-video-clip-empty]")
    assert "空空如也，请连接视频节点后操作" in empty.inner_text()
    assert "尝试：" in empty.inner_text()
    assert empty.locator("textarea").count() == 0
    assert empty.get_by_text("+参考", exact=True).count() == 0
    assert "智能剪辑 Beta" not in empty.inner_text()

    modes = page.locator("[data-video-clip-mode]")
    assert modes.count() == 4
    expected = ["讲解视频", "批量广告", "口播视频", "素材混剪"]
    mode_boxes = []
    for index, label in enumerate(expected):
        mode = modes.nth(index)
        assert mode.inner_text().strip() == label
        assert mode.get_attribute("aria-pressed") == str(
            label == expected_mode
        ).lower()
        mode_boxes.append(box(mode))
    for index in range(1, len(mode_boxes)):
        assert_close(mode_boxes[index]["x"], mode_boxes[0]["x"])
        assert mode_boxes[index]["y"] > mode_boxes[index - 1]["y"]

    assert page.locator("[data-video-clip-reference]").inner_text() == "+参考"
    assert page.locator("[data-video-clip-prompt]").get_attribute(
        "placeholder"
    ) == "描述想剪成什么效果"
    assert page.locator("[data-video-clip-mode-setting]").inner_text().replace(
        "\n", ""
    ) == (expected_mode or "默认模式")
    assert page.locator("[data-video-clip-output-setting]").inner_text().replace(
        "\n", ""
    ) == "16:9 · 720P · 30s"
    assert (
        page.locator("[data-video-clip-submit]").is_disabled()
        == expect_submit_disabled
    )

    classes = (panel.get_attribute("class") or "").split()
    assert {"nodrag", "nowheel", "nopan"}.issubset(classes)
    return node_box, panel_box


def drag(page: Page, start, dx: float, dy: float):
    page.mouse.move(*start)
    page.mouse.down()
    page.mouse.move(start[0] + dx / 2, start[1] + dy / 2, steps=4)
    page.mouse.move(start[0] + dx, start[1] + dy, steps=4)
    page.mouse.up()
    page.wait_for_timeout(180)


def zoom_to_50(page: Page):
    trigger = page.get_by_role("button", name="缩放选项")
    trigger.click()
    page.get_by_role("button", name="缩放至50%", exact=True).click()
    page.wait_for_timeout(240)
    if page.locator('[data-liblib-overlay="zoom-menu"]').is_visible():
        trigger.click()


def run_detail(page: Page):
    errors = attach_errors(page)
    switch_to_empty_canvas(page)
    node, node_id, panel = add_video_clip(page)
    node_box, panel_box = assert_structure(page, node, panel)
    assert_close(node_box["width"], 350)
    assert_close(node_box["height"], 350)
    page.screenshot(path=str(DETAIL_SCREENSHOT))

    page.locator('[data-video-clip-mode="素材混剪"]').click()
    assert page.locator(
        '[data-video-clip-mode="素材混剪"]'
    ).get_attribute("aria-pressed") == "true"
    assert page.locator("[data-video-clip-mode-setting]").inner_text().replace(
        "\n", ""
    ) == "素材混剪"

    page.locator("[data-video-clip-reference]").click()
    assert page.locator("[data-video-clip-status]").inner_text() == (
        "请先连接视频节点后添加参考"
    )
    prompt = page.locator("[data-video-clip-prompt]")
    prompt.fill("把三个咖啡馆镜头剪成 30 秒探店短片")
    assert page.locator("[data-video-clip-status]").count() == 0
    submit = page.locator("[data-video-clip-submit]")
    assert not submit.is_disabled()
    submit.click()
    assert page.locator("[data-video-clip-status]").inner_text() == (
        "已创建本地智能剪辑任务"
    )
    page.get_by_role("button", name="展开智能剪辑编辑器").click()
    assert page.locator("[data-video-clip-status]").inner_text() == (
        "本地原型：展开编辑器未连接"
    )

    zoom_to_50(page)
    zoom_node_before, zoom_panel_before = assert_structure(
        page,
        node,
        panel,
        expected_mode="素材混剪",
        expect_submit_disabled=False,
    )
    assert_close(zoom_node_before["width"], 175)
    assert_close(zoom_panel_before["width"], 660)
    drag(
        page,
        (zoom_node_before["x"] + 12, zoom_node_before["y"] + 12),
        44,
        28,
    )
    zoom_node_after, zoom_panel_after = assert_structure(
        page,
        node,
        panel,
        expected_mode="素材混剪",
        expect_submit_disabled=False,
    )
    assert_same_delta(
        zoom_node_before,
        zoom_node_after,
        zoom_panel_before,
        zoom_panel_after,
    )

    page.mouse.move(180, 120)
    page.mouse.wheel(70, 45)
    page.wait_for_timeout(200)
    pan_node, pan_panel = assert_structure(
        page,
        node,
        panel,
        expected_mode="素材混剪",
        expect_submit_disabled=False,
    )
    assert_same_delta(
        zoom_node_after,
        pan_node,
        zoom_panel_after,
        pan_panel,
    )

    page.get_by_role("button", name="添加节点").click()
    page.locator('[data-add-node-entry="text"]').click()
    text_node = page.locator(".react-flow__node-text.selected")
    assert text_node.count() == 1
    assert page.locator("[data-video-clip-edit-panel]").count() == 0
    node.click(position={"x": 10, "y": 10}, modifiers=["Meta"], force=True)
    page.wait_for_timeout(160)
    assert page.locator(".react-flow__node.selected").count() == 2
    assert page.locator("[data-video-clip-edit-panel]").count() == 0

    page.keyboard.press("Escape")
    node.click(position={"x": 10, "y": 10}, force=True)
    page.wait_for_timeout(120)
    assert page.locator("[data-video-clip-edit-panel]").count() == 1
    assert page.locator(
        f'.react-flow__node[data-id="{node_id}"]'
    ).count() == 1
    assert_no_overflow(page)
    assert not errors, errors


def run_source_context(page: Page):
    errors = attach_errors(page)
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(350)
    page.keyboard.press("Meta+0")
    page.wait_for_timeout(360)
    assert page.get_by_role("button", name="缩放选项").inner_text() == "28%"
    node, _, panel = add_video_clip(page)
    assert_structure(page, node, panel)
    assert_close(box(node)["width"], 350 * 0.28, 1.2)
    assert_no_overflow(page)
    page.screenshot(path=str(SOURCE_CONTEXT_SCREENSHOT))
    assert not errors, errors


def run_mobile(page: Page):
    errors = attach_errors(page)
    switch_to_empty_canvas(page)
    node, _, panel = add_video_clip(page)
    assert_structure(page, node, panel)
    panel_box = box(panel)
    assert panel_box["x"] < 0
    assert panel_box["x"] + panel_box["width"] > 390
    assert_no_overflow(page)
    page.screenshot(path=str(MOBILE_SCREENSHOT))
    assert not errors, errors


def save_contact_sheet():
    source = Image.open(SOURCE_CONTEXT_SCREENSHOT).convert("RGB")
    detail = Image.open(DETAIL_SCREENSHOT).convert("RGB")
    mobile = Image.open(MOBILE_SCREENSHOT).convert("RGB")
    label_height = 28
    gutter = 12
    width = source.width + detail.width + gutter
    height = max(source.height, detail.height) + mobile.height + label_height * 2 + gutter
    sheet = Image.new("RGB", (width, height), "#141414")
    draw = ImageDraw.Draw(sheet)
    draw.text((8, 8), "source context 28% 929x874", fill="#ededed")
    draw.text(
        (source.width + gutter + 8, 8),
        "isolated detail 100% 929x874",
        fill="#ededed",
    )
    sheet.paste(source, (0, label_height))
    sheet.paste(detail, (source.width + gutter, label_height))
    mobile_y = label_height + max(source.height, detail.height) + gutter
    draw.text((8, mobile_y + 8), "mobile natural clipping 390x844", fill="#ededed")
    sheet.paste(mobile, (0, mobile_y + label_height))
    sheet.save(CONTACT_SHEET)


def main():
    REFERENCE_DIR.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        detail = browser.new_page(
            viewport={"width": 929, "height": 874},
            device_scale_factor=1,
        )
        run_detail(detail)
        detail.close()
        source = browser.new_page(
            viewport={"width": 929, "height": 874},
            device_scale_factor=1,
        )
        run_source_context(source)
        source.close()
        mobile = browser.new_page(
            viewport={"width": 390, "height": 844},
            device_scale_factor=1,
        )
        run_mobile(mobile)
        mobile.close()
        browser.close()
    save_contact_sheet()
    print(
        "Batch25 Playwright verification passed: source-shaped empty node, "
        "single-column mode commands, 660x191 node-anchored editor, mode/reference/"
        "prompt/submit feedback, 50% zoom, drag/pan follow, multi-selection "
        "lifecycle, mobile clipping, overflow, screenshots, console."
    )


if __name__ == "__main__":
    main()
