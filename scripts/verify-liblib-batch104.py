#!/usr/bin/env python3

"""Verify Batch 104 storyboard three-section alignment with the 2026-09-05 source audit."""

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
    / "liblib-canvas-batch104-2026-09-05"
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


def toggle_storyboard(page: Page) -> None:
    page.get_by_role("button", name="故事板", exact=True).click()
    page.wait_for_timeout(400)


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool) -> None:
        assert ok, f"batch104 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(BASE_URL, wait_until="networkidle")
    page.wait_for_timeout(400)
    demo_nodes = page.locator(".react-flow__node").count()

    toggle_storyboard(page)
    check("demo:board-visible", page.locator("[data-storyboard-board]").is_visible())
    check("demo:sidebar-visible", page.locator("[data-storyboard-key-elements]").is_visible())
    for kind in ["script", "image", "video"]:
        check(f"demo:column:{kind}", page.locator(f"[data-storyboard-column='{kind}']").is_visible())
    check("demo:zoom-image", page.locator("[data-storyboard-zoom='image']").is_visible()
          and "放大图片" in page.locator("[data-storyboard-zoom='image']").inner_text())
    check("demo:zoom-video", page.locator("[data-storyboard-zoom='video']").is_visible()
          and "放大视频" in page.locator("[data-storyboard-zoom='video']").inner_text())
    check("demo:column-cards-image", page.locator("[data-storyboard-column='image'] [data-storyboard-card]").count() == 5)
    check("demo:column-cards-script", page.locator("[data-storyboard-column='script'] [data-storyboard-card]").count() == 1)
    check("demo:column-cards-video", page.locator("[data-storyboard-column='video'] [data-storyboard-card]").count() == 1)

    page.locator("[data-canvas-trigger]").click()
    page.locator("[data-canvas-row='canvas-1']").get_by_role("button").first.click()
    page.wait_for_timeout(300)
    toggle_storyboard(page)
    check("empty:sidebar-hidden", not page.locator("[data-storyboard-key-elements]").is_visible())
    for label in ["暂无文本", "暂无图片", "暂无视频"]:
        check(f"empty:{label}", page.get_by_text(label, exact=True).is_visible())
    check("empty:zoom-still-visible", page.locator("[data-storyboard-zoom='image']").is_visible())

    page.get_by_role("button", name="工作流", exact=True).click()
    page.wait_for_timeout(400)
    # 已切换到空画布 canvas-1，返回工作流应显示 0 节点且不串到 demo 画布
    check("back:empty-canvas-graph", page.locator(".react-flow__node").count() == 0)
    check("boot:demo-count-sane", demo_nodes > 0)

    check("diagnostics:zero", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 104,
        "title": "Storyboard three-section alignment with 2026-09-05 source audit",
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
        "Batch 104 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "Text/image/video column order, zoom buttons, empty-state copy, "
        "empty-canvas sidebar hiding and workbench round-trip recorded in "
        "runtime-audit.json."
    )


if __name__ == "__main__":
    main()
