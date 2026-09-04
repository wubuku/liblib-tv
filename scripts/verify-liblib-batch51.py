# AGED_GATE / HISTORICAL_CONTRACT（Batch 108 归因,2026-09-05）：
# 本 verifier 在基线 86673b6（Batch 96 收口）上同样失败，属既有漂移，
# 非 Batch 97-107 引入。已被 LIBTV_DIRECTOR_CURRENT_VERIFIER_MANIFEST /
# Batch 59、67-96 current gates 取代；处置见
# docs/research/LIBTV_VERIFIER_REPLACEMENT_MAP.md §4.z。
# 运行仍可用于历史快照对照，不能作为当前合同通过依据。
import os
import json
from pathlib import Path

from playwright.sync_api import Page, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
URL = os.environ.get("LIBLIB_BASE_URL", "http://localhost:4317")
REFERENCE_DIR = ROOT / "docs" / "design-references"
AUDIT_PATH = (
    ROOT
    / "docs"
    / "research"
    / "liblib-canvas-batch51-2026-08-26"
    / "runtime-audit.json"
)
IMAGE_ID = "i-YDfWhFlthe"
IMAGE_WORLD_WIDTH = 622


def node(page: Page):
    return page.locator(f'.react-flow__node[data-id="{IMAGE_ID}"]')


def box(locator):
    value = locator.bounding_box()
    assert value is not None
    return value


def center_x(rect):
    return rect["x"] + rect["width"] / 2


def assert_close(actual: float, expected: float, tolerance: float = 1):
    assert abs(actual - expected) <= tolerance, (actual, expected)


def collect_errors(page: Page):
    errors = []
    page.on(
        "console",
        lambda message: errors.append(f"console:{message.type}:{message.text}")
        if message.type == "error"
        else None,
    )
    page.on("pageerror", lambda error: errors.append(f"pageerror:{error}"))
    return errors


def organize(page: Page):
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(400)
    page.keyboard.press("Alt+Shift+f")
    page.wait_for_timeout(300)
    assert page.get_by_role("button", name="缩放选项").inner_text() == "28%"


def assert_image_anchor(page: Page, expected_zoom: float | None = None):
    node_box = box(node(page))
    toolbar_box = box(page.locator("[data-image-toolbar]"))
    panel_box = box(page.locator("[data-image-edit-panel]"))
    zoom = node_box["width"] / IMAGE_WORLD_WIDTH
    if expected_zoom is not None:
        assert_close(zoom, expected_zoom, 0.02)

    assert_close(center_x(toolbar_box), center_x(node_box))
    assert_close(node_box["y"] - (toolbar_box["y"] + toolbar_box["height"]), 10 + 24 * zoom)
    assert_close(toolbar_box["width"], 900.5)
    assert_close(toolbar_box["height"], 49)

    assert_close(center_x(panel_box), center_x(node_box))
    assert_close(panel_box["y"] - (node_box["y"] + node_box["height"]), 16 * zoom)
    assert_close(panel_box["width"], 660)
    assert_close(panel_box["height"], 274)
    return node_box, toolbar_box, panel_box, zoom


def main():
    REFERENCE_DIR.mkdir(parents=True, exist_ok=True)
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(
            viewport={"width": 929, "height": 874}, device_scale_factor=1
        )
        errors = collect_errors(page)
        organize(page)

        node(page).click(force=True)
        page.wait_for_timeout(180)
        initial_node, initial_toolbar, initial_panel, _ = assert_image_anchor(
            page, expected_zoom=0.28
        )
        measurements = {
            "28_percent": {
                "node": initial_node,
                "toolbar": initial_toolbar,
                "panel": initial_panel,
            }
        }
        page.screenshot(
            path=str(
                REFERENCE_DIR
                / "liblib-clone-batch51-image-toolbar-source-gap-28-2026-08-26.png"
            )
        )

        page.get_by_role("button", name="缩放选项").click()
        page.locator('[data-zoom-action="in"]').click()
        page.wait_for_timeout(260)
        zoomed_node, zoomed_toolbar, zoomed_panel, zoom = assert_image_anchor(page)
        measurements["zoomed"] = {
            "node": zoomed_node,
            "toolbar": zoomed_toolbar,
            "panel": zoomed_panel,
            "zoom": zoom,
        }
        assert zoom > 0.28
        assert_close(
            center_x(zoomed_node),
            center_x(zoomed_toolbar),
        )
        assert_close(
            center_x(zoomed_node),
            center_x(zoomed_panel),
        )
        assert_close(
            zoomed_toolbar["width"],
            initial_toolbar["width"],
        )
        assert_close(zoomed_toolbar["height"], initial_toolbar["height"])
        assert_close(zoomed_panel["width"], initial_panel["width"])
        assert_close(zoomed_panel["height"], initial_panel["height"])

        viewport_before = page.locator(".react-flow__viewport").get_attribute("style")
        page.mouse.move(260, 160)
        page.mouse.wheel(85, 42)
        page.wait_for_timeout(260)
        panned_node, panned_toolbar, panned_panel, _ = assert_image_anchor(page)
        measurements["zoomed_pan"] = {
            "node": panned_node,
            "toolbar": panned_toolbar,
            "panel": panned_panel,
            "zoom": zoom,
        }
        assert page.locator(".react-flow__viewport").get_attribute("style") != viewport_before
        assert_close(
            panned_node["x"] - zoomed_node["x"],
            panned_toolbar["x"] - zoomed_toolbar["x"],
        )
        assert_close(
            panned_node["y"] - zoomed_node["y"],
            panned_toolbar["y"] - zoomed_toolbar["y"],
        )
        assert_close(
            panned_node["x"] - zoomed_node["x"],
            panned_panel["x"] - zoomed_panel["x"],
        )
        assert_close(
            panned_node["y"] - zoomed_node["y"],
            panned_panel["y"] - zoomed_panel["y"],
        )
        page.screenshot(
            path=str(
                REFERENCE_DIR
                / "liblib-clone-batch51-image-toolbar-source-gap-zoom-pan-2026-08-26.png"
            )
        )

        assert page.locator("[data-image-toolbar]").count() == 1
        assert page.locator("[data-image-edit-panel]").count() == 1
        assert not errors, errors
        page.close()
        browser.close()

    AUDIT_PATH.write_text(
        json.dumps(
            {
                "url": URL,
                "viewport": {"width": 929, "height": 874},
                "node_id": IMAGE_ID,
                "contract": {
                    "toolbar_top_gap": "10 + 24 * zoom",
                    "panel_bottom_gap": "16 * zoom",
                    "toolbar_size": [900.5, 49],
                    "panel_width": 660,
                },
                "measurements": measurements,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )

    print(
        "Batch 51 Playwright verification passed: source-confirmed image "
        "toolbar top gap, node-centered bottom panel, zoom/pan follow, "
        "screen-size preservation, and console."
    )


if __name__ == "__main__":
    main()
