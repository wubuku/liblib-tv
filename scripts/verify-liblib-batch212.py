#!/usr/bin/env python3

"""Verify Batch 212: character library modal geometry at all viewports.

Source evidence (source-clib-modal-widths.json): with a video node created
per viewport and the 角色库 pill clicked, the modal measures 1280x720 at
1920/1680/1440 — horizontally centered (x=(vw-1280)/2), top y=90. The
clone's modal geometry was migrated from 1304x731 to 1280x720 accordingly.

★ Batch 827 改写：源站**当前**构建（2026-10-21 实测）里这个面板已经不是
  1280×720 的模态，而是 **1200×760** 的「角色造型室」⟹ 期望值随之更新。
  证据：docs/research/liblib-canvas-batch827-2026-10-01/raw/source-827-structure.json
        （面板根 1198×758 @361,161；祖先链里的 SECTION 1200×760 @360,160）。
  ★ 第二个页签也不再是「Seedance2.0&2.5合规素材库」⟹ 源站当前形态是
    「我的角色库 / 官方角色库」⟹ 断言改成钉**新**页签，并把旧页签钉为「不存在」。
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
    / "liblib-canvas-batch212-2026-09-08"
    / "runtime-audit.json"
)


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool) -> None:
        assert ok, f"batch212 check failed: {name}"
        result["checks"].append(name)

    errors: list[str] = []
    page.on("pageerror", lambda error: errors.append(f"pageerror:{error}"))
    page.goto("http://localhost:4317", wait_until="networkidle")
    page.wait_for_timeout(500)

    page.get_by_role("button", name="资产管理").count()  # ensure app ready
    page.get_by_role("button", name="Agent").click()
    page.wait_for_timeout(300)
    page.get_by_role("button", name="Agent").click()
    page.wait_for_timeout(300)

    # open the character library via the panel toolbar pill (video panel needs
    # a node; use the preset video node)
    # open via the left sidebar 角色库 tool button
    page.locator("[data-character-studio-tab]").count()  # noop warm
    # the video panel's 角色库 pill opens the left sidebar's character panel
    page.locator('.react-flow__node[data-id="v-UGQZzZOpbv"]').click(force=True)
    page.wait_for_timeout(300)
    page.locator("[data-clib-trigger]").click()
    page.wait_for_timeout(400)
    page.wait_for_timeout(400)
    modal = page.locator("[data-liblib-overlay='primary:character']")
    check("modal:opens", modal.count() == 1)
    mb = modal.bounding_box()
    # ★ Batch 827：源站当前形态是 1200×760（1280×720 是 2026-09-07 的旧形态）
    check("modal:width-1200", abs(mb["width"] - 1200) <= 8)
    check("modal:height-760", abs(mb["height"] - 760) <= 8)

    # tabs + 官方角色库页签内容
    # ★★ Batch 826：源站**当前**构建里第一个页签逐字是「官方角色库」
    # （旧的「公共角色库」在当前构建的活体 UI 上 0 命中）⟹ 期望值更新，
    # ★★ 断言强度不变（仍然逐字计数）。
    # ★★ Batch 827：第二个页签也不再是「Seedance2.0&2.5合规素材库」，
    #    源站当前形态是「我的角色库 / 官方角色库」⟹ 改钉新页签，
    #    并把旧页签钉为「不存在」。
    check("tabs:public", page.get_by_text("官方角色库", exact=True).count() >= 1)
    check("tabs:my-library", page.get_by_text("我的角色库", exact=True).count() >= 1)
    check(
        "tabs:compliance-removed",
        page.get_by_text("Seedance2.0&2.5合规素材库", exact=True).count() == 0,
    )

    page.keyboard.press("Escape")
    page.wait_for_timeout(200)

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 212, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch212: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
