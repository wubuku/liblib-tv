#!/usr/bin/env python3

"""Verify Batch 167: /project header buttons + card structure per 2026-09-07 DOM.

Source facts:
- 回收站 / 新建文件夹 are filled secondary buttons (h-8, bg-white/[0.08]-equivalent).
- The create card is a cover (aspect-video, centered 开始创作) + a title row
  (创建新的视频项目) below — not a dashed placeholder card.
- Canvas/project card covers are aspect-video (~150px at 267px card width,
  card total ~208px) with 14px medium titles.
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
    / "liblib-canvas-batch167-2026-09-07"
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
    return errors


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool) -> None:
        assert ok, f"batch167 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(BASE_URL + "/project", wait_until="networkidle")
    page.wait_for_timeout(500)

    # 实心次级按钮
    for attr in ["data-project-recycle", "data-project-new-folder"]:
        btn = page.locator(f"[{attr}]")
        check(f"{attr}:visible", btn.is_visible())
        st = btn.evaluate(
            """el => { const s = getComputedStyle(el);
            return {bg: s.backgroundColor, h: Math.round(el.getBoundingClientRect().height)}; }"""
        )
        check(f"{attr}:filled", st["bg"] not in ("rgba(0, 0, 0, 0)", "transparent"))
        check(f"{attr}:h-32", st["h"] == 32)

    # 创建卡：封面区（aspect-video）+ 下方标题行，无虚线框
    create = page.locator("[data-project-create-card]")
    check("create:visible", create.is_visible())
    check("create:no-dashed", "dashed" not in (create.get_attribute("style") or ""))
    cover = create.locator(".aspect-video")
    check("create:cover-aspect-video", cover.count() == 1)
    check("create:cover-text", cover.get_by_text("开始创作").is_visible())
    check("create:title-row", create.get_by_text("创建新的视频项目").is_visible())

    # 画布卡：aspect-video 封面 + 14px medium 标题
    card = page.locator("[data-project-card]").first
    check("card:cover-aspect-video", card.locator(".aspect-video").count() == 1)
    cbox = card.locator(".aspect-video").first.bounding_box()
    check("card:cover-tall", cbox is not None and cbox["height"] >= 140)

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 167, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch167: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
