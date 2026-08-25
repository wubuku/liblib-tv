from pathlib import Path

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "docs" / "design-references"
URL = "http://localhost:3000"


def run_desktop(page):
    errors = []
    page.on("console", lambda message: errors.append(f"console:{message.type}:{message.text}") if message.type == "error" else None)
    page.on("pageerror", lambda error: errors.append(f"pageerror:{error}"))
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(400)

    assert page.locator(".react-flow__node").count() == 10
    assert page.locator(".react-flow__edge").count() == 11
    page.screenshot(path=str(REFERENCE_DIR / "liblib-clone-batch4-initial-2026-08-25.png"))
    image = page.locator('[data-id="i-YDfWhFlthe"]')
    video = page.locator('[data-id="v-UGQZzZOpbv"]')
    image.click(force=True)
    video.click(modifiers=["Meta"], force=True)
    page.wait_for_timeout(250)
    assert page.locator(".react-flow__node.selected").count() == 2
    assert page.get_by_text("人像质感调节", exact=True).count() == 0
    assert page.get_by_text("Seedance 2.5", exact=True).count() == 0
    page.screenshot(path=str(REFERENCE_DIR / "liblib-clone-batch4-grouping-desktop-2026-08-25.png"))

    page.keyboard.press("g")
    page.wait_for_timeout(300)
    assert page.locator(".react-flow__node").count() == 11
    assert page.locator(".react-flow__node-storyboard-group").count() == 3
    assert page.locator(".react-flow__edge").count() == 11
    page.screenshot(path=str(REFERENCE_DIR / "liblib-clone-batch4-grouped-desktop-2026-08-25.png"))

    page.keyboard.press("Shift+g")
    page.wait_for_timeout(300)
    assert page.locator(".react-flow__node").count() == 10
    assert page.locator(".react-flow__node-storyboard-group").count() == 2
    assert page.locator(".react-flow__edge").count() == 11
    page.screenshot(path=str(REFERENCE_DIR / "liblib-clone-batch4-desktop-2026-08-25.png"))

    page.keyboard.press("Delete")
    page.wait_for_timeout(300)
    assert page.locator(".react-flow__node").count() == 8
    assert page.locator(".react-flow__edge").count() == 6
    page.keyboard.press("Meta+z")
    page.wait_for_timeout(300)
    assert page.locator(".react-flow__node").count() == 10
    assert page.locator(".react-flow__edge").count() == 11

    assert not errors, errors


def run_mobile(page):
    errors = []
    page.on("console", lambda message: errors.append(f"console:{message.type}:{message.text}") if message.type == "error" else None)
    page.on("pageerror", lambda error: errors.append(f"pageerror:{error}"))
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(400)
    assert page.locator(".react-flow__node").count() == 10
    assert page.evaluate("document.documentElement.scrollWidth <= document.documentElement.clientWidth")
    assert page.evaluate("document.body.scrollWidth <= document.body.clientWidth")
    page.screenshot(path=str(REFERENCE_DIR / "liblib-clone-batch4-mobile-390-2026-08-25.png"))
    assert not errors, errors


def main():
    REFERENCE_DIR.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        desktop = browser.new_page(viewport={"width": 1440, "height": 900}, device_scale_factor=1)
        run_desktop(desktop)
        desktop.close()
        mobile = browser.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=1)
        run_mobile(mobile)
        mobile.close()
        browser.close()
    print("Batch4 Playwright verification passed: desktop grouping, ungrouping, delete/undo, mobile overflow, console.")


if __name__ == "__main__":
    main()
