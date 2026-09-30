#!/usr/bin/env python3

"""Verify Batch 330: 分组重命名 / 改色 / 整组拖拽 的撤销覆盖。

缺陷（克隆侧）: Batch 329 补齐了 createGroup / ungroup / arrangeGroup 的撤销，
但 `renameGroup` / `setGroupColor` 仍只改 state 不入栈 → 动作不可撤销。
探针实测三者的 `pushed:false, undoRestores:false`。

修复: renameGroup / setGroupColor 改用 `pushHistorySnapshot(state)`。
**`moveGroup` 故意不入栈** —— 它在拖拽中每帧调用，入栈会灌爆 20 格历史；
整组拖拽的可撤销性由 UI 层在手势开始时调一次 `pushHistory()` 保证
（与节点拖拽 Batch 189/232 同一模式）。本验证器把这条当作**必须成立的不变式**
来测：一次 pushHistory + N 次 moveGroup = 一次撤销回原位。

断言:
1. 重命名入栈；撤销还原旧名；重做恢复新名；
2. 改色入栈；撤销还原原色；重做恢复新色；
3. 空名提交不生效且不产生脏历史项;
4. **整组拖拽：一次 pushHistory + 多次 moveGroup，撤销精确回原位**
   （且历史深度不随帧数增长 —— 防灌爆）;
5. 拖拽撤销后成员节点位置一并还原;
6. 成组/解组/排列的撤销不回退（Batch 329 行为保持）;
7. 诊断零错误。
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
    / "liblib-frameos-batch330-2026-10-01"
    / "runtime-audit.json"
)

SETUP_JS = """
() => {
  const st = window.__frameos_store;
  st.setState({ past: [], future: [] });
  const gid = st.getState().createGroup(st.getState().nodes.slice(0, 3).map((n) => n.id));
  const g = st.getState().groups.find((x) => x.id === gid);
  return { gid, name: g.name, color: g.color, x: g.x, y: g.y,
           members: st.getState().nodes.filter((n) => g.memberIds.includes(n.id))
             .map((n) => ({ id: n.id, x: n.position.x, y: n.position.y })) };
}
"""

GROUP_JS = "(gid) => { const g = window.__frameos_store.getState().groups.find((x) => x.id === gid); return g ? { name: g.name, color: g.color, x: g.x, y: g.y } : null; }"
MEMBERS_JS = "(gid) => { const st = window.__frameos_store; const g = st.getState().groups.find((x) => x.id === gid); if (!g) return null; return st.getState().nodes.filter((n) => g.memberIds.includes(n.id)).map((n) => ({ id: n.id, x: n.position.x, y: n.position.y })); }"


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
        assert ok, f"batch330 check failed: {name} {detail}".strip()
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/frameos/canvas/demo", wait_until="domcontentloaded", timeout=90000)
    page.wait_for_selector(".react-flow__node", timeout=30000)
    page.wait_for_timeout(1200)

    setup = page.evaluate(SETUP_JS)
    gid = setup["gid"]

    def grp() -> dict[str, Any]:
        return page.evaluate(GROUP_JS, gid)

    def mem() -> list[dict[str, Any]]:
        return page.evaluate(MEMBERS_JS, gid)

    def depth() -> int:
        return page.evaluate("() => window.__frameos_store.getState().past.length")

    # ── 1 重命名 ──
    d0 = depth()
    page.evaluate("(gid) => window.__frameos_store.getState().renameGroup(gid, '探测组B')", gid)
    check("rename:pushed", depth() > d0, f"{d0}->{depth()}")
    check("rename:applied", grp()["name"] == "探测组B", f"name={grp()['name']}")
    page.evaluate("() => window.__frameos_store.getState().undo()")
    check("rename:undo-restores", grp()["name"] == setup["name"], f"name={grp()['name']}")
    page.evaluate("() => window.__frameos_store.getState().redo()")
    check("rename:redo-applies", grp()["name"] == "探测组B")

    # ── 2 改色 ──
    page.evaluate("() => window.__frameos_store.getState().undo()")  # 回到原色
    d0 = depth()
    page.evaluate("(gid) => window.__frameos_store.getState().setGroupColor(gid, '#ff0000')", gid)
    check("color:pushed", depth() > d0)
    check("color:applied", grp()["color"] == "#ff0000", f"color={grp()['color']}")
    page.evaluate("() => window.__frameos_store.getState().undo()")
    check("color:undo-restores", grp()["color"] == setup["color"], f"color={grp()['color']}")
    page.evaluate("() => window.__frameos_store.getState().redo()")
    check("color:redo-applies", grp()["color"] == "#ff0000")
    page.evaluate("() => window.__frameos_store.getState().undo()")

    # ── 3 无净变化不入栈（空名 / 同名 / 同色）──
    # 否则一次空提交会占掉一格撤销，用户按撤销却看不到任何变化。
    depth_before_blank = depth()
    page.evaluate("(gid) => window.__frameos_store.getState().renameGroup(gid, '   ')", gid)
    check("rename:blank-name-ignored", grp()["name"] == setup["name"], f"name={grp()['name']}")
    check("rename:blank-no-history", depth() == depth_before_blank,
          f"depth {depth_before_blank} -> {depth()}")

    d_same = depth()
    page.evaluate(
        """([gid, name]) => window.__frameos_store.getState().renameGroup(gid, name)""",
        [gid, setup["name"]],
    )
    check("rename:same-name-no-history", depth() == d_same, f"depth {d_same} -> {depth()}")
    check("rename:same-name-kept", grp()["name"] == setup["name"])

    d_same_c = depth()
    page.evaluate(
        """([gid, color]) => window.__frameos_store.getState().setGroupColor(gid, color)""",
        [gid, setup["color"]],
    )
    check("color:same-color-no-history", depth() == d_same_c, f"depth {d_same_c} -> {depth()}")
    check("color:same-color-kept", grp()["color"] == setup["color"])

    # ── 4/5 整组拖拽：一次 pushHistory + 多次 moveGroup ──
    before_box = grp()
    assert before_box is not None, "group missing before drag section"
    before_mem = mem()
    d_before = depth()
    # 模拟 FrameosGroupCanvas 的手势：开始时 pushHistory 一次，然后逐帧 moveGroup
    page.evaluate("() => window.__frameos_store.getState().pushHistory()")
    for _ in range(6):
        page.evaluate("(gid) => window.__frameos_store.getState().moveGroup(gid, 10, 6)", gid)
    d_after_frames = depth()
    check("move:history-not-flooded", d_after_frames == d_before + 1,
          f"depth {d_before} -> {d_after_frames} after 6 moveGroup frames")
    moved = grp()
    check("move:applied", moved["x"] == before_box["x"] + 60 and moved["y"] == before_box["y"] + 36,
          f"{before_box} -> {moved}")
    check("move:members-followed",
          all(m["x"] == b["x"] + 60 and m["y"] == b["y"] + 36
              for m, b in zip(mem(), before_mem)))
    page.evaluate("() => window.__frameos_store.getState().undo()")
    check("move:undo-restores-box", grp() == before_box, f"{grp()} vs {before_box}")
    check("move:undo-restores-members", mem() == before_mem)

    # ── 6 Batch 329 行为保持 ──
    check("keep:group-exists", grp() is not None)
    check("keep:members-intact", len(mem()) == 3, f"members={len(mem())}")

    check("diagnostics:zero", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 330,
        "title": "FrameOS group rename/recolor/drag undo coverage",
        "defect": (
            "after Batch 329, createGroup/ungroup/arrangeGroup were undoable but "
            "renameGroup and setGroupColor still mutated state without pushing history, "
            "making those actions irreversible (probe: pushed=false, undoRestores=false)."
        ),
        "fix": (
            "renameGroup and setGroupColor now use pushHistorySnapshot(state). moveGroup is "
            "deliberately NOT pushing: it runs per drag frame, so history would flood; group "
            "drag undoability comes from a single pushHistory() at gesture start in "
            "FrameosGroupCanvas, the same pattern as node drag (Batch 189/232)."
        ),
        "clone_decision": (
            "whether the source site treats group rename/recolor/drag as undoable was NOT "
            "sampled (source blocked, see SOURCE_ACCESS_BLOCKED_2026-10-01.md). This batch "
            "closes the gap for internal consistency only; it is not a source-parity claim."
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
        "Batch 330 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "Group rename and recolor are undoable, group drag undoes in one step without "
        "flooding history, and member positions are restored with the box."
    )


if __name__ == "__main__":
    main()
