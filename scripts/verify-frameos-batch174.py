#!/usr/bin/env python3

"""Verify Batch 174: FrameOS connection creation is undoable.

Source evidence (docs/user-manual/frameos-canvas SOURCE_OBSERVATIONS §13.1):
the source undo is a global stack covering creations and deletions; the
clone's addEdge was a bare set so creating a connection could not be
undone (drift found in Batch 174 planning). addEdge now pushes undo
history. Verifies via real handle-drag connection:

1. drag text right handle -> image left handle creates an edge;
2. ⌘Z removes the created edge;
3. ⌘⇧Z restores it;
4. batch159 reference-chip regression stays green.
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
    / "liblib-frameos-batch174-2026-09-24"
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
        assert ok, f"batch174 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/frameos/canvas/demo", wait_until="domcontentloaded")
    page.wait_for_timeout(1200)

    edges_before = page.evaluate("window.__frameos_store.getState().edges.length")

    # 用 store 造一个无连线的图片节点, 避免依赖既有边
    page.evaluate(
        """(() => {
          const s = window.__frameos_store.getState();
          s.addNode("image", { panX: 0, panY: 0, zoom: 1, viewportWidth: 1440, viewportHeight: 900 });
        })()"""
    )
    page.wait_for_timeout(400)
    # Batch 225: 内容图片节点仅右 handle (2026-09-25 源站实测), 清空内容恢复左 handle 供连线
    page.evaluate(
        """(() => {
          const s = window.__frameos_store.getState();
          const img = [...s.nodes].reverse().find((n) => n.type === "image");
          s.updateNodeData(img.id, { imageUrl: null });
        })()"""
    )
    page.wait_for_timeout(300)

    # 找文本节点的右 handle 和新图片节点的左 handle, 真实拖拽连线
    handles = page.evaluate(
        """(() => {
          const s = window.__frameos_store.getState();
          const text = s.nodes.find((n) => n.type === "text");
          const img = [...s.nodes].reverse().find((n) => n.type === "image");
          const tr = document.querySelector(`.react-flow__node[data-id="${text.id}"] .react-flow__handle-right`);
          const il = document.querySelector(`.react-flow__node[data-id="${img.id}"] .react-flow__handle-left`);
          if (!tr || !il) return null;
          const a = tr.getBoundingClientRect();
          const b = il.getBoundingClientRect();
          return {
            from: { x: a.x + a.width / 2, y: a.y + a.height / 2 },
            to: { x: b.x + b.width / 2, y: b.y + b.height / 2 },
          };
        })()"""
    )
    check("connect:handles-found", handles is not None)
    if not handles:
        raise RuntimeError("handles missing")

    page.mouse.move(handles["from"]["x"], handles["from"]["y"])
    page.mouse.down()
    steps = 8
    for i in range(1, steps + 1):
        x = handles["from"]["x"] + (handles["to"]["x"] - handles["from"]["x"]) * i / steps
        y = handles["from"]["y"] + (handles["to"]["y"] - handles["from"]["y"]) * i / steps
        page.mouse.move(x, y)
    page.mouse.up()
    page.wait_for_timeout(500)

    edges_created = page.evaluate(
        "window.__frameos_store.getState().edges.length"
    )
    check("connect:edge-created", edges_created == edges_before + 1)

    # ⌘Z 撤销连线创建
    page.keyboard.press("Meta+z")
    page.wait_for_timeout(400)
    check(
        "undo:connection-removed",
        page.evaluate("window.__frameos_store.getState().edges.length") == edges_before,
    )

    # ⌘⇧Z 重做恢复连线
    page.keyboard.press("Meta+Shift+z")
    page.wait_for_timeout(400)
    check(
        "redo:connection-restored",
        page.evaluate("window.__frameos_store.getState().edges.length") == edges_created,
    )

    # 回归: 引用芯片 (batch159) 依旧工作 — Batch 225 起面板仅空媒体节点显示,
    # 先清空 image-1 内容再选中
    page.evaluate(
        "window.__frameos_store.getState().updateNodeData('image-1', { imageUrl: null })"
    )
    page.wait_for_timeout(300)
    image_node = page.locator(".react-flow__node-image").first
    image_node.click(position={"x": 60, "y": 30})
    page.wait_for_timeout(300)
    check(
        "regression:ref-chips",
        page.locator("[data-frameos-ref-chip]").count() >= 1,
    )

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 174, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch174: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
