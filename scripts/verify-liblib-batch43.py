from io import BytesIO
from pathlib import Path
import json
import math
import os

from PIL import Image, ImageChops, ImageDraw, ImageStat
from playwright.sync_api import Locator, Page, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "docs" / "design-references"
BASE_URL = os.environ.get("LIBLIB_BASE_URL", "http://localhost:3000")

LOOK_AT_SCREENSHOT = (
    REFERENCE_DIR
    / "liblib-clone-batch43-director-look-at-1440-2026-08-26.png"
)
FOLLOW_SCREENSHOT = (
    REFERENCE_DIR
    / "liblib-clone-batch43-director-follow-1440-2026-08-26.png"
)
FIRST_PERSON_SCREENSHOT = (
    REFERENCE_DIR
    / "liblib-clone-batch43-director-first-person-1440-2026-08-26.png"
)
CONFLICT_SCREENSHOT = (
    REFERENCE_DIR
    / "liblib-clone-batch43-director-phone-conflict-1440-2026-08-26.png"
)
MOBILE_SCREENSHOT = (
    REFERENCE_DIR
    / "liblib-clone-batch43-director-follow-mobile-390-2026-08-26.png"
)
CONTACT_SHEET = (
    REFERENCE_DIR
    / "liblib-clone-batch43-director-camera-follow-contact-sheet-2026-08-26.png"
)

CAMERA_ID = "director-camera-main"
CAMERA_TRACK_ID = "director-track-camera-main"
CHARACTER_ID = "director-character-lead"
PATH_CONFLICT = "请先关闭机位跟随，再绘制轨迹"
PHONE_CONFLICT = "请先关闭机位跟随，再使用手机运镜"


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


def image_difference(left: bytes, right: bytes):
    left_image = Image.open(BytesIO(left)).convert("RGB")
    right_image = Image.open(BytesIO(right)).convert("RGB")
    return ImageStat.Stat(ImageChops.difference(left_image, right_image))


def assert_pixel_difference(left: bytes, right: bytes, label: str):
    difference = image_difference(left, right)
    assert max(difference.mean) > 0.1, f"{label}: {difference.mean}"


def assert_finite_tuple(value):
    assert len(value) == 3
    assert all(math.isfinite(item) for item in value)


def open_director(page: Page, force_dom_click: bool = False):
    page.goto(f"{BASE_URL}/?batch43=1", wait_until="networkidle")
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


def prepare_camera(page: Page):
    page.evaluate(
        """({ cameraId, trackId }) => {
          const store = window.__director_store.getState();
          store.selectObject(cameraId);
          store.selectTimelineTrack(trackId);
          store.setViewMode("camera");
        }""",
        {"cameraId": CAMERA_ID, "trackId": CAMERA_TRACK_ID},
    )
    page.locator("[data-director-inspector-kind='camera']").wait_for(
        state="visible"
    )
    page.wait_for_timeout(180)


def director_state(page: Page):
    return page.evaluate(
        """() => {
          const state = window.__director_store.getState();
          return {
            objects: state.objects,
            timeline: state.timeline,
            phoneVcam: state.phoneVcam,
            selectedObjectId: state.selectedObjectId,
            activeCameraId: state.activeCameraId,
            viewMode: state.viewMode,
          };
        }"""
    )


def camera_state(state):
    return next(item for item in state["objects"] if item["id"] == CAMERA_ID)


def character_state(state):
    return next(item for item in state["objects"] if item["id"] == CHARACTER_ID)


def scroll_inspector_to_bottom(page: Page):
    page.locator("[data-director-inspector] > div").evaluate(
        "(element) => { element.scrollTop = element.scrollHeight; }"
    )
    page.wait_for_timeout(80)


def scroll_follow_controls_into_view(page: Page):
    page.locator("[data-director-camera-follow-view]").scroll_into_view_if_needed()
    page.wait_for_timeout(80)


def run_desktop(page: Page):
    errors = attach_errors(page)
    open_director(page)
    prepare_camera(page)
    webgl = page.locator('canvas[data-director-webgl-canvas="true"]')
    assert_nonblank_locator(webgl, "Batch 43 director WebGL canvas")
    coordinate_pixels = webgl.screenshot()

    look_at = page.locator("[data-director-camera-look-at-mode]")
    assert look_at.get_attribute("data-director-camera-look-at-mode") == "coordinate"
    assert look_at.locator("option").all_text_contents() == [
        "手动坐标",
        "手动旋转",
        "角色01 · 陈默",
        "咖啡桌",
        "冷掉的咖啡",
        "咖啡馆背景",
    ]
    assert page.get_by_text("注视目标", exact=True).count() == 1
    assert page.get_by_text("注视坐标", exact=True).count() == 1
    assert page.get_by_text("跟随目标", exact=True).count() == 1

    target_x = page.locator(
        '[data-director-transform-field="target"]'
        '[data-director-transform-axis="x"]'
    )
    target_x.fill("2.5")
    page.wait_for_timeout(120)
    edited_coordinate_pixels = webgl.screenshot()
    assert_pixel_difference(
        coordinate_pixels,
        edited_coordinate_pixels,
        "manual coordinate look-at",
    )

    look_at.select_option("rotation")
    rotation_y = page.locator(
        '[data-director-transform-field="rotation"]'
        '[data-director-transform-axis="y"]'
    )
    rotation_y.fill("135")
    page.wait_for_timeout(120)
    rotation_state = camera_state(director_state(page))
    assert rotation_state["camera"]["lookAtMode"] == "rotation"
    assert rotation_state["transform"]["rotation"][1] == 135
    rotation_pixels = webgl.screenshot()
    assert_pixel_difference(
        edited_coordinate_pixels,
        rotation_pixels,
        "manual camera rotation",
    )

    look_at.select_option(f"object:{CHARACTER_ID}")
    page.wait_for_timeout(120)
    object_state = director_state(page)
    object_camera = camera_state(object_state)
    object_character = character_state(object_state)
    assert object_camera["camera"]["lookAtMode"] == "object"
    assert object_camera["camera"]["lookAtObjectId"] == CHARACTER_ID
    assert abs(
        object_camera["camera"]["target"][0]
        - object_character["transform"]["position"][0]
    ) < 0.001
    assert abs(
        object_camera["camera"]["target"][1]
        - (object_character["transform"]["position"][1] + 1.48)
    ) < 0.001
    object_pixels = webgl.screenshot()
    assert_pixel_difference(rotation_pixels, object_pixels, "object look-at")
    scroll_inspector_to_bottom(page)
    page.screenshot(path=str(LOOK_AT_SCREENSHOT))

    page.evaluate(
        """(trackId) => {
          window.__director_store.getState().createMotionPath("ring", trackId);
        }""",
        CAMERA_TRACK_ID,
    )
    path_count = len(director_state(page)["timeline"]["motionPaths"])
    assert path_count == 1

    follow = page.locator("[data-director-camera-follow-target]")
    follow.select_option(CHARACTER_ID)
    page.wait_for_timeout(160)
    followed_at_zero = director_state(page)
    camera_at_zero = camera_state(followed_at_zero)
    assert camera_at_zero["camera"]["followTargetId"] == CHARACTER_ID
    assert camera_at_zero["camera"]["followView"] == "third-person"
    assert_finite_tuple(camera_at_zero["transform"]["position"])
    assert_finite_tuple(camera_at_zero["camera"]["target"])
    assert camera_at_zero["camera"]["fov"] == 43
    third_person_pixels = webgl.screenshot()
    assert_pixel_difference(object_pixels, third_person_pixels, "third-person follow")

    page.evaluate("window.__director_store.getState().setTimelineTime(4)")
    page.wait_for_timeout(120)
    followed_at_four = director_state(page)
    camera_at_four = camera_state(followed_at_four)
    character_at_four = character_state(followed_at_four)
    assert camera_at_four["camera"]["fov"] == 47
    assert camera_at_four["transform"]["position"] != camera_at_zero["transform"]["position"]
    assert camera_at_four["camera"]["target"] != camera_at_zero["camera"]["target"]
    assert abs(
        camera_at_four["camera"]["target"][0]
        - character_at_four["transform"]["position"][0]
    ) < 0.001
    assert abs(
        camera_at_four["camera"]["target"][1]
        - (character_at_four["transform"]["position"][1] + 1.48)
    ) < 0.001
    assert len(followed_at_four["timeline"]["motionPaths"]) == path_count
    third_person_at_four_pixels = webgl.screenshot()
    scroll_follow_controls_into_view(page)
    assert page.get_by_text(PATH_CONFLICT, exact=True).count() >= 1
    assert page.locator("[data-director-create-motion-path]").is_disabled()
    page.screenshot(path=str(FOLLOW_SCREENSHOT))

    before_guard_count = len(followed_at_four["timeline"]["motionPaths"])
    page.evaluate(
        """(trackId) => {
          const store = window.__director_store.getState();
          store.createMotionPath("line", trackId);
          store.startMotionPathDrawing("pencil", trackId);
        }""",
        CAMERA_TRACK_ID,
    )
    guarded_state = director_state(page)
    assert len(guarded_state["timeline"]["motionPaths"]) == before_guard_count
    assert guarded_state["timeline"]["motionPathDraft"] is None

    page.locator(
        '[data-director-camera-follow-view-option="first-person"]'
    ).click()
    page.wait_for_timeout(120)
    first_person_state = director_state(page)
    first_person_camera = camera_state(first_person_state)
    assert first_person_camera["camera"]["followView"] == "first-person"
    assert first_person_camera["transform"]["position"] == camera_at_four[
        "transform"
    ]["position"]
    assert first_person_camera["camera"]["target"] != camera_at_four["camera"]["target"]
    assert_finite_tuple(first_person_camera["camera"]["target"])
    first_person_pixels = webgl.screenshot()
    assert_pixel_difference(
        third_person_at_four_pixels,
        first_person_pixels,
        "first-person follow",
    )
    page.screenshot(path=str(FIRST_PERSON_SCREENSHOT))

    page.evaluate("window.__director_store.getState().setTimelineTime(0)")
    playback_start = camera_state(director_state(page))["transform"]["position"]
    page.locator("[data-director-playback]").click()
    page.wait_for_timeout(360)
    playback_state = director_state(page)
    assert playback_state["timeline"]["isPlaying"] is True
    assert playback_state["timeline"]["currentTime"] > 0.2
    assert camera_state(playback_state)["transform"]["position"] != playback_start
    page.get_by_role("button", name="暂停").click()

    page.locator("[data-director-phone-vcam-trigger]").click()
    page.locator("[data-director-phone-vcam-panel]").wait_for(state="visible")
    page.wait_for_timeout(380)
    assert page.get_by_text(PHONE_CONFLICT, exact=True).count() == 1
    page.locator("[data-director-phone-vcam-connect]").click()
    phone_state = director_state(page)
    assert phone_state["phoneVcam"]["status"] == "error"
    assert phone_state["phoneVcam"]["error"] == PHONE_CONFLICT
    assert page.get_by_text(PHONE_CONFLICT, exact=True).count() >= 2
    assert page.evaluate(
        "window.__director_store.getState().startPhoneVcamRecording()"
    ) is False
    assert director_state(page)["phoneVcam"]["error"] == PHONE_CONFLICT
    page.screenshot(path=str(CONFLICT_SCREENSHOT))

    page.evaluate(
        """(cameraId) => {
          const store = window.__director_store.getState();
          store.updateCamera(cameraId, { followTargetId: null });
        }""",
        CAMERA_ID,
    )
    page.wait_for_timeout(120)
    recovered = director_state(page)
    recovered_camera = camera_state(recovered)
    assert recovered_camera["camera"]["followTargetId"] is None
    assert recovered_camera["transform"]["position"] != first_person_camera[
        "transform"
    ]["position"]
    assert len(recovered["timeline"]["motionPaths"]) == path_count
    assert not page.locator("[data-director-create-motion-path]").is_disabled()
    assert page.evaluate(
        "window.__director_store.getState().connectPhoneVcamLocal()"
    ) is True
    assert director_state(page)["phoneVcam"]["error"] is None

    assert_no_overflow(page)
    assert errors == [], json.dumps(errors, ensure_ascii=False, indent=2)


def run_mobile(page: Page):
    errors = attach_errors(page)
    open_director(page, force_dom_click=True)
    page.evaluate(
        """({ cameraId, trackId, characterId }) => {
          const store = window.__director_store.getState();
          store.selectObject(cameraId);
          store.selectTimelineTrack(trackId);
          store.setViewMode("camera");
          store.updateCamera(cameraId, {
            lookAtMode: "object",
            lookAtObjectId: characterId,
            followTargetId: characterId,
          });
        }""",
        {
            "cameraId": CAMERA_ID,
            "trackId": CAMERA_TRACK_ID,
            "characterId": CHARACTER_ID,
        },
    )
    page.get_by_role("button", name="打开属性面板").click()
    page.wait_for_timeout(220)
    inspector = page.locator('aside[aria-label="属性"]')
    assert inspector.get_attribute("data-director-mobile-panel-state") == "open"
    inspector_box = box(inspector)
    timeline_box = box(page.locator("[data-director-timeline]"))
    assert inspector_box["x"] >= 100
    assert inspector_box["x"] + inspector_box["width"] <= 390
    assert inspector_box["y"] >= 48
    assert inspector_box["y"] + inspector_box["height"] <= timeline_box["y"]

    follow = page.locator("[data-director-camera-follow-target]")
    follow.scroll_into_view_if_needed()
    assert follow.is_visible()
    assert follow.input_value() == CHARACTER_ID
    page.locator("[data-director-camera-follow-offset]").scroll_into_view_if_needed()
    assert page.locator("[data-director-camera-follow-offset]").is_visible()
    assert page.locator("[data-director-camera-follow-view]").is_visible()
    assert page.get_by_text(PATH_CONFLICT, exact=True).count() >= 1
    inspector_metrics = inspector.evaluate(
        """(element) => ({
          width: element.getBoundingClientRect().width,
          scrollWidth: element.scrollWidth,
          clientHeight: element.clientHeight,
          scrollHeight: element.scrollHeight,
        })"""
    )
    assert inspector_metrics["scrollWidth"] <= inspector_metrics["width"] + 1
    assert inspector_metrics["scrollHeight"] > inspector_metrics["clientHeight"]
    assert_no_overflow(page)
    page.screenshot(path=str(MOBILE_SCREENSHOT))
    assert errors == [], json.dumps(errors, ensure_ascii=False, indent=2)


def make_contact_sheet():
    items = [
        ("LOOK-AT MODES", LOOK_AT_SCREENSHOT),
        ("THIRD-PERSON FOLLOW", FOLLOW_SCREENSHOT),
        ("FIRST-PERSON FOLLOW", FIRST_PERSON_SCREENSHOT),
        ("PHONE CONFLICT", CONFLICT_SCREENSHOT),
        ("MOBILE FOLLOW", MOBILE_SCREENSHOT),
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
        ROOT / "src/components/director/directorCameraFollow.ts"
    ).read_text()
    inspector_source = (
        ROOT / "src/components/director/DirectorInspector.tsx"
    ).read_text()
    viewport_source = (
        ROOT / "src/components/director/DirectorViewport.tsx"
    ).read_text()
    timeline_source = (
        ROOT / "src/components/director/DirectorTimeline.tsx"
    ).read_text()
    phone_source = (
        ROOT / "src/components/director/DirectorPhoneVcamPanel.tsx"
    ).read_text()
    store_source = (ROOT / "src/store/directorStore.ts").read_text()

    for label in [
        "注视目标",
        "手动坐标",
        "手动旋转",
        "注视坐标",
        "跟随目标",
        "不跟随",
        "跟随偏移",
        "跟随视角",
        "第三人称",
        "第一人称",
        PATH_CONFLICT,
    ]:
        assert label in inspector_source or label in timeline_source, label
    assert PHONE_CONFLICT in store_source
    assert PHONE_CONFLICT in phone_source
    assert "resolveDirectorCameraRelation" in math_source
    assert "sampleTimelineObjectsAtTime" in store_source
    assert "resolveCameraRelations" in store_source
    assert 'activeCamera.camera.lookAtMode === "rotation"' in viewport_source
    assert "data-director-camera-follow-state" in inspector_source


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
    print("Batch 43 director camera follow verification passed.")
