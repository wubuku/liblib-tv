from io import BytesIO
from pathlib import Path
import json
import os

from PIL import Image, ImageChops, ImageDraw, ImageStat
from playwright.sync_api import Locator, Page, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "docs" / "design-references"
BASE_URL = os.environ.get("LIBLIB_BASE_URL", "http://localhost:4317")

PRESETS_SCREENSHOT = (
    REFERENCE_DIR
    / "liblib-clone-batch42-director-pose-presets-1440-2026-08-26.png"
)
SAM_SCREENSHOT = (
    REFERENCE_DIR
    / "liblib-clone-batch42-director-sam-controls-1440-2026-08-26.png"
)
TIMELINE_SCREENSHOT = (
    REFERENCE_DIR
    / "liblib-clone-batch42-director-pose-timeline-1440-2026-08-26.png"
)
INTERPOLATION_SCREENSHOT = (
    REFERENCE_DIR
    / "liblib-clone-batch42-director-pose-interpolation-1440-2026-08-26.png"
)
MOBILE_SCREENSHOT = (
    REFERENCE_DIR
    / "liblib-clone-batch42-director-pose-mobile-390-2026-08-26.png"
)
CONTACT_SHEET = (
    REFERENCE_DIR
    / "liblib-clone-batch42-director-pose-contact-sheet-2026-08-26.png"
)

PRESET_LABELS = [
    "站立",
    "T型",
    "行走",
    "跑步",
    "坐姿",
    "蹲下",
    "单膝跪",
    "双膝跪",
    "叉腰",
    "倚靠",
    "鞠躬",
    "思考",
    "格斗",
    "踢球",
    "投掷",
    "推进",
    "招手",
    "伸手",
    "抱臂",
    "看手机",
]

GROUP_LABELS = ["身体", "头颈", "左臂", "右臂", "左腿", "右腿"]
BONE_LABELS = [
    "根骨骼",
    "腰部",
    "脊柱 1",
    "脊柱 2",
    "胸腔",
    "颈部",
    "头部",
    "锁骨",
    "上臂",
    "前臂",
    "手腕",
    "大腿",
    "小腿",
    "脚掌",
]


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


def open_director(page: Page, force_dom_click: bool = False):
    page.goto(f"{BASE_URL}/?batch42=1", wait_until="networkidle")
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
            objects: state.objects,
            timeline: state.timeline,
            selectedObjectId: state.selectedObjectId,
          };
        }"""
    )


def lead_character(state):
    return next(
        item
        for item in state["objects"]
        if item["id"] == "director-character-lead"
    )


def lead_tracks(state):
    return [
        track
        for track in state["timeline"]["tracks"]
        if track["objectId"] == "director-character-lead"
    ]


def pose_track(state):
    return next(track for track in lead_tracks(state) if track["kind"] == "pose")


def open_pose_panel(page: Page):
    page.locator('[data-director-character-tab="pose"]').click()
    panel = page.locator("[data-director-pose-panel]")
    panel.wait_for(state="visible")
    return panel


def run_desktop(page: Page):
    errors = attach_errors(page)
    open_director(page)
    webgl = page.locator('canvas[data-director-webgl-canvas="true"]')
    assert_nonblank_locator(webgl, "Batch 42 director WebGL canvas")
    stand_pixels = webgl.screenshot()

    tabs = page.locator("[data-director-character-tabs]")
    assert tabs.count() == 1
    assert (
        page.locator('[data-director-character-tab="properties"]').get_attribute(
            "aria-pressed"
        )
        == "true"
    )
    panel = open_pose_panel(page)
    assert page.locator("[data-director-pose-preset]").count() == 20
    assert page.locator("[data-director-pose-group]").count() == 6
    for label in PRESET_LABELS:
        assert panel.get_by_text(label, exact=True).count() >= 1, label
    for label in GROUP_LABELS:
        assert panel.get_by_text(label, exact=True).count() >= 1, label
    panel_text = panel.inner_text()
    for label in BONE_LABELS:
        assert label in panel_text, label
    pose_state = page.locator("[data-director-pose-state]")
    assert pose_state.get_attribute("data-pose-preset") == "stand"
    page.screenshot(path=str(PRESETS_SCREENSHOT))

    page.locator('[data-director-pose-preset="wave"]').click()
    page.wait_for_timeout(180)
    wave_state = director_state(page)
    wave_character = lead_character(wave_state)
    wave_track = pose_track(wave_state)
    assert [track["kind"] for track in lead_tracks(wave_state)] == [
        "transform",
        "pose",
    ]
    assert wave_character["characterRig"]["posePresetId"] == "wave"
    assert wave_character["characterRig"]["controls"]["rightElbow.bend"] == 90
    assert len(wave_track["keyframes"]) == 1
    assert wave_track["keyframes"][0]["time"] == 0
    assert wave_track["label"] == "角色01 · 陈默 · 姿态"
    assert wave_state["timeline"]["selectedTrackId"] == wave_track["id"]
    assert page.locator("[data-director-create-motion-path]").is_disabled()
    wave_pixels = webgl.screenshot()
    wave_diff = image_difference(stand_pixels, wave_pixels)
    assert max(wave_diff.mean) > 0.12, wave_diff.mean

    right_arm = page.locator('[data-director-pose-group="right-arm"]')
    right_arm.get_by_role("button").click()
    right_arm.locator(
        '[data-director-pose-control="rightShoulder.pitch"]'
    ).wait_for(state="visible")
    right_arm.scroll_into_view_if_needed()
    page.screenshot(path=str(SAM_SCREENSHOT))

    page.evaluate("window.__director_store.getState().setTimelineTime(4)")
    page.locator('[data-director-pose-preset="kick"]').click()
    kick_state = director_state(page)
    kick_track = pose_track(kick_state)
    assert [keyframe["time"] for keyframe in kick_track["keyframes"]] == [0, 4]
    assert kick_state["timeline"]["selectedTrackId"] == kick_track["id"]
    assert page.locator('[data-director-track-kind="pose"]').count() == 1
    assert (
        page.locator('[data-director-track-kind="pose"]').get_attribute(
            "data-director-track-object-id"
        )
        == "director-character-lead"
    )
    assert (
        page.locator('[data-director-track-kind="pose"]')
        .locator("[data-director-keyframe-id]")
        .count()
        == 2
    )
    motion_path_count = len(kick_state["timeline"]["motionPaths"])
    page.evaluate(
        """(trackId) =>
          window.__director_store.getState().createMotionPath("ring", trackId)
        """,
        kick_track["id"],
    )
    assert len(director_state(page)["timeline"]["motionPaths"]) == (
        motion_path_count
    )
    kick_pixels = webgl.screenshot()
    page.screenshot(path=str(TIMELINE_SCREENSHOT))

    page.evaluate("window.__director_store.getState().setTimelineTime(2)")
    page.wait_for_timeout(120)
    middle_state = director_state(page)
    middle_character = lead_character(middle_state)
    assert abs(middle_character["transform"]["position"][0] - (-0.3)) < 0.02
    assert abs(
        middle_character["characterRig"]["controls"]["rightShoulder.pitch"]
        - 18
    ) < 0.05
    assert abs(
        middle_character["characterRig"]["controls"]["rightElbow.bend"] - 45
    ) < 0.05
    assert middle_character["characterRig"]["posePresetId"] is None
    middle_pixels = webgl.screenshot()
    endpoint_diff = image_difference(middle_pixels, kick_pixels)
    assert max(endpoint_diff.mean) > 0.1, endpoint_diff.mean
    page.screenshot(path=str(INTERPOLATION_SCREENSHOT))

    page.locator("[data-director-add-keyframe]").click()
    inserted_state = director_state(page)
    inserted_track = pose_track(inserted_state)
    assert [keyframe["time"] for keyframe in inserted_track["keyframes"]] == [
        0,
        2,
        4,
    ]
    inserted_id = inserted_state["timeline"]["selectedKeyframeId"]
    assert inserted_id is not None
    page.locator("[data-director-delete-keyframe]").click()
    assert [
        keyframe["time"]
        for keyframe in pose_track(director_state(page))["keyframes"]
    ] == [0, 4]

    page.evaluate("window.__director_store.getState().setTimelineTime(3)")
    if right_arm.get_by_role("button").get_attribute("aria-expanded") == "false":
        right_arm.get_by_role("button").click()
    shoulder = right_arm.locator(
        '[data-director-pose-control="rightShoulder.pitch"]'
    )
    shoulder.fill("25")
    custom_state = director_state(page)
    custom_track = pose_track(custom_state)
    assert pose_state.get_attribute("data-pose-preset") == "custom"
    assert [keyframe["time"] for keyframe in custom_track["keyframes"]] == [
        0,
        3,
        4,
    ]
    assert custom_track["keyframes"][1]["value"]["controls"][
        "rightShoulder.pitch"
    ] == 25

    page.evaluate("window.__director_store.getState().setTimelineTime(2)")
    page.get_by_role("button", name="下一关键帧").click()
    assert director_state(page)["timeline"]["currentTime"] == 3
    page.get_by_role("button", name="上一关键帧").click()
    assert director_state(page)["timeline"]["currentTime"] == 0

    page.locator("[data-director-playback]").click()
    page.wait_for_timeout(320)
    playing_state = director_state(page)
    assert playing_state["timeline"]["isPlaying"] is True
    assert playing_state["timeline"]["currentTime"] > 0.2
    assert (
        lead_character(playing_state)["characterRig"]["controls"][
            "rightElbow.bend"
        ]
        < 90
    )
    page.get_by_role("button", name="暂停").click()

    assert_no_overflow(page)
    assert errors == [], json.dumps(errors, ensure_ascii=False, indent=2)


def run_mobile(page: Page):
    errors = attach_errors(page)
    open_director(page, force_dom_click=True)
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

    panel = open_pose_panel(page)
    assert panel.is_visible()
    assert page.locator("[data-director-pose-preset]").count() == 20
    page.locator('[data-director-pose-preset="phone"]').click()
    assert (
        page.locator("[data-director-pose-state]").get_attribute(
            "data-pose-preset"
        )
        == "phone"
    )
    assert page.locator('[data-director-track-kind="pose"]').count() == 1
    panel_metrics = panel.evaluate(
        """(element) => ({
          width: element.getBoundingClientRect().width,
          scrollWidth: element.scrollWidth,
          parentClientHeight: element.parentElement.clientHeight,
          parentScrollHeight: element.parentElement.scrollHeight,
        })"""
    )
    assert panel_metrics["scrollWidth"] <= panel_metrics["width"] + 1
    assert panel_metrics["parentScrollHeight"] > panel_metrics["parentClientHeight"]
    assert_no_overflow(page)
    page.screenshot(path=str(MOBILE_SCREENSHOT))
    assert errors == [], json.dumps(errors, ensure_ascii=False, indent=2)


def make_contact_sheet():
    items = [
        ("POSE PRESETS", PRESETS_SCREENSHOT),
        ("SAM CONTROLS", SAM_SCREENSHOT),
        ("POSE TRACK", TIMELINE_SCREENSHOT),
        ("INTERPOLATED POSE", INTERPOLATION_SCREENSHOT),
        ("MOBILE POSE", MOBILE_SCREENSHOT),
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
    pose_source = (
        ROOT / "src/components/director/directorPose.ts"
    ).read_text()
    mannequin_source = (
        ROOT / "src/components/director/DirectorMannequin.tsx"
    ).read_text()
    inspector_source = (
        ROOT / "src/components/director/DirectorInspector.tsx"
    ).read_text()
    timeline_source = (
        ROOT / "src/components/director/DirectorTimeline.tsx"
    ).read_text()
    math_source = (
        ROOT / "src/components/director/directorTimelineMath.ts"
    ).read_text()
    store_source = (ROOT / "src/store/directorStore.ts").read_text()

    for label in PRESET_LABELS + GROUP_LABELS + BONE_LABELS:
        assert label in pose_source, label
    assert "DIRECTOR_POSE_PRESET_IDS" in pose_source
    assert "interpolateDirectorPoseValue" in pose_source
    assert "director-articulated-character" in mannequin_source
    assert "data-director-character-tab" in inspector_source
    assert "data-director-pose-control" in inspector_source
    assert 'kind: "pose"' in store_source
    assert "tracksByObject" in store_source
    assert 'track.kind === "pose"' in timeline_source
    assert 'kind: "pose"' in math_source


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
    print("Batch 42 director character pose verification passed.")
