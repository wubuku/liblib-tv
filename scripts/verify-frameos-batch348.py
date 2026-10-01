#!/usr/bin/env python3

"""Verify Batch 348: 「双击空白处添加节点」是半成品接线 —— 事件接了，菜单没渲染。

缺陷（克隆侧，且修正了 Batch 346 的一个判断）:
`page.tsx:196-206` 里 Batch 168 早就把**事件半边**接好了，注释明写
「双击空白处打开「选择节点类型」菜单 (Batch 168)」：监听 `.react-flow__pane` 的
dblclick、跳过节点上的双击、记录坐标到 `paneMenuAt`。

但 `paneMenuAt` **store 外零引用** —— 没有任何组件读它。于是双击空白处:
状态被写进虚空，**什么都不会出现**，而且 **Esc 也清不掉这个状态**。

实测 (probe-frameos-batch348-dblclick-addnode.py, 修复前):
    [双击后] paneMenuAt={'x':140,'y':140}  出现「选择节点类型」字样=False
    [Esc 后] paneMenuAt={'x':140,'y':140}      ← 关不掉
    HALF_WIRED: true

**同时修正 Batch 346 的判断**：当时记录「承诺只说添加节点、没说添加哪一种，
无法实现」并记为保真度差距。但 Batch 168 的设计**已经回答了这个问题** ——
它要的是一个「选择节点类型」**菜单**，由用户选。所以这不是「无法实现」，
而是「做了一半」：事件半边在，渲染半边缺。

修复:
1. 新增 `FrameosPaneAddNodeMenu` —— 缺失的渲染半边，类型列表直接复用工具条的
   `NODE_TYPES`（同一个「有哪些节点类型」的事实只该有一个出处）；
2. `AddNodeOpts` 增加可选 `position`（**画布流坐标**）—— 此前 `addNode` 只能放
   视口中央或随机位置，用户在哪儿双击就必须在哪儿出现；
3. Esc 多级退出链补上 `paneMenuAt`（此前这个状态关不掉）。

断言:
1. 双击空白 → 菜单渲染;
2. 菜单标题是「选择节点类型」;
3. 菜单列出与工具条同一份类型表（文本/图片/视频/音频/3D模型/3D导演台/视频剪辑台）;
4. 选「文本」→ 节点数**恰好 +1**;
5. 新节点落在**双击的那一点**上（屏幕中心与双击点重合，容差半个节点）;
6. 选完菜单关闭、`paneMenuAt` 清空;
7. **Esc** 能关掉菜单;
8. 点遮罩能关掉菜单;
9. 双击**节点**不弹菜单（不回归：节点双击是聚焦/编辑）;
10. 新节点**可撤销**（与全 app 语义一致）;
11. `paneMenuAt` 不再是死状态（菜单随它出现/消失）;
12. 诊断零错误。
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
BASE_URL = os.environ.get("LIBLIB_BASE_URL", "http://localhost:4317")
AUDIT_PATH = (
    ROOT
    / "docs"
    / "research"
    / "liblib-frameos-batch348-2026-10-01"
    / "runtime-audit.json"
)
sys.path.insert(0, str(ROOT / "scripts"))
from frameos_verify_common import attach_errors, goto_clean_canvas  # noqa: E402

EMPTY_POINT_JS = """
() => {
  const rects = Array.from(document.querySelectorAll('.react-flow__node'))
    .map((n) => n.getBoundingClientRect());
  for (let y = 140; y < window.innerHeight - 140; y += 40) {
    for (let x = 140; x < window.innerWidth - 140; x += 40) {
      const hit = rects.some(
        (r) => x >= r.left && x <= r.right && y >= r.top && y <= r.bottom
      );
      if (!hit) return { x, y };
    }
  }
  return null;
}
"""

PICKED_JS = """
(pt) => {
  const s = window.__frameos_store.getState();
  const last = s.nodes[s.nodes.length - 1];
  const el = document.querySelector(`.react-flow__node[data-id="${last.id}"]`);
  const r = el ? el.getBoundingClientRect() : null;
  return {
    nodeCount: s.nodes.length,
    newId: last.id,
    type: last.type,
    screenCenter: r ? { x: r.left + r.width / 2, y: r.top + r.height / 2 } : null,
    clickedAt: pt,
    menuInDom: document.querySelectorAll('[data-frameos-pane-addnode-menu]').length,
    paneMenuAt: s.paneMenuAt,
  };
}
"""


def open_menu(page: Page) -> None:
    page.mouse.dblclick(*_pt(page))
    page.wait_for_timeout(600)


def _pt(page: Page) -> tuple[int, int]:
    pt = page.evaluate(EMPTY_POINT_JS)
    assert pt, "找不到画布空白点"
    return pt["x"], pt["y"]


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool, detail: str = "") -> None:
        assert ok, f"batch348 check failed: {name} {detail}".strip()
        result["checks"].append(name)

    errors = attach_errors(page)
    goto_clean_canvas(page, BASE_URL)

    # ── 1~3 双击空白 → 菜单 ──
    pt = page.evaluate(EMPTY_POINT_JS)
    result["click_point"] = pt
    check("menu:empty-point-found", pt is not None, "找不到空白点")
    page.mouse.dblclick(pt["x"], pt["y"])
    page.wait_for_timeout(700)
    menu = page.locator("[data-frameos-pane-addnode-menu]")
    check("menu:renders-on-dblclick", menu.count() == 1,
          f"count={menu.count()}")
    check("menu:title", "选择节点类型" in menu.first.inner_text(),
          f"text={menu.first.inner_text()[:40]!r}")
    types = page.evaluate(
        """() => Array.from(
             document.querySelectorAll('[data-frameos-pane-addnode-type]'))
           .map((el) => el.getAttribute('data-frameos-pane-addnode-type'))"""
    )
    result["menu_types"] = types
    for t in ("text", "image", "video", "audio", "model3d", "director3d", "videoEdit"):
        check(f"menu:has-type:{t}", t in types, f"types={types}")
    # 状态确实被消费了(不再死状态)
    check("state:paneMenuAt-consumed",
          page.evaluate("() => window.__frameos_store.getState().paneMenuAt") is not None,
          "paneMenuAt 没被设置 —— 事件半边也坏了")

    # ── 4~6 选一个类型 ──
    n_before = page.evaluate(
        "() => window.__frameos_store.getState().nodes.length"
    )
    page.locator('[data-frameos-pane-addnode-type="text"]').first.click()
    page.wait_for_timeout(700)
    picked = page.evaluate(PICKED_JS, pt)
    result["picked"] = picked
    check("pick:node-count-plus-one", picked["nodeCount"] == n_before + 1,
          f"{n_before} → {picked['nodeCount']}")
    check("pick:type-is-text", picked["type"] == "text", f"type={picked['type']}")
    sc = picked["screenCenter"]
    check("pick:lands-at-double-click-point",
          sc is not None
          and abs(sc["x"] - pt["x"]) <= 160 and abs(sc["y"] - pt["y"]) <= 110,
          f"node center={sc} double-click={pt}")
    check("pick:menu-closed", picked["menuInDom"] == 0 and picked["paneMenuAt"] is None,
          f"menuInDom={picked['menuInDom']} paneMenuAt={picked['paneMenuAt']}")

    # ── 7 Esc 能关 ──
    pt2 = page.evaluate(EMPTY_POINT_JS)
    page.mouse.dblclick(pt2["x"], pt2["y"])
    page.wait_for_timeout(600)
    check("esc:menu-opened-first",
          page.locator("[data-frameos-pane-addnode-menu]").count() == 1, "菜单没开")
    page.keyboard.press("Escape")
    page.wait_for_timeout(400)
    check("esc:closes-menu",
          page.locator("[data-frameos-pane-addnode-menu]").count() == 0, "Esc 关不掉菜单")
    check("esc:clears-state",
          page.evaluate("() => window.__frameos_store.getState().paneMenuAt") is None,
          "Esc 后 paneMenuAt 仍残留(修复前正是这个症状)")

    # ── 8 遮罩能关 ──
    pt3 = page.evaluate(EMPTY_POINT_JS)
    page.mouse.dblclick(pt3["x"], pt3["y"])
    page.wait_for_timeout(600)
    page.locator("[data-frameos-pane-addnode-backdrop]").first.click(
        position={"x": 1000, "y": 700}, force=True
    )
    page.wait_for_timeout(400)
    check("backdrop:closes-menu",
          page.locator("[data-frameos-pane-addnode-menu]").count() == 0,
          "点遮罩关不掉菜单")

    # ── 9 双击**节点**不弹菜单 ──
    node = page.locator(".react-flow__node").first
    bb = node.bounding_box()
    page.mouse.dblclick(bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2)
    page.wait_for_timeout(600)
    check("node-dblclick:does-not-open-menu",
          page.locator("[data-frameos-pane-addnode-menu]").count() == 0,
          "双击节点不该弹「添加节点」菜单(节点双击是聚焦/编辑)")

    # ── 10 新节点可撤销 ──
    n_now = page.evaluate("() => window.__frameos_store.getState().nodes.length")
    page.evaluate("() => window.__frameos_store.getState().undo()")
    page.wait_for_timeout(400)
    n_after_undo = page.evaluate(
        "() => window.__frameos_store.getState().nodes.length"
    )
    result["undo"] = {"before": n_now, "after": n_after_undo}
    check("undo:new-node-undoable", n_after_undo == n_now - 1,
          f"{n_now} → {n_after_undo}")

    check("diagnostics:zero", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 348,
        "title": "FrameOS double-click-to-add was half-wired: event half existed, menu half did not",
        "defect": (
            "Batch 168 wired the EVENT half of 'double-click empty canvas to add a node': "
            "a dblclick listener on .react-flow__pane that skips node hits and records the "
            "coordinates into paneMenuAt. But paneMenuAt had ZERO readers anywhere outside "
            "the store -- no component ever rendered it. Double-clicking empty canvas wrote "
            "state into the void: nothing appeared, and Escape could not even clear it "
            "(measured: paneMenuAt={x:140,y:140} both before and after Escape)."
        ),
        "fix": (
            "Added FrameosPaneAddNodeMenu (the missing rendering half), reusing the "
            "tool rail's exported NODE_TYPES so the list of node types has exactly one "
            "source of truth. Added an optional `position` to AddNodeOpts in FLOW "
            "coordinates -- addNode previously could only place a node at the viewport "
            "centre or at a random spot, so 'double-click here' would have put the node "
            "somewhere unrelated to where the user clicked. Added paneMenuAt to the "
            "Escape multi-level exit chain."
        ),
        "corrects_batch346": (
            "Batch 346 recorded '双击空白处添加节点' as an unfixable fidelity gap, on the "
            "reasoning that the promise never says WHICH node type to add. That reasoning "
            "was wrong: Batch 168's own design already answers it -- the intent was a "
            "'选择节点类型' MENU from which the user picks. So the feature was not "
            "unimplementable, it was half-built. The general lesson: before writing a "
            "feature off as 'cannot implement without inventing', check whether an "
            "existing half-implementation already encodes the answer."
        ),
        "results": [],
    }
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        desktop = browser.new_page(
            viewport={"width": 1440, "height": 900}, device_scale_factor=1
        )
        audit["results"].append(run_desktop(desktop))
        desktop.close()
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    checks = audit["results"][0]["checks"]
    print(
        "Batch 348 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "Double-clicking empty canvas now opens the node-type picker that Batch 168 "
        "intended; picking a type adds exactly one node landing on the double-clicked "
        "point; the menu closes on pick, on Escape and on backdrop click; double-clicking "
        "a node still focuses/edits instead of opening the menu; and the new node is "
        "undoable."
    )


if __name__ == "__main__":
    main()
