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
BASE_URL = os.environ.get("LIBLIB_BASE_URL", "http://localhost:4317")

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

    # ★★★ Batch 857 **判据迁移**：群众阵列的入口**只有 rail 一个**。
    # ★ ★ 原来这条走的是「视口工具栏里那枚「添加群众阵列」按钮 ＋ 一套 legacy 面板」
    #   （`[data-director-crowd-trigger]`／`[data-director-crowd-panel]`／
    #   `[data-director-crowd-rows]`…）。
    # ★ ★ 那个入口**源站没有** —— 源站实测（自指判据，见
    #   docs/research/liblib-canvas-batch857-2026-10-01/raw/source-857-crowd.json
    #   的「⑤同aria元素」）：全页「aria-label 等于对话框那个」的元素**只有 1 个**
    #   ⟹ ⟹ 源站**只有 rail 的「添加角色 → 群众 (3x3)」一个入口**
    #   ⟹ ⟹ clone 那枚按钮是**多出来的** ⟹ ⟹ 本批删掉它 ＋ 那套 legacy 面板
    #   ⟹ ⟹ 于是本条判据**迁到 rail 的对话框**（**被测行为一字未改**：
    #   仍然是「填 2×3／间距 1.1 ⟹ 加出 6 个成员 ＋ 一个组 ＋ 组选中」）。
    page.locator("[data-director-rail-entry='add-character']").click()
    page.wait_for_timeout(300)
    page.locator("[data-director-character-option='crowd-3x3']").click()
    page.wait_for_timeout(300)
    dialog = page.locator("[data-director-crowd-dialog]")
    dialog.wait_for(state="visible")
    page.locator("[data-director-crowd-input='rows']").fill("2")
    page.locator("[data-director-crowd-input='columns']").fill("3")
    page.locator("[data-director-crowd-input='spacing']").fill("1.1")
    assert page.locator("[data-director-crowd-count]").inner_text().strip() == "共6人"
    # ★ 几何断言也跟着换：源站逐字 `W({left:t.right+8,top:t.top})`
    #   ⟹ ⟹ 对话框在**浮层的右侧**，且宽度是 **220px**
    #   （源站实测：220×204 @(280,388) ⟹ 见 raw/source-857-crowd.json 的「④对话框」）。
    dialog_box = box(dialog)
    flyout_box = box(page.locator("[data-director-character-flyout]"))
    assert flyout_box["x"] + flyout_box["width"] <= dialog_box["x"]
    assert dialog_box["width"] == 220
    page.screenshot(path=str(CROWD_PANEL_SCREENSHOT))

    page.locator("[data-director-crowd-confirm]").click()
    page.locator("[data-director-crowd-dialog]").wait_for(state="hidden")
    # ★★★ Batch 857：**关掉 rail 的「添加角色」浮层**。
    #   ⟹ ⟹ 源站的「添加角色」是**左侧面板模式切换**（`z` 只能是 "scene" 或
    #   "character"、两者互斥）⟹ ⟹ 源站加完群众之后**场景树是不在的**。
    #   ⟹ ⟹ clone 把「添加角色」做成了**浮层**（盖在场景树上）⟹ ⟹ 场景树
    #   **还在下面、但被浮层挡住** ⟹ ⟹ 浮层里的
    #   `[data-director-character-option]` 会**截走**落在它矩形上的点击
    #   ⟹ ⟹ 后面要点组行的 toggle 时就点不到（本批迁移后暴露的）。
    #   ⟹ ⟹ 用户视角对应的动作是点 rail 的**「场景」**：源站点它 ⟹ 左侧
    #   面板切回场景树；clone 点它 ⟹ 浮层关闭、左侧仍是场景树。
    #   ⟹ ⟹ 所以这里点「场景」，**两边的语义一致**。
    page.locator("[data-director-rail-entry='scene']").click()
    page.wait_for_timeout(300)
    assert page.locator("[data-director-character-flyout]").count() == 0
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
    # ★★ Batch 854：组是**默认展开**的 —— 源站逐字 `expanded:!!F||!j.has(e.id)`
    # （`j` 是**被折叠**的组集合 ⟹ ⟹ 默认就在展开态），且 batch 854 的源站实测
    # 证实：新组建完，**成员立即可见**（源站探针 `raw/source-854-groupmembers.json`
    # 的 `⑤⌘G后x` 里组员就在缩进位上）。
    # ⟹ ⟹ 本断言从「先折叠、再点开」改成「**默认就展开**、点一下才收起」，
    #     并且**限定在这个组里**（不按全局计数）⟹ ⟹ 别的组的状态不会干扰。
    group_expanded = page.locator(
        f"[data-director-group-id='{group['id']}'] "
        "[data-director-group-expanded='true']"
    )
    group_members = page.locator(
        f"[data-director-group-id='{group['id']}'] [data-director-group-member-id]"
    )
    assert group_expanded.count() == 1
    assert group_members.count() == len(group["characterIds"])
    group_row.locator("[data-director-group-action='toggle']").click()
    assert group_expanded.count() == 0
    assert group_members.count() == 0

    # Batch 593: 建轨有两个入口——工具条「+ 新建轨道」(data-director-add-track)
    # 与「+ 轨道」(data-director-add-track-manual)。本断言要建的是**分组**
    # 轨道（objectId == group id + memberOffsets），所以点后者；原选择器
    # data-director-add-track 在两个按钮上重复，strict mode 直接报错。
    add_track = page.locator("[data-director-add-track-manual]")
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
    # ★★ Batch 856：**判据迁移**（本批按源站逐字删掉了组检查器的
    #   「位置／旋转／缩放」三个字段 ⟹ ⟹ 这个**输入框**在源站**不存在**，
    #   在 clone 里也被删掉了 ⟹ ⟹ 原来那条「填输入框」的路径**测不了了**）。
    # ★ ★ 换一条**语义等价**的路径：直接调 store 的 `updateGroupTransform`
    #   （源站对应的是「在时间轴上拖组轨道关键帧」）⟹ ⟹
    #   **被测的东西没变**（组变换 ⟹ 写轨道关键帧 ⟹ 锚点右移），
    #   只是**操作入口**从「源站没有的 UI」换成「store action」
    #   （★ 91.py 测同一条链时用的也是这个手法）。
    page.evaluate(
        """([groupId, nextX]) =>
          window.__director_store.getState().updateGroupTransform(groupId, {
            position: [nextX, 0, 0],
            rotation: [0, 0, 0],
            scale: [1, 1, 1],
          })""",
        [group["id"], before_anchor[0] + 1.2],
    )
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
    # Batch 593: 与 batch 36-40 / 88 / 89 / 96 / 85 / 580 / 587-592 同约定过滤
    # 已知瞬态 `TransformControls: The attached 3D object must be a part of the
    # scene graph.`（three.js 在对象被替换的那一帧抛出）。
    unexpected = [error for error in errors if "TransformControls" not in error]
    assert unexpected == [], json.dumps(unexpected, ensure_ascii=False, indent=2)
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
    # Batch 593: 与 batch 36-40 / 88 / 89 / 96 / 85 / 580 / 587-592 同约定过滤
    # 已知瞬态 `TransformControls: The attached 3D object must be a part of the
    # scene graph.`（three.js 在对象被替换的那一帧抛出）。
    unexpected = [error for error in errors if "TransformControls" not in error]
    assert unexpected == [], json.dumps(unexpected, ensure_ascii=False, indent=2)


def run_mobile(page: Page):
    errors = attach_errors(page)
    open_director(page, force_dom_click=True)
    # ★★★ Batch 857 **判据迁移**：legacy 的视口群众面板**已删**（源站没有那个入口）
    #   ⟹ ⟹ 移动端这条改走**移动端那枚 crowd 入口**。
    #   ★ ★ 为什么**不是** rail 的「添加角色」：
    #   clone 的 rail 在 **<899px 是 `hidden`** ⟹ ⟹ 移动端点 rail 入口会
    #   **超时**（元素不可见）⟹ ⟹ 移动端的入口是视口底部工具条那枚
    #   （`[data-director-crowd-mobile-trigger]`，桌面端隐藏）⟹ ⟹ 它开的是
    #   **同一个**对话框（量程／默认值／落点规则与桌面完全同源）。
    #   ★ 源站**没有移动端布局**（实测 390×844 下源站渲染的仍是桌面画布），
    #   ⟹ ⟹ 移动端这枚是 clone 自己的扩展 ⟹ ⟹ 如实登记，不冒充源站行为。
    page.locator("[data-director-crowd-mobile-trigger]").click()
    page.wait_for_timeout(400)
    dialog = page.locator("[data-director-crowd-dialog]")
    dialog.wait_for(state="visible")
    dialog_box = box(dialog)
    # ★ 源站逐字：对话框宽 **220px**（源站实测 220×204）
    assert dialog_box["width"] == 220
    # ★ ★ 移动端**可见**的 crowd 入口**只有这一枚**（与桌面同口径）
    assert page.locator("[data-director-character-option='crowd-3x3']").count() == 0
    assert_no_overflow(page)
    page.screenshot(path=str(MOBILE_SCREENSHOT))
    assert_nonblank_locator(
        page.locator('canvas[data-director-webgl-canvas="true"]'),
        "mobile director WebGL canvas",
    )
    # Batch 593: 与 batch 36-40 / 88 / 89 / 96 / 85 / 580 / 587-592 同约定过滤
    # 已知瞬态 `TransformControls: The attached 3D object must be a part of the
    # scene graph.`（three.js 在对象被替换的那一帧抛出）。
    unexpected = [error for error in errors if "TransformControls" not in error]
    assert unexpected == [], json.dumps(unexpected, ensure_ascii=False, indent=2)


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
    # ★★★ Batch 857：群众阵列的对话框在 **rail** 里 ⟹ ⟹ 静态契约也跟着搬。
    rail_source = (
        ROOT / "src/components/director/DirectorIconRail.tsx"
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
            rail_source,
            [
                "data-director-crowd-dialog",
                "data-director-crowd-input",
                "data-director-crowd-confirm",
                "addCrowdArray",
            ],
        ),
        (
            viewport_source,
            [
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

    # ★★★ Batch 857 **负向断言**：视口里那套 legacy 群众阵列面板**必须已清零**。
    #   ⟹ ⟹ 只写正向断言的话，「旧写法还在」也能过 ⟹ ⟹ 所以必须**显式**盯住清零。
    for legacy in [
        "data-director-crowd-trigger",
        "data-director-crowd-panel",
        "data-director-crowd-rows",
        "data-director-crowd-columns",
        "data-director-crowd-spacing",
        "data-director-crowd-action",
    ]:
        assert legacy not in viewport_source, (
            "视口里还有 legacy 群众阵列选择器：%s" % legacy
        )


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
