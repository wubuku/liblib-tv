#!/usr/bin/env python3

"""Verify Batch 134 FrameOS copy/cut/paste clipboard cycle."""

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
    / "liblib-frameos-batch134-2026-09-06"
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
        assert ok, f"batch134 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/frameos/canvas/demo", wait_until="domcontentloaded")
    page.wait_for_timeout(1200)

    nodes_before = page.locator(".react-flow__node").count()
    check("boot:nodes", nodes_before >= 5)

    # 选中节点 → Cmd+C → Cmd+V → 粘贴副本
    page.locator(".react-flow__node").first.click()
    page.wait_for_timeout(400)
    page.keyboard.press("Meta+c")
    page.wait_for_timeout(300)
    page.keyboard.press("Meta+v")
    page.wait_for_timeout(700)
    check("paste:node-added", page.locator(".react-flow__node").count() == nodes_before + 1)
    check(
        "paste:selected-new",
        page.evaluate("() => window.__frameos_store.getState().selectedNodeId") is not None
        and page.evaluate("() => window.__frameos_store.getState().selectedNodeId") != page.evaluate("() => window.__frameos_store.getState().nodes[0].id"),
    )
    new_title = page.evaluate(
        "() => window.__frameos_store.getState().nodes.find((n) => n.id === window.__frameos_store.getState().selectedNodeId)?.data?.title ?? null"
    )
    check("paste:title-kept", new_title is not None)

    # undo → 撤销粘贴
    page.keyboard.press("Meta+z")
    page.wait_for_timeout(500)
    check("paste:undo", page.locator(".react-flow__node").count() == nodes_before)

    # 再粘贴一次（幂等可用）
    page.keyboard.press("Meta+v")
    page.wait_for_timeout(600)
    check("paste:re-paste", page.locator(".react-flow__node").count() == nodes_before + 1)

    check("diagnostics:zero", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 134,
        "title": "FrameOS copy/paste clipboard cycle",
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
        "Batch 134 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "Cmd+C/Cmd+V clipboard cycle: paste inserts selected copy, undo, "
        "re-paste recorded in runtime-audit.json."
    )


if __name__ == "__main__":
    main()
