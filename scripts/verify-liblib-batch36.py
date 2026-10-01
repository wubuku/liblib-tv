from io import BytesIO
from pathlib import Path
import json
import os

from PIL import Image, ImageDraw, ImageStat
from playwright.sync_api import Locator, Page, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "docs" / "design-references"
BASE_URL = os.environ.get("LIBLIB_BASE_URL", "http://localhost:4317")

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
    # Batch 572 后：全新上下文会显示 1/5 引导气泡（遮挡传输控制）——
    # 挂载前写入持久化 dismiss 标记（移动端气泡晚挂载，点击 skip 会落空）
    page.evaluate(
        "() => window.localStorage.setItem("
        "'director-timeline-coach-dismissed', '1')"
    )
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
    # Batch 592: 源站实测时间轴展开高 182px（此前 clone 为 196px）。时间轴
    # 贴底对齐，故高度减 14px 后 y 由 704 变为 718（900 - 182）。
    assert timeline_box["y"] == 718
    assert timeline_box["width"] == 1440
    assert timeline_box["height"] == 182
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
    # Batch 593: 上一/下一关键帧 从工具条搬进了**每条轨道行**（源站本就在轨道
    # 行），所以行数 > 1 时按 role+name 会命中多个；这里按选中轨道行收敛。
    seek_row = page.locator(
        '[data-director-track-row="'
        + timeline_state(page)["timeline"]["selectedTrackId"]
        + '"]'
    )
    seek_row.get_by_role("button", name="下一关键帧").click()
    assert timeline_state(page)["timeline"]["currentTime"] == 4
    seek_row.get_by_role("button", name="上一关键帧").click()
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
    # Batch 594: 源站 `时间轴缩放` 是 min=0 max=100（无 step），不再是
    # 0.75-2.5 step 0.25，所以端点值随之改成 100。
    page.locator("[data-director-timeline-zoom]").fill("100")
    width_after = box(timeline_canvas)["width"]
    assert width_after > width_before
    assert_no_overflow(page)

    page.evaluate(
        "() => window.__director_store.getState().setTimelineTime(2)"
    )
    # Batch 573 source-aligned migration: 源站 onboarding 仅角色/摄像机
    # 可新建轨道——add-track 流改用角色对象（角色轨道 fixture 恒有，
    # 按钮点击为 NOOP；关键帧流走角色轨道的 添加/删除关键帧 按钮）。
    page.locator(
        '[data-director-object-id="director-character-lead"]'
    ).click()
    add_track = page.locator("[data-director-add-track]").first
    assert add_track.is_enabled()
    add_track.click()
    state = timeline_state(page)
    lead_track = track_by_object(state, "director-character-lead")
    keyframes_before = len(lead_track["keyframes"])

    page.locator("[data-director-add-keyframe]").click()
    state = timeline_state(page)
    assert (
        len(track_by_object(state, "director-character-lead")["keyframes"])
        == keyframes_before + 1
    )

    page.evaluate(
        "() => window.__director_store.getState().setTimelineTime(3)"
    )
    lead_x_input = page.locator(
        '[data-director-transform-field="position"]'
        '[data-director-transform-axis="x"]'
    )
    x_before_fill = object_by_id(
        state, "director-character-lead"
    )["transform"]["position"][0]
    lead_x_input.fill("1.25")
    state = timeline_state(page)
    lead_track = track_by_object(state, "director-character-lead")
    assert len(lead_track["keyframes"]) == keyframes_before + 2
    assert any(
        abs(keyframe["time"] - 3) < 0.001
        and abs(keyframe["value"]["position"][0] - 1.25) < 0.001
        for keyframe in lead_track["keyframes"]
    )
    assert state["timeline"]["selectedKeyframeId"] is not None
    page.locator("[data-director-delete-keyframe]").click()
    state = timeline_state(page)
    assert (
        len(track_by_object(state, "director-character-lead")["keyframes"])
        == keyframes_before + 1
    )
    # 删除 t=3 关键帧后位置回退（不再为 1.25；具体回退值取决于剩余
    # 关键帧插值，此处不假设）
    assert (
        object_by_id(state, "director-character-lead")["transform"]["position"][0]
        != 1.25
    )

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
    # 已知瞬态（batch 553/558/563 留痕）：TransformControls attach 告警
    real_errors = [
        error for error in errors if "TransformControls" not in error
    ]
    assert real_errors == [], json.dumps(
        real_errors, ensure_ascii=False, indent=2
    )


def run_mobile(page: Page):
    errors = attach_errors(page)
    open_director(page, force_dom_click=True)
    timeline = page.locator("[data-director-timeline]")
    timeline_box = box(timeline)
    assert timeline_box["x"] == 0
    assert timeline_box["y"] == 668
    assert timeline_box["width"] == 390
    assert timeline_box["height"] == 176
    # Batch 618 迁移：横向滚动的宿主从 header 本身下沉到内层
    # `[data-director-timeline-controls-scroll]`。header 带着 `pr-[260px]`
    # 给右格预留，而 padding-right 属于滚动溢出区——内容溢出后会画进预留区、
    # 被不透明右格压住（390 下四枚控件因此点不动）。裁切线必须落在 content
    # box，滚动宿主就得是 content box 本身。合同语义（「左格在窄屏横向滚动」）
    # 不变，只换宿主。
    controls_metrics = page.locator(
        "[data-director-timeline-controls-scroll]"
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
    # 已知瞬态（batch 553/558/563 留痕）：TransformControls attach 告警
    real_errors = [
        error for error in errors if "TransformControls" not in error
    ]
    assert real_errors == [], json.dumps(
        real_errors, ensure_ascii=False, indent=2
    )


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
    # Batch 596 gave the call site a `trailing` slot (the source's 导出视频到画布
    # button lives in the timeline strip's right cell, not the top bar), so the
    # literal self-closing form is gone. Assert the mount itself instead.
    assert "<DirectorTimeline" in desk_source
    assert 'from "@/components/director/DirectorTimeline"' in desk_source
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
