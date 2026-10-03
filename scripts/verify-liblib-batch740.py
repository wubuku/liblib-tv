#!/usr/bin/env python3
"""batch 740 验收：删连线的两条路径与历史栈对账

## 起点

739 测出「聚焦手柄按 Enter 真删一条边」，但没问**删掉的东西能不能撤**。
本批把两条删除路径与历史栈逐项对账。

## 两条路径（源码）

  ① 手柄 → `DeletableEdge.tsx:87` `window.dispatchEvent(new CustomEvent("delete-edge", {detail:{id}}))`
     → `page.tsx:1428-1435` 的 window 监听 → `canvasStore.removeEdge(id)`
     → `canvasStore.ts:3668` `historyByCanvas: pushHistory(state.historyByCanvas, currentCanvas)`
  ② Delete 键 → `page.tsx:1322-1329` `removeSelectedNodes(ids)`（删节点，连带删它的边）

`undo()`（`canvasStore.ts:3673`）恢复 `previous.nodes/edges`，
并**清空三个选区字段**（源码写明：`selectedNodeIds: []`、`selectedNodeId: null`、`selectedEdgeIds: []`）。

## 决定性读数

### ① 两条路径**都**进历史栈，各 push 1 条
| 路径 | 节点 | 边 | `past` |
|---|---|---|---|
| 起点 | 10 | 11 | 0 |
| ① 手柄删边 | 10 → **10（不变）** | 11 → **10** | 0 → **1**（快照含 11 条边） |
| ② Delete 删节点 | 10 → **9** | 11 → **10**（连带 1 条） | 0 → **1** |

### ② undo / redo **逐项精确**（不是只看数量）
- 路径① undo 后：边集与节点集**逐项等于起点**（`True` / `True`）；redo 后逐项等于删除后（`True`）
- 路径② undo 后：同样逐项精确（`True` / `True`）
- 手柄删的**只有那一条边**：`onlyBefore: ["e-AQmdIgKtl2"]`、节点差异为空

### ③ **undo 会清空选区** —— 实测确认源码写明的行为
| | undo 前 | undo 后 |
|---|---|---|
| 路径① | （手柄点击，不产生节点选区） | `selectedNodeIds=[]`、`selectedEdgeIds=[]` |
| 路径② | `selectedNodeIds=['g-245IDFh8sB']` | **`selectedNodeIds=[]`** |

⟹ **按 Delete 删掉一个刚选中的节点、撤销之后，那个节点不再被选中** ——
用户要重新点一次才能继续操作。

### ④ 刷新后历史栈归零（承 711「history 不入持久化」）
删除后 `past = 1` ⟹ 刷新 ⟹ `past = 0`、节点边回到种子 10/11。
`historyByCanvas` 是**内存里的分桶 Map**，不写 localStorage。

### ⑤ `historyByCanvas` 按画布分桶 ⟹ 切画布后 undo **不误伤另一张**
在 `canvas-2`（画布 2，默认激活）删一条边（`past[canvas-2] = 1`），
`setActiveCanvas('canvas-1')` 后调 `undo()` ⟹ **canvas-1 一条边都没变**（`canvases[0].edges` 前后相等），
且 canvas-2 的那条删除**没有被撤掉**（`undo` 是按当前画布取历史，canvas-1 的历史是空的 ⟹ 空操作）。

## 判据

C1  源码四处：派发 `delete-edge` / window 监听 / `removeEdge` 的 `pushHistory` / `undo` 清空选区
C2  路径①：手柄删边 ⟹ 边 11→10、**节点 10→10 不变**、`past` 0→1（快照含 11 条边）
C3  路径① undo/redo **逐项精确**
C4  路径① undo 后选区两个字段都空
C5  路径②：Delete 删节点 ⟹ 节点 10→9、连带边 1 条、`past` 0→1
C6  路径② undo 逐项精确，**且刚选中的节点被丢掉**
C7  删除后（`past = 1`）刷新 ⟹ `past = 0`、回到种子 10/11
C8  切到 canvas-1 后 `undo()` **不误伤 canvas-1**，也不撤掉 canvas-2 的删除
"""

import json
import re
import subprocess
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "docs/research/liblib-canvas-batch740-2026-10-01"
BASE = "http://localhost:4317"
W, H = 1280, 1150

SNAP = """() => {
  const s = window.__libtv_store.getState();
  const g = s.getActiveCanvas();
  const h = s.historyByCanvas ? (s.historyByCanvas[g.id] || {past: [], future: []}) : null;
  return {
    canvasId: g.id,
    nodes: g.nodes.map(n => n.id).sort(),
    edges: g.edges.map(e => e.id).sort(),
    edgeCount: g.edges.length, nodeCount: g.nodes.length,
    past: h ? h.past.length : null, future: h ? h.future.length : null,
    pastEdgeCounts: h ? h.past.map(p => p.edges.length) : null,
    selectedNodeIds: s.selectedNodeIds.slice(), selectedEdgeIds: s.selectedEdgeIds.slice(),
    allCanvases: s.canvases.map(c => ({id: c.id, name: c.name, edges: c.edges.length,
                                       nodes: c.nodes.length,
                                       edgeIds: c.edges.map(e => e.id).sort()})),
    pastPerCanvas: s.historyByCanvas ? Object.fromEntries(
      Object.entries(s.historyByCanvas).map(([k, v]) => [k, (v.past || []).length])) : null,
  };
}"""

CURVE_POINTS = """() => {
  const out = [];
  for (const p of document.querySelectorAll('path')) {
    const cs = getComputedStyle(p);
    if (!(cs.stroke === 'rgba(0, 0, 0, 0)' || cs.stroke === 'transparent')) continue;
    if (cs.strokeWidth !== '20px') continue;
    const len = p.getTotalLength(); if (!len) continue;
    const pt = p.getPointAtLength(len / 2); const m = p.getScreenCTM(); if (!m) continue;
    const sx = pt.x * m.a + pt.y * m.c + m.e, sy = pt.x * m.b + pt.y * m.d + m.f;
    if (sx > 4 && sy > 4 && sx < innerWidth - 4 && sy < innerHeight - 4)
      out.push({sx: Math.round(sx), sy: Math.round(sy)});
  }
  return out;
}"""


def static_lines():
    edge = (ROOT / "src/components/nodes/DeletableEdge.tsx").read_text(encoding="utf-8").split("\n")
    page = (ROOT / "src/app/page.tsx").read_text(encoding="utf-8").split("\n")
    store = (ROOT / "src/store/canvasStore.ts").read_text(encoding="utf-8").split("\n")
    # 注意：**不要让一个键承载两个含义**。第一版把 page.tsx 的 Delete 调用点
    # 与 store 里的 removeEdge 实现写进同一个 `removeEdge` 键，前者先命中
    # ⟹ 读到 1326 而不是 3656，判据因此连挂两轮。
    out = {"dispatch": None, "listener": None, "keyDeleteCall": None,
           "removeEdgeImpl": None, "pushInRemoveEdge": None,
           "undo": None, "undoClearsSelection": False}
    for n, line in enumerate(edge, start=1):
        if 'new CustomEvent("delete-edge"' in line and out["dispatch"] is None:
            out["dispatch"] = n
    for n, line in enumerate(page, start=1):
        if 'window.addEventListener("delete-edge"' in line and out["listener"] is None:
            out["listener"] = n
        if "removeSelectedNodes(" in line and out["keyDeleteCall"] is None:
            out["keyDeleteCall"] = n
    hit = False
    for n, line in enumerate(store, start=1):
        # 注意：401 行是**接口声明** `removeEdge: (edgeId: string) => void;`，
        # 只认实现（以 `=> {` 结尾的那一处），否则会把后面的 pushHistory 配错行。
        if line.strip().startswith("removeEdge: (edgeId: string) => {"):
            hit = True
            out["removeEdgeImpl"] = n
            continue
        if hit and out["pushInRemoveEdge"] is None and "pushHistory(" in line:
            out["pushInRemoveEdge"] = n
        if hit and line.strip() == "undo: () => {":
            out["undo"] = n
        if out["undo"] and n > out["undo"] + 20 and "selectedEdgeIds: []" in line:
            out["undoClearsSelection"] = True
    return out


def snap(page):
    return page.evaluate(SNAP)


def go(page, tag):
    page.goto(f"{BASE}/?batch740={tag}", wait_until="networkidle", timeout=90_000)
    page.wait_for_function("() => Boolean(window.__libtv_store)", timeout=60_000)
    page.evaluate("() => { for (const el of document.querySelectorAll('nextjs-portal')) el.remove(); }")
    page.wait_for_timeout(1_300)


def main() -> int:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)

    print("=== 静态：两条路径与历史栈的源码位置 ===")
    lines = static_lines()
    print(f"  dispatch delete-edge   DeletableEdge.tsx:{lines['dispatch']}")
    print(f"  window 监听            page.tsx:{lines['listener']}")
    print(f"  Delete → removeSelectedNodes  page.tsx:{lines['keyDeleteCall']}")
    print(f"  removeEdge 实现 / pushHistory  canvasStore.ts:{lines['removeEdgeImpl']} / :{lines['pushInRemoveEdge']}")
    print(f"  undo 定义 :{lines['undo']}；undo 里清空选区 = {lines['undoClearsSelection']}")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": W, "height": H})

        # ---------- 路径①：手柄删边 ----------
        go(page, "handle")
        s0 = snap(page)
        print(f"\n=== 路径① 手柄删边（起点 节点 {s0['nodeCount']} / 边 {s0['edgeCount']} / past {s0['past']}）===")
        active = None
        for pt in page.evaluate(CURVE_POINTS):
            page.mouse.move(pt["sx"], pt["sy"])
            page.wait_for_timeout(500)
            hit = page.evaluate("""() => { const el = [...document.querySelectorAll('button[data-edge-delete]')]
              .find(e => getComputedStyle(e).pointerEvents !== 'none');
              if (!el) return null; const r = el.getBoundingClientRect();
              return {x: Math.round(r.x + r.width/2), y: Math.round(r.y + r.height/2)}; }""")
            if hit:
                active = hit
                break
        page.mouse.click(active["x"], active["y"])
        page.wait_for_timeout(700)
        s1 = snap(page)
        print(f"  删后：边 {s1['edgeCount']}、节点 {s1['nodeCount']}；past {s0['past']}→{s1['past']}"
              f"（快照边数 {s1['pastEdgeCounts']}）")
        print(f"  只少了一条边: {sorted(set(s0['edges']) - set(s1['edges']))}；节点差异 "
              f"{sorted(set(s0['nodes']) ^ set(s1['nodes']))}")
        page.evaluate("() => window.__libtv_store.getState().undo()")
        page.wait_for_timeout(600)
        s2 = snap(page)
        print(f"  undo：边 {s2['edgeCount']}、节点 {s2['nodeCount']}；past {s2['past']}、future {s2['future']}")
        print(f"  逐项精确回起点: 边 {s2['edges'] == s0['edges']} 节点 {s2['nodes'] == s0['nodes']}；"
              f"undo 后选区 node={s2['selectedNodeIds']} edge={s2['selectedEdgeIds']}")
        page.evaluate("() => window.__libtv_store.getState().redo()")
        page.wait_for_timeout(600)
        s3 = snap(page)
        print(f"  redo：边 {s3['edgeCount']}；逐项精确回删除后 {s3['edges'] == s1['edges']}")

        # ---------- 路径②：Delete 删节点 ----------
        go(page, "key")
        t0 = snap(page)
        picked = page.evaluate("""() => { const n = document.querySelector('.react-flow__node');
          if (!n) return 'NONE';
          n.dispatchEvent(new MouseEvent('mousedown', {bubbles:true, clientX:0, clientY:0}));
          n.dispatchEvent(new MouseEvent('mouseup', {bubbles:true, clientX:0, clientY:0}));
          n.click(); return n.getAttribute('data-id'); }""")
        page.wait_for_timeout(700)
        t1 = snap(page)
        page.keyboard.press("Delete")
        page.wait_for_timeout(700)
        t2 = snap(page)
        print(f"\n=== 路径② Delete 删节点（选中 {picked}）===")
        print(f"  删后：节点 {t1['nodeCount']}→{t2['nodeCount']}、边 {t1['edgeCount']}→{t2['edgeCount']}"
              f"（连带 {t1['edgeCount'] - t2['edgeCount']} 条）；past {t1['past']}→{t2['past']}")
        page.evaluate("() => window.__libtv_store.getState().undo()")
        page.wait_for_timeout(600)
        t3 = snap(page)
        print(f"  undo：节点 {t3['nodeCount']}、边 {t3['edgeCount']}；"
              f"逐项精确 节点 {t3['nodes'] == t1['nodes']} 边 {t3['edges'] == t1['edges']}")
        print(f"  **undo 前选中的节点**: {t1['selectedNodeIds']} → undo 后 {t3['selectedNodeIds']}")

        # ---------- 切画布后 undo 会不会误伤 ----------
        go(page, "bucket")
        u0 = snap(page)
        for pt in page.evaluate(CURVE_POINTS):
            page.mouse.move(pt["sx"], pt["sy"])
            page.wait_for_timeout(500)
            hit = page.evaluate("""() => { const el = [...document.querySelectorAll('button[data-edge-delete]')]
              .find(e => getComputedStyle(e).pointerEvents !== 'none');
              if (!el) return null; const r = el.getBoundingClientRect();
              return {x: Math.round(r.x + r.width/2), y: Math.round(r.y + r.height/2)}; }""")
            if hit:
                page.mouse.click(hit["x"], hit["y"])
                break
        page.wait_for_timeout(700)
        u1 = snap(page)
        other = [c for c in u1["allCanvases"] if c["id"] != u1["canvasId"]][0]
        other_before = dict(other)
        page.evaluate("""(id) => window.__libtv_store.getState().setActiveCanvas(id)""", other["id"])
        page.wait_for_timeout(700)
        page.evaluate("() => window.__libtv_store.getState().undo()")
        page.wait_for_timeout(600)
        u2 = snap(page)
        other_after = [c for c in u2["allCanvases"] if c["id"] == other["id"]][0]
        print(f"\n=== 切画布后 undo（分桶检验）===")
        print(f"  在 {u1['canvasId']} 删边后 pastPerCanvas={json.dumps(u1['pastPerCanvas'], ensure_ascii=False)}")
        print(f"  切到 {other['id']}（{other['name']}）调 undo()：")
        print(f"    该画布边数 {other_before['edges']} → {other_after['edges']}（边集相等="
              f"{other_before['edgeIds'] == other_after['edgeIds']}）")
        print(f"    canvas-2 的删除还在吗：边 {u1['edgeCount']} → "
              f"{[c for c in u2['allCanvases'] if c['id'] == u1['canvasId']][0]['edges']}")

        # ---------- 刷新：必须在 past > 0 时做 ----------
        page.evaluate("""(id) => window.__libtv_store.getState().setActiveCanvas(id)""", u1["canvasId"])
        page.wait_for_timeout(500)
        for pt in page.evaluate(CURVE_POINTS):
            page.mouse.move(pt["sx"], pt["sy"])
            page.wait_for_timeout(500)
            hit = page.evaluate("""() => { const el = [...document.querySelectorAll('button[data-edge-delete]')]
              .find(e => getComputedStyle(e).pointerEvents !== 'none');
              if (!el) return null; const r = el.getBoundingClientRect();
              return {x: Math.round(r.x + r.width/2), y: Math.round(r.y + r.height/2)}; }""")
            if hit:
                page.mouse.click(hit["x"], hit["y"])
                break
        page.wait_for_timeout(700)
        r0 = snap(page)
        print(f"\n=== 刷新（先确认 past > 0：{r0['past']}）===")
        page.reload(wait_until="networkidle")
        page.wait_for_function("() => Boolean(window.__libtv_store)", timeout=60_000)
        page.wait_for_timeout(1_000)
        r1 = snap(page)
        print(f"  刷新前：节点 {r0['nodeCount']} / 边 {r0['edgeCount']} / past {r0['past']}")
        print(f"  刷新后：节点 {r1['nodeCount']} / 边 {r1['edgeCount']} / past {r1['past']}")

        page.close()
        browser.close()

    summary = {
        "staticLines": lines,
        "h0nodes": s0["nodeCount"], "h0edges": s0["edgeCount"], "h0past": s0["past"],
        "h1nodes": s1["nodeCount"], "h1edges": s1["edgeCount"], "h1past": s1["past"],
        "h1pastEdgeCounts": s1["pastEdgeCounts"],
        "handleOnlyOneEdge": sorted(set(s0["edges"]) - set(s1["edges"])),
        "handleNodesUnchanged": s0["nodeCount"] == s1["nodeCount"] and s0["nodes"] == s1["nodes"],
        "undoEdgesExact": s2["edges"] == s0["edges"], "undoNodesExact": s2["nodes"] == s0["nodes"],
        "undoFuture": s2["future"],
        "undoSelNode": s2["selectedNodeIds"], "undoSelEdge": s2["selectedEdgeIds"],
        "redoEdgesExact": s3["edges"] == s1["edges"],
        "keyPicked": picked,
        "k1nodes": t1["nodeCount"], "k1edges": t1["edgeCount"], "k1past": t1["past"],
        "k2nodes": t2["nodeCount"], "k2edges": t2["edgeCount"], "k2past": t2["past"],
        "keyCascadeEdges": t1["edgeCount"] - t2["edgeCount"],
        "keyUndoNodesExact": t3["nodes"] == t1["nodes"], "keyUndoEdgesExact": t3["edges"] == t1["edges"],
        "selBeforeUndo": t1["selectedNodeIds"], "selAfterUndo": t3["selectedNodeIds"],
        "bucketActive": u1["canvasId"], "bucketPastPerCanvas": u1["pastPerCanvas"],
        "otherCanvasEdgesBefore": other_before["edges"], "otherCanvasEdgesAfter": other_after["edges"],
        "otherCanvasExact": other_before["edgeIds"] == other_after["edgeIds"],
        "sourceEdgesAfterBucketUndo": [c for c in u2["allCanvases"] if c["id"] == u1["canvasId"]][0]["edges"],
        "reloadPastBefore": r0["past"], "reloadPastAfter": r1["past"],
        "reloadNodesAfter": r1["nodeCount"], "reloadEdgesAfter": r1["edgeCount"],
    }
    print("\n=== 汇总 ===")
    for k, v in summary.items():
        print(f"  {k}: {v}")

    checks = [
        ("C1 源码四处在位（派发 / 监听 / pushHistory / undo 清空选区）",
         lines["dispatch"] == 87 and lines["listener"] == 1433
         and lines["keyDeleteCall"] == 1326 and lines["removeEdgeImpl"] == 3656
         and lines["pushInRemoveEdge"] == 3668
         and lines["undo"] == 3673 and lines["undoClearsSelection"] is True,
         json.dumps(lines, ensure_ascii=False)),
        ("C2 路径①：边 11→10、节点 10→10 不变、past 0→1（快照含 11 条边）",
         summary["h1edges"] == 10 and summary["h0edges"] == 11
         and summary["handleNodesUnchanged"] is True and summary["h1past"] == 1
         and summary["h1pastEdgeCounts"] == [11] and len(summary["handleOnlyOneEdge"]) == 1,
         f"边 {summary['h0edges']}→{summary['h1edges']} 节点不变={summary['handleNodesUnchanged']} "
         f"past {summary['h0past']}→{summary['h1past']} 快照边数={summary['h1pastEdgeCounts']} "
         f"只少 {summary['handleOnlyOneEdge']}"),
        ("C3 路径① undo/redo 逐项精确",
         summary["undoEdgesExact"] is True and summary["undoNodesExact"] is True
         and summary["redoEdgesExact"] is True and summary["undoFuture"] == 1,
         f"undo 边={summary['undoEdgesExact']} 节点={summary['undoNodesExact']} "
         f"future={summary['undoFuture']}；redo 边={summary['redoEdgesExact']}"),
        ("C4 路径① undo 后选区两个字段都空",
         summary["undoSelNode"] == [] and summary["undoSelEdge"] == [],
         f"node={summary['undoSelNode']} edge={summary['undoSelEdge']}"),
        ("C5 路径②：节点 10→9、连带边 1 条、past 0→1",
         summary["k2nodes"] == 9 and summary["k1nodes"] == 10
         and summary["keyCascadeEdges"] == 1 and summary["k2past"] == 1,
         f"节点 {summary['k1nodes']}→{summary['k2nodes']} 连带边 {summary['keyCascadeEdges']} "
         f"past {summary['k1past']}→{summary['k2past']}"),
        ("C6 路径② undo 逐项精确，且刚选中的节点被丢掉",
         summary["keyUndoNodesExact"] is True and summary["keyUndoEdgesExact"] is True
         and len(summary["selBeforeUndo"]) == 1 and summary["selAfterUndo"] == [],
         f"逐项 节点={summary['keyUndoNodesExact']} 边={summary['keyUndoEdgesExact']}；"
         f"选区 {summary['selBeforeUndo']} → {summary['selAfterUndo']}"),
        ("C7 删除后（past>0）刷新 ⟹ past 归零、回到种子 10/11",
         summary["reloadPastBefore"] == 1 and summary["reloadPastAfter"] == 0
         and summary["reloadNodesAfter"] == 10 and summary["reloadEdgesAfter"] == 11,
         f"past {summary['reloadPastBefore']}→{summary['reloadPastAfter']}；"
         f"刷新后 节点 {summary['reloadNodesAfter']} 边 {summary['reloadEdgesAfter']}"),
        ("C8 切到另一张画布后 undo() 不误伤它、也不撤掉原画布的删除",
         summary["otherCanvasExact"] is True
         and summary["otherCanvasEdgesBefore"] == summary["otherCanvasEdgesAfter"]
         and summary["sourceEdgesAfterBucketUndo"] == 10,
         f"另一张画布边 {summary['otherCanvasEdgesBefore']}→{summary['otherCanvasEdgesAfter']}；"
         f"原画布删后仍为 {summary['sourceEdgesAfterBucketUndo']}（未被撤）"),
    ]

    print("\n=== 判据 ===")
    failures = []
    for name, ok, detail in checks:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}  ⟵ {detail}")
        if not ok:
            failures.append(name)

    payload = {
        "static": {"lines": lines},
        "run": {"handle": {"s0": s0, "s1": s1, "s2": s2, "s3": s3},
                "key": {"t1": t1, "t2": t2, "t3": t3, "picked": picked},
                "bucket": {"u1": u1, "u2": u2, "other": other_before},
                "reload": {"before": r0, "after": r1}},
        "summary": summary,
        "failures": failures,
    }
    (AUDIT_DIR / "runtime-audit.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=1, default=str), encoding="utf-8")

    print(f"\n{len(checks) - len(failures)}/{len(checks)} 判据通过；写入 {AUDIT_DIR / 'runtime-audit.json'}")
    try:
        subprocess.run(["git", "status", "--porcelain", "src"], cwd=ROOT, check=True)
    except Exception:
        pass
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
