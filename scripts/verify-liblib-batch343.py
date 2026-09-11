#!/usr/bin/env python3
"""Verify Batch 343: top-bar chrome matches the 2026-09-11 source
evidence (docs/research/liblib-canvas-batch342-2026-09-11/ + batch343).

Source evidence (2026-09-11, screenshots + three independent
button-text dumps of the source top bar, all consistent):
- no 积分超市 entry (the batch-139-era dual entry is gone)
- right-side order: 发布与分享 -> 开通会员(限时45折) -> 积分余额(100)
  -> Agent
- membership pill shows 青色商店图标 + 开通会员 + 限时 45 折
- blue mini icon between share and membership and the round avatar
  are SOURCE_UNKNOWN (not fabricated in the clone)
"""

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
    / "liblib-canvas-batch343-2026-09-11"
    / "runtime-audit.json"
)

RIGHT_ORDER = ["发布与分享", "开通会员 限时 45 折", "积分余额"]


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
        assert ok, f"batch343 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto("http://localhost:4317", wait_until="networkidle")
    page.wait_for_timeout(600)

    # ---- supermarket entry is gone from the top bar
    check("supermarket:gone", page.get_by_role("button", name="积分超市", exact=True).count() == 0)

    # ---- right-side entries exist and keep the source order
    xs = []
    for label in RIGHT_ORDER:
        button = page.get_by_role("button", name=label, exact=True)
        check(f"entry:{label}", button.count() == 1)
        box = button.first.bounding_box()
        xs.append(box["x"] if box else None)
    check(
        "order:membership-before-balance",
        bool(xs[1] is not None and xs[2] is not None and xs[1] < xs[2]),
    )
    check(
        "order:share-first",
        bool(xs[0] is not None and xs[1] is not None and xs[0] < xs[1]),
    )

    # ---- membership pill content
    membership = page.get_by_role("button", name="开通会员 限时 45 折", exact=True)
    check(
        "membership:copy",
        "开通会员" in membership.inner_text() and "限时 45 折" in membership.inner_text(),
    )

    # ---- balance value
    check(
        "balance:copy",
        "100" in page.get_by_role("button", name="积分余额", exact=True).inner_text(),
    )

    # ---- Agent entry at the far right of the actions cluster
    agent = page.get_by_role("button", name="Agent", exact=True)
    check("agent:entry", agent.count() == 1)
    agent_box = agent.first.bounding_box()
    check(
        "agent:rightmost",
        bool(agent_box and xs[2] is not None and agent_box["x"] > xs[2]),
    )

    # ---- top-left chrome unaffected
    check("left:workspace-input", page.locator('input[aria-label="工作区名称"]').is_visible())
    check("left:canvas-chip", page.get_by_role("button", name="画布 2").count() == 1)

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 343, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch343: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
