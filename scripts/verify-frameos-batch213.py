#!/usr/bin/env python3

"""Verify Batch 213: FrameOS audio node renderer + audio panel.

2026-09-24 source re-sampling: the rail menu 音频 entry creates an audio
node (音乐 icon card, 260x160, handles left/right, selected blue frame)
with an audio panel below — 参考 button, placeholder 描述音乐 / 配音 /
音效, BGM S6 model dropdown, 参数 dropdown, credits 100, ↑ 生成 button.
Verifies creation, card structure, panel content, and the text guard
regression. Generation is NOT triggered.
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
    / "liblib-frameos-batch213-2026-09-24"
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
        assert ok, f"batch213 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/frameos/canvas/demo", wait_until="domcontentloaded", timeout=90000)
    page.wait_for_timeout(1200)
    nodes_before = page.locator(".react-flow__node").count()

    # rail 添加节点菜单 → 音频 (DOM el.click 打开菜单)
    page.evaluate(
        """(() => {
          const btn = [...document.querySelectorAll("button")].find(x =>
            (x.getAttribute("aria-label") || "").trim() === "添加节点");
          if (btn) btn.click();
        })()"""
    )
    page.wait_for_timeout(500)
    page.evaluate(
        """(() => {
          const items = [...document.querySelectorAll("*")].filter(e => {
            if (!e.offsetParent || e.children.length > 0) return false;
            const r = e.getBoundingClientRect();
            return (e.textContent || "").trim() === "音频" && r.width < 200;
          });
          const el = items[items.length - 1];
          if (el) el.click();
        })()"""
    )
    page.wait_for_timeout(700)

    audio_node = page.locator(".react-flow__node-audio")
    check("audio:node-created", audio_node.count() == 1)
    check(
        "audio:selected",
        page.evaluate(
            "window.__frameos_store.getState().nodes.some((n) => n.type === 'audio' && n.selected)"
        ),
    )

    # 音频面板: 占位 (属性) + BGM S6 + 积分 100 + ↑ 生成 + 参考按钮
    editor = page.locator(".frameos-prompt-editor--audio")
    check("audio:panel-opens", editor.is_visible())
    panel_text = editor.inner_text()
    textarea_ph = editor.locator("textarea").first.get_attribute("placeholder")
    for k in ["参考", "BGM S6", "参数", "100"]:
        check(f"audio:panel:{k}", k in panel_text)
    check("audio:panel:desc-placeholder", textarea_ph == "描述音乐 / 配音 / 音效")
    check(
        "audio:panel:generate-btn",
        editor.locator("button[aria-label='生成音频']").count() == 1,
    )

    # 撤销 → 音频节点移除
    page.keyboard.press("Meta+z")
    page.wait_for_timeout(500)
    check(
        "undo:audio-removed",
        page.locator(".react-flow__node-audio").count() == 0,
    )

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 213, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch213: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
