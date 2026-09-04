# AGED_GATE / HISTORICAL_CONTRACT（Batch 108 归因,2026-09-05）：
# 本 verifier 在基线 86673b6（Batch 96 收口）上同样失败，属既有漂移，
# 非 Batch 97-107 引入。已被 LIBTV_DIRECTOR_CURRENT_VERIFIER_MANIFEST /
# Batch 59、67-96 current gates 取代；处置见
# docs/research/LIBTV_VERIFIER_REPLACEMENT_MAP.md §4.z。
# 运行仍可用于历史快照对照，不能作为当前合同通过依据。
from base64 import b64decode
from io import BytesIO
from pathlib import Path
import json
import os

from PIL import Image, ImageDraw, ImageStat
from playwright.sync_api import Locator, Page, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "docs" / "design-references"
BASE_URL = os.environ.get("LIBLIB_BASE_URL", "http://localhost:4317")

EMPTY_SCREENSHOT = (
    REFERENCE_DIR / "liblib-clone-batch46-director-capture-empty-1440-2026-08-26.png"
)
GALLERY_SCREENSHOT = (
    REFERENCE_DIR / "liblib-clone-batch46-director-capture-gallery-1440-2026-08-26.png"
)
VIEWER_SCREENSHOT = (
    REFERENCE_DIR / "liblib-clone-batch46-director-capture-viewer-1440-2026-08-26.png"
)
RETURN_SCREENSHOT = (
    REFERENCE_DIR / "liblib-clone-batch46-director-capture-return-1440-2026-08-26.png"
)
MOBILE_SCREENSHOT = (
    REFERENCE_DIR / "liblib-clone-batch46-director-capture-mobile-390-2026-08-26.png"
)
CONTACT_SHEET = (
    REFERENCE_DIR / "liblib-clone-batch46-director-capture-contact-sheet-2026-08-26.png"
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
    page.on(
        "requestfailed",
        lambda request: errors.append(
            f"requestfailed:{request.url}:{request.failure}"
        ),
    )
    return errors


def box(locator: Locator):
    result = locator.bounding_box()
    assert result is not None
    return result


def assert_no_overflow(page: Page):
    assert page.evaluate(
        "document.documentElement.scrollWidth <= document.documentElement.clientWidth"
    )
    assert page.evaluate(
        "document.body.scrollWidth <= document.body.clientWidth"
    )


def assert_nonblank_image(image: Image.Image, label: str):
    rgb = image.convert("RGB")
    stat = ImageStat.Stat(rgb)
    assert max(stat.stddev) > 8, f"{label} has insufficient variance: {stat.stddev}"
    spans = [maximum - minimum for minimum, maximum in stat.extrema]
    assert max(spans) > 80, f"{label} has insufficient range: {stat.extrema}"


def assert_nonblank_locator(locator: Locator, label: str):
    image = Image.open(BytesIO(locator.screenshot()))
    assert_nonblank_image(image, label)
    return image


def open_director(page: Page, force_dom_click: bool = False):
    page.goto(BASE_URL, wait_until="networkidle")
    button = page.locator("[data-open-director]")
    assert button.count() == 1
    if force_dom_click:
        button.evaluate("(element) => element.click()")
    else:
        button.click()
    page.locator("[data-director-workspace]").wait_for(state="visible")
    page.locator('canvas[data-director-webgl-canvas="true"]').wait_for(
        state="visible"
    )
    page.wait_for_timeout(700)


def director_state(page: Page):
    return page.evaluate(
        """() => {
          const state = window.__director_store.getState();
          return {
            captures: state.captures,
            activeCaptureId: state.activeCaptureId,
          };
        }"""
    )


def select_camera_and_open_gallery(page: Page):
    camera_row = page.locator('[data-director-object-kind="camera"]').first
    assert camera_row.count() == 1
    camera_row.click()
    assert page.locator('[data-director-inspector-kind="camera"]').count() == 1
    captures_tab = page.locator('[data-director-camera-tab="captures"]')
    assert captures_tab.count() == 1
    captures_tab.click()
    page.locator("[data-director-capture-gallery]").wait_for(state="visible")


def capture_twice(page: Page):
    capture_button = page.locator("[data-director-capture]")
    assert not capture_button.is_disabled()
    capture_button.click()
    page.wait_for_timeout(500)
    capture_button.click()
    page.wait_for_timeout(500)
    state = director_state(page)
    assert len(state["captures"]) == 2, state
    assert state["activeCaptureId"] == state["captures"][0]["id"]
    return state


def assert_inside(locator: Locator, outer: Locator):
    inner = box(locator)
    parent = box(outer)
    assert inner["x"] >= parent["x"] - 1
    assert inner["y"] >= parent["y"] - 1
    assert inner["x"] + inner["width"] <= parent["x"] + parent["width"] + 1
    assert inner["y"] + inner["height"] <= parent["y"] + parent["height"] + 1


def run_desktop(page: Page):
    errors = attach_errors(page)
    open_director(page)
    canvas = page.locator('canvas[data-director-webgl-canvas="true"]')
    assert_nonblank_locator(canvas, "Batch 46 director WebGL canvas")
    assert_no_overflow(page)

    select_camera_and_open_gallery(page)
    gallery = page.locator("[data-director-capture-gallery]")
    empty = page.locator("[data-director-capture-empty]")
    assert empty.count() == 1
    assert empty.get_attribute("aria-label") == "暂无摄像机截图"
    assert page.locator("[data-director-capture-item]").count() == 0
    assert page.locator("[data-director-capture-clear-all]").is_disabled()
    assert page.locator("[data-director-capture-send-all]").is_disabled()
    assert_inside(gallery, page.locator("[data-director-inspector]"))
    page.screenshot(path=str(EMPTY_SCREENSHOT))

    state = capture_twice(page)
    camera_name = state["captures"][0]["cameraName"]
    assert page.locator("[data-director-capture-empty]").count() == 0
    assert page.locator("[data-director-capture-item]").count() == 2
    assert (
        page.locator(
            '[data-director-capture-group="{}"]'.format(camera_name)
        ).count()
        == 1
    )
    assert page.locator("[data-director-capture-item-selected='true']").count() == 1
    assert (
        page.locator('[data-director-capture-item="{}"]'.format(state["captures"][0]["id"]))
        .get_by_role("button", name="选择截图 {}-截图02".format(camera_name))
        .count()
        == 1
    )
    assert not page.locator("[data-director-capture-clear-all]").is_disabled()
    assert not page.locator("[data-director-capture-send-all]").is_disabled()
    page.screenshot(path=str(GALLERY_SCREENSHOT))

    second = state["captures"][1]
    second_item = page.locator(
        '[data-director-capture-item="{}"]'.format(second["id"])
    )
    second_item.get_by_role(
        "button", name="选择截图 {}-截图01".format(camera_name)
    ).click()
    assert director_state(page)["activeCaptureId"] == second["id"]
    assert second_item.get_attribute("data-director-capture-item-selected") == "true"

    second_item.locator("[data-director-capture-view]").click()
    viewer = page.locator("[data-director-capture-viewer]")
    viewer.wait_for(state="visible")
    viewer_box = box(viewer)
    assert viewer_box["x"] == 0
    assert viewer_box["y"] == 0
    assert viewer_box["width"] == 1440
    assert viewer_box["height"] == 900
    viewer_image = viewer.locator("img")
    assert_nonblank_locator(viewer_image, "Batch 46 screenshot viewer")
    before_transform = viewer_image.get_attribute("style")
    viewer.get_by_role("button", name="放大图片").click()
    assert viewer_image.get_attribute("style") != before_transform
    page.screenshot(path=str(VIEWER_SCREENSHOT))
    page.keyboard.press("Escape")
    assert page.locator("[data-director-capture-viewer]").count() == 0

    second_item.locator("[data-director-capture-send]").click()
    page.wait_for_timeout(150)
    sent_state = director_state(page)
    sent_capture = next(
        capture for capture in sent_state["captures"] if capture["id"] == second["id"]
    )
    assert sent_capture["sentNodeId"]
    assert page.locator("[data-director-capture-node]").count() == 1
    assert second_item.locator("[data-director-capture-send]").is_disabled()
    page.locator("[data-director-capture-send-all]").click()
    page.wait_for_timeout(180)
    assert page.locator("[data-director-capture-node]").count() == 2
    assert page.locator("[data-director-capture-send-all]").is_disabled()

    page.locator("[data-director-capture-clear-all]").click()
    confirmation = page.locator("[data-director-capture-clear-confirm]")
    confirmation.wait_for(state="visible")
    assert confirmation.get_attribute("aria-label") == "确认清空所有截图"
    confirmation.locator("[data-director-capture-clear-cancel]").click()
    assert page.locator("[data-director-capture-clear-confirm]").count() == 0
    page.locator("[data-director-capture-clear-all]").click()
    page.locator("[data-director-capture-clear-confirm-submit]").click()
    page.wait_for_timeout(120)
    assert director_state(page)["captures"] == []
    assert page.locator("[data-director-capture-empty]").count() == 1
    assert page.locator("[data-director-capture-node]").count() == 2
    page.screenshot(path=str(RETURN_SCREENSHOT))

    assert_no_overflow(page)
    assert errors == [], json.dumps(errors, ensure_ascii=False, indent=2)


def run_mobile(page: Page):
    errors = attach_errors(page)
    open_director(page, force_dom_click=True)
    assert_no_overflow(page)
    canvas = page.locator('canvas[data-director-webgl-canvas="true"]')
    assert_nonblank_locator(canvas, "Batch 46 mobile WebGL canvas")

    inspector = page.locator('aside[aria-label="属性"]')
    page.get_by_role("button", name="打开属性面板").click()
    page.wait_for_timeout(220)
    assert inspector.get_attribute("data-director-mobile-panel-state") == "open"
    camera_row = page.locator('[data-director-object-kind="camera"]').first
    assert camera_row.count() == 1
    assert page.get_by_role("button", name="关闭移动端面板").count() == 1
    page.get_by_role("button", name="关闭移动端面板").click(position={"x": 20, "y": 160})
    page.get_by_role("button", name="打开场景对象").click()
    page.wait_for_timeout(180)
    page.locator('[data-director-object-kind="camera"]').first.click()
    page.get_by_role("button", name="关闭移动端面板").click(position={"x": 360, "y": 160})
    page.get_by_role("button", name="打开属性面板").click()
    page.wait_for_timeout(220)
    page.locator('[data-director-camera-tab="captures"]').click()
    assert page.locator("[data-director-capture-empty]").count() == 1
    assert_no_overflow(page)
    gallery = page.locator("[data-director-capture-gallery]")
    assert_inside(gallery, inspector)
    page.screenshot(path=str(MOBILE_SCREENSHOT))
    assert errors == [], json.dumps(errors, ensure_ascii=False, indent=2)


def make_contact_sheet():
    items = [
        ("EMPTY", EMPTY_SCREENSHOT),
        ("GALLERY", GALLERY_SCREENSHOT),
        ("VIEWER", VIEWER_SCREENSHOT),
        ("RETURN + EMPTY", RETURN_SCREENSHOT),
        ("MOBILE", MOBILE_SCREENSHOT),
    ]
    thumb_width = 720
    label_height = 34
    padding = 16
    rendered = []
    for label, path in items:
        image = Image.open(path).convert("RGB")
        target_width = 360 if path == MOBILE_SCREENSHOT else thumb_width
        ratio = target_width / image.width
        thumbnail = image.resize(
            (target_width, max(1, round(image.height * ratio))),
            Image.Resampling.LANCZOS,
        )
        rendered.append((label, thumbnail))
    sheet_width = thumb_width * 2 + padding * 3
    heights = [0, 0]
    for index, (_, image) in enumerate(rendered):
        heights[index % 2] += image.height + label_height + padding
    sheet_height = max(heights) + padding
    sheet = Image.new("RGB", (sheet_width, sheet_height), "#111111")
    draw = ImageDraw.Draw(sheet)
    column_y = [padding, padding]
    for index, (label, image) in enumerate(rendered):
        column = index % 2
        x = padding + column * (thumb_width + padding)
        y = column_y[column]
        draw.text((x, y + 8), label, fill="#d8d8d8")
        y += label_height
        sheet.paste(image, (x + (thumb_width - image.width) // 2, y))
        column_y[column] = y + image.height + padding
    sheet.save(CONTACT_SHEET)


def verify_static_contract():
    inspector_source = (
        ROOT / "src/components/director/DirectorInspector.tsx"
    ).read_text()
    desk_source = (ROOT / "src/components/director/DirectorDesk.tsx").read_text()
    store_source = (ROOT / "src/store/directorStore.ts").read_text()
    canvas_source = (ROOT / "src/store/canvasStore.ts").read_text()
    for source, labels in [
        (
            inspector_source,
            [
                "data-director-camera-tabs",
                "data-director-camera-tab",
                "data-director-capture-gallery",
                "data-director-capture-viewer",
                "data-director-capture-clear-confirm",
                "data-director-capture-send-all",
                "onSendAllCaptures",
            ],
        ),
        (
            desk_source,
            ["sendAllCaptures", "markCaptureSent", "createDirectorCapture"],
        ),
        (
            store_source,
            ["selectCapture", "removeCapture", "clearCaptures", "markCaptureSent"],
        ),
        (canvas_source, ["createDirectorCapture", "captureId"]),
    ]:
        for label in labels:
            assert label in source, label


if __name__ == "__main__":
    REFERENCE_DIR.mkdir(parents=True, exist_ok=True)
    verify_static_contract()
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        desktop = browser.new_page(
            viewport={"width": 1440, "height": 900},
            device_scale_factor=1,
        )
        run_desktop(desktop)
        mobile = browser.new_page(
            viewport={"width": 390, "height": 844},
            device_scale_factor=1,
        )
        run_mobile(mobile)
        browser.close()
    make_contact_sheet()
    print("Batch 46 Director capture gallery verification passed.")
