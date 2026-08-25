from pathlib import Path

from PIL import Image, ImageDraw
from playwright.sync_api import Locator, Page, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "docs" / "design-references"
URL = "http://localhost:3000"
MENU_SCREENSHOT = (
    REFERENCE_DIR / "liblib-clone-batch28-audio-menu-929-2026-08-25.png"
)
BUSY_SCREENSHOT = (
    REFERENCE_DIR / "liblib-clone-batch28-audio-busy-929-2026-08-25.png"
)
GRAPH_SCREENSHOT = (
    REFERENCE_DIR / "liblib-clone-batch28-audio-graph-929-2026-08-25.png"
)
MOBILE_SCREENSHOT = (
    REFERENCE_DIR / "liblib-clone-batch28-audio-mobile-390-2026-08-25.png"
)
CONTACT_SHEET = (
    REFERENCE_DIR
    / "liblib-clone-batch28-audio-contact-sheet-2026-08-25.png"
)


MODE_SUFFIXES = {
    "av": "音轨",
    "vocals": "人声",
    "background": "背景音",
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


def switch_to_empty_canvas(page: Page):
    page.goto(URL, wait_until="networkidle")
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
    assert page.locator("[data-video-audio-menu-trigger]").count() == 1
    return source, source_id


def open_audio_menu(page: Page):
    trigger = page.locator("[data-video-audio-menu-trigger]")
    assert trigger.inner_text().strip() == "音视频分离"
    assert not trigger.is_disabled()
    assert trigger.locator(".lucide-chevron-down").count() == 1
    trigger.click()

    menu = page.locator('[data-video-toolbar-menu="audio"]')
    menu.wait_for(state="visible")
    modes = menu.locator("[data-video-audio-mode]")
    assert modes.all_inner_texts() == ["音视频分离", "人声提取", "背景音提取"]
    assert menu.get_by_text("音效提取", exact=True).count() == 0
    assert modes.nth(0).get_attribute("data-video-audio-mode") == "av"
    assert modes.nth(1).get_attribute("data-video-audio-mode") == "vocals"
    assert modes.nth(2).get_attribute("data-video-audio-mode") == "background"
    assert modes.nth(0).get_attribute("title") == "分离内嵌音轨为独立音频节点"

    trigger_box = box(trigger)
    menu_box = box(menu)
    assert_close(center_x(menu_box), center_x(trigger_box))
    assert_close(menu_box["width"], 160)
    assert_close(
        menu_box["y"] - (trigger_box["y"] + trigger_box["height"]),
        7,
    )
    return trigger, menu


def start_mode(page: Page, mode: str):
    trigger, menu = open_audio_menu(page)
    menu.locator(f'[data-video-audio-mode="{mode}"]').click()
    assert page.locator('[data-video-toolbar-menu="audio"]').count() == 0
    assert trigger.is_disabled()
    assert trigger.inner_text().strip() == "分离中"
    assert trigger.locator(".lucide-chevron-down").count() == 0
    busy = page.locator("[data-video-audio-busy]")
    assert busy.count() == 1
    assert busy.get_attribute("data-video-audio-busy-mode") == mode
    trigger.evaluate("(element) => element.click()")
    assert page.locator('[data-video-toolbar-menu="audio"]').count() == 0
    return trigger


def output_node(page: Page, output_kind: str):
    return page.locator(
        f'.react-flow__node:has([data-audio-split-output-kind="{output_kind}"])'
    )


def assert_output_contract(
    page: Page,
    source: Locator,
    source_id: str,
    mode: str,
):
    assert page.locator(".react-flow__node").count() == 3
    assert page.locator(".react-flow__edge").count() == 2
    assert page.locator("[data-audio-split-output]").count() == 2

    audio = output_node(page, "audio")
    silent = output_node(page, "silent-video")
    assert audio.count() == 1
    assert silent.count() == 1
    audio_id = audio.get_attribute("data-id")
    silent_id = silent.get_attribute("data-id")
    assert audio_id and silent_id

    audio_metadata = audio.locator('[data-audio-split-output-kind="audio"]')
    silent_metadata = silent.locator(
        '[data-audio-split-output-kind="silent-video"]'
    )
    for metadata, output_kind in (
        (audio_metadata, "audio"),
        (silent_metadata, "silent-video"),
    ):
        assert metadata.get_attribute("data-audio-split-mode") == mode
        assert metadata.get_attribute("data-audio-split-output-kind") == output_kind
        assert metadata.get_attribute("data-audio-split-source-id") == source_id
        assert metadata.get_attribute("data-audio-split-edge-id")

    suffix = MODE_SUFFIXES[mode]
    assert f"视频节点 5-片段重拍_{suffix}" in audio.inner_text()
    assert f"{suffix if mode != 'av' else '独立音轨'}结果" in audio.inner_text()
    assert "来自 视频节点 5-片段重拍" in audio.inner_text()
    assert "00:30" in audio.inner_text()
    assert "视频节点 5-片段重拍_无声" in silent.inner_text()
    assert "无声视频结果" in silent.inner_text()
    assert "音视频分离 · 等待媒体资源" in silent.inner_text()
    assert silent.locator("[data-subtitle-erase-target]").count() == 0

    assert "selected" not in (source.get_attribute("class") or "")
    assert "selected" not in (audio.get_attribute("class") or "")
    assert "selected" in (silent.get_attribute("class") or "")
    assert page.locator(".react-flow__node.selected").count() == 1
    assert page.locator(".react-flow__node-toolbar").count() == 0
    assert page.locator("[data-video-generation-panel]").count() == 0

    source_to_audio = page.locator(
        f'.react-flow__edge[aria-label="Edge from {source_id} to {audio_id}"]'
    )
    source_to_silent = page.locator(
        f'.react-flow__edge[aria-label="Edge from {source_id} to {silent_id}"]'
    )
    audio_to_silent = page.locator(
        f'.react-flow__edge[aria-label="Edge from {audio_id} to {silent_id}"]'
    )
    assert source_to_audio.count() == 1
    assert source_to_silent.count() == 1
    assert audio_to_silent.count() == 0
    assert (
        audio_metadata.get_attribute("data-audio-split-edge-id")
        == source_to_audio.get_attribute("data-id")
    )
    assert (
        silent_metadata.get_attribute("data-audio-split-edge-id")
        == source_to_silent.get_attribute("data-id")
    )

    source_box = box(source)
    audio_box = box(audio)
    silent_box = box(silent)
    zoom = source_box["width"] / 512
    assert_close(audio_box["width"], 350 * zoom, 1.3)
    assert_close(silent_box["width"], 512 * zoom, 1.3)
    assert_close(
        audio_box["x"] - source_box["x"],
        source_box["width"] + 120 * zoom,
        1.3,
    )
    assert_close(
        silent_box["x"] - audio_box["x"],
        audio_box["width"] + 120 * zoom,
        1.3,
    )
    assert_close(audio_box["y"], source_box["y"], 1.3)
    assert_close(silent_box["y"], source_box["y"], 1.3)
    return audio_id, silent_id


def run_primary_flow(page: Page):
    errors = attach_errors(page)
    switch_to_empty_canvas(page)
    source, source_id = add_ready_video(page)
    _, menu = open_audio_menu(page)
    page.screenshot(path=str(MENU_SCREENSHOT))
    menu.locator('[data-video-audio-mode="av"]').click()

    trigger = page.locator("[data-video-audio-menu-trigger]")
    assert trigger.is_disabled()
    assert trigger.inner_text().strip() == "分离中"
    assert page.locator("[data-video-audio-busy]").count() == 1
    page.screenshot(path=str(BUSY_SCREENSHOT))

    page.wait_for_timeout(760)
    audio_id, silent_id = assert_output_contract(
        page,
        source,
        source_id,
        "av",
    )
    page.keyboard.press("Meta+0")
    page.wait_for_timeout(320)
    page.screenshot(path=str(GRAPH_SCREENSHOT))

    page.keyboard.press("Meta+z")
    page.wait_for_timeout(180)
    assert page.locator(".react-flow__node").count() == 1
    assert page.locator(".react-flow__edge").count() == 0
    assert page.locator(f'.react-flow__node[data-id="{audio_id}"]').count() == 0
    assert page.locator(f'.react-flow__node[data-id="{silent_id}"]').count() == 0

    page.keyboard.press("Meta+Shift+z")
    page.wait_for_timeout(180)
    assert page.locator(".react-flow__node").count() == 3
    assert page.locator(".react-flow__edge").count() == 2
    assert page.locator(f'.react-flow__node[data-id="{audio_id}"]').count() == 1
    silent = page.locator(f'.react-flow__node[data-id="{silent_id}"]')
    assert silent.count() == 1
    silent.click(position={"x": 12, "y": 12}, force=True)
    page.wait_for_timeout(100)
    assert_output_contract(page, source, source_id, "av")
    assert_no_overflow(page)
    assert not errors, errors


def run_mode(page: Page, mode: str):
    errors = attach_errors(page)
    switch_to_empty_canvas(page)
    source, source_id = add_ready_video(page)
    start_mode(page, mode)
    page.wait_for_timeout(760)
    assert_output_contract(page, source, source_id, mode)
    assert_no_overflow(page)
    assert not errors, errors


def run_multi_selection(page: Page):
    errors = attach_errors(page)
    switch_to_empty_canvas(page)
    source, _ = add_ready_video(page)
    page.get_by_role("button", name="添加节点").click()
    page.locator('[data-add-node-entry="text"]').click()
    source.click(position={"x": 12, "y": 12}, modifiers=["Meta"], force=True)
    page.wait_for_timeout(160)
    assert page.locator(".react-flow__node.selected").count() == 2
    assert page.locator("[data-video-audio-menu-trigger]").count() == 0
    assert page.locator(".react-flow__node-toolbar").count() == 0
    assert_no_overflow(page)
    assert not errors, errors


def run_mobile(page: Page):
    errors = attach_errors(page)
    switch_to_empty_canvas(page)
    add_ready_video(page)
    _, menu = open_audio_menu(page)
    toolbar_box = box(page.locator(".react-flow__node-toolbar"))
    assert toolbar_box["x"] < 0
    assert toolbar_box["x"] + toolbar_box["width"] > 390
    assert menu.is_visible()
    assert_no_overflow(page)
    page.screenshot(path=str(MOBILE_SCREENSHOT))
    assert not errors, errors


def save_contact_sheet():
    menu = Image.open(MENU_SCREENSHOT).convert("RGB")
    busy = Image.open(BUSY_SCREENSHOT).convert("RGB")
    graph = Image.open(GRAPH_SCREENSHOT).convert("RGB")
    mobile = Image.open(MOBILE_SCREENSHOT).convert("RGB")
    label_height = 28
    gutter = 12
    first_row_width = menu.width + busy.width + gutter
    second_row_width = graph.width + mobile.width + gutter
    width = max(first_row_width, second_row_width)
    first_row_height = max(menu.height, busy.height)
    second_row_height = max(graph.height, mobile.height)
    height = (
        label_height
        + first_row_height
        + gutter
        + label_height
        + second_row_height
    )
    sheet = Image.new("RGB", (width, height), "#141414")
    draw = ImageDraw.Draw(sheet)
    draw.text((8, 8), "three-item trigger-anchored menu 929x874", fill="#ededed")
    draw.text(
        (menu.width + gutter + 8, 8),
        "disabled spinner + separating copy 929x874",
        fill="#ededed",
    )
    sheet.paste(menu, (0, label_height))
    sheet.paste(busy, (menu.width + gutter, label_height))
    second_y = label_height + first_row_height + gutter
    draw.text(
        (8, second_y + 8),
        "source -> audio + silent-video graph 929x874",
        fill="#ededed",
    )
    draw.text(
        (graph.width + gutter + 8, second_y + 8),
        "mobile natural toolbar clipping 390x844",
        fill="#ededed",
    )
    sheet.paste(graph, (0, second_y + label_height))
    sheet.paste(mobile, (graph.width + gutter, second_y + label_height))
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

        for mode in ("vocals", "background"):
            mode_page = browser.new_page(
                viewport={"width": 929, "height": 874},
                device_scale_factor=1,
            )
            run_mode(mode_page, mode)
            mode_page.close()

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
        "Batch28 Playwright verification passed: trigger-anchored current "
        "three-item audio menu, no SFX entry, AV tooltip, busy spinner/copy/"
        "disable guard, AV/vocals/background dual-output transactions, labels, "
        "metadata, direct source edges, geometry, selection, atomic undo-redo, "
        "multi-selection hiding, mobile clipping, screenshots and zero browser "
        "errors."
    )


if __name__ == "__main__":
    main()
