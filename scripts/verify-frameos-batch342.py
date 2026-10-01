#!/usr/bin/env python3

"""Verify Batch 342: 节点搜索「点击结果聚焦」把**流坐标**当屏幕坐标传给 setCenter.

缺陷（克隆侧，用户可达）:
`FrameosNodeSearch.focusNode()` 用 `getBoundingClientRect()` 取节点的**屏幕
坐标**喂给 `useReactFlow().setCenter(x, y, ...)`，但 setCenter 要的是**画布
流坐标**。两者只差「视口原点 + 缩放 + 平移」, 所以在**默认视图**下偏移小、
容易被当成「差不多对」而放过。

实测（探针把视口改成 translate(400,260) scale(0.5), 模拟用户缩放/平移过）:
点击结果后目标节点落在屏幕 (1272, -66) —— 中心比视口顶边还高 66px,
**节点被推出了屏幕**, 与组件注释声明的「把视野缩放聚焦到它」正好相反。

修复: 直接用节点的流坐标 (`position + 尺寸/2`) 调 setCenter。

断言（本验证器**先做非默认视图**再点结果——这是本缺陷能否被测出来的前提）:
1. 工具条「搜索节点」能打开面板;
2. 输入后目标节点出现在结果里;
3. 点击结果后**选中**该节点;
4. 缩放达到源站实测的 2.73;
5. 目标节点落在视口中心（容差内）;
6. 目标节点**完整可见**（四边都在视口内）;
7. 点**另一条**结果时聚焦的是那条节点（不是恒定聚焦第一条）;
8. 诊断零错误。
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
    / "liblib-frameos-batch342-2026-10-01"
    / "runtime-audit.json"
)
sys.path.insert(0, str(ROOT / "scripts"))
from frameos_verify_common import attach_errors, goto_clean_canvas  # noqa: E402

VIEW_W, VIEW_H = 1600, 950

SETUP_JS = """
() => {
  const st = window.__frameos_store;
  st.setState({ past: [], future: [], groups: [], selectedNodeId: null });
  const nodes = st.getState().nodes;
  // 取两个内容可区分的节点, 用于「聚焦结果」与「聚焦另一条」两组断言
  const a = nodes.find((n) => String(n.data.title || '').length > 3) || nodes[0];
  const b = nodes.find((n) => n.id !== a.id && String(n.data.title || '').length > 3)
            || nodes[1];
  return {
    a: { id: a.id, title: String(a.data.title), position: a.position },
    b: { id: b.id, title: String(b.data.title), position: b.position },
  };
}
"""

NODE_SCREEN_JS = """
(id) => {
  const el = document.querySelector(`.react-flow__node[data-id="${id}"]`);
  if (!el) return null;
  const r = el.getBoundingClientRect();
  return { left: r.left, top: r.top, w: r.width, h: r.height,
           cx: r.left + r.width / 2, cy: r.top + r.height / 2 };
}
"""

VIEWPORT_TF_JS = """
() => {
  const t = document.querySelector('.react-flow__viewport');
  return t ? t.style.transform : null;
}
"""


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": f"{VIEW_W}x{VIEW_H}", "checks": []}

    def check(name: str, ok: bool, detail: str = "") -> None:
        assert ok, f"batch342 check failed: {name} {detail}".strip()
        result["checks"].append(name)

    errors = attach_errors(page)
    goto_clean_canvas(page, BASE_URL)
    setup = page.evaluate(SETUP_JS)
    result["setup"] = setup
    page.wait_for_timeout(500)

    # ── 前置: 把画布弄成**非默认视图**（真实用户手势，不改 DOM）──
    # 本缺陷在默认视图下偏移很小, 不先制造偏移就测不出来。
    for _ in range(3):
        page.locator('button[aria-label="缩小"]').first.click()
        page.wait_for_timeout(120)
    page.mouse.move(1250, 760)          # 空白处按下拖拽 = 平移
    page.mouse.down()
    for i in range(6):
        page.mouse.move(1250 - (i + 1) * 30, 760 - (i + 1) * 20)
        page.wait_for_timeout(16)
    page.mouse.up()
    page.wait_for_timeout(400)
    distorted_tf = page.evaluate(VIEWPORT_TF_JS)
    result["distorted_viewport"] = distorted_tf
    check("precondition:viewport-distorted",
          distorted_tf is not None and "scale" in distorted_tf,
          f"transform={distorted_tf}")
    before = page.evaluate(NODE_SCREEN_JS, setup["a"]["id"])
    result["before_screen"] = before

    # ── 1 打开搜索面板 ──
    page.locator('button[aria-label="搜索节点"]').first.click()
    page.wait_for_selector("[data-frameos-node-search-input]", timeout=10000)
    check("search:panel-opens",
          page.locator("[data-frameos-node-search-input]").count() == 1,
          "搜索面板未打开")

    # ── 2 输入过滤出目标 ──
    page.locator("[data-frameos-node-search-input]").first.fill(
        setup["a"]["title"][:5], timeout=10000
    )
    page.wait_for_timeout(400)
    target = page.locator(f'[data-frameos-node-search-result="{setup["a"]["id"]}"]')
    check("search:target-listed", target.count() == 1,
          f"title={setup['a']['title']!r} results={page.locator('[data-frameos-node-search-result]').count()}")

    # ── 3/4/5/6 点击结果: 选中 + 缩放 2.73 + 居中 + 完整可见 ──
    target.first.click()
    page.wait_for_timeout(1400)          # 600ms 动画 + 余量
    after = page.evaluate(NODE_SCREEN_JS, setup["a"]["id"])
    result["after_screen"] = after
    selected = page.evaluate(
        "() => window.__frameos_store.getState().selectedNodeId"
    )
    tf = page.evaluate(VIEWPORT_TF_JS)
    result["after_viewport"] = tf
    dx = after["cx"] - VIEW_W / 2
    dy = after["cy"] - VIEW_H / 2
    result["offset"] = {"dx": round(dx), "dy": round(dy)}

    check("focus:node-selected", selected == setup["a"]["id"],
          f"selected={selected} want={setup['a']['id']}")
    check("focus:zoom-2_73", "2.73" in (tf or ""), f"transform={tf}")
    # 缩到 2.73 后节点 300x200 → 819x546; 视口 1600x950。
    # 只要中心偏离 > 半屏就说明没对上, 这里用宽松但有意义的容差。
    check("focus:centered", abs(dx) <= 60 and abs(dy) <= 60,
          f"node center=({after['cx']:.0f},{after['cy']:.0f}) "
          f"expected=({VIEW_W / 2},{VIEW_H / 2}) dx={dx:+.0f} dy={dy:+.0f}")
    check("focus:fully-visible",
          after["left"] >= 0 and after["top"] >= 0
          and after["left"] + after["w"] <= VIEW_W
          and after["top"] + after["h"] <= VIEW_H,
          f"rect=({after['left']:.0f},{after['top']:.0f},"
          f"{after['w']:.0f},{after['h']:.0f})")

    # ── 7 聚焦的是**被点的那条**, 不是恒定聚焦某一条 ──
    # 注意: 点结果**不会**关闭面板 (组件注释即声明「× / Esc 关闭」), 面板仍开着,
    # 所以这里不能再点一次 toggle 按钮 —— 那会把面板关掉。
    page.wait_for_selector("[data-frameos-node-search-input]", timeout=10000)
    page.locator("[data-frameos-node-search-input]").first.fill(
        setup["b"]["title"][:5], timeout=10000
    )
    page.wait_for_timeout(400)
    other = page.locator(f'[data-frameos-node-search-result="{setup["b"]["id"]}"]')
    if other.count() == 1:
        other.first.click()
        page.wait_for_timeout(1400)
        b_screen = page.evaluate(NODE_SCREEN_JS, setup["b"]["id"])
        b_sel = page.evaluate(
            "() => window.__frameos_store.getState().selectedNodeId"
        )
        result["other_screen"] = b_screen
        bdx = b_screen["cx"] - VIEW_W / 2
        bdy = b_screen["cy"] - VIEW_H / 2
        check("focus:second-result-selected", b_sel == setup["b"]["id"],
              f"selected={b_sel} want={setup['b']['id']}")
        check("focus:second-result-centered", abs(bdx) <= 60 and abs(bdy) <= 60,
              f"dx={bdx:+.0f} dy={bdy:+.0f}")
    else:
        # 两条标题前缀相同导致结果不唯一 —— 跳过而不是伪造通过
        result["second_result"] = "skipped: same title prefix"

    check("diagnostics:zero", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 342,
        "title": "FrameOS node search focuses the clicked node (flow coords, not screen coords)",
        "defect": (
            "FrameosNodeSearch.focusNode passed getBoundingClientRect() SCREEN "
            "coordinates to useReactFlow().setCenter(), which expects FLOW "
            "coordinates. The two differ by viewport origin + zoom + pan, so the bug "
            "is nearly invisible in the default view. Measured after distorting the "
            "viewport to translate(400,260) scale(0.5): the clicked node ended at "
            "screen (1272, -66) -- its centre 66px ABOVE the top of the viewport, i.e. "
            "the node was pushed OFF SCREEN, the exact opposite of the component's own "
            "documented intent ('把视野缩放聚焦到它')."
        ),
        "fix": (
            "focusNode now derives the centre from the node's flow coordinates "
            "(position + size/2) instead of its screen rect. Same zoom (2.73, the "
            "source-observed value) and duration."
        ),
        "clone_decision": (
            "This is a clone-internal defect: the component's own comment states the "
            "intent, and the fix restores exactly that intent, so no source-site "
            "sampling was required. The source site remains blocked by the "
            "human-verification gate (see SOURCE_ACCESS_BLOCKED_2026-10-01.md)."
        ),
        "negative_result": (
            "The same batch also investigated Batch 333's persistence subscription, "
            "which writes localStorage once per store write (measured: one write per "
            "pointermove frame during a group drag). At fixture scale (7 nodes) it "
            "costs 0.025 ms/frame; at 287 nodes with a 60-member group the payload "
            "grows 3KB -> 111KB but the cost is still only 0.11 ms/frame. That is far "
            "below a 16ms frame budget, so NO change was made: 'one write per frame' "
            "sounds bad but is not measurably a user-visible defect. Numbers recorded so "
            "a future agent can re-evaluate if canvas size grows."
        ),
        "results": [],
    }
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        desktop = browser.new_page(
            viewport={"width": VIEW_W, "height": VIEW_H}, device_scale_factor=1
        )
        audit["results"].append(run_desktop(desktop))
        desktop.close()
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    checks = audit["results"][0]["checks"]
    print(
        "Batch 342 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "Clicking a node-search result now centres the clicked node in the viewport "
        "even after the user has zoomed and panned, and the node stays fully on screen."
    )


if __name__ == "__main__":
    main()
