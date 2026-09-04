# AGED_GATE / HISTORICAL_CONTRACT（Batch 108 归因,2026-09-05）：
# 本 verifier 在基线 86673b6（Batch 96 收口）上同样失败，属既有漂移，
# 非 Batch 97-107 引入。已被 LIBTV_DIRECTOR_CURRENT_VERIFIER_MANIFEST /
# Batch 59、67-96 current gates 取代；处置见
# docs/research/LIBTV_VERIFIER_REPLACEMENT_MAP.md §4.z。
# 运行仍可用于历史快照对照，不能作为当前合同通过依据。
from io import BytesIO
from pathlib import Path
import json
import os

from PIL import Image, ImageChops, ImageDraw, ImageStat
from playwright.sync_api import Locator, Page, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "docs" / "design-references"
BASE_URL = os.environ.get("LIBLIB_BASE_URL", "http://localhost:4317")
STORAGE_KEY = "liblib-tv-director-local-model-library-v1"

EMPTY_SCREENSHOT = (
    REFERENCE_DIR
    / "liblib-clone-batch48-director-local-model-library-empty-1440-2026-08-26.png"
)
POPULATED_SCREENSHOT = (
    REFERENCE_DIR
    / "liblib-clone-batch48-director-local-model-library-populated-1440-2026-08-26.png"
)
SCENE_SCREENSHOT = (
    REFERENCE_DIR
    / "liblib-clone-batch48-director-local-model-library-scene-1440-2026-08-26.png"
)
MOBILE_SCREENSHOT = (
    REFERENCE_DIR
    / "liblib-clone-batch48-director-local-model-library-mobile-390-2026-08-26.png"
)
CONTACT_SHEET = (
    REFERENCE_DIR
    / "liblib-clone-batch48-director-local-model-library-contact-sheet-2026-08-26.png"
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


def open_director(page: Page, clear_storage: bool = False):
    page.goto(f"{BASE_URL}/?batch48=1", wait_until="networkidle")
    if clear_storage:
        page.evaluate(f"localStorage.removeItem({json.dumps(STORAGE_KEY)})")
        page.reload(wait_until="networkidle")
    button = page.locator("[data-open-director]")
    assert button.count() == 1
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
            timeline: state.timeline,
          };
        }"""
    )


def open_my_models(page: Page):
    trigger = page.locator("[data-director-model-library-trigger]")
    trigger.click()
    panel = page.locator("[data-director-model-library-panel]")
    panel.wait_for(state="visible")
    page.locator("[data-director-model-library-tab='my-models']").click()
    return panel


def wait_for_local_cards(page: Page, count: int):
    page.wait_for_function(
        """(expected) =>
          document.querySelectorAll(
            '[data-director-model-library-local-card]'
          ).length === expected""",
        arg=count,
    )


def storage_items(page: Page):
    return page.evaluate(
        f"""() => JSON.parse(
          localStorage.getItem({json.dumps(STORAGE_KEY)}) || "[]"
        )"""
    )


def run_desktop(page: Page):
    errors = attach_errors(page)
    canvas = open_director(page, clear_storage=True)
    assert_nonblank_locator(canvas, "Batch 48 default Director WebGL canvas")
    assert_no_overflow(page)

    initial_state = director_state(page)
    panel = open_my_models(page)
    empty = page.locator("[data-director-model-library-empty]")
    empty.wait_for(state="visible")
    assert empty.get_attribute("aria-label") == "暂无任何模型"
    assert page.locator("[data-director-model-library-local-card]").count() == 0
    assert page.locator("[data-director-model-library-local-input]").count() == 1
    assert page.locator("[data-director-model-library-local-input]").get_attribute(
        "multiple"
    ) is not None
    assert_inside(panel, page.locator("[data-director-viewport]"))
    page.screenshot(path=str(EMPTY_SCREENSHOT))

    page.locator("[data-director-model-library-local-input]").set_input_files(
        [
            {
                "name": "desk-lamp.FBX",
                "mimeType": "application/octet-stream",
                "buffer": b"; fake FBX fixture",
            },
            {
                "name": "coffee-chair.obj",
                "mimeType": "text/plain",
                "buffer": b"o chair\nv 0 0 0",
            },
            {
                "name": "ignored-model.gltf",
                "mimeType": "model/gltf+json",
                "buffer": b"{}",
            },
        ]
    )
    wait_for_local_cards(page, 2)
    assert page.locator("[data-director-model-library-empty]").count() == 0
    local_cards = page.locator("[data-director-model-library-local-card]")
    assert local_cards.count() == 2
    assert page.get_by_text("desk-lamp", exact=True).count() == 1
    assert page.get_by_text("coffee-chair", exact=True).count() == 1
    file_names = page.locator("[data-director-model-library-local-file-name]")
    assert sorted(file_names.all_text_contents()) == [
        "coffee-chair.obj",
        "desk-lamp.FBX",
    ]

    persisted = storage_items(page)
    assert len(persisted) == 2
    assert {item["fileName"] for item in persisted} == {
        "desk-lamp.FBX",
        "coffee-chair.obj",
    }
    assert all(item["categoryId"] == "my-models" for item in persisted)
    assert all(item["dataUrl"].startswith("data:") for item in persisted)
    assert all(
        set(item) == {"id", "categoryId", "name", "fileName", "dataUrl", "visual", "color"}
        for item in persisted
    )
    assert_inside(panel, page.locator("[data-director-viewport]"))
    page.screenshot(path=str(POPULATED_SCREENSHOT))

    asset_id = local_cards.nth(0).get_attribute(
        "data-director-model-library-asset-id"
    )
    assert asset_id is not None
    card = page.locator(
        f"[data-director-model-library-local-card][data-director-model-library-asset-id='{asset_id}']"
    )
    card.click()
    panel.wait_for(state="hidden")
    page.wait_for_timeout(220)
    first_added_state = director_state(page)
    assert len(first_added_state["objects"]) == len(initial_state["objects"]) + 1
    local_objects = [
        item
        for item in first_added_state["objects"]
        if item.get("libraryAssetId") == asset_id
    ]
    assert len(local_objects) == 1
    assert local_objects[0]["librarySource"] == "local"
    assert local_objects[0]["libraryCategoryId"] == "my-models"
    assert local_objects[0]["libraryFileName"] in {
        "desk-lamp.FBX",
        "coffee-chair.obj",
    }
    assert local_objects[0]["primitive"] == "library"
    assert first_added_state["selectedObjectId"] == local_objects[0]["id"]
    assert first_added_state["selectedObjectIds"] == [local_objects[0]["id"]]
    assert first_added_state["selectedGroupId"] is None
    assert page.locator(
        f"[data-director-object-id='{local_objects[0]['id']}']"
    ).get_attribute("data-director-object-selected") == "true"
    assert (
        page.locator("[data-director-inspector]").get_attribute(
            "data-director-inspector-kind"
        )
        == "prop"
    )
    first_canvas = canvas.screenshot()

    panel = open_my_models(page)
    card = page.locator(
        f"[data-director-model-library-local-card][data-director-model-library-asset-id='{asset_id}']"
    )
    card.click()
    panel.wait_for(state="hidden")
    page.wait_for_timeout(220)
    second_added_state = director_state(page)
    linked_instances = [
        item
        for item in second_added_state["objects"]
        if item.get("libraryAssetId") == asset_id
    ]
    assert len(linked_instances) == 2
    assert len(second_added_state["objects"]) == len(initial_state["objects"]) + 2
    second_canvas = canvas.screenshot()
    assert_pixel_difference(
        first_canvas,
        second_canvas,
        "re-adding a local card changes the R3F viewport",
    )
    page.screenshot(path=str(SCENE_SCREENSHOT))

    panel = open_my_models(page)
    delete_button = page.locator(
        f"[data-director-model-library-local-delete][data-director-model-library-local-asset-id='{asset_id}']"
    )
    assert delete_button.count() == 1
    delete_button.click(force=True)
    assert page.locator(
        f"[data-director-model-library-local-card][data-director-model-library-asset-id='{asset_id}']"
    ).count() == 0
    remaining_cards = page.locator("[data-director-model-library-local-card]")
    assert remaining_cards.count() == 1
    deleted_state = director_state(page)
    assert not any(
        item.get("libraryAssetId") == asset_id
        for item in deleted_state["objects"]
    )
    assert deleted_state["selectedObjectId"] not in {
        item["id"] for item in linked_instances
    }
    assert len(storage_items(page)) == 1

    page.keyboard.press("Escape")
    panel.wait_for(state="hidden")
    trigger = page.locator("[data-director-model-library-trigger]")
    trigger.click()
    panel.wait_for(state="visible")
    viewport = box(page.locator("[data-director-viewport]"))
    page.mouse.click(viewport["x"] + 10, viewport["y"] + 10)
    panel.wait_for(state="hidden")
    assert_no_overflow(page)
    assert errors == [], json.dumps(errors, ensure_ascii=False, indent=2)


def run_refresh_and_mobile(page: Page):
    errors = attach_errors(page)
    canvas = open_director(page)
    panel = open_my_models(page)
    wait_for_local_cards(page, 1)
    assert_inside(panel, page.locator("[data-director-viewport]"))
    assert_no_overflow(page)
    assert_nonblank_locator(canvas, "Batch 48 mobile Director WebGL canvas")
    page.screenshot(path=str(MOBILE_SCREENSHOT))

    refreshed_item = page.locator("[data-director-model-library-local-card]")
    assert refreshed_item.count() == 1
    assert page.locator(
        "[data-director-model-library-local-file-name]"
    ).count() == 1
    assert len(storage_items(page)) == 1

    remaining_asset_id = refreshed_item.get_attribute(
        "data-director-model-library-asset-id"
    )
    assert remaining_asset_id is not None
    page.locator(
        f"[data-director-model-library-local-delete][data-director-model-library-local-asset-id='{remaining_asset_id}']"
    ).click(force=True)
    assert page.locator("[data-director-model-library-empty]").count() == 1
    assert storage_items(page) == []
    assert not any(
        item.get("librarySource") == "local"
        for item in director_state(page)["objects"]
    )
    assert errors == [], json.dumps(errors, ensure_ascii=False, indent=2)


def make_contact_sheet():
    items = [
        ("EMPTY", EMPTY_SCREENSHOT),
        ("POPULATED", POPULATED_SCREENSHOT),
        ("SCENE INSTANCES", SCENE_SCREENSHOT),
        ("MOBILE + REFRESH", MOBILE_SCREENSHOT),
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
    import_source = (
        ROOT / "src/components/director/directorLocalModelImport.ts"
    ).read_text()
    viewport_source = (
        ROOT / "src/components/director/DirectorViewport.tsx"
    ).read_text()
    store_source = (ROOT / "src/store/directorStore.ts").read_text()
    for source, labels in [
        (
            import_source,
            [
                "LOCAL_MODEL_EXTENSION_RE",
                "readDirectorLocalModelFiles",
                "readAsDataURL",
                "satisfies DirectorLocalModelLibraryItem",
            ],
        ),
        (
            viewport_source,
            [
                "data-director-model-library-local-input",
                "data-director-model-library-local-card",
                "data-director-model-library-local-delete",
                "handleLocalModelLibraryChange",
                "multiple",
            ],
        ),
        (
            store_source,
            [
                "DIRECTOR_LOCAL_MODEL_LIBRARY_STORAGE_KEY",
                "hydrateLocalModelLibrary",
                "addLocalModelLibraryItem",
                "removeLocalModelLibraryItem",
                "librarySource",
                "libraryFileName",
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
        desktop_context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            device_scale_factor=1,
        )
        desktop = desktop_context.new_page()
        run_desktop(desktop)

        storage_state = desktop_context.storage_state()
        mobile_context = browser.new_context(
            viewport={"width": 390, "height": 844},
            device_scale_factor=1,
            storage_state=storage_state,
        )
        mobile = mobile_context.new_page()
        run_refresh_and_mobile(mobile)

        browser.close()
    make_contact_sheet()
    print("Batch 48 director local-model-library verification passed.")
