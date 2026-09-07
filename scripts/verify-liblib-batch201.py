#!/usr/bin/env python3

"""Verify Batch 201: 换一批 rotation serves the four real skill batches.

Source evidence (2026-09-08 CDP, source-skill-batches.json): rotating 换一批
cycles through four real batches —
0: 皮克斯动画广告/爆款拉片复刻/新中式美学TVC/古典武侠电影全流程导演
1: 游戏实机PV/精品女频短剧一键成片/是枝裕和电影美学/韦斯安德森电影美学
2: 剧情TVC广告片/伊斯特伍德西部片/一键爽感轰炸流汽车TVC/旅拍大师
3: 一键海外狼人吸血鬼短剧/宝岛浪潮电影美学/无厘头喜剧 (3 cards)
The clone's skillBatches now embed the real directory (the clone-shaped
second-batch filler is removed); thumbnails remain local placeholders.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = (
    ROOT
    / "docs"
    / "research"
    / "liblib-canvas-batch201-2026-09-08"
    / "runtime-audit.json"
)

ROTATION = [
    ["皮克斯动画广告", "爆款拉片复刻", "新中式美学TVC", "古典武侠电影全流程导演"],
    ["游戏实机PV", "精品女频短剧一键成片", "是枝裕和电影美学", "韦斯安德森电影美学"],
    ["剧情TVC广告片", "伊斯特伍德西部片", "一键爽感轰炸流汽车TVC", "旅拍大师"],
    ["一键海外狼人吸血鬼短剧", "宝岛浪潮电影美学", "无厘头喜剧"],
]


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool) -> None:
        assert ok, f"batch201 check failed: {name}"
        result["checks"].append(name)

    errors: list[str] = []
    page.on("pageerror", lambda error: errors.append(f"pageerror:{error}"))
    page.goto("http://localhost:4317", wait_until="networkidle")
    page.wait_for_timeout(400)

    page.get_by_role("button", name="Agent").click()
    page.wait_for_timeout(500)
    drawer = page.locator("aside").first
    check("drawer:opens", drawer.count() == 1)

    for expected in ROTATION:
        current = drawer.locator("[data-skill-card], button").all_inner_texts()
        joined = " ".join(current)
        ok = all(name in joined for name in expected)
        check(f"batch:{expected[0]}", ok)
        huan = drawer.get_by_role("button", name="换一批")
        if huan.count():
            huan.click()
            page.wait_for_timeout(250)

    # rotation wraps back to batch 0 after 4 clicks
    wrapped = " ".join(drawer.locator("button").all_inner_texts())
    check("rotation:wraps-to-batch0", all(name in wrapped for name in ROTATION[0]))

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 201, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch201: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
