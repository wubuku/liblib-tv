#!/usr/bin/env python3
"""Verify Batch 529: material library showcase panels (风格库/特效库).

Contract: source-site live sampling 2026-09-25 rounds 6/7/8
(docs/research/liblib-source-exploration-2026-09-25/NOTES.md §132-145 +
screenshots 31/32/34/35) — the 素材库 launcher's two entries open large
centered showcase overlays:
- style: tabs 风格广场|我的收藏|最近使用, search 搜索风格名称、作者, category
  chips (推荐/摄影写真/电商营销/动漫游戏/风格插画/平面设计/建筑及室内设计/
  创意玩法/文创周边/小说推文), 仅看可商用 filter + 全部, commercial style
  cards (商用 badge, author, likes);
- effects: tabs 特效广场|我的收藏|最近使用, search 搜索特效名称、作者,
  推荐 + 全部 row, camera-movement preset cards (e.g. 小蜜蜂运镜);
- 我的收藏/最近使用 are empty states showing 暂无素材 (new account).
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
    / "liblib-canvas-batch529-2026-09-27"
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


def open_material_panel(page: Page) -> Any:
    page.get_by_role("button", name="素材库", exact=True).click()
    page.wait_for_timeout(300)
    return page.locator('[data-liblib-overlay="primary:material"]')


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool) -> None:
        assert ok, f"batch529 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(BASE_URL, wait_until="networkidle")
    page.wait_for_timeout(400)

    # —— 风格库 ——
    material = open_material_panel(page)
    check("material:open", material.is_visible())
    material.get_by_role("button", name="风格库").click()
    page.wait_for_timeout(300)
    style = page.locator('[data-liblib-overlay="primary:style-library"]')
    check("style:opens", style.is_visible())
    check("style:material-replaced", not material.is_visible())
    check("style:plaza-tab", style.locator("[data-library-plaza-tab]").inner_text() == "风格广场")
    for cat in ["推荐", "摄影写真", "电商营销", "动漫游戏", "小说推文"]:
        check(f"style:category:{cat}", style.locator(f"[data-library-category='{cat}']").count() == 1)
    check("style:commercial-filter", "仅看可商用" in style.inner_text())
    style_cards = style.locator("[data-library-card]")
    check("style:card-count", style_cards.count() == 16)
    check(
        "style:seedream-card",
        style.locator("[data-library-card-title='Seedream 5.0 pro']").count() == 1,
    )
    check("style:commercial-badge", "商用" in style.locator("[data-library-card]").first.inner_text())

    # 搜索本地过滤
    search = style.get_by_role("textbox")
    search.fill("Seedream")
    page.wait_for_timeout(200)
    check("style:search-filter", style.locator("[data-library-card]").count() == 1)
    search.fill("")
    page.wait_for_timeout(200)

    # 我的收藏 → 暂无素材空态（截图 34）
    style.locator("[data-library-empty-tab='我的收藏']").click()
    page.wait_for_timeout(200)
    empty = style.locator("[data-library-empty]")
    check("style:favorites-empty", empty.is_visible() and "暂无素材" in empty.inner_text())

    # 关闭按钮收起浮层
    style.locator("[data-library-close]").click()
    page.wait_for_timeout(200)
    check("style:close", not style.is_visible())

    # —— 特效库 ——
    material = open_material_panel(page)
    material.get_by_role("button", name="特效库").click()
    page.wait_for_timeout(300)
    effects = page.locator('[data-liblib-overlay="primary:effects-library"]')
    check("effects:opens", effects.is_visible())
    check("effects:plaza-tab", effects.locator("[data-library-plaza-tab]").inner_text() == "特效广场")
    check("effects:recommend-row", effects.locator("[data-library-category='推荐']").count() == 1)
    effects_cards = effects.locator("[data-library-card]")
    check("effects:card-count", effects_cards.count() == 24)
    check(
        "effects:bee-card",
        effects.locator("[data-library-card-title='小蜜蜂运镜']").inner_text().replace("\n", "")
        .find("商用") >= 0,
    )

    # 最近使用 → 暂无素材空态（截图 35）；ESC 经 primary-panel 分支退出
    effects.locator("[data-library-empty-tab='最近使用']").click()
    page.wait_for_timeout(200)
    check("effects:recent-empty", "暂无素材" in effects.locator("[data-library-empty]").inner_text())
    page.locator(".react-flow__pane").click(position={"x": 10, "y": 10})
    page.keyboard.press("Escape")
    page.wait_for_timeout(200)
    check("effects:escape-closes", not effects.is_visible())

    check("diagnostics:zero", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 529,
        "title": "Material library showcase panels (风格库/特效库)",
        "evidence": (
            "docs/research/liblib-source-exploration-2026-09-25/NOTES.md "
            "§132-145 + screenshots 31/32/34/35"
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
        "Batch 529 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "material launcher entries open style/effects showcase overlays with "
        "plaza tabs, category rows, commercial cards, local search filter, "
        "收藏/最近使用 暂无素材 empty states and close/ESC recorded in "
        "runtime-audit.json."
    )


if __name__ == "__main__":
    main()
