#!/usr/bin/env python3
"""Verify Batch 538: director rail panorama & aspect-ratio flyouts.

Contract: source-site sampling 2026-09-27 (screenshots
44-director-rail-25.png / 44-director-rail-26.png, CDP transcription) —
- 全景图 flyout: 本地上传 / 历史记录 / AI生成 (three source options;
  batch 589 DOM 复核确认「AI生成」无空格，538 截图转录曾误记为「AI 生成」);
- 选择画幅比例 flyout: seven cards 自适应 (default active) / 21:9 / 16:9 /
  4:3 / 1:1 / 3:4 / 9:16 with mini-glyphs, single-select.
Flyouts are visual only: AI生成/AI 识图 are paid AI actions and are never
triggered; ratio selection is a local draft state.
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
    / "liblib-canvas-batch538-2026-09-27"
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
        assert ok, f"batch538 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/?batch70=1", wait_until="networkidle")
    page.wait_for_function(
        """() => Boolean(window.__libtv_store && window.__libtv_ui_store)"""
    )

    page.evaluate(
        """() => {
          const store = window.__libtv_store.getState();
          store.addNode("script-execution", { title: "Batch 538" });
          const node = store.getActiveCanvas().nodes.at(-1);
          window.__libtv_ui_store.getState().openDirectorDesk(node.id, store.activeCanvasId);
        }"""
    )
    page.locator("[data-director-workspace]").wait_for(state="visible")
    page.wait_for_timeout(400)

    rail = page.locator("[data-director-icon-rail]")
    check("rail:visible", rail.is_visible())

    # ★ ★★ Batch 859（源站逐字）：「全景图」「选择画幅比例」**不再是浮层** ——
    #   源站逐字：左侧那个 232px 面板是**五模式互斥容器**
    #   （`"scene"===z?n:null,"character"===z?(…),"camera"===z?(…),
    #     "panorama"===z?(…),"aspect"===z?(…)`）⟹ ⟹ 这两枚是**面板模式**。
    # ⟹ ⟹ 「另一个面板关掉了」这条判据的**旧前提**是「浮层被卸载」
    #   （`count() == 0`）⟹ ⟹ 现在面板**常驻挂载**、靠 `hidden` 隐藏
    #   ⟹ ⟹ 判据改成「**不可见**」（`is_visible()` 为假）⟹ ⟹
    #   ★ 这才是同一件事（「这个面板不在场」）的正确读法。
    pano_panel = page.locator("[data-director-panorama-panel]")
    aspect_panel = page.locator("[data-director-aspect-panel]")

    # —— 全景图面板 ——
    rail.locator("[data-director-rail-entry='panorama']").click()
    page.wait_for_timeout(200)
    check("panorama:opens", pano_panel.is_visible())
    pano_text = pano_panel.inner_text()
    # Batch 589: 逐字为「AI生成」（无空格），源站 DOM 实测 232×96 @(48,100)。
    for token in ["本地上传", "历史记录", "AI生成"]:
        check(f"panorama:item:{token}", token in pano_text)

    # —— 选择画幅比例面板 ——
    rail.locator("[data-director-rail-entry='aspect-ratio']").click()
    page.wait_for_timeout(200)
    check("panorama:closes", not pano_panel.is_visible())
    check("aspect:opens", aspect_panel.is_visible())
    for ratio in ["自适应", "21:9", "16:9", "4:3", "1:1", "3:4", "9:16"]:
        check(
            f"aspect:option:{ratio}",
            aspect_panel.locator(f"[data-director-aspect-option='{ratio}']").is_visible(),
        )
    check(
        "aspect:default-fit",
        aspect_panel.locator("[data-director-aspect-option='自适应']").get_attribute("aria-pressed") == "true",
    )

    # 单选切换
    aspect_panel.locator("[data-director-aspect-option='16:9']").click()
    page.wait_for_timeout(150)
    check(
        "aspect:switch-16-9",
        aspect_panel.locator("[data-director-aspect-option='16:9']").get_attribute("aria-pressed") == "true",
    )
    check(
        "aspect:fit-inactive",
        aspect_panel.locator("[data-director-aspect-option='自适应']").get_attribute("aria-pressed") == "false",
    )

    # 切回场景条目：面板收起，场景树仍在
    rail.locator("[data-director-rail-entry='scene']").click()
    page.wait_for_timeout(150)
    check("scene:flyout-closes", not aspect_panel.is_visible())
    check("scene:tree-present", page.locator("[aria-label='场景对象']").first.is_visible())

    check("diagnostics:zero", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 538,
        "title": "Director rail panorama & aspect-ratio flyouts",
        "evidence": (
            "docs/research/liblib-source-exploration-2026-09-25/NOTES.md "
            "§8 + screenshots 44-director-rail-25/26 (CDP transcription)"
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
        "Batch 538 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "panorama flyout (本地上传/历史记录/AI生成), aspect-ratio grid "
        "(7 options, 自适应 default, single-select) recorded in "
        "runtime-audit.json."
    )


if __name__ == "__main__":
    main()
