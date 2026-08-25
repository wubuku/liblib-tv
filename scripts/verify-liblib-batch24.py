from pathlib import Path

from PIL import Image, ImageDraw
from playwright.sync_api import Locator, Page, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "docs" / "design-references"
URL = "http://localhost:3000"
READY_SCREENSHOT = (
    REFERENCE_DIR
    / "liblib-clone-batch24-shot-breakdown-ready-929-2026-08-25.png"
)
OVERVIEW_SCREENSHOT = (
    REFERENCE_DIR
    / "liblib-clone-batch24-shot-breakdown-results-overview-929-2026-08-25.png"
)
DETAIL_SCREENSHOT = (
    REFERENCE_DIR
    / "liblib-clone-batch24-shot-breakdown-results-detail-929-2026-08-25.png"
)
MOBILE_SCREENSHOT = (
    REFERENCE_DIR
    / "liblib-clone-batch24-shot-breakdown-mobile-390-2026-08-25.png"
)
CONTACT_SHEET = (
    REFERENCE_DIR
    / "liblib-clone-batch24-shot-breakdown-contact-sheet-2026-08-25.png"
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


def assert_close(actual: float, expected: float, tolerance: float = 1.2):
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
    page.wait_for_timeout(350)
    page.locator("[data-canvas-trigger]").click()
    page.locator('[data-canvas-row="canvas-1"] button').first.click()
    page.wait_for_timeout(180)
    assert page.locator(".react-flow__node").count() == 0
    assert page.locator(".react-flow__edge").count() == 0


def create_ready_breakdown(page: Page):
    page.get_by_role("button", name="添加节点").click()
    page.locator('[data-add-node-entry="shot-breakdown"]').click()
    source = page.locator(".react-flow__node-shot-breakdown")
    assert source.count() == 1
    source_id = source.get_attribute("data-id")
    assert source_id

    media = page.locator("[data-shot-breakdown-media]")
    media.click()
    page.get_by_role("button", name="从画布选择", exact=True).click()
    assert page.locator("[data-shot-breakdown-source-meta]").inner_text() == (
        "00:30 · 1280×720"
    )
    assert media.locator("img").count() == 1
    assert "咖啡馆漫步" not in media.inner_text()
    assert page.locator("[data-shot-breakdown-dimension]").count() == 3
    for dimension in ["storyboard", "motion", "music"]:
        control = page.locator(
            f'[data-shot-breakdown-dimension="{dimension}"]'
        )
        assert control.get_attribute("aria-pressed") == "true"
    assert not page.locator("[data-shot-breakdown-start]").is_disabled()
    return source, source_id


def wait_for_results(page: Page, expected_count: int = 5):
    start = page.locator("[data-shot-breakdown-start]")
    start.click()
    assert start.inner_text().strip() == "拉片中"
    page.locator("[data-shot-breakdown-result]").first.wait_for(
        state="attached",
        timeout=5000,
    )
    assert page.locator("[data-shot-breakdown-result]").count() == expected_count
    assert start.inner_text().strip() == "拉片完成"
    assert start.is_disabled()


def assert_default_results(page: Page, source_id: str):
    results = page.locator("[data-shot-breakdown-result]")
    assert results.count() == 5
    assert page.locator(
        '[data-shot-breakdown-category="storyboard"]'
    ).count() == 3
    assert page.locator('[data-shot-breakdown-category="motion"]').count() == 1
    assert page.locator('[data-shot-breakdown-category="music"]').count() == 1
    assert page.locator("[data-shot-breakdown-item]").count() == 12

    for item_id in [
        "S01",
        "S02",
        "S03",
        "S04",
        "S05",
        "S06",
        "S07",
        "S08",
        "M01",
        "M02",
        "M03",
        "BGM",
    ]:
        assert page.locator(
            f'[data-shot-breakdown-item="{item_id}"]'
        ).count() == 1

    assert page.locator("[data-shot-breakdown-waveform]").count() == 1
    assert page.get_by_role("button", name="播放 BGM").count() == 1
    assert page.get_by_text("加入参考", exact=True).count() == 0
    assert page.get_by_text("分析完成 · 本地示例结果", exact=True).count() == 0
    assert page.locator("[data-shot-breakdown-results-panel]").count() == 0

    source = page.locator(f'.react-flow__node[data-id="{source_id}"]')
    result_shells = page.locator(".react-flow__node-shot-breakdown-result")
    assert result_shells.count() == 5
    result_ids = []
    for index in range(result_shells.count()):
        result_id = result_shells.nth(index).get_attribute("data-id")
        assert result_id
        result_ids.append(result_id)
        assert page.locator(
            f'.react-flow__edge[aria-label="Edge from {source_id} to {result_id}"]'
        ).count() == 1
    assert len(set(result_ids)) == 5
    assert page.locator(".react-flow__node").count() == 6
    assert page.locator(".react-flow__edge").count() == 5

    first = page.locator(
        '[data-shot-breakdown-result="storyboard-01"]'
    ).locator("xpath=..")
    second = page.locator(
        '[data-shot-breakdown-result="storyboard-02"]'
    ).locator("xpath=..")
    third = page.locator(
        '[data-shot-breakdown-result="storyboard-03"]'
    ).locator("xpath=..")
    motion = page.locator(
        '[data-shot-breakdown-result="motion"]'
    ).locator("xpath=..")
    music = page.locator(
        '[data-shot-breakdown-result="music"]'
    ).locator("xpath=..")
    assert "width: 1040px" in (first.get_attribute("style") or "")
    assert "height: 680px" in (first.get_attribute("style") or "")
    assert "height: 350px" in (third.get_attribute("style") or "")
    assert "width: 324px" in (music.get_attribute("style") or "")
    assert "height: 220px" in (music.get_attribute("style") or "")

    first_box = box(first)
    second_box = box(second)
    third_box = box(third)
    motion_box = box(motion)
    music_box = box(music)
    zoom = first_box["width"] / 1040
    assert_close(second_box["y"] - (first_box["y"] + first_box["height"]), 48 * zoom)
    assert_close(third_box["y"] - (second_box["y"] + second_box["height"]), 48 * zoom)
    assert_close(motion_box["y"] - (third_box["y"] + third_box["height"]), 48 * zoom)
    assert_close(music_box["y"] - (motion_box["y"] + motion_box["height"]), 48 * zoom)
    assert_close(
        first_box["x"],
        box(source)["x"] + box(source)["width"] + 120 * zoom,
    )

def zoom_to(page: Page, label: str):
    page.get_by_role("button", name="缩放选项").click()
    page.get_by_role("button", name=label, exact=True).click()
    page.wait_for_timeout(240)
    page.keyboard.press("Escape")
    assert not page.locator('[data-liblib-overlay="zoom-menu"]').is_visible()


def focus_result(page: Page, result: Locator):
    zoom_to(page, "缩放至50%")
    for _ in range(4):
        result_box = box(result)
        delta_x = result_box["x"] - 50
        delta_y = result_box["y"] - 110
        if abs(delta_x) < 2 and abs(delta_y) < 2:
            break
        page.mouse.move(450, 420)
        page.mouse.wheel(delta_x, delta_y)
        page.wait_for_timeout(80)


def run_desktop(page: Page):
    errors = attach_errors(page)
    switch_to_empty_canvas(page)
    source, source_id = create_ready_breakdown(page)
    assert_close(box(source)["width"], 320)
    assert_close(box(source)["height"], 389)
    page.screenshot(path=str(READY_SCREENSHOT))

    wait_for_results(page)
    assert_default_results(page, source_id)

    page.keyboard.press("Escape")
    assert page.locator(".react-flow__node.selected").count() == 0
    assert page.locator("[data-shot-breakdown-result]").count() == 5

    page.keyboard.press("Meta+0")
    page.wait_for_timeout(360)
    assert_no_overflow(page)
    page.screenshot(path=str(OVERVIEW_SCREENSHOT))

    first_result = page.locator(
        '[data-shot-breakdown-result="storyboard-01"]'
    ).locator("xpath=..")
    focus_result(page, first_result)
    assert box(first_result)["width"] > 510
    page.screenshot(path=str(DETAIL_SCREENSHOT))

    action = page.locator('[data-shot-breakdown-item-action="S01"]')
    action.evaluate("(element) => element.click()")
    assert action.get_attribute("aria-pressed") == "true"

    page.keyboard.press("Meta+z")
    page.wait_for_timeout(150)
    assert page.locator("[data-shot-breakdown-result]").count() == 0
    assert page.locator(".react-flow__node").count() == 1
    assert page.locator(".react-flow__edge").count() == 0
    assert page.locator("[data-shot-breakdown-start]").inner_text().strip() == (
        "开始拉片"
    )

    page.keyboard.press("Meta+Shift+z")
    page.wait_for_timeout(150)
    assert page.locator("[data-shot-breakdown-result]").count() == 5
    assert page.locator(".react-flow__node").count() == 6
    assert page.locator(".react-flow__edge").count() == 5
    assert_no_overflow(page)
    assert not errors, errors


def run_dimension_filter(page: Page):
    errors = attach_errors(page)
    switch_to_empty_canvas(page)
    create_ready_breakdown(page)
    page.locator('[data-shot-breakdown-dimension="music"]').click()
    assert page.locator(
        '[data-shot-breakdown-dimension="music"]'
    ).get_attribute("aria-pressed") == "false"
    wait_for_results(page, expected_count=4)
    assert page.locator("[data-shot-breakdown-result]").count() == 4
    assert page.locator('[data-shot-breakdown-category="music"]').count() == 0
    assert page.locator("[data-shot-breakdown-item]").count() == 11
    assert page.locator(".react-flow__node").count() == 5
    assert page.locator(".react-flow__edge").count() == 4
    assert not errors, errors


def run_mobile(page: Page):
    errors = attach_errors(page)
    switch_to_empty_canvas(page)
    create_ready_breakdown(page)
    wait_for_results(page)
    assert_default_results(
        page,
        page.locator(".react-flow__node-shot-breakdown").get_attribute("data-id"),
    )
    page.keyboard.press("Meta+0")
    page.wait_for_timeout(360)
    assert_no_overflow(page)
    page.screenshot(path=str(MOBILE_SCREENSHOT))
    assert not errors, errors


def save_contact_sheet():
    ready = Image.open(READY_SCREENSHOT).convert("RGB")
    overview = Image.open(OVERVIEW_SCREENSHOT).convert("RGB")
    detail = Image.open(DETAIL_SCREENSHOT).convert("RGB")
    mobile = Image.open(MOBILE_SCREENSHOT).convert("RGB")
    label_height = 28
    gutter = 12
    first_row_width = ready.width + overview.width + gutter
    second_row_width = detail.width + mobile.width + gutter
    width = max(first_row_width, second_row_width)
    height = (
        max(ready.height, overview.height)
        + max(detail.height, mobile.height)
        + label_height * 2
        + gutter
    )
    sheet = Image.new("RGB", (width, height), "#141414")
    draw = ImageDraw.Draw(sheet)
    draw.text((8, 8), "ready input 929x874", fill="#ededed")
    draw.text(
        (ready.width + gutter + 8, 8),
        "persistent results overview 929x874",
        fill="#ededed",
    )
    sheet.paste(ready, (0, label_height))
    sheet.paste(overview, (ready.width + gutter, label_height))
    second_y = label_height + max(ready.height, overview.height) + gutter
    draw.text((8, second_y + 8), "storyboard detail 929x874", fill="#ededed")
    draw.text(
        (detail.width + gutter + 8, second_y + 8),
        "mobile fit 390x844",
        fill="#ededed",
    )
    sheet.paste(detail, (0, second_y + label_height))
    sheet.paste(mobile, (detail.width + gutter, second_y + label_height))
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
        dimension = browser.new_page(
            viewport={"width": 929, "height": 874},
            device_scale_factor=1,
        )
        run_dimension_filter(dimension)
        dimension.close()
        mobile = browser.new_page(
            viewport={"width": 390, "height": 844},
            device_scale_factor=1,
        )
        run_mobile(mobile)
        mobile.close()
        browser.close()
    save_contact_sheet()
    print(
        "Batch24 Playwright verification passed: source-shaped ready metadata, "
        "five persistent result nodes, S01-S08/M01-M03/BGM contents, derived "
        "edges, local reuse feedback, deselection persistence, dimension "
        "filtering, single undo/redo transaction, responsive canvas bounds, "
        "screenshots, console."
    )


if __name__ == "__main__":
    main()
