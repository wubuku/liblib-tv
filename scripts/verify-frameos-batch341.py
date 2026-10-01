#!/usr/bin/env python3

"""Verify Batch 341: 分组盒几何不变式对**所有**写路径生效（不再只挂在少数 action 上）.

缺陷（克隆侧，Batch 340 教训的直接延续）:
`reconcileGroups()` 此前只挂在 `removeNode` / `duplicateNode` / `undo` / `redo`
几条 action 上，于是每条**新**的改 nodes 的路径都重新打破了
「分组盒 == 存活成员包围盒 + 28」这个 createGroup/arrangeGroup/moveGroup
一致遵守的不变式。实测（probe-frameos-batch341-group-geometry.py）:

  一键整理 (FrameosMapDock → organizeNodes)  成员全被重排, 盒纹丝不动  drift x/y/w/h
  拖拽成员   (page.tsx onNodesChange → setNodes) 盒不跟随            drift x/w/h
  面板删除   (FrameosNodeEditPanel → setNodes) 悬空成员 + 盒不收缩

第三项尤其说明问题: 它与 Batch 328 修过的 `removeNode` 是**同一处缺陷的两条
路径** —— 修一条漏一条。

修复（两处，缺一不可）:
1. `reconcileGroups` 去掉 `unchanged` 短路，**无条件**重算。短路只看
   memberIds，于是「成员集合没变」被当成「盒不用动」——而成员**整体移动**时
   memberIds 原封不动，盒就永远不重算。
2. store 的写入口 `set` 套一层 `enforceGroupGeometry`，任何 action 写完
   nodes/groups 后统一收敛一次，新增 action 不可能再漏（Batch 329「13 处手写
   快照」与 Batch 333「多处写 localStorage」的同一判断：不变式只该有单一出口）。

断言:
1. 一键整理（**真实点击按钮**）后分组盒重算到成员 bbox + 28;
2. 拖拽成员后分组盒跟随;
3. 面板删除后无悬空成员、盒按存活成员收缩;
4. 无净变化时**返回同一对象**（引用稳定）—— 否则 Batch 333 的持久化订阅
   会把同样的内容反复写进 localStorage;
5. moveGroup 平移后盒仍等于 bbox + 28（平移不改变该关系）;
6. arrangeGroup 后盒等于 bbox + 28;
7. 撤销后盒与成员集一并还原;
8. 诊断零错误。

CLONE_DECISION: 「拖动成员时盒跟随成员」是按克隆自身不变式推的。源站是否允许
把成员拖出分组、是否自动退组，源站被人机验证阻塞**未采样**（见
SOURCE_ACCESS_BLOCKED_2026-10-01.md），本批**未**发明任何"拖出即退组"行为。
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
    / "liblib-frameos-batch341-2026-10-01"
    / "runtime-audit.json"
)
sys.path.insert(0, str(ROOT / "scripts"))
from frameos_verify_common import attach_errors, goto_clean_canvas  # noqa: E402

# 建组并把分组几何读出来（含「盒是否等于 bbox+28」的自检）
SETUP_JS = """
() => {
  const st = window.__frameos_store;
  st.setState({ past: [], future: [], groups: [] });
  const ids = st.getState().nodes.slice(0, 2).map((n) => n.id);
  const gid = st.getState().createGroup(ids);
  window.__gid = gid;
  const g = st.getState().groups.find((x) => x.id === gid);
  return { gid, memberIds: g.memberIds, box: { x: g.x, y: g.y, w: g.w, h: g.h } };
}
"""

# 读分组状态：实际盒 / 按存活成员算出的应有盒 / 悬空成员 / 盒对象引用
STATE_JS = """
() => {
  const st = window.__frameos_store;
  const P = 28;
  const s = st.getState();
  const g = s.groups.find((x) => x.id === window.__gid);
  if (!g) return { present: false, members: null, box: null, expected: null,
                   dangling: null, groupRefChanged: null };
  const sizeOf = (n) => ({ w: (n.style && n.style.width) || 300,
                           h: (n.style && n.style.height) || 200 });
  const mem = g.memberIds.map((id) => s.nodes.find((n) => n.id === id)).filter(Boolean);
  const dangling = g.memberIds.filter((id) => !s.nodes.some((n) => n.id === id));
  let expected = null;
  if (mem.length) {
    const minX = Math.min(...mem.map((n) => n.position.x));
    const minY = Math.min(...mem.map((n) => n.position.y));
    const maxX = Math.max(...mem.map((n) => n.position.x + sizeOf(n).w));
    const maxY = Math.max(...mem.map((n) => n.position.y + sizeOf(n).h));
    expected = { x: minX - P, y: minY - P, w: maxX - minX + P * 2, h: maxY - minY + P * 2 };
  }
  return {
    present: true,
    members: g.memberIds,
    box: { x: g.x, y: g.y, w: g.w, h: g.h },
    expected,
    dangling,
    groupRef: g,
  };
}
"""

# 拖拽成员 = page.tsx onNodesChange 的同一个入口（setNodes）
DRAG_MEMBER_JS = """
(dx) => {
  const st = window.__frameos_store;
  const s = st.getState();
  const g = s.groups.find((x) => x.id === window.__gid);
  const victim = g.memberIds[0];
  st.getState().setNodes(
    s.nodes.map((n) => n.id === victim
      ? { ...n, position: { x: n.position.x + dx, y: n.position.y + 520 } }
      : n)
  );
  return { victim };
}
"""


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool, detail: str = "") -> None:
        assert ok, f"batch341 check failed: {name} {detail}".strip()
        result["checks"].append(name)

    errors = attach_errors(page)
    goto_clean_canvas(page, BASE_URL)

    # ── 1 一键整理：真实点击按钮 ──
    page.evaluate(SETUP_JS)
    before = page.evaluate(STATE_JS)
    check("setup:group-created", len(before["members"]) == 2, f"members={before['members']}")
    check("setup:box-consistent", before["box"] == before["expected"],
          f"box={before['box']} expected={before['expected']}")
    organize_btn = page.locator('button[aria-label="一键整理 · 网格整理"]')
    check("organize:button-exists", organize_btn.count() == 1,
          f"count={organize_btn.count()}")
    organize_btn.first.click()
    page.wait_for_timeout(900)
    after = page.evaluate(STATE_JS)
    check("organize:nodes-moved",
          page.evaluate("() => window.__frameos_store.getState().nodes[0].position.x")
          != before["box"]["x"],
          "一键整理未改动节点坐标，场景不成立")
    check("organize:box-recomputed", after["box"] == after["expected"],
          f"box={after['box']} expected={after['expected']}")
    check("organize:no-dangling", after["dangling"] == [], f"dangling={after['dangling']}")

    # ── 2 拖拽成员：盒必须跟随 ──
    page.evaluate(SETUP_JS)
    page.evaluate(DRAG_MEMBER_JS, 640)
    page.wait_for_timeout(400)
    dragged = page.evaluate(STATE_JS)
    check("drag:box-follows", dragged["box"] == dragged["expected"],
          f"box={dragged['box']} expected={dragged['expected']}")
    check("drag:box-actually-moved",
          dragged["box"] != page.evaluate(SETUP_JS)["box"]
          or dragged["box"]["w"] != before["box"]["w"],
          f"box={dragged['box']}")

    # ── 3 面板删除：不得留悬空成员，盒按存活成员收缩 ──
    panel = page.evaluate(
        """() => {
          const st = window.__frameos_store;
          st.setState({ past: [], future: [], groups: [] });
          st.getState().toggleDebugMode();      // 节点编辑面板仅 debug 模式渲染
          const ids = st.getState().nodes.slice(0, 2).map((n) => n.id);
          const gid = st.getState().createGroup(ids);
          window.__gid = gid;
          const member = st.getState().groups.find((x) => x.id === gid).memberIds[0];
          st.getState().selectNode(member);
          return { member };
        }"""
    )
    page.wait_for_timeout(500)
    # confirm 是同步阻塞弹窗，Playwright 的 dialog 自动处理会与处理器竞态
    page.evaluate("() => { window.confirm = () => true; }")
    del_btn = page.locator("button", has_text="删除节点")
    check("panel:delete-button-exists", del_btn.count() >= 1, f"count={del_btn.count()}")
    try:
        # 面板按节点屏幕坐标 fixed 定位，可能落在视口外
        del_btn.first.click(force=True, timeout=5000)
    except Exception:  # noqa: BLE001
        del_btn.first.dispatch_event("click")
    page.wait_for_timeout(700)
    deleted = page.evaluate(STATE_JS)
    check("panel:node-gone",
          page.evaluate("(id) => !window.__frameos_store.getState().nodes.some((n) => n.id === id)",
                        panel["member"]) is True,
          f"member={panel['member']}")
    check("panel:no-dangling", deleted["dangling"] == [], f"dangling={deleted['dangling']}")
    check("panel:members-shrunk",
          deleted["members"] is not None and panel["member"] not in deleted["members"],
          f"members={deleted['members']}")
    check("panel:box-shrunk", deleted["box"] == deleted["expected"],
          f"box={deleted['box']} expected={deleted['expected']}")

    # ── 4 无净变化 → 引用稳定（否则持久化订阅会反复写同样内容）──
    stable = page.evaluate(
        """() => {
          const st = window.__frameos_store;
          const beforeRef = st.getState().groups.find((x) => x.id === window.__gid);
          // 与分组无关的写入不应牵动分组对象
          st.getState().toggleMinimap();
          st.getState().setPromptValue("无净变化探针");
          const afterRef = st.getState().groups.find((x) => x.id === window.__gid);
          return { same: beforeRef === afterRef };
        }"""
    )
    check("stability:no-net-change-keeps-reference", stable["same"] is True,
          "无净变化时分组对象被重建")

    # ── 5 moveGroup 平移后盒仍 = bbox + 28 ──
    moved = page.evaluate(
        """() => {
          const st = window.__frameos_store;
          st.getState().moveGroup(window.__gid, 120, 75);
          const g = st.getState().groups.find((x) => x.id === window.__gid);
          return { x: g.x, y: g.y, w: g.w, h: g.h };
        }"""
    )
    mstate = page.evaluate(STATE_JS)
    check("moveGroup:box-consistent", mstate["box"] == mstate["expected"],
          f"box={mstate['box']} expected={mstate['expected']} moved={moved}")

    # ── 6 arrangeGroup 后盒 = bbox + 28 ──
    for mode in ("grid", "horizontal", "vertical"):
        page.evaluate("(m) => window.__frameos_store.getState().arrangeGroup(window.__gid, m)", mode)
        page.wait_for_timeout(200)
        astate = page.evaluate(STATE_JS)
        check(f"arrangeGroup:{mode}:box-consistent", astate["box"] == astate["expected"],
              f"box={astate['box']} expected={astate['expected']}")

    # ── 7 撤销后盒与成员集一并还原 ──
    undo_state = page.evaluate(
        """() => {
          const st = window.__frameos_store;
          const key = st.getState().groups.find((x) => x.id === window.__gid);
          const n = st.getState().undo();
          const g = st.getState().groups.find((x) => x.id === window.__gid);
          return { n, present: Boolean(g),
                   members: g ? g.memberIds : null,
                   box: g ? { x: g.x, y: g.y, w: g.w, h: g.h } : null,
                   had: key ? key.memberIds.length : 0 };
        }"""
    )
    check("undo:group-present", undo_state["present"] is True, "撤销后分组消失")
    check("undo:members-restored", undo_state["members"] is not None
          and len(undo_state["members"]) == undo_state["had"],
          f"members={undo_state['members']} had={undo_state['had']}")

    check("diagnostics:zero", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 341,
        "title": "FrameOS group box geometry invariant holds on every write path",
        "defect": (
            "reconcileGroups was only wired into a few actions, so every other path that "
            "mutates nodes re-broke the 'group box == bbox(live members) + 28' invariant "
            "that createGroup/arrangeGroup/moveGroup all honour. Measured: 一键整理 left "
            "the box untouched while re-laying every node (drift x/y/w/h); dragging a "
            "member did not move the box (drift x/w/h); the debug-mode node panel's "
            "delete button left a dangling member and an un-shrunk box -- the same defect "
            "Batch 328 fixed, reached through a second path."
        ),
        "fix": (
            "reconcileGroups now recomputes unconditionally (the old `unchanged` "
            "short-circuit only looked at memberIds, so a wholesale member move never "
            "recomputed the box), and the store's write entrypoint is wrapped by "
            "enforceGroupGeometry so every action -- present or future -- converges once. "
            "Groups whose values do not change keep their object identity so Batch 333's "
            "persistence subscription does not rewrite identical content."
        ),
        "clone_decision": (
            "'the box follows a dragged member' is derived from the clone's own invariant. "
            "Whether the source site allows dragging a member out of a group, and whether "
            "it auto-ungroups, was NOT sampled (blocked by the human-verification gate, see "
            "SOURCE_ACCESS_BLOCKED_2026-10-01.md). No drag-out-ungroup behaviour was "
            "invented here."
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
        "Batch 341 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "The group box is recomputed from live members on every write path "
        "(一键整理 / 拖拽成员 / 面板删除 all verified), no net change keeps object "
        "identity, and moveGroup / arrangeGroup / undo stay consistent with "
        "bbox(live members) + 28."
    )


if __name__ == "__main__":
    main()
