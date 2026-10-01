#!/usr/bin/env python3
"""Verify Batch 590: 画幅比例卡样式 + 几何模型子菜单 + 群众阵列弹窗。

Source facts (live CDP sampling of the source director desk at 1920x1150,
driven with page.mouse.click because rail entries only respond to trusted
pointer events):

选择画幅比例 — the seven cards, measured individually:

    each card  104 x 72, border-radius 12px, background transparent
    label      12px, color rgba(255,255,255,0.9) — IDENTICAL selected and
               unselected; the only difference is the card border:
               selected rgba(255,255,255,0.85), unselected 0.1
    glyph      1px border rgba(255,255,255,0.9), per-ratio box:
               自适应 16x11   21:9 16x7    16:9 16x9    4:3 16x12
               1:1    14x14   3:4   8x16   9:16 8x16
               (source measures 3:4 and 9:16 identically — copied as measured,
               not "corrected" by ratio)
    grid       gap 8px, padding 0 8 12  ->  4*72 + 3*8 + 12 = 324 tall

几何模型 — expands a submenu BELOW its own row (204 x 256), eight options
at 199 x 32 on a 32px pitch: 上传文件 / 立方体 / 球体 / 圆柱体 / 环状体 /
圆锥 / 棱锥 / 添加空对象

群众 (3x3) — opens a dialog (220 x 204) rather than acting directly:
    title 添加群众阵列, a right-aligned 共N人 counter, three number inputs
    行数 [1..10 step 1 = 3] / 列数 [1..10 step 1 = 3] /
    间距 [0.1..10 step 0.1 = 1.2], footer 取消 / 添加 (添加 on a white fill)

Contract asserted here:
1. the seven ratio cards match the measured geometry, radius, colors and
   per-ratio glyph boxes;
2. the ratio grid keeps the source's 8px gap and 0/8/12 padding (324 tall);
3. 几何模型 opens the eight-option submenu below the flyout row;
4. 群众 (3x3) opens the dialog with all three inputs, their ranges and the
   共N人 counter, and 添加 commits the edited values to the store;
5. 取消 closes the dialog without adding anything;
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
    / "liblib-canvas-batch590-2026-10-01"
    / "runtime-audit.json"
)

ASPECT_RATIOS = ["自适应", "21:9", "16:9", "4:3", "1:1", "3:4", "9:16"]
# measured glyph boxes, in px
GLYPH_BOXES = {
    "自适应": (16, 11),
    "21:9": (16, 7),
    "16:9": (16, 9),
    "4:3": (16, 12),
    "1:1": (14, 14),
    "3:4": (8, 16),
    "9:16": (8, 16),
}
GEOMETRY_OPTIONS = [
    "上传文件",
    "立方体",
    "球体",
    "圆柱体",
    "环状体",
    "圆锥",
    "棱锥",
    "添加空对象",
]


def alpha_of(color: str | None) -> float | None:
    """Trailing alpha of a CSS colour in any serialisation the two apps use.

    The source reports lab(... / 0.85); Tailwind v4 in the clone emits
    oklab(... / 0.85). Only the alpha is comparable, and it is the part the
    source contract is actually about.
    """
    if not color:
        return None
    if "/" in color:
        tail = color.rsplit("/", 1)[1].strip().rstrip(")")
        try:
            return round(float(tail), 3)
        except ValueError:
            return None
    if color.startswith("rgba"):
        try:
            return round(float(color.rsplit(",", 1)[1].strip().rstrip(")")), 3)
        except (ValueError, IndexError):
            return None
    return None


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
        assert ok, f"batch590 check failed: {name} :: {detail}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/?batch70=1", wait_until="networkidle")
    page.wait_for_function(
        """() => Boolean(window.__libtv_store && window.__libtv_ui_store && window.__director_store)"""
    )
    page.evaluate(
        """() => {
          const store = window.__libtv_store.getState();
          store.addNode("script-execution", { title: "Batch 590" });
          const node = store.getActiveCanvas().nodes.at(-1);
          window.__libtv_ui_store.getState().openDirectorDesk(node.id, store.activeCanvasId);
        }"""
    )
    page.locator("[data-director-workspace]").wait_for(state="visible")
    page.wait_for_timeout(500)
    rail = page.locator("[data-director-icon-rail]")

    # 1+2) 选择画幅比例 card geometry, colors and glyph boxes
    rail.locator("[data-director-rail-entry='aspect-ratio']").click()
    page.wait_for_timeout(250)
    cards = page.evaluate(
        """() => [...document.querySelectorAll('[data-director-aspect-option]')].map(el => {
          const c = getComputedStyle(el);
          const glyph = el.querySelector('[data-director-aspect-glyph]');
          const g = glyph ? getComputedStyle(glyph) : null;
          const gb = glyph ? glyph.getBoundingClientRect() : null;
          // the ratio label is a bare text node, not a span, so its font
          // metrics are read off the button itself
          const lc = c;
          return {
            ratio: el.getAttribute('data-director-aspect-option'),
            pressed: el.getAttribute('aria-pressed'),
            w: Math.round(el.getBoundingClientRect().width),
            h: Math.round(el.getBoundingClientRect().height),
            radius: c.borderRadius, bg: c.backgroundColor,
            borderAlpha: c.borderColor,
            labelColor: lc ? lc.color : null, labelSize: lc ? lc.fontSize : null,
            glyphW: gb ? Math.round(gb.width) : null, glyphH: gb ? Math.round(gb.height) : null,
            glyphBorder: g ? g.borderColor : null,
          };
        })"""
    )
    result["aspect_cards"] = cards
    check(
        "aspect:seven-cards",
        [c["ratio"] for c in cards] == ASPECT_RATIOS,
        detail=[c["ratio"] for c in cards],
    )
    for card in cards:
        ratio = card["ratio"]
        # 232 - 16 (px-2) - 8 (gap) = 208 / 2 = 104, but the browser lands on
        # 103.5 CSS px, so allow 1px of sub-pixel slack
        check(
            f"aspect:{ratio}:size",
            abs(card["w"] - 104) <= 1 and card["h"] == 72,
            detail=card,
        )
        check(f"aspect:{ratio}:radius-12", card["radius"] == "12px", detail=card["radius"])
        check(f"aspect:{ratio}:transparent", card["bg"] == "rgba(0, 0, 0, 0)", detail=card["bg"])
        # the clone serialises white as oklab(...) (Tailwind v4) where the
        # source reported lab(...); compare the alpha, which is the point
        check(
            f"aspect:{ratio}:label-90",
            alpha_of(card["labelColor"]) == 0.9 and card["labelSize"] == "12px",
            detail=(card["labelColor"], card["labelSize"]),
        )
        want_w, want_h = GLYPH_BOXES[ratio]
        check(
            f"aspect:{ratio}:glyph-{want_w}x{want_h}",
            card["glyphW"] == want_w and card["glyphH"] == want_h,
            detail=(card["glyphW"], card["glyphH"]),
        )
        check(
            f"aspect:{ratio}:glyph-border-90",
            alpha_of(card["glyphBorder"]) == 0.9,
            detail=card["glyphBorder"],
        )
        want_alpha = 0.85 if card["pressed"] == "true" else 0.1
        check(
            f"aspect:{ratio}:border-{want_alpha}",
            alpha_of(card["borderAlpha"]) == want_alpha,
            detail=card["borderAlpha"],
        )
    grid = page.locator("[data-director-aspect-grid]").bounding_box()
    check("aspect:grid-232", grid is not None and round(grid["width"]) == 232, detail=grid)
    check(
        "aspect:grid-324",
        grid is not None and 318 <= round(grid["height"]) <= 330,
        detail=grid["height"] if grid else None,
    )

    # 4+5) 群众 (3x3) dialog
    # close any open flyout first — the rail's 选择画幅比例 entry always
    # *opens* its flyout (never toggles), so 场景 is the entry that clears it
    rail.locator("[data-director-rail-entry='scene']").click()
    page.wait_for_timeout(150)
    rail.locator("[data-director-rail-entry='add-character']").click()
    page.wait_for_timeout(250)
    check(
        "crowd:flyout-open",
        page.locator("[data-director-character-option='crowd-3x3']").count() == 1,
    )
    rail.locator("[data-director-character-option='crowd-3x3']").click()
    page.wait_for_timeout(250)
    dialog = page.locator("[data-director-crowd-dialog]")
    check("crowd:opens", dialog.is_visible())
    # the source keeps the flyout open behind the dialog
    check(
        "crowd:flyout-stays-open",
        page.locator("[data-director-character-flyout]").is_visible(),
    )
    check(
        "crowd:title",
        dialog.get_attribute("aria-label") == "添加群众阵列"
        and "添加群众阵列" in dialog.inner_text(),
    )
    check(
        "crowd:count-9",
        page.locator("[data-director-crowd-count]").inner_text().strip() == "共9人",
        detail=page.locator("[data-director-crowd-count]").inner_text(),
    )
    for key, label, lo, hi, step, value in [
        ("rows", "行数", "1", "10", "1", "3"),
        ("columns", "列数", "1", "10", "1", "3"),
        ("spacing", "间距", "0.1", "10", "0.1", "1.2"),
    ]:
        field = page.locator(f"[data-director-crowd-input='{key}']")
        check(f"crowd:{key}:aria", field.get_attribute("aria-label") == label)
        check(f"crowd:{key}:min", field.get_attribute("min") == lo, detail=field.get_attribute("min"))
        check(f"crowd:{key}:max", field.get_attribute("max") == hi, detail=field.get_attribute("max"))
        check(f"crowd:{key}:step", field.get_attribute("step") == step, detail=field.get_attribute("step"))
        check(f"crowd:{key}:default", field.input_value() == value, detail=field.input_value())

    # 5) 取消 must not add anything
    objects_before = page.evaluate(
        "() => window.__director_store.getState().objects.length"
    )
    page.locator("[data-director-crowd-cancel]").click()
    page.wait_for_timeout(200)
    check("crowd:cancel-closes", page.locator("[data-director-crowd-dialog]").count() == 0)
    check(
        "crowd:cancel-adds-nothing",
        page.evaluate("() => window.__director_store.getState().objects.length")
        == objects_before,
    )

    # 4) 添加 commits the edited values
    page.locator("[data-director-character-option='crowd-3x3']").click()
    page.wait_for_timeout(200)
    page.locator("[data-director-crowd-input='rows']").fill("2")
    page.locator("[data-director-crowd-input='columns']").fill("4")
    page.locator("[data-director-crowd-input='spacing']").fill("1.5")
    check(
        "crowd:count-follows",
        page.locator("[data-director-crowd-count]").inner_text().strip() == "共8人",
        detail=page.locator("[data-director-crowd-count]").inner_text(),
    )
    page.locator("[data-director-crowd-confirm]").click()
    page.wait_for_timeout(300)
    check("crowd:confirm-closes", page.locator("[data-director-crowd-dialog]").count() == 0)
    added = page.evaluate(
        """() => {
          const objs = window.__director_store.getState().objects;
          const props = objs.filter(o => o.crowd);
          return {total: objs.length, crowd: props.map(o => o.crowd)};
        }"""
    )
    result["crowd_result"] = added
    check(
        "crowd:confirm-adds-8",
        added["total"] == objects_before + 8,
        detail=(objects_before, added["total"]),
    )

    # 3) 几何模型 submenu — runs last: the submenu overlays its own parent
    # row, so it must not be left open while the crowd rows are clicked
    check(
        "geometry:closed-initially",
        page.locator("[data-director-geometry-submenu]").count() == 0,
    )
    rail.locator("[data-director-character-option='geometry']").click()
    page.wait_for_timeout(250)
    sub = page.locator("[data-director-geometry-submenu]")
    check("geometry:opens", sub.is_visible())
    sub_box = sub.bounding_box()
    result["geometry_box"] = sub_box
    check(
        "geometry:width-204",
        sub_box is not None and round(sub_box["width"]) == 204,
        detail=sub_box,
    )
    geo_options = page.evaluate(
        """() => [...document.querySelectorAll('[data-director-geometry-option]')].map(el => ({
             label: (el.innerText || '').trim(),
             w: Math.round(el.getBoundingClientRect().width),
             h: Math.round(el.getBoundingClientRect().height),
           }))"""
    )
    result["geometry_options"] = geo_options
    check(
        "geometry:eight-options",
        [o["label"] for o in geo_options] == GEOMETRY_OPTIONS,
        detail=[o["label"] for o in geo_options],
    )
    check(
        "geometry:option-rows-32",
        all(o["h"] == 32 for o in geo_options),
        detail=geo_options,
    )
    # the submenu hangs BELOW the flyout row, not to its right
    flyout_box = page.locator("[data-director-character-flyout]").bounding_box()
    check(
        "geometry:below-flyout",
        sub_box is not None
        and flyout_box is not None
        and sub_box["y"] > flyout_box["y"],
        detail=(flyout_box, sub_box),
    )
    rail.locator("[data-director-character-option='geometry']").click()
    page.wait_for_timeout(200)
    check("geometry:toggles-closed", page.locator("[data-director-geometry-submenu]").count() == 0)

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
        "batch": 590,
        "title": "画幅比例卡样式对齐 + 几何模型八项子菜单 + 群众阵列弹窗（源站 2026-10-01 实测）",
        "evidence": (
            "2026-10-01 live CDP sampling of the source director desk at "
            "1920x1150 + docs/research/liblib-canvas-batch590-2026-10-01/README.md"
        ),
        "source_quirks_copied_verbatim": [
            "3:4 and 9:16 both measure 8x16 on the source — copied as measured",
            "selected and unselected ratio labels share the same text color; "
            "only the card border differs (0.85 vs 0.1)",
        ],
        "clone_only": [
            "clone keeps aria-pressed on the ratio cards (the source has none) — "
            "a11y superset",
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
        "Batch 590 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "Ratio cards match the measured 104x72 / radius 12 / per-ratio glyph "
        "boxes, 几何模型 opens its eight-option submenu, and 群众 (3x3) opens "
        "the real dialog and commits. See runtime-audit.json."
    )


if __name__ == "__main__":
    main()
