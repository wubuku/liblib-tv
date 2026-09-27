#!/usr/bin/env python3
"""Verify Batch 542: character flyout 本地上传 wired to the local model
library import pipeline.

Contract: source-site sampling (batch 537, screenshot 44-director-rail-23)
— the 添加角色 flyout's 本地上传 entry uploads a custom character model.
In the clone the entry reuses the director local-model-library import
pipeline (readDirectorLocalModelFiles → addLocalModelLibraryItem, the same
pipeline as the DirectorViewport model library): a file chooser opens,
valid model files (.glb/.gltf/.fbx/.obj) are added to the local model
library, and an acknowledgement flashes. No cloud action occurs.
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
    / "liblib-canvas-batch542-2026-09-27"
    / "runtime-audit.json"
)

FIXTURES = Path("/tmp/batch542-fixture")


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
        assert ok, f"batch542 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/?batch70=1", wait_until="networkidle")
    page.wait_for_function(
        """() => Boolean(window.__libtv_store && window.__libtv_ui_store && window.__director_store)"""
    )

    page.evaluate(
        """() => {
          const store = window.__libtv_store.getState();
          store.addNode("script-execution", { title: "Batch 542" });
          const node = store.getActiveCanvas().nodes.at(-1);
          window.__libtv_ui_store.getState().openDirectorDesk(node.id, store.activeCanvasId);
        }"""
    )
    page.locator("[data-director-workspace]").wait_for(state="visible")
    page.wait_for_timeout(400)

    library_before = page.evaluate(
        "window.__director_store.getState().localModelLibrary.length"
    )

    rail = page.locator("[data-director-icon-rail]")
    rail.locator("[data-director-rail-entry='add-character']").click()
    page.wait_for_timeout(200)
    flyout = page.locator("[data-director-character-flyout]")
    check("flyout:opens", flyout.is_visible())

    # 本地上传 → 文件选择（隐藏 input 复用本地模型库导入管线）
    with page.expect_file_chooser() as chooser_info:
        flyout.locator("[data-director-character-option='local-upload']").click()
    chooser = chooser_info.value
    check("upload:file-chooser", chooser.is_multiple())
    chooser.set_files(
        [str(FIXTURES / "hero-character.fbx"), str(FIXTURES / "prop-mesh.obj")]
    )
    page.wait_for_timeout(500)

    library_after = page.evaluate(
        "window.__director_store.getState().localModelLibrary.length"
    )
    check(
        "upload:library-gains-two",
        library_after == library_before + 2,
    )
    ack = page.locator("[data-director-character-ack]")
    check("upload:ack", "已导入 2 个本地模型至模型库" in ack.inner_text())
    check("upload:flyout-closed", flyout.count() == 0)

    # ack 自动淡出
    page.wait_for_timeout(2200)
    check("ack:auto-dismiss", page.locator("[data-director-character-ack]").count() == 0)

    check("diagnostics:zero", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 542,
        "title": "Character flyout 本地上传 to local model library pipeline",
        "evidence": (
            "docs/research/liblib-source-exploration-2026-09-25/NOTES.md "
            "§8 + screenshot 44-director-rail-23 (batch 537)"
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
        "Batch 542 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "本地上传 opens a file chooser and imports valid model files into "
        "the director local model library with an acknowledgement, recorded "
        "in runtime-audit.json."
    )


if __name__ == "__main__":
    main()
