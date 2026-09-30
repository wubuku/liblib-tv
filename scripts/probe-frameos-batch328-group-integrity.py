#!/usr/bin/env python3
"""Batch 328 缺陷探针：删除分组成员后的分组完整性。

待验证的两个克隆侧疑点（均不依赖源站）：
  A. removeNode 不清理 groups[].memberIds → 悬空成员引用；
     分组盒 x/y/w/h 不重算 → 删掉成员后分组盒仍是旧几何。
  B. undo/redo 历史快照只存 {nodes, edges}，不含 groups →
     撤销不会恢复分组状态。

用法: ~/.venvs/liblib-harness/bin/python scripts/probe-frameos-batch328-group-integrity.py
"""

import json

from playwright.sync_api import sync_playwright

URL = "http://localhost:4317/frameos/canvas/demo"

PROBE_JS = """
() => {
  const st = window.__frameos_store;
  const out = {};

  // 造一个 2 成员分组（用真实 action，贴近用户路径）
  const ids = st.getState().nodes.slice(0, 2).map((n) => n.id);
  const gid = st.getState().createGroup(ids);
  const g0 = st.getState().groups.find((g) => g.id === gid);
  out.A_created = { groupId: gid, memberIds: g0?.memberIds ?? null, box: g0 ? {x:g0.x,y:g0.y,w:g0.w,h:g0.h} : null };

  // 删掉其中一个成员
  const victim = g0.memberIds[0];
  const survivor = g0.memberIds[1];
  st.getState().removeNode(victim);
  const g1 = st.getState().groups.find((g) => g.id === gid);
  out.B_afterRemove = {
    memberIds: g1?.memberIds ?? null,
    dangling: g1 ? g1.memberIds.filter((m) => !st.getState().nodes.some((n) => n.id === m)) : null,
    box: g1 ? {x:g1.x,y:g1.y,w:g1.w,h:g1.h} : null,
    boxUnchanged: g1 ? (g1.x === g0.x && g1.y === g0.y && g1.w === g0.w && g1.h === g0.h) : null,
    liveMembers: g1 ? g1.memberIds.filter((m) => st.getState().nodes.some((n) => n.id === m)) : null,
  };

  // DOM 上分组覆盖层还剩几个
  out.C_domGroups = document.querySelectorAll('.canvas-group').length;

  // 撤销能否恢复节点
  st.getState().undo();
  out.D_afterUndo = {
    nodeRestored: st.getState().nodes.some((n) => n.id === victim),
    groupStillThere: st.getState().groups.some((g) => g.id === gid),
    groupMemberIds: st.getState().groups.find((g) => g.id === gid)?.memberIds ?? null,
  };

  // 排列表：对只剩 1 个活成员的分组做水平排列是否还工作
  const g2 = st.getState().groups.find((g) => g.id === gid);
  if (g2) {
    st.getState().arrangeGroup(gid, 'horizontal');
    const g3 = st.getState().groups.find((g) => g.id === gid);
    out.E_arrange = { ok: true, box: g3 ? {x:g3.x,y:g3.y,w:g3.w,h:g3.h} : null };
  }
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
        print("=== group integrity probe ===")
        print(json.dumps(res, ensure_ascii=False, indent=2))
        browser.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
