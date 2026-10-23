#!/usr/bin/env python3
"""Verify Batch 540: rail 添加机位 —— **合同已被 batch 832 更正**。

★★★ 更正记录（batch 832，2026-10-21）：
  本文件原写的合同是：
    「source-site sampling 2026-09-27 (rail DOM enumeration, batch 537) ——
     the rail's 添加机位 entry is a **direct action** (clicking opens no panel);
     it shares the camera-creation semantics with the scene tree's 新增机位 button.」
  ⟹ ★★ **这条读数是错的**，batch 832 用**活体 DOM 差分**推翻了它：
     源站点 rail 的「添加机位」会把**左侧资源栏切成一个视图** ——
     标题条「添加机位」 ＋ 2 列 × 15 枚机位预设（每枚 104×72），
     **不是**直接加机位。
     ⟹ 错因：batch 537 当时用的是 **rail DOM 枚举** ⟹ 只看了「有哪些按钮」，
     **没点**，⟹ 于是把「点开的东西」当成了「没有面板」。
     ⟹ 详见 `docs/research/liblib-canvas-batch832-2026-10-01/README.md` §2。
  ⟹ ⇒ 本门禁改为核验**新合同**：
     ① 点 rail「添加机位」→ **打开机位预设面板**（15 枚）；
     ② **不**直接新增机位（场景树的机位数不变）；
     ③ 场景树里的「新增机位」按钮**仍然**直接加机位（那条语义没变）；
     ④ 点 rail「场景」→ 切回场景树。

Contract (current, batch 832): the rail's 添加机位 entry opens the
camera-preset panel in the left resource rail (15 presets, 2 columns).
The scene tree's 新增机位 button still calls
directorStore.addDirectorCamera directly.
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
    / "liblib-canvas-batch540-2026-09-27"
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
        assert ok, f"batch540 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/?batch70=1", wait_until="networkidle")
    page.wait_for_function(
        """() => Boolean(window.__libtv_store && window.__libtv_ui_store && window.__director_store)"""
    )

    page.evaluate(
        """() => {
          const store = window.__libtv_store.getState();
          store.addNode("script-execution", { title: "Batch 540" });
          const node = store.getActiveCanvas().nodes.at(-1);
          window.__libtv_ui_store.getState().openDirectorDesk(node.id, store.activeCanvasId);
        }"""
    )
    page.locator("[data-director-workspace]").wait_for(state="visible")
    page.wait_for_timeout(400)

    tree = page.locator("[data-director-tree], [aria-label='场景对象']").first
    tree_text_before = tree.inner_text()
    rail = page.locator("[data-director-icon-rail]")

    # ★★ batch 832 更正后的合同：rail「添加机位」打开**机位预设面板**，
    #    **不**直接新增机位。
    rail.locator("[data-director-rail-entry='add-camera']").click()
    page.wait_for_timeout(600)
    panel = page.locator("[data-director-camera-preset-panel]")
    check("camera:preset-panel-opens", panel.count() == 1)
    check(
        "camera:preset-panel-has-15",
        panel.locator("[data-director-camera-preset]").count() == 15,
    )
    check(
        "camera:preset-panel-title",
        (panel.inner_text() or "").strip().startswith("添加机位"),
    )
    # 场景树的机位数**不变**（点 rail 不再加机位了）
    check(
        "camera:no-entry-added",
        tree.inner_text().count("机位")
        == tree_text_before.count("机位"),
    )

    # 无 flyout / modal（机位预设面板**不是**浮层 ⟹ 它在左侧资源栏里）
    check("camera:no-flyout", page.locator("[data-director-character-panel]").count() == 0)
    check("camera:no-modal", page.locator("[data-director-ai-import-modal]").count() == 0)

    # ★ 点 rail「场景」→ 切回场景树（否则用户会卡在预设面板里）
    rail.locator("[data-director-rail-entry='scene']").click()
    page.wait_for_timeout(600)
    check("camera:back-to-tree", page.locator("[data-director-tree]").count() >= 1)
    check("camera:panel-closed", panel.count() == 0)

    # ★ 场景树里的「新增机位」按钮**仍然**直接加机位（那条语义没变）
    tree.locator("[data-director-add-camera]").click()
    page.wait_for_timeout(600)
    check(
        "camera:tree-button-still-adds",
        tree.inner_text().count("机位") > tree_text_before.count("机位"),
    )

    check("diagnostics:zero", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 540,
        "title": "Rail add-camera opens the camera-preset panel "
                 "(contract corrected by batch 832)",
        "evidence": (
            "★ batch 832 更正：源站的 rail「添加机位」**不是**直接动作，"
            "而是把左侧资源栏切成一个「机位预设」视图"
            "（标题条「添加机位」 ＋ 2 列 × 15 枚 104×72 的预设）"
            "⟹ 证据：docs/research/liblib-canvas-batch832-2026-10-01/"
            "raw/source-832-camera-presets.json（活体读数）"
            "⟹ ★ 旧证据（batch 537 的 rail DOM 枚举）只列了按钮、"
            "**没有点** ⟹ 错在「把点开的东西当成了没有面板」"
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
        "Batch 540 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "rail add-camera opens the camera-preset panel (15 presets) "
        "without adding a camera; the scene tree's 新增机位 button "
        "still adds one directly. Contract corrected by batch 832, "
        "recorded in runtime-audit.json."
    )


if __name__ == "__main__":
    main()
