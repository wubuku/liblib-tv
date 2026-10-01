#!/usr/bin/env python3
"""Verify Batch 562: AI import upload auto-selects the new node as the
panorama source (自动替换当前图源).

Contract: source-site dropzone note (batch 539/554) — 上传后画布将新连
一个图片节点并自动替换当前图源. Batch 554 landed the node+edge half;
this batch lifts the panorama source selection (DirectorDesk
selectedPanoramaSourceId) into the AI import modal via
onPanoramaSourceChange: after upload the scene panel's 画布环境 select
auto-selects the new image node.
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
    / "liblib-canvas-batch562-2026-09-29"
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
        assert ok, f"batch562 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/?batch70=1", wait_until="networkidle")
    page.wait_for_function(
        """() => Boolean(window.__libtv_store && window.__libtv_ui_store && window.__director_store)"""
    )

    page.evaluate(
        """() => {
          const store = window.__libtv_store.getState();
          store.addNode("script-execution", { title: "Batch 562" });
          const node = store.getActiveCanvas().nodes.at(-1);
          window.__libtv_ui_store.getState().openDirectorDesk(node.id, store.activeCanvasId);
        }"""
    )
    page.locator("[data-director-workspace]").wait_for(state="visible")
    page.wait_for_timeout(600)

    page.evaluate("window.__director_store.getState().selectObject(null)")
    page.wait_for_timeout(300)
    section = page.locator("[data-director-panorama-input]")
    select_before = section.locator(
        "[data-director-panorama-source]"
    ).input_value()
    check("source:empty-before", select_before == "")

    # 上传图片（batch 554 拖拽区）
    page.locator("[data-director-rail-entry='ai-import']").click()
    page.wait_for_timeout(250)
    modal = page.locator("[data-director-ai-import-modal]")
    check("modal:opens", modal.is_visible())
    with page.expect_file_chooser() as chooser_info:
        modal.locator("[data-director-ai-import-dropzone]").click()
    chooser_info.value.set_files([FIXTURE])
    page.wait_for_timeout(800)

    # 自动替换当前图源：全景源 select 选中新建节点
    select_after = section.locator(
        "[data-director-panorama-source]"
    ).input_value()
    check("source:auto-selected", select_after != "")
    new_node_id = page.evaluate(
        """() => {
          const canvas = window.__libtv_store.getState().getActiveCanvas();
          const imageNode = canvas.nodes.filter((n) => n.type === "image").at(-1);
          return imageNode ? imageNode.id : null;
        }"""
    )
    check(
        "source:points-at-new-node",
        select_after == new_node_id,
    )
    check(
        "panorama:connected-label",
        "已连接全景图" in section.inner_text()
        or section.locator("[data-director-panorama-connected]").count() == 1,
    )

    # ✕ 关闭
    modal.locator("[data-director-ai-import-close]").click()
    page.wait_for_timeout(200)
    check("close:x", page.locator("[data-director-ai-import-modal]").count() == 0)

    check("diagnostics:zero", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 562,
        "title": "AI import upload auto-selects the panorama source",
        "evidence": (
            "docs/research/liblib-source-exploration-2026-09-25/NOTES.md "
            "§8 + screenshot 44-director-rail-27 (batch 539/554)"
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
        "Batch 562 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "upload auto-selects the new image node as the panorama source in "
        "the scene panel select, recorded in runtime-audit.json."
    )


if __name__ == "__main__":
    main()
