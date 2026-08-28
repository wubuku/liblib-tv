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

TRANSFORM_SCREENSHOT = (
    REFERENCE_DIR
    / "liblib-clone-batch39-director-path-transform-1440-2026-08-26.png"
)
WORLD_ANCHOR_SCREENSHOT = (
    REFERENCE_DIR
    / "liblib-clone-batch39-director-world-anchor-1440-2026-08-26.png"
)
RESET_OFFSET_SCREENSHOT = (
    REFERENCE_DIR
    / "liblib-clone-batch39-director-reset-offset-1440-2026-08-26.png"
)
FULL_RESET_SCREENSHOT = (
    REFERENCE_DIR
    / "liblib-clone-batch39-director-full-reset-1440-2026-08-26.png"
)
MOBILE_SCREENSHOT = (
    REFERENCE_DIR
    / "liblib-clone-batch39-director-path-transform-mobile-390-2026-08-26.png"
)
CONTACT_SHEET = (
    REFERENCE_DIR
    / "liblib-clone-batch39-director-path-transform-contact-sheet-2026-08-26.png"
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


def assert_nonblank_locator(locator: Locator, label: str):
    image = Image.open(BytesIO(locator.screenshot())).convert("RGB")
    stat = ImageStat.Stat(image)
    assert max(stat.stddev) > 8, f"{label} has insufficient variance: {stat.stddev}"
    spans = [maximum - minimum for minimum, maximum in stat.extrema]
    assert max(spans) > 80, f"{label} has insufficient range: {stat.extrema}"


def close_tuple(left, right, tolerance=0.001):
    return all(
        abs(left[index] - right[index]) <= tolerance
        for index in range(3)
    )


def open_director(page: Page, force_dom_click: bool = False):
    page.goto(f"{BASE_URL}/?batch39=1", wait_until="networkidle")
    button = page.locator("[data-open-director]")
    assert button.count() == 1
    if force_dom_click:
        button.evaluate("(element) => element.click()")
    else:
        button.click()
    page.locator("[data-director-workspace]").wait_for(state="visible")
    page.locator("[data-director-timeline]").wait_for(state="visible")
    page.locator('canvas[data-director-webgl-canvas="true"]').wait_for(
        state="visible"
    )
    page.wait_for_timeout(650)


def director_state(page: Page):
    return page.evaluate(
        """() => {
          const state = window.__director_store.getState();
          return {
            timeline: state.timeline,
            objects: state.objects,
            captures: state.captures,
            activeCaptureId: state.activeCaptureId,
          };
        }"""
    )


def selected_path(state):
    path_id = state["timeline"]["selectedMotionPathId"]
    return next(
        path
        for path in state["timeline"]["motionPaths"]
        if path["id"] == path_id
    )


def selected_anchor(state):
    path = selected_path(state)
    anchor_id = state["timeline"]["selectedMotionPathAnchorId"]
    return next(anchor for anchor in path["anchors"] if anchor["id"] == anchor_id)


def object_by_id(state, object_id: str):
    return next(item for item in state["objects"] if item["id"] == object_id)


def create_rectangle_path(page: Page):
    page.locator("[data-director-create-motion-path]").click()
    page.locator('[data-director-motion-path-preset="rectangle"]').click()
    page.wait_for_timeout(100)


def fill_path_transform(
    page: Page,
    position=(1.6, 0.4, -0.35),
    rotation=(0, 48, 0),
    scale=(1.45, 1, 0.7),
):
    for field, values in [
        ("position", position),
        ("rotation", rotation),
        ("scale", scale),
    ]:
        for axis, value in zip(("x", "y", "z"), values):
            page.locator(
                f'[data-director-path-transform-field="{field}"] '
                f'[data-director-path-transform-axis="{axis}"]'
            ).fill(str(value))


def semantic_world_anchor(page: Page, anchor_id: str):
    value = page.locator(
        f'[data-director-motion-path-anchor-id="{anchor_id}"]'
    ).get_attribute("data-director-motion-path-world-anchor")
    assert value
    return [float(item) for item in value.split(",")]


def run_desktop(page: Page):
    errors = attach_errors(page)
    open_director(page)
    canvas = page.locator('canvas[data-director-webgl-canvas="true"]')
    assert_nonblank_locator(canvas, "Batch 39 director viewport")
    create_rectangle_path(page)

    state = director_state(page)
    path = selected_path(state)
    initial_path = json.loads(json.dumps(path))
    assert len(path["anchors"]) == 4
    assert path["anchors"] == path["initialAnchors"]
    assert path["transform"] == {
        "position": [0, 0, 0],
        "rotation": [0, 0, 0],
        "scale": [1, 1, 1],
    }
    assert all(value == value for value in path["pivot"])
    assert page.locator("[data-director-motion-path-pivot]").count() == 1
    assert page.locator(
        "[data-director-motion-path-world-anchor]"
    ).count() == 4

    fill_path_transform(page)
    state = director_state(page)
    path = selected_path(state)
    assert path["anchors"] == initial_path["anchors"]
    assert path["points"] != initial_path["points"]
    assert path["transform"] == {
        "position": [1.6, 0.4, -0.35],
        "rotation": [0, 48, 0],
        "scale": [1.45, 1, 0.7],
    }
    character = object_by_id(state, "director-character-lead")
    assert close_tuple(character["transform"]["position"], path["points"][0])
    assert page.locator(
        '[data-director-path-transform-field="position"]'
    ).count() == 1
    assert page.locator("[data-director-path-reset-offset]").is_visible()
    assert page.locator("[data-director-path-reset]").is_visible()
    assert_no_overflow(page)
    page.screenshot(path=str(TRANSFORM_SCREENSHOT))

    anchor_id = path["anchors"][0]["id"]
    world_before = semantic_world_anchor(page, anchor_id)
    world_target = [
        world_before[0] + 0.45,
        world_before[1] + 0.22,
        world_before[2] - 0.3,
    ]
    page.evaluate(
        """([pathId, anchorId, target]) =>
          window.__director_store.getState()
            .updateMotionPathAnchorWorldPosition(pathId, anchorId, target)""",
        [path["id"], anchor_id, world_target],
    )
    page.wait_for_timeout(80)
    assert close_tuple(semantic_world_anchor(page, anchor_id), world_target)
    state = director_state(page)
    path = selected_path(state)
    assert path["anchors"][0] != initial_path["anchors"][0]

    page.locator(
        f'[data-director-path-anchor-option="{anchor_id}"]'
    ).click()
    page.locator(
        '[data-director-path-anchor-type-option="symmetric"]'
    ).click()
    world_anchor = semantic_world_anchor(page, anchor_id)
    world_handle_target = [
        world_anchor[0] + 0.82,
        world_anchor[1] + 0.24,
        world_anchor[2] - 0.52,
    ]
    page.evaluate(
        """([pathId, anchorId, target]) =>
          window.__director_store.getState()
            .updateMotionPathAnchorWorldHandle(pathId, anchorId, "out", target)""",
        [path["id"], anchor_id, world_handle_target],
    )
    state = director_state(page)
    path = selected_path(state)
    anchor = selected_anchor(state)
    assert anchor["type"] == "symmetric"
    assert all(
        abs(anchor["handleIn"][index] + anchor["handleOut"][index]) < 0.000001
        for index in range(3)
    )
    assert len(path["points"]) > 4
    edited_anchor = json.loads(json.dumps(anchor))
    page.screenshot(path=str(WORLD_ANCHOR_SCREENSHOT))

    page.locator("[data-director-path-reset-offset]").click()
    state = director_state(page)
    path = selected_path(state)
    assert path["transform"] == {
        "position": [0, 0, 0],
        "rotation": [0, 0, 0],
        "scale": [1, 1, 1],
    }
    assert selected_anchor(state) == edited_anchor
    assert close_tuple(path["points"][0], edited_anchor["position"])
    page.screenshot(path=str(RESET_OFFSET_SCREENSHOT))

    page.locator(
        '[data-director-path-transform-field="scale"] '
        '[data-director-path-transform-axis="x"]'
    ).fill("-3")
    assert selected_path(director_state(page))["transform"]["scale"][0] == 0.05
    page.locator(
        '[data-director-path-transform-field="scale"] '
        '[data-director-path-transform-axis="y"]'
    ).fill("24")
    assert selected_path(director_state(page))["transform"]["scale"][1] == 20

    page.locator("[data-director-insert-path-anchor]").click()
    assert len(selected_path(director_state(page))["anchors"]) == 5
    page.locator("[data-director-path-reset]").click()
    state = director_state(page)
    path = selected_path(state)
    assert path["anchors"] == initial_path["anchors"]
    assert path["pivot"] == initial_path["pivot"]
    assert len(path["anchors"]) == 4
    assert path["transform"] == {
        "position": [0, 0, 0],
        "rotation": [0, 0, 0],
        "scale": [1, 1, 1],
    }
    assert state["timeline"]["selectedMotionPathAnchorId"] == (
        path["anchors"][0]["id"]
    )
    page.screenshot(path=str(FULL_RESET_SCREENSHOT))

    fill_path_transform(
        page,
        position=(0.8, 0.2, 0.5),
        rotation=(0, 25, 0),
        scale=(1.2, 1, 0.85),
    )
    page.evaluate("() => window.__director_store.getState().setTimelineTime(0)")
    start_position = object_by_id(
        director_state(page), "director-character-lead"
    )["transform"]["position"]
    page.locator("[data-director-playback]").click()
    page.wait_for_timeout(320)
    state = director_state(page)
    playing_position = object_by_id(
        state, "director-character-lead"
    )["transform"]["position"]
    assert state["timeline"]["currentTime"] > 0.2
    assert playing_position != start_position
    page.get_by_role("button", name="暂停").click()

    page.locator("[data-director-capture]").click()
    page.locator("[data-director-capture-preview]").wait_for(state="visible")
    state = director_state(page)
    capture = next(
        item
        for item in state["captures"]
        if item["id"] == state["activeCaptureId"]
    )
    raw = Image.open(
        BytesIO(b64decode(capture["dataUrl"].split(",", 1)[1]))
    ).convert("RGB")
    cyan_pixels = sum(
        red < 80 and green > 170 and blue > 180
        for red, green, blue in raw.getdata()
    )
    orange_pixels = sum(
        red > 190 and 100 < green < 220 and blue < 140
        for red, green, blue in raw.getdata()
    )
    assert cyan_pixels < 20, f"capture retained cyan helpers: {cyan_pixels}"
    assert orange_pixels < 20, f"capture retained orange helpers: {orange_pixels}"
    assert_no_overflow(page)
    assert errors == [], json.dumps(errors, ensure_ascii=False, indent=2)


def run_mobile(page: Page):
    errors = attach_errors(page)
    open_director(page, force_dom_click=True)
    assert box(page.locator("[data-director-timeline]"))["height"] == 176
    create_rectangle_path(page)
    page.get_by_role("button", name="打开属性面板").click()
    page.wait_for_timeout(260)

    inspector_panel = page.locator(
        '[aria-label="属性"][data-director-mobile-panel-state="open"]'
    )
    assert inspector_panel.is_visible()
    transform_section = page.locator(
        '[data-director-path-transform-field="position"]'
    )
    transform_section.evaluate(
        "(element) => element.scrollIntoView({block: 'center'})"
    )
    page.wait_for_timeout(120)
    fill_path_transform(
        page,
        position=(0.7, 0.25, -0.4),
        rotation=(0, 35, 0),
        scale=(1.3, 1, 0.8),
    )
    state = director_state(page)
    assert selected_path(state)["transform"]["rotation"][1] == 35
    assert page.locator("[data-director-path-reset-offset]").is_visible()
    assert page.locator("[data-director-path-reset]").is_visible()
    panel_box = box(inspector_panel)
    assert panel_box["x"] >= 100
    assert panel_box["x"] + panel_box["width"] <= 390.5
    assert_no_overflow(page)
    page.screenshot(path=str(MOBILE_SCREENSHOT))
    assert errors == [], json.dumps(errors, ensure_ascii=False, indent=2)


def make_contact_sheet():
    items = [
        ("PATH TRANSFORM", TRANSFORM_SCREENSHOT),
        ("WORLD ANCHOR", WORLD_ANCHOR_SCREENSHOT),
        ("RESET OFFSET", RESET_OFFSET_SCREENSHOT),
        ("FULL RESET", FULL_RESET_SCREENSHOT),
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
        thumb = image.resize(
            (target_width, max(1, round(image.height * ratio))),
            Image.Resampling.LANCZOS,
        )
        rendered.append((label, thumb))

    sheet_width = thumb_width * 2 + padding * 3
    column_y = [padding, padding]
    heights = [0, 0]
    for index, (_, image) in enumerate(rendered):
        heights[index % 2] += image.height + label_height + padding
    sheet_height = max(heights) + padding
    sheet = Image.new("RGB", (sheet_width, sheet_height), "#111111")
    draw = ImageDraw.Draw(sheet)
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
    store_source = (ROOT / "src/store/directorStore.ts").read_text()
    inspector_source = (
        ROOT / "src/components/director/DirectorInspector.tsx"
    ).read_text()
    viewport_source = (
        ROOT / "src/components/director/DirectorViewport.tsx"
    ).read_text()
    math_source = (
        ROOT / "src/components/director/directorMotionMath.ts"
    ).read_text()

    assert "initialAnchors" in store_source
    assert "updateMotionPathTransform" in store_source
    assert "updateMotionPathAnchorWorldPosition" in store_source
    assert "resetMotionPathOffset" in store_source
    assert "transformDirectorMotionPathPoint" in math_source
    assert "inverseTransformDirectorMotionPathPoint" in math_source
    assert "buildDirectorMotionPathWorldAnchors" in viewport_source
    assert "data-director-path-transform-field" in inspector_source
    assert "data-director-path-reset-offset" in inspector_source
    assert "data-director-path-reset" in inspector_source


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
    print("Batch 39 director path transform verification passed.")
