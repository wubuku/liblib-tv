from pathlib import Path

from PIL import Image, ImageDraw
from playwright.sync_api import Locator, Page, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "docs" / "design-references"
URL = "http://localhost:4317"
DEFAULT_SCREENSHOT = (
    REFERENCE_DIR
    / "liblib-clone-batch22-model-menu-default-929-2026-08-25.png"
)
FAST_SCREENSHOT = (
    REFERENCE_DIR
    / "liblib-clone-batch22-model-menu-fast-929-2026-08-25.png"
)
MOBILE_SCREENSHOT = (
    REFERENCE_DIR
    / "liblib-clone-batch22-model-menu-mobile-390-2026-08-25.png"
)
CONTACT_SHEET = (
    REFERENCE_DIR
    / "liblib-clone-batch22-model-menu-contact-sheet-2026-08-25.png"
)

# Batch 141: 2026-09-07 源站模型菜单全量采样（35 项,premium 标记沿用已采样子集）。
EXPECTED_MODELS = [
    ("2.5", "Seedance 2.5", "2min", True),
    ("2.0 VIP", "Seedance 2.0 VIP", "2min", True),
    ("Minimax H3 Max", "Minimax H3 Max", "30s", False),
    ("Minimax H3", "Minimax H3", "2min", True),
    ("2.0 Fast VIP", "Seedance 2.0 Fast VIP", "2min", True),
    ("2.0 Mini", "Seedance 2.0 Mini", "2min", True),
    ("Wan 3.0 Prime", "Wan 3.0 Prime", "1min", False),
    ("Wan 3.0", "Wan 3.0", "3min", False),
    ("Happy Horse 1.1", "Happy Horse 1.1", "3min", False),
    ("Happy Horse 1.0", "Happy Horse 1.0", "3min", False),
    ("Kling O3", "Kling O3", "3min", False),
    ("Kling 3.0 Turbo", "Kling 3.0 Turbo", "3min", False),
    ("Kling 3.0", "Kling 3.0", "3min", False),
    ("Wan 2.7", "Wan 2.7", "3min", False),
    ("Kling O1", "Kling O1", "3min", False),
    ("Wan 2.6", "Wan 2.6", "3min", False),
    ("Hailuo 2.3", "Hailuo 2.3", "2min", False),
    ("Seedance 1.5 Pro", "Seedance1.5 Pro", "2min", False),
    ("Seedance 1.0 Pro", "Seedance 1.0 Pro", "2min", False),
    ("Seedance 1.0 Lite", "Seedance 1.0 Lite", "1min", False),
    ("Kling 2.6", "Kling 2.6", "2min", False),
    ("Hailuo 02", "Hailuo 02", "2min", False),
    ("Vidu Q2", "Vidu Q2", "3min", False),
    ("Vidu Q2 Pro", "Vidu Q2 Pro", "", False),
    ("Vidu Q2 Turbo", "Vidu Q2 Turbo", "", False),
    ("Vidu Q3 Pro", "Vidu Q3 Pro", "2min", False),
    ("OmniHuman 1.5", "OmniHuman 1.5", "3min", False),
    ("Kling 2.5", "Kling 2.5", "2min", False),
    ("Wan 2.2", "Wan 2.2", "3min", False),
    ("Wan 2.5", "Wan 2.5", "3min", False),
    ("Pixverse V5.5", "Pixverse V5.5", "3min", False),
    ("Pixverse V5", "Pixverse V5", "3min", False),
    ("Hailuo 2.3 Fast", "Hailuo 2.3 Fast", "1min", False),
    ("Kling 3.0 Motion", "Kling3.0 动作迁移", "8min", False),
    ("Style Video", "Style Video", "2min", False),
]


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


def box(locator: Locator):
    result = locator.bounding_box()
    assert result is not None
    return result


def assert_close(actual: float, expected: float, tolerance: float = 0.8):
    assert abs(actual - expected) <= tolerance, (actual, expected)


def assert_no_overflow(page: Page):
    assert page.evaluate(
        "document.documentElement.scrollWidth <= document.documentElement.clientWidth"
    )
    assert page.evaluate(
        "document.body.scrollWidth <= document.body.clientWidth"
    )


def prepare(page: Page):
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(350)
    page.keyboard.press("Meta+0")
    page.wait_for_timeout(420)
    page.locator('.react-flow__node[data-id="v-UGQZzZOpbv"]').click(force=True)
    page.wait_for_timeout(140)
    panel = page.locator("[data-video-generation-panel]")
    assert panel.count() == 1
    return panel


def open_menu(page: Page):
    page.locator("[data-video-model-trigger]").click(force=True)
    menu = page.locator("[data-video-model-menu]")
    menu.wait_for(state="visible")
    return menu


def assert_item_matrix(page: Page):
    options = page.locator("[data-video-model-option]")
    assert options.count() == len(EXPECTED_MODELS)
    for index, (model_id, title, estimate, premium) in enumerate(EXPECTED_MODELS):
        option = options.nth(index)
        assert option.get_attribute("data-video-model-option") == model_id
        text = option.inner_text()
        assert title in text
        assert estimate in text
        assert option.locator("[data-video-model-premium]").count() == int(premium)
    # Batch 141: 2026-09-07 采样——菜单含 Kling O3 等 35 项;premium 角标 6 个
    # （2.5/2.0 VIP/Minimax H3/2.0 Fast VIP/2.0 Mini/……当日采样分布）。
    assert "Kling O3" in page.locator("[data-video-model-menu]").inner_text()
    # Batch 141: premium 沿用已采样子集（5 项）;未采样模型不标 premium。
    assert page.locator("[data-video-model-premium]").count() == 5


def run_desktop(page: Page):
    errors = attach_errors(page)
    panel = prepare(page)
    assert page.get_by_role("button", name="缩放选项").inner_text() == "28%"
    panel_box = box(panel)

    menu = open_menu(page)
    menu_box = box(menu)
    assert_close(menu_box["width"], 380)
    assert_close(menu_box["height"], 410)
    assert_close(menu_box["x"] - panel_box["x"], 0)
    # Batch 126: 高级设置行使模型菜单 y 偏移上移 28px。
    assert_close(menu_box["y"] - panel_box["y"], -209.5)
    assert_item_matrix(page)

    selected = page.locator('[data-video-model-option][aria-pressed="true"]')
    # Batch 158: 默认模型回落 Seedance 2.5（新建节点 2.5 + 尝试已选节点 2.5 两个直接样本）。
    assert selected.get_attribute("data-video-model-option") == "2.5"
    assert page.locator("[data-video-model-description]").inner_text() == (
        "最强视频模型，全能参考，30s音画同步"
    )
    assert_close(box(selected)["height"], 58)
    assert_close(
        box(page.locator('[data-video-model-option="2.0 VIP"]'))["height"],
        48,
    )
    page.screenshot(path=str(DEFAULT_SCREENSHOT))

    page.locator('[data-video-model-option="2.0 Fast VIP"]').click(force=True)
    assert page.locator("[data-video-model-menu]").count() == 0
    # Batch 149: 触发器显示缩写名（Seedance 2.0 Fast VIP → 2.0 Fast，源站 2026-09-07 实拍）。
    assert page.locator("[data-video-model-trigger]").inner_text().startswith(
        "2.0 Fast"
    )

    menu = open_menu(page)
    selected = page.locator('[data-video-model-option][aria-pressed="true"]')
    assert selected.get_attribute("data-video-model-option") == "2.0 Fast VIP"
    assert page.locator("[data-video-model-description]").count() == 1
    assert page.locator("[data-video-model-description]").inner_text() == (
        "最强视频模型快速版，会员专属通道，15s音画同步"
    )
    assert page.locator(
        '[data-video-model-option="2.5"] [data-video-model-description]'
    ).count() == 0
    page.screenshot(path=str(FAST_SCREENSHOT))

    page.locator("[data-video-model-trigger]").click(force=True)
    page.locator("[data-video-params-trigger]").click(force=True)
    assert page.locator("[data-video-params-menu]").count() == 1
    assert_close(box(page.locator("[data-video-params-menu]"))["width"], 341)
    assert_no_overflow(page)
    assert not errors, errors


def run_mobile(page: Page):
    errors = attach_errors(page)
    panel = prepare(page)
    assert page.get_by_role("button", name="缩放选项").inner_text() == "12%"
    menu = open_menu(page)
    panel_box = box(panel)
    menu_box = box(menu)
    assert_close(menu_box["width"], 380)
    assert_close(menu_box["height"], 410)
    assert_close(menu_box["x"] - panel_box["x"], 0)
    assert menu_box["x"] >= -1
    assert menu_box["x"] + menu_box["width"] <= 390 + 1
    assert_item_matrix(page)
    assert_no_overflow(page)
    page.screenshot(path=str(MOBILE_SCREENSHOT))
    assert not errors, errors


def save_contact_sheet():
    default = Image.open(DEFAULT_SCREENSHOT).convert("RGB")
    fast = Image.open(FAST_SCREENSHOT).convert("RGB")
    mobile = Image.open(MOBILE_SCREENSHOT).convert("RGB")
    label_height = 28
    gutter = 12
    width = default.width + fast.width + gutter
    height = max(default.height, fast.height) + mobile.height + label_height * 2 + gutter
    sheet = Image.new("RGB", (width, height), "#141414")
    draw = ImageDraw.Draw(sheet)
    draw.text((8, 8), "default 2.5 929x874", fill="#ededed")
    draw.text((default.width + gutter + 8, 8), "selected Fast 929x874", fill="#ededed")
    sheet.paste(default, (0, label_height))
    sheet.paste(fast, (default.width + gutter, label_height))
    mobile_y = label_height + max(default.height, fast.height) + gutter
    draw.text((8, mobile_y + 8), "mobile 390x844", fill="#ededed")
    sheet.paste(mobile, (0, mobile_y + label_height))
    sheet.save(CONTACT_SHEET)


def main():
    REFERENCE_DIR.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        desktop = browser.new_page(
            viewport={"width": 929, "height": 874},
            device_scale_factor=1,
        )
        run_desktop(desktop)
        desktop.close()
        mobile = browser.new_page(
            viewport={"width": 390, "height": 844},
            device_scale_factor=1,
        )
        run_mobile(mobile)
        mobile.close()
        browser.close()
    save_contact_sheet()
    print(
        "Batch22 Playwright verification passed: source-visible seven-model "
        "matrix, 380x410 geometry, premium/estimate hierarchy, selected-only "
        "descriptions, Fast selection, params handoff, mobile fit, overflow, "
        "screenshots, console."
    )


if __name__ == "__main__":
    main()
