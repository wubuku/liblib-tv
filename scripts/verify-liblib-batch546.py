#!/usr/bin/env python3
"""Verify Batch 546: AI import history tab lists imported local models.

Contract: source-site sampling shows the AI 识图导入 modal's 历史记录 tab
(batch 539; account was empty → 暂无历史记录). Source history content with
entries was never sampled (SOURCE_UNCERTAIN); the clone's local equivalent
(batch 546) lists directorStore.localModelLibrary entries — models the
user imported through the 本地上传 pipeline — as recognition-source
candidates. Fresh state keeps the 暂无历史记录 empty state.
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
    / "liblib-canvas-batch546-2026-09-27"
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
        assert ok, f"batch546 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/?batch70=1", wait_until="networkidle")
    page.wait_for_function(
        """() => Boolean(window.__libtv_store && window.__libtv_ui_store && window.__director_store)"""
    )

    page.evaluate(
        """() => {
          const store = window.__libtv_store.getState();
          store.addNode("script-execution", { title: "Batch 546" });
          const node = store.getActiveCanvas().nodes.at(-1);
          window.__libtv_ui_store.getState().openDirectorDesk(node.id, store.activeCanvasId);
        }"""
    )
    page.locator("[data-director-workspace]").wait_for(state="visible")
    page.wait_for_timeout(400)

    # 打开 AI 导入模态 → 历史记录空态（batch 539 合同）
    page.locator("[data-director-rail-entry='ai-import']").click()
    page.wait_for_timeout(250)
    modal = page.locator("[data-director-ai-import-modal]")
    modal.locator("[data-director-ai-import-tab='history']").click()
    page.wait_for_timeout(200)
    check(
        "history:fresh-empty",
        "暂无历史记录" in modal.locator("[data-director-ai-import-history]").inner_text(),
    )
    modal.locator("[data-director-ai-import-close]").click()
    page.wait_for_timeout(200)

    # 通过角色 flyout 本地上传导入一个模型（batch 542 管线）
    page.locator("[data-director-rail-entry='add-character']").click()
    page.wait_for_timeout(200)
    with page.expect_file_chooser() as chooser_info:
        page.locator("[data-director-character-option='local-upload']").click()
    chooser_info.value.set_files(["/tmp/batch542-fixture/hero-character.fbx"])
    page.wait_for_timeout(500)

    # 重开模态 → 历史记录列出已导入模型
    page.locator("[data-director-rail-entry='ai-import']").click()
    page.wait_for_timeout(250)
    modal.locator("[data-director-ai-import-tab='history']").click()
    page.wait_for_timeout(200)
    history = modal.locator("[data-director-ai-import-history]")
    check(
        "history:lists-model",
        history.locator("[data-director-ai-import-history-item]").count() == 1,
    )
    check("history:file-name", "hero-character.fbx" in history.inner_text())

    check("diagnostics:zero", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 546,
        "title": "AI import history tab lists local model library",
        "evidence": (
            "docs/research/liblib-source-exploration-2026-09-25/NOTES.md "
            "§8 + screenshot 44-director-rail-27 (batch 539); history "
            "content with entries unsampled — local-equivalent CLONE_DECISION"
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
        "Batch 546 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "history tab keeps the fresh empty state and lists imported local "
        "models after a batch-542 upload, recorded in runtime-audit.json."
    )


if __name__ == "__main__":
    main()
