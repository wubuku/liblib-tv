from pathlib import Path

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "docs" / "design-references"
URL = "http://localhost:3000"
IMAGE_ID = "i-YDfWhFlthe"
VIDEO_ID = "v-UGQZzZOpbv"


def box(page, node_id):
    value = page.locator(f'[data-id="{node_id}"]').bounding_box()
    assert value is not None, f"missing visible node box: {node_id}"
    return value


def center(rect):
    return rect["x"] + rect["width"] / 2, rect["y"] + rect["height"] / 2


def drag(page, node_id, dx, dy):
    x, y = center(box(page, node_id))
    page.mouse.move(x, y)
    page.mouse.down()
    page.mouse.move(x + dx / 2, y + dy / 2, steps=4)
    page.mouse.move(x + dx, y + dy, steps=4)
    page.mouse.up()


def select_image_and_video(page):
    page.locator(f'[data-id="{IMAGE_ID}"]').click(force=True)
    page.locator(f'[data-id="{VIDEO_ID}"]').click(modifiers=["Meta"], force=True)
    page.wait_for_timeout(250)
    assert page.locator(".react-flow__node.selected").count() == 2
    assert page.get_by_text("人像质感调节", exact=True).count() == 0
    assert page.get_by_text("Seedance 2.5", exact=True).count() == 0


def node_rects_with_text(page, text):
    return page.locator(".react-flow__node").evaluate_all(
        """(nodes, text) => nodes
          .filter((node) => (node.textContent || "").includes(text))
          .map((node) => {
            const rect = node.getBoundingClientRect();
            return { id: node.dataset.id || "", x: rect.x, y: rect.y, width: rect.width, height: rect.height };
          })""",
        text,
    )


def run_group_duplicate(page):
    errors = []
    page.on("console", lambda message: errors.append(f"console:{message.type}:{message.text}") if message.type == "error" else None)
    page.on("pageerror", lambda error: errors.append(f"pageerror:{error}"))
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(400)

    select_image_and_video(page)
    page.keyboard.press("g")
    page.wait_for_timeout(300)
    assert page.locator(".react-flow__node").count() == 11
    assert page.locator(".react-flow__node-storyboard-group").count() == 3
    grouped_image = node_rects_with_text(page, "分镜 #2")
    grouped_video = node_rects_with_text(page, "分镜视频-#9")
    grouped_groups = page.locator(".react-flow__node-storyboard-group").evaluate_all(
        """(nodes) => nodes.map((node) => {
          const rect = node.getBoundingClientRect();
          return { text: node.textContent || "", x: rect.x, y: rect.y, width: rect.width, height: rect.height };
        })"""
    )
    assert len(grouped_image) == 1
    assert len(grouped_video) == 1
    assert any("组合节点" in item["text"] for item in grouped_groups)

    page.keyboard.press("Meta+d")
    page.wait_for_timeout(350)
    assert page.locator(".react-flow__node").count() == 14
    assert page.locator(".react-flow__node-storyboard-group").count() == 4
    assert page.locator(".react-flow__edge").count() == 12
    assert page.locator(".react-flow__node.selected").count() == 1

    copied_groups = page.locator(".react-flow__node-storyboard-group").evaluate_all(
        """(nodes) => nodes.map((node) => {
          const rect = node.getBoundingClientRect();
          return { text: node.textContent || "", x: rect.x, y: rect.y, width: rect.width, height: rect.height };
        })"""
    )
    original_group = next(item for item in copied_groups if item["text"].strip() == "组合节点")
    copied_group = next(item for item in copied_groups if "组合节点 副本" in item["text"])
    delta = (copied_group["x"] - original_group["x"], copied_group["y"] - original_group["y"])
    assert abs(delta[0]) > 0 and abs(delta[1]) > 0

    copied_images = node_rects_with_text(page, "分镜 #2")
    copied_videos = node_rects_with_text(page, "分镜视频-#9")
    assert len(copied_images) == 2
    assert len(copied_videos) == 2
    assert any(
        abs((item["x"] - grouped_image[0]["x"]) - delta[0]) < 2
        and abs((item["y"] - grouped_image[0]["y"]) - delta[1]) < 2
        for item in copied_images
    )
    assert any(
        abs((item["x"] - grouped_video[0]["x"]) - delta[0]) < 2
        and abs((item["y"] - grouped_video[0]["y"]) - delta[1]) < 2
        for item in copied_videos
    )

    page.keyboard.press("Meta+z")
    page.wait_for_timeout(300)
    assert page.locator(".react-flow__node").count() == 11
    page.keyboard.press("Meta+Shift+z")
    page.wait_for_timeout(300)
    assert page.locator(".react-flow__node").count() == 14
    assert page.locator(".react-flow__node.selected").count() == 0
    page.screenshot(path=str(REFERENCE_DIR / "liblib-clone-batch5-group-duplicate-desktop-2026-08-25.png"))
    assert not errors, errors


def run_movement(page):
    errors = []
    page.on("console", lambda message: errors.append(f"console:{message.type}:{message.text}") if message.type == "error" else None)
    page.on("pageerror", lambda error: errors.append(f"pageerror:{error}"))
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(400)

    select_image_and_video(page)
    before_image = box(page, IMAGE_ID)
    before_video = box(page, VIDEO_ID)
    drag(page, IMAGE_ID, 72, 36)
    page.wait_for_timeout(300)

    after_image = box(page, IMAGE_ID)
    after_video = box(page, VIDEO_ID)
    image_delta = (round(after_image["x"] - before_image["x"]), round(after_image["y"] - before_image["y"]))
    video_delta = (round(after_video["x"] - before_video["x"]), round(after_video["y"] - before_video["y"]))
    assert image_delta == video_delta, (image_delta, video_delta)
    assert image_delta != (0, 0), image_delta

    page.keyboard.press("Meta+z")
    page.wait_for_timeout(300)
    restored_image = box(page, IMAGE_ID)
    restored_video = box(page, VIDEO_ID)
    assert (round(restored_image["x"] - before_image["x"]), round(restored_image["y"] - before_image["y"])) == (0, 0)
    assert (round(restored_video["x"] - before_video["x"]), round(restored_video["y"] - before_video["y"])) == (0, 0)

    page.keyboard.press("Meta+Shift+z")
    page.wait_for_timeout(300)
    redone_image = box(page, IMAGE_ID)
    redone_video = box(page, VIDEO_ID)
    assert (round(redone_image["x"] - before_image["x"]), round(redone_image["y"] - before_image["y"])) == image_delta
    assert (round(redone_video["x"] - before_video["x"]), round(redone_video["y"] - before_video["y"])) == video_delta

    page.screenshot(path=str(REFERENCE_DIR / "liblib-clone-batch5-multi-drag-desktop-2026-08-25.png"))
    assert not errors, errors


def run_group_drag(page):
    errors = []
    page.on("console", lambda message: errors.append(f"console:{message.type}:{message.text}") if message.type == "error" else None)
    page.on("pageerror", lambda error: errors.append(f"pageerror:{error}"))
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(400)

    select_image_and_video(page)
    page.keyboard.press("g")
    page.wait_for_timeout(300)
    group = page.locator(".react-flow__node-storyboard-group").filter(has_text="组合节点")
    group_box = group.bounding_box()
    assert group_box is not None
    before_image = node_rects_with_text(page, "分镜 #2")[0]
    before_video = node_rects_with_text(page, "分镜视频-#9")[0]
    before_group = group.bounding_box()
    assert before_group is not None

    x = before_group["x"] + 12
    y = before_group["y"] + 12
    page.mouse.move(x, y)
    page.mouse.down()
    page.mouse.move(x + 36, y + 18, steps=4)
    page.mouse.move(x + 72, y + 36, steps=4)
    page.mouse.up()
    page.wait_for_timeout(300)

    after_group = group.bounding_box()
    after_image = node_rects_with_text(page, "分镜 #2")[0]
    after_video = node_rects_with_text(page, "分镜视频-#9")[0]
    assert after_group is not None
    delta = (round(after_group["x"] - before_group["x"]), round(after_group["y"] - before_group["y"]))
    assert delta != (0, 0)
    assert (round(after_image["x"] - before_image["x"]), round(after_image["y"] - before_image["y"])) == delta
    assert (round(after_video["x"] - before_video["x"]), round(after_video["y"] - before_video["y"])) == delta

    page.keyboard.press("Meta+z")
    page.wait_for_timeout(300)
    restored_group = group.bounding_box()
    restored_image = node_rects_with_text(page, "分镜 #2")[0]
    restored_video = node_rects_with_text(page, "分镜视频-#9")[0]
    assert restored_group is not None
    assert (round(restored_group["x"] - before_group["x"]), round(restored_group["y"] - before_group["y"])) == (0, 0)
    assert (round(restored_image["x"] - before_image["x"]), round(restored_image["y"] - before_image["y"])) == (0, 0)
    assert (round(restored_video["x"] - before_video["x"]), round(restored_video["y"] - before_video["y"])) == (0, 0)

    page.screenshot(path=str(REFERENCE_DIR / "liblib-clone-batch5-group-drag-desktop-2026-08-25.png"))
    assert not errors, errors


def run_duplicate(page):
    errors = []
    page.on("console", lambda message: errors.append(f"console:{message.type}:{message.text}") if message.type == "error" else None)
    page.on("pageerror", lambda error: errors.append(f"pageerror:{error}"))
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(400)

    select_image_and_video(page)
    page.keyboard.press("Meta+d")
    page.wait_for_timeout(350)
    assert page.locator(".react-flow__node").count() == 12
    assert page.locator(".react-flow__edge").count() == 12
    assert page.locator(".react-flow__node.selected").count() == 2
    assert page.get_by_text("人像质感调节", exact=True).count() == 0
    assert page.get_by_text("Seedance 2.5", exact=True).count() == 0

    page.keyboard.press("Meta+z")
    page.wait_for_timeout(300)
    assert page.locator(".react-flow__node").count() == 10
    assert page.locator(".react-flow__edge").count() == 11
    page.keyboard.press("Meta+Shift+z")
    page.wait_for_timeout(300)
    assert page.locator(".react-flow__node").count() == 12
    assert page.locator(".react-flow__edge").count() == 12
    assert page.locator(".react-flow__node.selected").count() == 0

    page.screenshot(path=str(REFERENCE_DIR / "liblib-clone-batch5-multi-duplicate-desktop-2026-08-25.png"))
    assert not errors, errors


def run_single_duplicate_compatibility(page):
    errors = []
    page.on("console", lambda message: errors.append(f"console:{message.type}:{message.text}") if message.type == "error" else None)
    page.on("pageerror", lambda error: errors.append(f"pageerror:{error}"))
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(400)

    page.locator(f'[data-id="{IMAGE_ID}"]').click(force=True)
    page.keyboard.press("Meta+d")
    page.wait_for_timeout(350)
    assert page.locator(".react-flow__node").count() == 11
    assert page.locator(".react-flow__edge").count() == 14
    assert page.locator(".react-flow__node.selected").count() == 1
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
    page.screenshot(path=str(REFERENCE_DIR / "liblib-clone-batch5-mobile-390-2026-08-25.png"))
    assert not errors, errors


def main():
    REFERENCE_DIR.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        desktop = browser.new_page(viewport={"width": 1440, "height": 900}, device_scale_factor=1)
        run_movement(desktop)
        desktop.close()
        group_drag = browser.new_page(viewport={"width": 1440, "height": 900}, device_scale_factor=1)
        run_group_drag(group_drag)
        group_drag.close()
        duplicate = browser.new_page(viewport={"width": 1440, "height": 900}, device_scale_factor=1)
        run_duplicate(duplicate)
        duplicate.close()
        single_duplicate = browser.new_page(viewport={"width": 1440, "height": 900}, device_scale_factor=1)
        run_single_duplicate_compatibility(single_duplicate)
        single_duplicate.close()
        group_duplicate = browser.new_page(viewport={"width": 1440, "height": 900}, device_scale_factor=1)
        run_group_duplicate(group_duplicate)
        group_duplicate.close()
        mobile = browser.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=1)
        run_mobile(mobile)
        mobile.close()
        browser.close()
    print("Batch5 Playwright verification passed: multi-drag, single-step undo/redo, multi-duplicate, mobile overflow, console.")


if __name__ == "__main__":
    main()
