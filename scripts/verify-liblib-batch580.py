#!/usr/bin/env python3
"""Verify Batch 580: camera motion-track keyframe editor fields.

Source evidence: screenshot 64
(docs/research/liblib-source-exploration-2026-09-25/64-director-diamond-dragged.png,
right panel crop 3180-3840 x 1140-1960) — the camera 运动轨迹 tab keyframe
field group is 时长 / 位置 / 旋转 / 缩放 / 统一缩放, where 时长 and 统一缩放 are
**slider + numeric box** rows (grey track, cyan filled segment, white round
thumb), not plain text.

Contract asserted here:
1. field group order 时长 → 位置 → 旋转 → 缩放 → 统一缩放;
2. camera-track keyframe values render as finite numbers — batch 576 read
   value[field] while camera keyframes store { transform, target, fov }, so the
   motion tab (the only camera context) showed NaN;
3. 时长 slider + box mirror the playhead time and commit a seek;
4. 统一缩放 mirrors scale[0] of the selected keyframe and writes all three
   scale axes;
5. edits commit to the **selected** keyframe even when the playhead sits
   elsewhere (updateObjectTransform lands on the playhead);
6. no keyframe is created at the stray playhead time.
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
    / "liblib-canvas-batch580-2026-10-01"
    / "runtime-audit.json"
)

KEYFRAME_TIME = 2.0
STRAY_TIME = 5.0
UNIFORM_SCALE = 2.5
POSITION_X = 7.5


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


def read_selected_keyframe(page: Page) -> dict[str, Any]:
    return page.evaluate(
        """() => {
          const s = window.__director_store.getState();
          const track = s.timeline.tracks.find(
            (t) => t.objectId === s.selectedObjectId
              && (t.kind === 'transform' || t.kind === 'camera'));
          const keyframe = track?.keyframes.find(
            (k) => k.id === s.timeline.selectedKeyframeId) ?? null;
          return {
            trackKind: track?.kind ?? null,
            keyframeId: keyframe?.id ?? null,
            keyframeTime: keyframe?.time ?? null,
            keyframeCount: track?.keyframes.length ?? 0,
            playhead: s.timeline.currentTime,
            position: keyframe ? (keyframe.value.transform ?? keyframe.value).position : null,
            scale: keyframe ? (keyframe.value.transform ?? keyframe.value).scale : null,
          };
        }"""
    )


def axis_input_value(page: Page, field: str, axis: int) -> str:
    return page.locator(
        f'[data-director-motion-keyframe-field="{field}"]'
        f'[data-director-motion-keyframe-axis="{axis}"]'
    ).input_value()


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool, detail: Any = None) -> None:
        assert ok, f"batch580 check failed: {name} :: {detail}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/?batch70=1", wait_until="networkidle")
    page.wait_for_function(
        """() => Boolean(window.__libtv_store && window.__libtv_ui_store && window.__director_store)"""
    )

    page.evaluate(
        """() => {
          const store = window.__libtv_store.getState();
          store.addNode("script-execution", { title: "Batch 580" });
          const node = store.getActiveCanvas().nodes.at(-1);
          window.__libtv_ui_store.getState().openDirectorDesk(node.id, store.activeCanvasId);
        }"""
    )
    page.locator("[data-director-workspace]").wait_for(state="visible")
    page.wait_for_timeout(400)

    # select the camera, then place a keyframe at a non-zero time
    page.evaluate(
        """() => {
          const s = window.__director_store.getState();
          const camera = s.objects.find((o) => o.kind === 'camera');
          if (!camera) throw new Error('no camera in the director scene');
          s.selectObject(camera.id);
        }"""
    )
    page.evaluate("() => window.__director_store.getState().setTimelineTime(2)")
    page.evaluate("() => window.__director_store.getState().addTimelineKeyframe()")
    page.wait_for_timeout(300)

    before = read_selected_keyframe(page)
    check("setup:camera-track", before["trackKind"] == "camera")
    check("setup:keyframe-selected", before["keyframeId"] is not None)
    check(
        "setup:keyframe-time",
        before["keyframeTime"] is not None
        and abs(before["keyframeTime"] - KEYFRAME_TIME) < 0.001,
    )
    result["keyframe_before"] = before

    # 运动轨迹 tab
    page.locator('[data-director-camera-tab="motion"]').click()
    editor = page.locator("[data-director-motion-keyframe-editor]")
    editor.wait_for(state="visible")
    page.wait_for_timeout(200)
    check("editor:visible", editor.is_visible())

    # 1) field group order matches the source screenshot
    labels = editor.locator("span.block").all_inner_texts()
    result["field_group_labels"] = labels
    check(
        "layout:field-order",
        [label.strip() for label in labels if label.strip()]
        == ["时长", "位置", "旋转", "缩放", "统一缩放"],
    )

    # 2) camera keyframe values are finite (batch 576 rendered NaN here)
    for field in ("position", "rotation", "scale"):
        for axis in (0, 1, 2):
            raw = axis_input_value(page, field, axis)
            check(
                f"values:{field}-{axis}-finite",
                raw not in ("", "NaN") and _is_number(raw),
            )
    result["mirrored"] = {
        field: [axis_input_value(page, field, axis) for axis in (0, 1, 2)]
        for field in ("position", "rotation", "scale")
    }

    # 3) 时长 slider + box exist, mirror the playhead, and use the source
    #    grey-track/cyan-fill slider geometry
    duration_range = page.locator('[data-director-motion-slider="duration"]')
    duration_box = page.locator('[data-director-motion-slider-value="duration"]')
    check("duration:range-visible", duration_range.is_visible())
    check("duration:box-visible", duration_box.is_visible())
    check("duration:range-max", duration_range.get_attribute("max") == "10")
    check(
        "duration:mirrors-playhead",
        abs(float(duration_box.input_value()) - KEYFRAME_TIME) < 0.001,
    )
    fill = duration_range.evaluate("el => getComputedStyle(el).backgroundImage")
    result["duration_slider_fill"] = fill
    # computed style normalises #09caf5 to rgb(9, 202, 245); the fill stop
    # must also track the value ratio (source: cyan filled segment).
    normalized_fill = fill.replace(" ", "").lower()
    expected_percent = round(
        float(duration_box.input_value()) / 10 * 100
    )
    result["duration_slider_expected_percent"] = expected_percent
    check(
        "duration:cyan-fill",
        "linear-gradient" in normalized_fill
        and (
            "09caf5" in normalized_fill
            or "rgb(9,202,245)" in normalized_fill
        )
        and f"{expected_percent}%" in normalized_fill,
    )

    duration_box.fill("3.25")
    duration_box.dispatch_event("change")
    page.wait_for_timeout(250)
    check(
        "duration:seek-committed",
        abs(
            page.evaluate(
                "window.__director_store.getState().timeline.currentTime"
            )
            - 3.25
        )
        < 0.001,
    )
    page.evaluate(
        f"() => window.__director_store.getState().setTimelineTime({KEYFRAME_TIME})"
    )
    page.wait_for_timeout(200)

    # 4) 统一缩放 mirrors scale[0] and writes all three axes
    uniform_box = page.locator('[data-director-motion-slider-value="uniform-scale"]')
    check("uniform:box-visible", uniform_box.is_visible())
    mirrored_scale = read_selected_keyframe(page)["scale"]
    check(
        "uniform:mirrors-scale-x",
        abs(float(uniform_box.input_value()) - float(mirrored_scale[0])) < 0.001,
    )
    uniform_box.fill(str(UNIFORM_SCALE))
    uniform_box.dispatch_event("change")
    page.wait_for_timeout(300)
    after_uniform = read_selected_keyframe(page)
    result["keyframe_after_uniform"] = after_uniform
    check(
        "uniform:writes-all-axes",
        all(abs(value - UNIFORM_SCALE) < 0.001 for value in after_uniform["scale"]),
    )
    check(
        "uniform:mirrored-back",
        all(
            abs(float(axis_input_value(page, "scale", axis)) - UNIFORM_SCALE) < 0.001
            for axis in (0, 1, 2)
        ),
    )

    # 5) an edit commits to the selected keyframe even when the playhead moved
    stray_count = after_uniform["keyframeCount"]
    page.evaluate(
        f"() => window.__director_store.getState().setTimelineTime({STRAY_TIME})"
    )
    page.wait_for_timeout(200)
    check(
        "stray:playhead-moved",
        page.evaluate(
            "window.__director_store.getState().timeline.currentTime"
        )
        == STRAY_TIME,
    )
    position_x = page.locator(
        '[data-director-motion-keyframe-field="position"]'
        '[data-director-motion-keyframe-axis="0"]'
    )
    position_x.fill(str(POSITION_X))
    position_x.dispatch_event("change")
    page.wait_for_timeout(300)
    after_position = read_selected_keyframe(page)
    result["keyframe_after_position"] = after_position
    check(
        "commit:selected-keyframe-updated",
        abs(after_position["position"][0] - POSITION_X) < 0.001,
    )
    check(
        "commit:playhead-aligned-back",
        abs(after_position["playhead"] - KEYFRAME_TIME) < 0.001,
    )
    check(
        "commit:no-stray-keyframe",
        after_position["keyframeCount"] == stray_count,
    )

    # 已知瞬态（batch 36/553/558 同样显式过滤）：选中摄像机时
    # TransformControls attach 抛 "must be a part of the scene graph"，
    # 与本批字段组无关（AGENTS.md §5 记录 TransformControls 显式挂载约束）。
    unexpected = [
        error for error in errors if "TransformControls" not in error
    ]
    result["diagnostics"] = {
        "console": len(errors),
        "filtered_transformcontrols": len(errors) - len(unexpected),
        "errors": unexpected[:5],
    }
    check("diagnostics:zero", not unexpected, detail=unexpected[:8])
    return result


def _is_number(raw: str) -> bool:
    try:
        float(raw)
    except (TypeError, ValueError):
        return False
    return True


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 580,
        "title": "Camera motion-track keyframe editor: 时长/统一缩放 sliders, finite camera values, selected-keyframe commits",
        "evidence": (
            "docs/research/liblib-source-exploration-2026-09-25/"
            "64-director-diamond-dragged.png (right panel field group) + "
            "docs/research/liblib-canvas-batch580-2026-10-01/README.md"
        ),
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
        "Batch 580 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "Camera 运动轨迹 keyframe editor renders the source field group "
        "(时长/位置/旋转/缩放/统一缩放), mirrors finite camera-track values, and "
        "commits edits to the selected keyframe. See runtime-audit.json."
    )


if __name__ == "__main__":
    main()
