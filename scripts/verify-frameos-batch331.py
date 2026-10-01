#!/usr/bin/env python3

"""Verify Batch 331: 撤销栈按画布隔离（跨画布撤销会灌入上一张画布的节点）.

缺陷（克隆侧）: 撤销快照不记录来自哪张画布，而 `setBreadcrumb` 换画布时
只清 groups/选中态、**不重置** past/future → 在画布 A 上做的动作可以在
画布 B 上「撤销」，把 A 的 nodes/edges/groups 整份灌进 B。

实测（先在 A 上 addNode 制造一条 past，再切到 0 节点的 B 按一次撤销）:
    onB.bIds       : []
    afterUndoOnB  : ['text-1','text-2','video-1','video-2','video-3',
                     'image-1','image-2']      ← B 变成了 A 的 7 个节点

修复:
  1. `HistoryEntry` 增加 `canvasKey`，`pushHistorySnapshot` 写入当前画布 key；
  2. `setBreadcrumb` 换画布时清空 past/future（撤销本就不该跨画布生效）；
  3. undo/redo 遇到 canvasKey 不匹配的快照 → 拒绝并清空该侧栈（兜底）。

断言:
1. 换画布后 past/future 被清空;
2. 换画布后按撤销**不会**把上一张画布的节点灌进来（B 仍是 0 节点）;
3. canvasData 持久层两��画布数据均未被污染;
4. 切回 A，A 的原始数据完好;
5. **同画布内撤销仍然正常工作**（Batch 329 行为不回退）;
6. 同画布内 redo 正常;
7. 分组同样不跨画布泄漏;
8. 诊断零错误。
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
    / "liblib-frameos-batch331-2026-10-01"
    / "runtime-audit.json"
)

# 造出可撤销状态：在 A 上加节点 + 成组，然后记录 A 的基线
SETUP_A_JS = """
() => {
  const st = window.__frameos_store;
  st.setState({ past: [], future: [], groups: [] });
  const key = (b) => `${b.project}/${b.scene}/${b.canvas}`;
  const aKey = key(st.getState().breadcrumb);
  st.getState().addNode('text');                 // 制造 past 快照
  st.getState().createGroup(st.getState().nodes.slice(0, 2).map((n) => n.id));
  return {
    aKey,
    aNodeIds: st.getState().nodes.map((n) => n.id),
    aGroupCount: st.getState().groups.length,
    otherKeys: Object.keys(st.getState().canvasData).filter((k) => k !== aKey),
  };
}
"""

SWITCH_JS = """
([p, s, c]) => {
  const st = window.__frameos_store;
  st.getState().setBreadcrumb({ project: p, scene: s, canvas: c });
  return {
    nodes: st.getState().nodes.map((n) => n.id),
    groups: st.getState().groups.length,
    past: st.getState().past.length,
    future: st.getState().future.length,
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
        assert ok, f"batch331 check failed: {name} {detail}".strip()
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/frameos/canvas/demo", wait_until="domcontentloaded", timeout=90000)
    page.wait_for_selector(".react-flow__node", timeout=30000)
    page.wait_for_timeout(1200)

    setup = page.evaluate(SETUP_A_JS)
    check("setup:group-created", setup["aGroupCount"] == 1, f"groups={setup['aGroupCount']}")
    check("setup:other-canvas-available", len(setup["otherKeys"]) >= 1)

    other = setup["otherKeys"][0]
    p, s, c = other.split("/")

    # ── 1/2 换画布后栈被清空，按撤销不污染 B ──
    on_b = page.evaluate(SWITCH_JS, [p, s, c])
    check("switch:past-cleared", on_b["past"] == 0, f"past={on_b['past']}")
    check("switch:future-cleared", on_b["future"] == 0, f"future={on_b['future']}")
    b_baseline = on_b["nodes"]

    page.evaluate("() => window.__frameos_store.getState().undo()")
    after_undo = page.evaluate(
        "() => ({ nodes: window.__frameos_store.getState().nodes.map((n) => n.id),"
        " groups: window.__frameos_store.getState().groups.length })"
    )
    leaked = [n for n in after_undo["nodes"] if n in setup["aNodeIds"]]
    check("undo:no-cross-canvas-leak", leaked == [], f"leaked={leaked}")
    check("undo:canvas-b-unchanged", after_undo["nodes"] == b_baseline,
          f"got={after_undo['nodes']} want={b_baseline}")
    check("undo:no-group-leak", after_undo["groups"] == 0, f"groups={after_undo['groups']}")

    # ── 3 持久层未被污染 ──
    # 注意：canvasData 只在 setBreadcrumb 时从 MOCK_CANVASES 写入，
    # 本原型**不回写**实时编辑（既有 mock 行为，非本批范围）。
    # 因此这里断言的是「切到 B 不会用 A 的实时节点覆盖 B 的 fixture 数据」。
    cd = page.evaluate(
        """() => Object.fromEntries(Object.entries(window.__frameos_store.getState().canvasData)
             .map(([k, v]) => [k, (v.nodes || []).map((n) => n.id)]))"""
    )
    check("persist:other-canvas-clean", cd[other] == b_baseline,
          f"got={cd[other]} want={b_baseline}")
    check("persist:no-foreign-ids-in-other", cd[other] == [],
          f"canvas B fixture polluted: {cd[other]}")

    # ── 4 切回 A ──
    # Batch 332 起 setBreadcrumb 会把实时编辑写回 canvasData，故 setup 阶段
    # addNode 出来的临时节点**现在会**随切换回来（这是 332 修正的行为）。
    # 本批（331）关心的是「不混入 B 的节点」——那才是跨画布污染的判据。
    ap, as_, ac = setup["aKey"].split("/")
    back = page.evaluate(SWITCH_JS, [ap, as_, ac])
    check("back:source-canvas-no-foreign-nodes", not [n for n in back["nodes"] if n in b_baseline],
          f"foreign from B in A: {back['nodes']}")
    check("back:source-canvas-has-baseline",
          all(n in back["nodes"] for n in setup["aNodeIds"] if not n.startswith("text-1")
              or n in ("text-1", "text-2")),
          f"got={back['nodes']}")

    # ── 5/6 同画布内撤销/redo 仍工作 ──
    # 切回 A 走的是 fixture（分组不随之恢复，既有 mock 行为），故此处**重新
    # 造一次**可撤销状态再测同画布撤销/重做，避免依赖切回后的残留状态。
    page.evaluate(
        """() => {
          const st = window.__frameos_store;
          st.setState({ past: [], future: [], groups: [] });
          st.getState().addNode('text');
          st.getState().createGroup(st.getState().nodes.slice(0, 2).map((n) => n.id));
        }"""
    )
    # setup 依次做了 addNode + createGroup，故栈深 2：
    #   undo1 → 撤分组（groups 0，节点仍在）
    #   undo2 → 撤建节点（nodes 少 1）
    #   redo1 → 恢复节点；redo2 → 恢复分组
    after_setup = page.evaluate(
        "() => ({ nodes: window.__frameos_store.getState().nodes.length,"
        " groups: window.__frameos_store.getState().groups.length })"
    )
    check("same-canvas:setup-has-group", after_setup["groups"] == 1)

    page.evaluate("() => window.__frameos_store.getState().undo()")
    u1 = page.evaluate(
        "() => ({ nodes: window.__frameos_store.getState().nodes.length,"
        " groups: window.__frameos_store.getState().groups.length })"
    )
    check("same-canvas:undo1-removed-group", u1["groups"] == 0, f"groups={u1['groups']}")
    check("same-canvas:undo1-kept-nodes", u1["nodes"] == after_setup["nodes"],
          f"{u1['nodes']} vs {after_setup['nodes']}")

    page.evaluate("() => window.__frameos_store.getState().undo()")
    u2 = page.evaluate("() => window.__frameos_store.getState().nodes.length")
    check("same-canvas:undo2-removed-node", u2 == after_setup["nodes"] - 1,
          f"{u2} vs {after_setup['nodes'] - 1}")

    page.evaluate("() => window.__frameos_store.getState().redo()")
    r1 = page.evaluate("() => window.__frameos_store.getState().nodes.length")
    check("same-canvas:redo1-restored-node", r1 == after_setup["nodes"],
          f"{r1} vs {after_setup['nodes']}")

    page.evaluate("() => window.__frameos_store.getState().redo()")
    r2 = page.evaluate(
        "() => ({ nodes: window.__frameos_store.getState().nodes.length,"
        " groups: window.__frameos_store.getState().groups.length })"
    )
    check("same-canvas:redo2-restored-group", r2["groups"] == 1, f"groups={r2['groups']}")
    check("same-canvas:redo2-nodes", r2["nodes"] == after_setup["nodes"])

    check("diagnostics:zero", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 331,
        "title": "FrameOS canvas-scoped undo history (no cross-canvas node injection)",
        "defect": (
            "history snapshots carried no canvas identity and setBreadcrumb reset neither "
            "past nor future, so an action taken on canvas A could be undone on canvas B, "
            "injecting all of A's nodes/edges/groups into B. Measured: canvas B went from "
            "0 nodes to 7 (all of canvas A's) after a single undo."
        ),
        "fix": (
            "HistoryEntry gained canvasKey written by pushHistorySnapshot; setBreadcrumb "
            "clears past/future on canvas switch; undo/redo reject and clear the stack when "
            "a snapshot's canvasKey does not match the current canvas (backstop)"
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
        "Batch 331 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "Switching canvases clears the undo stacks, undo on another canvas no longer "
        "injects foreign nodes, persisted canvasData stays clean, and same-canvas "
        "undo/redo still work."
    )


if __name__ == "__main__":
    main()
