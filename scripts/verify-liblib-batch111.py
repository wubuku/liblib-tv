#!/usr/bin/env python3

"""Verify Batch 111 character library modal alignment with the 2026-09-05 sampling."""

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
    / "liblib-canvas-batch111-2026-09-05"
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
        assert ok, f"batch111 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(BASE_URL, wait_until="networkidle")
    page.wait_for_timeout(400)

    page.get_by_role("button", name="角色库").click()
    modal = page.locator('[data-liblib-overlay="primary:character"]')
    assert modal.is_visible()

    rect = modal.evaluate("(el) => { const r = el.getBoundingClientRect(); return { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) }; }")
    check("shell:width", abs(rect["w"] - 1304) <= 8)
    check("shell:height", abs(rect["h"] - 731) <= 8)
    check("shell:x", abs(rect["x"] - 68) <= 8)

    check("detail:title", modal.get_by_text("甜妹/清新少女", exact=True).first.is_visible())
    for tag in ["女主", "女", "现代", "青年", "温柔"]:
        check(f"tags:sweet:{tag}", modal.get_by_text(tag, exact=True).count() >= 1)
    for label in ["角色立绘", "脸部近景", "表情参考", "三视图"]:
        check(f"detail:label:{label}", modal.locator(f'img[alt="{label}"]').count() >= 1)
    check(
        "detail:description",
        "详见角色全身图、面部特写、表情九宫格与人物呈现板" in modal.inner_text(),
    )
    check("apply:visible", modal.get_by_text("应用至画布", exact=True).is_visible())
    check("strip:filter", modal.get_by_text("角色筛选", exact=True).is_visible())
    check("strip:recent", modal.get_by_text("最近使用", exact=True).is_visible())

    modal.get_by_role("button", name="close", exact=True).click()
    page.wait_for_timeout(200)
    check("close:works", not modal.is_visible())

    check("diagnostics:zero", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 111,
        "title": "Character library modal geometry and detail tags alignment",
        "evidence": "docs/research/liblib-live-2026-09-05/README.md",
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
        "Batch 111 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "Modal shell 1304x731@68, detail labels, sampled tag set, description "
        "template, apply button and close aria recorded in runtime-audit.json."
    )


if __name__ == "__main__":
    main()
