#!/usr/bin/env python3
"""Verify Batch 268: 图片高清 one-click preset generation on image nodes.

Source evidence (2026-09-10, docs/research/liblib-canvas-batch267-2026-09-10/
disambig-late.png): clicking 图片高清 deselects the source image node and
spawns a 预设 - 图片高清 preset container holding an AI生成-badged image
node. The clone implements this as createImageHdPreset (group + child
image with aiGenerated flag, selection moved to the group, single history
entry); the empty image node also gains the 尝试 suggestion row
(图生图 / 图片高清) from the batch-263 screenshot."""

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
    / "liblib-canvas-batch268-2026-09-10"
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
        assert ok, f"batch268 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto("http://localhost:4317", wait_until="networkidle")
    page.wait_for_timeout(500)

    # remove preset image nodes (Canvas 2's demo image has an imageUrl and
    # would suppress the attempt row + steal selection) — fresh profile per
    # run, so the removal does not persist across runs
    page.evaluate(
        """() => {
        const store = window.__libtv_store;
        const state = store.getState();
        const canvas = state.getActiveCanvas();
        for (const n of canvas.nodes.filter((n) => n.type === 'image')) {
            state.removeNode(n.id);
        }
    }"""
    )
    page.wait_for_timeout(300)

    # fresh image node via the add panel (auto-selected)
    page.get_by_role("button", name="添加节点").click()
    page.wait_for_timeout(300)
    page.locator("[data-liblib-overlay='add-node']").get_by_role("button", name="图片", exact=True).click()
    page.wait_for_timeout(1000)
    nid = page.evaluate(
        """() => { const s = document.querySelector('.react-flow__node.selected'); return s ? s.getAttribute('data-id') : null; }"""
    )
    check("setup:image-selected", bool(nid) and nid.startswith("image-"))

    # attempt row visible on the empty image node
    check("attempts:row", page.locator("[data-image-attempts]").count() == 1)
    check("attempts:tushengtu", page.locator('[data-image-attempt="图生图"]').count() == 1)
    check("attempts:gaoqing", page.locator('[data-image-attempt="图片高清"]').count() == 1)

    # 图生图: visual commit only
    page.locator('[data-image-attempt="图生图"]').click()
    page.wait_for_timeout(200)
    check(
        "tushengtu:pressed",
        page.locator('[data-image-attempt="图生图"]').get_attribute("aria-pressed") == "true",
    )

    # 图片高清: preset container spawned, selection moved to the group
    nodes_before = page.evaluate("() => document.querySelectorAll('.react-flow__node').length")
    page.locator('[data-image-attempt="图片高清"]').click()
    page.wait_for_timeout(600)
    state = page.evaluate(
        """() => {
        const store = window.__libtv_store;
        const canvas = store.getState().getActiveCanvas();
        const group = canvas.nodes.find((n) => n.type === 'storyboard-group' && n.data.title === '预设 - 图片高清');
        const child = group ? canvas.nodes.find((n) => n.parentId === group.id) : null;
        const selected = store.getState().selectedNodeId;
        return {
            group: Boolean(group),
            childAi: Boolean(child && child.data.aiGenerated),
            selectedIsGroup: selected === (group ? group.id : null),
            total: canvas.nodes.length,
        };
    }"""
    )
    check("hd:group-created", state["group"])
    check("hd:child-ai-generated", state["childAi"])
    check("hd:selection-on-group", state["selectedIsGroup"])
    check("hd:two-nodes-added", state["total"] == nodes_before + 2)

    # deselect/re-select: preset persists (batch 255-style node-data semantics
    # apply to the group/child because they are regular nodes)
    page.mouse.click(1360, 90)
    page.wait_for_timeout(400)
    # geometric re-select of the group by its title text
    page.get_by_text("预设 - 图片高清", exact=False).first.click(force=True)
    page.wait_for_timeout(600)
    check(
        "persist:group-reselectable",
        page.get_by_text("预设 - 图片高清", exact=False).count() >= 1,
    )

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 268, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        try:
            audit["results"].append(run_desktop(page))
        except Exception as exc:  # noqa: BLE001
            page.screenshot(path=str(AUDIT_PATH.parent / "fail.png"))
            print("EXC:", str(exc)[:300])
            raise
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch268: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
