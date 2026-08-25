from pathlib import Path

from playwright.sync_api import Page, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "docs" / "design-references"
URL = "http://localhost:3000"


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


def assert_graph(page: Page, nodes: int, edges: int):
    assert page.locator(".react-flow__node").count() == nodes
    assert page.locator(".react-flow__edge").count() == edges


def open_storyboard(page: Page):
    page.locator('button[aria-label="分镜"]').evaluate("(element) => element.click()")
    page.wait_for_timeout(120)
    assert page.locator("[data-storyboard-board]").is_visible()
    assert page.locator('[data-liblib-overlay="agent"]').count() == 1


def run_desktop(page: Page):
    errors = attach_errors(page)
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(400)
    assert_graph(page, 10, 11)

    open_storyboard(page)
    assert page.locator('[data-storyboard-key-group="image"] [data-storyboard-card]').count() == 5
    assert page.locator('[data-storyboard-key-group="text"] [data-storyboard-card]').count() == 1
    assert page.locator('[data-storyboard-column="image"] [data-storyboard-card]').count() == 5
    assert page.locator('[data-storyboard-column="video"] [data-storyboard-card]').count() == 1

    image_card = page.locator('[data-storyboard-column="image"] [data-storyboard-card="i-YDfWhFlthe"]')
    image_card.click()
    assert image_card.get_attribute("aria-pressed") == "true"

    script_card = page.locator('[data-storyboard-key-group="text"] [data-storyboard-card="t-9j2MoccxBj"]')
    script_card.click()
    assert script_card.get_attribute("aria-pressed") == "true"

    page.locator("[data-storyboard-return]").click()
    assert not page.locator("[data-storyboard-board]").is_visible()
    assert_graph(page, 10, 11)
    assert page.locator('.react-flow__node[data-id="t-9j2MoccxBj"].selected').count() == 1

    page.locator('button[aria-label="分镜"]').evaluate("(element) => element.click()")
    page.screenshot(path=str(REFERENCE_DIR / "liblib-clone-batch13-storyboard-desktop-929-2026-08-25.png"))
    page.locator("[data-storyboard-return]").click()

    page.get_by_role("button", name="画布 2").click()
    page.locator('[data-liblib-overlay="canvas-dropdown"]').get_by_role("button", name="画布 1").click()
    open_storyboard(page)
    assert page.locator('[data-storyboard-key-group="image"] [data-storyboard-card]').count() == 0
    assert page.locator('[data-storyboard-key-group="text"] [data-storyboard-card]').count() == 0
    assert page.get_by_text("当前画布暂无图片素材", exact=True).is_visible()
    assert page.get_by_text("当前画布暂无视频素材", exact=True).is_visible()

    page.screenshot(path=str(REFERENCE_DIR / "liblib-clone-batch13-storyboard-empty-desktop-929-2026-08-25.png"))
    assert not errors, errors


def run_mobile(page: Page):
    errors = attach_errors(page)
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(400)
    open_storyboard(page)
    assert page.locator('[data-storyboard-column="image"] [data-storyboard-card]').count() == 5
    assert page.evaluate("document.documentElement.scrollWidth <= document.documentElement.clientWidth")
    assert page.evaluate("document.body.scrollWidth <= document.body.clientWidth")
    page.screenshot(path=str(REFERENCE_DIR / "liblib-clone-batch13-storyboard-mobile-390-2026-08-25.png"))
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
        "Batch13 Playwright verification passed: storyboard data projection, "
        "key elements, card selection, workbench round-trip, empty canvas, "
        "mobile overflow, screenshots, console."
    )


if __name__ == "__main__":
    main()
