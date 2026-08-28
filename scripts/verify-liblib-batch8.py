from pathlib import Path

from playwright.sync_api import Page, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "docs" / "design-references"
URL = "http://localhost:4317"
VIDEO_GROUP_ID = "g-EFbbHpwq5w"
IMAGE_GROUP_ID = "g-245IDFh8sB"
VIDEO_ID = "v-UGQZzZOpbv"


def node(page: Page, node_id: str):
    return page.locator(f'.react-flow__node[data-id="{node_id}"]')


def node_box(page: Page, node_id: str):
    value = node(page, node_id).bounding_box()
    assert value is not None, f"missing node box: {node_id}"
    return value


def center(rect):
    return rect["x"] + rect["width"] / 2, rect["y"] + rect["height"] / 2


def drag(page: Page, start, dx: float, dy: float):
    page.mouse.move(*start)
    page.mouse.down()
    page.mouse.move(start[0] + dx / 2, start[1] + dy / 2, steps=4)
    page.mouse.move(start[0] + dx, start[1] + dy, steps=4)
    page.mouse.up()


def rounded_delta(before, after):
    return round(after["x"] - before["x"]), round(after["y"] - before["y"])


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


def assert_source_hierarchy(page: Page):
    video_group = node(page, VIDEO_GROUP_ID)
    image_group = node(page, IMAGE_GROUP_ID)
    assert "parent" in (video_group.get_attribute("class") or "").split()
    assert "parent" not in (image_group.get_attribute("class") or "").split()

    group_box = node_box(page, VIDEO_GROUP_ID)
    video_box = node_box(page, VIDEO_ID)
    zoom = video_box["width"] / 622
    assert abs((video_box["x"] - group_box["x"]) - 62 * zoom) < 1
    assert abs((video_box["y"] - group_box["y"]) - 62 * zoom) < 1


def run_parent_drag(page: Page):
    errors = attach_error_collection(page)
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(400)
    assert_source_hierarchy(page)

    before_group = node_box(page, VIDEO_GROUP_ID)
    before_video = node_box(page, VIDEO_ID)
    drag(page, (before_group["x"] + 10, before_group["y"] + 10), 72, 36)
    page.wait_for_timeout(300)

    after_group = node_box(page, VIDEO_GROUP_ID)
    after_video = node_box(page, VIDEO_ID)
    group_delta = rounded_delta(before_group, after_group)
    video_delta = rounded_delta(before_video, after_video)
    assert group_delta == video_delta
    assert group_delta != (0, 0)
    assert_source_hierarchy(page)

    page.keyboard.press("Meta+z")
    page.wait_for_timeout(250)
    assert rounded_delta(before_group, node_box(page, VIDEO_GROUP_ID)) == (0, 0)
    assert rounded_delta(before_video, node_box(page, VIDEO_ID)) == (0, 0)

    page.keyboard.press("Meta+Shift+z")
    page.wait_for_timeout(250)
    assert rounded_delta(before_group, node_box(page, VIDEO_GROUP_ID)) == group_delta
    assert rounded_delta(before_video, node_box(page, VIDEO_ID)) == video_delta
    page.screenshot(
        path=str(
            REFERENCE_DIR
            / "liblib-clone-batch8-video-group-drag-2026-08-25.png"
        )
    )
    assert not errors, errors


def run_child_drag(page: Page):
    errors = attach_error_collection(page)
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(400)
    before_group = node_box(page, VIDEO_GROUP_ID)
    before_video = node_box(page, VIDEO_ID)

    drag(page, center(before_video), 52, 26)
    page.wait_for_timeout(300)
    after_group = node_box(page, VIDEO_GROUP_ID)
    after_video = node_box(page, VIDEO_ID)
    assert rounded_delta(before_group, after_group) == (0, 0)
    assert rounded_delta(before_video, after_video) != (0, 0)
    assert "parent" in (node(page, VIDEO_GROUP_ID).get_attribute("class") or "").split()

    page.keyboard.press("Meta+z")
    page.wait_for_timeout(250)
    assert rounded_delta(before_group, node_box(page, VIDEO_GROUP_ID)) == (0, 0)
    assert rounded_delta(before_video, node_box(page, VIDEO_ID)) == (0, 0)
    assert not errors, errors


def relative_children_match(page: Page, group_boxes, video_boxes):
    zoom = video_boxes[0]["width"] / 622
    remaining = list(video_boxes)
    for group_box in group_boxes:
        match_index = next(
            (
                index
                for index, video_box in enumerate(remaining)
                if abs((video_box["x"] - group_box["x"]) - 62 * zoom) < 1
                and abs((video_box["y"] - group_box["y"]) - 62 * zoom) < 1
            ),
            None,
        )
        assert match_index is not None, (group_box, remaining)
        remaining.pop(match_index)
    assert not remaining


def run_group_duplicate(page: Page):
    errors = attach_error_collection(page)
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(400)
    node(page, VIDEO_GROUP_ID).click(position={"x": 10, "y": 10}, force=True)
    page.keyboard.press("Meta+d")
    page.wait_for_timeout(350)

    assert page.locator(".react-flow__node").count() == 12
    assert page.locator(".react-flow__edge").count() == 11
    assert page.locator(".react-flow__node-storyboard-group").count() == 3
    assert page.locator(".react-flow__node-video").count() == 2
    parent_groups = page.locator(
        ".react-flow__node-storyboard-group.parent"
    )
    assert parent_groups.count() == 2
    group_boxes = parent_groups.evaluate_all(
        """(nodes) => nodes.map((node) => {
          const rect = node.getBoundingClientRect();
          return { x: rect.x, y: rect.y, width: rect.width, height: rect.height };
        })"""
    )
    video_boxes = page.locator(".react-flow__node-video").evaluate_all(
        """(nodes) => nodes.map((node) => {
          const rect = node.getBoundingClientRect();
          return { x: rect.x, y: rect.y, width: rect.width, height: rect.height };
        })"""
    )
    relative_children_match(page, group_boxes, video_boxes)
    assert (
        page.locator(".react-flow__node-storyboard-group.selected")
        .filter(has_text="视频组 · 第一集：咖啡馆对峙-视频组 副本")
        .count()
        == 1
    )

    page.keyboard.press("Meta+z")
    page.wait_for_timeout(250)
    assert page.locator(".react-flow__node").count() == 10
    assert_source_hierarchy(page)
    assert not errors, errors


def point_close(point, expected, tolerance=2):
    return (
        abs(point["x"] - expected["x"]) <= tolerance
        and abs(point["y"] - expected["y"]) <= tolerance
    )


def run_child_duplicate(page: Page):
    errors = attach_error_collection(page)
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(400)
    original_group = node_box(page, VIDEO_GROUP_ID)
    original_video = node_box(page, VIDEO_ID)

    node(page, VIDEO_ID).click(force=True)
    page.keyboard.press("Meta+d")
    page.wait_for_timeout(350)
    assert page.locator(".react-flow__node").count() == 11
    assert page.locator(".react-flow__edge").count() == 14
    assert page.locator(".react-flow__node-video").count() == 2
    assert page.locator(".react-flow__node-storyboard-group.parent").count() == 1
    videos_before_drag = page.locator(".react-flow__node-video").evaluate_all(
        """(nodes) => nodes.map((node) => {
          const rect = node.getBoundingClientRect();
          return { x: rect.x, y: rect.y, width: rect.width, height: rect.height };
        })"""
    )
    copied_video = next(
        box
        for box in videos_before_drag
        if not point_close(box, original_video)
    )

    node(page, VIDEO_GROUP_ID).click(position={"x": 10, "y": 10}, force=True)
    before_group_drag = node_box(page, VIDEO_GROUP_ID)
    drag(page, (before_group_drag["x"] + 10, before_group_drag["y"] + 10), 72, 36)
    page.wait_for_timeout(300)
    after_group = node_box(page, VIDEO_GROUP_ID)
    group_delta = rounded_delta(original_group, after_group)
    videos_after_drag = page.locator(".react-flow__node-video").evaluate_all(
        """(nodes) => nodes.map((node) => {
          const rect = node.getBoundingClientRect();
          return { x: rect.x, y: rect.y, width: rect.width, height: rect.height };
        })"""
    )
    moved_original = {
        "x": original_video["x"] + group_delta[0],
        "y": original_video["y"] + group_delta[1],
    }
    assert any(point_close(box, moved_original) for box in videos_after_drag)
    assert any(point_close(box, copied_video) for box in videos_after_drag)
    page.screenshot(
        path=str(
            REFERENCE_DIR
            / "liblib-clone-batch8-child-copy-detached-2026-08-25.png"
        )
    )
    assert not errors, errors


def run_cascade_delete(page: Page):
    errors = attach_error_collection(page)
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(400)
    node(page, VIDEO_GROUP_ID).click(position={"x": 10, "y": 10}, force=True)
    page.keyboard.press("Delete")
    page.wait_for_timeout(300)
    assert page.locator(".react-flow__node").count() == 8
    assert page.locator(".react-flow__node-storyboard-group").count() == 1
    assert page.locator(".react-flow__node-video").count() == 0
    assert page.locator(".react-flow__edge").count() == 7

    page.keyboard.press("Meta+z")
    page.wait_for_timeout(300)
    assert page.locator(".react-flow__node").count() == 10
    assert page.locator(".react-flow__edge").count() == 11
    assert_source_hierarchy(page)
    assert not errors, errors


def run_organize(page: Page):
    errors = attach_error_collection(page)
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(400)
    page.keyboard.press("Alt+Shift+f")
    page.wait_for_timeout(300)
    assert page.get_by_role("button", name="缩放选项").inner_text() == "28%"
    assert_source_hierarchy(page)
    page.screenshot(
        path=str(
            REFERENCE_DIR
            / "liblib-clone-batch8-organize-parenting-929-2026-08-25.png"
        )
    )
    assert not errors, errors


def main():
    REFERENCE_DIR.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        parent_drag = browser.new_page(
            viewport={"width": 1440, "height": 900}, device_scale_factor=1
        )
        run_parent_drag(parent_drag)
        parent_drag.close()
        child_drag = browser.new_page(
            viewport={"width": 1440, "height": 900}, device_scale_factor=1
        )
        run_child_drag(child_drag)
        child_drag.close()
        group_duplicate = browser.new_page(
            viewport={"width": 1440, "height": 900}, device_scale_factor=1
        )
        run_group_duplicate(group_duplicate)
        group_duplicate.close()
        child_duplicate = browser.new_page(
            viewport={"width": 1440, "height": 900}, device_scale_factor=1
        )
        run_child_duplicate(child_duplicate)
        child_duplicate.close()
        cascade_delete = browser.new_page(
            viewport={"width": 1440, "height": 900}, device_scale_factor=1
        )
        run_cascade_delete(cascade_delete)
        cascade_delete.close()
        organize = browser.new_page(
            viewport={"width": 929, "height": 874}, device_scale_factor=1
        )
        run_organize(organize)
        organize.close()
        browser.close()
    print(
        "Batch8 Playwright verification passed: source parent class/offset, "
        "parent and child drag history, group/child copy, cascade delete, organize."
    )


if __name__ == "__main__":
    main()
