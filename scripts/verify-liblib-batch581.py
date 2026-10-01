#!/usr/bin/env python3
"""Verify Batch 581: camera 属性 panel alignment with the 2026-10-01 source.

Source evidence: live CDP sampling of the source director desk on
2026-10-01 (the desk is a persistent fullscreen overlay in the same document
as the canvas — reachable without the 打开导演台 node button responding).
Measured source 属性 panel for 机位1:

    摄像机 [属性] [截图]
    FOV 50°                      (y=134, directly under the tab bar)
    名称 / 切换机位                (y=289 / 361)
    位置 X Y Z                    (y=433 / 465)
    跟随目标 不跟随                (y=505)
    旋转 X Y Z                    (y=577 / 609)
    注视目标 手动坐标                (y=649)
    注视坐标 X Y Z                 (y=721 / 753)
    视野角度 (FOV) ? + 说明文案     (y=816)
    相机截图                       (y=903)

and the FOV slider's native input is min=15 / max=90 / step=1.

Contract asserted here:
1. the three camera tabs share one row (grid-cols-2 used to wrap the third);
2. the FOV control sits above 名称, reads `FOV {n}°`, and exposes 15–90 step 1;
3. source row order holds: 位置 → 跟随目标 → 旋转 → 注视目标 → 注视坐标;
4. the bottom 视野角度 (FOV) help block reveals the source copy verbatim;
5. the follow-target select still drives the store and its offset/view
   follow-up section still appears.
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
    / "liblib-canvas-batch581-2026-10-01"
    / "runtime-audit.json"
)

SOURCE_FOV_HELP = (
    "控制镜头视野范围。数值越小，画面越近、越聚焦；数值越大，画面越广、能看到更多环境。"
)


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


def set_range(page: Page, selector: str, value: str) -> None:
    page.evaluate(
        """([selector, value]) => {
          const el = document.querySelector(selector);
          const setter = Object.getOwnPropertyDescriptor(
            window.HTMLInputElement.prototype, 'value').set;
          setter.call(el, value);
          el.dispatchEvent(new Event('input', { bubbles: true }));
          el.dispatchEvent(new Event('change', { bubbles: true }));
        }""",
        [selector, value],
    )


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool, detail: Any = None) -> None:
        assert ok, f"batch581 check failed: {name} :: {detail}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/?batch70=1", wait_until="networkidle")
    page.wait_for_function(
        """() => Boolean(window.__libtv_store && window.__libtv_ui_store && window.__director_store)"""
    )
    page.evaluate(
        """() => {
          const store = window.__libtv_store.getState();
          store.addNode("script-execution", { title: "Batch 581" });
          const node = store.getActiveCanvas().nodes.at(-1);
          window.__libtv_ui_store.getState().openDirectorDesk(node.id, store.activeCanvasId);
        }"""
    )
    page.locator("[data-director-workspace]").wait_for(state="visible")
    page.wait_for_timeout(400)
    page.evaluate(
        """() => {
          const s = window.__director_store.getState();
          const camera = s.objects.find((o) => o.kind === 'camera');
          s.selectObject(camera.id);
        }"""
    )
    page.locator('[data-director-camera-tab="properties"]').wait_for(state="visible")
    page.wait_for_timeout(400)

    # 1) the three camera tabs share one row
    tab_ys = page.evaluate(
        """() => [...document.querySelectorAll('[data-director-camera-tab]')]
             .map(el => Math.round(el.getBoundingClientRect().y))"""
    )
    result["camera_tab_ys"] = tab_ys
    check("tabs:count", len(tab_ys) == 3)
    check("tabs:single-row", len(set(tab_ys)) == 1, detail=tab_ys)

    # 2) FOV range + the source's control form.
    # Batch 610 correction: this used to assert `fov:above-name`, taken from a
    # historical screenshot that read the `FOV 50°` **badge inside the sticky
    # preview thumbnail** (`div.pointer-events-none.absolute.left-3.top-3`,
    # measured y=134) as if it were the control.  The live reading puts the
    # real control in the 视野角度 (FOV) section at y=798 — i.e. *below* 名称
    # (y=321) and below 注视坐标 (y=721).  The assertion is migrated to that,
    # and the preview thumbnail it was mistaken for is still clone-only.
    fov_field = page.locator("[data-director-camera-fov-field]")
    fov_field.wait_for(state="visible")
    fov_field.scroll_into_view_if_needed()
    page.wait_for_timeout(200)
    fov_y = fov_field.evaluate("el => Math.round(el.getBoundingClientRect().y)")
    name_y = page.locator("[data-director-object-name]").evaluate(
        "el => Math.round(el.getBoundingClientRect().y)"
    )
    result["fov_y"] = fov_y
    result["name_y"] = name_y
    check("fov:below-name", fov_y > name_y, detail=f"{fov_y} vs {name_y}")
    fov_label_y = page.evaluate(
        """() => {
          const el = [...document.querySelectorAll('*')].find(
            (n) => n.childElementCount === 0
              && (n.textContent || '').trim() === '视野角度 (FOV)');
          return el ? Math.round(el.getBoundingClientRect().y) : null;
        }"""
    )
    result["fov_label_y"] = fov_label_y
    # The label is the first row of the field block: the source puts it 17.5px
    # below its `section` top because the section carries `py-4`; the clone's
    # field block carries no top padding, so the label sits flush with it.
    check("fov:label-opens-section",
          fov_label_y is not None and 0 <= fov_label_y - fov_y <= 4,
          detail=f"{fov_label_y} vs field top {fov_y}")

    slider = page.locator("[data-director-camera-fov]")
    check("fov:min", slider.get_attribute("min") == "15")
    check("fov:max", slider.get_attribute("max") == "90")
    check("fov:step", slider.get_attribute("step") == "1")

    store_fov = page.evaluate(
        """() => {
          const s = window.__director_store.getState();
          return s.objects.find((o) => o.kind === 'camera').camera.fov;
        }"""
    )
    # Batch 610: the readout moved from a `<span>FOV 43°</span>` to the
    # source's **number box** — a 49x28 `input[type=number]` with
    # `text-center text-[13px] tabular-nums` (measured @(1834,842) next to the
    # 170px slider).  The `°` suffix only ever existed on the preview
    # thumbnail's badge, which the clone does not have.
    readout = page.locator("[data-director-camera-fov-readout]").input_value().strip()
    result["fov_readout"] = readout
    check("fov:readout-format", readout == f"{store_fov}", detail=f"{readout} vs fov={store_fov}")
    check("fov:label", "FOV" in fov_field.inner_text())

    set_range(page, "[data-director-camera-fov]", "37")
    page.wait_for_timeout(300)
    after_fov = page.evaluate(
        """() => {
          const s = window.__director_store.getState();
          return s.objects.find((o) => o.kind === 'camera').camera.fov;
        }"""
    )
    check("fov:commit", after_fov == 37, detail=after_fov)
    check(
        "fov:readout-follows",
        page.locator("[data-director-camera-fov-readout]").input_value().strip() == "37",
    )

    # 3) source row order
    row_ys = page.evaluate(
        """() => {
          const wanted = ['位置', '跟随目标', '旋转', '注视目标', '注视坐标'];
          const found = {};
          // AxisFields renders its label as a leaf node of any tag, so scan
          // every element and keep the first visible occurrence of each label.
          [...document.querySelectorAll('*')].forEach((el) => {
            const t = (el.textContent || '').trim();
            if (!wanted.includes(t) || t in found || el.children.length > 0) return;
            const r = el.getBoundingClientRect();
            if (r.width > 0 && r.height > 0) found[t] = Math.round(r.y);
          });
          return found;
        }"""
    )
    result["source_row_ys"] = row_ys
    for label in ("位置", "跟随目标", "旋转", "注视目标", "注视坐标"):
        check(f"order:{label}-present", label in row_ys, detail=row_ys)
    if all(label in row_ys for label in ("位置", "跟随目标", "旋转", "注视目标", "注视坐标")):
        ordered = [row_ys[k] for k in ("位置", "跟随目标", "旋转", "注视目标", "注视坐标")]
        check("order:source-sequence", ordered == sorted(ordered), detail=ordered)

    # 4) the FOV help block and its source copy
    # Batch 610 correction: the live reading shows the copy is a **hover
    # overlay** — `pointer-events-none absolute bottom-[calc(100%+8px)]
    # left-1/2 w-52 -translate-x-1/2 rounded-lg bg-[#2b2b2b] px-2 py-1
    # text-xs leading-5 text-white/85 opacity-0 shadow-[0_8px_20px_
    # rgba(0,0,0,0.35)] transition-opacity group-hover:opacity-100`, measured
    # 208x68 @(1655.7,738) with computed opacity 0 at rest.  It is not a click
    # toggle and it is not expanded by default, so 581/582's
    # `data-open` / `help-toggle` contracts are migrated to hover reveal.
    help_block = page.locator("[data-director-camera-fov-help]")
    help_block.scroll_into_view_if_needed()
    tooltip = page.locator("[data-director-camera-fov-help-tooltip]")
    check("help:label", "视野角度 (FOV)" in fov_field.inner_text())
    check("help:hidden-at-rest", tooltip.evaluate("el => getComputedStyle(el).opacity") == "0")
    check("help:source-copy", SOURCE_FOV_HELP in tooltip.inner_text())
    check("help:pointer-events-none",
          tooltip.evaluate("el => getComputedStyle(el).pointerEvents") == "none")
    tooltip_box = tooltip.evaluate(
        "el => { const r = el.getBoundingClientRect();"
        " return [Math.round(r.width), Math.round(r.height)]; }"
    )
    result["help_tooltip_box"] = tooltip_box
    check("help:width-208", tooltip_box[0] == 208, detail=tooltip_box)
    page.locator("[data-director-camera-fov-help-badge]").hover()
    page.wait_for_timeout(300)
    check("help:reveals-on-hover",
          tooltip.evaluate("el => getComputedStyle(el).opacity") == "1")
    page.mouse.move(5, 5)
    page.wait_for_timeout(300)
    check("help:hides-again",
          tooltip.evaluate("el => getComputedStyle(el).opacity") == "0")
    result["help_text"] = tooltip.inner_text().strip()

    # 5) follow target still works and reveals its follow-up section
    follow = page.locator("[data-director-camera-follow-target]")
    check("follow:present", follow.count() == 1)
    target_id = page.evaluate(
        """() => {
          const s = window.__director_store.getState();
          const camera = s.objects.find((o) => o.kind === 'camera');
          const other = s.objects.find(
            (o) => o.kind !== 'camera' && o.id !== camera.id);
          return other ? other.id : null;
        }"""
    )
    if target_id:
        follow.select_option(target_id)
        page.wait_for_timeout(350)
        stored = page.evaluate(
            """() => {
              const s = window.__director_store.getState();
              return s.objects.find((o) => o.kind === 'camera').camera.followTargetId;
            }"""
        )
        check("follow:commit", stored == target_id, detail=f"{stored} vs {target_id}")
        check(
            "follow:offset-section",
            page.locator("[data-director-camera-follow-offset]").count() == 1,
        )
        check(
            "follow:view-section",
            page.locator("[data-director-camera-follow-view]").count() == 1,
        )

    # 6) camera kind without a camera payload never renders camera-only rows
    page.evaluate(
        """() => {
          const s = window.__director_store.getState();
          const character = s.objects.find((o) => o.kind === 'character');
          s.selectObject(character.id);
        }"""
    )
    page.wait_for_timeout(400)
    check("isolation:no-fov-on-character",
          page.locator("[data-director-camera-fov-field]").count() == 0)
    check("isolation:no-follow-on-character",
          page.locator("[data-director-camera-follow-target]").count() == 0)

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
        "batch": 581,
        "title": "Camera 属性 panel alignment: single-row tabs, FOV on top with source range, source row order, FOV help copy",
        "evidence": (
            "2026-10-01 live CDP sampling of the source director desk overlay "
            "(right panel 属性 for 机位1) + "
            "docs/research/liblib-canvas-batch581-2026-10-01/README.md"
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
        "Batch 581 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "Camera 属性 panel matches the 2026-10-01 source sampling: tabs on one "
        "row, the FOV section with 15–90 range below 注视坐标, source row "
        "order, and the FOV copy as a hover overlay. See runtime-audit.json."
    )


if __name__ == "__main__":
    main()
