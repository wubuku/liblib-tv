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


def open_add_node(page: Page):
    page.get_by_role("button", name="添加节点").click()
    assert page.locator('[data-liblib-overlay="add-node"]').is_visible()


def run_desktop(page: Page):
    errors = attach_errors(page)
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(400)

    initial_nodes = page.locator(".react-flow__node").count()
    initial_text = page.locator(".react-flow__node-text").count()
    open_add_node(page)
    panel = page.locator('[data-liblib-overlay="add-node"]')
    assert panel.locator("[data-add-node-entry]").count() == 9
    assert panel.locator('[data-add-node-entry="audio"]').is_visible()
    assert panel.locator('[data-add-node-entry="material"]').is_visible()
    assert panel.locator('[data-add-node-entry="script"] [data-add-node-arrow]').count() == 1
    assert panel.locator('[data-add-node-entry="material"] [data-add-node-arrow]').count() == 1
    page.screenshot(path=str(REFERENCE_DIR / "liblib-clone-batch15-add-node-menu-desktop-929-2026-08-25.png"))

    panel.locator('[data-add-node-resource="upload"]').click()
    assert "上传服务未连接" in panel.locator("[data-add-node-status]").inner_text()
    panel.locator('[data-add-node-resource="history"]').click()
    assert "生成历史未连接" in panel.locator("[data-add-node-status]").inner_text()

    panel.locator('[data-add-node-entry="material"]').click()
    submenu = page.locator('[data-add-node-submenu="material"]')
    assert submenu.is_visible()
    submenu.get_by_role("button", name="预设素材库").click()
    assert not page.locator('[data-liblib-overlay="add-node"]').is_visible()
    assert page.locator('[data-liblib-overlay="primary:material"]').is_visible()

    page.keyboard.press("Escape")
    assert not page.locator('[data-liblib-overlay="primary:material"]').is_visible()
    open_add_node(page)
    panel = page.locator('[data-liblib-overlay="add-node"]')
    panel.locator('[data-add-node-entry="audio"]').click()
    assert not page.locator('[data-liblib-overlay="add-node"]').is_visible()
    assert page.locator(".react-flow__node-audio").count() == 1
    assert page.locator(".react-flow__node-text").count() == initial_text
    assert page.locator(".react-flow__node-audio.selected").count() == 1
    assert page.locator(".react-flow__node").count() == initial_nodes + 1

    page.screenshot(path=str(REFERENCE_DIR / "liblib-clone-batch15-add-node-desktop-929-2026-08-25.png"))
    assert not errors, errors


def run_mobile(page: Page):
    errors = attach_errors(page)
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(400)
    open_add_node(page)
    panel = page.locator('[data-liblib-overlay="add-node"]')
    assert panel.locator("[data-add-node-entry]").count() == 9
    panel.locator('[data-add-node-entry="material"]').click()
    assert page.locator('[data-add-node-submenu="material"]').is_visible()
    assert page.evaluate("document.documentElement.scrollWidth <= document.documentElement.clientWidth")
    assert page.evaluate("document.body.scrollWidth <= document.body.clientWidth")
    page.keyboard.press("Escape")
    assert not page.locator('[data-liblib-overlay="add-node"]').is_visible()
    page.screenshot(path=str(REFERENCE_DIR / "liblib-clone-batch15-add-node-mobile-390-2026-08-25.png"))
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
        "Batch15 Playwright verification passed: nine add-node entries, "
        "audio node type, material submenu, resource feedback, Escape cleanup, "
        "mobile overflow, screenshots, console."
    )


if __name__ == "__main__":
    main()
