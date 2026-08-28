import os
from pathlib import Path

from playwright.sync_api import Page, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "docs" / "design-references"
URL = os.environ.get("LIBLIB_BASE_URL", "http://localhost:3000")


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


def open_zoom_menu(page: Page):
    trigger = page.locator('[data-viewport-menu-trigger="zoom"]')
    trigger.click()
    menu = page.locator('[data-liblib-overlay="zoom-menu"]')
    menu.wait_for(state="visible")
    return trigger, menu


def zoom_percent(trigger) -> int:
    return int(trigger.inner_text().strip().rstrip("%"))


def assert_no_overflow(page: Page):
    assert page.evaluate("document.documentElement.scrollWidth <= document.documentElement.clientWidth")
    assert page.evaluate("document.body.scrollWidth <= document.body.clientWidth")


def run_desktop(page: Page):
    errors = attach_errors(page)
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(400)
    trigger, menu = open_zoom_menu(page)

    assert zoom_percent(trigger) == 53
    assert menu.locator("[data-zoom-action]").count() == 6
    assert menu.locator("[data-zoom-current]").inner_text().split() == ["53", "%"]
    assert menu.get_by_text("放大", exact=True).is_visible()
    assert menu.get_by_text("缩小", exact=True).is_visible()
    assert menu.get_by_text("适合屏幕", exact=True).is_visible()
    assert menu.get_by_text("缩放至50%", exact=True).is_visible()
    assert menu.get_by_text("缩放至100%", exact=True).is_visible()
    assert menu.get_by_text("缩放至800%", exact=True).is_visible()
    assert menu.get_by_text("点阵网格", exact=True).count() == 0

    menu.locator('[data-zoom-action="in"]').click()
    page.wait_for_timeout(220)
    assert zoom_percent(trigger) == 63
    assert menu.is_visible()

    menu.locator('[data-zoom-action="out"]').click()
    page.wait_for_timeout(220)
    assert zoom_percent(trigger) == 53

    menu.locator('[data-zoom-action="50"]').click()
    page.wait_for_timeout(240)
    assert zoom_percent(trigger) == 50
    menu.locator('[data-zoom-action="100"]').click()
    page.wait_for_timeout(240)
    assert zoom_percent(trigger) == 100
    menu.locator('[data-zoom-action="800"]').click()
    page.wait_for_timeout(240)
    assert zoom_percent(trigger) == 800

    menu.locator('[data-zoom-action="fit"]').click()
    page.wait_for_timeout(420)
    assert 20 <= zoom_percent(trigger) <= 35
    assert menu.is_visible()
    page.screenshot(path=str(REFERENCE_DIR / "liblib-clone-batch18-zoom-menu-desktop-929-2026-08-25.png"))

    page.keyboard.press("Escape")
    assert not menu.is_visible()
    trigger.click()
    assert menu.is_visible()
    page.mouse.click(700, 400)
    assert not menu.is_visible()

    trigger.click()
    assert menu.is_visible()
    page.get_by_role("button", name="资产管理").click()
    assert not menu.is_visible()
    asset = page.locator('[data-liblib-overlay="asset"]')
    assert asset.is_visible()

    page.locator('[data-viewport-menu-trigger="zoom"]').click()
    assert not asset.is_visible()
    assert page.locator('[data-liblib-overlay="zoom-menu"]').is_visible()
    assert_no_overflow(page)
    assert not errors, errors


def run_mobile(page: Page):
    errors = attach_errors(page)
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(400)
    trigger, menu = open_zoom_menu(page)
    assert zoom_percent(trigger) == 28
    assert menu.locator("[data-zoom-action]").count() == 6
    assert_no_overflow(page)
    page.screenshot(path=str(REFERENCE_DIR / "liblib-clone-batch18-zoom-menu-mobile-390-2026-08-25.png"))
    page.keyboard.press("Escape")
    assert not menu.is_visible()
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
        "Batch18 Playwright verification passed: source-shaped zoom menu, zoom "
        "commands, fit/fixed values, persistent action state, Escape/outside cleanup, "
        "asset mutual exclusion, mobile overflow, screenshots, console."
    )


if __name__ == "__main__":
    main()
