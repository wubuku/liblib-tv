#!/usr/bin/env python3
"""Batch 343 探针：边的完整性不变式在**非 removeNode 路径**上是否被绕过。

背景（Batch 341 的同一个判断 —— 不变式只该有单一出口）:
Batch 341 把「分组盒 == 存活成员包围盒 + 28」提升为 store 写入口的强制不变式。
**边有完全同构的一条不变式**：「每条边的 source/target 都必须指向存活的节点」。

store 里剪边只出现在**一处**（`removeNode`）：
    edges: state.edges.filter((e) => e.source !== id && e.target !== id)

而 `setNodes` 是**公开 action**（`setNodes: (nodes) => set({ nodes })`），
FrameOS 内部有调用方直接用它替换节点集合：
  - FrameosNodeEditPanel 删除节点 → setNodes(nodes.filter(...))   ← 悬空边
  - page.tsx onNodesChange 拖拽 → setNodes(updated)               （只改位置，不删节点）

本探针先核实这些路径是否真能产生悬空边，以及悬空边对 React Flow 的可见影响。

用法: ~/.venvs/liblib-harness/bin/python scripts/probe-frameos-batch343-edge-integrity.py
"""

import json
import sys

from playwright.sync_api import sync_playwright

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from frameos_verify_common import attach_errors, goto_clean_canvas  # noqa: E402

BASE_URL = "http://localhost:4317"

# 建一组带连线的节点: 取前两个有边相连的节点
SETUP_JS = """
() => {
  const st = window.__frameos_store;
  st.setState({ past: [], future: [], groups: [] });
  const s = st.getState();
  const e = s.edges[0];
  if (!e) return { ok: false, reason: 'fixture has no edges' };
  window.__edgeId = e.id;
  window.__source = e.source;
  return { ok: true, edgeId: e.id, source: e.source, target: e.target,
           edgeCount: s.edges.length };
}
"""

STATE_JS = """
() => {
  const st = window.__frameos_store;
  const s = st.getState();
  const ids = new Set(s.nodes.map((n) => n.id));
  const dangling = s.edges
    .filter((e) => !ids.has(e.source) || !ids.has(e.target))
    .map((e) => ({ id: e.id, source: e.source, target: e.target,
                   missing: [!ids.has(e.source) ? e.source : null,
                             !ids.has(e.target) ? e.target : null].filter(Boolean) }));
  return {
    nodeCount: s.nodes.length,
    edgeCount: s.edges.length,
    renderedEdges: document.querySelectorAll('.react-flow__edge').length,
    dangling,
  };
}
"""

# 路径 A: removeNode —— 已知会剪边 (对照组)
VIA_REMOVE_NODE_JS = """
(id) => { window.__frameos_store.getState().removeNode(id); return true; }
"""

# 路径 B: setNodes(filter) —— 与 FrameosNodeEditPanel 删除按钮完全一致的写法
VIA_SET_NODES_JS = """
(id) => {
  const st = window.__frameos_store;
  st.getState().setNodes(st.getState().nodes.filter((n) => n.id !== id));
  return true;
}
"""


def main() -> int:
    out: dict = {}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1600, "height": 950})
        errors = attach_errors(page)
        goto_clean_canvas(page, BASE_URL)

        # ── 对照组: removeNode ──
        out["a_setup"] = page.evaluate(SETUP_JS)
        out["a_before"] = page.evaluate(STATE_JS)
        page.evaluate(VIA_REMOVE_NODE_JS, out["a_setup"]["source"])
        page.wait_for_timeout(500)
        out["a_after"] = page.evaluate(STATE_JS)

        # ── 路径 B: setNodes(filter) ──
        out["b_setup"] = page.evaluate(SETUP_JS)
        out["b_before"] = page.evaluate(STATE_JS)
        page.evaluate(VIA_SET_NODES_JS, out["b_setup"]["source"])
        page.wait_for_timeout(500)
        out["b_after"] = page.evaluate(STATE_JS)

        # 悬空边是否进了持久化 (刷新后是否仍在)
        persisted_before = page.evaluate(
            """() => {
              const raw = localStorage.getItem('frameos.canvasData.v1');
              if (!raw) return null;
              const data = JSON.parse(raw);
              const key = '测试作品/测试项目/画布 1';
              const c = data[key];
              if (!c) return null;
              const ids = new Set((c.nodes || []).map((n) => n.id));
              return {
                edgeCount: (c.edges || []).length,
                dangling: (c.edges || [])
                  .filter((e) => !ids.has(e.source) || !ids.has(e.target))
                  .map((e) => e.id),
              };
            }"""
        )
        out["persisted"] = persisted_before
        page.reload(wait_until="domcontentloaded", timeout=90000)
        page.wait_for_selector(".react-flow__node", timeout=30000)
        page.wait_for_timeout(1200)
        out["after_reload"] = page.evaluate(STATE_JS)

        out["consoleErrors"] = errors
        browser.close()

    a, b = out["a_after"], out["b_after"]
    print("=== batch343 边完整性探针 ===")
    print(f"[对照组 removeNode] edges {out['a_before']['edgeCount']} → {a['edgeCount']}, "
          f"dangling={a['dangling']}")
    print(f"[路径 setNodes]     edges {out['b_before']['edgeCount']} → {b['edgeCount']}, "
          f"dangling={b['dangling']}")
    print(f"  渲染出的 .react-flow__edge: {b['renderedEdges']} (边 {b['edgeCount']})")
    print(f"持久化里的悬空边: {out['persisted']}")
    print(f"刷新后: nodes={out['after_reload']['nodeCount']} "
          f"edges={out['after_reload']['edgeCount']} "
          f"dangling={out['after_reload']['dangling']}")
    if out["consoleErrors"]:
        print(f"console errors: {out['consoleErrors']}")
    print("\n=== 判定 ===")
    print(json.dumps({
        "removeNode_prunes": len(a["dangling"]) == 0,
        "setNodes_leaves_dangling": len(b["dangling"]) > 0,
        "dangling_count": len(b["dangling"]),
        "dangling_persisted": len((out["persisted"] or {}).get("dangling") or []),
        "dangling_survives_reload": len(out["after_reload"]["dangling"]) > 0,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
