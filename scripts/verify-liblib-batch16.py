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


def open_canvas_menu(page: Page):
    page.locator("[data-canvas-trigger]").click()
    assert page.locator('[data-liblib-overlay="canvas-dropdown"]').is_visible()


def assert_no_overflow(page: Page):
    assert page.evaluate("document.documentElement.scrollWidth <= document.documentElement.clientWidth")
    assert page.evaluate("document.body.scrollWidth <= document.body.clientWidth")


def run_desktop(page: Page):
    errors = attach_errors(page)
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(400)

    trigger = page.locator("[data-canvas-trigger]")
    assert trigger.inner_text().strip() == "画布 2"
    open_canvas_menu(page)
    menu = page.locator('[data-liblib-overlay="canvas-dropdown"]')
    assert menu.locator("[data-canvas-project]").is_visible()
    assert "当前项目" in menu.locator("[data-canvas-project]").inner_text()
    assert "未命名项目" in menu.locator("[data-canvas-project]").inner_text()
    assert menu.locator("[data-canvas-new]").is_visible()
    assert menu.locator('[data-canvas-active="true"]').count() == 1
    page.screenshot(path=str(REFERENCE_DIR / "liblib-clone-batch16-canvas-menu-desktop-929-2026-08-25.png"))

    menu.get_by_role("button", name="未命名项目", exact=True).click()
    project_input = menu.locator("[data-canvas-project-input]")
    project_input.fill("咖啡馆项目")
    project_input.press("Enter")
    assert "咖啡馆项目" in menu.locator("[data-canvas-project]").inner_text()

    menu.locator('[data-canvas-row="canvas-1"] button').first.click()
    assert not menu.is_visible()
    assert trigger.inner_text().strip() == "画布 1"

    open_canvas_menu(page)
    menu = page.locator('[data-liblib-overlay="canvas-dropdown"]')
    menu.locator("[data-canvas-new]").click()
    assert not menu.is_visible()
    assert trigger.inner_text().strip() == "画布 3"

    open_canvas_menu(page)
    menu = page.locator('[data-liblib-overlay="canvas-dropdown"]')
    # Batch 114: 行结构迁移 — hover 行 + 更多操作按钮；菜单项更名为 画布 动词；副本命名 副本{n}；删除有确认框；fallback 取创建序前一画布。
    row3 = menu.locator('[data-canvas-row="canvas-3"]')
    row3.hover()
    page.wait_for_timeout(250)
    row3.locator("button[aria-label='更多操作']").click(force=True)
    page.wait_for_timeout(300)
    menu.get_by_role("button", name="复制画布", exact=True).click()
    page.wait_for_timeout(400)
    assert not menu.is_visible()
    print("DEBUG trigger:", repr(trigger.inner_text().strip()))
    assert trigger.inner_text().strip() == "画布 3副本1"

    open_canvas_menu(page)
    menu = page.locator('[data-liblib-overlay="canvas-dropdown"]')
    row4 = menu.locator('[data-canvas-row="canvas-4"]')
    row4.hover()
    page.wait_for_timeout(250)
    row4.locator("button[aria-label='更多操作']").click(force=True)
    page.wait_for_timeout(300)
    menu.get_by_role("button", name="重命名画布", exact=True).click()
    rename_input = menu.locator('input[type="text"]').last
    rename_input.fill("主画布")
    rename_input.press("Enter")
    page.wait_for_timeout(300)
    assert not menu.is_visible()
    assert trigger.inner_text().strip() == "主画布"

    open_canvas_menu(page)
    menu = page.locator('[data-liblib-overlay="canvas-dropdown"]')
    row4 = menu.locator('[data-canvas-row="canvas-4"]')
    row4.hover()
    page.wait_for_timeout(250)
    row4.locator("button[aria-label='更多操作']").click(force=True)
    page.wait_for_timeout(300)
    menu.get_by_role("button", name="删除画布", exact=True).click()
    page.wait_for_timeout(400)
    confirm = page.locator("[data-canvas-delete-confirm]")
    assert confirm.is_visible()
    confirm.get_by_text("确认", exact=True).click()
    page.wait_for_timeout(500)
    # Batch 114: 删除活动画布回退到创建序前一画布（canvas-3，名称 画布 3），不再是画布 1。
    assert trigger.inner_text().strip() == "画布 3"

    open_canvas_menu(page)
    page.keyboard.press("Escape")
    assert not page.locator('[data-liblib-overlay="canvas-dropdown"]').is_visible()
    open_canvas_menu(page)
    page.mouse.click(700, 400)
    assert not page.locator('[data-liblib-overlay="canvas-dropdown"]').is_visible()
    assert_no_overflow(page)
    assert not errors, errors


def run_mobile(page: Page):
    errors = attach_errors(page)
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(400)
    open_canvas_menu(page)
    menu = page.locator('[data-liblib-overlay="canvas-dropdown"]')
    assert menu.locator("[data-canvas-project]").is_visible()
    assert_no_overflow(page)
    page.screenshot(path=str(REFERENCE_DIR / "liblib-clone-batch16-canvas-menu-mobile-390-2026-08-25.png"))
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
        "Batch16 Playwright verification passed: project metadata lifecycle, canvas "
        "create/switch/duplicate/rename/delete, close cleanup, Escape, overflow, "
        "screenshots, console."
    )


if __name__ == "__main__":
    main()
