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

SETTINGS_SCREENSHOT = (
    REFERENCE_DIR
    / "liblib-clone-batch40-director-export-settings-1440-2026-08-26.png"
)
EXPORTING_SCREENSHOT = (
    REFERENCE_DIR
    / "liblib-clone-batch40-director-exporting-1440-2026-08-26.png"
)
SUCCESS_SCREENSHOT = (
    REFERENCE_DIR
    / "liblib-clone-batch40-director-export-success-1440-2026-08-26.png"
)
GRAPH_SCREENSHOT = (
    REFERENCE_DIR
    / "liblib-clone-batch40-director-video-return-1440-2026-08-26.png"
)
MOBILE_SCREENSHOT = (
    REFERENCE_DIR
    / "liblib-clone-batch40-director-export-mobile-390-2026-08-26.png"
)
CONTACT_SHEET = (
    REFERENCE_DIR
    / "liblib-clone-batch40-director-animation-export-contact-sheet-2026-08-26.png"
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
    page.goto(f"{BASE_URL}/?batch40=1", wait_until="networkidle")
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


def decode_data_url(data_url: str) -> Image.Image:
    return Image.open(BytesIO(b64decode(data_url.split(",", 1)[1]))).convert(
        "RGB"
    )


def inspect_video(page: Page):
    return page.locator("[data-director-animation-export]").evaluate(
        """async (video) => {
          if (video.readyState < 1) {
            await new Promise((resolve, reject) => {
              const timeout = setTimeout(
                () => reject(new Error("metadata timeout")),
                10000,
              );
              video.addEventListener(
                "loadedmetadata",
                () => {
                  clearTimeout(timeout);
                  resolve();
                },
                { once: true },
              );
              video.addEventListener(
                "error",
                () => {
                  clearTimeout(timeout);
                  reject(new Error("video decode failed"));
                },
                { once: true },
              );
            });
          }

          const seek = (time) =>
            new Promise((resolve, reject) => {
              const timeout = setTimeout(
                () => reject(new Error("seek timeout")),
                10000,
              );
              video.addEventListener(
                "seeked",
                () => {
                  clearTimeout(timeout);
                  resolve();
                },
                { once: true },
              );
              video.currentTime = time;
            });
          const sample = () => {
            const canvas = document.createElement("canvas");
            canvas.width = 90;
            canvas.height = 160;
            const context = canvas.getContext("2d");
            if (!context) throw new Error("sample context unavailable");
            context.drawImage(video, 0, 0, canvas.width, canvas.height);
            return context.getImageData(
              0,
              0,
              canvas.width,
              canvas.height,
            ).data;
          };

          await seek(Math.min(0.08, video.duration / 4));
          const first = sample();
          await seek(Math.min(video.duration * 0.82, video.duration - 0.04));
          const later = sample();
          let difference = 0;
          for (let index = 0; index < first.length; index += 16) {
            difference += Math.abs(first[index] - later[index]);
            difference += Math.abs(first[index + 1] - later[index + 1]);
            difference += Math.abs(first[index + 2] - later[index + 2]);
          }

          const blob = await fetch(video.src).then((response) =>
            response.blob(),
          );
          video.currentTime = 0;
          await video.play();
          await new Promise((resolve) => setTimeout(resolve, 180));
          const playbackTime = video.currentTime;
          video.pause();
          return {
            blobSize: blob.size,
            blobType: blob.type,
            duration: video.duration,
            videoWidth: video.videoWidth,
            videoHeight: video.videoHeight,
            playbackTime,
            frameDifference: difference,
            poster: video.poster,
          };
        }"""
    )


def run_desktop(page: Page):
    errors = attach_errors(page)
    open_director(page)
    initial_nodes = page.locator(".react-flow__node").count()
    initial_edges = page.locator(".react-flow__edge").count()
    workspace = page.locator("[data-director-workspace]")
    source_id = workspace.get_attribute("data-director-source-node-id")
    assert source_id
    canvas = page.locator('canvas[data-director-webgl-canvas="true"]')
    assert_nonblank_locator(canvas, "Batch 40 director WebGL canvas")

    page.evaluate("() => window.__director_store.getState().setTimelineTime(2)")
    page.locator("[data-director-export-trigger]").click()
    panel = page.locator("[data-director-export-panel]")
    panel.wait_for(state="visible")
    assert panel.get_attribute("data-director-export-status") == "idle"
    assert panel.get_by_text("导出设置", exact=True).is_visible()
    assert panel.get_by_text("时长", exact=True).is_visible()
    assert panel.get_by_text("比例", exact=True).is_visible()
    assert page.locator("[data-director-export-aspect]").count() == 3

    duration = page.locator("[data-director-export-duration]")
    duration.fill("99")
    assert float(duration.input_value()) == 8
    duration.fill("0")
    assert float(duration.input_value()) == 1
    duration.fill("1")
    page.locator('[data-director-export-aspect="9:16"]').click()
    frame = page.locator("[data-director-aspect-frame]")
    frame_box = box(frame)
    assert abs(frame_box["width"] / frame_box["height"] - 9 / 16) < 0.02
    assert_no_overflow(page)
    page.screenshot(path=str(SETTINGS_SCREENSHOT))

    page.locator("[data-director-export-submit]").click()
    assert panel.get_attribute("data-director-export-status") == "exporting"
    assert page.locator("[data-close-director]").is_disabled()
    page.wait_for_function(
        """() => {
          const element = document.querySelector(
            "[data-director-export-progress]",
          );
          const value = Number(
            element?.getAttribute("data-director-export-progress"),
          );
          return value > 5 && value < 100;
        }""",
        timeout=10000,
    )
    page.screenshot(path=str(EXPORTING_SCREENSHOT))
    page.locator(
        '[data-director-export-panel][data-director-export-status="success"]'
    ).wait_for(state="visible", timeout=20000)
    assert (
        page.locator("[data-director-export-progress]").get_attribute(
            "data-director-export-progress"
        )
        == "100"
    )
    page.wait_for_timeout(100)
    state = page.evaluate("() => window.__director_store.getState()")
    assert abs(state["timeline"]["currentTime"] - 2) < 0.02
    assert state["timeline"]["isPlaying"] is False
    assert state["isCapturing"] is False
    page.screenshot(path=str(SUCCESS_SCREENSHOT))

    page.locator("[data-director-export-trigger]").click()
    page.locator("[data-director-capture]").click()
    page.locator("[data-director-capture-preview]").wait_for(state="visible")
    capture = page.evaluate(
        """() => {
          const state = window.__director_store.getState();
          return state.captures.find(
            (item) => item.id === state.activeCaptureId,
          );
        }"""
    )
    assert capture["aspectRatio"] == "9:16"
    capture_image = decode_data_url(capture["dataUrl"])
    assert abs(capture_image.width / capture_image.height - 9 / 16) < 0.02

    page.locator("[data-close-director]").click()
    workspace.wait_for(state="detached")
    returned = page.locator("[data-director-animation-export-node]")
    returned.wait_for(state="visible")
    assert returned.count() == 1
    assert page.locator(".react-flow__node").count() == initial_nodes + 1
    assert page.locator(".react-flow__edge").count() == initial_edges + 1
    assert (
        returned.get_attribute("data-director-animation-export-source-id")
        == source_id
    )
    assert returned.get_attribute(
        "data-director-animation-export-mime"
    ).startswith("video/webm")
    byte_size = int(
        returned.get_attribute("data-director-animation-export-bytes") or "0"
    )
    assert byte_size > 10_000
    edge_id = returned.get_attribute("data-director-animation-export-edge-id")
    assert edge_id
    assert page.locator(f'.react-flow__edge[data-id="{edge_id}"]').count() == 1
    returned_node = returned.locator(
        "xpath=ancestor::div[contains(concat(' ', normalize-space(@class), ' '), ' react-flow__node ')][1]"
    )
    assert "selected" in (returned_node.get_attribute("class") or "")
    returned_box = box(returned_node)
    assert abs(returned_box["width"] / returned_box["height"] - 9 / 16) < 0.02

    video_result = inspect_video(page)
    assert video_result["blobSize"] == byte_size
    assert video_result["blobType"].startswith("video/webm")
    assert 0.85 <= video_result["duration"] <= 1.3
    assert video_result["videoWidth"] == 540
    assert video_result["videoHeight"] == 960
    assert video_result["playbackTime"] > 0.1
    assert video_result["frameDifference"] > 1_000
    poster = decode_data_url(video_result["poster"])
    assert poster.size == (540, 960)
    assert max(ImageStat.Stat(poster).stddev) > 8
    page.screenshot(path=str(GRAPH_SCREENSHOT))

    page.keyboard.press("Meta+z")
    page.wait_for_timeout(150)
    assert page.locator("[data-director-animation-export-node]").count() == 0
    assert page.locator(".react-flow__node").count() == initial_nodes
    assert page.locator(".react-flow__edge").count() == initial_edges
    page.keyboard.press("Meta+Shift+z")
    page.wait_for_timeout(150)
    assert page.locator("[data-director-animation-export-node]").count() == 1
    assert page.locator(".react-flow__node").count() == initial_nodes + 1
    assert page.locator(".react-flow__edge").count() == initial_edges + 1
    assert_no_overflow(page)
    assert errors == [], json.dumps(errors, ensure_ascii=False, indent=2)


def run_mobile(page: Page):
    errors = attach_errors(page)
    open_director(page, force_dom_click=True)
    page.locator("[data-director-export-trigger]").click()
    panel = page.locator("[data-director-export-panel]")
    panel.wait_for(state="visible")
    panel_box = box(panel)
    assert panel_box["x"] >= 12
    assert panel_box["x"] + panel_box["width"] <= 378
    assert panel_box["y"] >= 40
    assert page.locator("[data-director-export-duration]").is_visible()
    assert page.locator('[data-director-export-aspect="1:1"]').is_visible()
    page.locator('[data-director-export-aspect="1:1"]').click()
    frame_box = box(page.locator("[data-director-aspect-frame]"))
    assert abs(frame_box["width"] / frame_box["height"] - 1) < 0.02
    assert_no_overflow(page)
    page.screenshot(path=str(MOBILE_SCREENSHOT))
    page.locator("[data-director-export-trigger]").click()
    page.locator("[data-close-director]").click()
    assert page.locator("[data-director-workspace]").count() == 0
    assert errors == [], json.dumps(errors, ensure_ascii=False, indent=2)


def make_contact_sheet():
    items = [
        ("EXPORT SETTINGS", SETTINGS_SCREENSHOT),
        ("RECORDING", EXPORTING_SCREENSHOT),
        ("EXPORT SUCCESS", SUCCESS_SCREENSHOT),
        ("PLAYABLE VIDEO RETURN", GRAPH_SCREENSHOT),
        ("MOBILE SETTINGS", MOBILE_SCREENSHOT),
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
    desk_source = (
        ROOT / "src/components/director/DirectorDesk.tsx"
    ).read_text()
    panel_source = (
        ROOT / "src/components/director/DirectorExportPanel.tsx"
    ).read_text()
    viewport_source = (
        ROOT / "src/components/director/DirectorViewport.tsx"
    ).read_text()
    recorder_source = (
        ROOT / "src/components/director/directorVideoExport.ts"
    ).read_text()
    video_source = (
        ROOT / "src/components/nodes/VideoNode.tsx"
    ).read_text()
    store_source = (ROOT / "src/store/canvasStore.ts").read_text()

    assert "data-director-export-trigger" in desk_source
    assert "data-director-export-panel" in panel_source
    assert "正在导出动画视频..." in panel_source
    assert "recordDirectorCanvasVideo" in viewport_source
    assert "captureStream(30)" in recorder_source
    assert "MediaRecorder" in recorder_source
    assert "video/webm;codecs=vp9" in recorder_source
    assert "createDirectorAnimationExport" in store_source
    assert "DirectorAnimationExportMetadata" in store_source
    assert "data-director-animation-export" in video_source
    assert "<video" in video_source


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
    print("Batch 40 director animation export verification passed.")
