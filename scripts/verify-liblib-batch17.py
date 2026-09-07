from pathlib import Path

from playwright.sync_api import Page, sync_playwright


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


def open_asset_manager(page: Page):
    page.get_by_role("button", name="资产管理").click()
    panel = page.locator('[data-liblib-overlay="asset"]')
    assert panel.is_visible()
    return panel


def assert_no_overflow(page: Page):
    assert page.evaluate("document.documentElement.scrollWidth <= document.documentElement.clientWidth")
    assert page.evaluate("document.body.scrollWidth <= document.body.clientWidth")


def run_desktop(page: Page):
    errors = attach_errors(page)
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(400)
    panel = open_asset_manager(page)

    assert panel.locator("[data-asset-manager-project]").inner_text() == "未命名工作区"
    assert panel.locator("[data-asset-manager-canvas]").inner_text().strip() == "画布 2"
    assert panel.locator("[data-asset-manager-heading]").inner_text() == "画布元素"
    assert panel.locator('[data-asset-manager-list="canvas"] [data-asset-manager-item]').count() == 10
    assert panel.locator("[data-asset-manager-item]").first.get_attribute("data-asset-manager-item") == "i-YDfWhFlthe"
    assert panel.locator('[data-asset-manager-item="v-UGQZzZOpbv"]').get_attribute("data-asset-manager-depth") == "1"
    workbench_box = page.locator('button[aria-label="工作流"]').bounding_box()
    assert workbench_box and workbench_box["x"] >= 260
    page.screenshot(path=str(REFERENCE_DIR / "liblib-clone-batch17-asset-tree-desktop-929-2026-08-25.png"))

    panel.locator("[data-asset-manager-filter]").click()
    panel.locator('[data-asset-manager-filter-option="image"]').click()
    assert panel.locator("[data-asset-manager-item]").count() == 5

    panel.locator("[data-asset-manager-filter]").click()
    panel.locator('[data-asset-manager-filter-option="all"]').click()
    panel.locator("[data-asset-manager-search]").click()
    search_input = panel.locator("[data-asset-manager-search-input]")
    search_input.fill("分镜视频")
    assert panel.locator("[data-asset-manager-item]").count() == 1
    assert panel.locator('[data-asset-manager-item="v-UGQZzZOpbv"]').get_attribute("data-asset-manager-depth") == "0"
    page.screenshot(path=str(REFERENCE_DIR / "liblib-clone-batch17-asset-search-desktop-929-2026-08-25.png"))

    panel.locator("[data-asset-manager-search]").click()
    assert panel.locator("[data-asset-manager-item]").count() == 10
    panel.locator("[data-asset-manager-sort]").click()
    assert panel.locator("[data-asset-manager-sort]").get_attribute("data-asset-manager-sort") == "name"

    panel.locator('[data-asset-manager-item="i-YDfWhFlthe"]').click()
    assert page.locator('.react-flow__node[data-id="i-YDfWhFlthe"].selected').count() == 1

    panel.locator("[data-asset-manager-canvas]").click()
    assert not panel.is_visible()
    canvas_menu = page.locator('[data-liblib-overlay="canvas-dropdown"]')
    assert canvas_menu.is_visible()
    canvas_menu.locator('[data-canvas-row="canvas-1"] button').first.click()
    assert not canvas_menu.is_visible()

    panel = open_asset_manager(page)
    assert panel.locator("[data-asset-manager-canvas]").inner_text().strip() == "画布 1"
    # Batch 102/103: 源站 2026-09-05 复核空态文案为「画布暂无节点」。
    assert panel.locator("[data-asset-manager-empty]").inner_text() == "画布暂无节点"
    panel.locator('[data-asset-manager-tab="assets"]').click()
    assert panel.locator("[data-asset-manager-empty]").inner_text() == "当前画布暂无媒体资产"
    page.screenshot(path=str(REFERENCE_DIR / "liblib-clone-batch17-asset-empty-desktop-929-2026-08-25.png"))

    assert_no_overflow(page)
    assert not errors, errors


def run_mobile(page: Page):
    errors = attach_errors(page)
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(400)
    panel = open_asset_manager(page)
    assert panel.locator("[data-asset-manager-project]").inner_text() == "未命名工作区"
    assert panel.locator("[data-asset-manager-canvas]").inner_text().strip() == "画布 2"
    assert panel.locator("[data-asset-manager-item]").count() == 10
    assert_no_overflow(page)
    page.screenshot(path=str(REFERENCE_DIR / "liblib-clone-batch17-asset-tree-mobile-390-2026-08-25.png"))
    assert not errors, errors


def main():
    REFERENCE_DIR.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        desktop = browser.new_page(viewport={"width": 929, "height": 874}, device_scale_factor=1)
        run_desktop(desktop)
        desktop.close()
        mobile = browser.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=1)
        run_mobile(mobile)
        mobile.close()
        browser.close()
    print(
        "Batch17 Playwright verification passed: asset context, source-order tree, "
        "child depth, filter/search/sort, active-canvas handoff, empty states, "
        "mobile overflow, screenshots, console."
    )


if __name__ == "__main__":
    main()
