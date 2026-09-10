#!/usr/bin/env python3
"""Verify Batch 337: storyboard video-column status filter and ready
play lightbox (CLONE_DECISION interactions, source sampling blocked).

- 全部 ∨ dropdown with four status options (全部/待确认/已完成/失败);
  selecting one filters the video cards and updates the filter label.
- Ready cards show a play control that opens a lightbox (<video> when
  the node has a videoUrl, otherwise a local-prototype placeholder);
  close button and backdrop click dismiss it.
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
    / "liblib-canvas-batch337-2026-09-11"
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
        assert ok, f"batch337 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto("http://localhost:4317", wait_until="networkidle")
    page.wait_for_timeout(600)

    video_id = page.evaluate(
        """() => {
        const store = window.__libtv_store.getState();
        const canvas = store.canvases.find((c) => c.id === store.activeCanvasId);
        const video = canvas.nodes.find((n) => n.type === 'video');
        return video ? video.id : null;
    }"""
    )
    check("setup:video-node", video_id is not None)

    page.get_by_role("button", name="故事板").click()
    page.wait_for_timeout(400)
    check("board:visible", page.locator("[data-storyboard-board]").is_visible())

    # ---- filter dropdown: open + four options
    filter_btn = page.locator("[data-storyboard-filter]")
    check("filter:label-all", filter_btn.inner_text().strip() == "全部")
    filter_btn.click()
    page.wait_for_timeout(250)
    menu = page.locator("[data-storyboard-filter-menu]")
    check("filter:menu-opens", menu.is_visible())
    labels = [t.split("\n")[0].strip() for t in menu.locator("[data-storyboard-filter-option]").all_inner_texts()]
    check("filter:four-options", labels == ["全部", "待确认", "已完成", "失败"])
    check(
        "filter:active-checkmark",
        "✓" in menu.locator('[data-storyboard-filter-option="all"]').inner_text(),
    )

    # ---- pending filter hides the empty default card
    menu.locator('[data-storyboard-filter-option="pending"]').click()
    page.wait_for_timeout(250)
    cards = page.locator("[data-storyboard-column='video'] [data-storyboard-card]")
    if cards.count() > 0:
        statuses = [cards.nth(i).get_attribute("data-storyboard-video-status") for i in range(cards.count())]
        check("filter:only-pending", all(s == "pending" for s in statuses))
    else:
        check("filter:empty-hint", page.get_by_text("该状态下暂无视频").is_visible())
    check("filter:label-pending", filter_btn.inner_text().strip() == "待确认")

    # ---- back to all
    filter_btn.click()
    page.wait_for_timeout(250)
    menu.locator('[data-storyboard-filter-option="all"]').click()
    page.wait_for_timeout(250)
    check("filter:label-back-all", filter_btn.inner_text().strip() == "全部")

    # ---- ready lightbox without a video source: placeholder + close
    page.evaluate(
        """(id) => window.__libtv_store.getState().updateNodeData(id, { status: 'ready', videoUrl: null })""",
        video_id,
    )
    page.wait_for_timeout(250)
    card = page.locator(f"[data-storyboard-card='{video_id}']")
    check("setup:card-ready", card.get_attribute("data-storyboard-video-status") == "ready")
    card.locator("[data-storyboard-play]").click()
    page.wait_for_timeout(300)
    lightbox = page.locator("[data-storyboard-lightbox]")
    check("lightbox:opens", lightbox.is_visible())
    check(
        "lightbox:placeholder",
        "本地原型" in lightbox.inner_text() and "无视频源" in lightbox.inner_text(),
    )
    page.locator("[data-storyboard-lightbox-close]").click()
    page.wait_for_timeout(250)
    check("lightbox:closes", lightbox.count() == 0 or not lightbox.is_visible())

    # ---- with a video source the lightbox renders a player
    page.evaluate(
        """(id) => window.__libtv_store.getState().updateNodeData(id, { videoUrl: '/videos/mock-clip.mp4' })""",
        video_id,
    )
    page.wait_for_timeout(250)
    card.locator("[data-storyboard-play]").click()
    page.wait_for_timeout(300)
    check("lightbox:player", page.locator("[data-storyboard-lightbox-player]").count() == 1)
    # backdrop click closes
    page.locator("[data-storyboard-lightbox]").click(position={"x": 20, "y": 20})
    page.wait_for_timeout(250)
    check("lightbox:backdrop-closes", page.locator("[data-storyboard-lightbox]").count() == 0)

    # Batch 337: mock-clip.mp4 为不存在的测试夹具，<video> 加载 404 为
    # 预期伪影（浏览器 404 消息不含 URL，按模式过滤）。
    product_errors = [e for e in errors if "404 (Not Found)" not in e]
    check("errors:empty", not product_errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 337, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        try:
            audit["results"].append(run_desktop(page))
        except AssertionError:
            audit["results"].append({"checks": ["__failed__"], "errors_hint": True})
            raise
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch337: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
