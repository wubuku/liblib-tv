#!/usr/bin/env python3

"""Verify Batch 112 character filter alignment.

★ Batch 827 改写：源站**当前**构建里，筛选不再是「一个面板 + 五个分组」，
  而是**三个原生 `<details>` 胶囊**（性别 / 年龄段 / 文化区域），
  选项逐字见 docs/research/liblib-canvas-batch827-2026-10-01/raw/source-827-dropdowns.json。
  ★ 旧门禁里的「种族 / 时代」两组在源站**当前**构建里**不存在** ⟹ 本批删掉，
    并**新增**一条断言把它们钉住为「不存在」。
  ★ 旧的「clear」按钮变成了选中后 summary 里的那枚 ✕。
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
    / "liblib-canvas-batch112-2026-09-05"
    / "runtime-audit.json"
)

GROUP_CHIPS = {
    "性别": ["男", "女", "中性"],
    "年龄段": ["儿童", "少年", "青年", "中年", "老年"],
    "文化区域": ["东亚", "欧美", "中东", "非洲", "其他"],
}


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
        assert ok, f"batch112 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(BASE_URL, wait_until="networkidle")
    page.wait_for_timeout(400)

    page.get_by_role("button", name="角色造型室").click()
    modal = page.locator('[data-liblib-overlay="primary:character"]')
    assert modal.is_visible()

    # ★ Batch 827：筛选从「一个面板 + 五个分组」变成**三个原生 `<details>` 胶囊**
    #   （源站当前形态：性别 / 年龄段 / 文化区域，选项逐字见 source-827-dropdowns.json）。
    #   ★ 旧门禁的「种族 / 时代」两组在源站**当前**构建里**不存在** ⟹ 删掉。
    summaries = modal.locator("[data-character-filter-summary]")
    check("filter:three-pills", summaries.count() == 3)
    for group, chips in GROUP_CHIPS.items():
        summary = modal.locator(f'[data-character-filter-summary="{group}"]')
        check(f"group:{group}", summary.count() == 1)
        check(f"group:{group}:label", summary.inner_text().strip() == group)
        for chip in chips:
            check(
                f"chip:{group}:{chip}",
                modal.locator(f"[data-character-filter-chip='{chip}']").count() == 1,
            )
    check("group:culture-unknown", modal.get_by_text("文化区域", exact=True).count() == 1)
    # ★ 源站**当前**形态里没有「种族 / 时代」两组
    for gone in ("种族", "时代"):
        check(f"group:legacy-removed:{gone}", modal.get_by_text(gone, exact=True).count() == 0)

    # 点开「性别」⟹ 下拉面板出现（源站：180 宽、top-10、选项行 36 高）
    gender_summary = modal.locator('[data-character-filter-summary="性别"]')
    gender_summary.click()
    page.wait_for_timeout(300)
    panel = modal.locator('[data-character-filter-panel="性别"]')
    check("panel:open", panel.is_visible())
    check("panel:width-180", abs(panel.bounding_box()["width"] - 180) <= 1)
    check("panel:below-summary", panel.bounding_box()["y"] - gender_summary.bounding_box()["y"] >= 38)

    panel.locator("[data-character-filter-chip='男']").click()
    page.wait_for_timeout(200)
    check(
        "filter:male-hides-sweet",
        modal.locator("[data-character-strip-card='甜妹/清新少女']").count() == 0,
    )
    check(
        "filter:male-keeps-bazong",
        modal.locator("[data-character-strip-card='霸总/精英大佬']").count() == 1,
    )
    # ★ 选中后源站的 summary 变成 [✕][标签][竖线][已选项] 的形状
    check(
        "filter:summary-shows-picked",
        "男" in gender_summary.inner_text(),
    )
    check(
        "filter:clear-present",
        modal.locator('[data-character-filter-clear="性别"]').count() == 1,
    )

    modal.locator('[data-character-filter-clear="性别"]').click()
    page.wait_for_timeout(200)
    check(
        "clear:restores-strip",
        modal.locator("[data-character-strip-card='甜妹/清新少女']").count() == 1,
    )
    check(
        "clear:summary-back-to-label",
        gender_summary.inner_text().strip() == "性别",
    )

    gender_summary.click()
    page.wait_for_timeout(200)
    # ★ 下拉的 panel 元素在**收起态也留在 DOM 里**（原生 `<details>` 的行为，
    #   源站同款）⟹ 判「收起」只能看 `<details>` 有没有 `open` 属性，
    #   **不能**用「panel 元素还在不在」来判（那永远为真）。
    check(
        "toggle:closes-panel",
        modal.locator('details[data-character-filter="性别"]').get_attribute("open") is None,
    )

    modal.get_by_role("button", name="关闭角色造型室", exact=True).click()
    page.wait_for_timeout(200)
    check("close:modal", not modal.is_visible())

    check("diagnostics:zero", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 112,
        "title": "Character filter panel alignment with 2026-09-05 sampling",
        "evidence": "docs/research/liblib-live-2026-09-05/README.md",
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
        "Batch 112 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "★ Batch 827 起本门禁钉的是源站**当前**形态：three <details> filter pills "
        "(性别/年龄段/文化区域), option text set, local tag-based filtering, "
        "clear-restore via the summary ✕ and toggle recorded in runtime-audit.json."
    )


if __name__ == "__main__":
    main()
