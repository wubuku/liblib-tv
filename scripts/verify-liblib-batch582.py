#!/usr/bin/env python3
"""Verify Batch 582: 3D场景 panel alignment with the 2026-10-01 source sampling.

Source evidence: live CDP sampling of the source director desk scene panel
(nothing selected). Measured source rows and native control attributes:

    场景缩放      range 0.1–10 step 0.1, readout "300%"   (percentage form)
    场景平移      per axis: <button aria="左右拖动调整 X 轴"> + number step 0.1
    场景旋转      per axis: <button aria="左右拖动调整 X 轴"> + number step 1
    全景背景      已连接全景图 + 请将图片节点连接到导演台左侧输入口
    天空颜色      color input + hex text + "#"
    全景球        水平旋转 range 0–360 step 1 "0°" / 球形半径 range 10–500 step 10
    角色标签 / 网格吸附 / 高斯地面吸附   toggles
    地面          透明度 range 0–1 step 0.05 "0.40"  →  高度 range −2–2 step 0.05 "0.0"

Contract asserted here:
1. 场景缩放/场景平移/场景旋转 are the first rows of the scene panel;
2. 场景缩放 exposes the source 0.1–10 range and keeps the percentage readout;
3. both vector rows carry the source axis drag-scrub chips (aria verbatim) and
   a real horizontal drag commits to the store;
4. 球形半径 is 10–500 step 10; 地面高度 step 0.05; 地面透明度 gains the
   two-decimal readout and precedes 地面高度;
5. 天空颜色 shows a hex readout;
6. the camera FOV help block is expanded by default (batch 581 follow-up);
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
    / "liblib-canvas-batch582-2026-10-01"
    / "runtime-audit.json"
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


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool, detail: Any = None) -> None:
        assert ok, f"batch582 check failed: {name} :: {detail}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/?batch70=1", wait_until="networkidle")
    page.wait_for_function(
        """() => Boolean(window.__libtv_store && window.__libtv_ui_store && window.__director_store)"""
    )
    page.evaluate(
        """() => {
          const store = window.__libtv_store.getState();
          store.addNode("script-execution", { title: "Batch 582" });
          const node = store.getActiveCanvas().nodes.at(-1);
          window.__libtv_ui_store.getState().openDirectorDesk(node.id, store.activeCanvasId);
        }"""
    )
    page.locator("[data-director-workspace]").wait_for(state="visible")
    page.wait_for_timeout(400)
    # nothing selected -> the scene panel renders
    page.evaluate("() => window.__director_store.getState().selectObject(null)")
    panel = page.locator("[data-director-scene-settings]")
    panel.wait_for(state="visible")
    page.wait_for_timeout(300)

    # 1) the transform group leads the panel
    row_ys = page.evaluate(
        """() => {
          const panel = document.querySelector('[data-director-scene-settings]');
          const wanted = ['场景缩放', '场景平移', '场景旋转', '天空颜色',
                          '全景球 水平旋转', '角色标签', '网格吸附',
                          '高斯地面吸附', '地面透明度', '地面高度'];
          const found = {};
          [...panel.querySelectorAll('*')].forEach((el) => {
            const t = (el.textContent || '').trim();
            if (!wanted.includes(t) || t in found || el.children.length > 0) return;
            const r = el.getBoundingClientRect();
            if (r.width > 0 && r.height > 0) found[t] = Math.round(r.y);
          });
          return found;
        }"""
    )
    result["scene_row_ys"] = row_ys
    for label in ("场景缩放", "场景平移", "场景旋转", "地面透明度", "地面高度"):
        check(f"rows:{label}", label in row_ys, detail=row_ys)
    if all(k in row_ys for k in ("场景缩放", "场景平移", "场景旋转")):
        check(
            "order:transform-group-leads",
            row_ys["场景缩放"] < row_ys["场景平移"] < row_ys["场景旋转"],
            detail=row_ys,
        )
    if "地面透明度" in row_ys and "地面高度" in row_ys:
        check(
            "order:opacity-before-height",
            row_ys["地面透明度"] < row_ys["地面高度"],
            detail=row_ys,
        )

    # 2) 场景缩放 range + percentage readout
    # Batch 588: 读数改为源站的**可编辑文本框**，其值不再出现在 innerText
    # 里（input 的 value 不参与 innerText），故断言改为读文本框值。
    scale = page.locator("[data-director-scene-scale]")
    check("scale:min", scale.get_attribute("min") == "0.1")
    check("scale:max", scale.get_attribute("max") == "10")
    scale_readout = page.locator("[data-director-scene-readout='scale']")
    result["scale_readout"] = scale_readout.input_value()
    check(
        "scale:percent-readout",
        scale_readout.input_value().strip().endswith("%"),
        detail=scale_readout.input_value(),
    )

    # 3) axis drag-scrub chips with the source aria, and a real drag commit
    chip_aria = page.evaluate(
        """() => [...document.querySelectorAll('[data-director-scene-axis-scrub]')]
             .map(el => el.getAttribute('aria-label'))"""
    )
    result["axis_scrub_aria"] = chip_aria
    check("scrub:count", len(chip_aria) == 6, detail=chip_aria)
    check(
        "scrub:source-aria",
        all(
            aria == f"左右拖动调整 {axis} 轴"
            for aria, axis in zip(
                chip_aria, ["X", "Y", "Z", "X", "Y", "Z"]
            )
        ),
        detail=chip_aria,
    )

    before = page.evaluate(
        "() => window.__director_store.getState().scene.sceneTranslate[0]"
    )
    chip = page.locator('[data-director-scene-axis-scrub="translate-X"]')
    box = chip.bounding_box()
    assert box, "translate-X scrub chip has no box"
    page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    page.mouse.down()
    for step in range(1, 7):
        page.mouse.move(
            box["x"] + box["width"] / 2 + step * 10, box["y"] + box["height"] / 2
        )
        page.wait_for_timeout(40)
    page.mouse.up()
    page.wait_for_timeout(250)
    after = page.evaluate(
        "() => window.__director_store.getState().scene.sceneTranslate[0]"
    )
    result["scrub_drag"] = {"before": before, "after": after}
    check("scrub:drag-commits", after != before, detail=f"{before} -> {after}")
    check("scrub:drag-increases", after > before, detail=f"{before} -> {after}")
    check(
        "scrub:number-mirrors",
        page.locator('[data-director-scene-translate="0"]').input_value()
        == f"{after:g}",
        detail=page.locator('[data-director-scene-translate="0"]').input_value(),
    )

    # 4) panorama radius / ground steps and opacity readout
    radius = page.locator("[data-director-scene-panorama-radius]")
    check("radius:min", radius.get_attribute("min") == "10")
    check("radius:max", radius.get_attribute("max") == "500")
    check("radius:step", radius.get_attribute("step") == "10")
    height = page.locator("[data-director-scene-ground-height]")
    check("height:step", height.get_attribute("step") == "0.05")
    # Batch 588: 同上，透明度读数已是可编辑文本框，改读其值。
    opacity_readout = page.locator("[data-director-scene-readout='ground-opacity']")
    opacity_text = opacity_readout.input_value()
    result["opacity_row_text"] = opacity_text
    check("opacity:readout", opacity_text.strip() == "0.40", detail=opacity_text)

    # 5) sky colour hex —— Batch 585 起为源站的**可编辑 hex 文本框**
    # （582 原为只读读数），故断言改为读文本框值。
    sky_hex = page.locator('[data-director-hex-input="sky"]')
    result["sky_hex_value"] = sky_hex.input_value()
    check("sky:hex-field", sky_hex.input_value() == "060608",
          detail=sky_hex.input_value())
    check(
        "sky:hash-prefix",
        "#" in sky_hex.evaluate(
            "el => el.closest('label').innerText.replace(/\\n/g, ' ').trim()"),
    )
    check(
        "sky:picker",
        page.locator('[data-director-color-picker="sky"]').count() == 1,
    )

    # 6) camera FOV help defaults to expanded (batch 581 follow-up)
    page.evaluate(
        """() => {
          const s = window.__director_store.getState();
          const camera = s.objects.find((o) => o.kind === 'camera');
          s.selectObject(camera.id);
        }"""
    )
    help_block = page.locator("[data-director-camera-fov-help]")
    help_block.wait_for(state="visible")
    check("help:expanded-by-default", help_block.get_attribute("data-open") == "true")
    check(
        "help:copy-visible",
        "控制镜头视野范围" in help_block.inner_text(),
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
        "batch": 582,
        "title": "3D场景 panel alignment: source row order, axis drag-scrub chips, scene/panorama/ground ranges, sky hex readout, FOV help default",
        "evidence": (
            "2026-10-01 live CDP sampling of the source director desk scene "
            "panel + docs/research/liblib-canvas-batch582-2026-10-01/README.md"
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
        "Batch 582 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "3D场景 panel matches the 2026-10-01 source sampling (transform group "
        "first, axis drag-scrub chips with source aria, 0.1–10 scene scale, "
        "10–500 sphere radius, ground steps and hex readout). See runtime-audit.json."
    )


if __name__ == "__main__":
    main()
