from pathlib import Path

from PIL import Image, ImageDraw
from playwright.sync_api import Locator, Page, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "docs" / "design-references"
URL = "http://localhost:4317"
NORMAL_SCREENSHOT = (
    REFERENCE_DIR
    / "liblib-clone-batch21-video-params-normal-929-2026-08-25.png"
)
LONG_SCREENSHOT = (
    REFERENCE_DIR
    / "liblib-clone-batch21-video-params-long-929-2026-08-25.png"
)
MOBILE_SCREENSHOT = (
    REFERENCE_DIR
    / "liblib-clone-batch21-video-params-mobile-390-2026-08-25.png"
)
CONTACT_SHEET = (
    REFERENCE_DIR
    / "liblib-clone-batch21-video-params-contact-sheet-2026-08-25.png"
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
    page.keyboard.press("Meta+0")
    page.wait_for_timeout(420)
    video = page.locator('.react-flow__node[data-id="v-UGQZzZOpbv"]')
    video.click(force=True)
    page.wait_for_timeout(140)
    panel = page.locator("[data-video-generation-panel]")
    assert panel.count() == 1
    return video, panel


def open_params(page: Page):
    trigger = page.locator("[data-video-params-trigger]")
    trigger.click(force=True)
    menu = page.locator("[data-video-params-menu]")
    menu.wait_for(state="visible")
    return trigger, menu


def assert_common_controls(page: Page):
    assert page.locator("[data-video-ratio-option]").count() == 7
    assert page.locator("[data-video-resolution-option]").count() == 3
    assert page.locator("[data-video-audio-option]").count() == 2
    assert page.locator('[data-video-ratio-option="16:9"]').get_attribute(
        "aria-pressed"
    ) == "true"
    assert page.locator('[data-video-resolution-option="720P"]').get_attribute(
        "aria-pressed"
    ) == "true"
    assert page.locator('[data-video-audio-option="开启"]').get_attribute(
        "aria-pressed"
    ) == "true"


def run_desktop(page: Page):
    errors = attach_errors(page)
    _, panel = prepare(page)
    assert page.get_by_role("button", name="缩放选项").inner_text() == "28%"
    panel_box = box(panel)
    assert_close(panel_box["width"], 660)
    assert_close(panel_box["height"], 274)

    trigger, menu = open_params(page)
    normal_box = box(menu)
    assert menu.get_attribute("data-video-params-mode") == "normal"
    assert_close(normal_box["width"], 341)
    assert_close(normal_box["height"], 445)
    assert_close(normal_box["x"] - panel_box["x"], 82)
    assert_close(normal_box["y"] - panel_box["y"], -211.7)
    assert_common_controls(page)
    assert page.locator("[data-video-count-option]").count() == 3
    assert page.locator("[data-video-long-hint]").count() == 0
    duration = page.locator("[data-video-duration]")
    assert duration.get_attribute("min") == "4"
    assert duration.get_attribute("max") == "30"
    assert duration.input_value() == "6"
    assert page.locator("[data-video-duration-value]").inner_text().replace(
        "\n", ""
    ) == "6s"
    page.screenshot(path=str(NORMAL_SCREENSHOT))

    page.locator('[data-video-ratio-option="21:9"]').click()
    page.locator('[data-video-resolution-option="1080P"]').click()
    duration.fill("30")
    page.locator('[data-video-count-option="4个"]').click()
    assert "21:9 · 1080P · 30s · 4个 ·" in trigger.inner_text()
    assert page.locator("[data-video-credits]").inner_text() == "5520"

    page.locator('[data-video-ratio-option="16:9"]').click()
    page.locator('[data-video-resolution-option="720P"]').click()
    page.locator('[data-video-count-option="1个"]').click()
    trigger.click(force=True)
    page.locator("[data-video-mode-trigger]").click(force=True)
    disabled_modes = ["text", "image", "first-last", "video-edit"]
    enabled_modes = ["omnireference", "image-reference", "long-video"]
    for mode in disabled_modes:
        assert page.locator(f'[data-video-mode-option="{mode}"]').is_disabled()
    for mode in enabled_modes:
        assert not page.locator(f'[data-video-mode-option="{mode}"]').is_disabled()
    page.locator('[data-video-mode-option="long-video"]').click(force=True)
    assert "超长视频" in page.locator("[data-video-mode-trigger]").inner_text()

    _, menu = open_params(page)
    long_box = box(menu)
    assert menu.get_attribute("data-video-params-mode") == "long"
    assert_close(long_box["width"], 341)
    assert_close(long_box["height"], 397)
    assert_close(long_box["x"] - panel_box["x"], 90)
    assert_close(long_box["y"] - panel_box["y"], -163.7)
    assert_common_controls(page)
    assert page.locator("[data-video-count-option]").count() == 0
    assert page.locator("[data-video-long-hint]").count() == 1
    duration = page.locator("[data-video-duration]")
    assert duration.get_attribute("min") == "30"
    assert duration.get_attribute("max") == "300"
    assert duration.input_value() == "30"
    page.screenshot(path=str(LONG_SCREENSHOT))

    duration.fill("300")
    assert "300s" in page.locator("[data-video-params-trigger]").inner_text()
    assert page.locator("[data-video-credits]").inner_text() == "14700"
    assert_no_overflow(page)
    assert not errors, errors


def run_mobile(page: Page):
    errors = attach_errors(page)
    _, panel = prepare(page)
    assert page.get_by_role("button", name="缩放选项").inner_text() == "12%"
    _, menu = open_params(page)
    panel_box = box(panel)
    menu_box = box(menu)
    assert_close(menu_box["width"], 341)
    assert_close(menu_box["height"], 445)
    assert_close(menu_box["x"] - panel_box["x"], 82)
    assert menu_box["x"] + menu_box["width"] > 390
    assert_no_overflow(page)
    page.screenshot(path=str(MOBILE_SCREENSHOT))
    assert not errors, errors


def save_contact_sheet():
    normal = Image.open(NORMAL_SCREENSHOT).convert("RGB")
    long = Image.open(LONG_SCREENSHOT).convert("RGB")
    mobile = Image.open(MOBILE_SCREENSHOT).convert("RGB")
    label_height = 28
    gutter = 12
    width = normal.width + long.width + gutter
    height = max(normal.height, long.height) + mobile.height + label_height * 2 + gutter
    sheet = Image.new("RGB", (width, height), "#141414")
    draw = ImageDraw.Draw(sheet)
    draw.text((8, 8), "normal 929x874", fill="#ededed")
    draw.text((normal.width + gutter + 8, 8), "long 929x874", fill="#ededed")
    sheet.paste(normal, (0, label_height))
    sheet.paste(long, (normal.width + gutter, label_height))
    mobile_y = label_height + max(normal.height, long.height) + gutter
    draw.text((8, mobile_y + 8), "mobile 390x844", fill="#ededed")
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
        "Batch21 Playwright verification passed: normal/long parameter dialog "
        "geometry, ratio/resolution/duration/audio/count controls, mode disabled "
        "states, 300s/14700, mobile clipping, overflow, screenshots, console."
    )


if __name__ == "__main__":
    main()
