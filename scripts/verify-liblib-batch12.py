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
    assert page.locator('[data-liblib-overlay="asset"]').is_visible()
    assert page.locator('[data-asset-manager-tab="canvas"]').get_attribute("aria-pressed") == "true"


def assert_graph(page: Page):
    assert page.locator(".react-flow__node").count() == 10
    assert page.locator(".react-flow__edge").count() == 11


def run_desktop(page: Page):
    errors = attach_errors(page)
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(400)
    assert_graph(page)

    open_asset_manager(page)
    assert page.locator('[data-asset-manager-list="canvas"] [data-asset-manager-item]').count() == 10

    page.locator('[data-asset-manager-tab="assets"]').click()
    assert page.locator('[data-asset-manager-tab="assets"]').get_attribute("aria-pressed") == "true"
    assert page.locator('[data-asset-manager-list="assets"] [data-asset-manager-item]').count() == 6
    assert page.get_by_text("共 6 项资产", exact=True).is_visible()

    page.locator('[data-asset-manager-item="i-YDfWhFlthe"]').click()
    assert page.locator('.react-flow__node[data-id="i-YDfWhFlthe"].selected').count() == 1

    page.locator('[data-asset-manager-tab="canvas"]').click()
    assert page.locator('[data-asset-manager-list="canvas"] [data-asset-manager-item]').count() == 10
    assert page.get_by_text("共 10 节点", exact=True).is_visible()
    assert_graph(page)

    page.get_by_role("button", name="关闭资产管理").click()
    assert not page.locator('[data-liblib-overlay="asset"]').is_visible()

    page.screenshot(
        path=str(REFERENCE_DIR / "liblib-clone-batch12-asset-manager-desktop-929-2026-08-25.png")
    )
    assert not errors, errors


def run_mobile(page: Page):
    errors = attach_errors(page)
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(400)
    open_asset_manager(page)
    page.locator('[data-asset-manager-tab="assets"]').click()
    assert page.locator('[data-asset-manager-list="assets"] [data-asset-manager-item]').count() == 6
    assert page.evaluate("document.documentElement.scrollWidth <= document.documentElement.clientWidth")
    assert page.evaluate("document.body.scrollWidth <= document.body.clientWidth")
    page.screenshot(
        path=str(REFERENCE_DIR / "liblib-clone-batch12-asset-manager-mobile-390-2026-08-25.png")
    )
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
        "Batch12 Playwright verification passed: canvas/assets tabs, "
        "six media assets, node selection, close lifecycle, mobile overflow, "
        "screenshots, console."
    )


if __name__ == "__main__":
    main()
