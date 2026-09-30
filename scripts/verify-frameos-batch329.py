#!/usr/bin/env python3

"""Verify Batch 329: 分组进入撤销历史（createGroup / ungroup / removeNode ↔ undo）.

缺陷（克隆侧，Batch 328 之后新暴露）:
  历史快照只存 `{nodes, edges}`，而 groups 会被 createGroup / ungroup /
  removeNode(reconcileGroups) 改动 → 撤销只还原 nodes/edges，分组状态留在
  「动作之后」。最严重的一条：撤销「删除分组成员」时**节点回来了但成员集没回来**
  ——被恢复的节点被静默踢出分组，且不产生任何悬空引用或报错。

修复:
  1. 快照类型纳入 `groups?`（可选，旧快照向后兼容为空数组）；
  2. 新增 `pushHistorySnapshot(state)` 统一入口，13 处入栈路径全部改用它，
     新增 action 不可能再漏带 groups；
  3. `createGroup` / `ungroup` 首次入历史栈；
  4. undo/redo 还原 groups 并过 `reconcileGroups` 兜底收敛。

断言:
1. createGroup 入栈，撤销后分组消失；
2. createGroup 可重做（redo 恢复分组）；
3. ungroup 入栈，撤销后分组回来；
4. **删除成员后撤销：成员集完整恢复，节点不被踢出分组，分组盒还原**；
5. redo 能重放「删除成员」后的收敛状态；
6. 连续多步 undo 不产生悬空成员；
7. 旧格式快照（无 groups 字段）被安全处理；
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
    / "liblib-frameos-batch329-2026-10-01"
    / "runtime-audit.json"
)

HELPERS_JS = """
() => {
  const st = window.__frameos_store;
  window.__g = {
    snap: () => ({
      nodes: st.getState().nodes.map((n) => n.id),
      groups: st.getState().groups.map((g) => ({
        id: g.id, name: g.name, memberIds: [...g.memberIds],
        box: { x: g.x, y: g.y, w: g.w, h: g.h },
      })),
      pastDepth: st.getState().past.length,
      futureDepth: st.getState().future.length,
    }),
    makeGroup: () => st.getState().createGroup(
      st.getState().nodes.slice(0, 2).map((n) => n.id)),
    dangling: () => {
      const ids = new Set(st.getState().nodes.map((n) => n.id));
      return st.getState().groups.flatMap((g) =>
        g.memberIds.filter((m) => !ids.has(m)).map((m) => `${g.id}:${m}`));
    },
  };
  return window.__g.snap();
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
        assert ok, f"batch329 check failed: {name} {detail}".strip()
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/frameos/canvas/demo", wait_until="domcontentloaded", timeout=90000)
    page.wait_for_selector(".react-flow__node", timeout=30000)
    page.wait_for_timeout(1200)
    page.evaluate(HELPERS_JS)

    def snap() -> dict[str, Any]:
        return page.evaluate("() => window.__g.snap()")

    def dangling() -> list[str]:
        return page.evaluate("() => window.__g.dangling()")

    def make_group() -> str:
        return page.evaluate("() => window.__g.makeGroup()")

    # ── 1/2 createGroup 入栈 + 撤销 + 重做 ──
    before = snap()
    make_group()
    after = snap()
    check("create:pushed-to-history", after["pastDepth"] > before["pastDepth"],
          f"{before['pastDepth']}->{after['pastDepth']}")
    check("create:group-exists", len(after["groups"]) == 1)
    gid = after["groups"][0]["id"]
    original_box = after["groups"][0]["box"]
    original_members = after["groups"][0]["memberIds"]

    page.evaluate("() => window.__frameos_store.getState().undo()")
    undone = snap()
    check("create:undo-removes-group", len(undone["groups"]) == 0, f"groups={len(undone['groups'])}")

    page.evaluate("() => window.__frameos_store.getState().redo()")
    redone = snap()
    check("create:redo-restores-group", len(redone["groups"]) == 1)
    check("create:redo-members-intact", redone["groups"][0]["memberIds"] == original_members)
    check("create:redo-box-intact", redone["groups"][0]["box"] == original_box)

    # ── 3 ungroup 入栈 + 撤销恢复 ──
    depth_before_ungroup = snap()["pastDepth"]
    page.evaluate("(id) => window.__frameos_store.getState().ungroup(id)", gid)
    after_ungroup = snap()
    check("ungroup:pushed-to-history", after_ungroup["pastDepth"] > depth_before_ungroup)
    check("ungroup:group-removed", len(after_ungroup["groups"]) == 0)
    page.evaluate("() => window.__frameos_store.getState().undo()")
    check("ungroup:undo-restores", len(snap()["groups"]) == 1)

    # ── 4 删除成员后撤销：成员集完整恢复（Batch 329 的核心断言）──
    victim = original_members[0]
    page.evaluate("(id) => window.__frameos_store.getState().removeNode(id)", victim)
    after_del = snap()
    check("delete:member-pruned", after_del["groups"][0]["memberIds"] == [m for m in original_members if m != victim],
          f"members={after_del['groups'][0]['memberIds']}")
    check("delete:no-dangling-after-delete", dangling() == [])

    page.evaluate("() => window.__frameos_store.getState().undo()")
    after_undo = snap()
    check("undo:node-restored", victim in after_undo["nodes"])
    check("undo:membership-fully-restored",
          sorted(after_undo["groups"][0]["memberIds"]) == sorted(original_members),
          f"got={after_undo['groups'][0]['memberIds']} want={original_members}")
    check("undo:box-restored", after_undo["groups"][0]["box"] == original_box,
          f"got={after_undo['groups'][0]['box']} want={original_box}")
    check("undo:no-dangling", dangling() == [], f"dangling={dangling()}")

    # ── 5 redo 重放删除后的收敛状态 ──
    page.evaluate("() => window.__frameos_store.getState().redo()")
    after_redo = snap()
    check("redo:delete-replayed", victim not in after_redo["nodes"])
    check("redo:membership-converged",
          after_redo["groups"][0]["memberIds"] == [m for m in original_members if m != victim],
          f"members={after_redo['groups'][0]['memberIds']}")
    check("redo:no-dangling", dangling() == [])

    # ── 6 连撤多步不产生悬空 ──
    for _ in range(6):
        page.evaluate("() => window.__frameos_store.getState().undo()")
        page.wait_for_timeout(80)
    final = snap()
    check("multi-undo:no-dangling", dangling() == [], f"dangling={dangling()}")
    check("multi-undo:state-consistent",
          all(g["memberIds"] for g in final["groups"]),
          f"groups={final['groups']}")

    # ── 7 旧格式快照（无 groups 字段）被安全处理 ──
    legacy = page.evaluate(
        """() => {
          const st = window.__frameos_store;
          // 伪造一条 Batch 329 之前的历史项：没有 groups 字段
          st.setState({
            past: [{ nodes: st.getState().nodes, edges: st.getState().edges }],
            future: [],
          });
          st.getState().undo();
          return {
            groups: st.getState().groups.length,
            nodes: st.getState().nodes.length,
            dangling: (() => {
              const ids = new Set(st.getState().nodes.map((n) => n.id));
              return st.getState().groups.flatMap((g) =>
                g.memberIds.filter((m) => !ids.has(m)));
            })(),
          };
        }"""
    )
    check("legacy-snapshot:no-crash", isinstance(legacy, dict))
    check("legacy-snapshot:no-dangling", legacy["dangling"] == [], f"dangling={legacy['dangling']}")

    check("diagnostics:zero", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 329,
        "title": "FrameOS group-aware undo history (createGroup/ungroup/removeNode)",
        "defect": (
            "history snapshots stored only {nodes, edges} while groups are mutated by "
            "createGroup/ungroup/removeNode(reconcileGroups). Undo restored nodes but not "
            "group state, so undoing a member delete silently orphaned the restored node "
            "out of its group - no dangling ref, no error, node just left the group."
        ),
        "fix": (
            "snapshot type gained optional groups; added pushHistorySnapshot(state) as the "
            "single history entry point used by all 13 push sites; createGroup and ungroup "
            "now push history; undo/redo restore groups through reconcileGroups"
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
        "Batch 329 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "Group create/ungroup/member-delete are all undoable, undo restores full "
        "membership and group box, and legacy group-less snapshots are handled safely."
    )


if __name__ == "__main__":
    main()
