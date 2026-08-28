from pathlib import Path

from playwright.sync_api import Page, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "docs" / "design-references"
URL = "http://localhost:4317"

NODE_IDS = {
    "female": "i-lBzmo67AHv",
    "cafe": "i-vxeeCnxySa",
    "male": "i-1FQ9tErTcC",
    "coffee": "i-dnwoZQ7jsG",
    "execution": "b-bTLLuU4w5q",
    "storyboard": "i-YDfWhFlthe",
    "image_group": "g-245IDFh8sB",
    "video_group": "g-EFbbHpwq5w",
    "video": "v-UGQZzZOpbv",
    "script": "t-9j2MoccxBj",
}


def node_locator(page: Page, node_id: str):
    return page.locator(f'.react-flow__node[data-id="{node_id}"]')


def node_box(page: Page, node_id: str):
    value = node_locator(page, node_id).bounding_box()
    assert value is not None, f"missing node box: {node_id}"
    return value


def node_transforms(page: Page):
    return {
        node_id: node_locator(page, node_id).evaluate("(node) => node.style.transform")
        for node_id in NODE_IDS.values()
    }


def close_to(actual: float, expected: float, tolerance: float = 3):
    assert abs(actual - expected) <= tolerance, (actual, expected)


def trigger_organize(page: Page):
    page.keyboard.press("Alt+Shift+f")
    page.wait_for_timeout(300)
    assert page.locator("[data-organize-confirmation]").count() == 1


def attach_error_collection(page: Page):
    errors = []
    page.on(
        "console",
        lambda message: errors.append(f"console:{message.type}:{message.text}")
        if message.type == "error"
        else None,
    )
    page.on("pageerror", lambda error: errors.append(f"pageerror:{error}"))
    return errors


def assert_no_overflow(page: Page):
    assert page.evaluate(
        "document.documentElement.scrollWidth <= document.documentElement.clientWidth"
    )
    assert page.evaluate("document.body.scrollWidth <= document.body.clientWidth")


def run_source_viewport(page: Page):
    errors = attach_error_collection(page)
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(400)
    baseline_transforms = node_transforms(page)
    baseline_viewport = page.locator(".react-flow__viewport").evaluate(
        "(node) => node.style.transform"
    )

    trigger_organize(page)
    assert page.locator(".react-flow__node").count() == 10
    assert page.locator(".react-flow__edge").count() == 11
    assert page.get_by_role("button", name="缩放选项").inner_text() == "28%"

    expected_positions = {
        "female": (72, 49),
        "cafe": (48, 177),
        "male": (72, 304),
        "coffee": (48, 432),
        "execution": (330, 182),
        "storyboard": (305, 344),
        "image_group": (538, 154),
        "video_group": (538, 316),
        "video": (558, 336),
        "script": (782, 49),
    }
    for name, (expected_x, expected_y) in expected_positions.items():
        box = node_box(page, NODE_IDS[name])
        close_to(box["x"], expected_x)
        close_to(box["y"], expected_y)

    confirmation = page.locator("[data-organize-confirmation]")
    confirmation_box = confirmation.bounding_box()
    assert confirmation_box is not None
    close_to(confirmation_box["x"], 49, 1)
    close_to(confirmation_box["y"], 733, 1)
    close_to(confirmation_box["width"], 168, 1)
    close_to(confirmation_box["height"], 88, 1)
    question_box = confirmation.get_by_text("是否保留此次整理结果？", exact=True).bounding_box()
    restore_box = confirmation.get_by_role("button", name="还原").bounding_box()
    keep_box = confirmation.get_by_role("button", name="保留").bounding_box()
    assert question_box is not None and restore_box is not None and keep_box is not None
    assert restore_box["y"] > question_box["y"]
    assert keep_box["y"] == restore_box["y"]
    assert keep_box["x"] > restore_box["x"]

    page.screenshot(
        path=str(
            REFERENCE_DIR
            / "liblib-clone-batch7-organize-929-2026-08-25.png"
        )
    )

    confirmation.get_by_role("button", name="还原").click()
    page.wait_for_timeout(250)
    assert page.locator("[data-organize-confirmation]").count() == 0
    assert node_transforms(page) == baseline_transforms
    assert (
        page.locator(".react-flow__viewport").evaluate("(node) => node.style.transform")
        == baseline_viewport
    )

    trigger_organize(page)
    organized_transforms = node_transforms(page)
    page.locator("[data-organize-confirmation]").get_by_role(
        "button", name="保留"
    ).click()
    page.wait_for_timeout(150)
    assert page.locator("[data-organize-confirmation]").count() == 0
    assert node_transforms(page) == organized_transforms

    page.keyboard.press("Meta+z")
    page.wait_for_timeout(250)
    assert node_transforms(page) == baseline_transforms
    page.keyboard.press("Meta+Shift+z")
    page.wait_for_timeout(250)
    assert node_transforms(page) == organized_transforms
    assert_no_overflow(page)
    assert not errors, errors


def run_desktop(page: Page):
    errors = attach_error_collection(page)
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(400)
    trigger_organize(page)
    assert page.get_by_role("button", name="缩放选项").inner_text() == "46%"
    confirmation_box = page.locator("[data-organize-confirmation]").bounding_box()
    assert confirmation_box is not None
    close_to(confirmation_box["x"], 49, 1)
    close_to(confirmation_box["y"] + confirmation_box["height"], 900 - 53, 1)
    assert_no_overflow(page)
    page.screenshot(
        path=str(
            REFERENCE_DIR
            / "liblib-clone-batch7-organize-desktop-2026-08-25.png"
        )
    )
    assert not errors, errors


def run_mobile(page: Page):
    errors = attach_error_collection(page)
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(400)
    trigger_organize(page)
    assert page.get_by_role("button", name="缩放选项").inner_text() == "10%"
    confirmation_box = page.locator("[data-organize-confirmation]").bounding_box()
    assert confirmation_box is not None
    close_to(confirmation_box["x"], 12, 1)
    close_to(confirmation_box["y"] + confirmation_box["height"], 844 - 106, 1)
    assert_no_overflow(page)
    page.screenshot(
        path=str(
            REFERENCE_DIR
            / "liblib-clone-batch7-organize-mobile-390-2026-08-25.png"
        )
    )
    assert not errors, errors


def main():
    REFERENCE_DIR.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        source_viewport = browser.new_page(
            viewport={"width": 929, "height": 874}, device_scale_factor=1
        )
        run_source_viewport(source_viewport)
        source_viewport.close()
        desktop = browser.new_page(
            viewport={"width": 1440, "height": 900}, device_scale_factor=1
        )
        run_desktop(desktop)
        desktop.close()
        mobile = browser.new_page(
            viewport={"width": 390, "height": 844}, device_scale_factor=1
        )
        run_mobile(mobile)
        mobile.close()
        browser.close()
    print(
        "Batch7 Playwright verification passed: source-like organize topology, "
        "confirmation geometry, restore/keep, undo/redo, responsive overflow, console."
    )


if __name__ == "__main__":
    main()
