#!/usr/bin/env python3

"""Verify Batch 146b 文化区域 filter options in the character library.

★ Batch 827 改写：源站**当前**构建里文化区域是三个 `<details>` 胶囊里的第三枚，
  选项逐字 = 东亚 / 欧美 / 中东 / 非洲 / 其他（我的角色库）与
  东亚 / 欧美 / 中东 / 非洲 / **奇幻**（官方角色库，服务端下发的配置）。
  ★ 旧门禁钉的「华语 / 日韩 / 东南亚」是 clone 自己编的 ⟹ 换成源站实测值，
    并**新增**断言把旧三项钉住为「不存在」。
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
    / "liblib-canvas-batch146b-2026-09-07"
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

    def check(name: str, ok: bool) -> None:
        assert ok, f"batch146b check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(BASE_URL, wait_until="networkidle")
    page.wait_for_timeout(500)

    page.locator("button[aria-label='角色造型室']").click()
    page.wait_for_timeout(800)
    modal = page.locator("[data-liblib-overlay='primary:character']")
    check("modal:opens", modal.is_visible())

    # ★ Batch 827：文化区域是**三个 `<details>` 胶囊**里的第三枚，
    #   选项逐字来自源站 2026-10-21 实测（batch 827 raw）：
    #   「我的角色库」页签 = 东亚 / 欧美 / 中东 / 非洲 / **其他**
    #   「官方角色库」页签 = 东亚 / 欧美 / 中东 / 非洲 / **奇幻**
    #   ⟹ 旧门禁里的「华语 / 日韩 / 东南亚」是 clone 自己编的 ⟹ 源站当前构建里 0 命中。
    culture_summary = modal.locator('[data-character-filter-summary="文化区域"]')
    check("culture:pill-present", culture_summary.count() == 1)
    culture_summary.click()
    page.wait_for_timeout(300)
    filter_panel = modal.locator('[data-character-filter-panel="文化区域"]')
    check("filter:panel-opens", filter_panel.is_visible())
    check("culture:label", culture_summary.inner_text().strip() == "文化区域")
    for region in ["东亚", "欧美", "中东", "非洲", "其他"]:
        check(
            f"culture:{region}",
            filter_panel.locator(f"[data-character-filter-chip='{region}']").count() == 1,
        )
    for gone in ["华语", "日韩", "东南亚"]:
        check(
            f"culture:legacy-removed:{gone}",
            filter_panel.locator(f"[data-character-filter-chip='{gone}']").count() == 0,
        )

    # 点击 东亚 芯片 → 筛选生效（有结果）
    filter_panel.locator("[data-character-filter-chip='东亚']").click()
    page.wait_for_timeout(300)
    cards = page.locator("[data-character-strip-card]")
    check("filter:has-results", cards.count() > 0)

    # 清空筛选（选中后 summary 里那枚 ✕）
    modal.locator('[data-character-filter-clear="文化区域"]').click()
    page.wait_for_timeout(300)
    check("clear:restores", cards.count() > 0)

    culture_summary.click()
    page.wait_for_timeout(200)
    # ★ 收起态下 panel 元素**仍在 DOM 里**（原生 `<details>`）⟹ 判收起看 `open` 属性
    check(
        "filter:closes",
        modal.locator('details[data-character-filter="文化区域"]').get_attribute("open") is None,
    )

    # ★ Batch 827：官方角色库页签的文化区域第五项是「奇幻」（源站服务端下发的配置）
    modal.locator('[data-character-studio-tab="official"]').click()
    page.wait_for_timeout(700)
    official_culture = modal.locator('[data-character-filter-panel="文化区域"]')
    check(
        "culture:official-has-fantasy",
        official_culture.locator("[data-character-filter-chip='奇幻']").count() == 1,
    )
    check(
        "culture:official-has-no-other",
        official_culture.locator("[data-character-filter-chip='其他']").count() == 0,
    )

    check("diagnostics:zero", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": "146b",
        "title": "文化区域 filter options in character library",
        "evidence": "docs/research/liblib-canvas-sampling-2026-09-06/README.md",
        "results": [],
    }
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        desktop = browser.new_page(viewport={"width": 1440, "height": 900}, device_scale_factor=1)
        audit["results"].append(run_desktop(desktop))
        desktop.close()
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    checks = audit["results"][0]["checks"]
    print(
        "Batch 146b verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "文化区域 filter group（★ Batch 827 起是源站**当前**形态："
        "我的角色库 = 东亚/欧美/中东/非洲/其他，官方角色库 = 东亚/欧美/中东/非洲/奇幻）、"
        "clear/restore, filter close recorded in runtime-audit.json."
    )


if __name__ == "__main__":
    main()
