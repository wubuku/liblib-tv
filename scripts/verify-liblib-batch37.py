from base64 import b64decode
from io import BytesIO
from pathlib import Path
import json
import math
import os

from PIL import Image, ImageChops, ImageDraw, ImageStat
from playwright.sync_api import Locator, Page, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "docs" / "design-references"
BASE_URL = os.environ.get("LIBLIB_BASE_URL", "http://localhost:4317")

MENU_SCREENSHOT = (
    REFERENCE_DIR
    / "liblib-clone-batch37-director-path-menu-1440-2026-08-26.png"
)
RING_SCREENSHOT = (
    REFERENCE_DIR
    / "liblib-clone-batch37-director-ring-path-1440-2026-08-26.png"
)
CURVE_SCREENSHOT = (
    REFERENCE_DIR
    / "liblib-clone-batch37-director-curve-editor-1440-2026-08-26.png"
)
PLAYBACK_SCREENSHOT = (
    REFERENCE_DIR
    / "liblib-clone-batch37-director-path-playback-1440-2026-08-26.png"
)
MOBILE_SCREENSHOT = (
    REFERENCE_DIR
    / "liblib-clone-batch37-director-path-mobile-390-2026-08-26.png"
)
CONTACT_SHEET = (
    REFERENCE_DIR
    / "liblib-clone-batch37-director-path-contact-sheet-2026-08-26.png"
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


def changed_pixels(before: bytes, after: bytes):
    before_image = Image.open(BytesIO(before)).convert("RGB")
    after_image = Image.open(BytesIO(after)).convert("RGB")
    difference = ImageChops.difference(before_image, after_image).convert("L")
    return sum(value > 8 for value in difference.getdata())


def open_director(page: Page, force_dom_click: bool = False):
    page.goto(BASE_URL, wait_until="networkidle")
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
            selectedObjectId: state.selectedObjectId,
            captures: state.captures,
            activeCaptureId: state.activeCaptureId,
          };
        }"""
    )


def object_by_id(state, object_id: str):
    return next(item for item in state["objects"] if item["id"] == object_id)


def track_by_id(state, track_id: str):
    return next(
        track for track in state["timeline"]["tracks"] if track["id"] == track_id
    )


def selected_path(state):
    path_id = state["timeline"]["selectedMotionPathId"]
    return next(
        path
        for path in state["timeline"]["motionPaths"]
        if path["id"] == path_id
    )


def click_path_preset(page: Page, preset: str):
    page.locator("[data-director-create-motion-path]").click()
    page.locator(f'[data-director-motion-path-preset="{preset}"]').click()


def run_desktop(page: Page):
    errors = attach_errors(page)
    open_director(page)
    timeline = page.locator("[data-director-timeline]")
    assert timeline.get_attribute("data-director-timeline-mode") == "timeline"
    assert director_state(page)["timeline"]["motionPaths"] == []
    assert_no_overflow(page)

    trigger = page.locator("[data-director-create-motion-path]")
    assert trigger.is_enabled()
    trigger.click()
    menu = page.locator("[data-director-motion-path-menu]")
    assert menu.is_visible()
    assert box(menu)["width"] == 176
    labels = menu.locator("[data-director-motion-path-preset]").all_text_contents()
    assert labels == ["直线路径", "圆环路径", "矩形路径"]
    page.screenshot(path=str(MENU_SCREENSHOT))

    canvas = page.locator('canvas[data-director-webgl-canvas="true"]')
    before_path = canvas.screenshot()
    page.locator('[data-director-motion-path-preset="ring"]').click()
    page.wait_for_timeout(180)
    state = director_state(page)
    path = selected_path(state)
    assert path["preset"] == "ring"
    assert path["closed"] is True
    assert path["enabled"] is True
    assert path["orientToPath"] is False
    assert len(path["points"]) == 16
    character_track = track_by_id(
        state, "director-track-character-lead-transform"
    )
    assert character_track["motionPathId"] == path["id"]
    assert page.locator("[data-director-motion-path-id]").count() == 1
    assert page.locator("[data-director-motion-path-anchor]").count() == 16
    assert page.locator("[data-director-motion-path-enabled]").get_attribute(
        "aria-pressed"
    ) == "true"
    after_path = canvas.screenshot()
    assert changed_pixels(before_path, after_path) > 100
    assert_nonblank_locator(canvas, "R3F ring trajectory")
    assert_no_overflow(page)
    page.screenshot(path=str(RING_SCREENSHOT))

    page.evaluate("() => window.__director_store.getState().setTimelineTime(4)")
    state = director_state(page)
    character = object_by_id(state, "director-character-lead")
    assert abs(character["transform"]["position"][0] - (-4.05)) < 0.03
    assert abs(character["transform"]["position"][2] - 0.2) < 0.03
    linear_position = character["transform"]["position"]

    orient = page.locator("[data-director-motion-path-orient]")
    orient.click()
    page.evaluate("() => window.__director_store.getState().setTimelineTime(2)")
    state = director_state(page)
    character = object_by_id(state, "director-character-lead")
    assert abs(character["transform"]["rotation"][1] - 3) > 20
    assert orient.get_attribute("aria-pressed") == "true"
    assert page.locator("[data-director-motion-path-rotation-hint]").inner_text() == (
        "已开启沿路径朝向，Y 轴旋转由运动轨迹控制"
    )
    assert page.locator(
        '[data-director-transform-field="rotation"]'
        '[data-director-transform-axis="y"]'
    ).is_disabled()

    enabled = page.locator("[data-director-motion-path-enabled]")
    enabled.click()
    page.evaluate("() => window.__director_store.getState().setTimelineTime(4)")
    state = director_state(page)
    character = object_by_id(state, "director-character-lead")
    assert abs(character["transform"]["position"][0] - 0.65) < 0.001
    enabled.click()
    page.evaluate("() => window.__director_store.getState().setTimelineTime(4)")
    state = director_state(page)
    character = object_by_id(state, "director-character-lead")
    assert abs(character["transform"]["position"][0] - linear_position[0]) < 0.03

    page.locator("[data-director-open-curve-editor]").click()
    curve_editor = page.locator("[data-director-curve-editor]")
    assert curve_editor.is_visible()
    assert timeline.get_attribute("data-director-timeline-mode") == "curve"
    assert curve_editor.get_attribute("data-director-curve-track-id") == (
        "director-track-character-lead-transform"
    )
    preset_labels = curve_editor.locator(
        "[data-director-curve-preset]"
    ).all_text_contents()
    assert preset_labels == ["线性", "平滑", "缓入", "缓出", "缓入缓出"]
    page.locator('[data-director-curve-preset="ease-in"]').click()
    page.evaluate("() => window.__director_store.getState().setTimelineTime(4)")
    state = director_state(page)
    character = object_by_id(state, "director-character-lead")
    eased_position = character["transform"]["position"]
    assert abs(eased_position[0] - linear_position[0]) > 0.5
    assert track_by_id(
        state, "director-track-character-lead-transform"
    )["speedCurve"]["preset"] == "ease-in"

    first_handle = page.locator('[data-director-curve-handle="1"]')
    handle_box = box(first_handle)
    page.mouse.move(
        handle_box["x"] + handle_box["width"] / 2,
        handle_box["y"] + handle_box["height"] / 2,
    )
    page.mouse.down()
    page.mouse.move(
        handle_box["x"] + handle_box["width"] / 2 + 56,
        handle_box["y"] + handle_box["height"] / 2 - 18,
        steps=5,
    )
    page.mouse.up()
    state = director_state(page)
    curve = track_by_id(
        state, "director-track-character-lead-transform"
    )["speedCurve"]
    assert curve["preset"] == "custom"
    assert all(
        math.isfinite(value) and 0 <= value <= 1
        for value in curve["control1"] + curve["control2"]
    )
    assert "贝塞尔曲线参数" in page.locator(
        "[data-director-curve-values]"
    ).inner_text()
    page.screenshot(path=str(CURVE_SCREENSHOT))

    current_time = state["timeline"]["currentTime"]
    page.locator("[data-director-back-to-timeline]").click()
    assert timeline.get_attribute("data-director-timeline-mode") == "timeline"
    assert abs(director_state(page)["timeline"]["currentTime"] - current_time) < 0.001

    page.evaluate("() => window.__director_store.getState().setTimelineTime(0)")
    start = object_by_id(
        director_state(page), "director-character-lead"
    )["transform"]["position"]
    page.locator("[data-director-playback]").click()
    page.wait_for_timeout(320)
    state = director_state(page)
    playing_position = object_by_id(
        state, "director-character-lead"
    )["transform"]["position"]
    assert state["timeline"]["isPlaying"] is True
    assert state["timeline"]["currentTime"] > 0.2
    assert abs(playing_position[0] - start[0]) > 0.01
    page.screenshot(path=str(PLAYBACK_SCREENSHOT))
    page.get_by_role("button", name="暂停").click()

    click_path_preset(page, "rectangle")
    state = director_state(page)
    assert len(state["timeline"]["motionPaths"]) == 1
    assert selected_path(state)["preset"] == "rectangle"
    click_path_preset(page, "line")
    state = director_state(page)
    assert len(state["timeline"]["motionPaths"]) == 1
    assert selected_path(state)["preset"] == "line"
    page.locator("[data-director-delete-motion-path]").click()
    state = director_state(page)
    assert state["timeline"]["motionPaths"] == []
    assert (
        track_by_id(state, "director-track-character-lead-transform").get(
            "motionPathId"
        )
        is None
    )

    page.locator(
        '[data-director-track-label="director-track-camera-main"] button'
    ).click()
    page.evaluate("() => window.__director_store.getState().setTimelineTime(0)")
    click_path_preset(page, "line")
    state = director_state(page)
    assert selected_path(state)["objectId"] == "director-camera-main"
    assert page.locator("[data-director-motion-path-orient]").count() == 0
    page.evaluate("() => window.__director_store.getState().setTimelineTime(4)")
    camera = object_by_id(director_state(page), "director-camera-main")
    assert camera["transform"]["position"][0] > 5
    page.locator('[data-director-view-mode="camera"]').click()
    assert_nonblank_locator(canvas, "camera motion path sample")
    page.locator('[data-director-view-mode="director"]').click()
    page.locator("[data-director-delete-motion-path]").click()

    page.locator(
        '[data-director-track-label="director-track-character-lead-transform"] button'
    ).click()
    page.evaluate("() => window.__director_store.getState().setTimelineTime(0)")
    click_path_preset(page, "ring")
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
    assert cyan_pixels < 20, f"capture retained cyan helpers: {cyan_pixels}"
    assert errors == [], json.dumps(errors, ensure_ascii=False, indent=2)


def run_mobile(page: Page):
    errors = attach_errors(page)
    open_director(page, force_dom_click=True)
    timeline = page.locator("[data-director-timeline]")
    assert box(timeline)["height"] == 176
    click_path_preset(page, "rectangle")
    state = director_state(page)
    assert len(state["timeline"]["motionPaths"]) == 1
    assert selected_path(state)["preset"] == "rectangle"
    page.locator("[data-director-open-curve-editor]").click()
    page.locator('[data-director-curve-preset="ease-out"]').click()
    assert timeline.get_attribute("data-director-timeline-mode") == "curve"
    graph_scroller = page.locator("[data-director-curve-editor] > div").last
    metrics = graph_scroller.evaluate(
        "(element) => ({ clientWidth: element.clientWidth, scrollWidth: element.scrollWidth })"
    )
    assert metrics["scrollWidth"] > metrics["clientWidth"]
    page.evaluate("() => window.__director_store.getState().setTimelineTime(4)")
    assert track_by_id(
        director_state(page), "director-track-character-lead-transform"
    )["speedCurve"]["preset"] == "ease-out"
    assert page.locator("[data-director-motion-path-id]").count() == 1
    assert_no_overflow(page)
    page.screenshot(path=str(MOBILE_SCREENSHOT))
    assert errors == [], json.dumps(errors, ensure_ascii=False, indent=2)


def make_contact_sheet():
    items = [
        ("PATH MENU", MENU_SCREENSHOT),
        ("RING PATH", RING_SCREENSHOT),
        ("CURVE EDITOR", CURVE_SCREENSHOT),
        ("PATH PLAYBACK", PLAYBACK_SCREENSHOT),
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
    timeline_source = (
        ROOT / "src/components/director/DirectorTimeline.tsx"
    ).read_text()
    curve_source = (
        ROOT / "src/components/director/DirectorCurveEditor.tsx"
    ).read_text()
    motion_source = (
        ROOT / "src/components/director/directorMotionMath.ts"
    ).read_text()
    viewport_source = (
        ROOT / "src/components/director/DirectorViewport.tsx"
    ).read_text()

    assert "DirectorMotionPathPreset" in store_source
    assert "createMotionPath:" in store_source
    assert "sampleDirectorMotionPath" in motion_source
    assert "solveBezierParameter" in motion_source
    assert "data-director-create-motion-path" in timeline_source
    assert "data-director-motion-path-preset" in timeline_source
    assert "data-director-curve-editor" in curve_source
    assert "data-director-curve-handle" in curve_source
    assert "<DirectorMotionPaths />" in viewport_source


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
    print("Batch 37 director motion path verification passed.")
