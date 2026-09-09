#!/usr/bin/env python3
"""Verify Batch 281: history panel scope chips (全部画布 + 本画布).

Source evidence (2026-09-10, docs/research/liblib-canvas-batch280-2026-09-10/
生成历史.png): the generation history overlay carries TWO scope chips —
全部画布 and 本画布 — alongside the image/video/audio count tabs, the
所有评级/时间倒序/批量操作 controls, and the 暂无历史记录 empty state."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = (
    ROOT
    / "docs"
    / "research"
    / "liblib-canvas-batch281-2026-09-10"
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
    return errors


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool) -> None:
        assert ok, f"batch281 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto("http://localhost:4317", wait_until="networkidle")
    page.wait_for_timeout(500)

    # open the history panel via the uiStore-exposed toggle (entry tested by
    # its own batches)
    page.evaluate("""() => window.__libtv_store.setState({}) """) if False else None
    page.evaluate(
        """() => {
        const ui = document.querySelector('[data-liblib-overlay]')?.parentElement;
        // use the uiStore through the React root is not exposed; instead click
        // the toolbar entry if present, else dispatch through the add-panel
        // history item
    }"""
    )
    # open via the add-panel 从生成历史选择 (known entry, batch 205)
    page.get_by_text("资产管理", exact=True).click(force=True)
    page.wait_for_timeout(500)
    opened = page.evaluate("""() => {
        // prefer the bottom toolbar 生成历史 button when present
        for (const el of document.querySelectorAll('button')) {
            if ((el.getAttribute('aria-label') || '') === '生成历史') { el.click(); return 'toolbar'; }
        }
        return null;
    }""")
    if not opened:
        page.keyboard.press("Escape"); page.wait_for_timeout(300)
    # fall back: the uiStore toggle via keyboard shortcut is unknown; use the
    # add panel's 从生成历史选择 item which toggles the same overlay
    if page.locator("[data-liblib-overlay='primary:history']").count() == 0:
        page.get_by_role("button", name="添加节点").click()
        page.wait_for_timeout(300)
        page.locator("[data-add-node-resource='history']").click()
        page.wait_for_timeout(800)

    overlay = page.locator("[data-liblib-overlay='primary:history']")
    check("history:open", overlay.count() == 1)

    check(
        "scope:all-chip",
        page.locator('[data-history-scope-chip="all"]').count() == 1,
    )
    check(
        "scope:canvas-chip",
        page.locator("[data-history-scope-chip]").count() == 2,
    )
    check("scope:canvas-default", page.locator('[data-history-scope-chip="all"]').get_attribute("aria-pressed") == "false")
    page.locator('[data-history-scope-chip="all"]').click()
    page.wait_for_timeout(150)
    check("scope:all-switchable", page.locator('[data-history-scope-chip="all"]').get_attribute("aria-pressed") == "true")
    page.locator('[data-history-scope-chip="canvas"]').click()
    page.wait_for_timeout(150)

    for tab in ("image", "video", "audio"):
        check(f"tabs:{tab}", page.locator(f"[data-history-tab='{tab}']").count() == 1)
    for control in ("data-history-rating", "data-history-scope-chip"):
        check(f"controls:{control}", page.locator(f"[{control}]").count() >= 1)
    check("controls:sort", page.get_by_text("时间倒序").count() == 1)
    check("controls:batch", page.get_by_text("批量操作").count() == 1)
    page.locator("[data-history-tab='video']").click()
    page.wait_for_timeout(150)
    check("empty:暂无历史记录", page.get_by_text("暂无历史记录").count() >= 1)

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 281, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        try:
            audit["results"].append(run_desktop(page))
        except Exception as exc:  # noqa: BLE001
            page.screenshot(path=str(AUDIT_PATH.parent / "fail.png"))
            print("EXC:", str(exc)[:300])
            raise
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch281: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
