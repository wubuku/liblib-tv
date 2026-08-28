from io import BytesIO
from pathlib import Path
import json
import os

from PIL import Image, ImageDraw, ImageStat
from playwright.sync_api import Locator, Page, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "docs" / "design-references"
BASE_URL = os.environ.get("LIBLIB_BASE_URL", "http://localhost:4317")

WAITING_SCREENSHOT = (
    REFERENCE_DIR
    / "liblib-clone-batch41-director-phone-waiting-1440-2026-08-26.png"
)
CONTROLS_SCREENSHOT = (
    REFERENCE_DIR
    / "liblib-clone-batch41-director-phone-controls-1440-2026-08-26.png"
)
RECORDING_SCREENSHOT = (
    REFERENCE_DIR
    / "liblib-clone-batch41-director-phone-recording-1440-2026-08-26.png"
)
IMPORTED_SCREENSHOT = (
    REFERENCE_DIR
    / "liblib-clone-batch41-director-phone-imported-1440-2026-08-26.png"
)
MOBILE_SCREENSHOT = (
    REFERENCE_DIR
    / "liblib-clone-batch41-director-phone-mobile-390-2026-08-26.png"
)
CONTACT_SHEET = (
    REFERENCE_DIR
    / "liblib-clone-batch41-director-phone-contact-sheet-2026-08-26.png"
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
    page.goto(f"{BASE_URL}/?batch41=1", wait_until="networkidle")
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
    page.wait_for_timeout(500)


def wait_for_phone_status(page: Page, status: str):
    page.wait_for_function(
        """(status) =>
          document.querySelector("[data-director-phone-vcam-panel]")
            ?.getAttribute("data-director-phone-vcam-status") === status
        """,
        arg=status,
    )


def camera_state(page: Page):
    return page.evaluate(
        """() => {
          const state = window.__director_store.getState();
          const camera = state.objects.find(
            (object) => object.id === state.activeCameraId,
          );
          return camera
            ? {
                id: camera.id,
                position: [...camera.transform.position],
                target: camera.camera ? [...camera.camera.target] : null,
              }
            : null;
        }"""
    )


def move_pose_pad(page: Page, x_ratio: float, y_ratio: float):
    pad = page.locator("[data-director-phone-vcam-pose-pad]")
    pad_box = box(pad)
    x = pad_box["x"] + pad_box["width"] * x_ratio
    y = pad_box["y"] + pad_box["height"] * y_ratio
    page.mouse.move(x, y)
    page.mouse.down()
    page.mouse.move(x + 1, y + 1)
    page.mouse.up()
    page.wait_for_timeout(80)


def run_desktop(page: Page):
    errors = attach_errors(page)
    open_director(page)
    webgl = page.locator('canvas[data-director-webgl-canvas="true"]')
    assert_nonblank_locator(webgl, "Batch 41 director WebGL canvas")

    trigger = page.locator("[data-director-phone-vcam-trigger]")
    trigger.click()
    panel = page.locator("[data-director-phone-vcam-panel]")
    panel.wait_for(state="visible")
    wait_for_phone_status(page, "waiting")
    assert panel.get_by_text("虚拟相机", exact=True).is_visible()
    assert panel.get_by_text("本机预演", exact=True).count() >= 1
    assert panel.get_by_text(
        "请保持手机和电脑在同一 wifi 下，用手机扫码连接",
        exact=True,
    ).is_visible()
    assert panel.get_by_text(
        "如果手机提示证书风险，请在同一 Wi-Fi 下继续访问并信任本机证书。",
        exact=True,
    ).is_visible()
    assert (
        panel.get_attribute("data-director-phone-vcam-mode")
        == "local-preview"
    )
    page.screenshot(path=str(WAITING_SCREENSHOT))

    page.locator("[data-director-phone-vcam-connect]").click()
    wait_for_phone_status(page, "local-ready")
    connected = page.evaluate(
        """() => {
          const state = window.__director_store.getState();
          return {
            viewMode: state.viewMode,
            selectedObjectId: state.selectedObjectId,
            activeCameraId: state.activeCameraId,
            phone: state.phoneVcam,
          };
        }"""
    )
    assert connected["viewMode"] == "camera"
    assert connected["selectedObjectId"] == connected["activeCameraId"]
    assert connected["phone"]["baselineCamera"] is not None

    initial_camera = camera_state(page)
    assert initial_camera is not None
    move_pose_pad(page, 0.86, 0.17)
    moved_camera = camera_state(page)
    assert moved_camera is not None
    assert moved_camera["position"] != initial_camera["position"]
    pose = page.locator("[data-director-phone-vcam-pose]")
    assert float(pose.get_attribute("data-yaw") or "0") > 20
    assert float(pose.get_attribute("data-pitch") or "0") > 10

    stability = page.locator("[data-director-phone-vcam-stability]")
    stability.fill("88")
    assert page.evaluate(
        "window.__director_store.getState().phoneVcam.stability"
    ) == 88

    page.locator("[data-director-phone-vcam-keep-level]").click()
    assert page.evaluate(
        "window.__director_store.getState().phoneVcam.keepLevel"
    ) is False
    hold = page.locator("[data-director-phone-vcam-hold]")
    hold.click()
    held_camera = camera_state(page)
    move_pose_pad(page, 0.18, 0.82)
    assert camera_state(page)["position"] == held_camera["position"]
    assert hold.get_attribute("aria-pressed") == "true"
    hold.click()

    elevation_before = page.evaluate(
        "window.__director_store.getState().phoneVcam.elevation"
    )
    page.locator('[data-director-phone-vcam-elevate="up"]').click()
    elevation_after = page.evaluate(
        "window.__director_store.getState().phoneVcam.elevation"
    )
    assert elevation_after > elevation_before
    page.screenshot(path=str(CONTROLS_SCREENSHOT))

    initial_counts = page.evaluate(
        """() => {
          const state = window.__director_store.getState();
          return {
            cameras: state.objects.filter((object) => object.kind === "camera").length,
            tracks: state.timeline.tracks.length,
          };
        }"""
    )
    page.evaluate("window.__director_store.getState().setTimelineTime(8)")
    page.locator("[data-director-phone-vcam-record]").click()
    assert page.locator("[data-director-phone-vcam-error]").get_by_text(
        "当前播放头后没有可录制时长",
        exact=True,
    ).is_visible()
    assert (
        panel.get_attribute("data-director-phone-vcam-status")
        == "local-ready"
    )
    guarded_counts = page.evaluate(
        """() => {
          const state = window.__director_store.getState();
          return {
            cameras: state.objects.filter((object) => object.kind === "camera").length,
            tracks: state.timeline.tracks.length,
          };
        }"""
    )
    assert guarded_counts == initial_counts

    page.evaluate("window.__director_store.getState().setTimelineTime(2)")
    page.locator("[data-director-phone-vcam-calibrate]").click()
    source_camera_id = page.evaluate(
        "window.__director_store.getState().activeCameraId"
    )
    source_baseline = page.evaluate(
        "window.__director_store.getState().phoneVcam.baselineCamera"
    )
    page.locator("[data-director-phone-vcam-record]").click()
    wait_for_phone_status(page, "recording")
    assert page.locator("[data-close-director]").is_disabled()
    assert page.locator("[data-director-export-trigger]").is_disabled()
    assert page.locator("[data-director-capture]").is_disabled()
    assert page.locator(
        '[data-director-capture-status="phone-recording"]'
    ).is_visible()
    page.wait_for_timeout(160)
    move_pose_pad(page, 0.12, 0.28)
    page.wait_for_timeout(260)
    assert int(
        page.locator(
            "[data-director-phone-vcam-sample-count]"
        ).get_attribute("data-director-phone-vcam-sample-count")
        or "0"
    ) >= 3
    page.screenshot(path=str(RECORDING_SCREENSHOT))
    page.locator("[data-director-phone-vcam-record]").click()
    wait_for_phone_status(page, "imported")

    imported = page.evaluate(
        """(sourceCameraId) => {
          const state = window.__director_store.getState();
          const camera = state.objects.find(
            (object) => object.id === state.phoneVcam.importedCameraId,
          );
          const source = state.objects.find(
            (object) => object.id === sourceCameraId,
          );
          const track = state.timeline.tracks.find(
            (item) => item.id === state.phoneVcam.importedTrackId,
          );
          return {
            phone: state.phoneVcam,
            camera,
            source,
            track,
            activeCameraId: state.activeCameraId,
            selectedObjectId: state.selectedObjectId,
            selectedTrackId: state.timeline.selectedTrackId,
            selectedKeyframeId: state.timeline.selectedKeyframeId,
            currentTime: state.timeline.currentTime,
            cameraCount: state.objects.filter(
              (object) => object.kind === "camera",
            ).length,
            trackCount: state.timeline.tracks.length,
          };
        }""",
        source_camera_id,
    )
    assert imported["phone"]["error"] is None
    assert imported["phone"]["sampleCount"] >= 3
    assert imported["camera"]["name"] == "手机运镜 1"
    assert imported["track"]["label"] == "手机运镜 1"
    assert imported["track"]["kind"] == "camera"
    assert imported["track"]["objectId"] == imported["camera"]["id"]
    assert len(imported["track"]["keyframes"]) >= 3
    first_keyframe = imported["track"]["keyframes"][0]
    last_keyframe = imported["track"]["keyframes"][-1]
    assert abs(first_keyframe["time"] - 2) < 0.03
    assert last_keyframe["time"] > first_keyframe["time"] + 0.25
    assert last_keyframe["time"] <= 8
    assert (
        first_keyframe["value"]["transform"]["position"]
        != last_keyframe["value"]["transform"]["position"]
    )
    assert imported["source"]["transform"] == source_baseline["transform"]
    assert imported["source"]["camera"]["target"] == source_baseline["target"]
    assert imported["activeCameraId"] == imported["camera"]["id"]
    assert imported["selectedObjectId"] == imported["camera"]["id"]
    assert imported["selectedTrackId"] == imported["track"]["id"]
    assert (
        imported["selectedKeyframeId"]
        == imported["track"]["keyframes"][-1]["id"]
    )
    assert abs(imported["currentTime"] - last_keyframe["time"]) < 0.001
    assert imported["cameraCount"] == initial_counts["cameras"] + 1
    assert imported["trackCount"] == initial_counts["tracks"] + 1
    take = page.locator("[data-director-phone-vcam-take]")
    assert take.get_attribute("data-camera-id") == imported["camera"]["id"]
    assert take.get_attribute("data-track-id") == imported["track"]["id"]
    page.screenshot(path=str(IMPORTED_SCREENSHOT))

    assert_no_overflow(page)
    assert errors == [], json.dumps(errors, ensure_ascii=False, indent=2)


def run_mobile(page: Page):
    errors = attach_errors(page)
    open_director(page, force_dom_click=True)
    toolbar = page.locator("[data-director-viewport-toolbar]")
    toolbar_box = box(toolbar)
    assert toolbar_box["x"] >= 12
    assert toolbar_box["x"] + toolbar_box["width"] <= 378

    page.locator("[data-director-phone-vcam-trigger]").click()
    wait_for_phone_status(page, "waiting")
    page.locator("[data-director-phone-vcam-connect]").click()
    wait_for_phone_status(page, "local-ready")
    panel = page.locator("[data-director-phone-vcam-panel]")
    panel_box = box(panel)
    timeline_box = box(page.locator("[data-director-timeline]"))
    assert panel_box["x"] >= 12
    assert panel_box["x"] + panel_box["width"] <= 378
    assert panel_box["y"] >= 48
    assert panel_box["y"] + panel_box["height"] <= timeline_box["y"]
    assert page.locator("[data-director-phone-vcam-pose-pad]").is_visible()
    assert page.locator("[data-director-phone-vcam-stability]").is_visible()
    assert page.locator("[data-director-phone-vcam-record]").is_visible()
    move_pose_pad(page, 0.72, 0.26)
    assert_no_overflow(page)
    page.screenshot(path=str(MOBILE_SCREENSHOT))

    page.get_by_role("button", name="关闭虚拟相机").click()
    page.locator("[data-close-director]").click()
    assert page.locator("[data-director-workspace]").count() == 0
    assert errors == [], json.dumps(errors, ensure_ascii=False, indent=2)


def make_contact_sheet():
    items = [
        ("WAITING / LOCAL BOUNDARY", WAITING_SCREENSHOT),
        ("CONNECTED CONTROLS", CONTROLS_SCREENSHOT),
        ("RECORDING", RECORDING_SCREENSHOT),
        ("IMPORTED CAMERA TRACK", IMPORTED_SCREENSHOT),
        ("MOBILE CONTROLS", MOBILE_SCREENSHOT),
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
    panel_source = (
        ROOT / "src/components/director/DirectorPhoneVcamPanel.tsx"
    ).read_text()
    math_source = (
        ROOT / "src/components/director/directorPhoneVcamMath.ts"
    ).read_text()
    viewport_source = (
        ROOT / "src/components/director/DirectorViewport.tsx"
    ).read_text()
    desk_source = (
        ROOT / "src/components/director/DirectorDesk.tsx"
    ).read_text()
    store_source = (ROOT / "src/store/directorStore.ts").read_text()

    assert "data-director-phone-vcam-panel" in panel_source
    assert "data-director-phone-vcam-mode=\"local-preview\"" in panel_source
    assert "deviceorientation" in panel_source
    assert "启动本机预演" in panel_source
    assert "当前播放头后没有可录制时长" in store_source
    assert "手机运镜已导入机位时间轴" in panel_source
    assert "mapDirectorPhonePoseToCamera" in math_source
    assert "normalizeDirectorPhoneOrientation" in math_source
    assert "importPhoneVcamTake" in store_source
    assert "data-director-phone-vcam-trigger" in viewport_source
    assert "phone-recording" in desk_source


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
    print("Batch 41 director phone virtual-camera verification passed.")
