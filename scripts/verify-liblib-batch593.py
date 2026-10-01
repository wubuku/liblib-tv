#!/usr/bin/env python3
"""Verify Batch 593: 时间轴左列两级结构（对象行 + 轨道行）与关键帧按钮归位。

Source facts (live CDP sampling of the source director desk at 1920x1150,
2026-10-01, evidence under /tmp/src593 + this batch's README):

The timeline is TWO stacked layers, not one toolbar + one list:

    root          1920 x 182 @ (0, 968), pointer-events-none
    panel         1920 x 130 @ (0, 1020), pointer-events-auto
      strip       1920 x 36  @ (0, 1021)  absolute top-0 z-30  (gap 2px)
        left      320 x 36 — 播放 / 自动帧 / 循环播放 / 播放头位置(46x24)
                 / 总时长(46x24) / ms / + 新建轨道(82x24)
        right    1598 x 36 — ruler canvas + 时间轴缩放 + 时间线最小化
                 + 导出视频到画布
      track area  left 320 / right 1598, gap 2px

The 320px left column is TWO levels deep — a per-object row, then that
object's track rows:

    对象行  320 x 32 @ (0, 1057)
            grid-template-columns: 16px minmax(0,1fr) 220px
            col1 20x20 <button aria-label="收起属性" aria-expanded="true">,
                 chevron rotate-90 (rotate-0 when collapsed), no title
            col2 div[role=button][title="主机位"] > span.truncate
            col3 <button aria-label="绘制轨迹" aria-pressed="false"> 86x24
                 icon 14x14 + label 13px
    轨道行  320 x 32 @ (0, 1089)
            grid-template-columns: 40px 36px 78px minmax(0,1fr)
            col1 span[aria-hidden].h-full.w-10 — a plain decorative plus:
                 1px vertical from the row top to the midline, 16px
                 horizontal on the midline, both #363636
            col2 div[role=button][title="位置"] > span.truncate
            col3 three 24x24 buttons inside flex.h-6.gap-0.5:
                 上一关键帧        (disabled when the TRACK has no earlier
                                    keyframe)
                 当前帧有关键帧 / 当前帧无关键帧, aria-pressed
                 下一关键帧        (disabled when the TRACK has no later
                                    keyframe)
            col4 span.text-right.text-[13px].tabular-nums -> "3.3,2.2,10"

The three keyframe buttons are therefore per-TRACK, and 收起属性 / 展开属性
(aria-expanded) is a SECOND, independent collapse control that lives in the
object row — distinct from 时间线最小化 on the right of the strip.

Measured behaviour of the keyframe trio (playhead 0 vs 977ms, one track with
a single keyframe at 0):

    playhead 0     ‹ disabled   ◆ 当前帧有关键帧 pressed=true   › disabled
    playhead 977   ‹ enabled    ◆ 当前帧无关键帧 pressed=false  › disabled

so the seek range is the track, not the whole timeline; and the value column
still read 3.3,2.2,10 at 977ms, i.e. it shows the keyframe in force at the
playhead rather than an interpolated value.

The clone had a single 220px column listing tracks flat (no object row), kept
上一/下一关键帧 in the toolbar, showed the delete affordance inside the track
row, and rendered 绘制轨迹 as a span[role=button] rather than a real button.

NOT verified (recorded, not fabricated):
* the source's per-property track split (位置 / 旋转 / 缩放 as three tracks).
  Creating extra tracks on the source would mutate the user's real project,
  so this batch keeps the clone's one-track-per-object model and only aligns
  the two-level layout, the grid columns and the button semantics;
* whether 收起属性 is per-object or global — the source has a single object
  (主机位), so the chevron is treated as per-object (the standard tree
  reading) and said so inline;
* 3.3,2.2,10 is the source camera's own position; the clone prints its own
  object's position in the same format.

Contract asserted here:
1. the toolbar is 36px and starts with the source's seven controls, and
   carries no 上一/下一关键帧 (they moved to the track rows);
2. the left column is 320px and holds one 对象行 per object that owns tracks;
3. the object row is 32px with columns 16px / 1fr / 220px; its first cell is
   a 20x20 收起属性 button carrying aria-expanded and no title; its third
   cell is a real 86x24 绘制轨迹 button carrying aria-pressed;
4. every track row is 32px with columns 40px / 36px / 78px / 1fr, a 40px
   aria-hidden decorative plus, and the three 24x24 keyframe buttons;
5. the keyframe trio flips name/pressed/disabled exactly as measured, and
   the middle button adds a keyframe at an empty playhead and removes it
   when one is there;
6. the value column prints a plain x,y,z triple (no fixed decimals);
7. 收起属性 hides only the track rows — the object row and the timeline
   height both survive;
8. no diagnostics.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
BASE_URL = os.environ.get("LIBLIB_BASE_URL", "http://localhost:4317")
AUDIT_PATH = (
    ROOT
    / "docs"
    / "research"
    / "liblib-canvas-batch593-2026-10-01"
    / "runtime-audit.json"
)

TRACK_LIST_PX = 320
TOOLBAR_PX = 36
ROW_PX = 32
OBJECT_COLUMNS = "16px minmax(0,1fr) 220px"
TRACK_COLUMNS = "40px 36px 78px minmax(0,1fr)"
# 逐字取自源站工具条左格的可及名（batch 591 已用同一份清单）：
# 播放 / 自动帧 / 循环播放 / 播放头位置 / 总时长 /
# 切换时间单位为 s（源站当前是 ms）/ 选中角色、道具或分组后建立轨道
SOURCE_PREFIX = [
    "播放",
    "自动帧",
    "循环播放",
    "播放头位置",
    "总时长",
    "切换时间单位为 ms",
    "选中角色、道具或分组后建立轨道",
]


def normalize_columns(value: str) -> str:
    """CSSOM echoes `minmax(0, 1fr)` back as `minmax(0px, 1fr)`; compare the
    specified track sizes, not the resolved pixel values."""
    return value.replace("0px", "0").replace(" ", "")


def attach_errors(page: Page) -> list[str]:
    errors: list[str] = []
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
            f"requestfailed:{request.method}:{request.url}:{request.failure}"
        ),
    )
    return errors


def open_desk(page: Page) -> None:
    page.goto(f"{BASE_URL}/?batch70=1", wait_until="networkidle")
    page.wait_for_function(
        """() => Boolean(window.__libtv_store && window.__libtv_ui_store && window.__director_store)"""
    )
    page.evaluate(
        """() => {
          const store = window.__libtv_store.getState();
          store.addNode("script-execution", { title: "Batch 593" });
          const node = store.getActiveCanvas().nodes.at(-1);
          window.__libtv_ui_store.getState().openDirectorDesk(node.id, store.activeCanvasId);
        }"""
    )
    page.locator("[data-director-workspace]").wait_for(state="visible")
    page.wait_for_timeout(600)
    page.locator("[data-director-timeline-controls]").wait_for(state="visible")


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1920x1150", "checks": []}

    def check(name: str, ok: bool, detail: Any = None) -> None:
        result["checks"].append(
            {"name": name, "ok": bool(ok), "detail": detail}
        )

    errors = attach_errors(page)
    open_desk(page)

    # 1) toolbar geometry + source-ordered prefix, and no keyframe nav in it
    toolbar = page.evaluate(
        """() => {
          const bar = document.querySelector('[data-director-timeline-controls]');
          const r = bar.getBoundingClientRect();
          const name = (el) => (el.getAttribute('aria-label')
            || (el.innerText || '').trim() || el.getAttribute('data-director-time-field')
            || el.getAttribute('type'));
          return {h: Math.round(r.height),
                  order: [...bar.querySelectorAll('button, input')].map(name).filter(Boolean)};
        }"""
    )
    result["toolbar"] = toolbar
    check("toolbar:36px", toolbar["h"] == TOOLBAR_PX, detail=toolbar)
    check(
        "toolbar:source-prefix",
        toolbar["order"][: len(SOURCE_PREFIX)] == SOURCE_PREFIX,
        detail=toolbar["order"][: len(SOURCE_PREFIX) + 2],
    )
    check(
        "toolbar:no-keyframe-nav",
        "上一关键帧" not in toolbar["order"] and "下一关键帧" not in toolbar["order"],
        detail=toolbar["order"],
    )

    # 2) the left column is 320px wide
    list_width = page.evaluate(
        """() => Math.round(document.querySelector('[data-director-timeline-track-list]')
             .getBoundingClientRect().width)"""
    )
    check("track-list:320px", list_width == TRACK_LIST_PX, detail=list_width)

    # 3) one object row per object that owns tracks, 32px, source columns
    object_rows = page.evaluate(
        """() => [...document.querySelectorAll('[data-director-timeline-object-row]')].map((row) => {
          const r = row.getBoundingClientRect();
          const toggle = row.querySelector('button[aria-expanded]');
          const tr = toggle ? toggle.getBoundingClientRect() : null;
          const name = row.querySelector('[data-director-timeline-object-name]');
          return {
            objectId: row.getAttribute('data-director-timeline-object-row'),
            h: Math.round(r.height),
            columns: row.style.gridTemplateColumns || getComputedStyle(row).gridTemplateColumns,
            toggle: tr ? {w: Math.round(tr.width), h: Math.round(tr.height)} : null,
            toggleAria: toggle ? toggle.getAttribute('aria-label') : null,
            toggleExpanded: toggle ? toggle.getAttribute('aria-expanded') : null,
            toggleTitle: toggle ? toggle.getAttribute('title') : null,
            name: name ? name.textContent.trim() : null,
            nameTitle: name ? name.getAttribute('title') : null,
            drawTrail: (() => {
              const b = row.querySelector('[data-director-track-draw-trail]');
              if (!b) return null;
              const br = b.getBoundingClientRect();
              return {tag: b.tagName.toLowerCase(), w: Math.round(br.width),
                      h: Math.round(br.height), aria: b.getAttribute('aria-label'),
                      pressed: b.getAttribute('aria-pressed')};
            })(),
          };
        })"""
    )
    result["object_rows"] = object_rows
    check("object-row:exists", bool(object_rows), detail=object_rows)
    check(
        "object-row:32px",
        all(row["h"] == ROW_PX for row in object_rows),
        detail=[row["h"] for row in object_rows],
    )
    check(
        "object-row:source-columns",
        all(
            normalize_columns(row["columns"])
            == normalize_columns(OBJECT_COLUMNS)
            for row in object_rows
        ),
        detail=[row["columns"] for row in object_rows],
    )
    check(
        "object-row:toggle",
        all(
            row["toggle"] == {"w": 20, "h": 20}
            and row["toggleAria"] == "收起属性"
            and row["toggleExpanded"] == "true"
            and row["toggleTitle"] is None
            for row in object_rows
        ),
        detail=object_rows,
    )
    # 源站当前只有一个对象（主机位，带摄像机），所以「绘制轨迹」只出现在
    # 摄像机对象行上；clone 的角色行没有该按钮，这是数据差异不是结构差异。
    # 断言的是：**有**它的行必须是真 button + 逐字可及名 + 86x24。
    trail = [row["drawTrail"] for row in object_rows if row["drawTrail"]]
    check(
        "object-row:draw-trail-is-button",
        len(trail) >= 1
        and all(
            item["tag"] == "button"
            and item["aria"] == "绘制轨迹"
            and item["pressed"] in {"true", "false"}
            and item["w"] == 86
            and item["h"] == 24
            for item in trail
        ),
        detail=trail,
    )
    check(
        "object-row:name-has-title",
        all(row["nameTitle"] and row["name"] for row in object_rows),
        detail=[(row["name"], row["nameTitle"]) for row in object_rows],
    )

    # 4) every track row: 32px, source columns, 40px decorative plus, nav trio
    track_rows = page.evaluate(
        """() => [...document.querySelectorAll('[data-director-track-row]')].map((row) => {
          const r = row.getBoundingClientRect();
          const plus = row.children[0];
          const pr = plus.getBoundingClientRect();
          const name = row.querySelector('[title]');
          const nav = [...row.querySelectorAll('button')];
          const navBoxes = nav.map((b) => {
            const br = b.getBoundingClientRect();
            return {aria: b.getAttribute('aria-label'), pressed: b.getAttribute('aria-pressed'),
                    disabled: b.disabled, w: Math.round(br.width), h: Math.round(br.height)};
          });
          const value = row.querySelector('[data-director-track-value]');
          return {
            trackId: row.getAttribute('data-director-track-row'),
            h: Math.round(r.height),
            columns: row.style.gridTemplateColumns || getComputedStyle(row).gridTemplateColumns,
            plus: {hidden: plus.getAttribute('aria-hidden'), w: Math.round(pr.width)},
            name: name ? name.textContent.trim() : null,
            nameTitle: name ? name.getAttribute('title') : null,
            nav: navBoxes,
            value: value ? value.textContent.trim() : null,
          };
        })"""
    )
    result["track_rows"] = track_rows
    check("track-row:exists", bool(track_rows), detail=track_rows)
    check(
        "track-row:32px",
        all(row["h"] == ROW_PX for row in track_rows),
        detail=[row["h"] for row in track_rows],
    )
    check(
        "track-row:source-columns",
        all(
            normalize_columns(row["columns"]) == normalize_columns(TRACK_COLUMNS)
            for row in track_rows
        ),
        detail=[row["columns"] for row in track_rows],
    )
    check(
        "track-row:decorative-plus",
        all(
            row["plus"] == {"hidden": "true", "w": 40} for row in track_rows
        ),
        detail=[row["plus"] for row in track_rows],
    )
    check(
        "track-row:keyframe-nav",
        all(
            len(row["nav"]) == 3
            and [item["aria"] for item in row["nav"][:2]]
            == ["上一关键帧", "当前帧有关键帧"]
            and row["nav"][2]["aria"] == "下一关键帧"
            and all(item["w"] == 24 and item["h"] == 24 for item in row["nav"])
            for row in track_rows
        ),
        detail=[row["nav"] for row in track_rows],
    )
    check(
        "track-row:value-triple",
        all(
            row["value"] is None
            or all(
                part.replace("-", "", 1).replace(".", "", 1).isdigit()
                for part in row["value"].split(",")
            )
            for row in track_rows
        ),
        detail=[row["value"] for row in track_rows],
    )

    # 5) the trio's name / pressed / disabled follow the playhead, per track
    first_row = track_rows[0]["trackId"]
    row_sel = f'[data-director-track-row="{first_row}"]'

    def nav_state() -> list[dict[str, Any]]:
        return page.evaluate(
            """(sel) => [...document.querySelector(sel).querySelectorAll('button')].map((b) => ({
                 aria: b.getAttribute('aria-label'),
                 pressed: b.getAttribute('aria-pressed'),
                 disabled: b.disabled}))""",
            row_sel,
        )

    def keyframe_times(track_id: str) -> list[float]:
        return page.evaluate(
            """(id) => {
              const track = window.__director_store.getState().timeline.tracks
                .find((t) => t.id === id);
              return track ? track.keyframes.map((k) => k.time) : [];
            }""",
            track_id,
        )

    def assert_nav_rule(label: str, current_time: float) -> None:
        page.evaluate(
            "(t) => window.__director_store.getState().setTimelineTime(t)",
            current_time,
        )
        page.wait_for_timeout(150)
        nav = nav_state()
        times = keyframe_times(first_row)
        on_frame = any(
            abs(time - current_time) < 1e-3 for time in times
        )
        earlier = [time for time in times if time < current_time - 1e-3]
        later = [time for time in times if time > current_time + 1e-3]
        result[label] = {
            "currentTime": current_time,
            "keyframes": times,
            "nav": nav,
        }
        check(
            f"keyframe-nav:{label}",
            nav[0] == {
                "aria": "上一关键帧",
                "pressed": None,
                "disabled": not earlier,
            }
            and nav[1]
            == {
                "aria": "当前帧有关键帧" if on_frame else "当前帧无关键帧",
                "pressed": "true" if on_frame else "false",
                "disabled": False,
            }
            and nav[2] == {
                "aria": "下一关键帧",
                "pressed": None,
                "disabled": not later,
            },
            detail=result[label],
        )

    # 源站实测：播放头 0（唯一关键帧所在）→ ‹› 双禁用 + 当前帧有关键帧；
    # 播放头 977ms（该帧无关键帧）→ ‹ 可用 + 当前帧无关键帧。clone 的主轨道
    # 关键帧是 0/4/8，所以按**规则**而不是按某一组固定数字断言。
    assert_nav_rule("at-zero", 0)
    assert_nav_rule("between-keyframes", 1.234)
    assert_nav_rule("on-second-keyframe", 4)

    # the middle button removes a keyframe sitting on the playhead, and adds
    # one back afterwards
    page.evaluate("() => window.__director_store.getState().setTimelineTime(0)")
    page.wait_for_timeout(200)
    page.locator(f"{row_sel}").get_by_role(
        "button", name="当前帧有关键帧"
    ).click()
    page.wait_for_timeout(200)
    after_remove = nav_state()
    result["nav_after_remove"] = after_remove
    check(
        "keyframe-nav:toggle-off",
        after_remove[1]["aria"] == "当前帧无关键帧"
        and after_remove[1]["pressed"] == "false",
        detail=after_remove,
    )
    page.locator(f"{row_sel}").get_by_role(
        "button", name="当前帧无关键帧"
    ).click()
    page.wait_for_timeout(200)
    after_add = nav_state()
    result["nav_after_add"] = after_add
    check(
        "keyframe-nav:toggle-on",
        after_add[1]["aria"] == "当前帧有关键帧"
        and after_add[1]["pressed"] == "true",
        detail=after_add,
    )

    # 6) 收起属性 hides **that object's** track rows only — the object row,
    #    the other object's rows and the timeline height all survive.
    #    (源站只有一个对象，所以「按对象」是从栅格/箭头位置推断的，见 docstring。)
    target_object = object_rows[0]["objectId"]
    row_sel = f'[data-director-timeline-object-row="{target_object}"]'
    # 轨道行是对象行的**兄弟**（同在 group 包装里），所以按 group 统计。
    group_sel = f'[data-director-object-group="object:{target_object}"]'
    before = page.evaluate(
        """([sel, group_sel]) => ({
          timeline: Math.round(document.querySelector('[data-director-timeline]')
                     .getBoundingClientRect().height),
          objects: document.querySelectorAll('[data-director-timeline-object-row]').length,
          tracks: document.querySelectorAll('[data-director-track-row]').length,
          mine: document.querySelectorAll(group_sel + ' [data-director-track-row]').length})""",
        [row_sel, group_sel],
    )
    page.locator(f"{row_sel}").get_by_role("button", name="收起属性").click()
    page.wait_for_timeout(250)
    after = page.evaluate(
        """([sel, group_sel]) => {
          const row = document.querySelector(sel);
          const toggle = row.querySelector('button[aria-expanded]');
          return {
            timeline: Math.round(document.querySelector('[data-director-timeline]')
                       .getBoundingClientRect().height),
            objects: document.querySelectorAll('[data-director-timeline-object-row]').length,
            tracks: document.querySelectorAll('[data-director-track-row]').length,
            mine: document.querySelectorAll(group_sel + ' [data-director-track-row]').length,
            toggle: {aria: toggle.getAttribute('aria-label'),
                     expanded: toggle.getAttribute('aria-expanded')}};
        }""",
        [row_sel, group_sel],
    )
    result["collapse"] = {"target": target_object, "before": before, "after": after}
    check(
        "collapse:hides-own-track-rows",
        before["mine"] > 0 and after["mine"] == 0,
        detail={"before": before, "after": after},
    )
    check(
        "collapse:keeps-other-objects",
        after["tracks"] == before["tracks"] - before["mine"] and after["tracks"] > 0,
        detail={"before": before, "after": after},
    )
    check(
        "collapse:keeps-object-row",
        after["objects"] == before["objects"] and after["objects"] > 0,
        detail={"before": before, "after": after},
    )
    check(
        "collapse:keeps-timeline-height",
        after["timeline"] == before["timeline"],
        detail={"before": before, "after": after},
    )
    check(
        "collapse:renames-toggle",
        after["toggle"] == {"aria": "展开属性", "expanded": "false"},
        detail=after["toggle"],
    )

    page.locator(f"{row_sel}").get_by_role("button", name="展开属性").click()
    page.wait_for_timeout(250)
    restored = page.evaluate(
        """([sel, group_sel]) => {
          const row = document.querySelector(sel);
          return {mine: document.querySelectorAll(group_sel + ' [data-director-track-row]').length,
                  toggle: row.querySelector('button[aria-expanded]')
                    .getAttribute('aria-label')};
        }""",
        [row_sel, group_sel],
    )
    result["restore"] = restored
    check(
        "collapse:restores",
        restored == {"mine": before["mine"], "toggle": "收起属性"},
        detail=restored,
    )

    page.screenshot(path=str(ROOT / "docs" / "design-references" / "liblib-timeline-two-level-1920.png"))
    result["diagnostics"] = errors
    check("no-diagnostics", not errors, detail=errors)
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 593,
        "title": "时间轴左列两级结构：对象行（收起属性/绘制轨迹）+ 轨道行（40/36/78/1fr 栅格、‹◆›、x,y,z 读数）",
        "evidence": (
            "2026-10-01 live CDP sampling of the source director desk at "
            "1920x1150 + docs/research/liblib-canvas-batch593-2026-10-01/README.md"
        ),
        "source_facts": {
            "timeline_root": [0, 968, 1920, 182],
            "panel": [0, 1020, 1920, 130],
            "strip": [0, 1021, 1920, 36],
            "left_column_px": 320,
            "object_row": {
                "box": [0, 1057, 320, 32],
                "grid": "16px minmax(0,1fr) 220px",
                "toggle": "20x20 button aria-expanded, chevron rotate-90/0, no title",
                "draw_trail": "86x24 button aria-pressed=false",
            },
            "track_row": {
                "box": [0, 1089, 320, 32],
                "grid": "40px 36px 78px minmax(0,1fr)",
                "plus": "40px aria-hidden decorative plus, #363636",
                "nav": [
                    "上一关键帧 (disabled without an earlier keyframe)",
                    "当前帧有关键帧 / 当前帧无关键帧, aria-pressed",
                    "下一关键帧 (disabled without a later keyframe)",
                ],
                "value": "3.3,2.2,10 (plain triple, not fixed decimals)",
            },
            "nav_at_zero": [
                {"disabled": True},
                {"aria": "当前帧有关键帧", "pressed": "true"},
                {"disabled": True},
            ],
            "nav_at_977ms": [
                {"disabled": False},
                {"aria": "当前帧无关键帧", "pressed": "false"},
                {"disabled": True},
            ],
        },
        "clone_only": [
            "one track per object (the source splits 位置 / 旋转 / 缩放 into "
            "separate tracks) — splitting them would require mutating the "
            "user's real project to observe, so it stays recorded, not done",
            "the track-row name column prints a two-character kind name "
            "(变换 / 机位 / 姿势 / 分组) with the full label on title, because "
            "the source's 36px column holds two-character property names",
            "删除轨道 lives in the toolbar; the source's 4-column track row has "
            "no room for it",
        ],
        "not_verified": [
            "whether the source's 收起属性 is per-object or global — the source "
            "has a single object, so it is treated as per-object inline",
            "the source's per-property track split and its value formatting for "
            "rotation / scale tracks",
        ],
        "migrated_contracts": [
            "batch 591: 上一/下一关键帧 are no longer a clone-only toolbar "
            "suffix — batch 593 re-measured the source and found them in every "
            "track row, so 591 now asserts their absence from the toolbar and "
            "their presence per track row",
            "batch 36 / 42: scope the keyframe nav buttons to the selected "
            "track row (role+name now matches one button per track)",
            "batch 37: click the track name (div[role=button]) instead of the "
            "row's first <button>, which is 上一关键帧 now",
        ],
        "results": [],
    }
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        desktop = browser.new_page(
            viewport={"width": 1920, "height": 1150}, device_scale_factor=1
        )
        audit["results"].append(run_desktop(desktop))
        desktop.close()
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    checks = audit["results"][0]["checks"]
    failed = [item for item in checks if not item["ok"]]
    print(
        "Batch 593 verification: "
        f"{len(checks) - len(failed)}/{len(checks)} checks passed"
    )
    if failed:
        raise SystemExit(
            "FAILED: " + json.dumps(failed, ensure_ascii=False, indent=2)
        )


if __name__ == "__main__":
    main()
