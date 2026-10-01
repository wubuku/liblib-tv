#!/usr/bin/env python3
"""Verify Batch 588: 场景面板读数与开关行形态对齐源站（2026-10-01 实测）。

Source facts (live CDP sampling of the source 3D场景 panel at 1920x1150):

Slider readouts are EDITABLE `input[type=text]` boxes, not read-only text.
All five carry `readOnly=false` / `disabled=false` and share one style:

    focus:bg-white/13 h-7 min-w-px flex-1 rounded-lg border-0 ...

  场景缩放    70x28  `300%`   range 0.1..10  step 0.1
  水平旋转    70x28  `0°`     range 0..360  step 1
  球形半径    70x28  `60`     range 10..500 step 10   (no unit)
  透明度      62x28  `0.40`   range 0..1    step 0.05 (two decimals)
  高度        62x28  `0.0`    range -2..2   step 0.05 (one decimal)

The 天空颜色 hex box is the same family but `maxLength=6` and its
`uppercase` is a CSS `text-transform` — the computed style is `uppercase`
while the underlying value keeps whatever case was typed.

The three scene switches are NOT native checkboxes. Each is a full-width
`button` (280x56, transparent background, `space-between` / `center`) with a
label span plus a 24x14 fully-rounded track and a 10x10 knob:

  on  = track rgb(255,255,255),       knob rgb(31,31,31) at track x+12
  off = track rgba(255,255,255,0.18), knob at track x+2

`地面` uses the same construction at 240x15 (a nested row, not full width).

The left search box placeholder is `请输入搜索内容` (216x32, no aria-label).
`搜索场景对象` is a separate 1x1 span acting as the a11y label — a different
string, not the placeholder.

NOT verified (recorded, not fabricated): whether the source commits the typed
value on blur, how it clamps, and the default 球形半径 (the sampled `60` may
already have been edited in the user's project). This batch therefore reuses
the commit pattern batch 585 already source-verified on the sibling hex row
(commit while typing, revert to the last legal value on blur, clamp to the
range's own min/max) and keeps the source-verified *formats* verbatim.
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
    / "liblib-canvas-batch588-2026-10-01"
    / "runtime-audit.json"
)

TOGGLES = [
    ("角色标签", "data-director-scene-character-labels", True),
    ("网格吸附", "data-director-scene-snap-to-grid", False),
    ("高斯地面吸附", "data-director-scene-gaussian-snap", True),
]

READOUT_FORMATS = {
    "scale": r"^\d+%$",
    "panorama-rotation": r"^\d+°$",
    "sphere-radius": r"^\d+$",
    "ground-opacity": r"^\d\.\d{2}$",
    "ground-height": r"^-?\d+\.\d$",
}


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
        assert ok, f"batch588 check failed: {name} :: {detail}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/?batch70=1", wait_until="networkidle")
    page.wait_for_function(
        """() => Boolean(window.__libtv_store && window.__libtv_ui_store && window.__director_store)"""
    )
    page.evaluate(
        """() => {
          const store = window.__libtv_store.getState();
          store.addNode("script-execution", { title: "Batch 588" });
          const node = store.getActiveCanvas().nodes.at(-1);
          window.__libtv_ui_store.getState().openDirectorDesk(node.id, store.activeCanvasId);
        }"""
    )
    page.locator("[data-director-workspace]").wait_for(state="visible")
    page.wait_for_timeout(500)

    # The 3D场景 panel only renders with no object selected (batch 89 relies
    # on the same behaviour).
    page.locator("[data-director-selection-action='clear']").click()
    scene_panel = page.locator("[data-director-scene-settings]")
    scene_panel.wait_for(state="visible")

    # 1) all five readouts are editable text inputs in the source format
    for test_id, pattern in READOUT_FORMATS.items():
        readout = page.locator(f"[data-director-scene-readout='{test_id}']")
        check(f"readout:{test_id}:present", readout.count() == 1)
        check(
            f"readout:{test_id}:type-text",
            readout.get_attribute("type") == "text",
        )
        check(
            f"readout:{test_id}:editable",
            readout.evaluate("el => el.readOnly === false && el.disabled === false"),
        )
        text = readout.input_value().strip()
        check(
            f"readout:{test_id}:source-format",
            __import__("re").match(pattern, text) is not None,
            detail=text,
        )
    result["readouts"] = {
        test_id: page.locator(
            f"[data-director-scene-readout='{test_id}']"
        ).input_value()
        for test_id in READOUT_FORMATS
    }

    # the scene-scale readout is a percentage of the stored multiplier
    stored_scale = page.evaluate(
        "() => window.__director_store.getState().scene.sceneScale ?? 1"
    )
    check(
        "readout:scale:is-percent-of-store",
        result["readouts"]["scale"] == f"{round(stored_scale * 100)}%",
        detail=(stored_scale, result["readouts"]["scale"]),
    )

    # 2) no plain-span readout is left behind for these five rows
    check(
        "readout:no-legacy-span",
        page.locator("[data-director-scene-settings] span.tabular-nums").count() == 0,
    )

    # 3) hex box: maxLength 6 + CSS text-transform uppercase
    # (source-measured: computed textTransform=uppercase while the underlying
    # value keeps whatever case was typed — NOT a value transform, which would
    # fight the store's lowercase convention fixed in batch 585)
    hex_box = page.locator("[data-director-hex-input='sky']")
    check("hex:maxlength", hex_box.get_attribute("maxlength") == "6")
    check(
        "hex:uppercase-is-css",
        hex_box.evaluate("el => getComputedStyle(el).textTransform") == "uppercase",
        detail=hex_box.evaluate("el => getComputedStyle(el).textTransform"),
    )
    hex_box.fill("aabbcc")
    check(
        "hex:keeps-typed-case",
        hex_box.input_value() == "aabbcc",
        detail=hex_box.input_value(),
    )
    check(
        "hex:commits-lowercase-store",
        page.evaluate(
            "() => window.__director_store.getState().scene.skyColor"
        )
        == "#aabbcc",
        detail=page.evaluate(
            "() => window.__director_store.getState().scene.skyColor"
        ),
    )

    # 4) the three switches are self-drawn switch buttons, not checkboxes
    for label, attr, _default_on in TOGGLES:
        row = page.locator(f"[{attr}]")
        check(f"toggle:{label}:is-button", row.evaluate("el => el.tagName") == "BUTTON")
        check(
            f"toggle:{label}:role-switch",
            row.get_attribute("role") == "switch",
        )
        check(
            f"toggle:{label}:aria-checked",
            row.get_attribute("aria-checked") in ("true", "false"),
            detail=row.get_attribute("aria-checked"),
        )
        track = row.locator("[data-director-scene-toggle-track]")
        knob = row.locator("[data-director-scene-toggle-knob]")
        check(f"toggle:{label}:track-24x14", track.bounding_box() is not None
              and round(track.bounding_box()["width"]) == 24
              and round(track.bounding_box()["height"]) == 14,
              detail=track.bounding_box())
        check(f"toggle:{label}:knob-10x10", knob.bounding_box() is not None
              and round(knob.bounding_box()["width"]) == 10
              and round(knob.bounding_box()["height"]) == 10,
              detail=knob.bounding_box())
        check(
            f"toggle:{label}:no-native-checkbox",
            row.evaluate("el => el.querySelector('input[type=checkbox]') === null"),
        )

    # 5) the knob actually moves and the store follows
    grid = page.locator("[data-director-scene-snap-to-grid]")
    check("toggle:grid:starts-off", grid.get_attribute("aria-checked") == "false")
    knob_before = grid.locator("[data-director-scene-toggle-knob]").bounding_box()
    grid.click()
    page.wait_for_timeout(120)
    check("toggle:grid:turns-on", grid.get_attribute("aria-checked") == "true")
    check(
        "toggle:grid:store-follows",
        page.evaluate("() => window.__director_store.getState().scene.snapToGrid")
        is True,
    )
    knob_after = grid.locator("[data-director-scene-toggle-knob]").bounding_box()
    check(
        "toggle:grid:knob-moves-right",
        knob_after["x"] - knob_before["x"] > 6,
        detail=(knob_before, knob_after),
    )
    grid.click()
    page.wait_for_timeout(120)
    check("toggle:grid:turns-off-again", grid.get_attribute("aria-checked") == "false")

    # 6) left search box placeholder is the source string
    search = page.get_by_placeholder("请输入搜索内容")
    check("search:present", search.count() == 1)
    check(
        "search:still-labels-itself",
        search.get_attribute("aria-label") == "搜索场景内容",
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
        "batch": 588,
        "title": "场景面板读数改为可编辑文本框 + 开关行自绘轨道/旋钮 + 搜索框 placeholder 对齐源站",
        "evidence": (
            "2026-10-01 live CDP sampling of the source 3D场景 panel at "
            "1920x1150 + docs/research/liblib-canvas-batch588-2026-10-01/README.md"
        ),
        "not_verified": [
            "whether the source commits the typed readout on blur, and how it "
            "clamps — this batch reuses the batch 585 hex-row commit pattern "
            "instead of inventing a rule",
            "the default 球形半径: the sampled 60 may have been edited in the "
            "user's project, so the clone keeps its own default",
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
        "Batch 588 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "Scene readouts are editable text inputs in the source formats, the "
        "three switches are self-drawn 24x14 track + 10x10 knob rows, and the "
        "search placeholder matches. See runtime-audit.json."
    )


if __name__ == "__main__":
    main()
