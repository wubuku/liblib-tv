from base64 import b64decode
from io import BytesIO
from pathlib import Path
import json
import math
import os

from PIL import Image, ImageDraw, ImageStat
from playwright.sync_api import Locator, Page, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "docs" / "design-references"
BASE_URL = os.environ.get("LIBLIB_BASE_URL", "http://localhost:3000")

DEFAULT_SCREENSHOT = (
    REFERENCE_DIR
    / "liblib-clone-batch49-director-gizmo-default-1440-2026-08-26.png"
)
AXIS_SCREENSHOT = (
    REFERENCE_DIR
    / "liblib-clone-batch49-director-gizmo-x-positive-1440-2026-08-26.png"
)
CAMERA_SCREENSHOT = (
    REFERENCE_DIR
    / "liblib-clone-batch49-director-gizmo-camera-mode-1440-2026-08-26.png"
)
CAPTURE_HIDDEN_SCREENSHOT = (
    REFERENCE_DIR
    / "liblib-clone-batch49-director-gizmo-capture-hidden-1440-2026-08-26.png"
)
MOBILE_SCREENSHOT = (
    REFERENCE_DIR
    / "liblib-clone-batch49-director-gizmo-mobile-390-2026-08-26.png"
)
CONTACT_SHEET = (
    REFERENCE_DIR
    / "liblib-clone-batch49-director-gizmo-contact-sheet-2026-08-26.png"
)

AXES = [
    "x-positive",
    "x-negative",
    "y-positive",
    "y-negative",
    "z-positive",
    "z-negative",
]
AXIS_LABELS = {
    "x-positive": "X 正向",
    "x-negative": "X 反向",
    "y-positive": "Y 正向",
    "y-negative": "Y 反向",
    "z-positive": "Z 正向",
    "z-negative": "Z 反向",
}
AXIS_VECTORS = {
    "x-positive": (1, 0, 0),
    "x-negative": (-1, 0, 0),
    "y-positive": (0, 1, 0),
    "y-negative": (0, -1, 0),
    "z-positive": (0, 0, 1),
    "z-negative": (0, 0, -1),
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


def assert_inside(inner: Locator, outer: Locator, tolerance: float = 1):
    inner_box = box(inner)
    outer_box = box(outer)
    assert inner_box["x"] >= outer_box["x"] - tolerance
    assert inner_box["y"] >= outer_box["y"] - tolerance
    assert inner_box["x"] + inner_box["width"] <= (
        outer_box["x"] + outer_box["width"] + tolerance
    )
    assert inner_box["y"] + inner_box["height"] <= (
        outer_box["y"] + outer_box["height"] + tolerance
    )


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
    assert max(spans) > 45, f"{label} has insufficient range: {stat.extrema}"


def open_director(page: Page):
    page.goto(f"{BASE_URL}/?batch49=1", wait_until="networkidle")
    page.locator("[data-open-director]").click()
    page.locator("[data-director-workspace]").wait_for(state="visible")
    page.locator("[data-director-timeline]").wait_for(state="visible")
    page.locator('canvas[data-director-webgl-canvas="true"]').wait_for(
        state="visible"
    )
    page.locator("[data-director-viewport-gizmo]").wait_for(state="visible")
    page.wait_for_timeout(800)


def director_state(page: Page):
    return page.evaluate(
        """() => {
          const state = window.__director_store.getState();
          return {
            objects: state.objects,
            selectedObjectId: state.selectedObjectId,
            selectedObjectIds: state.selectedObjectIds,
            selectedGroupId: state.selectedGroupId,
            activeCameraId: state.activeCameraId,
            viewMode: state.viewMode,
            timeline: state.timeline,
            phoneVcam: state.phoneVcam,
          };
        }"""
    )


def gizmo_position(page: Page):
    raw = page.locator("[data-director-viewport-gizmo]").get_attribute(
        "data-director-viewport-gizmo-position"
    )
    target_raw = page.locator("[data-director-viewport-gizmo]").get_attribute(
        "data-director-viewport-gizmo-target"
    )
    assert raw is not None
    assert target_raw is not None
    return (
        tuple(float(value) for value in raw.split(",")),
        tuple(float(value) for value in target_raw.split(",")),
    )


def assert_axis_position(page: Page, axis: str):
    position, target = gizmo_position(page)
    direction = AXIS_VECTORS[axis]
    relative = tuple(position[index] - target[index] for index in range(3))
    radius = math.sqrt(sum(value * value for value in relative))
    assert radius > 0.1
    projection = sum(relative[index] * direction[index] for index in range(3))
    assert projection / radius > 0.99, (axis, position, target)


def run_desktop(page: Page):
    errors = attach_errors(page)
    open_director(page)
    viewport = page.locator("[data-director-viewport]")
    gizmo = page.locator("[data-director-viewport-gizmo]")
    main_canvas = page.locator('canvas[data-director-webgl-canvas="true"]')
    gizmo_canvas = page.locator('canvas[data-director-gizmo-webgl-canvas="true"]')
    hit_layer = page.locator("[data-director-viewport-gizmo-hit-layer]")
    buttons = page.locator("[data-director-viewport-gizmo-button]")

    assert buttons.count() == 6
    assert sorted(buttons.evaluate_all("(items) => items.map((item) => item.getAttribute('aria-label'))")) == sorted(
        AXIS_LABELS.values()
    )
    assert gizmo.get_attribute("aria-label") == "3D视口原生坐标控件"
    assert hit_layer.get_attribute("data-director-viewport-gizmo-disabled") == "false"
    assert_nonblank_locator(main_canvas, "Batch 49 main Director WebGL canvas")
    assert_nonblank_locator(gizmo_canvas, "Batch 49 gizmo WebGL canvas")
    assert_inside(gizmo, viewport)
    gizmo_box = box(gizmo)
    viewport_box = box(viewport)
    assert abs(gizmo_box["width"] - 80) <= 1
    assert abs(gizmo_box["height"] - 80) <= 1
    assert gizmo_box["x"] + gizmo_box["width"] <= (
        viewport_box["x"] + viewport_box["width"] + 1
    )
    assert gizmo_box["y"] >= viewport_box["y"] + 19
    for index in range(buttons.count()):
        assert_inside(buttons.nth(index), gizmo, tolerance=2)
    assert_no_overflow(page)
    page.screenshot(path=str(DEFAULT_SCREENSHOT))

    initial = director_state(page)
    initial_canvas = main_canvas.screenshot()
    for axis in AXES:
        button = page.locator(
            f"[data-director-viewport-gizmo-button='{axis}']"
        )
        if axis == "x-positive":
            button.click()
        else:
            button.dispatch_event("click")
        page.wait_for_timeout(150)
        state = director_state(page)
        assert state["viewMode"] == "director"
        assert state["objects"] == initial["objects"]
        assert state["timeline"] == initial["timeline"]
        assert state["selectedObjectId"] == initial["selectedObjectId"]
        assert state["selectedObjectIds"] == initial["selectedObjectIds"]
        assert state["selectedGroupId"] == initial["selectedGroupId"]
        assert_axis_position(page, axis)
        next_canvas = main_canvas.screenshot()
        if axis == "x-positive":
            assert next_canvas != initial_canvas
            page.screenshot(path=str(AXIS_SCREENSHOT))

    page.locator("[data-director-view-mode='camera']").click()
    page.wait_for_timeout(280)
    camera_mode_state = director_state(page)
    camera_objects = camera_mode_state["objects"]
    assert camera_mode_state["viewMode"] == "camera"
    page.screenshot(path=str(CAMERA_SCREENSHOT))
    page.locator(
        "[data-director-viewport-gizmo-button='y-negative']"
    ).dispatch_event("click")
    page.wait_for_timeout(180)
    after_camera_axis = director_state(page)
    assert after_camera_axis["viewMode"] == "director"
    assert after_camera_axis["objects"] == camera_objects
    assert_axis_position(page, "y-negative")

    page.evaluate(
        """() => {
          const store = window.__director_store.getState();
          store.startMotionPathDrawing(
            "pencil",
            "director-track-character-lead-transform",
          );
        }"""
    )
    page.locator("[data-director-path-drawing]").wait_for(state="visible")
    assert hit_layer.get_attribute("data-director-viewport-gizmo-disabled") == "true"
    assert buttons.count() == 6
    assert all(buttons.nth(index).is_disabled() for index in range(buttons.count()))
    page.evaluate(
        "window.__director_store.getState().cancelMotionPathDrawing()"
    )
    page.wait_for_timeout(120)
    assert hit_layer.get_attribute("data-director-viewport-gizmo-disabled") == "false"

    page.locator("[data-director-phone-vcam-trigger]").click()
    page.locator("[data-director-phone-vcam-panel]").wait_for(state="visible")
    assert page.evaluate(
        "window.__director_store.getState().connectPhoneVcamLocal()"
    ) is True
    assert page.evaluate(
        "window.__director_store.getState().startPhoneVcamRecording()"
    ) is True
    page.wait_for_timeout(120)
    assert page.locator(
        "[data-director-capture-status='phone-recording']"
    ).is_visible()
    assert hit_layer.get_attribute("data-director-viewport-gizmo-disabled") == "true"
    assert all(buttons.nth(index).is_disabled() for index in range(buttons.count()))
    page.evaluate(
        "window.__director_store.getState().setPhoneVcamStatus('idle')"
    )
    page.wait_for_timeout(120)

    page.locator("[data-director-capture]").click()
    page.locator("[data-director-viewport-gizmo]").wait_for(state="hidden")
    page.screenshot(path=str(CAPTURE_HIDDEN_SCREENSHOT))
    page.locator("[data-director-capture-preview]").wait_for(state="visible")
    capture = page.evaluate(
        """() => window.__director_store.getState().captures.at(-1)"""
    )
    assert capture is not None
    capture_image = Image.open(
        BytesIO(b64decode(capture["dataUrl"].split(",", 1)[1]))
    )
    assert capture_image.width > 100
    assert capture_image.height > 100
    page.locator("[data-director-viewport-gizmo]").wait_for(state="visible")
    assert_no_overflow(page)
    assert errors == [], json.dumps(errors, ensure_ascii=False, indent=2)


def run_mobile(page: Page):
    errors = attach_errors(page)
    open_director(page)
    viewport = page.locator("[data-director-viewport]")
    gizmo = page.locator("[data-director-viewport-gizmo]")
    buttons = page.locator("[data-director-viewport-gizmo-button]")
    assert_inside(gizmo, viewport)
    gizmo_box = box(gizmo)
    viewport_box = box(viewport)
    assert gizmo_box["x"] >= viewport_box["x"]
    assert gizmo_box["x"] + gizmo_box["width"] <= (
        viewport_box["x"] + viewport_box["width"] + 1
    )
    assert gizmo_box["y"] >= viewport_box["y"]
    assert gizmo_box["y"] + gizmo_box["height"] <= (
        viewport_box["y"] + viewport_box["height"] + 1
    )
    for index in range(buttons.count()):
        assert_inside(buttons.nth(index), gizmo, tolerance=2)
    assert_no_overflow(page)
    assert_nonblank_locator(
        page.locator('canvas[data-director-gizmo-webgl-canvas="true"]'),
        "Batch 49 mobile gizmo WebGL canvas",
    )
    page.screenshot(path=str(MOBILE_SCREENSHOT))
    assert errors == [], json.dumps(errors, ensure_ascii=False, indent=2)


def make_contact_sheet():
    items = [
        ("DEFAULT", DEFAULT_SCREENSHOT),
        ("X POSITIVE", AXIS_SCREENSHOT),
        ("CAMERA MODE", CAMERA_SCREENSHOT),
        ("CAPTURE HIDES GIZMO", CAPTURE_HIDDEN_SCREENSHOT),
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
    math_source = (
        ROOT / "src/components/director/directorViewportMath.ts"
    ).read_text()
    viewport_source = (
        ROOT / "src/components/director/DirectorViewport.tsx"
    ).read_text()
    assert "DirectorViewportSnapshot" in math_source
    assert "getDirectorViewportAxisSnapshot" in math_source
    assert "GizmoHelper" in viewport_source
    assert "GizmoViewport" in viewport_source
    assert "DirectorCameraSnapshotBridge" in viewport_source
    assert "data-director-viewport-gizmo-button" in viewport_source
    assert "directorCameraCommand" in viewport_source
    assert "preserveDrawingBuffer: true" in viewport_source


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
    print("Batch 49 director viewport gizmo verification passed.")
