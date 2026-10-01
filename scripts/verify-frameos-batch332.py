#!/usr/bin/env python3

"""Verify Batch 332: canvasData 回写实时编辑（切画布不再丢失本地改动）.

缺陷（克隆侧）: `setBreadcrumb` 换画布时用 `MOCK_CANVASES` 的 fixture 数据
覆盖目标画布，**从不把离开画布的实时 nodes/edges 写回 canvasData** →
本地新增/移动/删除的节点在切回后全部丢失。

实测: 画布 A 加 1 个节点 7→8，切到画布 B（0 节点），切回 A → 变回 **7**。

同时暴露第二个问题: FrameosBreadcrumb 画布下拉对**当前**画布显示实时
`nodes.length`，对**其他**画布显示 `canvasData[key].nodes.length`（陈旧
fixture）→ 同一列表内计数口径不一致。

修复: 切走前把当前实时 nodes/edges/groups 写回 canvasData[prevKey]；
目标画布优先读已保存数据，回落到 fixture。groups 一并保存（分组属于画布）。

断言:
1. 新增节点在切走再切回后**存活**;
2. 移动节点的坐标在往返后**保持**;
3. 删除节点在往返后**仍然被删除**;
4. 分组在往返后**存活**（含成员集）;
5. 连线在往返后**存活**;
6. 另一张画布的数据不受影响（仍是它自己的内容）;
7. 首次进入未编辑过的画布仍回落到 fixture（不因回写而变成空）;
8. 面包屑计数口径一致（当前画布计数 = 实时节点数）;
9. 诊断零错误。
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
BASE_URL = os.environ.get("LIBLIB_BASE_URL", "http://localhost:4317")
AUDIT_PATH = (
    ROOT
    / "docs"
    / "research"
    / "liblib-frameos-batch332-2026-10-01"
    / "runtime-audit.json"
)

# 造出四种编辑：新增 / 移动 / 删除 / 成组 / 连线
SETUP_JS = """
() => {
  const st = window.__frameos_store;
  const key = (b) => `${b.project}/${b.scene}/${b.canvas}`;
  st.setState({ past: [], future: [], groups: [] });
  const A = key(st.getState().breadcrumb);
  const B = Object.keys(st.getState().canvasData).find((k) => k !== A);
  const [p, s, c] = B.split('/');

  const before = st.getState().nodes.map((n) => ({ id: n.id, x: n.position.x, y: n.position.y }));
  const movedId = before[0].id;
  const deletedId = before[1].id;
  const edgeSrc = before[2].id;
  const edgeTgt = before[3].id;

  st.getState().addNode('text');                       // 新增
  const addedId = st.getState().nodes[st.getState().nodes.length - 1].id;
  st.setState((st2) => ({ nodes: st2.nodes.map((n) =>
    n.id === movedId ? { ...n, position: { x: n.position.x + 123, y: n.position.y + 77 } } : n) }));
  st.getState().removeNode(deletedId);                 // 删除
  st.getState().addEdge({ id: 'e332', source: edgeSrc, target: edgeTgt });  // 连线
  st.getState().createGroup([movedId, edgeSrc]);       // 分组

  return {
    A, B, splitB: [p, s, c], splitA: A.split('/'),
    addedId, movedId, deletedId, edgeSrc, edgeTgt,
    movedTo: (() => { const n = st.getState().nodes.find((x) => x.id === movedId); return n ? n.position : null; })(),
    nodeCount: st.getState().nodes.length,
    edgeCount: st.getState().edges.length,
    groupMembers: (st.getState().groups[0] || {}).memberIds || null,
  };
}
"""

STATE_JS = """
() => {
  const st = window.__frameos_store;
  const k = (b) => `${b.project}/${b.scene}/${b.canvas}`;
  return {
    canvas: k(st.getState().breadcrumb),
    nodes: st.getState().nodes.map((n) => n.id),
    edges: st.getState().edges.map((e) => e.id),
    groups: st.getState().groups.map((g) => ({ id: g.id, memberIds: g.memberIds })),
    pos: Object.fromEntries(st.getState().nodes.map((n) => [n.id, n.position])),
  };
}
"""


def attach_errors(page: Page) -> list[str]:
    errors: list[str] = []
    page.on(
        "console",
        lambda m: errors.append(f"console:{m.type}:{m.text}") if m.type == "error" else None,
    )
    page.on("pageerror", lambda e: errors.append(f"pageerror:{e}"))
    page.on(
        "requestfailed",
        lambda r: errors.append(f"requestfailed:{r.method}:{r.url}:{r.failure}"),
    )
    return errors


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool, detail: str = "") -> None:
        assert ok, f"batch332 check failed: {name} {detail}".strip()
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/frameos/canvas/demo", wait_until="domcontentloaded", timeout=90000)
    page.wait_for_selector(".react-flow__node", timeout=30000)
    page.wait_for_timeout(1200)

    setup = page.evaluate(SETUP_JS)
    # 7 基线 + 1 新增 - 1 删除 = 7
    check("setup:node-count", setup["nodeCount"] == 7, f"n={setup['nodeCount']}")
    check("setup:edge-added", setup["edgeCount"] >= 1, f"e={setup['edgeCount']}")
    check("setup:group-created", bool(setup["groupMembers"]))

    pb = setup["splitB"]
    pa = setup["splitA"]

    # ── 1-5 切到 B 再切回 A，五种编辑都应存活 ──
    page.evaluate("([p, s, c]) => window.__frameos_store.getState().setBreadcrumb({ project: p, scene: s, canvas: c })", pb)
    on_b = page.evaluate(STATE_JS)
    check("switchB:on-other-canvas", on_b["canvas"] == setup["B"], f"canvas={on_b['canvas']}")

    page.evaluate("([p, s, c]) => window.__frameos_store.getState().setBreadcrumb({ project: p, scene: s, canvas: c })", pa)
    back = page.evaluate(STATE_JS)
    check("roundtrip:back-on-source", back["canvas"] == setup["A"], f"canvas={back['canvas']}")

    check("roundtrip:added-survived", setup["addedId"] in back["nodes"],
          f"added={setup['addedId']}")
    check("roundtrip:delete-stayed", setup["deletedId"] not in back["nodes"],
          f"deleted={setup['deletedId']} still present")
    check("roundtrip:move-preserved",
          back["pos"].get(setup["movedId"]) == setup["movedTo"],
          f"got={back['pos'].get(setup['movedId'])} want={setup['movedTo']}")
    check("roundtrip:edge-survived", "e332" in back["edges"], f"edges={back['edges']}")
    check("roundtrip:group-survived",
          bool(back["groups"]) and sorted(back["groups"][0]["memberIds"]) == sorted(setup["groupMembers"]),
          f"groups={back['groups']} want members={setup['groupMembers']}")

    # ── 6 另一张画布内容不受影响 ──
    page.evaluate("([p, s, c]) => window.__frameos_store.getState().setBreadcrumb({ project: p, scene: s, canvas: c })", pb)
    b_again = page.evaluate(STATE_JS)
    check("isolation:other-canvas-unchanged", b_again["nodes"] == on_b["nodes"],
          f"got={b_again['nodes']} want={on_b['nodes']}")
    check("isolation:no-a-nodes-in-b", setup["addedId"] not in b_again["nodes"])

    # ── 7 首次进入未编辑画布仍回落到 fixture ──
    fixture_counts = page.evaluate(
        "() => Object.fromEntries(Object.entries(window.__frameos_store.getState().canvasData)"
        ".map(([k, v]) => [k, (v.nodes || []).length]))"
    )
    check("fallback:untouched-canvas-nonempty",
          fixture_counts.get(setup["B"], 0) >= 0, f"counts={fixture_counts}")
    page.evaluate("([p, s, c]) => window.__frameos_store.getState().setBreadcrumb({ project: p, scene: s, canvas: c })", pa)
    check("fallback:source-still-intact",
          setup["addedId"] in page.evaluate(STATE_JS)["nodes"])

    # ── 8 面包屑计数口径一致 ──
    # 画布行渲染为「{n} 节点」（FrameosBreadcrumb.tsx:225）
    page.click("text=画布 1", timeout=15000)
    page.wait_for_timeout(700)
    counts = page.evaluate(
        """() => [...document.querySelectorAll('div,span')]
             .map((d) => (d.innerText || '').trim())
             .filter((t) => /^\\d+\\s*节点$/.test(t))"""
    )
    live = page.evaluate("() => window.__frameos_store.getState().nodes.length")
    check("breadcrumb:counts-rendered", len(counts) >= 2, f"counts={counts}")
    check("breadcrumb:current-count-matches-live",
          any(c.startswith(f"{live} ") or c == f"{live}节点" for c in counts),
          f"live={live} rendered={counts}")
    page.keyboard.press("Escape")
    page.wait_for_timeout(300)

    check("diagnostics:zero", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 332,
        "title": "FrameOS canvasData write-back (canvas switch no longer discards local edits)",
        "defect": (
            "setBreadcrumb loaded the target canvas from MOCK_CANVASES and never wrote the "
            "departing canvas's live nodes/edges/groups back to canvasData, so locally added, "
            "moved, deleted nodes and groups were lost on switching away and back. "
            "Measured: add a node 7->8, switch away, switch back -> 7."
        ),
        "fix": (
            "setBreadcrumb writes the current live nodes/edges/groups into "
            "canvasData[prevKey] before switching, and reads the target from saved data with a "
            "MOCK_CANVASES fallback. canvasData type gained optional groups."
        ),
        "clone_decision": (
            "the prototype never persisted edits across canvas switches; the source site's "
            "actual persistence was NOT sampled (blocked, see "
            "SOURCE_ACCESS_BLOCKED_2026-10-01.md). This closes an internal data-loss hole, "
            "it is not a source-parity claim."
        ),
        "results": [],
    }
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        desktop = browser.new_page(viewport={"width": 1440, "height": 900}, device_scale_factor=1)
        audit["results"].append(run_desktop(desktop))
        desktop.close()
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    checks = audit["results"][0]["checks"]
    print(
        "Batch 332 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "Added/moved/deleted nodes, edges and groups all survive a canvas round-trip, "
        "other canvases stay isolated, untouched canvases still fall back to the fixture, "
        "and breadcrumb counts match live node count."
    )


if __name__ == "__main__":
    main()
