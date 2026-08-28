from pathlib import Path

from playwright.sync_api import Locator, Page, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "docs" / "design-references"
URL = "http://localhost:4317"


def attach_errors(page: Page):
    errors = []
    page.on(
        "console",
        lambda message: errors.append(f"console:{message.type}:{message.text}")
        if message.type == "error"
        else None,
    )
    page.on("pageerror", lambda error: errors.append(f"pageerror:{error}"))
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


def open_minimap(page: Page):
    trigger = page.get_by_role("button", name="显示缩略图")
    assert trigger.get_attribute("aria-pressed") == "false"
    trigger.click()
    minimap = page.locator(".liblib-minimap")
    minimap.wait_for(state="visible")
    assert trigger.get_attribute("aria-pressed") == "true"
    return trigger, minimap


def assert_source_visuals(page: Page, minimap: Locator):
    styles = minimap.evaluate(
        """element => {
          const style = getComputedStyle(element);
          const mask = element.querySelector('.react-flow__minimap-mask');
          const node = element.querySelector('.react-flow__minimap-node');
          const maskStyle = mask ? getComputedStyle(mask) : null;
          const nodeStyle = node ? getComputedStyle(node) : null;
          return {
            background: style.backgroundColor,
            borderRadius: style.borderRadius,
            maskFill: maskStyle?.fill ?? null,
            maskStroke: maskStyle?.stroke ?? null,
            nodeFill: nodeStyle?.fill ?? null,
            nodeStroke: nodeStyle?.stroke ?? null,
          };
        }"""
    )
    assert styles["background"] == "rgb(38, 38, 38)", styles
    assert styles["borderRadius"] == "10px", styles
    assert styles["maskFill"] == "rgba(20, 20, 20, 0.56)", styles
    assert styles["maskStroke"] == "rgb(116, 116, 116)", styles
    assert styles["nodeFill"] == "rgb(98, 98, 98)", styles
    assert styles["nodeStroke"] == "rgb(112, 112, 112)", styles
    assert page.locator(".react-flow__minimap-node").count() == 10


def run_desktop(page: Page):
    errors = attach_errors(page)
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(400)
    assert page.locator(".liblib-minimap").count() == 0

    trigger, minimap = open_minimap(page)
    trigger_box = box(trigger)
    minimap_box = box(minimap)
    assert abs(minimap_box["x"] - 152) <= 1, minimap_box
    assert abs(minimap_box["y"] - 710) <= 1, minimap_box
    assert abs(minimap_box["width"] - 150) <= 1, minimap_box
    assert abs(minimap_box["height"] - 110) <= 1, minimap_box
    assert abs(minimap_box["x"] - trigger_box["x"]) <= 12
    assert_source_visuals(page, minimap)
    initial_mask = page.locator(".react-flow__minimap-mask").get_attribute("d")
    page.keyboard.press("Meta+0")
    page.wait_for_timeout(420)
    fit_zoom = int(
        page.get_by_role("button", name="缩放选项").inner_text().strip().rstrip("%")
    )
    assert 20 <= fit_zoom <= 35
    assert page.locator(".react-flow__minimap-mask").get_attribute("d") != initial_mask
    page.screenshot(
        path=str(
            REFERENCE_DIR
            / "liblib-clone-batch19-minimap-desktop-929-2026-08-25.png"
        )
    )

    page.get_by_role("button", name="资产管理").click()
    page.wait_for_timeout(180)
    shifted_trigger_box = box(trigger)
    shifted_minimap_box = box(minimap)
    assert abs((shifted_trigger_box["x"] - trigger_box["x"]) - 240) <= 1
    assert abs((shifted_minimap_box["x"] - minimap_box["x"]) - 240) <= 1
    assert (
        abs(
            (shifted_minimap_box["x"] - shifted_trigger_box["x"])
            - (minimap_box["x"] - trigger_box["x"])
        )
        <= 1
    )
    page.screenshot(
        path=str(
            REFERENCE_DIR
            / "liblib-clone-batch19-minimap-asset-drawer-929-2026-08-25.png"
        )
    )

    trigger.click()
    assert page.locator(".liblib-minimap").count() == 0
    assert trigger.get_attribute("aria-pressed") == "false"
    assert_no_overflow(page)
    assert not errors, errors


def run_mobile(page: Page):
    errors = attach_errors(page)
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(400)
    _, minimap = open_minimap(page)
    minimap_box = box(minimap)
    primary_toolbar = box(page.get_by_role("button", name="添加节点").locator(".."))

    assert abs(minimap_box["x"] - 128) <= 1, minimap_box
    assert abs(minimap_box["y"] - 627) <= 1, minimap_box
    assert abs(minimap_box["width"] - 150) <= 1, minimap_box
    assert abs(minimap_box["height"] - 110) <= 1, minimap_box
    assert minimap_box["y"] + minimap_box["height"] <= primary_toolbar["y"] - 4
    assert_no_overflow(page)
    page.screenshot(
        path=str(
            REFERENCE_DIR
            / "liblib-clone-batch19-minimap-mobile-390-2026-08-25.png"
        )
    )
    assert not errors, errors


def main():
    REFERENCE_DIR.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        desktop = browser.new_page(
            viewport={"width": 929, "height": 874}, device_scale_factor=1
        )
        run_desktop(desktop)
        desktop.close()
        mobile = browser.new_page(
            viewport={"width": 390, "height": 844}, device_scale_factor=1
        )
        run_mobile(mobile)
        mobile.close()
        browser.close()
    print(
        "Batch19 Playwright verification passed: minimap source anchor, "
        "visuals, toggle state, asset-drawer follow, mobile toolbar avoidance, "
        "overflow, screenshots, console."
    )


if __name__ == "__main__":
    main()
