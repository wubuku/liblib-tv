#!/usr/bin/env python3

"""Verify Batch 206: FrameOS work dropdown carries per-work project counts.

2026-09-24 source deep-sampling: the work-level breadcrumb dropdown lists
every work with a right-aligned "N 项目" count. The clone's mock works now
render counts from their projects arrays. Verifies counts on the work
dropdown rows and the project dropdown still lists the current work's
projects.
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
    / "liblib-frameos-batch206-2026-09-24"
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
        assert ok, f"batch206 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/frameos/canvas/demo", wait_until="domcontentloaded")
    page.wait_for_timeout(1200)

    # 作品下拉: 每行带 "N 项目" 计数
    page.locator("button.breadcrumb-switcher", has_text="测试作品").click()
    page.wait_for_timeout(700)
    dd_text = page.evaluate(
        """(() => {
          const anchor = [...document.querySelectorAll("*")].find(e => e.offsetParent &&
            (e.textContent || "").includes("短剧作品A"));
          if (!anchor) return null;
          let p = anchor;
          for (let i = 0; i < 6 && p.parentElement; i++) {
            p = p.parentElement;
            const r = p.getBoundingClientRect();
            if (r.width > 180 && r.height > 60) return p.textContent.replace(/\\s+/g, " ");
          }
          return null;
        })()"""
    )
    check("work:dropdown-opens", dd_text is not None)
    check(
        "work:counts-present",
        dd_text is not None and "项目" in dd_text,
    )
    page.mouse.click(1000, 500)
    page.wait_for_timeout(300)

    # 项目下拉: 当前作品的项目列表
    page.locator("button.breadcrumb-switcher", has_text="测试项目").click()
    page.wait_for_timeout(900)
    proj = page.evaluate(
        """(() => {
          const anchor = [...document.querySelectorAll("*")].find(e => e.offsetParent &&
            (e.textContent || "").includes("备用项目"));
          return anchor ? "found" : null;
        })()"""
    )
    check("project:dropdown-lists", proj == "found")
    page.mouse.click(1000, 500)
    page.wait_for_timeout(300)

    # 画布下拉节点计数 (batch 164 回归)
    page.locator("button.breadcrumb-switcher", has_text="画布 1").click()
    page.wait_for_timeout(400)
    canvas_dd = page.evaluate(
        """(() => {
          const el = [...document.querySelectorAll("*")].find(e => e.offsetParent &&
            (e.textContent || "").replace(/\\s+/g, "").startsWith("画布") &&
            e.textContent.includes("节点"));
          return el ? el.textContent.replace(/\\s+/g, " ") : null;
        })()"""
    )
    check("canvas:node-count", canvas_dd is not None and "节点" in canvas_dd)
    page.mouse.click(1000, 500)
    page.wait_for_timeout(300)

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 206, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch206: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
