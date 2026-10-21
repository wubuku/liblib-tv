#!/usr/bin/env python3

"""Verify Batch 111 character library modal alignment with the 2026-09-05 sampling.

★ Batch 827 改写（本门禁的期望值全部换成了**源站当前**形态的实测值）：
  ★ 面板从 1280×720 变成 **1200×760**（源站 2026-10-21 活体读数，
    batch 827 raw：source-827-structure.json / source-827-details.json）。
  ★ 页签从「公共角色库 / 合规素材库」变成「**我的角色库 / 官方角色库**」。
  ★ 「角色筛选」面板变成三个原生 `<details>` 胶囊（性别 / 年龄段 / 文化区域）。
  ★ 「应用至画布」变成「**添加到画布**」，且只出现在「官方角色库」页签
    （源站 bundle：底部 CTA 有三种形态，见 character-studio.css 的注释）。
  ★ 旧门禁里那些「角色立绘 / 脸部近景 / 表情参考 / 三视图 / 最近使用 /
    女主 / 现代 / 温柔」是 **2026-09-07 旧形态**里那块「角色详情」区的内容，
    源站**当前**构建里已不存在 ⟹ 改钉当前形态里**对应位置**的东西
    （三个筛选胶囊 / 居中名字组 / 底部 CTA）。
  ★ 详见 docs/research/liblib-canvas-batch827-2026-10-01/README.md。
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
    / "liblib-canvas-batch111-2026-09-05"
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
        assert ok, f"batch111 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(BASE_URL, wait_until="networkidle")
    page.wait_for_timeout(400)

    page.get_by_role("button", name="角色造型室").click()
    modal = page.locator('[data-liblib-overlay="primary:character"]')
    assert modal.is_visible()

    rect = modal.evaluate("(el) => { const r = el.getBoundingClientRect(); return { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) }; }")
    # ★ Batch 827：源站当前形态是 1200×760（1280×720 是 2026-09-07 的旧形态）。
    check("shell:width", abs(rect["w"] - 1200) <= 8)
    check("shell:height", abs(rect["h"] - 760) <= 8)
    # ★ Batch 827：模态水平居中（1440 视口 x=120）；y 是**视口相关**的
    #   ⟹ 900 视口下 y = (900-760)/2 = 70（1920×1080 下才是 160）⟹
    #   ★★ 绝对 y 读数**不能跨视口复用**（batch 827 的教训）。
    check("shell:x", abs(rect["x"] - 120) <= 8)
    check("shell:y", abs(rect["y"] - 70) <= 8)

    # ★ Batch 827：页签两枚，逐字「我的角色库 / 官方角色库」
    tabs = modal.locator("[data-character-studio-tab]")
    check("tabs:count-2", tabs.count() == 2)
    check("tabs:my-library", tabs.nth(0).inner_text().strip() == "我的角色库")
    check("tabs:official-library", tabs.nth(1).inner_text().strip() == "官方角色库")

    # ★ Batch 827：三个筛选胶囊（源站当前形态）＋ 逐字选项
    for group, options in (
        ("性别", ["男", "女", "中性"]),
        ("年龄段", ["儿童", "少年", "青年", "中年", "老年"]),
        ("文化区域", ["东亚", "欧美", "中东", "非洲", "其他"]),
    ):
        summary = modal.locator(f'[data-character-filter-summary="{group}"]')
        check(f"filter:{group}:present", summary.count() == 1)
        for option in options:
            check(
                f"filter:{group}:option:{option}",
                modal.locator(f'[data-character-filter-chip="{option}"]').count() >= 1,
            )

    # ★ Batch 827：底部 CTA —— 我的角色库页签是**居中单枚**白底「创建新角色」
    cta = modal.locator('[data-character-studio-cta="create"]')
    check("cta:create-count-1", cta.count() == 1)
    check("cta:create-text", cta.inner_text().strip() == "创建新角色")
    # ★ Batch 827：居中单枚 ⟹ 1440 视口下 x = (1440-1200)/2 + 1 + (1198-116)/2 = 662
    check("cta:create-centered", abs(cta.bounding_box()["x"] - 662) <= 8)
    check("cta:no-apply-to-canvas-yet", modal.get_by_text("应用到画布", exact=True).count() == 0)
    check("cta:no-legacy-apply", modal.get_by_text("应用至画布", exact=True).count() == 0)

    # ★ Batch 827：切到「官方角色库」⟹ 居中名字组 ＋ 居中那组 CTA
    modal.locator('[data-character-studio-tab="official"]').click()
    page.wait_for_timeout(700)
    name_label = modal.locator("[data-character-studio-name]")
    check("name:label-present", name_label.count() == 1)
    check("name:label-text", name_label.inner_text().strip() == "甜妹/清新少女")
    check(
        "add-to-canvas:visible",
        modal.locator('[data-character-studio-cta="add-to-canvas"]').is_visible(),
    )
    check(
        "edit-role:visible",
        modal.locator('[data-character-studio-cta="edit"]').is_visible(),
    )

    modal.get_by_role("button", name="关闭角色造型室", exact=True).click()
    page.wait_for_timeout(200)
    check("close:works", not modal.is_visible())

    check("diagnostics:zero", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 111,
        "title": "Character library modal geometry and detail tags alignment",
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
        "Batch 111 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "★ Batch 827 起本门禁钉的是源站**当前**形态：Modal shell 1200x760, "
        "tabs 我的角色库/官方角色库, three filter pills, centered name label, "
        "bottom CTA and close aria recorded in runtime-audit.json."
    )


if __name__ == "__main__":
    main()
