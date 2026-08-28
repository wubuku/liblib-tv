from pathlib import Path

from PIL import Image, ImageDraw
from playwright.sync_api import Locator, Page, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "docs" / "design-references"
URL = "http://localhost:4317"
MENU_SCREENSHOT = (
    REFERENCE_DIR / "liblib-clone-batch29-frame-menu-929-2026-08-25.png"
)
PLAYER_SCREENSHOT = (
    REFERENCE_DIR
    / "liblib-clone-batch29-player-camera-929-2026-08-25.png"
)
GRAPH_SCREENSHOT = (
    REFERENCE_DIR / "liblib-clone-batch29-frame-graph-929-2026-08-25.png"
)
SELECTED_SCREENSHOT = (
    REFERENCE_DIR
    / "liblib-clone-batch29-frame-output-selected-929-2026-08-25.png"
)
MOBILE_SCREENSHOT = (
    REFERENCE_DIR / "liblib-clone-batch29-frame-mobile-390-2026-08-25.png"
)
CONTACT_SHEET = (
    REFERENCE_DIR
    / "liblib-clone-batch29-frame-contact-sheet-2026-08-25.png"
)


CAPTURE_CONTRACT = {
    "first": {"seconds": 0.0, "name": "首帧", "alt": "视频首帧"},
    "last": {"seconds": 29.95, "name": "尾帧", "alt": "视频尾帧"},
    "current": {"seconds": 12.5, "name": "截图", "alt": "视频截图"},
}


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
    toolbar = page.locator(".react-flow__node-toolbar")
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
    assert page.locator("[data-video-frame-menu-trigger]").count() == 1
    assert page.locator("[data-video-player-camera]").count() == 1
    return source, source_id


def open_top_frame_menu(page: Page):
    trigger = page.locator("[data-video-frame-menu-trigger]")
    assert trigger.inner_text().strip() == "截取首帧"
    assert trigger.locator(".lucide-chevron-down").count() == 1
    trigger.click()

    menu = page.locator('[data-video-toolbar-menu="frame"]')
    menu.wait_for(state="visible")
    items = menu.locator("[data-video-frame-kind]")
    assert items.all_inner_texts() == ["截取首帧", "截取尾帧", "截取当前帧"]
    assert items.nth(0).get_attribute("data-video-frame-kind") == "first"
    assert items.nth(1).get_attribute("data-video-frame-kind") == "last"
    assert items.nth(2).get_attribute("data-video-frame-kind") == "current"

    trigger_box = box(trigger)
    menu_box = box(menu)
    assert_close(center_x(menu_box), center_x(trigger_box))
    assert_close(menu_box["width"], 160)
    assert_close(
        menu_box["y"] - (trigger_box["y"] + trigger_box["height"]),
        7,
    )

    picture_edit_trigger = page.get_by_role(
        "button",
        name="主体消除",
        exact=True,
    )
    download = page.get_by_role("link", name="下载视频封面")
    assert (
        box(picture_edit_trigger)["x"]
        < trigger_box["x"]
        < box(download)["x"]
    )
    return trigger, menu


def capture_root(page: Page, kind: str):
    return page.locator(f'[data-video-frame-capture-kind="{kind}"]')


def capture_shell(page: Page, kind: str):
    return capture_root(page, kind).locator("xpath=..")


def assert_capture_metadata(
    page: Page,
    source_id: str,
    kind: str,
):
    root = capture_root(page, kind)
    assert root.count() == 1
    expected = CAPTURE_CONTRACT[kind]
    assert root.get_attribute("data-video-frame-source-id") == source_id
    assert root.get_attribute("data-video-frame-name") == expected["name"]
    assert root.get_attribute("data-video-frame-alt") == expected["alt"]
    assert_close(
        float(root.get_attribute("data-video-frame-capture-seconds") or "-1"),
        expected["seconds"],
        0.001,
    )
    edge_id = root.get_attribute("data-video-frame-edge-id")
    assert edge_id
    shell = capture_shell(page, kind)
    target_id = shell.get_attribute("data-id")
    assert target_id
    edge = page.locator(
        f'.react-flow__edge[aria-label="Edge from {source_id} to {target_id}"]'
    )
    assert edge.count() == 1
    assert edge.get_attribute("data-id") == edge_id
    assert shell.locator(f'img[alt="{expected["alt"]}"]').count() == 1
    assert expected["name"] in shell.inner_text()
    assert "1280 × 720" in shell.inner_text()
    return shell, target_id


def assert_source_selected(page: Page, source_id: str):
    selected = page.locator(".react-flow__node.selected")
    assert selected.count() == 1
    assert selected.get_attribute("data-id") == source_id
    assert page.locator("[data-video-frame-menu-trigger]").count() == 1
    assert page.locator("[data-video-generation-panel]").count() == 1


def run_primary_flow(page: Page):
    errors = attach_errors(page)
    switch_to_empty_canvas(page)
    source, source_id = add_ready_video(page)

    _, menu = open_top_frame_menu(page)
    assert_processing_toolbar_anchor(page, source)
    page.screenshot(path=str(MENU_SCREENSHOT))
    menu.locator('[data-video-frame-kind="first"]').click()
    page.wait_for_timeout(100)

    first, first_id = assert_capture_metadata(page, source_id, "first")
    assert page.locator("[data-video-frame-feedback]").inner_text() == (
        "首帧已截取，并添加到画布"
    )
    assert_source_selected(page, source_id)
    assert page.locator(".react-flow__node").count() == 2
    assert page.locator(".react-flow__edge").count() == 1

    source_box = box(source)
    first_box = box(first)
    zoom = source_box["width"] / 512
    assert_close(
        first_box["x"] - source_box["x"],
        source_box["width"] + 100 * zoom,
        1.3,
    )
    assert_close(first_box["y"], source_box["y"], 1.3)

    _, menu = open_top_frame_menu(page)
    menu.locator('[data-video-frame-kind="last"]').click()
    page.wait_for_timeout(100)
    last, last_id = assert_capture_metadata(page, source_id, "last")
    assert page.locator("[data-video-frame-feedback]").inner_text() == (
        "尾帧已截取，并添加到画布"
    )
    assert_source_selected(page, source_id)
    last_box = box(last)
    assert_close(last_box["x"], first_box["x"], 1.3)
    assert_close(
        last_box["y"] - first_box["y"],
        (288 + 48) * zoom,
        1.3,
    )

    playhead = page.locator("[data-video-playhead]")
    playhead.fill("12.5")
    assert playhead.input_value() == "12.5"
    camera = page.locator("[data-video-player-camera]")
    assert_close(box(camera)["width"], 28)
    assert_close(box(camera)["height"], 28)
    camera.hover()
    page.wait_for_timeout(100)
    player_menu = page.locator("[data-video-player-frame-menu]")
    assert player_menu.get_attribute("data-state") == "open"
    assert player_menu.locator(
        "[data-video-player-frame-kind]"
    ).all_inner_texts() == ["截取首帧", "截取尾帧", "截取当前帧"]
    menu_box = box(player_menu)
    camera_box = box(camera)
    assert_close(menu_box["x"] + menu_box["width"], camera_box["x"] + camera_box["width"])
    assert_close(camera_box["y"] - (menu_box["y"] + menu_box["height"]), 0)
    page.screenshot(path=str(PLAYER_SCREENSHOT))
    camera.click()
    page.wait_for_timeout(100)

    current, current_id = assert_capture_metadata(page, source_id, "current")
    assert page.locator("[data-video-frame-feedback]").inner_text() == (
        "截图已截取，并添加到画布"
    )
    assert_source_selected(page, source_id)
    current_box = box(current)
    assert_close(current_box["x"], first_box["x"], 1.3)
    assert_close(
        current_box["y"] - last_box["y"],
        (288 + 48) * zoom,
        1.3,
    )
    assert page.locator(".react-flow__node").count() == 4
    assert page.locator(".react-flow__edge").count() == 3

    page.keyboard.press("Meta+z")
    page.wait_for_timeout(150)
    assert page.locator(".react-flow__node").count() == 3
    assert page.locator(".react-flow__edge").count() == 2
    assert page.locator(f'.react-flow__node[data-id="{current_id}"]').count() == 0
    assert page.locator(f'.react-flow__node[data-id="{first_id}"]').count() == 1
    assert page.locator(f'.react-flow__node[data-id="{last_id}"]').count() == 1

    page.keyboard.press("Meta+Shift+z")
    page.wait_for_timeout(150)
    assert page.locator(".react-flow__node").count() == 4
    assert page.locator(".react-flow__edge").count() == 3
    assert page.locator(f'.react-flow__node[data-id="{current_id}"]').count() == 1
    assert_capture_metadata(page, source_id, "current")

    page.keyboard.press("Meta+0")
    page.wait_for_timeout(320)
    page.screenshot(path=str(GRAPH_SCREENSHOT))

    current = page.locator(f'.react-flow__node[data-id="{current_id}"]')
    current.click(position={"x": 20, "y": 20}, force=True)
    page.wait_for_timeout(150)
    assert page.locator("[data-image-toolbar]").count() == 1
    assert page.locator("[data-image-edit-panel]").count() == 1
    assert page.locator("[data-video-frame-menu-trigger]").count() == 0
    page.screenshot(path=str(SELECTED_SCREENSHOT))
    assert_no_overflow(page)
    assert not errors, errors


def run_player_menu_action(page: Page):
    errors = attach_errors(page)
    switch_to_empty_canvas(page)
    _, source_id = add_ready_video(page)
    camera = page.locator("[data-video-player-camera]")
    camera.hover()
    menu = page.locator("[data-video-player-frame-menu]")
    menu.locator('[data-video-player-frame-kind="first"]').click()
    page.wait_for_timeout(100)
    assert_capture_metadata(page, source_id, "first")
    assert_source_selected(page, source_id)
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
    assert page.locator("[data-video-frame-menu-trigger]").count() == 0
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
    trigger = page.locator("[data-video-frame-menu-trigger]")
    trigger.evaluate("(element) => element.click()")
    menu = page.locator('[data-video-toolbar-menu="frame"]')
    menu.wait_for(state="visible")
    assert menu.locator("[data-video-frame-kind]").count() == 3
    assert_no_overflow(page)
    page.screenshot(path=str(MOBILE_SCREENSHOT))
    assert not errors, errors


def save_contact_sheet():
    menu = Image.open(MENU_SCREENSHOT).convert("RGB")
    player = Image.open(PLAYER_SCREENSHOT).convert("RGB")
    graph = Image.open(GRAPH_SCREENSHOT).convert("RGB")
    selected = Image.open(SELECTED_SCREENSHOT).convert("RGB")
    mobile = Image.open(MOBILE_SCREENSHOT).convert("RGB")
    label_height = 28
    gutter = 12
    first_row_width = menu.width + player.width + gutter
    second_row_width = graph.width + selected.width + gutter
    width = max(first_row_width, second_row_width, mobile.width)
    first_row_height = max(menu.height, player.height)
    second_row_height = max(graph.height, selected.height)
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
    draw.text((8, 8), "top source-order frame menu 929x874", fill="#ededed")
    draw.text(
        (menu.width + gutter + 8, 8),
        "player camera hover menu 929x874",
        fill="#ededed",
    )
    sheet.paste(menu, (0, label_height))
    sheet.paste(player, (menu.width + gutter, label_height))

    second_y = label_height + first_row_height + gutter
    draw.text(
        (8, second_y + 8),
        "source -> first/last/current graph 929x874",
        fill="#ededed",
    )
    draw.text(
        (graph.width + gutter + 8, second_y + 8),
        "captured image ordinary overlays 929x874",
        fill="#ededed",
    )
    sheet.paste(graph, (0, second_y + label_height))
    sheet.paste(selected, (graph.width + gutter, second_y + label_height))

    third_y = second_y + label_height + second_row_height + gutter
    draw.text(
        (8, third_y + 8),
        "mobile natural toolbar clipping 390x844",
        fill="#ededed",
    )
    sheet.paste(mobile, (0, third_y + label_height))
    sheet.save(CONTACT_SHEET)


def main():
    REFERENCE_DIR.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)

        primary = browser.new_page(
            viewport={"width": 929, "height": 874},
            device_scale_factor=1,
        )
        run_primary_flow(primary)
        primary.close()

        player = browser.new_page(
            viewport={"width": 929, "height": 874},
            device_scale_factor=1,
        )
        run_player_menu_action(player)
        player.close()

        multi = browser.new_page(
            viewport={"width": 929, "height": 874},
            device_scale_factor=1,
        )
        run_multi_selection(multi)
        multi.close()

        mobile = browser.new_page(
            viewport={"width": 390, "height": 844},
            device_scale_factor=1,
        )
        run_mobile(mobile)
        mobile.close()
        browser.close()

    save_contact_sheet()
    print(
        "Batch29 Playwright verification passed: source-order top frame menu, "
        "trigger-relative geometry, player camera current-frame shortcut and "
        "hover menu, first/last/current time/name/alt metadata, direct source "
        "edges, source-backed poster rendering, 100-unit first slot, repeated "
        "capture avoidance, source selection preservation, atomic undo-redo, "
        "ordinary image overlays, multi-selection hiding, mobile clipping, "
        "screenshots and zero browser errors."
    )


if __name__ == "__main__":
    main()
