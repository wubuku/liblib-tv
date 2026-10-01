#!/usr/bin/env python3
"""Batch 331 探针（续）：跨画布撤销对 canvasData 的实际污染。

上一探针证明：画布 A 切到画布 B 后按撤销，A 的 7 个节点被灌进 B。
本探针确认**持久化层**也被污染 —— 切回 A 时数据是否已丢失/串味。
"""

import json

from playwright.sync_api import sync_playwright

URL = "http://localhost:4317/frameos/canvas/demo"

PROBE_JS = """
() => {
  const st = window.__frameos_store;
  const key = () => `${st.getState().breadcrumb.project}/${st.getState().breadcrumb.scene}/${st.getState().breadcrumb.canvas}`;
  const dump = () => {
    const cd = st.getState().canvasData || {};
    return Object.fromEntries(Object.entries(cd).map(([k, v]) => [k, (v.nodes || []).map((n) => n.id)]));
  };
  const out = {};

  const aKey = key();
  const aIds0 = st.getState().nodes.map((n) => n.id);
  const bKey = Object.keys(st.getState().canvasData).find((k) => k !== aKey);
  out.start = { aKey, aIds: aIds0, canvasData: dump() };

  // 关键前置：在 A 上先做一个可撤销动作，**制造一条 past 快照**。
  // 没有 past 时 undo 是 no-op（也就不会污染）—— 上一版探针因此漏判。
  st.getState().addNode('text');
  out.afterAddOnA = { nodeCount: st.getState().nodes.length, pastDepth: st.getState().past.length };

  // 切到 B
  const [p, s, c] = bKey.split('/');
  st.getState().setBreadcrumb({ project: p, scene: s, canvas: c });
  const bIds0 = st.getState().nodes.map((n) => n.id);
  out.onB = { bKey, bIds: bIds0 };

  // 在 B 上按一次撤销 → A 的节点被灌入 B
  st.getState().undo();
  const bIdsAfterUndo = st.getState().nodes.map((n) => n.id);
  out.afterUndoOnB = { bIds: bIdsAfterUndo, count: bIdsAfterUndo.length };

  // 切回 A —— A 的原始数据是否还在？还是被覆盖了？
  const [p2, s2, c2] = aKey.split('/');
  st.getState().setBreadcrumb({ project: p2, scene: s2, canvas: c2 });
  const aIdsAfter = st.getState().nodes.map((n) => n.id);
  out.backOnA = { aIds: aIdsAfter, count: aIdsAfter.length, sameAsStart: JSON.stringify(aIdsAfter) === JSON.stringify(aIds0) };

  // canvasData 里两张画布现在各是什么
  out.canvasDataNow = dump();
  out.VERDICT = (() => {
    const cd = st.getState().canvasData;
    const b = cd[bKey] ? (cd[bKey].nodes || []).map((n) => n.id) : null;
    if (!b) return 'B-missing';
    if (b.length > bIds0.length) return `B-POLLUTED: ${b.length} nodes (started ${bIds0.length})`;
    return 'B-clean';
  })();
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
        print("=== cross-canvas undo pollution ===")
        print(json.dumps(res, ensure_ascii=False, indent=2)[:3000])
        browser.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
