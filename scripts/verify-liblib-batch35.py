from base64 import b64decode
from io import BytesIO
from pathlib import Path
import json
import os

from PIL import Image, ImageDraw, ImageStat
from playwright.sync_api import Locator, Page, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "docs" / "design-references"
BASE_URL = os.environ.get("LIBLIB_BASE_URL", "http://localhost:3000")

DESKTOP_SCREENSHOT = (
    REFERENCE_DIR / "liblib-clone-batch35-director-desktop-1440-2026-08-26.png"
)
CAMERA_SCREENSHOT = (
    REFERENCE_DIR / "liblib-clone-batch35-director-camera-1440-2026-08-26.png"
)
CAPTURE_SCREENSHOT = (
    REFERENCE_DIR / "liblib-clone-batch35-director-capture-1440-2026-08-26.png"
)
RAW_CAPTURE_SCREENSHOT = (
    REFERENCE_DIR / "liblib-clone-batch35-director-output-16x9-2026-08-26.png"
)
RETURN_SCREENSHOT = (
    REFERENCE_DIR / "liblib-clone-batch35-director-return-1440-2026-08-26.png"
)
MOBILE_SCREENSHOT = (
    REFERENCE_DIR / "liblib-clone-batch35-director-mobile-390-2026-08-26.png"
)
CONTACT_SHEET = (
    REFERENCE_DIR / "liblib-clone-batch35-director-contact-sheet-2026-08-26.png"
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


def assert_nonblank_image(image: Image.Image, label: str):
    rgb = image.convert("RGB")
    stat = ImageStat.Stat(rgb)
    assert max(stat.stddev) > 8, f"{label} has insufficient pixel variance: {stat.stddev}"
    extrema_spans = [maximum - minimum for minimum, maximum in stat.extrema]
    assert max(extrema_spans) > 80, f"{label} has insufficient color range: {stat.extrema}"


def assert_nonblank_locator(locator: Locator, label: str):
    image = Image.open(BytesIO(locator.screenshot()))
    assert_nonblank_image(image, label)
    return image


def read_capture_image(data_url: str):
    prefix = "data:image/png;base64,"
    assert data_url.startswith(prefix)
    return Image.open(BytesIO(b64decode(data_url.removeprefix(prefix))))


def open_director(page: Page, force_dom_click: bool = False):
    button = page.locator("[data-open-director]")
    assert button.count() == 1
    source_id = button.locator(
        "xpath=ancestor::div[contains(@class, 'react-flow__node')][1]"
    ).get_attribute("data-id")
    assert source_id
    if force_dom_click:
        button.evaluate("(element) => element.click()")
    else:
        button.click()
    page.locator("[data-director-workspace]").wait_for(state="visible")
    page.locator('canvas[data-director-webgl-canvas="true"]').wait_for(
        state="visible"
    )
    page.wait_for_timeout(700)
    return source_id


def run_desktop(page: Page):
    errors = attach_errors(page)
    page.goto(BASE_URL, wait_until="networkidle")
    initial_nodes = page.locator(".react-flow__node").count()
    initial_edges = page.locator(".react-flow__edge").count()
    viewport_style = page.locator(".react-flow__viewport").get_attribute("style")
    source_id = open_director(page)

    workspace = page.locator("[data-director-workspace]")
    workspace_box = box(workspace)
    assert workspace_box["x"] == 0
    assert workspace_box["y"] == 0
    assert workspace_box["width"] == 1440
    assert workspace_box["height"] == 900
    assert page.locator(".react-flow__node").count() == initial_nodes
    assert page.locator(".react-flow__edge").count() == initial_edges
    assert page.locator("[data-director-object-id]").count() == 5
    assert (
        page.locator("[data-director-inspector]").get_attribute(
            "data-director-inspector-kind"
        )
        == "character"
    )
    assert_no_overflow(page)

    canvas = page.locator('canvas[data-director-webgl-canvas="true"]')
    assert_nonblank_locator(canvas, "default director WebGL canvas")
    page.screenshot(path=str(DESKTOP_SCREENSHOT))

    mug_row = page.locator(
        '[data-director-object-id="director-prop-mug"]'
    )
    mug_row.click()
    assert mug_row.get_attribute("data-director-object-selected") == "true"
    assert (
        page.locator("[data-director-inspector]").get_attribute(
            "data-director-inspector-kind"
        )
        == "prop"
    )
    x_input = page.locator(
        '[data-director-transform-field="position"]'
        '[data-director-transform-axis="x"]'
    )
    x_input.fill("0.8")
    assert (
        page.evaluate(
            """() => window.__director_store.getState().objects
              .find((object) => object.id === "director-prop-mug")
              .transform.position[0]"""
        )
        == 0.8
    )
    visibility_button = mug_row.get_by_role("button", name="隐藏冷掉的咖啡")
    visibility_button.click()
    assert mug_row.get_attribute("data-director-object-visible") == "false"
    mug_row.get_by_role("button", name="显示冷掉的咖啡").click()
    assert mug_row.get_attribute("data-director-object-visible") == "true"

    camera_mode = page.locator('[data-director-view-mode="camera"]')
    camera_mode.click()
    assert camera_mode.get_attribute("aria-pressed") == "true"
    assert page.locator("[data-director-viewport]").get_attribute(
        "data-director-view"
    ) == "camera"
    assert (
        page.locator("[data-director-inspector]").get_attribute(
            "data-director-inspector-kind"
        )
        == "camera"
    )
    assert_nonblank_locator(canvas, "camera-view WebGL canvas")

    frame = page.locator("[data-director-aspect-frame]")
    frame_16_9 = box(frame)
    assert abs(frame_16_9["width"] / frame_16_9["height"] - 16 / 9) < 0.02
    page.locator('[data-director-aspect="9:16"]').click()
    frame_9_16 = box(frame)
    assert abs(frame_9_16["width"] / frame_9_16["height"] - 9 / 16) < 0.02
    assert frame_9_16["width"] < frame_16_9["width"]
    page.locator('[data-director-aspect="16:9"]').click()
    page.get_by_role("button", name="开启九宫格辅助线").click()
    assert page.locator("[data-director-thirds]").count() == 1
    page.screenshot(path=str(CAMERA_SCREENSHOT))

    page.locator("[data-director-capture]").click()
    page.locator("[data-director-capture-preview]").wait_for(state="visible")
    assert page.locator("[data-director-capture-status]").get_attribute(
        "data-director-capture-status"
    ) == "ready"
    capture = page.evaluate(
        "() => window.__director_store.getState().captures[0]"
    )
    assert capture["aspectRatio"] == "16:9"
    assert capture["cameraId"] == "director-camera-main"
    capture_image = read_capture_image(capture["dataUrl"])
    assert_nonblank_image(capture_image, "director PNG capture")
    assert abs(capture_image.width / capture_image.height - 16 / 9) < 0.02
    capture_image.convert("RGB").save(RAW_CAPTURE_SCREENSHOT)
    page.screenshot(path=str(CAPTURE_SCREENSHOT))

    page.locator("[data-director-send-capture]").click()
    assert page.locator("[data-director-capture-node]").count() == 1
    assert page.locator(".react-flow__node").count() == initial_nodes + 1
    assert page.locator(".react-flow__edge").count() == initial_edges + 1
    returned = page.locator("[data-director-capture-node]")
    assert returned.get_attribute("data-director-capture-source-id") == source_id
    assert returned.get_attribute("data-director-capture-camera-id") == (
        "director-camera-main"
    )
    assert returned.get_attribute("data-director-capture-aspect") == "16:9"

    page.locator("[data-close-director]").click()
    workspace.wait_for(state="detached")
    assert page.locator(".react-flow__viewport").get_attribute("style") == viewport_style
    assert (
        page.locator(f'.react-flow__node.selected[data-id="{source_id}"]').count()
        == 1
    )
    page.screenshot(path=str(RETURN_SCREENSHOT))

    page.keyboard.press("Meta+z")
    page.wait_for_timeout(120)
    assert page.locator("[data-director-capture-node]").count() == 0
    assert page.locator(".react-flow__node").count() == initial_nodes
    assert page.locator(".react-flow__edge").count() == initial_edges
    page.keyboard.press("Meta+Shift+z")
    page.wait_for_timeout(120)
    assert page.locator("[data-director-capture-node]").count() == 1
    assert page.locator(".react-flow__node").count() == initial_nodes + 1
    assert page.locator(".react-flow__edge").count() == initial_edges + 1
    assert errors == [], json.dumps(errors, ensure_ascii=False, indent=2)


def run_mobile(page: Page):
    errors = attach_errors(page)
    page.goto(BASE_URL, wait_until="networkidle")
    open_director(page, force_dom_click=True)
    assert_no_overflow(page)
    canvas = page.locator('canvas[data-director-webgl-canvas="true"]')
    assert_nonblank_locator(canvas, "mobile director WebGL canvas")

    tree_panel = page.locator('aside[aria-label="场景对象"]')
    inspector_panel = page.locator('aside[aria-label="属性"]')
    assert tree_panel.get_attribute("data-director-mobile-panel-state") == "closed"
    assert inspector_panel.get_attribute(
        "data-director-mobile-panel-state"
    ) == "closed"
    page.get_by_role("button", name="打开场景对象").click()
    page.wait_for_timeout(240)
    assert tree_panel.get_attribute("data-director-mobile-panel-state") == "open"
    assert box(tree_panel)["x"] == 0
    assert_no_overflow(page)
    page.screenshot(path=str(MOBILE_SCREENSHOT))

    backdrop = page.get_by_role("button", name="关闭移动端面板")
    backdrop.click(position={"x": 340, "y": 160})
    page.get_by_role("button", name="打开属性面板").click()
    page.wait_for_timeout(240)
    assert inspector_panel.get_attribute(
        "data-director-mobile-panel-state"
    ) == "open"
    inspector_box = box(inspector_panel)
    assert inspector_box["x"] + inspector_box["width"] == 390
    assert_no_overflow(page)
    backdrop.click(position={"x": 24, "y": 160})
    page.locator("[data-close-director]").click()
    assert page.locator("[data-director-workspace]").count() == 0
    assert errors == [], json.dumps(errors, ensure_ascii=False, indent=2)


def make_contact_sheet():
    items = [
        ("DIRECTOR VIEW", DESKTOP_SCREENSHOT),
        ("CAMERA + GUIDES", CAMERA_SCREENSHOT),
        ("CAPTURE PREVIEW", CAPTURE_SCREENSHOT),
        ("RAW HELPER-FREE PNG", RAW_CAPTURE_SCREENSHOT),
        ("CANVAS RETURN", RETURN_SCREENSHOT),
        ("MOBILE TREE", MOBILE_SCREENSHOT),
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
    left_height = sum(
        image.height + label_height + padding for _, image in rendered[::2]
    )
    right_height = sum(
        image.height + label_height + padding for _, image in rendered[1::2]
    )
    sheet_height = max(left_height, right_height) + padding
    sheet = Image.new("RGB", (sheet_width, sheet_height), "#111111")
    draw = ImageDraw.Draw(sheet)
    column_y = [padding, padding]
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
    package = (ROOT / "package.json").read_text()
    page_source = (ROOT / "src/app/page.tsx").read_text()
    node_source = (
        ROOT / "src/components/nodes/ScriptExecutionNode.tsx"
    ).read_text()
    desk_source = (
        ROOT / "src/components/director/DirectorDesk.tsx"
    ).read_text()
    viewport_source = (
        ROOT / "src/components/director/DirectorViewport.tsx"
    ).read_text()
    store_source = (ROOT / "src/store/canvasStore.ts").read_text()
    director_store_source = (ROOT / "src/store/directorStore.ts").read_text()

    for dependency in [
        '"three"',
        '"@react-three/fiber"',
        '"@react-three/drei"',
    ]:
        assert dependency in package
    assert 'ssr: false' in page_source
    assert "data-open-director" in node_source
    assert "nodrag nopan nowheel" in node_source
    assert "data-director-workspace" in desk_source
    assert "preserveDrawingBuffer: true" in viewport_source
    assert "scene.showGrid && !isCapturing" in viewport_source
    assert "const hideCameraRig" in viewport_source
    assert 'viewMode === "camera" && object.id === activeCameraId' in viewport_source
    assert "createDirectorCapture" in store_source
    assert "historyByCanvas: pushHistory" in store_source
    assert "__director_store" in director_store_source


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
    print("Batch 35 director workspace verification passed.")
