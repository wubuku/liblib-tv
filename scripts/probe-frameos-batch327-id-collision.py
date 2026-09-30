#!/usr/bin/env python3
"""Batch 327 缺陷复现探针：duplicateNode / pasteNodeFromClipboard 的节点 id
碰撞（裸 Date.now()，同毫秒内两次操作产生相同 id）。

先在页面上做只读式探测（不改业务代码），确认 id 碰撞真实存在。
Run: ~/.venvs/liblib-harness/bin/python scripts/probe-frameos-batch327-id-collision.py
"""

import json

from playwright.sync_api import sync_playwright

BASE = "http://localhost:4317"
URL = f"{BASE}/frameos/canvas/demo"

# 在同一 JS tick 内连续触发两次「复制」与两次「粘贴」，观察 nodes 数组里
# 出现了多少个重复 id。duplicateNode / pasteNodeFromClipboard 各自用裸
# Date.now() 生成 id —— 同一毫秒内两次调用必然相同。
PROBE_JS = """
() => {
  const st = window.__frameos_store;
  if (!st) return { error: 'no store' };
  const before = st.getState().nodes.length;
  const target = st.getState().nodes[0];
  if (!target) return { error: 'no nodes' };

  // 同一 tick 内连续 duplicateNode 两次
  st.getState().duplicateNode(target.id);
  st.getState().duplicateNode(target.id);
  const afterDup = st.getState().nodes;
  const dupIds = afterDup.map((n) => n.id);
  const dupCollisions = dupIds.filter((id, i) => dupIds.indexOf(id) !== i);

  const dupResult = {
    added: afterDup.length - before,
    uniqueIds: new Set(dupIds).size,
    totalIds: dupIds.length,
    collisions: [...new Set(dupCollisions)],
  };

  // 复制 + 同一 tick 内连续粘贴两次
  st.getState().copyNodeToClipboard(target.id);
  st.getState().pasteNodeFromClipboard();
  st.getState().pasteNodeFromClipboard();
  const pasteIds = st.getState().nodes.map((n) => n.id);
  const pasteCollisions = pasteIds.filter((id, i) => pasteIds.indexOf(id) !== i);

  return {
    duplicate: dupResult,
    paste: {
      uniqueIds: new Set(pasteIds).size,
      totalIds: pasteIds.length,
      collisions: [...new Set(pasteCollisions)],
    },
  };
}
"""

# 对照组：addNode 已有计数器，同 tick 两次建节点不应碰撞
PROBE_ADDNODE_JS = """
() => {
  const st = window.__frameos_store;
  const before = st.getState().nodes.length;
  st.getState().addNode('text');
  st.getState().addNode('text');
  const ids = st.getState().nodes.map((n) => n.id);
  return {
    added: st.getState().nodes.length - before,
    uniqueIds: new Set(ids).size,
    totalIds: ids.length,
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

        addnode = page.evaluate(PROBE_ADDNODE_JS)
        print("=== addNode (has counter, expected control) ===")
        print(json.dumps(addnode, ensure_ascii=False))

        result = page.evaluate(PROBE_JS)
        print("=== duplicateNode / pasteNodeFromClipboard (bare Date.now()) ===")
        print(json.dumps(result, ensure_ascii=False, indent=2))

        # 渲染侧后果：碰撞 id 在 DOM 里只渲染出一个节点
        page.wait_for_timeout(600)
        dom = page.evaluate(
            "() => { const ns=[...document.querySelectorAll('.react-flow__node')];"
            "const ids=ns.map(n=>n.getAttribute('data-id'));"
            "return { domNodes: ns.length, uniqueDomIds: new Set(ids).size, ids }; }"
        )
        print("=== DOM after collision ===")
        print(json.dumps({k: v for k, v in dom.items() if k != "ids"}, ensure_ascii=False))
        browser.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
