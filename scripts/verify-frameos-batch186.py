#!/usr/bin/env python3

"""Verify Batch 186: FrameOS vertical organize layers upstream on top.

按连线纵向 (layer nodes along connections, top to bottom): with the demo
graph text-1 -> image-1, switching the organize mode to 按连线纵向 and
running organize must place the text node ABOVE the image node it feeds
(smaller y). Complements Batch 185 (horizontal mode).
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
    / "liblib-frameos-batch186-2026-09-24"
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
        assert ok, f"batch186 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/frameos/canvas/demo", wait_until="domcontentloaded", timeout=90000)
    page.wait_for_timeout(1200)

    # 把 image-1 移到上方远处 (布置), 记录坐标
    page.evaluate(
        """(() => {
          const s = window.__frameos_store.getState();
          s.setNodes(s.nodes.map((n) => n.id === "image-1"
            ? { ...n, position: { x: n.position.x, y: 2000 } }
            : n));
        })()"""
    )
    page.wait_for_timeout(300)

    # 切换整理方式为 按连线纵向
    page.locator("button[aria-label='选择整理方式']").click()
    page.wait_for_timeout(300)
    opt = page.get_by_text("按连线纵向", exact=True)
    check("menu:vertical-option", opt.is_visible())
    opt.click()
    page.wait_for_timeout(300)

    # 一键整理 → image-1 拉回纵向分层 (y 小于 text-1)
    page.locator("button[aria-label='一键整理 · 网格整理']").click()
    page.wait_for_timeout(1000)
    ys = page.evaluate(
        """(() => {
          const s = window.__frameos_store.getState();
          const by = {};
          for (const n of s.nodes) by[n.id] = n.position.y;
          return { text: by["text-1"], image: by["image-1"] };
        })()"""
    )
    check(
        "organize:vertical-layers-text-above-image",
        ys["text"] is not None and ys["image"] is not None and ys["text"] < ys["image"],
    )

    # 撤销可回退整理 (覆盖验证见 batch 175 grid 流程)

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 186, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch186: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
