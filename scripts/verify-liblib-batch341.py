#!/usr/bin/env python3
"""Verify Batch 341: workbench toolbar chrome matches the 2026-09-11
source aria-label evidence (docs/research/liblib-canvas-batch341-2026-09-11/).

Source evidence (2026-09-11 live aria-label dump of the workbench):
- bottom-left cluster: 资产管理, 整理画布，Option+Shift+F, 切换小地图,
  隐藏节点连线, 网格吸附, 缩放选项
- center cluster: 添加节点, 移动, 打开工具箱, 素材库, 角色库,
  生成历史, 快捷键, 教程
Batch 341 fixes two drifted clone labels: 显示缩略图 → 切换小地图,
吸附到网格 → 网格吸附.
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
    / "liblib-canvas-batch341-2026-09-11"
    / "runtime-audit.json"
)

LEFT_CLUSTER = [
    "资产管理",
    "整理画布，Option+Shift+F",
    "切换小地图",
    "隐藏节点连线",
    "网格吸附",
    "缩放选项",
]

CENTER_CLUSTER = [
    "添加节点",
    "移动",
    "打开工具箱",
    "素材库",
    "角色库",
    "生成历史",
    "快捷键",
    "教程",
]


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
        assert ok, f"batch341 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto("http://localhost:4317", wait_until="networkidle")
    page.wait_for_timeout(600)

    def label_x(name: str) -> float | None:
        button = page.locator(f'button[aria-label="{name}"]')
        if button.count() == 0:
            return None
        box = button.first.bounding_box()
        return box["x"] if box else None

    # ---- left cluster labels exist with source-exact text
    for label in LEFT_CLUSTER:
        check(f"left:{label}", label_x(label) is not None)

    # ---- center cluster labels exist
    for label in CENTER_CLUSTER:
        check(f"center:{label}", label_x(label) is not None)

    # ---- drifted labels are gone
    check("drift:显示缩略图-gone", page.locator('button[aria-label="显示缩略图"]').count() == 0)
    check("drift:吸附到网格-gone", page.locator('button[aria-label="吸附到网格"]').count() == 0)

    # ---- left cluster ordering matches the source dump
    xs = [label_x(label) for label in LEFT_CLUSTER]
    check("left:order", all(xs[i] is not None and xs[i + 1] is not None and xs[i] < xs[i + 1] for i in range(len(xs) - 1)))

    # ---- zoom control is the percent label inside the left cluster tail
    zoom = page.locator('button[aria-label="缩放选项"]')
    check("zoom:percent-text", "%" in zoom.inner_text())

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 341, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch341: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
