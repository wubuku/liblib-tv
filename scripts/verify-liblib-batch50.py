from io import BytesIO
from pathlib import Path
import copy
import json
import os

from PIL import Image, ImageDraw, ImageStat
from playwright.sync_api import Locator, Page, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "docs" / "design-references"
BASE_URL = os.environ.get("LIBLIB_BASE_URL", "http://localhost:3000")

DESKTOP_EXPANDED_SCREENSHOT = (
    REFERENCE_DIR
    / "liblib-clone-batch50-director-workspace-expanded-1440-2026-08-26.png"
)
DESKTOP_COLLAPSED_SCREENSHOT = (
    REFERENCE_DIR
    / "liblib-clone-batch50-director-workspace-collapsed-1440-2026-08-26.png"
)
MOBILE_TREE_SCREENSHOT = (
    REFERENCE_DIR
    / "liblib-clone-batch50-director-workspace-mobile-tree-390-2026-08-26.png"
)
MOBILE_COLLAPSED_SCREENSHOT = (
    REFERENCE_DIR
    / "liblib-clone-batch50-director-workspace-mobile-collapsed-390-2026-08-26.png"
)
CONTACT_SHEET = (
    REFERENCE_DIR
    / "liblib-clone-batch50-director-workspace-contact-sheet-2026-08-26.png"
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


def assert_inside(inner: Locator, outer: Locator, tolerance: float = 1):
    inner_box = box(inner)
    outer_box = box(outer)
    assert inner_box["x"] >= outer_box["x"] - tolerance
    assert inner_box["y"] >= outer_box["y"] - tolerance
    assert inner_box["x"] + inner_box["width"] <= (
        outer_box["x"] + outer_box["width"] + tolerance
    )
    assert inner_box["y"] + inner_box["height"] <= (
        outer_box["y"] + outer_box["height"] + tolerance
    )


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
    assert max(spans) > 45, f"{label} has insufficient range: {stat.extrema}"


def open_director(page: Page):
    page.goto(f"{BASE_URL}/?batch50=1", wait_until="networkidle")
    page.locator("[data-open-director]").click()
    page.locator("[data-director-workspace]").wait_for(state="visible")
    page.locator("[data-director-timeline]").wait_for(state="visible")
    page.locator('canvas[data-director-webgl-canvas="true"]').wait_for(
        state="visible"
    )
    page.wait_for_timeout(800)


def computed_display(locator: Locator) -> str:
    return locator.evaluate(
        "(element) => window.getComputedStyle(element).display"
    )


def director_state(page: Page):
    return page.evaluate(
        """() => {
          const state = window.__director_store.getState();
          return {
            objects: state.objects,
            selectedObjectId: state.selectedObjectId,
            selectedObjectIds: state.selectedObjectIds,
            selectedGroupId: state.selectedGroupId,
            activeCameraId: state.activeCameraId,
            viewMode: state.viewMode,
            aspectRatio: state.aspectRatio,
            showThirds: state.showThirds,
            timeline: state.timeline,
            phoneVcam: state.phoneVcam,
            captures: state.captures,
          };
        }"""
    )


def open_export_panel(page: Page):
    page.locator("[data-director-export-trigger]").click()
    panel = page.locator("[data-director-export-panel]")
    panel.wait_for(state="visible")
    return panel


def run_desktop(page: Page):
    errors = attach_errors(page)
    open_director(page)

    workspace = page.locator("[data-director-workspace]")
    viewport = page.locator("[data-director-viewport]")
    tree_rail = page.locator('aside[aria-label="场景对象"]')
    inspector_rail = page.locator('aside[aria-label="属性"]')
    toggle = page.locator("[data-director-panels-toggle]")
    main_canvas = page.locator('canvas[data-director-webgl-canvas="true"]')

    assert workspace.get_attribute("role") == "dialog"
    assert workspace.get_attribute("aria-modal") == "true"
    assert workspace.get_attribute("aria-label") == "3D导演台工作区"
    assert page.evaluate(
        """() => Boolean(
          document.activeElement?.hasAttribute(
            "data-director-workspace-focus-owner"
          )
        )"""
    )
    assert workspace.get_attribute("data-director-panels-collapsed") == "false"
    assert computed_display(tree_rail) != "none"
    assert computed_display(inspector_rail) != "none"
    assert tree_rail.get_attribute("aria-hidden") is None
    assert inspector_rail.get_attribute("aria-hidden") is None
    assert toggle.get_attribute("aria-label") == "全屏"
    assert toggle.get_attribute("aria-pressed") == "false"
    assert_nonblank_locator(main_canvas, "Batch 50 Director WebGL canvas")
    assert_inside(viewport, workspace)
    assert_no_overflow(page)

    initial_state = director_state(page)
    initial_state_without_captures = copy.deepcopy(initial_state)
    initial_state_without_captures["captures"] = []
    desktop_viewport_box = box(viewport)
    page.screenshot(path=str(DESKTOP_EXPANDED_SCREENSHOT))

    toggle.click()
    page.wait_for_timeout(180)
    collapsed_viewport_box = box(viewport)
    assert workspace.get_attribute("data-director-panels-collapsed") == "true"
    assert viewport.get_attribute("data-director-panels-collapsed") == "true"
    assert computed_display(tree_rail) == "none"
    assert computed_display(inspector_rail) == "none"
    assert tree_rail.get_attribute("aria-hidden") == "true"
    assert inspector_rail.get_attribute("aria-hidden") == "true"
    assert toggle.get_attribute("aria-label") == "恢复侧栏"
    assert toggle.get_attribute("aria-pressed") == "true"
    assert collapsed_viewport_box["x"] <= desktop_viewport_box["x"] - 200
    assert collapsed_viewport_box["width"] > desktop_viewport_box["width"] + 450
    state_after_collapse = director_state(page)
    state_after_collapse["captures"] = []
    assert state_after_collapse == initial_state_without_captures
    assert_no_overflow(page)
    page.screenshot(path=str(DESKTOP_COLLAPSED_SCREENSHOT))

    toggle.click()
    page.wait_for_timeout(180)
    restored_viewport_box = box(viewport)
    assert workspace.get_attribute("data-director-panels-collapsed") == "false"
    assert computed_display(tree_rail) != "none"
    assert computed_display(inspector_rail) != "none"
    assert abs(restored_viewport_box["x"] - desktop_viewport_box["x"]) <= 1
    assert abs(restored_viewport_box["width"] - desktop_viewport_box["width"]) <= 1
    restored_state = director_state(page)
    restored_state["captures"] = []
    assert restored_state == initial_state_without_captures

    underlying_node_count = page.locator("[data-director-node]").count()
    workspace.focus()
    page.keyboard.press("Tab")
    assert page.locator("[data-liblib-overlay='add-node']").count() == 0
    workspace.focus()
    page.keyboard.down("Space")
    page.wait_for_timeout(50)
    assert page.locator(".react-flow[data-temporary-pan='true']").count() == 0
    page.keyboard.up("Space")
    workspace.focus()
    page.keyboard.press("Delete")
    assert page.locator("[data-director-node]").count() == underlying_node_count
    workspace.focus()
    page.keyboard.press("Control+z")
    assert page.locator("[data-director-node]").count() == underlying_node_count

    name_input = page.locator("[data-director-inspector] input").first
    name_input.fill("临时可编辑名称")
    name_input.focus()
    page.keyboard.press("Delete")
    page.keyboard.down("Space")
    page.wait_for_timeout(40)
    page.keyboard.up("Space")
    page.keyboard.press("Tab")
    assert page.locator("[data-liblib-overlay='add-node']").count() == 0
    assert page.locator(".react-flow[data-temporary-pan='true']").count() == 0
    assert page.locator("[data-director-phone-vcam-panel]").count() == 0

    export_panel = open_export_panel(page)
    page.keyboard.press("Escape")
    export_panel.wait_for(state="hidden")
    assert workspace.is_visible()
    open_export_panel(page)
    page.keyboard.press("Escape")
    page.keyboard.press("Escape")
    workspace.wait_for(state="hidden")
    assert errors == [], json.dumps(errors, ensure_ascii=False, indent=2)


def run_mobile(page: Page):
    errors = attach_errors(page)
    open_director(page)

    workspace = page.locator("[data-director-workspace]")
    viewport = page.locator("[data-director-viewport]")
    tree_rail = page.locator('aside[aria-label="场景对象"]')
    inspector_rail = page.locator('aside[aria-label="属性"]')
    tree_trigger = page.locator("[aria-label='打开场景对象']")
    inspector_trigger = page.locator("[aria-label='打开属性面板']")
    toggle = page.locator("[data-director-panels-toggle]")

    assert workspace.get_attribute("data-director-panels-collapsed") == "false"
    assert page.locator("[data-director-mobile-panel-state='open']").count() == 0
    assert_inside(viewport, workspace)
    assert_no_overflow(page)

    tree_trigger.click()
    page.wait_for_timeout(220)
    assert tree_rail.get_attribute("data-director-mobile-panel-state") == "open"
    assert inspector_rail.get_attribute("data-director-mobile-panel-state") == "closed"
    assert page.locator("[aria-label='关闭移动端面板']").count() == 1
    page.screenshot(path=str(MOBILE_TREE_SCREENSHOT))

    page.keyboard.press("Escape")
    page.wait_for_timeout(180)
    assert page.locator("[data-director-mobile-panel-state='open']").count() == 0
    inspector_trigger.click()
    page.wait_for_timeout(220)
    assert tree_rail.get_attribute("data-director-mobile-panel-state") == "closed"
    assert inspector_rail.get_attribute("data-director-mobile-panel-state") == "open"
    assert page.locator("[data-director-mobile-panel-state='open']").count() == 1
    assert_no_overflow(page)

    page.evaluate(
        "() => window.__director_store.getState().setViewportPanelsCollapsed(true)"
    )
    page.wait_for_timeout(180)
    assert workspace.get_attribute("data-director-panels-collapsed") == "true"
    assert tree_rail.get_attribute("data-director-mobile-panel-state") == "closed"
    assert inspector_rail.get_attribute("data-director-mobile-panel-state") == "closed"
    assert page.locator("[data-director-mobile-panel-state='open']").count() == 0
    page.screenshot(path=str(MOBILE_COLLAPSED_SCREENSHOT))

    tree_trigger.click()
    page.wait_for_timeout(220)
    assert workspace.get_attribute("data-director-panels-collapsed") == "false"
    assert tree_rail.get_attribute("data-director-mobile-panel-state") == "open"
    assert inspector_rail.get_attribute("data-director-mobile-panel-state") == "closed"
    assert_no_overflow(page)
    assert errors == [], json.dumps(errors, ensure_ascii=False, indent=2)


def make_contact_sheet():
    items = [
        ("DESKTOP EXPANDED", DESKTOP_EXPANDED_SCREENSHOT),
        ("DESKTOP COLLAPSED", DESKTOP_COLLAPSED_SCREENSHOT),
        ("MOBILE TREE", MOBILE_TREE_SCREENSHOT),
        ("MOBILE COLLAPSED", MOBILE_COLLAPSED_SCREENSHOT),
    ]
    thumb_width = 720
    label_height = 34
    padding = 16
    rendered = []
    for label, path in items:
        image = Image.open(path).convert("RGB")
        target_width = 360 if image.width < 600 else thumb_width
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
    viewport_source = (
        ROOT / "src/components/director/DirectorViewport.tsx"
    ).read_text()
    store_source = (ROOT / "src/store/directorStore.ts").read_text()
    page_source = (ROOT / "src/app/page.tsx").read_text()
    assert "data-director-workspace-focus-owner" in desk_source
    assert "data-director-panels-collapsed" in desk_source
    assert "data-director-panels-toggle" in viewport_source
    assert "viewportPanelsCollapsed" in store_source
    assert "activeDirectorNodeId" in page_source


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
    print("Batch 50 director workspace shell verification passed.")
