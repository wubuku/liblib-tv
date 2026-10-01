#!/usr/bin/env python3
"""Verify Batch 535: director desk scene prompt bar.

Contract: source-site live sampling. **Superseded in part by batch 604.**

This batch's original contract came from the 2026-09-25 round 2 notes plus
screenshot 18-director-console-opened.png, and described a bottom-center pill
bar with a mode segment of three toggles (光标/相机/手). Batch 604 re-sampled
the live source DOM on 2026-10-01 and showed that segment does not exist: the
bottom bar is **two pills side by side** in one `flex items-center gap-2` row —
a `nav` tool pill (移动/截图/动画时间轴) and a `grid grid-cols-[32px_1fr_32px]`
prompt pill (上传图片 / input / 发送). The three mode buttons are therefore
removed from the clone and this verifier now asserts their absence.

What still holds from batch 535: the prompt draft input, its accessible name,
and a local-only submit confirmation (no generation, no network). Real scene
building is a cloud AI action, so the clone keeps the draft and mode selection
locally and submit only flashes a local-draft confirmation.
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
    / "liblib-canvas-batch535-2026-09-27"
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

    def check(name: str, ok: bool, detail: Any = None) -> None:
        # batch 604: 接受 detail，让迁移进来的断言能记录实测依据
        assert ok, f"batch535 check failed: {name} ({detail})"
        result["checks"].append({"name": name, "ok": True, "detail": detail})

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/?batch70=1", wait_until="networkidle")
    page.wait_for_function(
        """() => Boolean(window.__libtv_store && window.__libtv_ui_store)"""
    )

    # 建导演台节点并打开导演台（batch 70 路径）
    page.evaluate(
        """() => {
          const store = window.__libtv_store.getState();
          store.addNode("script-execution", { title: "Batch 535" });
          const node = store.getActiveCanvas().nodes.at(-1);
          window.__libtv_ui_store.getState().openDirectorDesk(node.id, store.activeCanvasId);
        }"""
    )
    page.locator("[data-director-workspace]").wait_for(state="visible")
    page.wait_for_timeout(400)

    bar = page.locator("[data-director-scene-prompt-bar]")
    check("bar:visible", bar.is_visible())
    # Batch 592（源站 2026-10-01 DOM 复核）：可及名/占位逐字是
    # 「描述想搭建的场景」——535 早期凭截图转录多写了一个「要」。
    check(
        "bar:placeholder",
        bar.locator("[data-director-scene-prompt-input]").get_attribute("placeholder")
        == "描述想搭建的场景",
    )

    # Batch 604 迁移：源站 2026-10-01 实时 DOM 复核推翻了本文件 docstring
    # 记录的「模式段三切换（光标/相机/手）」——那是从历史截图 18 转录来的，
    # 源站真实结构是**两枚并排胶囊**：`nav` 工具胶囊（移动/截图/动画时间轴）
    # + `grid grid-cols-[32px_1fr_32px]` prompt 胶囊（上传图片/输入/发送）。
    # 模式三态在源站不存在，clone 的三枚模式钮已删除，故此处改为断言「不存在」。
    check(
        "mode-toggles:removed",
        page.locator("[data-director-scene-mode]").count() == 0,
        detail="source has no 光标/相机/手 mode segment; the clone's three "
        "mode buttons (transcribed from screenshot 18) are gone",
    )
    check(
        "bar:in-bottom-bar-row",
        page.locator(
            "[data-director-bottom-bar] [data-director-scene-prompt-bar]"
        ).count()
        == 1,
        detail="prompt pill now shares the source's single bottom row with the "
        "tool pill (was an independent absolutely positioned bar)",
    )
    check(
        "bar:upload-cell",
        bar.locator("[data-director-scene-prompt-upload]").get_attribute("aria-label")
        == "上传图片",
    )

    # 输入草稿 + 提交 → 本地确认回显（无网络动作）
    prompt_input = bar.locator("[data-director-scene-prompt-input]")
    prompt_input.fill("一间咖啡馆，窗边两张桌子")
    bar.locator("[data-director-scene-prompt-submit]").click()
    page.wait_for_timeout(200)
    status = bar.locator("[data-director-scene-prompt-status]")
    check("submit:local-ack", "本地草稿" in status.inner_text())
    check("submit:draft-kept", prompt_input.input_value() == "一间咖啡馆，窗边两张桌子")

    check("diagnostics:zero", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 535,
        "title": "Director desk scene prompt bar",
        "evidence": (
            "docs/research/liblib-source-exploration-2026-09-25/NOTES.md "
            "§8 + screenshot 18-director-console-opened.png"
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
        "Batch 535 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "scene prompt bar (grid pill: upload / draft input / circular submit) "
        "with local-only submit confirmation recorded in runtime-audit.json. "
        "Batch 604 removed the 光标/相机/手 mode segment that this batch's "
        "original docstring transcribed from screenshot 18; the source has no "
        "such control."
    )


if __name__ == "__main__":
    main()
