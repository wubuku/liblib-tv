#!/usr/bin/env python3
"""Batch 340 探针：组内复制副本的分组归属（dup 落在组盒内但不是成员）。

疑点（克隆侧，不依赖源站）:
  `duplicateNode`（⌘D / 创建副本）产生的副本**不加入**源节点所在分组
  （memberIds 不变），但副本位置 = 源位置 + (40,40) —— 若源节点靠近分组
  盒边缘，副本会**落在分组盒内**，看起来「在组里」，实际不是成员。
  后果：删掉其余成员后分组盒按存活成员重算（Batch 328），那个「看起来在组里」
  的副本被排除在盒外 → 用户看到组里空了一块，或副本与盒重叠错位。

本探针只测**克隆自身的一致性**（副本位置 与 分组归属是否自洽），
不声称源站如何处理（源站阻塞，见 SOURCE_ACCESS_BLOCKED_2026-10-01.md）。

用法: ~/.venvs/liblib-harness/bin/python scripts/probe-frameos-batch340-dup-group.py
"""

import json

from playwright.sync_api import sync_playwright

URL = "http://localhost:4317/frameos/canvas/demo"

PROBE_JS = """
() => {
  const st = window.__frameos_store;
  st.setState({ past: [], future: [], groups: [] });
  const ids = st.getState().nodes.slice(0, 2).map((n) => n.id);
  const gid = st.getState().createGroup(ids);
  const g0 = st.getState().groups.find((g) => g.id === gid);
  const member = g0.memberIds[0];

  st.getState().duplicateNode(member);
  const dupId = st.getState().nodes[st.getState().nodes.length - 1].id;
  const g1 = st.getState().groups.find((g) => g.id === gid);
  const dup = st.getState().nodes.find((n) => n.id === dupId);
  const src = st.getState().nodes.find((n) => n.id === member);

  const box = { x: g1.x, y: g1.y, w: g1.w, h: g1.h };
  const inside = (n) =>
    n.position.x >= box.x && n.position.x <= box.x + box.w &&
    n.position.y >= box.y && n.position.y <= box.y + box.h;

  // 删掉被复制的那个成员（副本若真在组里，盒应因它而保留/扩张）
  st.getState().removeNode(member);
  const g2 = st.getState().groups.find((g) => g.id === gid);
  const box2 = g2 ? { x: g2.x, y: g2.y, w: g2.w, h: g2.h } : null;
  const dup2 = st.getState().nodes.find((n) => n.id === dupId);

  return {
    groupMembersBeforeDup: g0.memberIds,
    groupMembersAfterDup: g1.memberIds,
    dupJoinedGroup: g1.memberIds.includes(dupId),
    dupInsideBoxBefore: inside(dup),
    dupPos: dup.position,
    srcPos: src.position,
    boxBefore: box,
    groupMembersAfterDelete: g2 ? g2.memberIds : null,
    boxAfter: box2,
    dupInsideBoxAfter: box2 ? inside(dup2) : null,
    // 判定：副本在盒内但不是成员 → 归属与视觉不一致
    INCONSISTENT: inside(dup) && !g1.memberIds.includes(dupId),
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
        res = page.evaluate(PROBE_JS)
        print("=== dup-in-group consistency probe ===")
        print(json.dumps(res, ensure_ascii=False, indent=2))
        browser.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
