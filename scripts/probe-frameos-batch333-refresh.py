#!/usr/bin/env python3
"""Batch 333 探针：刷新后跨画布编辑丢失。

背景（**有源站证据**，非凭空发明）:
  - 手册 20-reference.md「刷新后内容保留；撤销/重做历史清空」；
  - Batch 251 采样记录「刷新确认持久化」—— 源站刷新后编辑仍在。
  - Batch 208 的 verifier 只断言 `nodes_after == nodes_before`（**节点数**相等），
    恰好对「回到 mock 初值」也成立，因此**没有真正验证内容持久**。

本探针验证真实内容是否跨刷新保留。

用法: ~/.venvs/liblib-harness/bin/python scripts/probe-frameos-batch333-refresh.py
"""

import json

from playwright.sync_api import sync_playwright

URL = "http://localhost:4317/frameos/canvas/demo"

SETUP_JS = """
() => {
  const st = window.__frameos_store;
  const key = (b) => `${b.project}/${b.scene}/${b.canvas}`;
  st.setState({ past: [], future: [], groups: [] });
  const A = key(st.getState().breadcrumb);
  st.getState().addNode('text');                       // 新增（带内容语义的新 id）
  const addedId = st.getState().nodes[st.getState().nodes.length - 1].id;
  st.setState((s) => ({ nodes: s.nodes.map((n, i) =>
    i === 0 ? { ...n, position: { x: n.position.x + 250, y: n.position.y + 130 } } : n) }));
  st.getState().createGroup(st.getState().nodes.slice(0, 2).map((n) => n.id));
  return {
    A, addedId,
    ids: st.getState().nodes.map((n) => n.id),
    groups: st.getState().groups.map((g) => g.memberIds),
    pos0: st.getState().nodes[0].position,
  };
}
"""


def main() -> int:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1600, "height": 950})
        page.goto(URL, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_selector(".react-flow__node", timeout=30000)
        page.wait_for_timeout(1200)

        setup = page.evaluate(SETUP_JS)
        print("=== before refresh ===")
        print(json.dumps(setup, ensure_ascii=False, indent=2))

        page.reload(wait_until="domcontentloaded", timeout=60000)
        page.wait_for_selector(".react-flow__node", timeout=30000)
        page.wait_for_timeout(1200)

        after = page.evaluate(
            """() => {
              const st = window.__frameos_store;
              return {
                ids: st.getState().nodes.map((n) => n.id),
                groups: st.getState().groups.map((g) => g.memberIds),
                pos0: st.getState().nodes[0] ? st.getState().nodes[0].position : null,
                undoDisabled: document.querySelectorAll('button[disabled]').length,
                past: st.getState().past.length,
              };
            }"""
        )
        print("=== after refresh ===")
        print(json.dumps(after, ensure_ascii=False, indent=2))

        added_survived = setup["addedId"] in after["ids"]
        move_survived = after["pos0"] == setup["pos0"]
        group_survived = bool(after["groups"])
        print()
        print("ADDED_SURVIVED   :", added_survived)
        print("MOVE_SURVIVED    :", move_survived)
        print("GROUP_SURVIVED   :", group_survived)
        print("HISTORY_RESET    :", after["past"] == 0)
        print("VERDICT          :", "CONTENT-PERSISTED" if (added_survived and move_survived and group_survived) else "CONTENT-LOST")
        browser.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
