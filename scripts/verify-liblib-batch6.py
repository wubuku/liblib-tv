# AGED_GATE / HISTORICAL_CONTRACT（Batch 108 归因,2026-09-05）：
# 本 verifier 在基线 86673b6（Batch 96 收口）上同样失败，属既有漂移，
# 非 Batch 97-107 引入。已被 LIBTV_DIRECTOR_CURRENT_VERIFIER_MANIFEST /
# Batch 59、67-96 current gates 取代；处置见
# docs/research/LIBTV_VERIFIER_REPLACEMENT_MAP.md §4.z。
# 运行仍可用于历史快照对照，不能作为当前合同通过依据。
from pathlib import Path

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "docs" / "design-references"
URL = "http://localhost:4317"
IMAGE_ID = "i-YDfWhFlthe"


def node_box(page, node_id=IMAGE_ID):
    value = page.locator(f'.react-flow__node[data-id="{node_id}"]').bounding_box()
    assert value is not None, f"missing node box: {node_id}"
    return value


def rounded_delta(before, after):
    return round(after["x"] - before["x"]), round(after["y"] - before["y"])


def drag(page, start, end, on_midpoint=None):
    page.mouse.move(*start)
    page.mouse.down()
    page.mouse.move(
        start[0] + (end[0] - start[0]) / 2,
        start[1] + (end[1] - start[1]) / 2,
        steps=4,
    )
    if on_midpoint:
        on_midpoint()
    page.mouse.move(*end, steps=4)
    page.mouse.up()


def select_with_marquee(page):
    target = node_box(page)
    before = node_box(page)
    start = (target["x"] - 24, target["y"] - 24)
    end = (target["x"] + target["width"] + 24, target["y"] + target["height"] + 24)

    saw_selection_rect = {"value": False}

    def inspect_drag():
        saw_selection_rect["value"] = page.locator(".react-flow__selection").count() == 1

    drag(page, start, end, inspect_drag)
    page.wait_for_timeout(250)
    assert saw_selection_rect["value"], "selection rectangle did not appear"
    assert page.locator(f'.react-flow__node[data-id="{IMAGE_ID}"].selected').count() == 1
    assert rounded_delta(before, node_box(page)) == (0, 0)


def run_desktop(page):
    errors = []
    page.on("console", lambda message: errors.append(f"console:{message.type}:{message.text}") if message.type == "error" else None)
    page.on("pageerror", lambda error: errors.append(f"pageerror:{error}"))
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(400)

    flow = page.locator(".react-flow")
    assert flow.get_attribute("data-canvas-tool") == "select"
    assert flow.get_attribute("data-temporary-pan") == "false"

    select_with_marquee(page)
    page.screenshot(path=str(REFERENCE_DIR / "liblib-clone-batch6-marquee-desktop-2026-08-25.png"))

    page.keyboard.press("h")
    page.wait_for_timeout(100)
    assert flow.get_attribute("data-canvas-tool") == "pan"
    assert "cursor-grab" in (flow.get_attribute("class") or "")
    before_h_pan = node_box(page)
    drag(page, (1180, 650), (1260, 700))
    page.wait_for_timeout(250)
    h_delta = rounded_delta(before_h_pan, node_box(page))
    assert h_delta != (0, 0), h_delta

    page.keyboard.press("v")
    page.wait_for_timeout(100)
    assert flow.get_attribute("data-canvas-tool") == "select"
    assert "cursor-grab" not in (flow.get_attribute("class") or "")

    before_space_pan = node_box(page)
    page.keyboard.down("Space")
    page.wait_for_timeout(100)
    assert flow.get_attribute("data-temporary-pan") == "true"
    assert flow.get_attribute("data-canvas-tool") == "select"
    assert "cursor-grab" in (flow.get_attribute("class") or "")
    drag(page, (1120, 620), (1180, 660))
    page.wait_for_timeout(250)
    space_delta = rounded_delta(before_space_pan, node_box(page))
    assert space_delta != (0, 0), space_delta
    page.keyboard.up("Space")
    page.wait_for_timeout(100)
    assert flow.get_attribute("data-temporary-pan") == "false"
    assert flow.get_attribute("data-canvas-tool") == "select"

    page.locator(f'.react-flow__node[data-id="{IMAGE_ID}"]').click(force=True)
    page.wait_for_timeout(150)
    textarea = page.locator("textarea").first
    assert textarea.count() == 1
    textarea.click()
    page.keyboard.down("Space")
    page.wait_for_timeout(100)
    assert flow.get_attribute("data-temporary-pan") == "false"
    page.keyboard.up("Space")

    page.locator(".react-flow__pane").click(position={"x": 1180, "y": 620})
    page.keyboard.down("Space")
    page.wait_for_timeout(100)
    assert flow.get_attribute("data-temporary-pan") == "true"
    page.evaluate("window.dispatchEvent(new Event('blur'))")
    page.wait_for_timeout(100)
    assert flow.get_attribute("data-temporary-pan") == "false"
    page.keyboard.up("Space")

    page.screenshot(path=str(REFERENCE_DIR / "liblib-clone-batch6-space-pan-desktop-2026-08-25.png"))
    assert not errors, errors


def run_mobile(page):
    errors = []
    page.on("console", lambda message: errors.append(f"console:{message.type}:{message.text}") if message.type == "error" else None)
    page.on("pageerror", lambda error: errors.append(f"pageerror:{error}"))
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(400)
    assert page.locator(".react-flow").get_attribute("data-canvas-tool") == "select"
    assert page.evaluate("document.documentElement.scrollWidth <= document.documentElement.clientWidth")
    assert page.evaluate("document.body.scrollWidth <= document.body.clientWidth")
    page.screenshot(path=str(REFERENCE_DIR / "liblib-clone-batch6-mobile-390-2026-08-25.png"))
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
    print("Batch6 Playwright verification passed: marquee selection, H/V tools, Space temporary pan, input guard, blur reset, mobile overflow.")


if __name__ == "__main__":
    main()
