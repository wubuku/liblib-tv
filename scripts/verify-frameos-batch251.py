#!/usr/bin/env python3

"""Verify Batch 251: canvas group (成组) full behavior.

Batch 251 implements the sampled frameos.cn grouping (2026-09-27,
docs/research/liblib-frameos-batch251-2026-09-27/GROUP_OBSERVATIONS.md):
- marquee ≥2 nodes → 成组 creates a flow-coords overlay group (组1) with
  28px padding around member bbox, nodes deselected;
- selected group toolbar: 切换背景色/排列方式 | 整组执行 存为模板 解组 批量下载
  (批量下载 title = 打包下载 N 个文件);
- color popover 10 swatches → group bg/border color rgba(c, .16/.9);
- arrange menu 水平排列 → members one row sorted by Y, gap 40, aligned to
  group origin + 28; group box recomputed;
- group drag moves group + all members by the same delta;
- 解组 removes the group, members keep positions, toolbar hides.

Checks (desktop 1440x900):
1. marquee two nodes → multi toolbar → 成组 click creates 组1;
2. group element + label + selected-state, nodes deselected;
3. expanded toolbar buttons + 批量下载 title count;
4. color popover pick #ef4444 → rgba(239,68,68,...) on group, pop closes;
5. 水平排列 → equal member Y, x spacing = w+40, group box recomputed;
6. group drag moves group and members together;
7. 解组 removes group + toolbar, members keep positions;
8. console/page errors clean.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright

from frameos_verify_common import marquee_select


ROOT = Path(__file__).resolve().parents[1]
BASE_URL = os.environ.get("LIBLIB_BASE_URL", "http://localhost:4317")
AUDIT_PATH = (
    ROOT
    / "docs"
    / "research"
    / "liblib-frameos-batch251-2026-09-27"
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
        assert ok, f"batch251 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/frameos/canvas/demo", wait_until="domcontentloaded", timeout=90000)
    page.wait_for_timeout(1500)

    # ── 1. 框选两个节点 (同 batch229/234 几何; Batch 253 起用共享辅助) ──
    boxes, selected_ids = marquee_select(
        page, ["image-1", "image-2"], extra_exclude=[".frameos-canvas-group"]
    )
    selected = page.evaluate(
        "document.querySelectorAll('.react-flow__node.selected').length"
    )
    check("marquee:multi-selected", selected >= 2)
    selected_ids = page.evaluate(
        "window.__frameos_store.getState().nodes.filter((n) => n.selected).map((n) => n.id)"
    )
    group_tb = page.locator(".frameos-group-toolbar")
    check("multi:toolbar-opens", group_tb.is_visible())
    # 工具条水平居中于选中集合包围盒 (源站实测: 中心 = bbox 中心)
    centering = page.evaluate(
        """(() => {
          const tb = document.querySelector('.frameos-group-toolbar')?.getBoundingClientRect();
          const els = [...document.querySelectorAll('.react-flow__node.selected')].map((n) => n.getBoundingClientRect());
          if (!tb || els.length < 2) return false;
          const minX = Math.min(...els.map((r) => r.left));
          const maxX = Math.max(...els.map((r) => r.right));
          return Math.abs((tb.left + tb.width / 2) - (minX + maxX) / 2) < 3;
        })()"""
    )
    check("multi:toolbar-centered-on-bbox", centering)

    # ── 2. 成组创建 ──
    group_tb.locator("button[aria-label='成组']").click()
    page.wait_for_timeout(500)
    grp = page.evaluate(
        """(() => {
          const el = document.querySelector('[data-frameos-group]');
          if (!el) return null;
          const s = window.__frameos_store.getState();
          const g = s.groups[0];
          return {
            cls: el.className,
            name: el.querySelector('.frameos-canvas-group-name')?.textContent,
            hasHandles: el.querySelectorAll('.frameos-canvas-group-handle').length,
            storeGroups: s.groups.length,
            selectedGroupId: s.selectedGroupId,
            nodesSelected: s.nodes.filter((n) => n.selected).length,
            members: g ? g.memberIds.length : 0,
            paddingOk: g ? Math.round(g.x + g.w) >= Math.round(Math.max(...s.nodes.filter((n) => g.memberIds.includes(n.id)).map((n) => n.position.x + ((n.style && n.style.width) || 300)))) : false,
          };
        })()"""
    )
    check("group:element-created", grp is not None)
    check("group:name-组1", grp and grp["name"] == "组1")
    check("group:store-selected", grp and grp["storeGroups"] == 1 and grp["selectedGroupId"])
    check("group:handles-4-when-selected", grp and grp["hasHandles"] == 4)
    check("group:nodes-deselected", grp and grp["nodesSelected"] == 0)
    check(
        "group:members-match-selection",
        grp and grp["members"] == len(selected_ids),
    )
    check("group:label-selected-cls", grp and "is-selected" in grp["cls"])

    # ── 3. 展开工具栏 ──
    gt_group = page.locator(".frameos-group-toolbar--group")
    check("group:toolbar-switches", gt_group.is_visible())
    for label in ["切换背景色", "排列方式"]:
        check(f"group:toolbar-{label}", gt_group.locator(f"button[aria-label='{label}']").count() == 1)
    for text in ["整组执行", "存为模板", "解组", "批量下载"]:
        check(f"group:toolbar-text-{text}", gt_group.get_by_text(text, exact=True).count() >= 1)
    dl_title = page.evaluate(
        "document.querySelector(\".frameos-group-toolbar--group button[aria-label='批量下载']\")?.getAttribute('title')"
    )
    media_selected = page.evaluate(
        """window.__frameos_store.getState().nodes.filter((n) => %s.includes(n.id) && (n.data.imageUrl || n.data.audioUrl)).length"""
        % json.dumps(selected_ids)
    )
    check(
        "group:批量下载-title-count",
        dl_title == f"打包下载 {media_selected} 个文件" and media_selected >= 2,
    )

    # ── 4. 调色板 ──
    gt_group.locator("button[aria-label='切换背景色']").click()
    page.wait_for_timeout(300)
    pop = page.locator(".frameos-group-color-pop")
    check("color:popover-opens", pop.is_visible())
    check("color:swatches-10", page.evaluate("document.querySelectorAll('.frameos-group-color-pop .gt-color-swatch').length") == 10)
    check("color:default-aria", page.evaluate("document.querySelector(\".frameos-group-color-pop button[aria-label='默认色']\") !== null"))
    pop.locator("button[aria-label='背景色 #ef4444']").click()
    page.wait_for_timeout(300)
    red = page.evaluate(
        """(() => {
          const el = document.querySelector('[data-frameos-group]');
          const s = window.__frameos_store.getState();
          return {
            bg: el ? getComputedStyle(el).backgroundColor : null,
            border: el ? getComputedStyle(el).borderColor : null,
            storeColor: s.groups[0]?.color,
            popClosed: !document.querySelector('.frameos-group-color-pop'),
          };
        })()"""
    )
    check("color:bg-red", red and "239, 68, 68" in red["bg"] and "0.16" in red["bg"])
    check("color:border-red", red and "239, 68, 68" in red["border"])
    check("color:store-hex", red and red["storeColor"] == "#ef4444")
    check("color:popover-closed", red and red["popClosed"])

    page.screenshot(path=str(ROOT / "docs" / "design-references" / "frameos" / "frameos-clone-batch251-group-red-toolbar-1440.png"))

    # ── 5. 水平排列 ──
    before = page.evaluate(
        "window.__frameos_store.getState().nodes.filter((n) => window.__frameos_store.getState().groups[0].memberIds.includes(n.id)).map((n) => ({ id: n.id, x: n.position.x, y: n.position.y, w: n.style.width }))"
    )
    gt_group.locator("button[aria-label='排列方式']").click()
    page.wait_for_timeout(300)
    menu = page.locator(".frameos-group-arrange-pop")
    check("arrange:menu-opens", menu.is_visible())
    check("arrange:items-3", page.evaluate("document.querySelectorAll('.frameos-group-arrange-pop .gt-menu-item').length") == 3)
    menu.get_by_text("水平排列", exact=True).click()
    page.wait_for_timeout(400)
    after = page.evaluate(
        """(() => {
          const s = window.__frameos_store.getState();
          const g = s.groups[0];
          const members = s.nodes.filter((n) => g.memberIds.includes(n.id));
          const ys = new Set(members.map((n) => n.position.y));
          const xs = members.map((n) => n.position.x).sort((a, b) => a - b);
          const gaps = xs.slice(1).map((x, i) => x - xs[i] - (members.find((n) => n.position.x === xs[i]).style.width || 300));
          return { ys: [...ys], gaps, boxW: g.w, boxH: g.h };
        })()"""
    )
    check("arrange:horizontal-same-y", after and len(after["ys"]) == 1)
    check("arrange:horizontal-gap-40", after and all(abs(gap - 40) < 0.01 for gap in after["gaps"]))
    contentW = sum((b["w"] or 300) for b in before)
    expectedW = contentW + (len(before) - 1) * 40 + 56
    check("arrange:group-box-recomputed", after and abs(after["boxW"] - expectedW) < 1)

    # ── 6. 分组拖拽 (成员同步位移) ──
    pre = page.evaluate(
        """(() => {
          const s = window.__frameos_store.getState();
          const g = s.groups[0];
          const m = s.nodes.find((n) => g.memberIds.includes(n.id));
          return { mid: m.id, gx: g.x, gy: g.y, mx: m.position.x, my: m.position.y };
        })()"""
    )
    handle = page.locator("[data-frameos-group]").bounding_box()
    page.mouse.move(handle["x"] + 8, handle["y"] + handle["height"] / 2)
    page.mouse.down()
    page.mouse.move(handle["x"] + 58, handle["y"] + handle["height"] / 2 + 30, steps=6)
    page.mouse.up()
    page.wait_for_timeout(400)
    post = page.evaluate(
        """(() => {
          const s = window.__frameos_store.getState();
          const g = s.groups[0];
          const m = s.nodes.find((n) => g.memberIds.includes(n.id));
          return { gx: g.x, gy: g.y, mx: m.position.x, my: m.position.y };
        })()"""
    )
    dx = post["gx"] - pre["gx"]
    dy = post["gy"] - pre["gy"]
    check("drag:group-moved", abs(dx - 50) < 2 and abs(dy - 30) < 2)
    check(
        "drag:members-follow",
        abs((post["mx"] - pre["mx"]) - dx) < 0.01
        and abs((post["my"] - pre["my"]) - dy) < 0.01,
    )

    # ── 6b. 宫格排列 (Batch 252 采样对齐: 按原 Y 排序, ceil(√n) 列行优先, 间距 40) ──
    gt_group.locator("button[aria-label='排列方式']").click()
    page.wait_for_timeout(300)
    page.locator(".frameos-group-arrange-pop").get_by_text("宫格排列", exact=True).click()
    page.wait_for_timeout(500)
    grid = page.evaluate(
        """(() => {
          const s = window.__frameos_store.getState();
          const g = s.groups[0];
          const members = s.nodes.filter((n) => g.memberIds.includes(n.id));
          const rows = [...new Set(members.map((n) => n.position.y))].sort((a, b) => a - b);
          const row1 = members.filter((n) => n.position.y === rows[0]);
          const row2 = members.filter((n) => n.position.y === rows[1]);
          const gap = (a, b) => b - a;
          const xs1 = row1.map((n) => n.position.x).sort((a, b) => a - b);
          const w1 = Math.max(...row1.map((n) => n.style.width || 300));
          return {
            rowCount: rows.length,
            row1Count: row1.length,
            row2Count: row2.length,
            colGap: xs1.length > 1 ? xs1[1] - xs1[0] - (row1.find((n) => n.position.x === xs1[0]).style.width || 300) : null,
            rowPitch: rows.length > 1 ? rows[1] - rows[0] - w1 : null,
            boxW: g.w,
          };
        })()"""
    )
    check("arrange2:grid-two-rows", grid and grid["rowCount"] == 2)
    check("arrange2:grid-row-counts", grid and grid["row1Count"] == 2 and grid["row2Count"] == 1)
    check("arrange2:grid-col-gap-40", grid and grid["colGap"] is not None and abs(grid["colGap"] - 40) < 0.01)
    check("arrange2:grid-row-pitch-40", grid and grid["rowPitch"] is not None and abs(grid["rowPitch"] - 40) < 0.01)

    # ── 6c. 垂直排列 (Batch 252 源站实测: 同样按原 Y 排序, 单列, 间距 40) ──
    gt_group.locator("button[aria-label='排列方式']").click()
    page.wait_for_timeout(300)
    page.locator(".frameos-group-arrange-pop").get_by_text("垂直排列", exact=True).click()
    page.wait_for_timeout(500)
    vert = page.evaluate(
        """(() => {
          const s = window.__frameos_store.getState();
          const g = s.groups[0];
          const members = s.nodes.filter((n) => g.memberIds.includes(n.id));
          const xs = [...new Set(members.map((n) => n.position.x))];
          const ys = members.map((n) => n.position.y).sort((a, b) => a - b);
          const gaps = ys.slice(1).map((y, i) => y - ys[i] - (members.find((n) => n.position.y === ys[i]).style.height || 200));
          return {
            colCount: xs.length,
            boxW: g.w,
            maxW: Math.max(...members.map((n) => n.style.width || 300)),
            gaps,
          };
        })()"""
    )
    check("arrange2:vertical-single-column", vert and vert["colCount"] == 1)
    check(
        "arrange2:vertical-gap-40",
        vert and all(abs(gp - 40) < 0.01 for gp in vert["gaps"]) and len(vert["gaps"]) >= 2,
    )
    check("arrange2:vertical-box-w", vert and abs(vert["boxW"] - (vert["maxW"] + 56)) < 1)

    # ── 7. 解组 ──
    member_before_ungroup = page.evaluate(
        """(() => {
          const s = window.__frameos_store.getState();
          const m = s.nodes.find((n) => n.id === %s);
          return { x: m.position.x, y: m.position.y };
        })()"""
        % json.dumps(pre["mid"])
    )
    gt_group.get_by_text("解组", exact=True).click()
    page.wait_for_timeout(400)
    ungrouped = page.evaluate(
        """(() => {
          const s = window.__frameos_store.getState();
          return {
            groups: s.groups.length,
            selectedGroupId: s.selectedGroupId,
            elGone: !document.querySelector('[data-frameos-group]'),
            tbGone: !document.querySelector('.frameos-group-toolbar'),
          };
        })()"""
    )
    check("ungroup:store-empty", ungrouped and ungrouped["groups"] == 0 and not ungrouped["selectedGroupId"])
    check("ungroup:element-gone", ungrouped and ungrouped["elGone"])
    check("ungroup:toolbar-hides", ungrouped and ungrouped["tbGone"])
    kept = page.evaluate(
        "window.__frameos_store.getState().nodes.find((n) => n.id === %s).position"
        % json.dumps(pre["mid"])
    )
    check("ungroup:members-keep-positions", kept and abs(kept["x"] - member_before_ungroup["x"]) < 0.01 and abs(kept["y"] - member_before_ungroup["y"]) < 0.01)

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 251, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch251: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
