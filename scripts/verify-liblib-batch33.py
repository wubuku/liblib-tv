from pathlib import Path
import os

from PIL import Image, ImageDraw
from playwright.sync_api import Locator, Page, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "docs" / "design-references"
BASE_URL = os.environ.get("LIBLIB_BASE_URL", "http://localhost:4317")

INFO_SCREENSHOT = (
    REFERENCE_DIR / "liblib-clone-batch33-long-info-929-2026-08-26.png"
)
BUSY_SCREENSHOT = (
    REFERENCE_DIR / "liblib-clone-batch33-long-busy-929-2026-08-26.png"
)
GRAPH_SCREENSHOT = (
    REFERENCE_DIR / "liblib-clone-batch33-long-graph-929-2026-08-26.png"
)
REPEATED_SCREENSHOT = (
    REFERENCE_DIR / "liblib-clone-batch33-long-repeated-929-2026-08-26.png"
)
MOBILE_SCREENSHOT = (
    REFERENCE_DIR / "liblib-clone-batch33-long-mobile-390-2026-08-26.png"
)
CONTACT_SHEET = (
    REFERENCE_DIR
    / "liblib-clone-batch33-long-video-contact-sheet-2026-08-26.png"
)


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


def assert_no_overflow(page: Page):
    assert page.evaluate(
        "document.documentElement.scrollWidth <= document.documentElement.clientWidth"
    )
    assert page.evaluate(
        "document.body.scrollWidth <= document.body.clientWidth"
    )


def switch_to_empty_canvas(page: Page):
    page.goto(BASE_URL, wait_until="networkidle")
    page.locator("[data-canvas-trigger]").click()
    page.locator('[data-canvas-row="canvas-1"] button').first.click()
    page.wait_for_timeout(180)
    assert page.locator(".react-flow__node").count() == 0
    assert page.locator(".react-flow__edge").count() == 0


def add_ready_video(page: Page):
    page.get_by_role("button", name="添加节点").click()
    page.locator('[data-add-node-entry="video"]').click()
    source = page.locator(".react-flow__node-video.selected")
    assert source.count() == 1
    source_id = source.get_attribute("data-id")
    assert source_id
    source = page.locator(f'.react-flow__node[data-id="{source_id}"]')
    assert page.locator("[data-video-generation-panel]").count() == 1
    return source, source_id


def move_source_up(page: Page, source: Locator, delta: int = 180):
    source_box = box(source)
    page.mouse.move(source_box["x"] + 30, source_box["y"] + 30)
    page.mouse.down()
    page.mouse.move(
        source_box["x"] + 30,
        source_box["y"] + 30 - delta,
        steps=10,
    )
    page.mouse.up()
    page.wait_for_timeout(180)


def click_locator(locator: Locator, dom_click: bool):
    if dom_click:
        locator.evaluate("(element) => element.click()")
    else:
        locator.click()


def select_long_mode(
    page: Page,
    duration: int = 300,
    dom_click: bool = False,
):
    click_locator(page.locator("[data-video-mode-trigger]"), dom_click)
    click_locator(
        page.locator('[data-video-mode-option="long-video"]'),
        dom_click,
    )
    assert "超长视频" in page.locator("[data-video-mode-trigger]").inner_text()
    click_locator(page.locator("[data-video-params-trigger]"), dom_click)
    params = page.locator("[data-video-params-menu]")
    assert params.get_attribute("data-video-params-mode") == "long"
    slider = page.locator("[data-video-duration]")
    assert slider.get_attribute("min") == "30"
    assert slider.get_attribute("max") == "300"
    slider.fill(str(duration))
    click_locator(page.locator("[data-video-params-trigger]"), dom_click)
    assert f"{duration}s" in page.locator(
        "[data-video-params-trigger]"
    ).inner_text()
    assert page.locator("[data-video-credits]").inner_text() == str(duration * 49)


def process_nodes(page: Page):
    return page.locator("[data-long-video-process-node]")


def process_shells_for_id(page: Page, process_id: str):
    return page.locator(
        f'[data-long-video-process-id="{process_id}"]'
    ).locator("xpath=ancestor::div[contains(@class, 'react-flow__node')][1]")


def graph_bounds(locator: Locator):
    rects = [box(locator.nth(index)) for index in range(locator.count())]
    return {
        "left": min(rect["x"] for rect in rects),
        "top": min(rect["y"] for rect in rects),
        "right": max(rect["x"] + rect["width"] for rect in rects),
        "bottom": max(rect["y"] + rect["height"] for rect in rects),
    }


def submit_long_process(page: Page):
    submit = page.locator("[data-video-generate-submit]")
    assert submit.get_attribute("data-video-long-submit-state") == "idle"
    submit.click()
    assert submit.is_disabled()
    assert (
        submit.get_attribute("data-video-long-submit-state") == "submitting"
    )
    assert page.locator("[data-video-long-submit-spinner]").count() == 1
    return submit


def run_desktop(page: Page):
    errors = attach_errors(page)
    switch_to_empty_canvas(page)
    source, source_id = add_ready_video(page)
    move_source_up(page, source)

    page.locator("[data-video-generate-submit]").click()
    assert process_nodes(page).count() == 0
    assert page.locator(".react-flow__node").count() == 1
    assert page.locator(".react-flow__edge").count() == 0

    select_long_mode(page)
    page.get_by_role("button", name="查看过程").click()
    info = page.locator("[data-video-long-process-info]")
    assert info.count() == 1
    assert "过程将在提交后创建" in info.inner_text()
    assert "素材 · 镜头 · 候选批次 · 300s 成片" in info.inner_text()
    page.screenshot(path=str(INFO_SCREENSHOT))
    page.get_by_role("button", name="返回 Prompt").click()

    submit = submit_long_process(page)
    page.screenshot(path=str(BUSY_SCREENSHOT))
    page.wait_for_timeout(650)
    assert submit.get_attribute("data-video-long-submit-state") == "created"
    assert process_nodes(page).count() == 12
    assert page.locator(".react-flow__node").count() == 13
    assert page.locator(".react-flow__edge").count() == 22
    assert page.locator(".react-flow__node.selected").get_attribute(
        "data-id"
    ) == source_id
    assert "画布过程已创建" in page.locator(
        "[data-video-long-process-info]"
    ).inner_text()

    nodes = process_nodes(page)
    process_ids = nodes.evaluate_all(
        "(items) => [...new Set(items.map((item) => item.dataset.longVideoProcessId))]"
    )
    assert len(process_ids) == 1
    process_id = process_ids[0]
    assert process_id
    stage_counts = {
        stage: page.locator(
            f'[data-long-video-process-stage="{stage}"]'
        ).count()
        for stage in ["material", "shot", "candidate", "assembly", "final"]
    }
    assert stage_counts == {
        "material": 3,
        "shot": 3,
        "candidate": 4,
        "assembly": 1,
        "final": 1,
    }
    assert page.locator(
        '[data-long-video-process-batch-index="1"]'
    ).count() == 2
    assert page.locator(
        '[data-long-video-process-batch-index="2"]'
    ).count() == 2
    first = nodes.first
    assert first.get_attribute("data-long-video-process-source-id") == source_id
    assert first.get_attribute("data-long-video-process-status") == "pending"
    # Batch 149: 默认模型迁移为 Seedance 2.0 VIP（源站 2026-09-07 触发器实拍「2.0」）。
    assert first.get_attribute("data-long-video-process-model") == "2.0 VIP"
    assert first.get_attribute("data-long-video-process-ratio") == "16:9"
    assert first.get_attribute("data-long-video-process-resolution") == "720P"
    assert first.get_attribute("data-long-video-process-duration") == "300"
    assert first.get_attribute("data-long-video-process-audio") == "true"
    assert first.get_attribute("data-long-video-process-credits") == "14700"
    assert first.get_attribute("data-long-video-process-reference-count") == "3"
    assert int(
        first.get_attribute("data-long-video-process-prompt-length") or "0"
    ) > 100
    assert "等待生成" in page.locator(
        '[data-long-video-process-stage="candidate"]'
    ).first.inner_text()
    assert "等待拼接" in page.locator(
        '[data-long-video-process-stage="final"]'
    ).inner_text()

    material_ids = page.locator(
        '[data-long-video-process-stage="material"]'
    ).evaluate_all(
        "(items) => items.map((item) => item.closest('.react-flow__node').dataset.id)"
    )
    shot_ids = page.locator(
        '[data-long-video-process-stage="shot"]'
    ).evaluate_all(
        "(items) => items.map((item) => item.closest('.react-flow__node').dataset.id)"
    )
    candidate_ids = page.locator(
        '[data-long-video-process-stage="candidate"]'
    ).evaluate_all(
        "(items) => items.map((item) => item.closest('.react-flow__node').dataset.id)"
    )
    assembly_id = page.locator(
        '[data-long-video-process-stage="assembly"]'
    ).evaluate(
        "(item) => item.closest('.react-flow__node').dataset.id"
    )
    final_id = page.locator(
        '[data-long-video-process-stage="final"]'
    ).evaluate(
        "(item) => item.closest('.react-flow__node').dataset.id"
    )
    assert all(material_ids)
    assert all(shot_ids)
    assert all(candidate_ids)
    for shot_id in shot_ids:
        assert page.locator(
            f'.react-flow__edge[aria-label="Edge from {source_id} to {shot_id}"]'
        ).count() == 1
    material_to_shot = sum(
        page.locator(
            f'.react-flow__edge[aria-label="Edge from {material_id} to {shot_id}"]'
        ).count()
        for material_id in material_ids
        for shot_id in shot_ids
    )
    assert material_to_shot == 6
    for candidate_id in candidate_ids:
        assert page.locator(
            f'.react-flow__edge[aria-label="Edge from {candidate_id} to {assembly_id}"]'
        ).count() == 1
    assert page.locator(
        f'.react-flow__edge[aria-label="Edge from {assembly_id} to {final_id}"]'
    ).count() == 1

    page.keyboard.press("Escape")
    page.wait_for_timeout(120)
    page.keyboard.press("Meta+0")
    page.wait_for_timeout(360)
    page.screenshot(path=str(GRAPH_SCREENSHOT))
    assert_no_overflow(page)

    page.keyboard.press("Meta+z")
    page.wait_for_timeout(160)
    assert process_nodes(page).count() == 0
    assert page.locator(".react-flow__node").count() == 1
    assert page.locator(".react-flow__edge").count() == 0
    page.keyboard.press("Meta+Shift+z")
    page.wait_for_timeout(160)
    assert process_nodes(page).count() == 12
    assert page.locator(".react-flow__node").count() == 13
    assert page.locator(".react-flow__edge").count() == 22

    source = page.locator(f'.react-flow__node[data-id="{source_id}"]')
    source.click(position={"x": 18, "y": 18}, force=True)
    page.locator("[data-video-mode-trigger]").evaluate(
        "(element) => element.click()"
    )
    page.locator('[data-video-mode-option="long-video"]').evaluate(
        "(element) => element.click()"
    )
    page.locator("[data-video-params-trigger]").evaluate(
        "(element) => element.click()"
    )
    page.locator("[data-video-duration]").fill("300")
    page.locator("[data-video-params-trigger]").evaluate(
        "(element) => element.click()"
    )
    submit_long_process(page)
    page.wait_for_timeout(650)
    assert process_nodes(page).count() == 24
    assert page.locator(".react-flow__edge").count() == 44
    repeated_ids = process_nodes(page).evaluate_all(
        "(items) => [...new Set(items.map((item) => item.dataset.longVideoProcessId))]"
    )
    assert len(repeated_ids) == 2

    page.keyboard.press("Escape")
    page.wait_for_timeout(120)
    page.keyboard.press("Meta+0")
    page.wait_for_timeout(360)
    first_bounds = graph_bounds(process_shells_for_id(page, repeated_ids[0]))
    second_bounds = graph_bounds(process_shells_for_id(page, repeated_ids[1]))
    separated = (
        first_bounds["bottom"] < second_bounds["top"]
        or second_bounds["bottom"] < first_bounds["top"]
    )
    assert separated, (first_bounds, second_bounds)
    page.screenshot(path=str(REPEATED_SCREENSHOT))
    assert_no_overflow(page)
    assert not errors, errors


def run_multi_selection(page: Page):
    errors = attach_errors(page)
    switch_to_empty_canvas(page)
    source, _ = add_ready_video(page)
    page.get_by_role("button", name="添加节点").click()
    page.locator('[data-add-node-entry="text"]').click()
    source.click(position={"x": 12, "y": 12}, modifiers=["Meta"], force=True)
    page.wait_for_timeout(150)
    assert page.locator(".react-flow__node.selected").count() == 2
    assert page.locator("[data-video-generation-panel]").count() == 0
    assert page.locator("[data-video-processing-toolbar]").count() == 0
    assert_no_overflow(page)
    assert not errors, errors


def run_mobile(page: Page):
    errors = attach_errors(page)
    switch_to_empty_canvas(page)
    source, _ = add_ready_video(page)
    select_long_mode(page, duration=30, dom_click=True)
    page.get_by_role("button", name="查看过程").evaluate(
        "(element) => element.click()"
    )
    panel = page.locator("[data-video-generation-panel]")
    panel_box = box(panel)
    source_box = box(source)
    assert panel_box["x"] < 0
    assert panel_box["x"] + panel_box["width"] > 390
    assert abs(
        panel_box["x"]
        + panel_box["width"] / 2
        - (source_box["x"] + source_box["width"] / 2)
    ) <= 1.5
    assert "过程将在提交后创建" in page.locator(
        "[data-video-long-process-info]"
    ).inner_text()
    assert_no_overflow(page)
    page.screenshot(path=str(MOBILE_SCREENSHOT))
    assert not errors, errors


def save_contact_sheet():
    images = [
        ("process info", Image.open(INFO_SCREENSHOT).convert("RGB")),
        ("busy submit", Image.open(BUSY_SCREENSHOT).convert("RGB")),
        ("process graph", Image.open(GRAPH_SCREENSHOT).convert("RGB")),
        ("repeated graph", Image.open(REPEATED_SCREENSHOT).convert("RGB")),
        ("mobile clipping", Image.open(MOBILE_SCREENSHOT).convert("RGB")),
    ]
    label_height = 28
    gutter = 12
    cell_width = max(image.width for _, image in images)
    cell_height = max(image.height for _, image in images)
    columns = 2
    rows = (len(images) + columns - 1) // columns
    sheet = Image.new(
        "RGB",
        (
            cell_width * columns + gutter * (columns - 1),
            (cell_height + label_height + gutter) * rows,
        ),
        "#141414",
    )
    draw = ImageDraw.Draw(sheet)
    for index, (label, image) in enumerate(images):
        column = index % columns
        row = index // columns
        x = column * (cell_width + gutter)
        y = row * (cell_height + label_height + gutter)
        draw.text((x + 8, y + 8), label, fill="#ededed")
        sheet.paste(image, (x, y + label_height))
    sheet.save(CONTACT_SHEET)


def main():
    REFERENCE_DIR.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        desktop = browser.new_page(viewport={"width": 929, "height": 874})
        run_desktop(desktop)

        multi = browser.new_page(viewport={"width": 929, "height": 874})
        run_multi_selection(multi)

        mobile = browser.new_page(viewport={"width": 390, "height": 844})
        run_mobile(mobile)
        browser.close()

    save_contact_sheet()
    print(
        "Batch 33 verified: long mode request, busy state, 12-node process graph, "
        "dense source/material/shot/candidate/assembly/final topology, metadata, "
        "repeated graph avoidance, atomic history, multi-selection and mobile clipping."
    )


if __name__ == "__main__":
    main()
