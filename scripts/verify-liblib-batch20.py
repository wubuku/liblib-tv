from pathlib import Path

from PIL import Image, ImageDraw
from playwright.sync_api import Locator, Page, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "docs" / "design-references"
URL = "http://localhost:3000"
DESKTOP_SCREENSHOT = (
    REFERENCE_DIR
    / "liblib-clone-batch20-panorama-desktop-929-2026-08-25.png"
)
MOBILE_SCREENSHOT = (
    REFERENCE_DIR
    / "liblib-clone-batch20-panorama-mobile-390-2026-08-25.png"
)
CONTACT_SHEET = (
    REFERENCE_DIR
    / "liblib-clone-batch20-panorama-contact-sheet-2026-08-25.png"
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


def assert_close(actual: float, expected: float, tolerance: float = 0.7):
    assert abs(actual - expected) <= tolerance, (actual, expected)


def assert_no_overflow(page: Page):
    assert page.evaluate(
        "document.documentElement.scrollWidth <= document.documentElement.clientWidth"
    )
    assert page.evaluate(
        "document.body.scrollWidth <= document.body.clientWidth"
    )


def panorama_node(page: Page):
    return page.locator(".react-flow__node").filter(has_text="720°全景图")


def create_panorama(page: Page, source_id: str):
    source = page.locator(f'.react-flow__node[data-id="{source_id}"]')
    source.click(force=True)
    action = page.get_by_role("button", name="全景", exact=True)
    # At 390px the source-shaped 900.5px toolbar is intentionally clipped.
    action.evaluate("(element) => element.click()")
    page.wait_for_timeout(180)
    return source, panorama_node(page)


def assert_panorama_contract(
    page: Page,
    source: Locator,
    derived: Locator,
    source_id: str,
    expected_reference: str,
):
    assert page.locator(".react-flow__node").count() == 11
    assert page.locator(".react-flow__edge").count() == 12
    assert derived.count() == 1
    assert page.locator(".react-flow__node.selected").count() == 1
    assert "selected" in (derived.get_attribute("class") or "")

    source_box = box(source)
    derived_box = box(derived)
    zoom = derived_box["width"] / 700
    assert_close(derived_box["width"], 700 * zoom)
    assert_close(derived_box["height"], 350 * zoom)
    assert_close(
        derived_box["x"] - source_box["x"],
        source_box["width"] + 120 * zoom,
    )
    assert_close(derived_box["y"] - source_box["y"], -110 * zoom)
    assert "width: 700px" in (derived.get_attribute("style") or "")
    assert "height: 350px" in (derived.get_attribute("style") or "")

    placeholder = derived.locator('[data-image-placeholder="panorama"]')
    assert placeholder.count() == 1
    assert placeholder.locator("img").count() == 0

    derived_id = derived.get_attribute("data-id")
    assert derived_id
    edge = page.locator(
        f'.react-flow__edge[aria-label="Edge from {source_id} to {derived_id}"]'
    )
    assert edge.count() == 1

    panel = page.locator("[data-panorama-edit-panel]")
    panel_box = box(panel)
    assert_close(panel_box["width"], 660)
    assert_close(panel_box["height"], 252)
    assert_close(
        panel_box["x"] + panel_box["width"] / 2,
        derived_box["x"] + derived_box["width"] / 2,
    )
    assert_close(panel_box["y"] - (derived_box["y"] + derived_box["height"]), 16 * zoom)

    reference = page.locator("[data-panorama-reference]")
    assert reference.count() == 1
    assert_close(box(reference)["width"], 47)
    assert_close(box(reference)["height"], 47)
    assert reference.locator("img").get_attribute("src") == expected_reference
    assert page.locator("[data-panorama-add-reference]").inner_text() == "+参考"
    assert page.locator("[data-panorama-prompt]").inner_text() == (
        "点击生成，直接将场景图像转为720全景图，支持文生/参考图"
    )
    assert "720全景" in panel.inner_text()
    assert page.locator("[data-image-editor-model]").inner_text() == "Lib Image"
    assert page.locator("[data-image-editor-settings]").inner_text() == (
        "2:1 · 标准画质 · 2K · 1张"
    )

    return derived_id


def run_desktop(page: Page):
    errors = attach_errors(page)
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(400)
    page.keyboard.press("Meta+0")
    page.wait_for_timeout(420)
    assert page.get_by_role("button", name="缩放选项").inner_text() == "28%"
    assert page.locator("[data-organize-confirmation]").count() == 0
    assert page.locator(".react-flow__node").count() == 10
    assert page.locator(".react-flow__edge").count() == 11

    source, derived = create_panorama(page, "i-YDfWhFlthe")
    derived_id = assert_panorama_contract(
        page,
        source,
        derived,
        "i-YDfWhFlthe",
        "/images/storyboard-2.png",
    )
    page.screenshot(path=str(DESKTOP_SCREENSHOT))

    submit = page.locator("[data-panorama-submit]")
    submit.evaluate("(element) => element.click()")
    assert "已创建本地全景任务" in page.locator("[data-panorama-edit-panel]").inner_text()

    page.keyboard.press("Meta+z")
    page.wait_for_timeout(120)
    assert page.locator(".react-flow__node").count() == 10
    assert page.locator(".react-flow__edge").count() == 11
    assert page.locator(f'.react-flow__node[data-id="{derived_id}"]').count() == 0

    page.keyboard.press("Meta+Shift+z")
    page.wait_for_timeout(120)
    assert page.locator(".react-flow__node").count() == 11
    assert page.locator(".react-flow__edge").count() == 12
    assert page.locator(f'.react-flow__node[data-id="{derived_id}"]').count() == 1
    assert page.locator(
        f'.react-flow__edge[aria-label="Edge from i-YDfWhFlthe to {derived_id}"]'
    ).count() == 1
    assert_no_overflow(page)
    assert not errors, errors


def run_mobile(page: Page):
    errors = attach_errors(page)
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(400)
    assert page.get_by_role("button", name="缩放选项").inner_text() == "28%"

    source, derived = create_panorama(page, "i-1FQ9tErTcC")
    assert_panorama_contract(
        page,
        source,
        derived,
        "i-1FQ9tErTcC",
        "/images/scene-coffee-1.png",
    )
    derived_box = box(derived)
    panel_box = box(page.locator("[data-panorama-edit-panel]"))
    assert derived_box["x"] + derived_box["width"] > 390
    assert panel_box["x"] + panel_box["width"] > 390
    assert_no_overflow(page)
    page.screenshot(path=str(MOBILE_SCREENSHOT))
    assert not errors, errors


def save_contact_sheet():
    desktop = Image.open(DESKTOP_SCREENSHOT).convert("RGB")
    mobile = Image.open(MOBILE_SCREENSHOT).convert("RGB")
    label_height = 28
    gutter = 12
    width = desktop.width + mobile.width + gutter
    height = max(desktop.height, mobile.height) + label_height
    sheet = Image.new("RGB", (width, height), "#141414")
    draw = ImageDraw.Draw(sheet)
    draw.text((8, 8), "desktop 929x874", fill="#ededed")
    draw.text((desktop.width + gutter + 8, 8), "mobile 390x844", fill="#ededed")
    sheet.paste(desktop, (0, label_height))
    sheet.paste(mobile, (desktop.width + gutter, label_height))
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
        "Batch20 Playwright verification passed: panorama node/edge transaction, "
        "700x350 geometry, source offset, empty media, specialized 660x252 panel, "
        "reference/copy/settings, local submit, undo/redo, mobile clipping, "
        "overflow, screenshots, console."
    )


if __name__ == "__main__":
    main()
