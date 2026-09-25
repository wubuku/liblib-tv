#!/usr/bin/env python3

"""Verify Batch 235: node search covers workspace node kinds.

Batch 221 added director3d/videoEdit nodes. NodeSearch filters by title
generically, so the new kinds must be findable and selectable.

Checks:
1. create 3D导演台 + 视频剪辑台 via the rail menu;
2. 搜索节点 → query 导演 → result lists the director node → click selects it;
3. errors clean.
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
    / "liblib-frameos-batch235-2026-09-26"
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
        assert ok, f"batch235 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/frameos/canvas/demo", wait_until="domcontentloaded", timeout=90000)
    page.wait_for_timeout(1500)

    # 1) 建两个工作台节点
    for label, kind_cls, btn in [
        ("3D导演台", ".react-flow__node-director3d", "进入导演台"),
        ("视频剪辑台", ".react-flow__node-videoEdit", "进入剪辑台"),
    ]:
        page.keyboard.press("Escape")
        page.wait_for_timeout(200)
        page.locator("button[aria-label='添加节点']").click()
        page.wait_for_timeout(300)
        page.get_by_text(label, exact=True).click()
        page.wait_for_timeout(400)
        check(f"create:{label}", page.locator(kind_cls).count() == 1)

    # 2) 搜索节点 → 查 导演 → 选中 director 节点
    page.keyboard.press("Escape")
    page.wait_for_timeout(200)
    page.locator("button[aria-label='搜索节点']").click()
    page.wait_for_timeout(400)
    search = page.locator("[data-frameos-node-search]")
    check("search:opens", search.is_visible())
    search.locator("input").first.fill("导演")
    page.wait_for_timeout(400)
    results = search.locator("[class*=result], [class*=item], button")
    texts = [results.nth(i).inner_text() for i in range(results.count())]
    check(
        "search:director-listed",
        any("3D导演台" in t for t in texts),
    )
    # 点击第一条含 3D导演台 的结果
    clicked = False
    for i in range(results.count()):
        if "3D导演台" in (results.nth(i).inner_text() or ""):
            results.nth(i).click()
            clicked = True
            break
    check("search:result-clicked", clicked)
    page.wait_for_timeout(600)
    check(
        "search:director-selected",
        page.evaluate(
            "document.querySelector('.react-flow__node-director3d')?.classList.contains('selected') ?? false"
        ),
    )

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 235, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch235: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
