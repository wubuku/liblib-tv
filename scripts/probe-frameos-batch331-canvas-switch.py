#!/usr/bin/env python3
"""Batch 331 探针：画布切换（setBreadcrumb）与撤销栈的交互。

疑点（克隆侧，不依赖源站）:
  A. setBreadcrumb 换画布时清 `groups: []`，但**不重置** past/future →
     在画布 A 做的动作可以「撤销」到画布 B 上；更糟的是快照里的 nodes 属于
     画布 A，undo 会把 A 的节点灌进 B。
  B. undo 还原 groups 时用 `reconcileGroups(prev.groups ?? [], prev.nodes)`；
     跨画布后 prev.nodes 属于另一张画布，分组语义是否被污染。
  C. setNodes/setEdges 不入栈 —— ReactFlow 拖拽等外部写入是否绕过历史。

用法: ~/.venvs/liblib-harness/bin/python scripts/probe-frameos-batch331-canvas-switch.py
"""

import json

from playwright.sync_api import sync_playwright

URL = "http://localhost:4317/frameos/canvas/demo"

PROBE_JS = """
() => {
  const st = window.__frameos_store;
  const out = {};
  const keys = Object.keys(st.getState().canvasData || {});
  out.availableCanvases = keys;

  const snap = () => ({
    breadcrumb: st.getState().breadcrumb,
    nodes: st.getState().nodes.map((n) => n.id),
    nodeCount: st.getState().nodes.length,
    groups: st.getState().groups.length,
    pastDepth: st.getState().past.length,
    futureDepth: st.getState().future.length,
  });

  const start = snap();
  // 画布 A 上做一个可撤销动作：新建节点
  st.getState().addNode('text');
  const afterAdd = snap();
  out.A_beforeSwitch = { start, afterAdd };

  // 切到另一张画布
  const other = keys.find((k) => k !== `${st.getState().breadcrumb.project}/${st.getState().breadcrumb.scene}/${st.getState().breadcrumb.canvas}`);
  if (!other) { out.B_noOtherCanvas = true; return out; }
  const [p, s, c] = other.split('/');
  st.getState().setBreadcrumb({ project: p, scene: s, canvas: c });
  const afterSwitch = snap();
  out.B_afterSwitch = { key: other, state: afterSwitch };

  // 在画布 B 上撤销 —— 会发生什么？
  st.getState().undo();
  const afterUndo = snap();
  out.C_undoOnOtherCanvas = {
    afterSwitch: afterSwitch,
    afterUndo: afterUndo,
    // A 画布的节点是否被灌进了 B 画布
    leakedFromA: afterUndo.nodes.filter((id) => afterAdd.nodes.includes(id) && !afterSwitch.nodes.includes(id)),
  };

  // 再撤销一次
  st.getState().undo();
  out.D_secondUndo = snap();
  return out;
}
"""


def main() -> int:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1600, "height": 950})
        page.goto(URL, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_selector(".react-flow__node", timeout=30000)
        page.wait_for_timeout(1200)
        res = page.evaluate(PROBE_JS)
        print("=== canvas switch / undo probe ===")
        print(json.dumps(res, ensure_ascii=False, indent=2)[:3500])
        browser.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
