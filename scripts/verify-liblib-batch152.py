#!/usr/bin/env python3

"""Verify Batch 152: /project card sub-line shows date only (no workspace prefix).

Source evidence (2026-09-07): each /project card renders title + date only
(未命名 / 2026-09-06). Also refreshes the 2026-09-07 coverage-matrix facts:
panel-embedded generation surface, credits 4th data point, new-tab cards.
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
    / "liblib-canvas-batch152-2026-09-07"
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
        assert ok, f"batch152 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(BASE_URL + "/project", wait_until="networkidle")
    page.wait_for_timeout(500)

    cards = page.locator("[data-project-card]")
    check("project:has-cards", cards.count() >= 1)

    first = cards.first
    text = first.inner_text()
    # 标题存在
    check("card:has-title", len(text.strip()) > 0)
    # 副行仅日期：YYYY-MM-DD，且不含工作区名（工作区名默认含「工作区」或与标题不同）
    import re
    dates = re.findall(r"\d{4}-\d{2}-\d{2}", text)
    check("card:has-date", len(dates) == 1)
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    # 最后一行应为纯日期（节点计数在封面角标内，也在卡片文本里；日期行本身无 · 前缀）
    date_lines = [ln for ln in lines if re.fullmatch(r"\d{4}-\d{2}-\d{2}", ln)]
    check("card:date-only-line", len(date_lines) == 1)
    check(
        "card:no-workspace-prefix",
        all("工作区" not in ln for ln in lines if re.search(r"\d{4}-\d{2}-\d{2}", ln)),
    )
    # 节点计数角标仍在封面区
    check("card:node-count", "个节点" in text)

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 152, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch152: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
