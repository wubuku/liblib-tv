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

PENCIL_SCREENSHOT = (
    REFERENCE_DIR
    / "liblib-clone-batch38-director-pencil-path-1440-2026-08-26.png"
)
PEN_DRAFT_SCREENSHOT = (
    REFERENCE_DIR
    / "liblib-clone-batch38-director-pen-draft-1440-2026-08-26.png"
)
ANCHOR_SCREENSHOT = (
    REFERENCE_DIR
    / "liblib-clone-batch38-director-anchor-editor-1440-2026-08-26.png"
)
PLAYBACK_SCREENSHOT = (
    REFERENCE_DIR
    / "liblib-clone-batch38-director-path-playback-1440-2026-08-26.png"
)
MOBILE_SCREENSHOT = (
    REFERENCE_DIR
    / "liblib-clone-batch38-director-path-mobile-390-2026-08-26.png"
)
CONTACT_SHEET = (
    REFERENCE_DIR
    / "liblib-clone-batch38-director-path-authoring-contact-sheet-2026-08-26.png"
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
    page.goto(f"{BASE_URL}/?batch38=1", wait_until="networkidle")
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


def start_draw_tool(page: Page, tool: str):
    page.locator("[data-director-create-motion-path]").click()
    page.locator(f'[data-director-motion-path-draw-tool="{tool}"]').click()
    drawing = page.locator("[data-director-path-drawing]")
    assert drawing.is_visible()
    assert drawing.get_attribute("data-director-path-drawing-tool") == tool


def draw_pencil(page: Page):
    canvas_box = box(page.locator('canvas[data-director-webgl-canvas="true"]'))
    start_x = canvas_box["x"] + canvas_box["width"] * 0.37
    start_y = canvas_box["y"] + canvas_box["height"] * 0.51
    page.mouse.move(start_x, start_y)
    page.mouse.down()
    for index in range(1, 9):
        page.mouse.move(
            start_x + index * canvas_box["width"] * 0.026,
            start_y + math.sin(index * 0.82) * canvas_box["height"] * 0.055,
            steps=2,
        )
    page.mouse.up()
    page.wait_for_timeout(160)


def draw_pen(page: Page):
    canvas_box = box(page.locator('canvas[data-director-webgl-canvas="true"]'))
    gestures = [
        (0.38, 0.51, 0.055, -0.045),
        (0.50, 0.43, 0, 0),
        (0.63, 0.52, -0.05, 0.065),
    ]
    for relative_x, relative_y, delta_x, delta_y in gestures:
        x = canvas_box["x"] + canvas_box["width"] * relative_x
        y = canvas_box["y"] + canvas_box["height"] * relative_y
        page.mouse.move(x, y)
        page.mouse.down()
        if delta_x or delta_y:
            page.mouse.move(
                x + canvas_box["width"] * delta_x,
                y + canvas_box["height"] * delta_y,
                steps=5,
            )
        page.mouse.up()


def run_desktop(page: Page):
    errors = attach_errors(page)
    open_director(page)
    canvas = page.locator('canvas[data-director-webgl-canvas="true"]')
    assert_nonblank_locator(canvas, "Batch 38 director viewport")
    assert_no_overflow(page)

    page.locator("[data-director-create-motion-path]").click()
    menu = page.locator("[data-director-motion-path-menu]")
    assert menu.is_visible()
    assert menu.locator(
        "[data-director-motion-path-draw-tool]"
    ).all_text_contents() == ["铅笔路径", "钢笔路径"]
    assert menu.locator(
        "[data-director-motion-path-preset]"
    ).all_text_contents() == ["直线路径", "圆环路径", "矩形路径"]
    page.locator('[data-director-motion-path-draw-tool="pencil"]').click()

    assert page.locator("[data-director-capture]").is_disabled()
    draw_pencil(page)
    state = director_state(page)
    path = selected_path(state)
    assert path["preset"] == "pencil"
    assert len(state["timeline"]["motionPaths"]) == 1
    assert len(path["anchors"]) >= 8
    assert len(path["anchors"]) == len(path["points"])
    assert state["selectedObjectId"] == "director-character-lead"
    assert state["timeline"]["motionPathDraft"] is None
    assert state["timeline"]["selectedMotionPathAnchorId"] == path["anchors"][0]["id"]
    assert page.locator("[data-director-motion-path-inspector]").count() == 1
    assert page.locator("[data-director-motion-path-anchor-id]").count() == len(
        path["anchors"]
    )
    page.screenshot(path=str(PENCIL_SCREENSHOT))

    first_anchor_count = len(path["anchors"])
    first_point_count = len(path["points"])
    page.locator(
        '[data-director-path-anchor-type-option="symmetric"]'
    ).click()
    state = director_state(page)
    path = selected_path(state)
    anchor = selected_anchor(state)
    assert anchor["type"] == "symmetric"
    assert any(abs(value) > 0.0001 for value in anchor["handleOut"])
    assert all(
        abs(anchor["handleIn"][index] + anchor["handleOut"][index]) < 0.000001
        for index in range(3)
    )
    assert len(path["points"]) > first_point_count
    assert page.locator(
        '[data-director-motion-path-handle="in"]'
    ).count() == 1

    page.locator("[data-director-path-name]").fill("手绘推镜路线")
    assert selected_path(director_state(page))["name"] == "手绘推镜路线"
    before_position = object_by_id(
        director_state(page), "director-character-lead"
    )["transform"]["position"]
    position_x = page.locator(
        '[data-director-path-anchor-position="x"]'
    )
    position_x.fill(str(anchor["position"][0] + 0.55))
    state = director_state(page)
    moved_position = object_by_id(
        state, "director-character-lead"
    )["transform"]["position"]
    assert abs(moved_position[0] - before_position[0]) > 0.4

    page.locator(
        '[data-director-path-anchor-type-option="asymmetric"]'
    ).click()
    before_anchor = selected_anchor(director_state(page))
    before_points = selected_path(director_state(page))["points"]
    output_x = page.locator(
        '[data-director-path-anchor-handle="out"]'
        '[data-director-path-anchor-handle-axis="x"]'
    )
    output_x.fill(str(before_anchor["handleOut"][0] + 0.7))
    state = director_state(page)
    after_anchor = selected_anchor(state)
    assert after_anchor["type"] == "asymmetric"
    assert after_anchor["handleIn"] == before_anchor["handleIn"]
    assert after_anchor["handleOut"] != before_anchor["handleOut"]
    assert selected_path(state)["points"] != before_points
    page.screenshot(path=str(ANCHOR_SCREENSHOT))

    page.locator("[data-director-insert-path-anchor]").click()
    state = director_state(page)
    assert len(selected_path(state)["anchors"]) == first_anchor_count + 1
    page.locator("[data-director-toggle-path-closed]").click()
    assert selected_path(director_state(page))["closed"] is True
    page.locator("[data-director-delete-path-anchor]").click()
    state = director_state(page)
    assert len(selected_path(state)["anchors"]) == first_anchor_count
    assert selected_path(state)["closed"] is True

    preserved_path_id = state["timeline"]["selectedMotionPathId"]
    preserved_path = selected_path(state)
    start_draw_tool(page, "pen")
    canvas_box = box(canvas)
    page.mouse.click(
        canvas_box["x"] + canvas_box["width"] * 0.45,
        canvas_box["y"] + canvas_box["height"] * 0.49,
    )
    page.keyboard.press("Escape")
    state = director_state(page)
    assert page.locator("[data-director-workspace]").is_visible()
    assert state["timeline"]["motionPathDraft"] is None
    assert state["timeline"]["selectedMotionPathId"] == preserved_path_id
    assert selected_path(state) == preserved_path

    start_draw_tool(page, "pen")
    draw_pen(page)
    draft = director_state(page)["timeline"]["motionPathDraft"]
    assert draft is not None
    assert len(draft["anchors"]) == 3
    assert [anchor["type"] for anchor in draft["anchors"]] == [
        "symmetric",
        "vertex",
        "symmetric",
    ]
    assert director_state(page)["selectedObjectId"] == "director-character-lead"
    page.screenshot(path=str(PEN_DRAFT_SCREENSHOT))
    page.locator("[data-director-path-drawing-complete]").click()
    page.wait_for_timeout(120)

    state = director_state(page)
    path = selected_path(state)
    assert path["preset"] == "pen"
    assert len(state["timeline"]["motionPaths"]) == 1
    assert len(path["anchors"]) == 3
    assert len(path["points"]) == 25
    assert state["selectedObjectId"] == "director-character-lead"
    assert page.locator("[data-director-motion-path-inspector]").count() == 1
    for anchor in [path["anchors"][0], path["anchors"][2]]:
        assert anchor["type"] == "symmetric"
        assert all(
            abs(anchor["handleIn"][index] + anchor["handleOut"][index])
            < 0.000001
            for index in range(3)
        )

    page.evaluate("() => window.__director_store.getState().setTimelineTime(0)")
    start_position = object_by_id(
        director_state(page), "director-character-lead"
    )["transform"]["position"]
    page.locator("[data-director-playback]").click()
    page.wait_for_timeout(360)
    state = director_state(page)
    playing_position = object_by_id(
        state, "director-character-lead"
    )["transform"]["position"]
    assert state["timeline"]["isPlaying"] is True
    assert state["timeline"]["currentTime"] > 0.2
    assert playing_position != start_position
    page.screenshot(path=str(PLAYBACK_SCREENSHOT))
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
    timeline = page.locator("[data-director-timeline]")
    assert box(timeline)["height"] == 176
    canvas = page.locator('canvas[data-director-webgl-canvas="true"]')

    start_draw_tool(page, "pencil")
    draw_pencil(page)
    state = director_state(page)
    path = selected_path(state)
    assert path["preset"] == "pencil"
    assert len(path["anchors"]) >= 2

    page.get_by_role("button", name="打开属性面板").click()
    page.wait_for_timeout(260)
    inspector_panel = page.locator(
        '[aria-label="属性"][data-director-mobile-panel-state="open"]'
    )
    assert inspector_panel.is_visible()
    inspector = page.locator("[data-director-motion-path-inspector]")
    assert inspector.count() == 1
    inspector.evaluate("(element) => element.scrollIntoView({block: 'end'})")
    page.wait_for_timeout(120)
    panel_box = box(inspector_panel)
    assert panel_box["x"] >= 100
    assert panel_box["x"] + panel_box["width"] <= 390.5
    assert_no_overflow(page)
    assert_nonblank_locator(canvas, "Batch 38 mobile director viewport")
    page.screenshot(path=str(MOBILE_SCREENSHOT))
    assert errors == [], json.dumps(errors, ensure_ascii=False, indent=2)


def make_contact_sheet():
    items = [
        ("PENCIL PATH", PENCIL_SCREENSHOT),
        ("PEN DRAFT", PEN_DRAFT_SCREENSHOT),
        ("ANCHOR EDITOR", ANCHOR_SCREENSHOT),
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
    inspector_source = (
        ROOT / "src/components/director/DirectorInspector.tsx"
    ).read_text()
    viewport_source = (
        ROOT / "src/components/director/DirectorViewport.tsx"
    ).read_text()
    math_source = (
        ROOT / "src/components/director/directorMotionMath.ts"
    ).read_text()

    assert "DirectorMotionPathAnchorType" in store_source
    assert "motionPathDraft" in store_source
    assert "buildDirectorMotionPathPoints" in math_source
    assert "setDirectorMotionPathAnchorType" in math_source
    assert "data-director-motion-path-draw-tool" in timeline_source
    assert "data-director-path-anchor-type-option" in inspector_source
    assert "DirectorMotionPathDrawingSurface" in viewport_source
    assert "motionPathDraft === null" in viewport_source


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
    print("Batch 38 director path authoring verification passed.")
