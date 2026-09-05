from pathlib import Path

from playwright.sync_api import Page, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "docs" / "design-references"
URL = "http://localhost:4317"


# Batch 103: 源站 2026-09-05 复核将顶栏模式切换更名为 工作流/故事板（aria 已同步）。
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


def open_agent(page: Page):
    page.get_by_role("button", name="Agent", exact=True).click()
    assert page.locator('[data-liblib-overlay="agent"]').is_visible()


def run_desktop(page: Page):
    errors = attach_errors(page)
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(400)
    open_agent(page)

    agent = page.locator('[data-liblib-overlay="agent"]')
    assert agent.get_by_text("新对话", exact=True).is_visible()
    assert agent.locator("[data-agent-skill]").count() == 4
    assert agent.locator("[data-agent-notification]").is_visible()
    assert agent.locator("[data-agent-composer]").is_visible()

    first_skill = agent.locator('[data-agent-skill="pixar"]')
    first_skill.click()
    assert first_skill.get_attribute("aria-pressed") == "true"
    # Batch 97: 源站 2026-09-05 复核将首张 Skill 卡更名为「皮克斯动画广告」。
    assert agent.locator("textarea").input_value() == "皮克斯动画广告"

    agent.locator("[data-agent-refresh]").click()
    assert agent.locator('[data-agent-skill="character"]').count() == 1
    assert agent.locator('[data-agent-skill="pixar"]').count() == 0

    agent.locator("[data-agent-notification-enable]").click()
    assert not agent.locator("[data-agent-notification]").is_visible()

    agent.locator("textarea").fill("检查当前画布的镜头连续性")
    agent.locator("[data-agent-send]").click()
    assert agent.locator("[data-agent-status]").is_visible()
    assert "本地预览" in agent.locator("[data-agent-status]").inner_text()

    page.screenshot(path=str(REFERENCE_DIR / "liblib-clone-batch14-agent-desktop-929-2026-08-25.png"))

    # Batch 97: 源站 2026-09-05 复核将关闭按钮 aria 收敛为「关闭」。
    agent.get_by_role("button", name="关闭", exact=True).click()
    assert not agent.is_visible()
    # Batch 121: 源站 2026-09-06 顶栏分享按钮 aria 为「发布与分享」。
    page.get_by_role("button", name="发布与分享").click()
    share = page.locator('[data-liblib-overlay="share"]')
    assert share.is_visible()
    assert share.get_by_text("发布与分享", exact=True).is_visible()
    assert share.get_by_text("在LibTV上发布", exact=True).is_visible()
    assert share.get_by_text("分享链接", exact=True).is_visible()
    share.locator('[data-share-action="publish"]').click()
    assert "发布服务未连接" in share.locator("[data-share-status]").inner_text()
    share.locator('[data-share-action="link"]').click()
    assert "分享链接服务未连接" in share.locator("[data-share-status]").inner_text()
    page.screenshot(path=str(REFERENCE_DIR / "liblib-clone-batch14-share-desktop-929-2026-08-25.png"))
    assert not errors, errors


def run_mobile(page: Page):
    errors = attach_errors(page)
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(400)
    assert page.evaluate("document.documentElement.scrollWidth <= document.documentElement.clientWidth")
    assert page.evaluate("document.body.scrollWidth <= document.body.clientWidth")
    page.locator('button[aria-label="故事板"]').evaluate("(element) => element.click()")
    page.wait_for_timeout(120)
    assert page.locator("[data-storyboard-board]").is_visible()
    assert page.evaluate("document.documentElement.scrollWidth <= document.documentElement.clientWidth")
    assert page.evaluate("document.body.scrollWidth <= document.body.clientWidth")
    page.screenshot(path=str(REFERENCE_DIR / "liblib-clone-batch14-mobile-390-2026-08-25.png"))
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
        "Batch14 Playwright verification passed: Agent source-shaped shell, "
        "Skill selection/refresh, notification/composer feedback, share copy/status, "
        "mobile overflow, screenshots, console."
    )


if __name__ == "__main__":
    main()

