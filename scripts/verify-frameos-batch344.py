#!/usr/bin/env python3

"""Verify Batch 344: 分组右键菜单的「删除」兑现承诺，⌫ 快捷键接上。

缺陷（克隆侧，用户可达）:
`FrameosGroupCanvas` 的分组右键菜单里，「删除」项此前是
`showToast("已删除分组 (mock)", "success")` —— 弹一条**绿色成功提示说分组已删**，
但**分组根本没有被删除**。

实测 (probe-frameos-batch344-group-menu.py, 修复前):
    菜单项: ['复制\\n⌘C', '创建副本\\n⌘D', '删除\\n⌫']
    [点「删除」] groupCount=1 hasGroup=True DOM 分组盒=1   ← 组还在
    [按 ⌫]      hasGroup=True groupCount=1 pastDepth=1     ← 毫无反应

第二个缺陷：菜单把 ⌫ 标成「删除分组」的快捷键，但 `page.tsx` 的
Delete/Backspace 分支只认 `selectedNodeId` —— 纯选中分组时按 ⌫ **什么都不发生**。
**菜单上写着的快捷键必须能用。**

修复:
1. 「删除」直接复用 store 已有的 `ungroup`（工具条「解组」用的同一个 action），
   并且**不发 toast** —— 组从画布上消失本身就是反馈，比一条可能不兑现的文案
   诚实，且与工具条保持一致。
2. Delete/Backspace 分支补上 selectedGroupId 分支，语义与菜单项一致。

CLONE_DECISION: 「删除分组」也可能指「连成员一起删」。那是破坏性操作、且需要
二次确认，源站行为**未采样**（被人机验证阻塞，见 SOURCE_ACCESS_BLOCKED_2026-10-01.md），
**不擅自发明**。此处取非破坏、可撤销的那一种读法（成员位置保持）。

断言:
1. 菜单三项齐全（复制/创建副本/删除）—— 源站实测过它们存在, 不删;
2. 点「删除」后分组**真的消失**（store + DOM 两侧都验）;
3. 删除后**成员节点一个不少**（ungroup 语义, 不是删成员）;
4. 删除**入了撤销栈**且撤销能还原分组;
5. 删除后 selectedGroupId **不留悬空选中**;
6. **不发 toast**（不再有「已删除分组」这种可能不兑现的文案）;
7. 菜单标注的 ⌫ 在纯选中分组时**真的删掉分组**;
8. ⌫ 在**选中节点**时仍然删节点（不回归 Batch 177）;
9. 诊断零错误。
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
    / "liblib-frameos-batch344-2026-10-01"
    / "runtime-audit.json"
)
sys.path.insert(0, str(ROOT / "scripts"))
from frameos_verify_common import attach_errors, goto_clean_canvas  # noqa: E402

SETUP_JS = """
() => {
  const st = window.__frameos_store;
  st.setState({ past: [], future: [], groups: [], selectedNodeId: null,
                selectedGroupId: null });
  const ids = st.getState().nodes.slice(0, 2).map((n) => n.id);
  const gid = st.getState().createGroup(ids);
  window.__gid = gid;
  window.__members = ids;
  const g = st.getState().groups.find((x) => x.id === gid);
  return { gid, members: g.memberIds, memberCount: g.memberIds.length,
           nodeCount: st.getState().nodes.length, groupCount: st.getState().groups.length };
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
    membersAlive: (window.__members || []).every((id) =>
      s.nodes.some((n) => n.id === id)),
    groupBoxInDom: document.querySelectorAll('.frameos-canvas-group').length,
  };
}
"""


def open_group_menu(page: Page) -> list[str]:
    """右键分组 → 读出菜单项文本。"""
    box = page.locator(".frameos-canvas-group").first.bounding_box()
    assert box, "找不到分组盒"
    page.mouse.click(
        box["x"] + box["width"] / 2, box["y"] + box["height"] / 2, button="right"
    )
    page.wait_for_timeout(500)
    items = page.locator("[data-frameos-context-item]")
    return [items.nth(i).inner_text().strip() for i in range(items.count())]


def toasts(page: Page) -> list[str]:
    return page.evaluate(
        """() => Array.from(
             document.querySelectorAll('[data-frameos-toast], .frameos-toast, .toast')
           ).map((e) => e.textContent)"""
    )


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool, detail: str = "") -> None:
        assert ok, f"batch344 check failed: {name} {detail}".strip()
        result["checks"].append(name)

    errors = attach_errors(page)
    goto_clean_canvas(page, BASE_URL)

    # ── 1 菜单三项齐全 ──
    setup = page.evaluate(SETUP_JS)
    result["setup"] = setup
    page.wait_for_timeout(500)
    labels = open_group_menu(page)
    result["menu_items"] = labels
    check("menu:has-three-items", len(labels) == 3, f"items={labels}")
    check("menu:delete-present", any(l.startswith("删除") for l in labels),
          f"items={labels}")
    check("menu:delete-advertises-backspace", any("⌫" in l for l in labels),
          f"items={labels}")

    # ── 2/3/4/5/6 点「删除」──
    before = page.evaluate(STATE_JS)
    page.locator('[data-frameos-context-item="删除"]').first.click()
    page.wait_for_timeout(700)
    after = page.evaluate(STATE_JS)
    result["after_delete"] = after
    result["toasts_after_delete"] = toasts(page)
    check("delete:group-gone-from-store", after["hasGroup"] is False,
          f"hasGroup={after['hasGroup']}")
    check("delete:group-gone-from-dom", after["groupBoxInDom"] == 0,
          f"groupBoxInDom={after['groupBoxInDom']}")
    check("delete:members-kept", after["membersAlive"] is True
          and after["nodeCount"] == setup["nodeCount"],
          f"nodeCount {setup['nodeCount']} → {after['nodeCount']} "
          f"membersAlive={after['membersAlive']}")
    check("delete:group-count-drops",
          after["groupCount"] == before["groupCount"] - 1,
          f"{before['groupCount']} → {after['groupCount']}")
    check("delete:no-dangling-selection", after["selectedGroupId"] is None,
          f"selectedGroupId={after['selectedGroupId']}")
    check("delete:no-false-success-toast",
          not any("已删除分组" in t for t in result["toasts_after_delete"]),
          f"toasts={result['toasts_after_delete']}")

    undone = page.evaluate(
        """() => {
          window.__frameos_store.getState().undo();
          const s = window.__frameos_store.getState();
          return { hasGroup: s.groups.some((g) => g.id === window.__gid) };
        }"""
    )
    result["undo"] = undone
    check("undo:group-restored", undone["hasGroup"] is True,
          "撤销后分组没有回来")

    # ── 7 菜单标注的 ⌫ ──
    page.evaluate(SETUP_JS)
    page.wait_for_timeout(400)
    box = page.locator(".frameos-canvas-group").first.bounding_box()
    page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    page.wait_for_timeout(300)
    sel = page.evaluate(STATE_JS)
    check("shortcut:group-is-selected", sel["selectedGroupId"] is not None
          and sel["selectedNodeId"] is None,
          f"selectedGroupId={sel['selectedGroupId']} selectedNodeId={sel['selectedNodeId']}")
    page.keyboard.press("Backspace")
    page.wait_for_timeout(600)
    after_bs = page.evaluate(STATE_JS)
    result["after_backspace"] = after_bs
    check("shortcut:backspace-removes-group", after_bs["hasGroup"] is False,
          f"hasGroup={after_bs['hasGroup']}")
    check("shortcut:backspace-keeps-members",
          after_bs["nodeCount"] == setup["nodeCount"],
          f"nodeCount {setup['nodeCount']} → {after_bs['nodeCount']}")

    # ── 8 ⌫ 删节点仍正常（Batch 177 不回归）──
    page.evaluate(SETUP_JS)
    node_state = page.evaluate(
        """() => {
          const st = window.__frameos_store;
          st.setState({ past: [], future: [], groups: [], selectedNodeId: null,
                        selectedGroupId: null });
          const n = st.getState().nodes[0];
          st.getState().selectNode(n.id);
          window.__victim = n.id;
          return { victim: n.id, nodeCount: st.getState().nodes.length };
        }"""
    )
    page.wait_for_timeout(300)
    page.keyboard.press("Delete")
    page.wait_for_timeout(500)
    node_after = page.evaluate(
        """() => {
          const s = window.__frameos_store.getState();
          return { gone: !s.nodes.some((n) => n.id === window.__victim),
                   nodeCount: s.nodes.length };
        }"""
    )
    result["node_delete"] = {"before": node_state, "after": node_after}
    check("shortcut:delete-still-removes-node", node_after["gone"] is True,
          f"victim={node_state['victim']}")
    check("shortcut:node-count-drops",
          node_after["nodeCount"] == node_state["nodeCount"] - 1,
          f"{node_state['nodeCount']} → {node_after['nodeCount']}")

    check("diagnostics:zero", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 344,
        "title": "FrameOS group context menu: 删除 actually deletes, and its ⌫ shortcut works",
        "defect": (
            "The group context menu's 删除 item only fired "
            "showToast(\"已删除分组 (mock)\", \"success\") -- a GREEN success toast "
            "claiming the group was deleted while the group was still on the canvas. "
            "Measured: after clicking it, groupCount stayed 1, hasGroup stayed true and "
            "the group box was still in the DOM. Separately, the menu advertises ⌫ as "
            "the shortcut for 删除, but the Delete/Backspace handler only looked at "
            "selectedNodeId, so pressing ⌫ with only a group selected did nothing at all."
        ),
        "fix": (
            "删除 now calls the existing ungroup action (the same one the toolbar's 解组 "
            "uses) and fires no toast at all -- the group disappearing from the canvas is "
            "the honest feedback, and it matches the toolbar. The Delete/Backspace branch "
            "gained a selectedGroupId case with the same semantics. Reusing the existing "
            "action instead of hand-rolling it is the same principle as batches 328/341/343."
        ),
        "clone_decision": (
            "「删除分组」could also mean 'delete the members too'. That is destructive, "
            "would need a confirmation, and the source site's behaviour was NOT sampled "
            "(blocked by the human-verification gate, see "
            "SOURCE_ACCESS_BLOCKED_2026-10-01.md) -- so it was NOT invented here. The "
            "non-destructive, undoable reading (members keep their positions) was taken. "
            "The 复制 / 创建副本 items are still mocks: the source confirmed the ITEMS "
            "exist but not what they do, and implementing them would require inventing "
            "semantics (does a duplicated group share members with the original? that "
            "would break the one-group-per-node model), so they were left untouched."
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
        "Batch 344 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "The group context menu's 删除 now really removes the group (store and DOM), keeps "
        "its member nodes, pushes history and leaves no dangling selection, no longer "
        "claims success via a toast, and the ⌫ shortcut it advertises actually works "
        "while Delete on a node still works."
    )


if __name__ == "__main__":
    main()
