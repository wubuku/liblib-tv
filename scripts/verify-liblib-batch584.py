#!/usr/bin/env python3
"""Verify Batch 584: 姿势 tab alignment with the 2026-10-01 source sampling.

Source evidence: live CDP sampling of the source director desk with 角色A
selected and the 姿势 tab open. Measured source structure:

  姿势预设  20 preset buttons in a 4-column grid
            站立 T型 行走 跑步 / 坐姿 蹲下 单膝跪 双膝跪 / 叉腰 倚靠 鞠躬 思考
            格斗 踢球 投掷 推进 / 招手 伸手 抱臂 看手机
  姿势调节  seven anatomical groups, all permanently expanded (no accordion),
            left/right sub-rows inside the limb groups, label above a
            full-width slider and **no numeric readout**:
            身体       前倾 ±90  转身 ±90  侧倾 ±45
            躯干       前倾 ±45  扭转 ±45  侧倾 ±30
            头部       点头 ±60  转头 ±90  歪头 ±30
            手臂 — 肩  左/右 前举 −90..180 外展 −10..90 扭转 ±90
            肘部       左/右 弯曲 0..150
            腿部 — 髋  左/右 前抬 ±90 外展 −30..60 扭转 ±45
            膝部       左/右 弯曲 0..150
            (all step=1)

The clone previously organised this as six bone-chain accordions
(身体/头颈/左臂/右臂/左腿/右腿) with a visible degree readout, wider
−135..135 ranges, and extra 根骨骼·高度 / 手腕 / 脚掌 sliders.

Contract asserted here:
1. seven groups with the source ids/labels, all marked expanded, no buttons;
2. left/right sub-rows in the four limb groups;
3. every joint slider carries the source label, range and step;
4. joint angles have no visible numeric readout (sr-only + aria);
5. the internal-only joints stay out of the UI but presets still apply them
   (a crouch preset must still move the hidden height joint);
6. a slider drag reaches the store and a preset still round-trips;
7. no diagnostics.
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
    / "liblib-canvas-batch584-2026-10-01"
    / "runtime-audit.json"
)

GROUP_IDS = [
    "body",
    "torso",
    "head",
    "arm-shoulder",
    "elbow",
    "leg-hip",
    "knee",
]
GROUP_LABELS = ["身体", "躯干", "头部", "手臂 — 肩", "肘部", "腿部 — 髋", "膝部"]
# key -> (label, min, max) straight from the source sampling
SOURCE_JOINTS = {
    "body.pitch": ("前倾", -90, 90),
    "body.yaw": ("转身", -90, 90),
    "body.roll": ("侧倾", -45, 45),
    "torso.pitch": ("前倾", -45, 45),
    "torso.yaw": ("扭转", -45, 45),
    "torso.roll": ("侧倾", -30, 30),
    "head.pitch": ("点头", -60, 60),
    "head.yaw": ("转头", -90, 90),
    "head.roll": ("歪头", -30, 30),
    "leftShoulder.pitch": ("前举", -90, 180),
    "leftShoulder.spread": ("外展", -10, 90),
    "leftShoulder.twist": ("扭转", -90, 90),
    "rightShoulder.pitch": ("前举", -90, 180),
    "rightShoulder.spread": ("外展", -10, 90),
    "rightShoulder.twist": ("扭转", -90, 90),
    "leftElbow.bend": ("弯曲", 0, 150),
    "rightElbow.bend": ("弯曲", 0, 150),
    "leftHip.pitch": ("前抬", -90, 90),
    "leftHip.spread": ("外展", -30, 60),
    "leftHip.twist": ("扭转", -45, 45),
    "rightHip.pitch": ("前抬", -90, 90),
    "rightHip.spread": ("外展", -30, 60),
    "rightHip.twist": ("扭转", -45, 45),
    "leftKnee.bend": ("弯曲", 0, 150),
    "rightKnee.bend": ("弯曲", 0, 150),
}
INTERNAL_ONLY = [
    "body.offsetY",
    "leftHand.pitch",
    "rightHand.roll",
    "leftFoot.pitch",
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


def set_range(page: Page, key: str, value: str) -> None:
    page.evaluate(
        """([key, value]) => {
          const el = document.querySelector(
            `[data-director-pose-control="${key}"]`);
          const setter = Object.getOwnPropertyDescriptor(
            window.HTMLInputElement.prototype, 'value').set;
          setter.call(el, value);
          el.dispatchEvent(new Event('input', { bubbles: true }));
          el.dispatchEvent(new Event('change', { bubbles: true }));
        }""",
        [key, value],
    )


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool, detail: Any = None) -> None:
        assert ok, f"batch584 check failed: {name} :: {detail}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/?batch70=1", wait_until="networkidle")
    page.wait_for_function(
        """() => Boolean(window.__libtv_store && window.__libtv_ui_store && window.__director_store)"""
    )
    page.evaluate(
        """() => {
          const store = window.__libtv_store.getState();
          store.addNode("script-execution", { title: "Batch 584" });
          const node = store.getActiveCanvas().nodes.at(-1);
          window.__libtv_ui_store.getState().openDirectorDesk(node.id, store.activeCanvasId);
        }"""
    )
    page.locator("[data-director-workspace]").wait_for(state="visible")
    page.wait_for_timeout(400)
    page.evaluate(
        """() => {
          const s = window.__director_store.getState();
          const character = s.objects.find((o) => o.kind === 'character');
          s.selectObject(character.id);
        }"""
    )
    page.locator("[data-director-character-tab='pose']").click()
    panel = page.locator("[data-director-pose-panel]")
    panel.wait_for(state="visible")
    page.wait_for_timeout(400)

    # 1) seven anatomical groups, permanently expanded, no accordion buttons
    group_ids = page.evaluate(
        """() => [...document.querySelectorAll('[data-director-pose-group]')]
             .map(el => el.getAttribute('data-director-pose-group'))"""
    )
    result["group_ids"] = group_ids
    check("groups:count", len(group_ids) == 7, detail=group_ids)
    check("groups:source-ids", group_ids == GROUP_IDS, detail=group_ids)
    check(
        "groups:all-expanded",
        page.locator('[data-director-pose-group][data-expanded="true"]').count() == 7,
    )
    check(
        "groups:no-accordion-buttons",
        page.locator("[data-director-pose-panel] button[aria-expanded]").count() == 0,
    )
    for label in GROUP_LABELS:
        check(f"groups:label-{label}", label in panel.inner_text())

    # 2) left/right sub-rows in the four limb groups
    check("sides:left-rows", page.locator('[data-director-pose-side="left"]').count() == 4)
    check("sides:right-rows", page.locator('[data-director-pose-side="right"]').count() == 4)

    # 3) every joint slider matches the source label/range/step
    sliders = page.evaluate(
        """() => {
          const out = {};
          document.querySelectorAll('[data-director-pose-control]').forEach((el) => {
            out[el.getAttribute('data-director-pose-control')] = {
              min: Number(el.getAttribute('min')),
              max: Number(el.getAttribute('max')),
              step: Number(el.getAttribute('step')),
            };
          });
          return out;
        }"""
    )
    result["sliders"] = sliders
    check("joints:count", len(sliders) == 25, detail=len(sliders))
    for key, (label, low, high) in SOURCE_JOINTS.items():
        entry = sliders.get(key)
        check(f"joint:{key}-present", entry is not None, detail=sorted(sliders))
        if entry is None:
            continue
        check(f"joint:{key}-range", entry["min"] == low and entry["max"] == high,
              detail=f"{entry} vs {low}..{high}")
        check(f"joint:{key}-step", entry["step"] == 1, detail=entry)
    joint_text = panel.inner_text()
    for label in ("前倾", "转身", "侧倾", "扭转", "点头", "转头", "歪头",
                  "前举", "外展", "前抬", "弯曲"):
        check(f"joint:label-{label}", label in joint_text)

    # 4) no visible numeric readout for joint angles
    readout = page.locator('[data-director-pose-value="body.pitch"]')
    check("readout:sr-only", "sr-only" in (readout.get_attribute("class") or ""))
    check("readout:aria", readout.get_attribute("aria-label") == "前倾角度")
    # sr-only keeps a 1×1 box, so Playwright still calls it "visible";
    # assert the box is visually collapsed instead.
    box = readout.bounding_box() or {"width": 99, "height": 99}
    check(
        "readout:not-visible",
        box["width"] <= 1 and box["height"] <= 1,
        detail=box,
    )

    # 5) internal-only joints are hidden but presets still drive them
    for key in INTERNAL_ONLY:
        check(
            f"internal:hidden-{key}",
            page.locator(f'[data-director-pose-control="{key}"]').count() == 0,
        )
    page.locator('[data-director-pose-preset="crouch"]').click()
    page.wait_for_timeout(350)
    crouch = page.evaluate(
        """() => window.__director_store.getState().objects
             .find(o => o.kind === 'character').characterRig.controls"""
    )
    result["crouch_controls"] = crouch
    check(
        "internal:preset-still-drives-height",
        "body.offsetY" in crouch and crouch["body.offsetY"] < 0,
        detail=crouch,
    )
    check(
        "internal:preset-label",
        page.locator("[data-director-pose-state]").get_attribute("data-pose-preset")
        == "crouch",
    )

    # 6) slider drag reaches the store; a preset round-trips back to stand
    set_range(page, "leftShoulder.spread", "60")
    page.wait_for_timeout(300)
    after_drag = page.evaluate(
        """() => window.__director_store.getState().objects
             .find(o => o.kind === 'character').characterRig.controls[
               'leftShoulder.spread']"""
    )
    check("drag:commits", after_drag == 60, detail=after_drag)
    page.locator('[data-director-pose-preset="stand"]').click()
    page.wait_for_timeout(350)
    after_stand = page.evaluate(
        """() => {
          const controls = window.__director_store.getState().objects
            .find(o => o.kind === 'character').characterRig.controls;
          return Object.prototype.hasOwnProperty.call(controls, 'leftShoulder.spread')
            ? controls['leftShoulder.spread']
            : 0;
        }"""
    )
    # 站立 预设的 controls 为空对象（键被移除而非置 0），按真实语义判定
    check("preset:stand-resets", after_stand == 0, detail=after_stand)
    check(
        "preset:stand-label",
        page.locator("[data-director-pose-state]").get_attribute("data-pose-preset")
        == "stand",
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
        "batch": 584,
        "title": "姿势 tab: seven anatomical groups permanently expanded, source joint labels/ranges, left-right sub-rows, no angle readout, internal joints hidden but preset-driven",
        "evidence": (
            "2026-10-01 live CDP sampling of the source director desk 姿势 tab "
            "+ docs/research/liblib-canvas-batch584-2026-10-01/README.md"
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
        "Batch 584 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "姿势 tab matches the 2026-10-01 source sampling: seven anatomical "
        "groups permanently expanded with source joint labels/ranges and "
        "left/right sub-rows. See runtime-audit.json."
    )


if __name__ == "__main__":
    main()
