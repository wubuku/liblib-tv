#!/usr/bin/env python3

"""Verify Batch 164: footer trigger geometry per sampled source class strings.

Source evidence (2026-09-07 chain dumps):
- model trigger: `h-8 min-w-[88px] justify-between px-2 py-1`, 13px normal weight
- mode trigger: `justify-center py-1 pl-2 pr-2.5`
- footer row: 32px tall, no top border
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
    / "liblib-canvas-batch164-2026-09-07"
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
        assert ok, f"batch164 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(BASE_URL, wait_until="networkidle")
    page.wait_for_timeout(400)

    page.get_by_role("button", name="添加节点").click()
    page.wait_for_timeout(400)
    panel = page.locator("[data-liblib-overlay='add-node']")
    panel.get_by_role("button", name="视频", exact=True).click()
    page.wait_for_timeout(1200)
    node = page.locator(".react-flow__node-video").first
    node.click()
    page.wait_for_timeout(600)

    vg = page.locator("[data-video-generation-panel]")
    model = vg.locator("[data-video-model-trigger]")
    mode = vg.locator("[data-video-mode-trigger]")

    mbox = model.bounding_box()
    check("model:min-w-88", mbox is not None and mbox["width"] >= 87)
    check("model:h-32", mbox is not None and 30 <= mbox["height"] <= 34)
    check(
        "model:justify-between",
        model.evaluate("el => getComputedStyle(el).justifyContent") == "space-between",
    )
    check(
        "model:text-13-normal",
        model.evaluate(
            "el => { const s = getComputedStyle(el.querySelector('span')); return s.fontSize + '/' + s.fontWeight; }"
        )
        in ("13px/400", "13px/normal"),
    )
    check(
        "mode:padding",
        mode.evaluate(
            "el => { const s = getComputedStyle(el); return s.paddingLeft + '/' + s.paddingRight; }"
        )
        in ("8px/10px",),
    )
    footer = vg.locator("footer")
    fbox = footer.bounding_box()
    check("footer:h-32", fbox is not None and 30 <= fbox["height"] <= 34)
    check(
        "footer:no-border",
        footer.evaluate("el => getComputedStyle(el).borderTopWidth") == "0px",
    )

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 164, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch164: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
