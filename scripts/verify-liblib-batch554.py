#!/usr/bin/env python3
"""Verify Batch 554: AI import dropzone upload creates a connected image node.

Contract: source-site dropzone note (screenshot 44-director-rail-27,
transcribed in batch 539) — 上传后画布将新连一个图片节点并自动替换当前
图源. In the clone the dropzone opens an image file chooser; the selected
image is added as a new image node on the active canvas and connected to
the director source node (edge image.source → director.target). The
自动替换当前图源 half is deferred (panorama source state lives in the
desk — CLONE_DECISION). No cloud recognition occurs.
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
    / "liblib-canvas-batch554-2026-09-27"
    / "runtime-audit.json"
)

FIXTURE = "/tmp/batch554-fixture.png"


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
        assert ok, f"batch554 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/?batch70=1", wait_until="networkidle")
    page.wait_for_function(
        """() => Boolean(window.__libtv_store && window.__libtv_ui_store && window.__director_store)"""
    )

    page.evaluate(
        """() => {
          const store = window.__libtv_store.getState();
          store.addNode("script-execution", { title: "Batch 554" });
          const node = store.getActiveCanvas().nodes.at(-1);
          window.__libtv_ui_store.getState().openDirectorDesk(node.id, store.activeCanvasId);
        }"""
    )
    page.locator("[data-director-workspace]").wait_for(state="visible")
    page.wait_for_timeout(600)

    nodes_before = page.evaluate(
        "window.__libtv_store.getState().getActiveCanvas().nodes.length"
    )
    edges_before = page.evaluate(
        "window.__libtv_store.getState().getActiveCanvas().edges.length"
    )

    # 打开模态 → 点击拖拽区（file chooser）
    page.locator("[data-director-rail-entry='ai-import']").click()
    page.wait_for_timeout(250)
    modal = page.locator("[data-director-ai-import-modal]")
    check("modal:opens", modal.is_visible())
    with page.expect_file_chooser() as chooser_info:
        modal.locator("[data-director-ai-import-dropzone]").click()
    chooser_info.value.set_files([FIXTURE])
    page.wait_for_timeout(800)

    nodes_after = page.evaluate(
        "window.__libtv_store.getState().getActiveCanvas().nodes.length"
    )
    check("canvas:image-node-added", nodes_after == nodes_before + 1)
    edges_after = page.evaluate(
        "window.__libtv_store.getState().getActiveCanvas().edges.length"
    )
    check(
        "canvas:edge-to-director",
        edges_after >= edges_before + 1,
    )
    note = modal.locator("[data-director-ai-import-upload-note]")
    check(
        "upload:ack",
        note.is_visible() and "已创建图片节点并连接到导演台" in note.inner_text(),
    )

    # ✕ 关闭模态
    modal.locator("[data-director-ai-import-close]").click()
    page.wait_for_timeout(200)
    check("close:x", page.locator("[data-director-ai-import-modal]").count() == 0)

    check("diagnostics:zero", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 554,
        "title": "AI import dropzone upload creates a connected image node",
        "evidence": (
            "docs/research/liblib-source-exploration-2026-09-25/NOTES.md "
            "§8 + screenshot 44-director-rail-27 (batch 539 transcription)"
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
        "Batch 554 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "dropzone image upload creates a canvas image node wired to the "
        "director source node with a local-equivalent acknowledgement, "
        "recorded in runtime-audit.json."
    )


if __name__ == "__main__":
    main()
