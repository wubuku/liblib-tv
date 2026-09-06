#!/usr/bin/env python3

"""Verify Batch 150: /project card opens canvas in a new tab + add-panel container visuals.

Source evidence (2026-09-07, external Chrome CDP DOM):
- /project canvas card click opens /canvas in a NEW tab; the list page stays put.
- add-node panel container: rounded-2xl + backdrop-blur-[32px] + hairline border
  (39px narrow rail was a frozen mid-animation state, not a collapsed mode).
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
    / "liblib-canvas-batch150-2026-09-07"
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
        assert ok, f"batch150 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(BASE_URL + "/project", wait_until="networkidle")
    page.wait_for_timeout(500)

    check(
        "project:page-visible",
        page.locator("[data-project-list-page]").is_visible(),
    )
    cards = page.locator("[data-project-card]")
    check("project:has-cards", cards.count() >= 1)

    # 画布卡点击 → 新标签页打开画布，列表页保持不动。
    with page.context.expect_page() as popup_info:
        cards.first.click()
    popup = popup_info.value
    check("card:stays-on-project", page.url.endswith("/project"))
    popup.wait_for_timeout(900)
    check("popup:on-canvas", popup.locator(".react-flow").count() >= 1)
    check("popup:not-project", not popup.url.endswith("/project"))
    popup.close()

    # 添加节点面板容器：rounded-2xl(16px) + backdrop-blur(32px)。
    page.goto(BASE_URL, wait_until="networkidle")
    page.wait_for_timeout(400)
    page.get_by_role("button", name="添加节点").click()
    page.wait_for_timeout(300)
    panel = page.locator("[data-liblib-overlay='add-node']")
    check("addpanel:visible", panel.is_visible())
    style = panel.evaluate("""(el) => {
      const cs = getComputedStyle(el);
      return { radius: cs.borderTopLeftRadius, blur: cs.backdropFilter || cs.webkitBackdropFilter || '' };
    }""")
    check("addpanel:radius-16", style["radius"] == "16px")
    check("addpanel:blur-32", "blur(32px)" in (style["blur"] or ""))

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 150, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch150: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
