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

PRESET_PANEL_SCREENSHOT = (
    REFERENCE_DIR
    / "liblib-clone-batch44-director-preset-panel-1440-2026-08-26.png"
)
REPLACE_SCREENSHOT = (
    REFERENCE_DIR
    / "liblib-clone-batch44-director-preset-replace-1440-2026-08-26.png"
)
APPEND_SCREENSHOT = (
    REFERENCE_DIR
    / "liblib-clone-batch44-director-preset-append-1440-2026-08-26.png"
)
NO_ROOM_SCREENSHOT = (
    REFERENCE_DIR
    / "liblib-clone-batch44-director-preset-no-room-1440-2026-08-26.png"
)
FOLLOW_CONFLICT_SCREENSHOT = (
    REFERENCE_DIR
    / "liblib-clone-batch44-director-preset-follow-conflict-1440-2026-08-26.png"
)
MOBILE_SCREENSHOT = (
    REFERENCE_DIR
    / "liblib-clone-batch44-director-preset-mobile-390-2026-08-26.png"
)
CONTACT_SHEET = (
    REFERENCE_DIR
    / "liblib-clone-batch44-director-preset-camera-contact-sheet-2026-08-26.png"
)

CAMERA_ID = "director-camera-main"
CAMERA_TRACK_ID = "director-track-camera-main"
CHARACTER_ID = "director-character-lead"
PRESET_IDS = [
    "orbit",
    "half-arc",
    "push-in",
    "pull-out",
    "pedestal-up",
    "truck-right",
    "spiral-up",
]
PRESET_LABELS = ["环绕", "半弧", "推近", "拉远", "升降", "横移", "螺旋上升"]
NO_ROOM = "当前时间轴没有可追加的时长"
FOLLOW_CONFLICT = "跟随目标时不可使用预设运镜"


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


def assert_finite_value(value):
    if isinstance(value, list):
        assert all(math.isfinite(item) for item in value)
    else:
        assert math.isfinite(value)


def open_director(page: Page, force_dom_click: bool = False):
    page.goto(f"{BASE_URL}/?batch44=1", wait_until="networkidle")
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
            selectedObjectId: state.selectedObjectId,
            activeCameraId: state.activeCameraId,
            viewMode: state.viewMode,
          };
        }"""
    )


def camera_state(state):
    return next(item for item in state["objects"] if item["id"] == CAMERA_ID)


def camera_track(state):
    return next(
        track
        for track in state["timeline"]["tracks"]
        if track["id"] == CAMERA_TRACK_ID
    )


def open_preset_panel(page: Page):
    trigger = page.locator("[data-director-camera-preset-trigger]")
    assert trigger.count() == 1
    assert not trigger.is_disabled()
    trigger.click()
    panel = page.locator("[data-director-camera-preset-panel]")
    panel.wait_for(state="visible")
    return panel


def run_preset_pixel_matrix(browser):
    for preset_id in PRESET_IDS:
        page = browser.new_page(
            viewport={"width": 1440, "height": 900},
            device_scale_factor=1,
        )
        errors = attach_errors(page)
        open_director(page)
        prepare_camera(page)
        webgl = page.locator('canvas[data-director-webgl-canvas="true"]')
        page.evaluate(
            "window.__director_store.getState().setTimelineTime(4)"
        )
        page.wait_for_timeout(100)
        baseline_pixels = webgl.screenshot()
        page.evaluate(
            "window.__director_store.getState().setTimelineTime(0)"
        )
        applied = page.evaluate(
            """({ preset, trackId }) =>
              window.__director_store.getState().applyCameraMotionPreset(
                preset,
                "replace",
                trackId,
              )""",
            {"preset": preset_id, "trackId": CAMERA_TRACK_ID},
        )
        assert applied is True, preset_id
        page.evaluate(
            "window.__director_store.getState().setTimelineTime(4)"
        )
        page.wait_for_timeout(100)
        state = director_state(page)
        track = camera_track(state)
        assert len(track["keyframes"]) >= 3
        for keyframe in track["keyframes"]:
            assert_finite_value(keyframe["value"]["transform"]["position"])
            assert_finite_value(keyframe["value"]["target"])
            assert_finite_value(keyframe["value"]["fov"])
        assert_pixel_difference(
            baseline_pixels,
            webgl.screenshot(),
            f"preset {preset_id}",
        )
        assert errors == [], json.dumps(errors, ensure_ascii=False, indent=2)
        page.close()


def run_desktop(page: Page):
    errors = attach_errors(page)
    open_director(page)
    prepare_camera(page)
    webgl = page.locator('canvas[data-director-webgl-canvas="true"]')
    assert_nonblank_locator(webgl, "Batch 44 director WebGL canvas")

    panel = open_preset_panel(page)
    assert page.locator("[data-director-camera-preset-option]").count() == 7
    assert panel.get_by_text("预设运镜", exact=True).count() == 1
    assert panel.get_by_text("替换运镜", exact=True).count() == 1
    assert panel.get_by_text("追加运镜", exact=True).count() == 1
    for label in PRESET_LABELS:
        assert panel.get_by_text(label, exact=True).count() == 1, label
    assert page.locator('[data-director-camera-preset-mode-option="replace"]').get_attribute(
        "aria-pressed"
    ) == "true"
    page.screenshot(path=str(PRESET_PANEL_SCREENSHOT))

    page.locator('[data-director-camera-preset-option="orbit"]').click()
    page.wait_for_timeout(130)
    replaced = director_state(page)
    replaced_track = camera_track(replaced)
    assert [keyframe["time"] for keyframe in replaced_track["keyframes"]] == [
        0,
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
    ]
    application = replaced["timeline"]["cameraMotionPreset"]["application"]
    assert application["preset"] == "orbit"
    assert application["mode"] == "replace"
    assert application["startTime"] == 0
    assert application["endTime"] == 8
    assert len(application["generatedKeyframeIds"]) == 9
    for keyframe in replaced_track["keyframes"]:
        assert keyframe["value"]["fov"] == 43
        assert_finite_value(keyframe["value"]["transform"]["position"])
        assert_finite_value(keyframe["value"]["target"])
    page.locator("[data-director-camera-preset-panel]").wait_for(state="visible")
    assert page.locator("[data-director-camera-preset-status]").count() == 1
    page.evaluate("window.__director_store.getState().setTimelineTime(4)")
    page.wait_for_timeout(100)
    page.screenshot(path=str(REPLACE_SCREENSHOT))

    page.locator('[data-director-camera-preset-mode-option="append"]').click()
    page.locator('[data-director-camera-preset-option="push-in"]').click()
    after_append = director_state(page)
    append_track = camera_track(after_append)
    assert [keyframe["time"] for keyframe in append_track["keyframes"]] == list(
        range(9)
    )
    assert after_append["timeline"]["cameraMotionPreset"]["error"] is not None
    assert after_append["timeline"]["cameraMotionPreset"]["error"]["message"] == (
        NO_ROOM
    )
    assert page.get_by_text(NO_ROOM, exact=True).count() == 1
    page.screenshot(path=str(NO_ROOM_SCREENSHOT))

    append_errors = attach_errors(page)
    open_director(page)
    prepare_camera(page)
    page.evaluate(
        """({ trackId }) => {
          const state = window.__director_store.getState();
          const track = state.timeline.tracks.find(
            (item) => item.id === trackId,
          );
          if (!track) throw new Error("camera track not found");
          state.deleteTimelineKeyframe("director-keyframe-camera-8");
          state.setTimelineTime(0);
        }""",
        {"trackId": CAMERA_TRACK_ID},
    )
    page.wait_for_timeout(80)
    open_preset_panel(page)
    page.locator(
        '[data-director-camera-preset-mode-option="append"]'
    ).click()
    page.locator(
        '[data-director-camera-preset-option="pull-out"]'
    ).click()
    appended = director_state(page)
    appended_track = camera_track(appended)
    assert [keyframe["time"] for keyframe in appended_track["keyframes"]] == [
        0,
        4,
        6,
        8,
    ]
    assert appended["timeline"]["cameraMotionPreset"]["application"]["mode"] == (
        "append"
    )
    assert appended["timeline"]["cameraMotionPreset"]["application"]["startTime"] == 4
    assert page.locator("[data-director-camera-preset-status]").count() == 1
    page.evaluate("window.__director_store.getState().setTimelineTime(6)")
    page.wait_for_timeout(100)
    page.screenshot(path=str(APPEND_SCREENSHOT))
    assert append_errors == [], json.dumps(
        append_errors, ensure_ascii=False, indent=2
    )
    path_errors = attach_errors(page)
    open_director(page)
    prepare_camera(page)
    page.evaluate(
        """({ trackId }) => {
          const store = window.__director_store.getState();
          store.createMotionPath("ring", trackId);
          store.selectTimelineTrack(trackId);
        }""",
        {"trackId": CAMERA_TRACK_ID},
    )
    page.wait_for_timeout(100)
    before_path = director_state(page)
    before_path_id = camera_track(before_path)["motionPathId"]
    assert before_path_id
    page.evaluate(
        """({ preset, trackId }) =>
          window.__director_store.getState().applyCameraMotionPreset(
            preset,
            "replace",
            trackId,
          )""",
        {"preset": "half-arc", "trackId": CAMERA_TRACK_ID},
    )
    after_path = director_state(page)
    after_path_track = camera_track(after_path)
    retained_path = next(
        path
        for path in after_path["timeline"]["motionPaths"]
        if path["id"] == before_path_id
    )
    assert after_path_track["motionPathId"] == before_path_id
    assert retained_path["enabled"] is False
    assert path_errors == [], json.dumps(path_errors, ensure_ascii=False, indent=2)
    page.goto(f"{BASE_URL}/?batch44=1", wait_until="networkidle")
    page.locator("[data-open-director]").click()
    page.locator("[data-director-workspace]").wait_for(state="visible")
    page.locator("[data-director-timeline]").wait_for(state="visible")
    page.locator('canvas[data-director-webgl-canvas="true"]').wait_for(
        state="visible"
    )
    page.wait_for_timeout(650)
    prepare_camera(page)
    page.evaluate(
        """({ cameraId, characterId, trackId }) => {
          const store = window.__director_store.getState();
          store.updateCamera(cameraId, {
            followTargetId: characterId,
          });
          store.selectTimelineTrack(trackId);
        }""",
        {
            "cameraId": CAMERA_ID,
            "characterId": CHARACTER_ID,
            "trackId": CAMERA_TRACK_ID,
        },
    )
    page.wait_for_timeout(120)
    before_conflict = director_state(page)
    before_keyframes = len(camera_track(before_conflict)["keyframes"])
    assert page.locator("[data-director-camera-preset-trigger]").is_disabled()
    assert page.get_by_text(FOLLOW_CONFLICT, exact=True).count() >= 1
    if page.locator("[data-director-camera-preset-panel]").is_visible():
        page.keyboard.press("Escape")
    page.locator("[data-director-camera-preset-panel]").wait_for(
        state="hidden"
    )
    conflict_result = page.evaluate(
        """({ preset, trackId }) =>
          window.__director_store.getState().applyCameraMotionPreset(
            preset,
            "replace",
            trackId,
          )""",
        {"preset": "spiral-up", "trackId": CAMERA_TRACK_ID},
    )
    assert conflict_result is False
    conflict_state = director_state(page)
    assert len(camera_track(conflict_state)["keyframes"]) == before_keyframes
    assert (
        conflict_state["timeline"]["cameraMotionPreset"]["error"]["message"]
        == FOLLOW_CONFLICT
    )
    page.locator("[data-director-phone-vcam-trigger]").click()
    page.locator("[data-director-phone-vcam-panel]").wait_for(state="visible")
    page.wait_for_timeout(380)
    page.screenshot(path=str(FOLLOW_CONFLICT_SCREENSHOT))

    page.evaluate(
        """(cameraId) =>
          window.__director_store.getState().updateCamera(cameraId, {
            followTargetId: null,
          })""",
        CAMERA_ID,
    )
    page.wait_for_timeout(100)
    assert not page.locator("[data-director-camera-preset-trigger]").is_disabled()
    assert_no_overflow(page)
    assert errors == [], json.dumps(errors, ensure_ascii=False, indent=2)


def run_mobile(page: Page):
    errors = attach_errors(page)
    open_director(page, force_dom_click=True)
    prepare_camera(page)
    trigger = page.locator("[data-director-camera-preset-trigger]")
    trigger.scroll_into_view_if_needed()
    trigger.click()
    panel = page.locator("[data-director-camera-preset-panel]")
    panel.wait_for(state="visible")
    panel_box = box(panel)
    assert panel_box["x"] >= 0
    assert panel_box["x"] + panel_box["width"] <= 390
    timeline_box = box(page.locator("[data-director-timeline]"))
    assert panel_box["y"] >= 0
    assert (
        panel_box["y"] + panel_box["height"] <= timeline_box["y"] + 1
    ), {"panel": panel_box, "timeline": timeline_box}
    assert page.locator("[data-director-camera-preset-option]").count() == 7
    assert page.get_by_text("替换运镜", exact=True).count() == 1
    panel_metrics = panel.evaluate(
        """(element) => ({
          width: element.getBoundingClientRect().width,
          scrollWidth: element.scrollWidth,
          height: element.getBoundingClientRect().height,
        })"""
    )
    assert panel_metrics["scrollWidth"] <= panel_metrics["width"] + 1
    assert panel_metrics["height"] > 0
    assert_no_overflow(page)
    page.screenshot(path=str(MOBILE_SCREENSHOT))
    assert errors == [], json.dumps(errors, ensure_ascii=False, indent=2)


def make_contact_sheet():
    items = [
        ("PRESET PANEL", PRESET_PANEL_SCREENSHOT),
        ("REPLACE ORBIT", REPLACE_SCREENSHOT),
        ("APPEND PULL-OUT", APPEND_SCREENSHOT),
        ("NO ROOM", NO_ROOM_SCREENSHOT),
        ("FOLLOW CONFLICT", FOLLOW_CONFLICT_SCREENSHOT),
        ("MOBILE PANEL", MOBILE_SCREENSHOT),
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
    preset_source = (
        ROOT / "src/components/director/directorCameraPresets.ts"
    ).read_text()
    timeline_source = (
        ROOT / "src/components/director/DirectorTimeline.tsx"
    ).read_text()
    store_source = (ROOT / "src/store/directorStore.ts").read_text()

    for label in ["预设运镜", "替换运镜", "追加运镜"]:
        assert label in timeline_source, label
    for label in PRESET_LABELS:
        assert label in preset_source, label
    assert NO_ROOM in store_source
    assert FOLLOW_CONFLICT in store_source
    assert "createDirectorCameraMotionPresetValues" in preset_source
    assert "applyCameraMotionPreset" in store_source
    assert "cameraMotionPreset" in store_source
    assert "data-director-camera-preset-option" in timeline_source


if __name__ == "__main__":
    REFERENCE_DIR.mkdir(parents=True, exist_ok=True)
    verify_static_contract()
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        run_preset_pixel_matrix(browser)
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
    print("Batch 44 director preset camera motion verification passed.")
