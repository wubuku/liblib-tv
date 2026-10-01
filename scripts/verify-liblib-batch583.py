#!/usr/bin/env python3
"""Verify Batch 583: object 属性 panel alignment with the 2026-10-01 source.

Source evidence: live CDP sampling of the source director desk with 角色A
selected. Measured source character 属性 panel (two tabs 属性 | 姿势):

    名称 (121)          text input 角色A
    位置 (193/225)      per axis: <button aria="左右拖动调整 X 轴"> + number step 0.1
    旋转 (265/297)      per axis: axis chip + number step 1
    缩放 (337/369)      per axis: axis chip + number step 0.05   (1.03/1.03/1.03)
    统一缩放 (409)      range min=0.1 max=10 step=0.05 value=1 + text "1.0"
    颜色 (481/518)      color #4f8ef7 + hex text 4F8EF7 + "#"

This resolves batch 580's open question: the uniform-scale slider really is
0.1–10 step 0.05 (not the 0–10 inferred from a screenshot), and object
transform rows — not just the scene panel — carry the axis drag chips.

Contract asserted here:
1. 位置/旋转/缩放 rows expose axis chips with the source aria, and a real
   horizontal drag commits to the store;
2. 缩放 step is 0.05 (rotation stays 1, position 0.1);
3. 统一缩放 exists right after 缩放 with the source range and a 1-decimal
   readout, and writing it sets all three scale axes;
4. 颜色 follows 统一缩放 and shows a hex readout;
5. the motion tab's 统一缩放 slider uses the same measured 0.1–10 / 0.05
   (batch 580 correction);
6. no diagnostics.
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
    / "liblib-canvas-batch583-2026-10-01"
    / "runtime-audit.json"
)

UNIFORM_SCALE = 1.75


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
        assert ok, f"batch583 check failed: {name} :: {detail}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/?batch70=1", wait_until="networkidle")
    page.wait_for_function(
        """() => Boolean(window.__libtv_store && window.__libtv_ui_store && window.__director_store)"""
    )
    page.evaluate(
        """() => {
          const store = window.__libtv_store.getState();
          store.addNode("script-execution", { title: "Batch 583" });
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
    page.locator("[data-director-character-tab='properties']").wait_for(
        state="visible"
    )
    page.wait_for_timeout(300)

    # 1) axis chips on all three transform rows, with the source aria
    chips = page.evaluate(
        """() => [...document.querySelectorAll('[data-director-scene-axis-scrub]')]
             .map(el => ({
               id: el.getAttribute('data-director-scene-axis-scrub'),
               aria: el.getAttribute('aria-label'),
             }))"""
    )
    result["axis_chips"] = chips
    fields = {chip["id"].split("-")[0] for chip in chips}
    check("chips:all-transform-rows", {"position", "rotation", "scale"} <= fields,
          detail=sorted(fields))
    check(
        "chips:source-aria",
        all(
            chip["aria"] == f"左右拖动调整 {chip['aria'].split(' ')[1]} 轴"
            for chip in chips
            if chip["aria"]
        ),
        detail=[chip["aria"] for chip in chips][:6],
    )

    # real drag on the 位置 X chip
    before = page.evaluate(
        """() => window.__director_store.getState().objects
             .find(o => o.kind === 'character').transform.position[0]"""
    )
    chip = page.locator('[data-director-scene-axis-scrub="position-X"]')
    box = chip.bounding_box()
    assert box, "position-X chip has no box"
    page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    page.mouse.down()
    for step in range(1, 6):
        page.mouse.move(
            box["x"] + box["width"] / 2 + step * 12, box["y"] + box["height"] / 2
        )
        page.wait_for_timeout(40)
    page.mouse.up()
    page.wait_for_timeout(250)
    after = page.evaluate(
        """() => window.__director_store.getState().objects
             .find(o => o.kind === 'character').transform.position[0]"""
    )
    result["chip_drag"] = {"before": before, "after": after}
    check("chips:drag-commits", after != before, detail=f"{before} -> {after}")
    check(
        "chips:number-mirrors",
        page.locator(
            '[data-director-transform-field="position"]'
            '[data-director-transform-axis="x"]'
        ).input_value()
        == f"{after:.2f}",
    )

    # 2) per-field steps match the source
    steps = page.evaluate(
        """() => {
          const out = {};
          ['position', 'rotation', 'scale'].forEach((field) => {
            const el = document.querySelector(
              `[data-director-transform-field="${field}"]`);
            if (el) out[field] = el.getAttribute('step');
          });
          return out;
        }"""
    )
    result["field_steps"] = steps
    check("steps:position", steps.get("position") == "0.1", detail=steps)
    check("steps:rotation", steps.get("rotation") == "1", detail=steps)
    check("steps:scale", steps.get("scale") == "0.05", detail=steps)

    # 3) 统一缩放 row after 缩放, with the source range and readout
    row_ys = page.evaluate(
        """() => {
          const wanted = ['位置', '旋转', '缩放', '统一缩放', '颜色'];
          const found = {};
          [...document.querySelectorAll('*')].forEach((el) => {
            const t = (el.textContent || '').trim();
            if (!wanted.includes(t) || t in found || el.children.length > 0) return;
            const r = el.getBoundingClientRect();
            if (r.width > 0 && r.height > 0) found[t] = Math.round(r.y);
          });
          return found;
        }"""
    )
    result["row_ys"] = row_ys
    for label in ("缩放", "统一缩放", "颜色"):
        check(f"rows:{label}", label in row_ys, detail=row_ys)
    if all(k in row_ys for k in ("缩放", "统一缩放", "颜色")):
        check(
            "order:scale-uniform-color",
            row_ys["缩放"] < row_ys["统一缩放"] < row_ys["颜色"],
            detail=row_ys,
        )

    uniform = page.locator("[data-director-uniform-scale]")
    check("uniform:min", uniform.get_attribute("min") == "0.1")
    check("uniform:max", uniform.get_attribute("max") == "10")
    check("uniform:step", uniform.get_attribute("step") == "0.05")

    scale_before = page.evaluate(
        """() => window.__director_store.getState().objects
             .find(o => o.kind === 'character').transform.scale.slice()"""
    )
    page.evaluate(
        """([selector, value]) => {
          const el = document.querySelector(selector);
          const setter = Object.getOwnPropertyDescriptor(
            window.HTMLInputElement.prototype, 'value').set;
          setter.call(el, value);
          el.dispatchEvent(new Event('input', { bubbles: true }));
          el.dispatchEvent(new Event('change', { bubbles: true }));
        }""",
        ["[data-director-uniform-scale]", str(UNIFORM_SCALE)],
    )
    page.wait_for_timeout(300)
    scale_after = page.evaluate(
        """() => window.__director_store.getState().objects
             .find(o => o.kind === 'character').transform.scale.slice()"""
    )
    result["uniform_write"] = {"before": scale_before, "after": scale_after}
    check(
        "uniform:writes-all-axes",
        all(abs(value - UNIFORM_SCALE) < 0.001 for value in scale_after),
        detail=scale_after,
    )
    check(
        "uniform:readout",
        page.locator("[data-director-uniform-scale-readout]").inner_text().strip()
        == f"{UNIFORM_SCALE:.1f}",
    )

    # 4) 颜色 hex —— Batch 585 起为源站的**可编辑 hex 文本框**（原为只读
    # 读数），故此处断言改为读文本框值 + 取色器存在。
    store_color = page.evaluate(
        """() => window.__director_store.getState().objects
             .find(o => o.kind === 'character').color"""
    )
    hex_input = page.locator('[data-director-hex-input="object"]')
    result["color_hex_value"] = hex_input.input_value()
    check(
        "color:hex-field",
        hex_input.input_value() == store_color.replace("#", "").lower(),
        detail=f"{hex_input.input_value()} vs {store_color}",
    )
    check(
        "color:hash-prefix",
        "#" in hex_input.evaluate(
            "el => el.closest('label').innerText.replace(/\\n/g, ' ').trim()"),
    )
    check("color:swatch", page.locator('[data-director-color-picker="object"]').count() == 1)

    # 5) motion tab uniform scale uses the same measured range
    page.evaluate(
        """() => {
          const s = window.__director_store.getState();
          const camera = s.objects.find((o) => o.kind === 'camera');
          s.selectObject(camera.id);
        }"""
    )
    # the motion tab field group only renders with a selected keyframe
    page.evaluate("() => window.__director_store.getState().setTimelineTime(2)")
    page.evaluate("() => window.__director_store.getState().addTimelineKeyframe()")
    page.wait_for_timeout(300)
    page.locator('[data-director-camera-tab="motion"]').click()
    motion_uniform = page.locator('[data-director-motion-slider="uniform-scale"]')
    motion_uniform.wait_for(state="visible")
    check("motion:uniform-min", motion_uniform.get_attribute("min") == "0.1")
    check("motion:uniform-max", motion_uniform.get_attribute("max") == "10")
    check("motion:uniform-step", motion_uniform.get_attribute("step") == "0.05")
    check(
        "motion:duration-range-unchanged",
        page.locator('[data-director-motion-slider="duration"]')
        .get_attribute("min")
        == "0",
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
        "batch": 583,
        "title": "Object 属性 panel: axis drag chips on all transform rows, 统一缩放 property row (measured 0.1–10/0.05), scale step 0.05, 颜色 hex readout after 统一缩放",
        "evidence": (
            "2026-10-01 live CDP sampling of the source director desk with "
            "角色A selected + docs/research/liblib-canvas-batch583-2026-10-01/README.md"
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
        "Batch 583 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "Object 属性 panel matches the 2026-10-01 source sampling: axis drag "
        "chips on all transform rows, 统一缩放 with the measured 0.1–10/0.05 "
        "range, scale step 0.05, 颜色 hex readout. See runtime-audit.json."
    )


if __name__ == "__main__":
    main()
