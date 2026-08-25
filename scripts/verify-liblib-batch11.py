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


def overlay(page: Page, name: str):
    return page.locator(f'[data-liblib-overlay="{name}"]')


def assert_only_overlay(page: Page, expected: str):
    names = [
        "primary:move",
        "primary:toolbox",
        "primary:material",
        "primary:character",
        "primary:history",
        "primary:tutorial",
        "add-node",
        "shortcuts",
        "canvas-dropdown",
        "asset",
        "share",
        "agent",
    ]
    visible = [name for name in names if overlay(page, name).is_visible()]
    assert visible == [expected], visible


def assert_graph_unchanged(page: Page):
    assert page.locator(".react-flow__node").count() == 10
    assert page.locator(".react-flow__edge").count() == 11


def run_desktop(page: Page):
    errors = attach_errors(page)
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(400)
    assert_graph_unchanged(page)

    page.get_by_role("button", name="打开工具箱").click()
    assert_only_overlay(page, "primary:toolbox")

    page.get_by_role("button", name="Agent", exact=True).click()
    assert_only_overlay(page, "agent")

    page.get_by_role("button", name="分享").click()
    assert_only_overlay(page, "share")

    page.get_by_role("button", name="资产管理").click()
    assert_only_overlay(page, "asset")

    page.get_by_role("button", name="画布 2").click()
    assert_only_overlay(page, "canvas-dropdown")

    page.get_by_role("button", name="添加节点").click()
    assert_only_overlay(page, "add-node")

    page.get_by_role("button", name="快捷键").click()
    assert_only_overlay(page, "shortcuts")

    page.get_by_role("button", name="角色库").click()
    assert_only_overlay(page, "primary:character")
    page.get_by_role("button", name="关闭角色库").click()
    assert not overlay(page, "primary:character").is_visible()

    page.get_by_role("button", name="教程与帮助").click()
    assert_only_overlay(page, "primary:tutorial")

    page.keyboard.press("Escape")
    assert not any(overlay(page, name).is_visible() for name in (
        "primary:tutorial",
        "add-node",
        "shortcuts",
        "canvas-dropdown",
        "asset",
        "share",
        "agent",
    ))

    page.get_by_role("button", name="分镜").click()
    page.wait_for_timeout(150)
    assert_only_overlay(page, "agent")
    assert page.get_by_text("角色与物件", exact=True).is_visible()

    page.get_by_role("button", name="工作台").click()
    page.wait_for_timeout(150)
    assert not overlay(page, "agent").is_visible()
    assert page.locator(".react-flow__node").count() == 10
    assert page.locator(".react-flow__edge").count() == 11

    page.screenshot(
        path=str(REFERENCE_DIR / "liblib-clone-batch11-overlay-lifecycle-desktop-929-2026-08-25.png")
    )
    assert not errors, errors


def run_mobile(page: Page):
    errors = attach_errors(page)
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(400)
    assert_graph_unchanged(page)

    page.get_by_role("button", name="打开工具箱").click()
    assert_only_overlay(page, "primary:toolbox")
    page.get_by_role("button", name="快捷键").click()
    assert_only_overlay(page, "shortcuts")
    page.keyboard.press("Escape")
    assert not overlay(page, "shortcuts").is_visible()

    assert page.evaluate("document.documentElement.scrollWidth <= document.documentElement.clientWidth")
    assert page.evaluate("document.body.scrollWidth <= document.body.clientWidth")
    page.screenshot(
        path=str(REFERENCE_DIR / "liblib-clone-batch11-overlay-lifecycle-mobile-390-2026-08-25.png")
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
        "Batch11 Playwright verification passed: mutually exclusive LibTV "
        "overlays, Escape cleanup, storyboard Agent lifecycle, graph "
        "preservation, mobile overflow, screenshots, console."
    )


if __name__ == "__main__":
    main()
