#!/usr/bin/env python3
"""Verify Batch 585: colour rows use the source's editable hex field.

Source evidence: live CDP sampling of the source director desk on 2026-10-01.
Every colour row is `#` prefix + an **editable hex text input** + a colour
picker, all on one line:

  character 颜色  (y=481/513/518)  color #4f8ef7 + text 4F8EF7 + "#"
  scene 天空颜色   (y=452/457)      color #060608 + text 060608 + "#"

Batch 582/583 only added a read-only hex readout; this batch replaces it with
the source's editable field. Batch 585 also closes two evidence questions
left open by 584: the source 姿势 tab ends at 膝部 (no ankle/foot groups —
the panel scrolls to its end at 膝部右 弯曲), and the camera 属性 position /
rotation rows do carry the same axis chips as the character rows.

Contract asserted here:
1. both colour rows expose `#` + hex text input + picker;
2. the hex input mirrors the store value and commits a valid 6-digit hex
   (with or without `#`, case-normalised);
3. an invalid hex does not commit and reverts on blur;
4. the picker still commits;
5. camera 属性 rows carry the axis chips (584 follow-up #2);
6. 25 pose joints across the seven source groups (584 completeness);
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
    / "liblib-canvas-batch585-2026-10-01"
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
NEW_HEX = "1a7f5c"
BAD_HEX = "zzz"


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


def read_color(page: Page, expression: str) -> str:
    return page.evaluate(expression)


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool, detail: Any = None) -> None:
        assert ok, f"batch585 check failed: {name} :: {detail}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/?batch70=1", wait_until="networkidle")
    page.wait_for_function(
        """() => Boolean(window.__libtv_store && window.__libtv_ui_store && window.__director_store)"""
    )
    page.evaluate(
        """() => {
          const store = window.__libtv_store.getState();
          store.addNode("script-execution", { title: "Batch 585" });
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

    # 1) source-shaped colour row: # prefix + hex text + picker
    hex_input = page.locator('[data-director-hex-input="object"]')
    picker = page.locator('[data-director-color-picker="object"]')
    check("color:hex-input", hex_input.count() == 1)
    check("color:picker", picker.count() == 1)
    check("color:picker-type", picker.get_attribute("type") == "color")
    check("color:aria", hex_input.get_attribute("aria-label") == "颜色 hex 值")
    row_text = hex_input.evaluate(
        "el => el.closest('label').innerText.replace(/\\n/g, ' ').trim()"
    )
    result["color_row_text"] = row_text
    check("color:hash-prefix", "#" in row_text, detail=row_text)

    # 2) the hex input mirrors the store and commits a bare 6-digit value
    store_color = read_color(
        page,
        """() => window.__director_store.getState().objects
             .find(o => o.kind === 'character').color""",
    )
    check(
        "color:mirrors-store",
        hex_input.input_value() == store_color.replace("#", ""),
        detail=f"{hex_input.input_value()} vs {store_color}",
    )
    hex_input.fill(NEW_HEX)
    page.wait_for_timeout(300)
    after_hex = read_color(
        page,
        """() => window.__director_store.getState().objects
             .find(o => o.kind === 'character').color""",
    )
    check("color:hex-commits", after_hex == f"#{NEW_HEX}", detail=after_hex)
    check(
        "color:input-follows-store",
        hex_input.input_value() == NEW_HEX,
        detail=hex_input.input_value(),
    )

    # a '#'-prefixed value is accepted too
    hex_input.fill(f"#{NEW_HEX.upper()}")
    page.wait_for_timeout(300)
    prefixed = read_color(
        page,
        """() => window.__director_store.getState().objects
             .find(o => o.kind === 'character').color""",
    )
    check("color:accepts-hash-prefix", prefixed == f"#{NEW_HEX}", detail=prefixed)

    # 3) an invalid hex must not commit and reverts on blur
    hex_input.fill(BAD_HEX)
    page.wait_for_timeout(250)
    still = read_color(
        page,
        """() => window.__director_store.getState().objects
             .find(o => o.kind === 'character').color""",
    )
    check("color:invalid-rejected", still == f"#{NEW_HEX}", detail=still)
    hex_input.blur()
    page.wait_for_timeout(250)
    check(
        "color:invalid-reverts-on-blur",
        hex_input.input_value() == NEW_HEX,
        detail=hex_input.input_value(),
    )

    # 4) the picker still commits
    page.evaluate(
        """() => {
          const el = document.querySelector('[data-director-color-picker="object"]');
          const setter = Object.getOwnPropertyDescriptor(
            window.HTMLInputElement.prototype, 'value').set;
          setter.call(el, '#336699');
          el.dispatchEvent(new Event('input', { bubbles: true }));
          el.dispatchEvent(new Event('change', { bubbles: true }));
        }"""
    )
    page.wait_for_timeout(300)
    after_picker = read_color(
        page,
        """() => window.__director_store.getState().objects
             .find(o => o.kind === 'character').color""",
    )
    check("color:picker-commits", after_picker == "#336699", detail=after_picker)

    # 5) camera 属性 rows carry the axis chips (584 follow-up #2)
    page.evaluate(
        """() => {
          const s = window.__director_store.getState();
          const camera = s.objects.find((o) => o.kind === 'camera');
          s.selectObject(camera.id);
        }"""
    )
    page.locator('[data-director-camera-tab="properties"]').wait_for(state="visible")
    page.wait_for_timeout(300)
    cam_chips = page.evaluate(
        """() => [...document.querySelectorAll('[data-director-scene-axis-scrub]')]
             .map(el => el.getAttribute('data-director-scene-axis-scrub'))"""
    )
    result["camera_axis_chips"] = cam_chips
    for field in ("position", "rotation", "target"):
        check(
            f"camera:chips-{field}",
            any(chip.startswith(f"{field}-") for chip in cam_chips),
            detail=cam_chips,
        )

    # 6) 584 completeness: seven groups, 25 joints (no ankle/foot group exists)
    page.evaluate(
        """() => {
          const s = window.__director_store.getState();
          const character = s.objects.find((o) => o.kind === 'character');
          s.selectObject(character.id);
        }"""
    )
    page.locator("[data-director-character-tab='pose']").click()
    pose_panel = page.locator("[data-director-pose-panel]")
    pose_panel.wait_for(state="visible")
    page.wait_for_timeout(300)
    group_ids = page.evaluate(
        """() => [...document.querySelectorAll('[data-director-pose-group]')]
             .map(el => el.getAttribute('data-director-pose-group'))"""
    )
    check("pose:seven-groups", group_ids == GROUP_IDS, detail=group_ids)
    check(
        "pose:25-joints",
        page.locator("[data-director-pose-control]").count() == 25,
    )
    pose_text = pose_panel.inner_text()
    for absent in ("踝", "脚掌", "脚"):
        check(f"pose:no-{absent}-group", absent not in pose_text)

    # 7) scene sky colour row uses the same editable field
    page.evaluate("() => window.__director_store.getState().selectObject(null)")
    sky = page.locator('[data-director-hex-input="sky"]')
    sky.wait_for(state="visible")
    check("sky:hex-input", sky.count() == 1)
    check("sky:picker", page.locator('[data-director-color-picker="sky"]').count() == 1)
    sky.fill("102030")
    page.wait_for_timeout(300)
    sky_store = page.evaluate(
        "() => window.__director_store.getState().scene.skyColor"
    )
    check("sky:hex-commits", sky_store == "#102030", detail=sky_store)

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
        "batch": 585,
        "title": "Colour rows use the source's editable hex field; closes 584 follow-ups (no ankle/foot group, camera axis chips)",
        "evidence": (
            "2026-10-01 live CDP sampling of the source director desk colour "
            "rows + docs/research/liblib-canvas-batch585-2026-10-01/README.md"
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
        "Batch 585 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "Colour rows match the 2026-10-01 source shape (# + editable hex + "
        "picker) and the 584 pose/camera follow-ups are closed. See runtime-audit.json."
    )


if __name__ == "__main__":
    main()
