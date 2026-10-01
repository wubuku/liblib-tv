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

from frameos_verify_common import attach_errors, marquee_select


ROOT = Path(__file__).resolve().parents[1]
BASE_URL = os.environ.get("LIBLIB_BASE_URL", "http://localhost:4317")
AUDIT_PATH = (
    ROOT
    / "docs"
    / "research"
    / "liblib-frameos-batch251-2026-09-27"
    / "runtime-audit.json"
)



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

    # ── 3b. 批量连线端口 (Batch 261 源站采样: 选中分组右缘 24px 圆形端口) ──
    port = page.evaluate(
        """(() => {
          const p = document.querySelector('.frameos-group-batch-connect-port');
          if (!p) return null;
          const cs = getComputedStyle(p);
          const r = p.getBoundingClientRect();
          const grpR = document.querySelector('[data-frameos-group]')?.getBoundingClientRect();
          return {
            visible: p.offsetParent !== null,
            size: { w: Math.round(r.width), h: Math.round(r.height) },
            bg: cs.backgroundColor,
            border: cs.borderColor,
            radius: cs.borderRadius,
            verticallyCentered: grpR ? Math.abs((r.y + r.height / 2) - (grpR.y + grpR.height / 2)) < 3 : false,
            rightOverlap: grpR ? Math.abs((r.right - grpR.right) - 12) < 3 : false,
          };
        })()"""
    )
    check("port:exists-visible", port and port["visible"])
    check("port:24px-circle", port and port["size"]["w"] == 24 and port["size"]["h"] == 24 and port["radius"] == "50%")
    check("port:style", port and "48, 54, 66" in port["bg"] and "255, 255, 255" in port["border"])
    check("port:right-edge-centered", port and port["verticallyCentered"] and port["rightOverlap"])
    page.locator("button[aria-label='批量连线']").click()
    page.wait_for_timeout(400)
    # Batch 357: 此前这一条断言的是 `page.get_by_text("批量连线 (mock)")` ——
    # 断的是**mock 占位符本身**, 不是源站行为: 源站的点击效果从未采样, 所以这里
    # 一直是个 mock。Batch 357 把这条谎报换成了 warning「批量连线暂不可用」。
    #
    # 与 batch170 对照（那一条本批也被我推翻过）: batch170 断的是
    # BEHAVIORS.md:33 里**采样到的启用态**, 属源站事实, 所以该改的是我的代码;
    # 这一条断的只是占位文案, 属该跟着修的断言。
    #
    # 不去钉死新的具体文案 —— 只钉两件真正要保的性质:
    #   ① 点了有反馈（圆点没变成死的）;
    #   ② 那条反馈**不是绿色成功**（不谎称已连线）。
    toasts = page.locator("[data-frameos-toast]")
    n_toasts = toasts.count()
    check("port:click-gives-feedback", n_toasts > 0)
    check(
        "port:click-not-success-claim",
        n_toasts > 0
        and all(
            toasts.nth(i).get_attribute("data-frameos-toast-variant") != "success"
            for i in range(n_toasts)
        ),
    )
    page.wait_for_timeout(2600)

    # ── 3c. 组重命名 (Batch 262 源站采样: 双击标签 → 内联 input → Enter) ──
    # (标签可能被其他节点卡片遮挡, 用页面内派发 dblclick)
    page.evaluate(
        """(() => {
          const label = document.querySelector('.frameos-canvas-group-name');
          const r = label.getBoundingClientRect();
          const x = r.x + r.width / 2, y = r.y + r.height / 2;
          const opt = { bubbles: true, cancelable: true, view: window };
          label.dispatchEvent(new MouseEvent('dblclick', { ...opt, clientX: x, clientY: y, button: 0 }));
        })()"""
    )
    page.wait_for_timeout(300)
    rename_input = page.locator(".frameos-group-rename-input")
    check("rename:input-appears", rename_input.count() == 1)
    rename_input.fill("探测组A")
    rename_input.press("Enter")
    page.wait_for_timeout(400)
    name_after = page.evaluate(
        "document.querySelector('.frameos-canvas-group-name')?.textContent"
    )
    check("rename:committed", name_after == "探测组A")

    # ── 3d. 分组右键菜单 (Batch 262 源站采样: 复制⌘C / 创建副本⌘D / 删除⌫) ──
    page.locator("[data-frameos-group]").click(button="right")
    page.wait_for_timeout(400)
    ctx_menu = page.locator("[data-frameos-context-menu]")
    check("ctx:menu-opens", ctx_menu.is_visible())
    for label in ["复制", "创建副本", "删除"]:
        check(
            f"ctx:item-{label}",
            ctx_menu.locator(f"[data-frameos-context-item='{label}']").count() == 1,
        )
    page.mouse.click(10, 10)  # 点击遮罩关闭右键菜单 (Escape 会触发页面级取消选中)
    page.wait_for_timeout(300)
    # 重新选中分组 (后续调色板/排列检查需要展开工具条)
    page.evaluate(
        """(() => {
          const g = document.querySelector('[data-frameos-group]');
          g.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true, cancelable: true, pointerId: 99, pointerType: 'mouse', isPrimary: true, clientX: 200, clientY: 300, button: 0, buttons: 1, view: window }));
          g.dispatchEvent(new PointerEvent('pointerup', { bubbles: true, cancelable: true, pointerId: 99, pointerType: 'mouse', isPrimary: true, clientX: 200, clientY: 300, button: 0, buttons: 0, view: window }));
        })()"""
    )
    page.wait_for_timeout(400)

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

    # ── 8. 双分组场景 (Batch 272 加固: 编号 组1/组2、独立选中、各自解组) ──
    page.evaluate(
        """(() => {
          const s = window.__frameos_store.getState();
          const idsA = s.nodes.slice(0, 2).map((n) => n.id);
          const idsB = s.nodes.slice(2, 4).map((n) => n.id);
          s.createGroup(idsA);
          s.createGroup(idsB);
        })()"""
    )
    page.wait_for_timeout(500)
    two = page.evaluate(
        """(() => {
          const s = window.__frameos_store.getState();
          const els = [...document.querySelectorAll('[data-frameos-group]')];
          return {
            groupCount: s.groups.length,
            names: s.groups.map((g) => g.name),
            elCount: els.length,
            selectedId: s.selectedGroupId,
          };
        })()"""
    )
    check("two:groups-created", two and two["groupCount"] == 2 and two["elCount"] == 2)
    check("two:numbered-组1-组2", two and two["names"][0] == "组1" and two["names"][1] == "组2")
    # 切换选中到第一组
    page.evaluate(
        """(() => { const s = window.__frameos_store.getState(); s.selectGroup(s.groups[0].id); })()"""
    )
    page.wait_for_timeout(300)
    switched = page.evaluate(
        """(() => {
          const s = window.__frameos_store.getState();
          return { selected: s.selectedGroupId === s.groups[0].id, selectedCls: document.querySelector('[data-frameos-group]')?.className.includes('is-selected') };
        })()"""
    )
    check("two:select-switches", switched and switched["selected"] and switched["selectedCls"])
    page.evaluate(
        """(() => { const s = window.__frameos_store.getState(); s.groups.forEach((g) => s.ungroup(g.id)); })()"""
    )
    page.wait_for_timeout(400)
    cleared = page.evaluate(
        """(() => {
          const s = window.__frameos_store.getState();
          return { groups: s.groups.length, els: document.querySelectorAll('[data-frameos-group]').length };
        })()"""
    )
    check("two:all-ungrouped", cleared and cleared["groups"] == 0 and cleared["els"] == 0)

    if errors:
        raise AssertionError(f"batch251 console/page errors: {errors[:3]}")
    result["checks"].append("errors:empty")
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
