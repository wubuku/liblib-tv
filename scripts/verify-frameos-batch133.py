#!/usr/bin/env python3

"""Verify Batch 133 FrameOS duplicate node insertion."""

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
    / "liblib-frameos-batch133-2026-09-06"
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
        assert ok, f"batch133 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/frameos/canvas/demo", wait_until="domcontentloaded")
    page.wait_for_timeout(1200)

    nodes_before = page.locator(".react-flow__node").count()
    check("boot:nodes", nodes_before >= 5)

    # 选中第一个节点
    page.locator(".react-flow__node").first.click()
    page.wait_for_timeout(400)
    selected_title = page.evaluate(
        "() => window.__frameos_store.getState().nodes.find((n) => n.id === window.__frameos_store.getState().selectedNodeId)?.data?.title ?? null"
    )

    # Cmd+D 复制
    page.keyboard.press("Meta+d")
    page.wait_for_timeout(600)

    nodes_after = page.locator(".react-flow__node").count()
    check("duplicate:node-added", nodes_after == nodes_before + 1)
    check("duplicate:selected-id", page.evaluate("() => window.__frameos_store.getState().selectedNodeId") is not None)
    new_title = page.evaluate(
        "() => window.__frameos_store.getState().nodes.find((n) => n.id === window.__frameos_store.getState().selectedNodeId)?.data?.title ?? null"
    )
    check("duplicate:title-copy", new_title is not None and "副本" in new_title)
    check("duplicate:visual-selected", page.locator(".react-flow__node.selected").count() >= 1)

    # undo → 恢复
    page.keyboard.press("Meta+z")
    page.wait_for_timeout(500)
    check("undo:node-removed", page.locator(".react-flow__node").count() == nodes_before)

    # redo → 再次出现
    page.keyboard.press("Meta+Shift+z")
    page.wait_for_timeout(500)
    check("redo:node-back", page.locator(".react-flow__node").count() == nodes_before + 1)

    # toast 出现过（已复制）——重新复制一次并检查 toast 文本
    page.evaluate(
        "() => { const s = window.__frameos_store.getState(); if (s.selectedNodeId) s.duplicateNode(s.selectedNodeId); }"
    )
    page.wait_for_timeout(400)
    check("toast:copy", "已复制" in page.inner_text("body"))
    check("duplicate:title-source", selected_title is not None)

    check("diagnostics:zero", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 133,
        "title": "FrameOS duplicate node insertion",
        "evidence": "docs/research/liblib-canvas-sampling-2026-09-06/README.md",
        "results": [],
    }
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        desktop = browser.new_page(viewport={"width": 1440, "height": 900}, device_scale_factor=1)
        audit["results"].append(run_desktop(desktop))
        desktop.close()
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    checks = audit["results"][0]["checks"]
    print(
        "Batch 133 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "Cmd+D duplicate inserts node, selects copy with 副本 title, undo/redo "
        "and copy toast recorded in runtime-audit.json."
    )


if __name__ == "__main__":
    main()
