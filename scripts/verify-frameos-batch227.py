#!/usr/bin/env python3

"""Verify Batch 227: FrameOS image lightbox (⛶全屏查看 on content image).

Source sampling 2026-09-25: clicking ⛶ on a content image's toolbar opens a
fullscreen lightbox (`.lightbox-chrome`) — near-black overlay, centered
contain image, top-center controls [zoom-in | zoom-out | reset | divider |
download], top-right circular × close; Esc closes.

Checks:
1. content image selected → click ⛶ → lightbox opens with the node's image;
2. toolbar buttons present (放大/缩小/重置缩放/下载/关闭灯箱);
3. zoom in changes transform; Esc closes;
4. errors clean.
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
    / "liblib-frameos-batch227-2026-09-25"
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
        assert ok, f"batch227 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/frameos/canvas/demo", wait_until="domcontentloaded")
    page.wait_for_timeout(1200)

    image = page.locator(".react-flow__node-image").first
    check("boot:content-image", image.count() == 1)
    image.click(position={"x": 60, "y": 80})
    page.wait_for_timeout(400)

    # 1) 点击 ⛶ → 灯箱打开
    page.locator(
        ".frameos-floating-toolbar-new button[aria-label='全屏查看']"
    ).click()
    page.wait_for_timeout(500)
    lightbox = page.locator("[data-frameos-image-lightbox]")
    check("lightbox:opens", lightbox.is_visible())
    lb_img = lightbox.locator("img")
    check("lightbox:image-rendered", lb_img.count() == 1)
    src = lb_img.get_attribute("src") or ""
    check("lightbox:image-is-node-cover", "/images/frameos/node-image-1.png" in src)

    # 2) 控制条按钮齐全
    for label in ["放大", "缩小", "重置缩放", "下载", "关闭灯箱"]:
        check(
            f"lightbox:btn-{label}",
            lightbox.locator(f"button[aria-label='{label}']").count() == 1,
        )

    # 3) 缩放交互
    before = lb_img.get_attribute("style") or ""
    lightbox.locator("button[aria-label='放大']").click()
    page.wait_for_timeout(300)
    after = lb_img.get_attribute("style") or ""
    check("lightbox:zoom-changes", before != after and "scale(1.25)" in after)
    lightbox.locator("button[aria-label='重置缩放']").click()
    page.wait_for_timeout(300)
    check(
        "lightbox:zoom-resets",
        "scale(1)" in (lb_img.get_attribute("style") or ""),
    )

    # 4) Esc 关闭
    page.keyboard.press("Escape")
    page.wait_for_timeout(300)
    check("lightbox:esc-closes", page.locator("[data-frameos-image-lightbox]").count() == 0)

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 227, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch227: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
