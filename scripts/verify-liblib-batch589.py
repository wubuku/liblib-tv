#!/usr/bin/env python3
"""Verify Batch 589: 图标栏 flyout 对齐源站（2026-10-01 实时 DOM 复核）。

Source facts (live CDP sampling of the source director desk at 1920x1150;
the rail entries only respond to trusted pointer events, so these are driven
with page.mouse.click at the button's viewport coordinates):

All three flyout panels measure **232px wide** and open at (48, 100):

  添加角色        232 x 1050   11 options, rows 20px on a 32px pitch
  全景图          232 x 96     3 options,  rows 20px on a 32px pitch
  选择画幅比例     232 x 324    7 options, 2 columns, ~81px row pitch

Each panel carries a 12px `truncate` title line above its options
(`添加角色` @(60,66) 48x20). Separately, hovering a rail entry pops a Mantine
`Tooltip-tooltip` (@(45,118) 64x28) — a tooltip, not the panel title.

添加角色 options, verbatim and in order:
  本地上传 / 标准男性 / 标准女性 / 健硕 / 纤细 / 少年 / 儿童 / 宽厚 /
  二头身 / 群众 (3x3) / 几何模型          (last two carry a submenu chevron)

全景图 options, verbatim: 本地上传 / 历史记录 / **AI生成**

That last one is the correction this batch exists for: batch 538 transcribed
it from a screenshot as 「AI 生成」 with a space. The live DOM has no space.

选择画幅比例 options: 自适应 / 21:9 / 16:9 / 4:3 / 1:1 / 3:4 / 9:16
(自适应 default-selected) — confirmed against the source grid.

Contract asserted here:
1. the three panels all measure 232px wide;
2. each carries its 12px title line;
3. 添加角色 exposes the eleven source options in source order, with the two
   trailing submenu chevrons;
4. 全景图 exposes the three source options verbatim, including the
   space-free 「AI生成」 and not the old 「AI 生成」;
5. 选择画幅比例 keeps the seven source ratios in a two-column grid at the
   source's ~81px row pitch;
6. flyouts still open exclusively from their rail entry and close when
   another entry is picked;
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
    / "liblib-canvas-batch589-2026-10-01"
    / "runtime-audit.json"
)

SOURCE_WIDTH = 232
CHARACTER_OPTIONS = [
    ("local-upload", "本地上传", False),
    ("standard-male", "标准男性", False),
    ("standard-female", "标准女性", False),
    ("muscular", "健硕", False),
    ("slim", "纤细", False),
    ("teen", "少年", False),
    ("child", "儿童", False),
    ("broad", "宽厚", False),
    ("chibi", "二头身", False),
    ("crowd-3x3", "群众 (3x3)", True),
    ("geometry", "几何模型", True),
]
PANORAMA_OPTIONS = [("本地上传", "local-upload"), ("历史记录", "history"), ("AI生成", "ai-generate")]
ASPECT_RATIOS = ["自适应", "21:9", "16:9", "4:3", "1:1", "3:4", "9:16"]


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
        assert ok, f"batch589 check failed: {name} :: {detail}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/?batch70=1", wait_until="networkidle")
    page.wait_for_function(
        """() => Boolean(window.__libtv_store && window.__libtv_ui_store && window.__director_store)"""
    )
    page.evaluate(
        """() => {
          const store = window.__libtv_store.getState();
          store.addNode("script-execution", { title: "Batch 589" });
          const node = store.getActiveCanvas().nodes.at(-1);
          window.__libtv_ui_store.getState().openDirectorDesk(node.id, store.activeCanvasId);
        }"""
    )
    page.locator("[data-director-workspace]").wait_for(state="visible")
    page.wait_for_timeout(500)
    rail = page.locator("[data-director-icon-rail]")

    def width_of(selector: str) -> float:
        box = page.locator(selector).bounding_box()
        assert box is not None, f"{selector} has no box"
        return box["width"]

    # 1+2+3) 添加角色
    rail.locator("[data-director-rail-entry='add-character']").click()
    page.wait_for_timeout(220)
    char = page.locator("[data-director-character-flyout]")
    check("character:opens", char.is_visible())
    result["character_width"] = width_of("[data-director-character-flyout]")
    check(
        "character:width-232",
        abs(result["character_width"] - SOURCE_WIDTH) <= 1,
        detail=result["character_width"],
    )
    title = page.locator("[data-director-flyout-title='add-character']")
    check("character:title-present", title.count() == 1)
    check(
        "character:title-text",
        title.inner_text().strip() == "添加角色",
        detail=title.inner_text(),
    )
    check(
        "character:title-12px",
        title.evaluate("el => getComputedStyle(el).fontSize") == "12px",
    )
    check(
        "character:title-truncates",
        "truncate" in (title.get_attribute("class") or ""),
    )
    options = page.evaluate(
        """() => [...document.querySelectorAll('[data-director-character-option]')]
             .map(el => {
               // the trailing submenu chevron is aria-hidden, so read the
               // first non-aria-hidden span to get the label alone
               const labelSpan = [...el.querySelectorAll('span')]
                 .find(s => s.getAttribute('aria-hidden') !== 'true');
               return {id: el.getAttribute('data-director-character-option'),
                       label: (labelSpan?.innerText || '').trim(),
                       chevron: Boolean(el.querySelector('span[aria-hidden="true"]'))};
             })"""
    )
    result["character_options"] = options
    check(
        "character:eleven-options",
        len(options) == len(CHARACTER_OPTIONS),
        detail=[o["label"] for o in options],
    )
    check(
        "character:options-source-order",
        [(o["id"], o["label"]) for o in options]
        == [(i, l) for i, l, _ in CHARACTER_OPTIONS],
        detail=[o["label"] for o in options],
    )
    check(
        "character:submenu-chevrons",
        [o["chevron"] for o in options] == [c for _, _, c in CHARACTER_OPTIONS],
        detail=[(o["label"], o["chevron"]) for o in options],
    )

    # 4) 全景图 — the AI生成 correction
    rail.locator("[data-director-rail-entry='panorama']").click()
    page.wait_for_timeout(220)
    check("panorama:character-closes", char.count() == 0)
    pano = page.locator("[data-director-panorama-flyout]")
    check("panorama:opens", pano.is_visible())
    result["panorama_width"] = width_of("[data-director-panorama-flyout]")
    check(
        "panorama:width-232",
        abs(result["panorama_width"] - SOURCE_WIDTH) <= 1,
        detail=result["panorama_width"],
    )
    pano_title = page.locator("[data-director-flyout-title='panorama']")
    check(
        "panorama:title",
        pano_title.count() == 1 and pano_title.inner_text().strip() == "全景图",
    )
    pano_text = pano.inner_text()
    result["panorama_text"] = pano_text
    for label, option_id in PANORAMA_OPTIONS:
        check(
            f"panorama:option:{option_id}",
            pano.locator(f"[data-director-panorama-option='{option_id}']").inner_text().strip()
            == label,
        )
    check("panorama:AI生成-no-space", "AI生成" in pano_text, detail=pano_text)
    check("panorama:no-stale-AI-space", "AI 生成" not in pano_text, detail=pano_text)

    # 5) 选择画幅比例
    rail.locator("[data-director-rail-entry='aspect-ratio']").click()
    page.wait_for_timeout(220)
    check("panorama:closes-on-switch", pano.count() == 0)
    aspect = page.locator("[data-director-aspect-flyout]")
    check("aspect:opens", aspect.is_visible())
    result["aspect_width"] = width_of("[data-director-aspect-flyout]")
    check(
        "aspect:width-232",
        abs(result["aspect_width"] - SOURCE_WIDTH) <= 1,
        detail=result["aspect_width"],
    )
    check(
        "aspect:title",
        page.locator("[data-director-flyout-title='aspect-ratio']").inner_text().strip()
        == "选择画幅比例",
    )
    for ratio in ASPECT_RATIOS:
        check(
            f"aspect:option:{ratio}",
            aspect.locator(f"[data-director-aspect-option='{ratio}']").is_visible(),
        )
    check(
        "aspect:default-fit",
        aspect.locator("[data-director-aspect-option='自适应']").get_attribute("aria-pressed")
        == "true",
    )
    row_ys = aspect.evaluate(
        """() => [...document.querySelectorAll('[data-director-aspect-option]')]
             .map(el => Math.round(el.getBoundingClientRect().y))"""
    )
    result["aspect_row_ys"] = row_ys
    # Source rows are 2/2/2/1 (自适应+21:9, 16:9+4:3, 1:1+3:4, 9:16 alone).
    # A title span without col-span-2 would become a grid item and push 自适应
    # into a single-item first row — the row counts catch that.
    distinct = sorted(set(row_ys))
    check(
        "aspect:two-columns",
        len(distinct) == 4
        and row_ys.count(distinct[0]) == 2
        and all(row_ys.count(y) == 2 for y in distinct[1:3])
        and row_ys.count(distinct[3]) == 1,
        detail=row_ys,
    )
    # Row pitch is measured between distinct row tops — in a 2-column grid
    # consecutive siblings share a row, so the naive consecutive difference
    # alternates 0 / pitch.
    row_pitches = [distinct[i + 1] - distinct[i] for i in range(len(distinct) - 1)]
    result["aspect_row_pitches"] = row_pitches
    check(
        "aspect:row-pitch-74-82",
        all(74 <= p <= 82 for p in row_pitches),
        detail=row_pitches,
    )
    grid_box = page.locator("[data-director-aspect-grid]").bounding_box()
    result["aspect_card_height"] = grid_box["height"] if grid_box else None
    check(
        "aspect:card-fits-324",
        grid_box is not None and 310 <= round(grid_box["height"]) <= 340,
        detail=grid_box,
    )
    # the source title sits ABOVE the card (title y=66, card starts y=100)
    title_box = page.locator("[data-director-flyout-title='aspect-ratio']").bounding_box()
    result["aspect_title_box"] = title_box
    check(
        "aspect:title-above-card",
        title_box is not None
        and grid_box is not None
        and title_box["y"] + title_box["height"] <= grid_box["y"] + 1,
        detail=(title_box, grid_box),
    )

    # 6) only one flyout at a time
    check("aspect:single-open", page.locator("[data-director-flyout-title]").count() == 1)

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
        "batch": 589,
        "title": "图标栏三个 flyout 统一 232px 宽 + 12px 标题行 + 「AI生成」逐字修正",
        "evidence": (
            "2026-10-01 live CDP DOM sampling of the source director desk at "
            "1920x1150 + docs/research/liblib-canvas-batch589-2026-10-01/README.md"
        ),
        "corrections": [
            "全景图 第三项逐字是「AI生成」（无空格）；batch 538 从截图转录时"
            "记成了「AI 生成」——verify-liblib-batch538.py 的对应断言随之迁移"
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
        "Batch 589 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "All three rail flyouts are 232px with a 12px title line, the "
        "eleven 添加角色 options match the source order, and 全景图 reads "
        "「AI生成」 verbatim. See runtime-audit.json."
    )


if __name__ == "__main__":
    main()
