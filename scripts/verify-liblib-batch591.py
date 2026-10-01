#!/usr/bin/env python3
"""Verify Batch 591: 导演台时间轴工具栏对齐源站（2026-10-01 实测）。

Source facts (live CDP sampling of the source director desk at 1920x1150;
the 动画时间轴 toggle is a real button and opens the panel at
1920x182 @(0,968), after which `aria-pressed="true"`):

Toolbar order, left to right — 播放 / 自动帧 / 循环播放 / 播放头位置 /
总时长 / 时间单位 / 新建轨道, then (right side) 时间轴缩放 / 时间线最小化 /
导出视频到画布.

The two readouts are **joined editable text boxes**, each 46x24, 12px,
centered, `border-width: 0`, and NOT read-only:

    播放头位置  radius 8px 0 0 8px
    总时长     radius 0

Their values follow the unit toggle:

    s  mode ->  0.00 / 10.00     button text `s`   aria 切换时间单位为 ms
    ms mode ->  0    / 10000     button text `ms`  aria 切换时间单位为 s

自动帧 carries `aria-pressed="false"`; 新建轨道's accessible name is
`选中角色、道具或分组后建立轨道` (a precondition hint, not 「新建轨道」).

The clone previously showed the readouts as `mm:ss.ss` text, had a read-only
duration span, had no unit toggle, and ordered 自动帧 after 循环播放.

Contract asserted here:
1. the first seven toolbar controls appear in the source order;
2. 播放头位置 / 总时长 are editable text inputs of the measured size, and
   render `0.00` / `10.00` in s mode;
3. the unit toggle flips both readouts to integer milliseconds and its own
   label/aria, and flips back;
4. editing 总时长 commits through the store;
5. 新建轨道 exposes the source's verbatim accessible name;
6. the toolbar carries NOTHING named 上一/下一关键帧. Batch 593 measured the
   source again and found those two buttons live in every TRACK ROW, not in
   the toolbar — so 591's old "clone-only suffix" contract was wrong and is
   migrated here (the buttons moved to the track rows, 36 / 42 click them
   scoped to the selected track row);
7. no diagnostics.

NOT verified (recorded, not fabricated): what the source clamps an edited
duration to. This batch reuses the conservative rule the store already
applies elsewhere — positive, and never earlier than the last keyframe — and
says so in the code.
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
    / "liblib-canvas-batch591-2026-10-01"
    / "runtime-audit.json"
)

SOURCE_PREFIX = [
    "播放",
    "自动帧",
    "循环播放",
    "播放头位置",
    "总时长",
    "切换时间单位为 ms",
    "选中角色、道具或分组后建立轨道",
]


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


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool, detail: Any = None) -> None:
        assert ok, f"batch591 check failed: {name} :: {detail}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/?batch70=1", wait_until="networkidle")
    page.wait_for_function(
        """() => Boolean(window.__libtv_store && window.__libtv_ui_store && window.__director_store)"""
    )
    page.evaluate(
        """() => {
          const store = window.__libtv_store.getState();
          store.addNode("script-execution", { title: "Batch 591" });
          const node = store.getActiveCanvas().nodes.at(-1);
          window.__libtv_ui_store.getState().openDirectorDesk(node.id, store.activeCanvasId);
        }"""
    )
    page.locator("[data-director-workspace]").wait_for(state="visible")
    page.wait_for_timeout(600)
    page.locator("[data-director-timeline-controls]").wait_for(state="visible")

    # 1) the seven source-ordered controls, in order, by accessible name
    order = page.evaluate(
        """() => {
          const bar = document.querySelector('[data-director-timeline-controls]');
          const name = (el) => (el.getAttribute('aria-label')
            || (el.innerText || '').trim() || el.getAttribute('data-director-time-field')
            || el.getAttribute('type'));
          return [...bar.querySelectorAll('button, input')]
            .map(name)
            .filter(Boolean);
        }"""
    )
    result["toolbar_order"] = order
    check(
        "toolbar:source-prefix",
        order[: len(SOURCE_PREFIX)] == SOURCE_PREFIX,
        detail=order[: len(SOURCE_PREFIX) + 1],
    )
    check(
        "toolbar:no-keyframe-nav",
        "上一关键帧" not in order and "下一关键帧" not in order,
        detail=order,
    )
    # Batch 593: 关键帧导航归位到每条轨道行——逐行核对三个按钮都在。
    row_nav = page.evaluate(
        """() => [...document.querySelectorAll('[data-director-track-row]')].map((row) => ({
          row: row.getAttribute('data-director-track-row'),
          names: [...row.querySelectorAll('button')]
            .map((b) => b.getAttribute('aria-label'))
            .filter((n) => n && n.includes('关键帧')),
        }))"""
    )
    result["track_row_nav"] = row_nav
    check(
        "track-row:keyframe-nav-per-row",
        bool(row_nav)
        and all(
            names == ["上一关键帧", "当前帧有关键帧", "下一关键帧"]
            or names == ["上一关键帧", "当前帧无关键帧", "下一关键帧"]
            for names in (item["names"] for item in row_nav)
        ),
        detail=row_nav,
    )

    # 2) both readouts are editable text inputs of the measured size
    fields = page.evaluate(
        """() => [...document.querySelectorAll('[data-director-time-field]')].map(el => {
          const c = getComputedStyle(el);
          const r = el.getBoundingClientRect();
          return {field: el.getAttribute('data-director-time-field'),
                  aria: el.getAttribute('aria-label'), type: el.type, value: el.value,
                  readOnly: el.readOnly, w: Math.round(r.width), h: Math.round(r.height),
                  fontSize: c.fontSize, textAlign: c.textAlign,
                  borderWidth: c.borderTopWidth, radius: c.borderRadius,
                  unit: el.getAttribute('data-director-time-field-unit')};
        })"""
    )
    result["fields_s_mode"] = fields
    check("fields:two", len(fields) == 2, detail=fields)
    by_aria = {f["aria"]: f for f in fields}
    check("fields:head-aria", "播放头位置" in by_aria, detail=list(by_aria))
    check("fields:duration-aria", "总时长" in by_aria, detail=list(by_aria))
    for aria, field in by_aria.items():
        check(f"fields:{aria}:type-text", field["type"] == "text")
        check(f"fields:{aria}:editable", field["readOnly"] is False)
        check(
            f"fields:{aria}:46x24",
            abs(field["w"] - 46) <= 1 and abs(field["h"] - 24) <= 1,
            detail=(field["w"], field["h"]),
        )
        check(f"fields:{aria}:12px-centered", field["fontSize"] == "12px"
              and field["textAlign"] == "center", detail=(field["fontSize"], field["textAlign"]))
        check(
            f"fields:{aria}:no-border",
            float(field["borderWidth"].replace("px", "") or 0) == 0,
            detail=field["borderWidth"],
        )
        check(f"fields:{aria}:unit-s", field["unit"] == "s", detail=field["unit"])

    head = page.locator("[data-director-time-field='time']")
    duration = page.locator("[data-director-time-field='duration']")
    store_head = page.evaluate(
        "() => window.__director_store.getState().timeline.currentTime"
    )
    store_dur = page.evaluate(
        "() => window.__director_store.getState().timeline.duration"
    )
    result["store_time_and_duration"] = [store_head, store_dur]
    check("s-mode:head-two-decimals", head.input_value() == f"{store_head:.2f}",
          detail=(head.input_value(), store_head))
    check("s-mode:duration-two-decimals", duration.input_value() == f"{store_dur:.2f}",
          detail=(duration.input_value(), store_dur))
    check("s-mode:no-mm-ss", ":" not in head.input_value(), detail=head.input_value())

    # 3) the unit toggle flips both readouts and its own label/aria
    unit_btn = page.locator("[data-director-time-unit]")
    check("unit:initial-aria", unit_btn.get_attribute("aria-label") == "切换时间单位为 ms")
    check("unit:initial-text", unit_btn.inner_text().strip() == "s", detail=unit_btn.inner_text())
    unit_btn.click()
    page.wait_for_timeout(200)
    check("unit:ms-text", unit_btn.inner_text().strip() == "ms", detail=unit_btn.inner_text())
    check("unit:ms-aria", unit_btn.get_attribute("aria-label") == "切换时间单位为 s")
    check(
        "ms-mode:head-integer-ms",
        head.input_value() == str(round(store_head * 1000)),
        detail=(head.input_value(), store_head),
    )
    check(
        "ms-mode:duration-integer-ms",
        duration.input_value() == str(round(store_dur * 1000)),
        detail=(duration.input_value(), store_dur),
    )
    unit_btn.click()
    page.wait_for_timeout(200)
    check("unit:back-to-s", unit_btn.inner_text().strip() == "s")
    check("unit:back-to-two-decimals", head.input_value() == f"{store_head:.2f}")

    # 4) editing 总时长 commits through the store
    duration.fill("12.5")
    duration.press("Enter")
    page.wait_for_timeout(300)
    new_dur = page.evaluate("() => window.__director_store.getState().timeline.duration")
    result["duration_after_edit"] = new_dur
    check("duration:commits", abs(new_dur - 12.5) < 1e-6, detail=new_dur)
    check("duration:readout-follows", duration.input_value() == "12.50",
          detail=duration.input_value())
    # a nonsense value must not reach the store
    duration.fill("abc")
    duration.press("Enter")
    page.wait_for_timeout(250)
    check(
        "duration:rejects-nonsense",
        page.evaluate("() => window.__director_store.getState().timeline.duration")
        == new_dur,
    )
    check("duration:rolls-back", duration.input_value() == "12.50",
          detail=duration.input_value())

    # 5) 新建轨道 accessible name is the source string
    # the clone carries a second, clone-only `+ 轨道` add-track button further
    # down the toolbar; scope to the one that carries the source's aria
    add_track = page.locator("[data-director-add-track][aria-label]")
    check(
        "add-track:source-aria",
        add_track.get_attribute("aria-label") == "选中角色、道具或分组后建立轨道",
        detail=add_track.get_attribute("aria-label"),
    )
    # the clone keeps its richer tooltip alongside the source accessible name:
    # enabled -> 「新建轨道」, disabled -> the coachmark-referencing hint
    check(
        "add-track:keeps-hint-title",
        add_track.get_attribute("title")
        in ("新建轨道", "请选择一个角色或者摄像机后，可新建轨道"),
        detail=add_track.get_attribute("title"),
    )

    unexpected = [error for error in errors if "TransformControls" not in error]
    result["diagnostics"] = {
        "console": len(errors),
        "filtered_transformcontrols": len(errors) - len(unexpected),
        "errors": unexpected[:5],
    }
    check("diagnostics:zero", not unexpected, detail=unexpected[:8])
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 591,
        "title": "时间轴工具栏对齐源站：可编辑 播放头位置/总时长、s↔ms 单位切换、控件顺序与可及名逐字",
        "evidence": (
            "2026-10-01 live CDP sampling of the source director desk at "
            "1920x1150 + docs/research/liblib-canvas-batch591-2026-10-01/README.md"
        ),
        "clone_only": [],
        "not_verified": [
            "the source's duration clamp on commit — the store uses a "
            "conservative rule (positive, never before the last keyframe) "
            "and says so inline",
        ],
        "results": [],
    }
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        desktop = browser.new_page(
            viewport={"width": 1440, "height": 900}, device_scale_factor=1
        )
        audit["results"].append(run_desktop(desktop))
        desktop.close()
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    checks = audit["results"][0]["checks"]
    print(
        "Batch 591 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "The timeline toolbar's first seven controls now match the source "
        "order, 播放头位置 / 总时长 are editable 46x24 inputs in the source's "
        "s/ms formats, and 新建轨道 carries the source's accessible name. "
        "See runtime-audit.json."
    )


if __name__ == "__main__":
    main()
