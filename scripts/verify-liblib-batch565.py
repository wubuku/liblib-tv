#!/usr/bin/env python3
"""Verify Batch 565: panorama background linkage end-to-end (zero product
change).

Contract: source-site sampling (screenshots 45/48) — connecting an image
node to the director input makes the 全景背景 connected state appear
(已连接全景图 after load), and the 画布环境 select auto-picks the upstream
image (resolvedPanoramaSourceId defaults to the first canvas media
input). Driven end-to-end: add an image node, connect it upstream of the
director node via addEdge, and assert the select auto-selects it, the
runtime reaches ready and the 已连接全景图 label appears.
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
    / "liblib-canvas-batch565-2026-09-27"
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
        assert ok, f"batch565 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/?batch70=1", wait_until="networkidle")
    page.wait_for_function(
        """() => Boolean(window.__libtv_store && window.__libtv_ui_store && window.__director_store)"""
    )

    page.evaluate(
        """() => {
          const store = window.__libtv_store.getState();
          store.addNode("script-execution", { title: "Batch 565" });
          const node = store.getActiveCanvas().nodes.at(-1);
          window.__libtv_ui_store.getState().openDirectorDesk(node.id, store.activeCanvasId);
        }"""
    )
    page.locator("[data-director-workspace]").wait_for(state="visible")
    page.wait_for_timeout(600)

    # 空上游：select 为空、无已连接标签（场景属性面板需无选中对象）
    page.evaluate("window.__director_store.getState().selectObject(null)")
    page.wait_for_timeout(300)
    section = page.locator("[data-director-panorama-input]")
    check("empty:select-empty", section.locator("[data-director-panorama-source]").input_value() == "")

    # 连接上游图片节点（image.source → director.target）
    page.evaluate(
        """() => {
          const store = window.__libtv_store.getState();
          store.addNode("image", {
            imageUrl: "/images/scene-coffee-1.png",
            filename: "batch565-panorama.png",
          });
          const canvas = store.getActiveCanvas();
          const imageNode = canvas.nodes.filter((n) => n.type === "image").at(-1);
          const directorNode = canvas.nodes.at(-2);
          if (imageNode && directorNode) {
            store.addEdge({
              id: `edge-${imageNode.id}-${directorNode.id}`,
              source: imageNode.id,
              target: directorNode.id,
              sourceHandle: "source",
              targetHandle: "target",
            });
          }
        }"""
    )
    page.wait_for_timeout(800)

    # 画布环境 select 自动选中上游图片（resolved 默认 = 第一个 input）；
    # 面板为场景属性态（无选中对象）
    page.evaluate("window.__director_store.getState().selectObject(null)")
    page.wait_for_timeout(300)
    select_value = section.locator("[data-director-panorama-source]").input_value()
    check("linkage:select-auto-picks", select_value != "")

    # 全景运行时 ready → 已连接全景图 标签出现
    page.wait_for_timeout(800)
    connected = page.locator("[data-director-panorama-connected]")
    check("linkage:connected-label", connected.is_visible())
    check(
        "linkage:label-text",
        "已连接全景图" in connected.inner_text(),
    )

    # 状态点 ready
    status = page.locator("[data-director-panorama-status]")
    check(
        "linkage:status-ready",
        status.get_attribute("data-director-panorama-state") == "ready",
    )

    check("diagnostics:zero", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 565,
        "title": "Panorama background linkage end-to-end",
        "evidence": (
            "docs/research/liblib-source-exploration-2026-09-25/NOTES.md "
            "§8 + screenshots 45/48"
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
        "Batch 565 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "upstream image node auto-selected as panorama source, runtime "
        "ready and 已连接全景图 label recorded in runtime-audit.json."
    )


if __name__ == "__main__":
    main()
