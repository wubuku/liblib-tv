#!/usr/bin/env python3
"""Batch 332 探针：canvasData 不回写实时编辑。

疑点（克隆侧，不依赖源站）:
  A. setBreadcrumb 换画布时从 MOCK_CANVASES 取数，**不把离开画布的实时
     nodes/edges 写回 canvasData** → 切走再切回，本地新增/移动/删除的
     节点全部丢失（编辑内容不跟随画布）。
  B. FrameosBreadcrumb 的画布下拉对**当前**画布显示实时 `nodes.length`，
     对**其他**画布显示 `canvasData[key].nodes.length`（静态 fixture）。
     → 同一列表内，有的画布计数是实时的、有的是陈旧的，彼此矛盾。

用法: ~/.venvs/liblib-harness/bin/python scripts/probe-frameos-batch332-canvas-persist.py
"""

import json

from playwright.sync_api import sync_playwright

URL = "http://localhost:4317/frameos/canvas/demo"

PROBE_JS = """
() => {
  const st = window.__frameos_store;
  const key = (b) => `${b.project}/${b.scene}/${b.canvas}`;
  const cur = () => key(st.getState().breadcrumb);
  const out = {};

  const otherKey = Object.keys(st.getState().canvasData).find((k) => k !== cur());
  out.setup = { currentCanvas: cur(), otherCanvas: otherKey,
                liveNodes: st.getState().nodes.length,
                otherStored: (st.getState().canvasData[otherKey]?.nodes || []).length };

  // A. 在当前画布做三种编辑：新增 / 移动 / 删除
  const before = st.getState().nodes.map((n) => ({ id: n.id, x: n.position.x, y: n.position.y }));
  st.getState().addNode('text');                       // 新增
  const addedId = st.getState().nodes[st.getState().nodes.length - 1].id;
  st.setState((s) => ({ nodes: s.nodes.map((n) =>
      n.id === before[0].id ? { ...n, position: { x: n.position.x + 123, y: n.position.y + 77 } } : n) }));
  const movedId = before[0].id;
  st.getState().removeNode(before[1].id);               // 删除
  const deletedId = before[1].id;

  const afterEdits = {
    count: st.getState().nodes.length,
    ids: st.getState().nodes.map((n) => n.id),
    movedPos: (() => { const n = st.getState().nodes.find((x) => x.id === movedId); return n ? n.position : null; })(),
  };
  out.afterEdits = { ...afterEdits, addedId, movedId, deletedId };

  // 切到另一张画布，再切回来
  const [p, s, c] = otherKey.split('/');
  st.getState().setBreadcrumb({ project: p, scene: s, canvas: c });
  st.getState().setBreadcrumb({ ...(() => { const b = st.getState().breadcrumb; const [P,S,C] = cur().split('/'); return { project: P, scene: S, canvas: C }; })() });
  out.afterRoundTrip = {
    count: st.getState().nodes.length,
    ids: st.getState().nodes.map((n) => n.id),
    addedSurvived: st.getState().nodes.some((n) => n.id === addedId),
    deletedStayedDeleted: !st.getState().nodes.some((n) => n.id === deletedId),
    movedPos: (() => { const n = st.getState().nodes.find((x) => x.id === movedId); return n ? n.position : null; })(),
  };
  out.LOST = {
    addedNodeLost: !out.afterRoundTrip.addedSurvived,
    deleteReverted: !out.afterRoundTrip.deletedStayedDeleted,
    moveReverted: out.afterRoundTrip.movedPos && out.afterRoundTrip.movedPos.x === before[0].x,
  };

  // B. 面包屑下拉的计数一致性
  const cd = st.getState().canvasData;
  out.breadcrumbCounts = Object.fromEntries(Object.entries(cd).map(([k, v]) => [k, (v.nodes || []).length]));
  out.currentLiveCount = st.getState().nodes.length;
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
        print("=== canvasData persistence probe ===")
        print(json.dumps(res, ensure_ascii=False, indent=2)[:3000])
        browser.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
