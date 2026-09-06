#!/usr/bin/env python3

"""Verify Batch 139 topbar credits supermarket / balance split."""

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
    / "liblib-canvas-batch139-2026-09-07"
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
        assert ok, f"batch139 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(BASE_URL, wait_until="networkidle")
    page.wait_for_timeout(400)

    check("supermarket:entry", page.get_by_role("button", name="积分超市", exact=True).count() == 1)
    check("balance:entry", page.get_by_role("button", name="积分余额", exact=True).count() == 1)
    check(
        "balance:value",
        "100" in page.get_by_role("button", name="积分余额", exact=True).inner_text(),
    )
    check("membership:entry", page.get_by_role("button", name="开通会员 限时 45 折", exact=True).count() == 1)

    # 顺序：积分超市 在 积分余额 之前（源站顺序）
    order = page.evaluate(
        """() => {
          const btns = Array.from(document.querySelectorAll('button')).map((b, i) => ({ i, label: b.getAttribute('aria-label') || '', x: b.getBoundingClientRect().x }));
          const sup = btns.find((b) => b.label === '积分超市');
          const bal = btns.find((b) => b.label === '积分余额');
          return sup && bal ? sup.x < bal.x : null;
        }"""
    )
    check("order:supermarket-before-balance", order is True)

    check("diagnostics:zero", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 139,
        "title": "Topbar credits supermarket / balance split",
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
        "Batch 139 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "Credits supermarket and balance entries, order and membership entry "
        "recorded in runtime-audit.json."
    )


if __name__ == "__main__":
    main()
