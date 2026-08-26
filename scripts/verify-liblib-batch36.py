from io import BytesIO
from pathlib import Path
import json
import os

from PIL import Image, ImageDraw, ImageStat
from playwright.sync_api import Locator, Page, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "docs" / "design-references"
BASE_URL = os.environ.get("LIBLIB_BASE_URL", "http://localhost:3000")

TIMELINE_SCREENSHOT = (
    REFERENCE_DIR / "liblib-clone-batch36-director-timeline-1440-2026-08-26.png"
)
KEYFRAME_SCREENSHOT = (
    REFERENCE_DIR / "liblib-clone-batch36-director-keyframe-1440-2026-08-26.png"
)
PLAYBACK_SCREENSHOT = (
    REFERENCE_DIR / "liblib-clone-batch36-director-playback-1440-2026-08-26.png"
)
MOBILE_SCREENSHOT = (
    REFERENCE_DIR
    / "liblib-clone-batch36-director-timeline-mobile-390-2026-08-26.png"
)
CONTACT_SHEET = (
    REFERENCE_DIR
    / "liblib-clone-batch36-director-timeline-contact-sheet-2026-08-26.png"
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


def timeline_state(page: Page):
    return page.evaluate(
        """() => {
          const state = window.__director_store.getState();
          return {
            timeline: state.timeline,
            objects: state.objects,
            selectedObjectId: state.selectedObjectId,
          };
        }"""
    )


def object_by_id(state, object_id: str):
    return next(item for item in state["objects"] if item["id"] == object_id)


def track_by_object(state, object_id: str):
    return next(
        track
        for track in state["timeline"]["tracks"]
        if track["objectId"] == object_id
    )


def run_desktop(page: Page):
    errors = attach_errors(page)
    open_director(page)
    timeline = page.locator("[data-director-timeline]")
    timeline_box = box(timeline)
    assert timeline_box["x"] == 0
    assert timeline_box["y"] == 704
    assert timeline_box["width"] == 1440
    assert timeline_box["height"] == 196
    assert page.locator("[data-director-track-id]").count() == 2
    assert page.locator("[data-director-keyframe-id]").count() == 6
    assert_no_overflow(page)

    state = timeline_state(page)
    assert state["timeline"]["duration"] == 8
    assert state["timeline"]["currentTime"] == 0
    assert state["timeline"]["loop"] is True
    assert state["timeline"]["autoKeyframe"] is True
    assert object_by_id(state, "director-character-lead")["transform"][
        "position"
    ][0] == -1.25

    timeline_canvas = page.locator("[data-director-timeline-canvas]")
    canvas_box = box(timeline_canvas)
    first_marker = box(
        page.locator(
            '[data-director-keyframe-id="director-keyframe-character-0"]'
        )
    )
    last_marker = box(
        page.locator(
            '[data-director-keyframe-id="director-keyframe-character-8"]'
        )
    )
    assert first_marker["x"] >= canvas_box["x"]
    assert last_marker["x"] + last_marker["width"] <= (
        canvas_box["x"] + canvas_box["width"]
    )
    page.screenshot(path=str(TIMELINE_SCREENSHOT))

    ruler = page.locator("[data-director-timeline-ruler]")
    ruler_box = box(ruler)
    page.mouse.click(
        ruler_box["x"] + ruler_box["width"] * 0.25,
        ruler_box["y"] + ruler_box["height"] / 2,
    )
    state = timeline_state(page)
    assert abs(state["timeline"]["currentTime"] - 2) < 0.08
    character_x = object_by_id(
        state, "director-character-lead"
    )["transform"]["position"][0]
    assert abs(character_x - (-0.3)) < 0.04

    page.locator(
        '[data-director-keyframe-id="director-keyframe-character-4"]'
    ).click()
    state = timeline_state(page)
    assert state["timeline"]["currentTime"] == 4
    assert state["timeline"]["selectedKeyframeId"] == (
        "director-keyframe-character-4"
    )
    assert state["selectedObjectId"] == "director-character-lead"
    assert abs(
        object_by_id(state, "director-character-lead")["transform"]["position"][0]
        - 0.65
    ) < 0.001
    page.screenshot(path=str(KEYFRAME_SCREENSHOT))

    page.locator("[data-director-playback]").click()
    page.wait_for_timeout(360)
    state = timeline_state(page)
    assert state["timeline"]["isPlaying"] is True
    assert 4.2 < state["timeline"]["currentTime"] < 4.8
    assert (
        object_by_id(state, "director-character-lead")["transform"]["position"][0]
        < 0.65
    )
    page.screenshot(path=str(PLAYBACK_SCREENSHOT))
    page.get_by_role("button", name="暂停").click()

    page.evaluate(
        "() => window.__director_store.getState().setTimelineTime(2)"
    )
    page.get_by_role("button", name="下一关键帧").click()
    assert timeline_state(page)["timeline"]["currentTime"] == 4
    page.get_by_role("button", name="上一关键帧").click()
    assert timeline_state(page)["timeline"]["currentTime"] == 0

    loop_button = page.locator("[data-director-loop]")
    loop_button.click()
    assert loop_button.get_attribute("aria-pressed") == "false"
    page.evaluate(
        "() => window.__director_store.getState().setTimelineTime(7.9)"
    )
    page.locator("[data-director-playback]").click()
    page.wait_for_timeout(240)
    state = timeline_state(page)
    assert state["timeline"]["currentTime"] == 8
    assert state["timeline"]["isPlaying"] is False
    loop_button.click()
    assert loop_button.get_attribute("aria-pressed") == "true"

    width_before = box(timeline_canvas)["width"]
    page.locator("[data-director-timeline-zoom]").fill("2.5")
    width_after = box(timeline_canvas)["width"]
    assert width_after > width_before
    assert_no_overflow(page)

    page.evaluate(
        "() => window.__director_store.getState().setTimelineTime(2)"
    )
    page.locator('[data-director-object-id="director-prop-mug"]').click()
    add_track = page.locator("[data-director-add-track]")
    assert add_track.is_enabled()
    add_track.click()
    assert page.locator("[data-director-track-id]").count() == 3
    assert add_track.is_disabled()
    state = timeline_state(page)
    mug_track = track_by_object(state, "director-prop-mug")
    assert mug_track["kind"] == "transform"
    assert len(mug_track["keyframes"]) == 1

    page.locator("[data-director-add-keyframe]").click()
    state = timeline_state(page)
    assert len(track_by_object(state, "director-prop-mug")["keyframes"]) == 1

    page.evaluate(
        "() => window.__director_store.getState().setTimelineTime(3)"
    )
    mug_x_input = page.locator(
        '[data-director-transform-field="position"]'
        '[data-director-transform-axis="x"]'
    )
    mug_x_input.fill("1.25")
    state = timeline_state(page)
    mug_track = track_by_object(state, "director-prop-mug")
    assert len(mug_track["keyframes"]) == 2
    assert any(
        abs(keyframe["time"] - 3) < 0.001
        and abs(keyframe["value"]["position"][0] - 1.25) < 0.001
        for keyframe in mug_track["keyframes"]
    )
    assert state["timeline"]["selectedKeyframeId"] is not None
    page.locator("[data-director-delete-keyframe]").click()
    state = timeline_state(page)
    assert len(track_by_object(state, "director-prop-mug")["keyframes"]) == 1
    assert abs(
        object_by_id(state, "director-prop-mug")["transform"]["position"][0] - 0.25
    ) < 0.001

    page.get_by_role(
        "button", name="移除冷掉的咖啡 · 变换轨道"
    ).click()
    assert page.locator("[data-director-track-id]").count() == 2

    page.locator(
        '[data-director-keyframe-id="director-keyframe-camera-8"]'
    ).click()
    state = timeline_state(page)
    camera = object_by_id(state, "director-camera-main")
    assert camera["camera"]["fov"] == 52
    assert state["selectedObjectId"] == "director-camera-main"
    page.locator('[data-director-view-mode="camera"]').click()
    assert_nonblank_locator(
        page.locator('canvas[data-director-webgl-canvas="true"]'),
        "timeline sampled camera view",
    )

    keyframe_count = len(
        track_by_object(timeline_state(page), "director-camera-main")["keyframes"]
    )
    page.locator("[data-director-auto-keyframe]").click()
    page.evaluate(
        "() => window.__director_store.getState().setTimelineTime(6)"
    )
    page.locator("[data-director-camera-fov]").fill("60")
    state = timeline_state(page)
    assert len(track_by_object(state, "director-camera-main")["keyframes"]) == (
        keyframe_count
    )
    page.locator("[data-director-add-keyframe]").click()
    state = timeline_state(page)
    assert len(track_by_object(state, "director-camera-main")["keyframes"]) == (
        keyframe_count + 1
    )
    assert errors == [], json.dumps(errors, ensure_ascii=False, indent=2)


def run_mobile(page: Page):
    errors = attach_errors(page)
    open_director(page, force_dom_click=True)
    timeline = page.locator("[data-director-timeline]")
    timeline_box = box(timeline)
    assert timeline_box["x"] == 0
    assert timeline_box["y"] == 668
    assert timeline_box["width"] == 390
    assert timeline_box["height"] == 176
    controls_metrics = page.locator(
        "[data-director-timeline-controls]"
    ).evaluate(
        "(element) => ({ clientWidth: element.clientWidth, scrollWidth: element.scrollWidth })"
    )
    assert controls_metrics["scrollWidth"] > controls_metrics["clientWidth"]
    canvas_metrics = page.locator(
        "[data-director-timeline-canvas]"
    ).evaluate(
        "(element) => ({ clientWidth: element.clientWidth, scrollWidth: element.parentElement.scrollWidth })"
    )
    assert canvas_metrics["scrollWidth"] >= canvas_metrics["clientWidth"]
    assert_no_overflow(page)

    page.locator("[data-director-playback]").click()
    page.wait_for_timeout(260)
    state = timeline_state(page)
    assert state["timeline"]["isPlaying"] is True
    assert state["timeline"]["currentTime"] > 0.15
    page.get_by_role("button", name="暂停").click()

    page.get_by_role("button", name="打开场景对象").click()
    page.wait_for_timeout(240)
    assert (
        page.locator('aside[aria-label="场景对象"]').get_attribute(
            "data-director-mobile-panel-state"
        )
        == "open"
    )
    assert_no_overflow(page)
    page.screenshot(path=str(MOBILE_SCREENSHOT))
    assert errors == [], json.dumps(errors, ensure_ascii=False, indent=2)


def make_contact_sheet():
    items = [
        ("TIMELINE", TIMELINE_SCREENSHOT),
        ("KEYFRAME SAMPLE", KEYFRAME_SCREENSHOT),
        ("PLAYBACK", PLAYBACK_SCREENSHOT),
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
    math_source = (
        ROOT / "src/components/director/directorTimelineMath.ts"
    ).read_text()
    desk_source = (
        ROOT / "src/components/director/DirectorDesk.tsx"
    ).read_text()
    inspector_source = (
        ROOT / "src/components/director/DirectorInspector.tsx"
    ).read_text()
    viewport_source = (
        ROOT / "src/components/director/DirectorViewport.tsx"
    ).read_text()

    assert 'kind: "transform"' in store_source
    assert 'kind: "camera"' in store_source
    assert "sampleDirectorTimelineTrack" in math_source
    assert "data-director-timeline" in timeline_source
    assert "requestAnimationFrame" in timeline_source
    assert "data-director-keyframe-id" in timeline_source
    assert "<DirectorTimeline />" in desk_source
    assert "recordObjectKeyframe(selected.id)" in inspector_source
    assert "recordObjectKeyframe(object.id)" in viewport_source


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
    print("Batch 36 director timeline verification passed.")
