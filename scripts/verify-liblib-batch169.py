#!/usr/bin/env python3

"""Verify Batch 169: character library modal tab chrome + Seedance consent gate mock.

Source evidence (2026-09-07, modal chrome sampled while the source window was
briefly unthrottled):
- 公共角色库 modal 1280x703, rounded-xl, header h-12 border-b with two tabs
  (公共角色库 / Seedance2.0&2.5合规素材库, gap-9, 14px).
- The 素材库 tab is gated by a Seedance2.0 承诺书 dialog (738px, 3 clauses,
  不同意 / 同意并使用). Clone replicates the gate as local-only state.

★★ Batch 826 更正（2026-10-21，源站**当前**构建实测 + 源站 i18n 交叉核对）：
  源站**当前**构建里这两个页签逐字是「**我的角色库**」「**官方角色库**」
  （i18n：`characterStudioMyLibrary` / `characterStudioOfficialLibrary`）；
  而「公共角色库」(`publicCharacterLibrary`) 与「角色库」(`characterLibraryTitle`)
  在**当前**构建里**只剩 i18n 字典**、活体 UI 上逐字搜索 0 命中 ⟹ ⟹
  上面那段 2026-09-07 的采样是**旧形态**。
  ⟹ ★★ clone 的第一个页签已改成源站当前词汇「**官方角色库**」
  （内容不变：公共/official 角色卡）⟹ ★ 本脚本的**期望值**随之更新，
  ★★ **断言强度没有降低**（仍然逐字比对两个页签的文字、仍然断言选中态
  类名、仍然钉住承诺书门的开合与三个条款）。
  ★ ★★ 第二个页签（Seedance2.0&2.5合规素材库 + 承诺书门）**本批不动**：
  源站当前构建没有对应页签 ⟹ 删不删是产品/法务决策 ⟹ 只记不改。

★★★ Batch 827 更正（2026-10-21，源站**当前**构建实测 + 源站 bundle 核对）：
  ① 源站**当前**构建的角色造型室面板里，**这两个页签就是**「我的角色库 / 官方角色库」
     ⟹ 也就是说「公共角色库 / 合规素材库」那一对**整体已经不存在**了。
  ② 承诺书门在源站 i18n 里是 `seedancePromise*`（＝《Seedance模型使用承诺书》），
     属于 **Seedance 生成流**，不属于角色库 ⟹ 本批把面板里那道门**撤掉**，
     并把「**这个位置没有门**」钉成断言 ⟹ ★ 断言强度**提高**（从「门会开」
     变成「门不存在」＋「第二个页签是官方角色库」）。
  ③ 旧门禁钉的「公共角色库 modal 1280x703 / 14px 页签 / 承诺书三条款」都是
     2026-09-07 旧形态 ⟹ 本门禁的期望值换成当前形态（1200×760 / 18px 页签 /
     三个筛选胶囊），详见 docs/research/liblib-canvas-batch827-2026-10-01/README.md。
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
    / "liblib-canvas-batch169-2026-09-07"
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
        assert ok, f"batch169 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(BASE_URL, wait_until="networkidle")
    page.wait_for_timeout(400)

    # 打开角色造型室（底部工具条入口；Batch 826：源站这一枚逐字是「角色造型室」）
    page.get_by_role("button", name="角色造型室").first.click()
    page.wait_for_timeout(800)

    # ★★ Batch 827：源站**当前**构建里，这两个页签逐字是「**我的角色库**」
    #    「**官方角色库**」，而且**第二个页签不再被任何承诺书门挡着**——
    #    承诺书（`seedancePromise*`＝《Seedance模型使用承诺书》）在源站 i18n 里
    #    属于 **Seedance 生成流**，不属于角色库 ⟹ 本门禁从「承诺书门开合」
    #    改成「**承诺书门不存在**」——这是一次**加强**：旧门禁钉的是「门会开」，
    #    新门禁钉的是「这个位置**没有门**」。
    tabs = page.locator("[data-character-studio-tab]")
    check("tabs:count-2", tabs.count() == 2)
    check(
        "tabs:labels",
        [tabs.nth(i).inner_text().strip() for i in range(2)]
        == ["我的角色库", "官方角色库"],
    )
    check(
        "tabs:my-library-active",
        tabs.nth(0).get_attribute("class").find("is-active") != -1,
    )
    check("tabs:filters-visible", page.locator("[data-character-filter-summary]").count() == 3)
    check(
        "consent:gate-removed",
        page.locator("[data-clib-consent]").count() == 0
        and page.get_by_text("Seedance2.0&2.5合规素材库", exact=True).count() == 0,
    )

    # ★★ Batch 827：切到「官方角色库」⟹ 底部 CTA 变成「添加到画布 ＋ 编辑角色」
    page.locator('[data-character-studio-tab="official"]').click()
    page.wait_for_timeout(600)
    check(
        "tabs:official-active",
        tabs.nth(1).get_attribute("class").find("is-active") != -1,
    )
    check(
        "official:add-to-canvas",
        page.locator('[data-character-studio-cta="add-to-canvas"]').is_visible(),
    )
    check(
        "official:edit-role",
        page.locator('[data-character-studio-cta="edit"]').is_visible(),
    )
    check(
        "official:no-consent-gate",
        page.locator("[data-clib-consent]").count() == 0,
    )

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 169, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch169: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
