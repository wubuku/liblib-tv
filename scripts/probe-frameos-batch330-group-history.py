#!/usr/bin/env python3
"""Batch 330 探针：分组动作的可撤销覆盖。

Batch 329 后仍不入历史栈的分组动作：
  renameGroup / setGroupColor / moveGroup
（arrangeGroup / createGroup / ungroup 已覆盖）

用法: ~/.venvs/liblib-harness/bin/python scripts/probe-frameos-batch330-group-history.py
"""

import json

from playwright.sync_api import sync_playwright

URL = "http://localhost:4317/frameos/canvas/demo"

PROBE_JS = """
() => {
  const st = window.__frameos_store;
  const out = {};
  // ensure() 可能重建分组并返回**新** id；后续动作必须用新 id，
  // 否则 setGroupColor/moveGroup 会作用在不存在的分组上（静默 no-op）。
  const ensure = () => {
    const existing = st.getState().groups.find((g) => g.memberIds.length === 3);
    if (existing) return existing.id;
    st.setState((s) => ({ past: s.past.slice(0, -1), future: [] }));
    return st.getState().createGroup(st.getState().nodes.slice(0, 3).map((n) => n.id));
  };
  const snap = (id) => {
    const g = st.getState().groups.find((x) => x.id === id);
    return g ? { name: g.name, color: g.color, x: g.x, y: g.y, members: g.memberIds.length } : null;
  };

  const probe = (label, action) => {
    const gid = ensure();
    const d0 = st.getState().past.length;
    const before = JSON.stringify(snap(gid));
    action(gid);
    const d1 = st.getState().past.length;
    const after = JSON.stringify(snap(gid));
    st.getState().undo();
    const undone = JSON.stringify(snap(gid));
    return { changedState: before !== after, pushed: d1 > d0,
             undoRestores: before === undone,
             before: JSON.parse(before), after: JSON.parse(after),
             undone: JSON.parse(undone) };
  };

  out.rename = probe('rename', (g) => st.getState().renameGroup(g, '探测组B'));
  out.color  = probe('color',  (g) => st.getState().setGroupColor(g, '#ff0000'));
  out.move   = probe('move',   (g) => st.getState().moveGroup(g, 60, 40));
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
        print("=== group history coverage ===")
        print(json.dumps(res, ensure_ascii=False, indent=2))
        browser.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
