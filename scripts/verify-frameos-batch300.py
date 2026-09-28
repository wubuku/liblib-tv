#!/usr/bin/env python3

"""Verify Batch 300: two-dimensional spec popover (分辨率 + 宽高比).

Source-sampled 2026-09-28: the empty-node prompt panel spec control opens a
popover with 分辨率 [1K, 2K] and 宽高比 [16:9, 9:16, 21:9, 4:3, 3:4, 1:1];
the value displays combined as "2K · 16:9".

Checks (desktop 1440x900):
1. new empty image node → panel shows spec value button "2K · 16:9";
2. click opens popover with 分辨率 1K/2K and six aspects;
3. pick 1K + 9:16 → value "1K · 9:16";
4. popover closes on outside click;
5. console/page errors clean.
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
    / "liblib-frameos-batch300-2026-09-28"
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
        assert ok, f"batch300 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/frameos/canvas/demo", wait_until="domcontentloaded", timeout=90000)
    page.wait_for_timeout(1500)

    # create an empty image node (auto-selected → prompt panel opens)
    page.evaluate("""(() => { window.__frameos_store.getState().addNode('image'); })()""")
    page.wait_for_timeout(800)

    value_btn = page.locator("button[data-frameos-spec-value]")
    check("spec:value-btn-2K-16:9", value_btn.count() == 1 and (value_btn.text_content() or "").strip().startswith("2K · 16:9"))

    value_btn.click()
    page.wait_for_timeout(400)
    pop = page.locator("[data-frameos-spec-pop]")
    check("spec:popover-opens", pop.is_visible())
    check("spec:res-1K-2K", page.evaluate(
        """(() => {
          const pop = document.querySelector('[data-frameos-spec-pop]');
          const btns = [...pop.querySelectorAll('button')].map((b) => b.textContent.trim());
          return btns.includes('1K') && btns.includes('2K');
        })()"""
    ))
    for aspect in ["16:9", "9:16", "21:9", "4:3", "3:4", "1:1"]:
        check(f"spec:aspect-{aspect}", page.evaluate(
            f"""(() => {{
              const pop = document.querySelector('[data-frameos-spec-pop]');
              return [...pop.querySelectorAll('button')].some((b) => b.textContent.trim() === '{aspect}');
            }})()"""
        ))

    # pick 1K + 9:16
    pop.locator("button", has_text="1K").first.click()
    page.wait_for_timeout(200)
    pop.locator("button", has_text="9:16").first.click()
    page.wait_for_timeout(300)
    val = page.evaluate(
        """(document.querySelector('button[data-frameos-spec-value]')?.getAttribute('data-frameos-spec-value'))"""
    )
    check("spec:value-1K-9:16", val == "1K · 9:16")

    # outside click closes popover
    page.mouse.click(400, 300)
    page.wait_for_timeout(300)
    check("spec:popover-closes", page.evaluate("!document.querySelector('[data-frameos-spec-pop]')"))

    if errors:
        raise AssertionError(f"batch300 console/page errors: {errors[:3]}")
    result["checks"].append("errors:empty")
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 300, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch300: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
