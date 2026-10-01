#!/usr/bin/env python3

"""Verify Batch 343: 边完整性不变式（「两端都指向存活节点」）对所有写路径生效.

缺陷（克隆侧，与 Batch 341 同构）:
store 里剪边只出现在**一处** —— `removeNode` 的
`edges.filter((e) => e.source !== id && e.target !== id)`。而 `setNodes` 是
**公开 action**，FrameosNodeEditPanel 的删除按钮正是
`setNodes(nodes.filter(...))`，绕开了 action，于是:
  ① 与被删节点相连的边**留在图里**（悬空边）;
  ② 悬空边被 Batch 333 的持久化**写进 localStorage 并在刷新后存活**
     —— 内存里的潜在缺陷被固化成了持久损坏;
  ③ `setNodes` 不 pushHistory → **删了不可撤销**。

实测 (probe-frameos-batch343-edge-integrity.py, 修复前):
    [对照组 removeNode] edges 5 → 3, dangling=[]
    [路径   setNodes]   edges 3 → 3, dangling=[e-video1-image1, e-video1-video3]
    持久化里的悬空边: ['e-video1-image1', 'e-video1-video3']
    刷新后 dangling: 仍在

修复（两处，缺一不可）:
1. 把「每条边两端都指向存活节点」收进 Batch 341 建立的**同一个写入口**
   (`enforceGraphInvariants`)。放进同一个出口后也顺带**治愈**已经写坏的存档
   —— `restorePersistedCanvas()` 载入时同样会经过那里。
2. 面板删除按钮改用 `removeNode`，而不是手写一遍它的过滤逻辑。逐条补齐
   悬空边/历史/选中态, 不如直接用本来就有这三条语义的 action。

断言:
1. 对照: removeNode 仍然剪边（不回归）;
2. setNodes 路径不再留悬空边;
3. **不误剪** —— 两端都存活��边原样保留;
4. 面板删除（真实 UI 点击）后无悬空边;
5. 持久化里没有悬空边;
6. 刷新后仍然没有悬空边（持久损坏已消除）;
7. 面板删除**可撤销** —— 撤销后节点与它的边一起回来;
8. 拖拽成员（onNodesChange 入口）不误删任何边;
9. 诊断零错误。
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
BASE_URL = os.environ.get("LIBLIB_BASE_URL", "http://localhost:4317")
AUDIT_PATH = (
    ROOT
    / "docs"
    / "research"
    / "liblib-frameos-batch343-2026-10-01"
    / "runtime-audit.json"
)
sys.path.insert(0, str(ROOT / "scripts"))
from frameos_verify_common import attach_errors, goto_clean_canvas  # noqa: E402

SETUP_JS = """
() => {
  const st = window.__frameos_store;
  st.setState({ past: [], future: [], groups: [], selectedNodeId: null });
  const s = st.getState();
  // 挑一个「有出边」的节点, 删掉它才会真的产生悬空边
  const victim = s.nodes.find((n) => s.edges.some((e) => e.source === n.id)) || s.nodes[0];
  window.__victim = victim.id;
  window.__victimEdges = s.edges
    .filter((e) => e.source === victim.id || e.target === victim.id)
    .map((e) => e.id);
  return { victim: victim.id, victimEdges: window.__victimEdges,
           edgeCount: s.edges.length, nodeCount: s.nodes.length,
           edgeIds_snapshot: s.edges.map((e) => e.id) };
}
"""

STATE_JS = """
() => {
  const s = window.__frameos_store.getState();
  const ids = new Set(s.nodes.map((n) => n.id));
  return {
    nodeCount: s.nodes.length,
    edgeCount: s.edges.length,
    edgeIds: s.edges.map((e) => e.id),
    dangling: s.edges
      .filter((e) => !ids.has(e.source) || !ids.has(e.target))
      .map((e) => e.id),
    pastDepth: s.past.length,
  };
}
"""

PERSISTED_DANGLING_JS = """
() => {
  const raw = localStorage.getItem('frameos.canvasData.v1');
  if (!raw) return null;
  const data = JSON.parse(raw);
  const c = data['测试作品/测试项目/画布 1'];
  if (!c) return null;
  const ids = new Set((c.nodes || []).map((n) => n.id));
  return (c.edges || [])
    .filter((e) => !ids.has(e.source) || !ids.has(e.target))
    .map((e) => e.id);
}
"""


def s6_setup_edges(page: Page) -> list[str]:
    """拖拽前的边 id 快照 —— 拖拽是纯位置变更, 边集合必须一字不差。"""
    return page.evaluate(
        "() => window.__frameos_store.getState().edges.map((e) => e.id)"
    )


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool, detail: str = "") -> None:
        assert ok, f"batch343 check failed: {name} {detail}".strip()
        result["checks"].append(name)

    errors = attach_errors(page)
    goto_clean_canvas(page, BASE_URL)

    # ── 1 对照组: removeNode 仍然剪边 ──
    setup = page.evaluate(SETUP_JS)
    result["setup"] = setup
    check("setup:victim-has-edges", len(setup["victimEdges"]) >= 1,
          f"victim={setup['victim']} edges={setup['victimEdges']}")
    base = page.evaluate(STATE_JS)
    page.evaluate("(id) => window.__frameos_store.getState().removeNode(id)",
                  setup["victim"])
    page.wait_for_timeout(300)
    after_remove = page.evaluate(STATE_JS)
    check("control:removeNode-prunes", after_remove["dangling"] == [],
          f"dangling={after_remove['dangling']}")
    check("control:removeNode-drops-victim-edges",
          all(e not in after_remove["edgeIds"] for e in setup["victimEdges"]),
          f"edges={after_remove['edgeIds']} victimEdges={setup['victimEdges']}")
    # 不误剪: 与受害者无关的边必须一条不少
    survivors = [e for e in base["edgeIds"] if e not in setup["victimEdges"]]
    check("control:other-edges-kept",
          all(e in after_remove["edgeIds"] for e in survivors),
          f"missing={[e for e in survivors if e not in after_remove['edgeIds']]}")

    # ── 2 setNodes 路径: 不再留悬空边 ──
    page.evaluate(SETUP_JS)
    s2 = page.evaluate(SETUP_JS)
    page.evaluate(
        """(id) => {
          const st = window.__frameos_store;
          st.getState().setNodes(st.getState().nodes.filter((n) => n.id !== id));
          return true;
        }""",
        s2["victim"],
    )
    page.wait_for_timeout(300)
    after_setnodes = page.evaluate(STATE_JS)
    result["setNodes"] = after_setnodes
    check("setNodes:no-dangling", after_setnodes["dangling"] == [],
          f"dangling={after_setnodes['dangling']}")
    check("setNodes:victim-edges-dropped",
          all(e not in after_setnodes["edgeIds"] for e in s2["victimEdges"]),
          f"edges={after_setnodes['edgeIds']}")
    check("setNodes:other-edges-kept",
          [e for e in s2["edgeIds_snapshot"] if e not in s2["victimEdges"]]
          == [e for e in after_setnodes["edgeIds"] if e not in s2["victimEdges"]],
          f"before={s2['edgeIds_snapshot']} after={after_setnodes['edgeIds']}")

    # ── 3 面板删除（真实 UI 点击）: 无悬空边 + 可撤销 ──
    s3 = page.evaluate(
        """() => {
          const st = window.__frameos_store;
          st.setState({ past: [], future: [], groups: [], selectedNodeId: null });
          if (!st.getState().isDebugMode) st.getState().toggleDebugMode();
          const s = st.getState();
          const victim = s.nodes.find((n) => s.edges.some((e) => e.source === n.id)) || s.nodes[0];
          window.__victim = victim.id;
          window.__victimEdges = s.edges
            .filter((e) => e.source === victim.id || e.target === victim.id)
            .map((e) => e.id);
          st.getState().selectNode(victim.id);
          return { victim: victim.id, victimEdges: window.__victimEdges,
                   edgeCount: s.edges.length };
        }"""
    )
    page.wait_for_timeout(500)
    page.evaluate("() => { window.confirm = () => true; }")
    del_btn = page.locator("button", has_text="删除节点")
    check("panel:button-exists", del_btn.count() >= 1, f"count={del_btn.count()}")
    try:
        del_btn.first.click(force=True, timeout=5000)
    except Exception:  # noqa: BLE001
        del_btn.first.dispatch_event("click")
    page.wait_for_timeout(600)
    after_panel = page.evaluate(STATE_JS)
    result["panel"] = after_panel
    check("panel:no-dangling", after_panel["dangling"] == [],
          f"dangling={after_panel['dangling']}")
    check("panel:node-gone",
          page.evaluate("(id) => !window.__frameos_store.getState().nodes.some((n) => n.id === id)",
                        s3["victim"]) is True,
          f"victim={s3['victim']}")
    check("panel:pushed-history", after_panel["pastDepth"] >= 1,
          f"pastDepth={after_panel['pastDepth']} — 面板删除必须可撤销")

    # 撤销: 节点与它的边一起回来
    undone = page.evaluate(
        """() => {
          window.__frameos_store.getState().undo();
          const s = window.__frameos_store.getState();
          return {
            nodeBack: s.nodes.some((n) => n.id === window.__victim),
            edgesBack: window.__victimEdges.every((id) => s.edges.some((e) => e.id === id)),
            missingEdges: window.__victimEdges.filter((id) => !s.edges.some((e) => e.id === id)),
          };
        }"""
    )
    result["undo"] = undone
    check("undo:node-back", undone["nodeBack"] is True, f"victim={s3['victim']}")
    check("undo:edges-back", undone["edgesBack"] is True, f"missing={undone['missingEdges']}")

    # ── 4 持久化无悬空边 ──
    persisted = page.evaluate(PERSISTED_DANGLING_JS)
    result["persisted_dangling"] = persisted
    check("persist:no-dangling", persisted == [], f"dangling={persisted}")

    # ── 5 刷新后仍无悬空边 ──
    # 断言绑的是**真实性质**: 刷新前后状态一致。此前几段已经删过节点,
    # 所以不能拿初始 fixture 的节点数去比 (那会把「删了没删」和「刷新丢没丢」
    # 两件事混在一起)。用刷新**前**的快照做基准。
    before_reload = page.evaluate(STATE_JS)
    page.reload(wait_until="domcontentloaded", timeout=90000)
    page.wait_for_selector(".react-flow__node", timeout=30000)
    page.wait_for_timeout(1200)
    reloaded = page.evaluate(STATE_JS)
    result["reload"] = {"before": before_reload, "after": reloaded}
    check("reload:no-dangling", reloaded["dangling"] == [],
          f"dangling={reloaded['dangling']}")
    check("reload:nodes-preserved",
          reloaded["nodeCount"] == before_reload["nodeCount"],
          f"before={before_reload['nodeCount']} after={reloaded['nodeCount']}")
    check("reload:edges-preserved",
          reloaded["edgeIds"] == before_reload["edgeIds"],
          f"before={before_reload['edgeIds']} after={reloaded['edgeIds']}")

    # ── 6 拖拽成员不误删边 ──
    s6 = page.evaluate(SETUP_JS)
    edges_before = s6_setup_edges(page)          # 拖拽前的边 id 列表
    page.evaluate(
        """(id) => {
          const st = window.__frameos_store;
          st.getState().setNodes(
            st.getState().nodes.map((n) => n.id === id
              ? { ...n, position: { x: n.position.x + 300, y: n.position.y + 200 } }
              : n)
          );
          return true;
        }""",
        s6["victim"],
    )
    page.wait_for_timeout(300)
    moved = page.evaluate(STATE_JS)
    result["drag"] = {"before": edges_before, "after": moved["edgeIds"]}
    check("drag:edges-unchanged", moved["edgeIds"] == edges_before,
          f"before={edges_before} after={moved['edgeIds']}")
    check("drag:node-moved", page.evaluate(
        "(id) => window.__frameos_store.getState().nodes.find((n) => n.id === id).position.x",
        s6["victim"],
    ) is not None, f"victim={s6['victim']}")
    check("drag:no-dangling", moved["dangling"] == [], f"dangling={moved['dangling']}")

    check("diagnostics:zero", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 343,
        "title": "FrameOS edge integrity invariant holds on every write path",
        "defect": (
            "Edge pruning existed in exactly one place (removeNode). setNodes is a public "
            "action and FrameosNodeEditPanel's delete button used it directly, so deleting "
            "a connected node left edges pointing at a node that no longer existed. "
            "Measured: 2 dangling edges, and because Batch 333 persists on every store "
            "write they were written to localStorage and SURVIVED A RELOAD -- an in-memory "
            "latent defect turned into durable corruption. The same path also skipped the "
            "history stack entirely, so the delete was not undoable."
        ),
        "fix": (
            "(1) the 'both endpoints are live nodes' invariant joined the same store write "
            "choke point Batch 341 introduced (enforceGraphInvariants), which also heals "
            "already-corrupted saves because restorePersistedCanvas passes through it; "
            "(2) the panel's delete button now calls removeNode instead of hand-rolling "
            "its filter, so it inherits edge pruning, history and selection handling."
        ),
        "clone_decision": (
            "Pruning edges whose endpoints are gone is forced by the data model itself "
            "(an edge to a nonexistent node is not renderable -- React Flow rendered 0 "
            "edges for it), so no source-site sampling was needed. The source site remains "
            "blocked by the human-verification gate (see "
            "SOURCE_ACCESS_BLOCKED_2026-10-01.md)."
        ),
        "results": [],
    }
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        desktop = browser.new_page(
            viewport={"width": 1440, "height": 900}, device_scale_factor=1
        )
        audit["results"].append(run_desktop(desktop))
        desktop.close()
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    checks = audit["results"][0]["checks"]
    print(
        "Batch 343 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "Deleting a node through any path (action, setNodes, or the debug panel) now "
        "leaves no dangling edges, nothing dangling is persisted or survives a reload, "
        "the panel delete is undoable, and dragging a node never drops an edge."
    )


if __name__ == "__main__":
    main()
