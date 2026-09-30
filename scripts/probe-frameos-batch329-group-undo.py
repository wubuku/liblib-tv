#!/usr/bin/env python3
"""Batch 329 探针：分组与撤销历史的一致性。

疑点（克隆侧，不依赖源站）：
  A. createGroup 不入历史栈 → 撤销成组动作不恢复分组；
  B. removeNode 会改动 groups（Batch 328 的 reconcileGroups），但历史快照
     只存 {nodes, edges} → 撤销「删除分组成员」时，节点回来了、分组却停在
     删除后的收敛状态（成员少一个），**分组与节点不一致**；
  C. ungroup 同样不入栈 → 撤销解组不解组。

用法: ~/.venvs/liblib-harness/bin/python scripts/probe-frameos-batch329-group-undo.py
"""

import json

from playwright.sync_api import sync_playwright

URL = "http://localhost:4317/frameos/canvas/demo"

PROBE_JS = """
() => {
  const st = window.__frameos_store;
  const snap = () => ({
    nodes: st.getState().nodes.length,
    groups: st.getState().groups.map((g) => ({ id: g.id, memberIds: g.memberIds, box: {x:g.x,y:g.y,w:g.w,h:g.h} })),
    pastDepth: st.getState().past.length,
  });
  const out = {};

  // ── A: createGroup 是否入历史栈 ──
  const before = snap();
  const ids = st.getState().nodes.slice(0, 2).map((n) => n.id);
  const gid = st.getState().createGroup(ids);
  const afterCreate = snap();
  out.A_createGroup = {
    pastDepthBefore: before.pastDepth,
    pastDepthAfter: afterCreate.pastDepth,
    pushedToHistory: afterCreate.pastDepth > before.pastDepth,
    groupsAfter: afterCreate.groups.length,
  };

  // 撤销 → 分组是否还在
  st.getState().undo();
  out.A_afterUndo = { groups: snap().groups.length };

  // ── B: 删除分组成员后撤销，节点恢复但分组成员集是否同步 ──
  const g2 = st.getState().createGroup(st.getState().nodes.slice(0, 2).map((n) => n.id));
  const g = st.getState().groups.find((x) => x.id === g2);
  const victim = g.memberIds[0];
  st.getState().removeNode(victim);
  const afterDel = snap();
  st.getState().undo();
  const afterUndo = snap();
  out.B_deleteMemberUndo = {
    memberIdsAfterDelete: afterDel.groups.find((x) => x.id === g2)?.memberIds ?? null,
    nodeRestored: afterUndo.nodes,
    memberIdsAfterUndo: afterUndo.groups.find((x) => x.id === g2)?.memberIds ?? null,
    boxAfterUndo: afterUndo.groups.find((x) => x.id === g2)?.box ?? null,
    consistent: (() => {
      const gg = afterUndo.groups.find((x) => x.id === g2);
      if (!gg) return 'group-missing';
      const ids = new Set(st.getState().nodes.map((n) => n.id));
      const dangling = gg.memberIds.filter((m) => !ids.has(m));
      return dangling.length === 0 ? 'no-dangling' : 'DANGLING:' + JSON.stringify(dangling);
    })(),
  };

  // ── C: ungroup 是否入历史栈 ──
  const p0 = snap().pastDepth;
  st.getState().ungroup(g2);
  const p1 = snap().pastDepth;
  st.getState().undo();
  out.C_ungroup = { pushedToHistory: p1 > p0, groupsAfterUndo: snap().groups.length };
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
        print("=== group/undo probe ===")
        print(json.dumps(res, ensure_ascii=False, indent=2))
        browser.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
