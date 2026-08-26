from base64 import b64decode
from io import BytesIO
from pathlib import Path
import json
import math
import os

from PIL import Image, ImageChops, ImageDraw, ImageStat
from playwright.sync_api import Locator, Page, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "docs" / "design-references"
BASE_URL = os.environ.get("LIBLIB_BASE_URL", "http://localhost:3000")

CROWD_PANEL_SCREENSHOT = (
    REFERENCE_DIR
    / "liblib-clone-batch45-director-crowd-panel-1440-2026-08-26.png"
)
CROWD_GROUP_SCREENSHOT = (
    REFERENCE_DIR
    / "liblib-clone-batch45-director-crowd-group-1440-2026-08-26.png"
)
GROUP_KEYFRAME_SCREENSHOT = (
    REFERENCE_DIR
    / "liblib-clone-batch45-director-group-keyframe-1440-2026-08-26.png"
)
GROUP_PLAYBACK_SCREENSHOT = (
    REFERENCE_DIR
    / "liblib-clone-batch45-director-group-playback-1440-2026-08-26.png"
)
MULTI_SELECT_SCREENSHOT = (
    REFERENCE_DIR
    / "liblib-clone-batch45-director-multi-select-1440-2026-08-26.png"
)
MOBILE_SCREENSHOT = (
    REFERENCE_DIR
    / "liblib-clone-batch45-director-crowd-mobile-390-2026-08-26.png"
)
CONTACT_SHEET = (
    REFERENCE_DIR
    / "liblib-clone-batch45-director-groups-contact-sheet-2026-08-26.png"
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
    page.on(
        "requestfailed",
        lambda request: errors.append(
            f"requestfailed:{request.url}:{request.failure}"
        ),
    )
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


def assert_nonblank_image(image: Image.Image, label: str):
    rgb = image.convert("RGB")
    stat = ImageStat.Stat(rgb)
    assert max(stat.stddev) > 8, f"{label} has insufficient variance: {stat.stddev}"
    spans = [maximum - minimum for minimum, maximum in stat.extrema]
    assert max(spans) > 80, f"{label} has insufficient range: {stat.extrema}"


def assert_nonblank_locator(locator: Locator, label: str):
    image = Image.open(BytesIO(locator.screenshot()))
    assert_nonblank_image(image, label)
    return image


def assert_pixel_difference(left: bytes, right: bytes, label: str):
    left_image = Image.open(BytesIO(left)).convert("RGB")
    right_image = Image.open(BytesIO(right)).convert("RGB")
    difference = ImageStat.Stat(ImageChops.difference(left_image, right_image))
    assert max(difference.mean) > 0.1, f"{label}: {difference.mean}"


def assert_finite_tuple(values, label: str):
    assert isinstance(values, list) and len(values) == 3, label
    assert all(math.isfinite(value) for value in values), (label, values)


def open_director(page: Page, force_dom_click: bool = False):
    page.goto(f"{BASE_URL}/?batch45=1", wait_until="networkidle")
    button = page.locator("[data-open-director]")
    assert button.count() == 1
    if force_dom_click:
        button.evaluate("(element) => element.click()")
    else:
        button.click()
    page.locator("[data-director-workspace]").wait_for(state="visible")
    page.locator("[data-director-timeline]").wait_for(state="visible")
    canvas = page.locator('canvas[data-director-webgl-canvas="true"]')
    canvas.wait_for(state="visible")
    page.wait_for_timeout(650)
    return canvas


def director_state(page: Page):
    return page.evaluate(
        """() => {
          const state = window.__director_store.getState();
          return {
            objects: state.objects,
            groups: state.groups,
            selectedObjectId: state.selectedObjectId,
            selectedObjectIds: state.selectedObjectIds,
            selectedGroupId: state.selectedGroupId,
            timeline: state.timeline,
          };
        }"""
    )


def find_group(state, group_id):
    return next(group for group in state["groups"] if group["id"] == group_id)


def find_group_track(state, group_id):
    return next(
        track
        for track in state["timeline"]["tracks"]
        if track["kind"] == "group" and track["groupId"] == group_id
    )


def run_crowd_group_loop(page: Page):
    errors = attach_errors(page)
    canvas = open_director(page)
    assert_nonblank_locator(canvas, "default director WebGL canvas")
    assert_no_overflow(page)

    initial_state = director_state(page)
    initial_object_count = len(initial_state["objects"])
    initial_group_count = len(initial_state["groups"])

    page.locator("[data-director-crowd-trigger]").click()
    panel = page.locator("[data-director-crowd-panel]")
    panel.wait_for(state="visible")
    page.locator("[data-director-crowd-rows]").fill("2")
    page.locator("[data-director-crowd-columns]").fill("3")
    page.locator("[data-director-crowd-spacing]").fill("1.1")
    assert panel.locator("[data-director-crowd-count='6']").count() == 1
    panel_box = box(panel)
    viewport_box = box(page.locator("[data-director-viewport]"))
    assert viewport_box["x"] <= panel_box["x"]
    assert panel_box["x"] + panel_box["width"] <= (
        viewport_box["x"] + viewport_box["width"]
    )
    assert panel_box["y"] >= viewport_box["y"]
    assert panel_box["y"] + panel_box["height"] <= (
        viewport_box["y"] + viewport_box["height"]
    )
    page.screenshot(path=str(CROWD_PANEL_SCREENSHOT))

    page.locator("[data-director-crowd-action='add']").click()
    page.locator("[data-director-crowd-panel]").wait_for(state="hidden")
    state = director_state(page)
    assert len(state["objects"]) == initial_object_count + 6
    assert len(state["groups"]) == initial_group_count + 1
    group = state["groups"][-1]
    assert group["crowd"] == {"rows": 2, "columns": 3, "spacing": 1.1}
    assert len(group["characterIds"]) == 6
    assert len(set(group["characterIds"])) == 6
    members = [
        next(object for object in state["objects"] if object["id"] == member_id)
        for member_id in group["characterIds"]
    ]
    positions = [tuple(member["transform"]["position"]) for member in members]
    assert len(set(positions)) == 6
    for member in members:
        assert_finite_tuple(member["transform"]["position"], "crowd position")
        assert_finite_tuple(member["transform"]["rotation"], "crowd rotation")
        assert_finite_tuple(member["transform"]["scale"], "crowd scale")
    group_row = page.locator(f"[data-director-group-id='{group['id']}']")
    assert group_row.get_attribute("data-director-group-selected") == "true"
    assert page.locator("[data-director-inspector-kind='group']").count() == 1
    assert director_state(page)["selectedGroupId"] == group["id"]

    page.screenshot(path=str(CROWD_GROUP_SCREENSHOT))
    group_row.locator("[data-director-group-action='toggle']").click()
    assert page.locator("[data-director-group-expanded='true']").count() == 1
    assert (
        page.locator("[data-director-group-member-id]").count()
        == len(group["characterIds"])
    )

    add_track = page.locator("[data-director-add-track]")
    assert not add_track.is_disabled()
    add_track.click()
    page.locator(
        f"[data-director-track-kind='group'][data-director-track-group-id='{group['id']}']"
    ).wait_for(state="visible")
    state = director_state(page)
    group_track = find_group_track(state, group["id"])
    assert group_track["objectId"] == group["id"]
    assert group_track["memberOffsets"].keys() >= set(group["characterIds"])
    assert len(group_track["keyframes"]) >= 1

    before_anchor = page.evaluate(
        """(groupId) => {
          const state = window.__director_store.getState();
          const group = state.groups.find((item) => item.id === groupId);
          const members = group.characterIds.map((id) =>
            state.objects.find((object) => object.id === id),
          );
          return members.reduce(
            (sum, member) => [
              sum[0] + member.transform.position[0],
              sum[1] + member.transform.position[1],
              sum[2] + member.transform.position[2],
            ],
            [0, 0, 0],
          ).map((value) => value / members.length);
        }""",
        group["id"],
    )
    page.evaluate(
        "() => window.__director_store.getState().setTimelineTime(4)"
    )
    page.locator(
        '[data-director-group-transform-field="position"] '
        '[data-director-transform-axis="x"]'
    ).fill(str(before_anchor[0] + 1.2))
    page.wait_for_timeout(160)
    state = director_state(page)
    group_track = find_group_track(state, group["id"])
    assert any(abs(keyframe["time"] - 4) < 0.001 for keyframe in group_track["keyframes"])
    after_anchor = page.evaluate(
        """(groupId) => {
          const state = window.__director_store.getState();
          const group = state.groups.find((item) => item.id === groupId);
          const members = group.characterIds.map((id) =>
            state.objects.find((object) => object.id === id),
          );
          return members.reduce(
            (sum, member) => [
              sum[0] + member.transform.position[0],
              sum[1] + member.transform.position[1],
              sum[2] + member.transform.position[2],
            ],
            [0, 0, 0],
          ).map((value) => value / members.length);
        }""",
        group["id"],
    )
    assert after_anchor[0] > before_anchor[0] + 1
    state = director_state(page)
    positions_after_transform = {
        member_id: next(
            object
            for object in state["objects"]
            if object["id"] == member_id
        )["transform"]["position"]
        for member_id in group["characterIds"]
    }
    page.screenshot(path=str(GROUP_KEYFRAME_SCREENSHOT))

    page.evaluate(
        "() => window.__director_store.getState().setTimelineTime(0)"
    )
    page.wait_for_timeout(120)
    frame_at_zero = canvas.screenshot()
    page.evaluate(
        "() => window.__director_store.getState().setTimelineTime(4)"
    )
    page.wait_for_timeout(120)
    frame_at_four = canvas.screenshot()
    assert_pixel_difference(frame_at_zero, frame_at_four, "group timeline scrub")
    assert_nonblank_locator(canvas, "group timeline frame")
    page.screenshot(path=str(GROUP_PLAYBACK_SCREENSHOT))

    page.evaluate(
        """() => {
          const store = window.__director_store.getState();
          store.setTimelineTime(0);
          store.setTimelinePlaying(true);
        }"""
    )
    page.wait_for_timeout(260)
    playing_state = director_state(page)
    assert playing_state["timeline"]["currentTime"] > 0
    page.evaluate(
        "() => window.__director_store.getState().setTimelinePlaying(false)"
    )

    page.locator("[data-director-group-action='ungroup']").click()
    page.wait_for_timeout(140)
    state = director_state(page)
    assert len(state["groups"]) == initial_group_count
    assert all(
        member_id in [object["id"] for object in state["objects"]]
        for member_id in group["characterIds"]
    )
    assert not any(
        track["kind"] == "group" and track["groupId"] == group["id"]
        for track in state["timeline"]["tracks"]
    )
    assert page.locator(f"[data-director-group-id='{group['id']}']").count() == 0
    assert errors == [], json.dumps(errors, ensure_ascii=False, indent=2)
    return positions_after_transform


def run_multi_select_group_loop(page: Page):
    errors = attach_errors(page)
    open_director(page)
    character_rows = page.locator("[data-director-object-kind='character']")
    assert character_rows.count() == 1
    first = character_rows.nth(0)

    page.evaluate(
        """() => {
          const state = window.__director_store.getState();
          const characterIds = state.objects
            .filter((object) => object.kind === "character")
            .map((object) => object.id);
          if (characterIds.length < 1) {
            throw new Error("default character fixture missing");
          }
        }"""
    )
    first.click()
    lead_id = first.get_attribute("data-director-object-id")
    assert lead_id
    page.evaluate(
        """() => {
          const store = window.__director_store.getState();
          const objects = store.objects.filter(
            (object) => object.kind === "character",
          );
          const second = objects[0];
          const extra = {
            ...second,
            id: "batch45-multi-select-character",
            name: "批量选择角色",
            transform: {
              ...second.transform,
              position: [1.2, 0, 0.8],
            },
          };
          store.addCrowdArray({ rows: 1, columns: 2, spacing: 1 });
          store.selectObject(second.id);
        }"""
    )
    state = director_state(page)
    crowd_group = state["groups"][-1]
    assert len(crowd_group["characterIds"]) == 2
    page.locator(
        f"[data-director-group-id='{crowd_group['id']}']"
    ).click()
    page.locator("[data-director-group-action='ungroup']").click()
    page.wait_for_timeout(100)

    character_rows = page.locator("[data-director-object-kind='character']")
    assert character_rows.count() >= 3
    first = character_rows.nth(0)
    second = character_rows.nth(1)
    first.click()
    second.click(modifiers=["Shift"])
    assert page.locator("[data-director-object-selected='true']").count() >= 2
    group_action = page.locator("[data-director-group-action='group']")
    assert not group_action.is_disabled()
    group_action.click()
    page.wait_for_timeout(120)
    state = director_state(page)
    group = state["groups"][-1]
    assert len(group["characterIds"]) == 2
    assert page.locator(
        f"[data-director-group-id='{group['id']}']"
    ).get_attribute("data-director-group-selected") == "true"
    page.screenshot(path=str(MULTI_SELECT_SCREENSHOT))

    page.locator("[data-director-group-action='ungroup']").click()
    state = director_state(page)
    assert not state["groups"]
    assert errors == [], json.dumps(errors, ensure_ascii=False, indent=2)


def run_mobile(page: Page):
    errors = attach_errors(page)
    open_director(page, force_dom_click=True)
    trigger = page.locator("[data-director-crowd-trigger]")
    trigger.click()
    panel = page.locator("[data-director-crowd-panel]")
    panel.wait_for(state="visible")
    panel_box = box(panel)
    viewport_box = box(page.locator("[data-director-viewport]"))
    assert panel_box["x"] >= viewport_box["x"]
    assert panel_box["x"] + panel_box["width"] <= (
        viewport_box["x"] + viewport_box["width"]
    )
    assert panel_box["y"] >= viewport_box["y"]
    assert panel_box["y"] + panel_box["height"] <= (
        viewport_box["y"] + viewport_box["height"]
    )
    assert_no_overflow(page)
    page.screenshot(path=str(MOBILE_SCREENSHOT))
    assert_nonblank_locator(
        page.locator('canvas[data-director-webgl-canvas="true"]'),
        "mobile director WebGL canvas",
    )
    assert errors == [], json.dumps(errors, ensure_ascii=False, indent=2)


def make_contact_sheet():
    items = [
        ("CROWD PANEL", CROWD_PANEL_SCREENSHOT),
        ("CROWD GROUP", CROWD_GROUP_SCREENSHOT),
        ("GROUP KEYFRAME", GROUP_KEYFRAME_SCREENSHOT),
        ("GROUP PLAYBACK", GROUP_PLAYBACK_SCREENSHOT),
        ("MULTI SELECT", MULTI_SELECT_SCREENSHOT),
        ("MOBILE", MOBILE_SCREENSHOT),
    ]
    thumb_width = 720
    label_height = 34
    padding = 16
    rendered = []
    for label, path in items:
        image = Image.open(path).convert("RGB")
        target_width = 360 if path == MOBILE_SCREENSHOT else thumb_width
        ratio = target_width / image.width
        thumbnail = image.resize(
            (target_width, max(1, round(image.height * ratio))),
            Image.Resampling.LANCZOS,
        )
        rendered.append((label, thumbnail))
    sheet_width = thumb_width * 2 + padding * 3
    heights = [0, 0]
    for index, (_, image) in enumerate(rendered):
        heights[index % 2] += image.height + label_height + padding
    sheet_height = max(heights) + padding
    sheet = Image.new("RGB", (sheet_width, sheet_height), "#111111")
    draw = ImageDraw.Draw(sheet)
    column_y = [padding, padding]
    for index, (label, image) in enumerate(rendered):
        column = index % 2
        x = padding + column * (thumb_width + padding)
        y = column_y[column]
        draw.text((x, y + 8), label, fill="#d8d8d8")
        y += label_height
        sheet.paste(image, (x + (thumb_width - image.width) // 2, y))
        column_y[column] = y + image.height + padding
    sheet.save(CONTACT_SHEET)


def verify_static_contract():
    math_source = (
        ROOT / "src/components/director/directorGroupMath.ts"
    ).read_text()
    tree_source = (
        ROOT / "src/components/director/DirectorObjectTree.tsx"
    ).read_text()
    viewport_source = (
        ROOT / "src/components/director/DirectorViewport.tsx"
    ).read_text()
    timeline_source = (
        ROOT / "src/components/director/DirectorTimeline.tsx"
    ).read_text()
    store_source = (ROOT / "src/store/directorStore.ts").read_text()
    for source, labels in [
        (
            math_source,
            [
                "getDirectorGroupAnchorTransform",
                "getDirectorGroupMemberOffsets",
                "applyDirectorGroupTransform",
                "createDirectorCrowdPositions",
            ],
        ),
        (
            tree_source,
            [
                "data-director-group-id",
                "data-director-group-expanded",
                "groupSelectedCharacters",
                "ungroupSelectedCharacters",
            ],
        ),
        (
            viewport_source,
            [
                "data-director-crowd-panel",
                "data-director-crowd-rows",
                "data-director-crowd-columns",
                "addCrowdArray",
                "data-director-group-rig",
            ],
        ),
        (
            timeline_source,
            [
                'track.kind === "group"',
                "data-director-track-group-id",
                "data-director-keyframe-id",
            ],
        ),
        (
            store_source,
            [
                "DirectorCharacterGroup",
                'kind: "group"',
                "groupSelectedCharacters",
                "addCrowdArray",
                "recordGroupKeyframe",
            ],
        ),
    ]:
        for label in labels:
            assert label in source, label


if __name__ == "__main__":
    REFERENCE_DIR.mkdir(parents=True, exist_ok=True)
    verify_static_contract()
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        desktop = browser.new_page(
            viewport={"width": 1440, "height": 900},
            device_scale_factor=1,
        )
        run_crowd_group_loop(desktop)
        multi_select = browser.new_page(
            viewport={"width": 1440, "height": 900},
            device_scale_factor=1,
        )
        run_multi_select_group_loop(multi_select)
        mobile = browser.new_page(
            viewport={"width": 390, "height": 844},
            device_scale_factor=1,
        )
        run_mobile(mobile)
        browser.close()
    make_contact_sheet()
    print("Batch 45 director group/crowd verification passed.")
