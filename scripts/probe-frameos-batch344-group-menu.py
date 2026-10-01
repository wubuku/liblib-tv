#!/usr/bin/env python3
"""Batch 344 探针：分组右键菜单的「删除」与它标注的 ⌫ 快捷键是否真的生效。

疑点（克隆侧，不依赖源站）:
`FrameosGroupCanvas` 的分组右键菜单三项全部是 `showToast(..., "success")`
的 mock，其中「删除」的 toast 写着「已删除分组」—— 但**分组根本没有被删除**。
同一菜单还标注了快捷键 ⌫，而 `page.tsx` 的 Delete/Backspace 分支只在
`state.selectedNodeId` 存在时才处理，纯选中分组时按 ⌫ 应当无任何反应。

用户表现：右键分组 → 点「删除」→ 弹出绿色「已删除分组」→ **组还在原地**；
或按 ⌫ → 什么都没发生（尽管菜单上写着 ⌫）。

本探针只测克隆自身是否兑现自己的文案/标注，不声称源站如何处理
（源站被人机验证阻塞，见 SOURCE_ACCESS_BLOCKED_2026-10-01.md）。

用法: ~/.venvs/liblib-harness/bin/python scripts/probe-frameos-batch344-group-menu.py
"""

import json
import sys

from playwright.sync_api import sync_playwright

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from frameos_verify_common import attach_errors, goto_clean_canvas  # noqa: E402

BASE_URL = "http://localhost:4317"

SETUP_JS = """
() => {
  const st = window.__frameos_store;
  st.setState({ past: [], future: [], groups: [], selectedNodeId: null,
                selectedGroupId: null });
  const ids = st.getState().nodes.slice(0, 2).map((n) => n.id);
  const gid = st.getState().createGroup(ids);
  window.__gid = gid;
  const g = st.getState().groups.find((x) => x.id === gid);
  return { gid, name: g.name, members: g.memberIds.length,
           groupCount: st.getState().groups.length };
}
"""

STATE_JS = """
() => {
  const s = window.__frameos_store.getState();
  return {
    groupCount: s.groups.length,
    hasGroup: s.groups.some((g) => g.id === window.__gid),
    selectedGroupId: s.selectedGroupId,
    selectedNodeId: s.selectedNodeId,
    pastDepth: s.past.length,
    nodeCount: s.nodes.length,
    groupBoxInDom: document.querySelectorAll('.frameos-canvas-group').length,
    toasts: Array.from(document.querySelectorAll('[data-frameos-toast], .frameos-toast'))
      .map((e) => e.textContent),
  };
}
"""


def main() -> int:
    out: dict = {}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1600, "height": 950})
        errors = attach_errors(page)
        goto_clean_canvas(page, BASE_URL)

        # ── 场景 1: 右键分组 → 点「删除」──
        out["setup"] = page.evaluate(SETUP_JS)
        page.wait_for_timeout(500)
        box = page.locator(".frameos-canvas-group").first.bounding_box()
        if not box:
            print("!! 找不到分组盒")
            return 1
        page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2,
                         button="right")
        page.wait_for_timeout(500)
        items = page.locator("[data-frameos-context-item]")
        out["menuItems"] = [items.nth(i).inner_text().strip()
                            for i in range(items.count())]
        out["menu_present"] = page.locator("[data-frameos-context-menu]").count()
        del_item = page.locator('[data-frameos-context-item="删除"]')
        out["delete_item_count"] = del_item.count()
        if del_item.count() == 0:
            print("!! 菜单里没有「删除」项")
            return 1
        del_item.first.click()
        page.wait_for_timeout(700)
        out["after_delete_click"] = page.evaluate(STATE_JS)

        # ── 场景 2: 菜单标注的 ⌫ 快捷键（纯选中分组时）──
        page.evaluate(SETUP_JS)
        page.wait_for_timeout(400)
        b2 = page.locator(".frameos-canvas-group").first.bounding_box()
        page.mouse.click(b2["x"] + b2["width"] / 2, b2["y"] + b2["height"] / 2)
        page.wait_for_timeout(300)
        out["before_backspace"] = page.evaluate(STATE_JS)
        page.keyboard.press("Backspace")
        page.wait_for_timeout(600)
        out["after_backspace"] = page.evaluate(STATE_JS)

        out["consoleErrors"] = errors
        browser.close()

    d, b = out["after_delete_click"], out["after_backspace"]
    print("=== batch344 分组右键菜单探针 ===")
    print(f"菜单项: {out['menuItems']}")
    print(f"[点「删除」] groupCount={d['groupCount']} hasGroup={d['hasGroup']} "
          f"DOM 分组盒={d['groupBoxInDom']} pastDepth={d['pastDepth']}")
    print(f"  toast: {d['toasts']}")
    print(f"[按 ⌫]  before: hasGroup={out['before_backspace']['hasGroup']} "
          f"selectedGroupId={out['before_backspace']['selectedGroupId']} "
          f"selectedNodeId={out['before_backspace']['selectedNodeId']}")
    print(f"          after : hasGroup={b['hasGroup']} groupCount={b['groupCount']} "
          f"pastDepth={b['pastDepth']}")
    if errors:
        print(f"console errors: {errors}")
    print("\n=== 判定 ===")
    print(json.dumps({
        "delete_item_is_mock": d["hasGroup"] is True,
        "delete_pushes_history": d["pastDepth"] > out["setup"]["members"] * 0,
        "menu_shortcut_backspace_works": (
            b["hasGroup"] is False and b["groupCount"] < out["before_backspace"]["groupCount"]
        ),
        "group_still_in_dom_after_delete": d["groupBoxInDom"] > 0,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
