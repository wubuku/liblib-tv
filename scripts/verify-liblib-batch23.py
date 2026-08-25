from pathlib import Path

from PIL import Image, ImageDraw
from playwright.sync_api import Locator, Page, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "docs" / "design-references"
URL = "http://localhost:3000"
DEFAULT_SCREENSHOT = (
    REFERENCE_DIR
    / "liblib-clone-batch23-segment-reshoot-default-929-2026-08-25.png"
)
SELECTED_SCREENSHOT = (
    REFERENCE_DIR
    / "liblib-clone-batch23-segment-reshoot-selected-929-2026-08-25.png"
)
MOBILE_SCREENSHOT = (
    REFERENCE_DIR
    / "liblib-clone-batch23-segment-reshoot-mobile-390-2026-08-25.png"
)
CONTACT_SHEET = (
    REFERENCE_DIR
    / "liblib-clone-batch23-segment-reshoot-contact-sheet-2026-08-25.png"
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


def assert_close(actual: float, expected: float, tolerance: float = 0.8):
    assert abs(actual - expected) <= tolerance, (actual, expected)


def assert_no_overflow(page: Page):
    assert page.evaluate(
        "document.documentElement.scrollWidth <= document.documentElement.clientWidth"
    )
    assert page.evaluate(
        "document.body.scrollWidth <= document.body.clientWidth"
    )


def prepare(page: Page):
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(350)
    page.get_by_role("button", name="添加节点").click()
    page.locator('[data-add-node-entry="video"]').click()
    page.wait_for_timeout(240)
    video = page.locator(".react-flow__node-video.selected")
    assert video.count() == 1
    assert "视频节点 5-片段重拍" in video.inner_text()
    page.get_by_role("button", name="片段重拍", exact=True).evaluate(
        "(element) => element.click()"
    )
    panel = page.locator("[data-segment-reshoot-panel]")
    panel.wait_for(state="visible")
    return video, panel


def assert_structure(page: Page, video: Locator, panel: Locator):
    video_box = box(video)
    panel_box = box(panel)
    filmstrip = page.locator("[data-segment-filmstrip]")
    editor = page.locator("[data-segment-editor]")
    filmstrip_box = box(filmstrip)
    editor_box = box(editor)
    zoom = video_box["width"] / 512

    assert panel.get_attribute("data-segment-mode") == "reshoot"
    assert_close(panel_box["width"], 660)
    assert_close(panel_box["height"], 316)
    assert_close(filmstrip_box["width"], 660)
    assert_close(filmstrip_box["height"], 56)
    assert_close(editor_box["width"], 660)
    assert_close(editor_box["height"], 252)
    assert_close(editor_box["y"] - (filmstrip_box["y"] + filmstrip_box["height"]), 8)
    assert_close(
        panel_box["x"] + panel_box["width"] / 2,
        video_box["x"] + video_box["width"] / 2,
    )
    assert_close(panel_box["y"] - (video_box["y"] + video_box["height"]), 16 * zoom)

    assert panel.get_by_text("片段重拍", exact=True).count() == 0
    for command in ["参考", "标记", "角色库"]:
        assert panel.get_by_role("button", name=command, exact=True).count() == 1
    assert page.locator("[data-segment-source]").count() == 1
    assert page.locator("[data-segment-source]").inner_text().replace("\n", "") == (
        "130.1s"
    )
    assert page.locator("[data-segment-option]").count() == 8
    assert page.locator('[data-segment-option="28-30"]').is_disabled()
    assert_close(
        box(page.locator('[data-segment-option="0-4"]'))["width"],
        box(page.locator('[data-segment-option="28-30"]'))["width"] * 2,
        1.2,
    )
    assert page.locator("[data-segment-count]").inner_text() == "0/5 个片段"
    assert page.locator("[data-segment-video-token]").count() == 0
    assert page.locator("[data-segment-range-token]").count() == 0
    assert "留空 = 原样重跑一次" in editor.inner_text()
    assert not page.locator("[data-segment-submit]").is_disabled()


def run_desktop(page: Page):
    errors = attach_errors(page)
    video, panel = prepare(page)
    assert_structure(page, video, panel)
    page.screenshot(path=str(DEFAULT_SCREENSHOT))

    page.locator("[data-segment-submit]").click(force=True)
    assert page.locator("[data-segment-status]").inner_text() == (
        "已创建本地整段重跑任务"
    )

    page.locator('[data-segment-option="0-4"]').evaluate(
        "(element) => element.click()"
    )
    assert page.locator("[data-segment-count]").inner_text() == "1/5 个片段"
    assert page.locator("[data-segment-video-token]").inner_text().strip() == "视频 1"
    assert page.locator("[data-segment-range-token]").count() == 1
    assert page.locator("[data-segment-range-token]").inner_text() == "00:00-00:04"

    for segment_id in ["4-8", "8-12", "12-16", "16-20"]:
        page.locator(f'[data-segment-option="{segment_id}"]').click(force=True)
    assert page.locator("[data-segment-count]").inner_text() == "5/5 个片段"
    assert page.locator("[data-segment-range-token]").count() == 5
    page.locator('[data-segment-option="20-24"]').click(force=True)
    assert page.locator("[data-segment-count]").inner_text() == "5/5 个片段"
    assert page.locator("[data-segment-range-token]").count() == 5

    page.locator("[data-segment-intent]").fill(
        "改为女孩从门缝里面走出来，然后走出镜头"
    )
    page.locator("[data-segment-submit]").click(force=True)
    assert page.locator("[data-segment-status]").inner_text() == (
        "已创建本地片段重拍任务"
    )
    page.screenshot(path=str(SELECTED_SCREENSHOT))

    page.get_by_role("button", name="片段重拍", exact=True).evaluate(
        "(element) => element.click()"
    )
    assert page.locator("[data-segment-reshoot-panel]").count() == 0
    assert page.locator("[data-video-generation-panel]").count() == 1
    assert_no_overflow(page)
    assert not errors, errors


def run_mobile(page: Page):
    errors = attach_errors(page)
    video, panel = prepare(page)
    assert_structure(page, video, panel)
    panel_box = box(panel)
    assert panel_box["x"] < 0
    assert panel_box["x"] + panel_box["width"] > 390
    page.locator('[data-segment-option="0-4"]').evaluate(
        "(element) => element.click()"
    )
    assert page.locator("[data-segment-range-token]").inner_text() == "00:00-00:04"
    assert_no_overflow(page)
    page.screenshot(path=str(MOBILE_SCREENSHOT))
    assert not errors, errors


def save_contact_sheet():
    default = Image.open(DEFAULT_SCREENSHOT).convert("RGB")
    selected = Image.open(SELECTED_SCREENSHOT).convert("RGB")
    mobile = Image.open(MOBILE_SCREENSHOT).convert("RGB")
    label_height = 28
    gutter = 12
    width = default.width + selected.width + gutter
    height = max(default.height, selected.height) + mobile.height + label_height * 2 + gutter
    sheet = Image.new("RGB", (width, height), "#141414")
    draw = ImageDraw.Draw(sheet)
    draw.text((8, 8), "whole rerun 929x874", fill="#ededed")
    draw.text(
        (default.width + gutter + 8, 8),
        "five ranges + intent 929x874",
        fill="#ededed",
    )
    sheet.paste(default, (0, label_height))
    sheet.paste(selected, (default.width + gutter, label_height))
    mobile_y = label_height + max(default.height, selected.height) + gutter
    draw.text((8, mobile_y + 8), "mobile selected 390x844", fill="#ededed")
    sheet.paste(mobile, (0, mobile_y + label_height))
    sheet.save(CONTACT_SHEET)


def main():
    REFERENCE_DIR.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        desktop = browser.new_page(
            viewport={"width": 929, "height": 874},
            device_scale_factor=1,
        )
        run_desktop(desktop)
        desktop.close()
        mobile = browser.new_page(
            viewport={"width": 390, "height": 844},
            device_scale_factor=1,
        )
        run_mobile(mobile)
        mobile.close()
        browser.close()
    save_contact_sheet()
    print(
        "Batch23 Playwright verification passed: ready-video entry, separate "
        "filmstrip/editor geometry, proportional 4s ranges, five-range cap, "
        "video/range tokens, empty-intent whole rerun, intent submission, "
        "generator handoff, mobile clipping, overflow, screenshots, console."
    )


if __name__ == "__main__":
    main()
