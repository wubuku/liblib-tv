#!/usr/bin/env python3

"""Verify Batch 224: FrameOS material library round-2 alignment + 添加参考素材.

Source sampling 2026-09-25 (selected a library asset and clicked
添加参考素材 on frameos.cn): the action creates a content-bearing node per
selected asset on the canvas (audio asset → audio node with player, titled
by asset name, no edges), then CLOSES the library; the footer button is
disabled while nothing is selected. The library tree has 全部素材/我的收藏
top-level entries; the filter row also carries 收藏/创建者/创建时间; asset
cards show a duration badge and the creator name.

Checks:
1. library opens with 全部素材/我的收藏 tree rows + 收藏/创建者/创建时间;
2. footer 添加参考素材 disabled at 0 selected;
3. selecting 环境音效 → enabled + 已选 1 个 → click → dialog closes and a
   content audio node 环境音效 with the player row appears on canvas;
4. errors clean.
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
    / "liblib-frameos-batch224-2026-09-25"
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
    page.on("dialog", lambda d: d.dismiss())
    return errors


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool) -> None:
        assert ok, f"batch224 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/frameos/canvas/demo", wait_until="domcontentloaded")
    page.wait_for_timeout(1200)
    nodes_before = page.evaluate(
        "window.__frameos_store.getState().nodes.length"
    )

    # 1) 打开素材库
    page.locator("button[aria-label='从素材库选择']").click()
    page.wait_for_timeout(500)
    dialog = page.locator("[role=dialog][aria-label='素材库']")
    check("library:opens", dialog.is_visible())
    tree_text = dialog.inner_text()
    for folder in ["全部素材", "我的收藏", "测试作品", "测试项目", "工具箱素材", "画布素材", "上传素材"]:
        check(f"library:tree:{folder}", folder in tree_text)
    check("library:filter-favorite", dialog.locator("button[aria-label='收藏筛选']").count() == 1)
    check("library:filter-creator", dialog.locator("button[aria-label='创建者筛选']").count() == 1)
    check("library:filter-time", dialog.locator("button[aria-label='创建时间排序']").count() == 1)

    # 2) 0 选中 → 添加按钮禁用
    add_btn = dialog.locator("button[aria-label='添加参考素材']")
    check("footer:add-disabled-at-zero", add_btn.is_disabled())

    # 3) 选中 环境音效 → 添加 → 画布建内容音频节点 + 素材库关闭
    card = dialog.locator("[data-frameos-material-card='环境音效']")
    check("library:audio-card", card.count() == 1)
    check(
        "library:duration-badge",
        card.locator("[data-frameos-material-duration]").count() == 1,
    )
    card.click()
    page.wait_for_timeout(300)
    check("footer:add-enabled", add_btn.is_enabled())
    check("footer:selected-count", "已选 1 个" in dialog.inner_text())
    add_btn.click()
    page.wait_for_timeout(700)
    check("library:closes-after-add", not dialog.is_visible())
    state = page.evaluate(
        """(() => {
          const s = window.__frameos_store.getState();
          const audio = s.nodes.filter((n) => n.type === 'audio');
          const last = audio[audio.length - 1];
          return { count: s.nodes.length, title: last?.data?.title,
                   audioUrl: last?.data?.audioUrl };
        })()"""
    )
    check("add:node-created", state["count"] == nodes_before + 1)
    check("add:title-from-asset", state["title"] == "环境音效")
    check("add:audio-content", (state["audioUrl"] or "").startswith("/audio/"))
    audio_node = page.locator(".react-flow__node-audio").last
    check(
        "add:player-rendered",
        audio_node.locator("[data-frameos-audio-player]").count() == 1,
    )

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 224, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch224: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
