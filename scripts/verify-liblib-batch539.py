#!/usr/bin/env python3
"""Verify Batch 539: director AI image-recognition import modal.

Contract: source-site sampling 2026-09-27 (transcribed from saved
screenshot 44-director-rail-27.png) — the rail's AI 识图导入 entry opens a
centered modal: title + close; 本地上传/历史记录 tabs; dashed dropzone
(点击上传图片 或 拖拽本地图片至此上传; 上传后画布将新连一个图片节点并
自动替换当前图源); radio group 选择是否覆盖场景 — 插入当前导演台 (default,
作为站位参考层插入，不覆盖当前全景、角色和机位) vs 覆盖当前导演台
(…覆盖当前全景、角色和机位); footer 关闭不会中断识图任务，生成站位参考
后自动导入导演台 + 生成站位参考 button held in the disabled state —
real recognition/upload/generation are cloud AI actions and are never
triggered. 历史记录 tab shows an empty placeholder.
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
    / "liblib-canvas-batch539-2026-09-27"
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
        assert ok, f"batch539 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/?batch70=1", wait_until="networkidle")
    page.wait_for_function(
        """() => Boolean(window.__libtv_store && window.__libtv_ui_store)"""
    )

    page.evaluate(
        """() => {
          const store = window.__libtv_store.getState();
          store.addNode("script-execution", { title: "Batch 539" });
          const node = store.getActiveCanvas().nodes.at(-1);
          window.__libtv_ui_store.getState().openDirectorDesk(node.id, store.activeCanvasId);
        }"""
    )
    page.locator("[data-director-workspace]").wait_for(state="visible")
    page.wait_for_timeout(400)

    # 打开模态
    page.locator("[data-director-rail-entry='ai-import']").click()
    page.wait_for_timeout(250)
    modal = page.locator("[data-director-ai-import-modal]")
    check("modal:opens", modal.is_visible())
    check("modal:title", "AI 识图导入" in modal.inner_text())

    # 页签与上传区
    check(
        "modal:tab-upload-active",
        modal.locator("[data-director-ai-import-tab='upload']").get_attribute("aria-pressed") == "true",
    )
    dropzone = modal.locator("[data-director-ai-import-dropzone]")
    dropzone_text = dropzone.inner_text()
    for token in ["点击上传图片", "拖拽本地图片至此上传", "上传后画布将新连一个图片节点并自动替换当前图源"]:
        check(f"modal:dropzone:{token[:8]}", token in dropzone_text)

    # 覆盖场景单选组
    check(
        "coverage:insert-default",
        modal.locator("[data-director-coverage-option='insert']").get_attribute("aria-pressed") == "true",
    )
    modal.locator("[data-director-coverage-option='override']").click()
    page.wait_for_timeout(150)
    check(
        "coverage:override-selected",
        modal.locator("[data-director-coverage-option='override']").get_attribute("aria-pressed") == "true",
    )
    check(
        "coverage:insert-inactive",
        modal.locator("[data-director-coverage-option='insert']").get_attribute("aria-pressed") == "false",
    )
    check(
        "coverage:details",
        "不覆盖当前全景、角色和机位" in modal.inner_text()
        and "覆盖当前全景、角色和机位" in modal.inner_text(),
    )

    # 生成站位参考保持禁用（付费 AI 动作不触发）
    check(
        "generate:disabled",
        modal.locator("[data-director-ai-import-generate]").is_disabled(),
    )
    check(
        "footer:notice",
        "关闭不会中断识图任务" in modal.inner_text(),
    )

    # 历史记录页签：空态占位
    modal.locator("[data-director-ai-import-tab='history']").click()
    page.wait_for_timeout(150)
    check("history:empty-placeholder", "暂无历史记录" in modal.inner_text())

    # ✕ 关闭 → 重开（force 规避模态卸载瞬间的遮挡重试）→ 背景点击关闭
    modal.locator("[data-director-ai-import-close]").click()
    page.wait_for_timeout(200)
    check("close:x", page.locator("[data-director-ai-import-modal]").count() == 0)
    page.locator("[data-director-rail-entry='ai-import']").click(force=True)
    page.wait_for_timeout(250)
    check("reopen:modal", page.locator("[data-director-ai-import-modal]").is_visible())
    page.locator("[data-director-ai-import-backdrop]").click(position={"x": 1150, "y": 650})
    page.wait_for_timeout(200)
    check("close:backdrop", page.locator("[data-director-ai-import-modal]").count() == 0)

    check("diagnostics:zero", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 539,
        "title": "Director AI image-recognition import modal",
        "evidence": (
            "docs/research/liblib-source-exploration-2026-09-25/NOTES.md "
            "§8 + screenshot 44-director-rail-27 (transcription)"
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
        "Batch 539 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "AI 识图导入 modal (tabs, dropzone, coverage radio group, disabled "
        "generate button, history empty state, close paths) recorded in "
        "runtime-audit.json."
    )


if __name__ == "__main__":
    main()
