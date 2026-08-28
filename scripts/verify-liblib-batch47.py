from io import BytesIO
from pathlib import Path
import json
import os

from PIL import Image, ImageChops, ImageDraw, ImageStat
from playwright.sync_api import Locator, Page, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "docs" / "design-references"
BASE_URL = os.environ.get("LIBLIB_BASE_URL", "http://localhost:4317")
LOCAL_MODEL_STORAGE_KEY = "liblib-tv-director-local-model-library-v1"

PANEL_SCREENSHOT = (
    REFERENCE_DIR
    / "liblib-clone-batch47-director-model-library-panel-1440-2026-08-26.png"
)
ADDED_SCREENSHOT = (
    REFERENCE_DIR
    / "liblib-clone-batch47-director-model-library-added-1440-2026-08-26.png"
)
EMPTY_SCREENSHOT = (
    REFERENCE_DIR
    / "liblib-clone-batch47-director-model-library-empty-1440-2026-08-26.png"
)
MOBILE_SCREENSHOT = (
    REFERENCE_DIR
    / "liblib-clone-batch47-director-model-library-mobile-390-2026-08-26.png"
)
CONTACT_SHEET = (
    REFERENCE_DIR
    / "liblib-clone-batch47-director-model-library-contact-sheet-2026-08-26.png"
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


def assert_inside(locator: Locator, outer: Locator):
    inner = box(locator)
    parent = box(outer)
    assert inner["x"] >= parent["x"] - 1
    assert inner["y"] >= parent["y"] - 1
    assert inner["x"] + inner["width"] <= parent["x"] + parent["width"] + 1
    assert inner["y"] + inner["height"] <= parent["y"] + parent["height"] + 1


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


def assert_pixel_difference(left: bytes, right: bytes, label: str):
    left_image = Image.open(BytesIO(left)).convert("RGB")
    right_image = Image.open(BytesIO(right)).convert("RGB")
    difference = ImageStat.Stat(ImageChops.difference(left_image, right_image))
    assert max(difference.mean) > 0.08, f"{label}: {difference.mean}"


def open_director(page: Page, force_dom_click: bool = False):
    page.goto(f"{BASE_URL}/?batch47=1", wait_until="networkidle")
    # Batch 48 adds persistence to this tab; keep the catalog-only fixture
    # deterministic without importing Batch 48 behavior into this verifier.
    page.evaluate(
        f"localStorage.removeItem({json.dumps(LOCAL_MODEL_STORAGE_KEY)})"
    )
    button = page.locator("[data-open-director]")
    assert button.count() == 1
    if force_dom_click:
        button.evaluate("(element) => element.click()")
    else:
        button.click()
    page.locator("[data-director-workspace]").wait_for(state="visible")
    page.locator("[data-director-timeline]").wait_for(state="visible")
    canvas = page.locator('canvas[data-director-webgl-canvas="true"]')
    canvas.wait_for(state="visible")
    page.wait_for_timeout(700)
    return canvas


def director_state(page: Page):
    return page.evaluate(
        """() => {
          const state = window.__director_store.getState();
          return {
            objects: state.objects,
            selectedObjectId: state.selectedObjectId,
            selectedObjectIds: state.selectedObjectIds,
            selectedGroupId: state.selectedGroupId,
          };
        }"""
    )


def run_desktop(page: Page):
    errors = attach_errors(page)
    canvas = open_director(page)
    assert_nonblank_locator(canvas, "Batch 47 default Director WebGL canvas")
    assert_no_overflow(page)
    initial_state = director_state(page)
    before_canvas = canvas.screenshot()

    trigger = page.locator("[data-director-model-library-trigger]")
    assert trigger.count() == 1
    trigger.click()
    panel = page.locator("[data-director-model-library-panel]")
    panel.wait_for(state="visible")
    assert panel.get_attribute("aria-label") == "模型库"
    assert page.locator("[data-director-model-library-tab]").count() == 5
    assert (
        page.locator(
            "[data-director-model-library-tab='convenience']"
        ).get_attribute("aria-selected")
        == "true"
    )
    assert page.locator("[data-director-model-library-card]").count() == 3
    assert_inside(panel, page.locator("[data-director-viewport]"))
    panel_box = box(panel)
    toolbar_box = box(page.locator("[data-director-viewport-toolbar]"))
    assert panel_box["y"] + panel_box["height"] <= toolbar_box["y"] - 6
    page.screenshot(path=str(PANEL_SCREENSHOT))

    category_expectations = {
        "convenience": ["饮料瓶", "咖啡杯", "购物篮"],
        "home": ["餐椅", "台灯", "盆栽"],
        "outdoor": ["帐篷", "保温瓶", "营灯"],
        "tools": ["锤子", "扳手", "工具箱"],
    }
    for category_id, names in category_expectations.items():
        page.locator(
            f"[data-director-model-library-tab='{category_id}']"
        ).click()
        assert (
            page.locator(
                f"[data-director-model-library-tab='{category_id}']"
            ).get_attribute("aria-selected")
            == "true"
        )
        cards = page.locator("[data-director-model-library-card]")
        assert cards.count() == len(names)
        for name in names:
            assert panel.get_by_text(name, exact=True).count() == 1

    page.locator("[data-director-model-library-tab='home']").click()
    asset_id = "proxy-home-chair"
    card = page.locator(
        f"[data-director-model-library-asset-id='{asset_id}']"
    )
    assert card.get_attribute("aria-label") == "添加模型 餐椅"
    card.click()
    panel.wait_for(state="hidden")
    page.wait_for_timeout(220)

    state = director_state(page)
    assert len(state["objects"]) == len(initial_state["objects"]) + 1
    added = next(
        item for item in state["objects"] if item.get("libraryAssetId") == asset_id
    )
    assert added["name"] == "餐椅"
    assert added["kind"] == "prop"
    assert added["primitive"] == "library"
    assert added["libraryCategoryId"] == "home"
    assert added["libraryVisual"] == "chair"
    assert state["selectedObjectId"] == added["id"]
    assert state["selectedObjectIds"] == [added["id"]]
    assert state["selectedGroupId"] is None

    tree_row = page.locator(f"[data-director-object-id='{added['id']}']")
    assert tree_row.count() == 1
    assert tree_row.get_attribute("data-director-object-selected") == "true"
    assert tree_row.get_by_text("餐椅", exact=True).count() == 1
    inspector = page.locator("[data-director-inspector]")
    assert inspector.get_attribute("data-director-inspector-kind") == "prop"
    assert inspector.locator("input").first.input_value() == "餐椅"
    assert inspector.locator(
        '[data-director-transform-field="position"]'
    ).count() == 3
    assert inspector.locator(
        '[data-director-transform-field="rotation"]'
    ).count() == 3
    assert inspector.locator(
        '[data-director-transform-field="scale"]'
    ).count() == 3
    after_canvas = canvas.screenshot()
    assert_pixel_difference(
        before_canvas,
        after_canvas,
        "adding a library prop changes the R3F viewport",
    )
    assert_nonblank_locator(canvas, "Batch 47 Director WebGL canvas after add")
    page.screenshot(path=str(ADDED_SCREENSHOT))

    trigger.click()
    panel.wait_for(state="visible")
    page.locator("[data-director-model-library-tab='my-models']").click()
    empty = page.locator("[data-director-model-library-empty]")
    empty.wait_for(state="visible")
    assert empty.get_attribute("aria-label") == "暂无任何模型"
    assert empty.get_by_text("暂无任何模型", exact=True).count() == 1
    # Batch 48 supersedes the old disabled placeholder with the real
    # clone-owned local-import entry point.
    assert not empty.get_by_role("button", name="本地导入").is_disabled()
    page.screenshot(path=str(EMPTY_SCREENSHOT))

    page.keyboard.press("Escape")
    panel.wait_for(state="hidden")
    assert page.locator("[data-director-workspace]").count() == 1

    trigger.click()
    panel.wait_for(state="visible")
    viewport = box(page.locator("[data-director-viewport]"))
    page.mouse.click(viewport["x"] + 10, viewport["y"] + 10)
    panel.wait_for(state="hidden")
    assert page.locator("[data-director-workspace]").count() == 1
    assert_no_overflow(page)
    assert errors == [], json.dumps(errors, ensure_ascii=False, indent=2)


def run_mobile(page: Page):
    errors = attach_errors(page)
    canvas = open_director(page, force_dom_click=True)
    trigger = page.locator("[data-director-model-library-trigger]")
    trigger.click()
    panel = page.locator("[data-director-model-library-panel]")
    panel.wait_for(state="visible")
    assert_inside(panel, page.locator("[data-director-viewport]"))
    assert page.locator("[data-director-model-library-tab]").count() == 5
    assert page.locator("[data-director-model-library-card]").count() == 3
    assert_no_overflow(page)
    assert_nonblank_locator(canvas, "Batch 47 mobile Director WebGL canvas")
    page.screenshot(path=str(MOBILE_SCREENSHOT))
    page.locator("[data-director-model-library-tab='my-models']").click()
    assert page.locator("[data-director-model-library-empty]").count() == 1
    assert errors == [], json.dumps(errors, ensure_ascii=False, indent=2)


def make_contact_sheet():
    items = [
        ("MODEL LIBRARY", PANEL_SCREENSHOT),
        ("ADDED PROP", ADDED_SCREENSHOT),
        ("MY MODELS EMPTY", EMPTY_SCREENSHOT),
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
    catalog_source = (
        ROOT / "src/components/director/directorModelLibrary.ts"
    ).read_text()
    viewport_source = (
        ROOT / "src/components/director/DirectorViewport.tsx"
    ).read_text()
    camera_follow_source = (
        ROOT / "src/components/director/directorCameraFollow.ts"
    ).read_text()
    store_source = (ROOT / "src/store/directorStore.ts").read_text()
    for source, labels in [
        (
            catalog_source,
            [
                "DIRECTOR_MODEL_LIBRARY_CATEGORIES",
                "DIRECTOR_MODEL_LIBRARY_ITEMS",
                "getDirectorModelLibraryItems",
            ],
        ),
        (
            viewport_source,
            [
                "LibraryPropPrimitive",
                "data-director-model-library-trigger",
                "data-director-model-library-panel",
                "data-director-model-library-card",
                "data-director-model-library-empty",
            ],
        ),
        (
            store_source,
            [
                'DirectorPrimitive =',
                '"library"',
                "addModelLibraryObject",
                "libraryAssetId",
                "libraryCategoryId",
                "libraryVisual",
            ],
        ),
        (
            camera_follow_source,
            [
                '"library"',
                'object.primitive === "library"',
            ],
        ),
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
    print("Batch 47 director model-library verification passed.")
