#!/usr/bin/env python3

"""Verify Batch 328: 分组完整性 — 删除分组成员后收敛成员集与分组盒.

缺陷（克隆侧）: `removeNode` 只过滤 `nodes`/`edges`，`groups[].memberIds` 仍指向
已删节点（悬空成员），分组盒 `x/y/w/h` 也不重算 → 覆盖层保留旧几何、比实际成员
大，排列/拖拽/解组都基于错误成员集计算。

修复: 新增 `reconcileGroups(groups, nodes)`，删除后按存活成员剪枝并重算包围盒；
成员删空时分组随之消失，`selectedGroupId` 一并清空（不留指向不存在分组的选中态）。

断言:
1. 删除 1 个成员后 memberIds 无悬空引用;
2. 分组盒按剩余成员重算（几何确实变化且贴合剩余成员 bbox + 28）;
3. 剩余成员仍全部在组内，组未被误删;
4. 成员全部删空时分组消失，且不残留选中态;
5. 撤销可恢复被删节点，分组仍在（成员集保持收敛后的状态，不回退成悬空）;
6. 排列作用于存活成员且分组盒随之更新;
7. 未分组节点的普通删除不受影响（无分组时 groups 保持为空）;
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
    / "liblib-frameos-batch328-2026-10-01"
    / "runtime-audit.json"
)

# 与 store 中 FRAMEOS_GROUP_PADDING 一致（分组盒 = 成员 bbox + 28）
GROUP_PADDING = 28
NODE_W = 300
NODE_H = 200

SETUP_JS = """
() => {
  const st = window.__frameos_store;
  const ids = st.getState().nodes.slice(0, 2).map((n) => n.id);
  const gid = st.getState().createGroup(ids);
  const g = st.getState().groups.find((x) => x.id === gid);
  return {
    groupId: gid,
    memberIds: g.memberIds,
    box: { x: g.x, y: g.y, w: g.w, h: g.h },
    nodeGeom: st.getState().nodes.slice(0, 2).map((n) => ({
      id: n.id,
      x: n.position.x,
      y: n.position.y,
      w: (n.style && n.style.width) || 300,
      h: (n.style && n.style.height) || 200,
    })),
  };
}
"""

REMOVE_JS = """
(victim) => {
  const st = window.__frameos_store;
  st.getState().removeNode(victim);
  const g = st.getState().groups.find((x) => x.id === window.__groupId);
  return {
    groups: st.getState().groups.map((x) => ({ id: x.id, memberIds: x.memberIds, box: {x:x.x,y:x.y,w:x.w,h:x.h} })),
    selectedGroupId: st.getState().selectedGroupId,
    surviving: st.getState().nodes.filter((n) => n.id === g.memberIds[0]).map((n) => ({
      id: n.id, x: n.position.x, y: n.position.y,
      w: (n.style && n.style.width) || 300, h: (n.style && n.style.height) || 200,
    })),
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
        assert ok, f"batch328 check failed: {name} {detail}".strip()
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/frameos/canvas/demo", wait_until="domcontentloaded", timeout=90000)
    page.wait_for_selector(".react-flow__node", timeout=30000)
    page.wait_for_timeout(1200)

    setup = page.evaluate(SETUP_JS)
    page.evaluate("(gid) => { window.__groupId = gid; }", setup["groupId"])
    check("setup:group-created", len(setup["memberIds"]) == 2)

    # ── 1/2/3 删除一个成员 ──
    victim = setup["memberIds"][0]
    state = page.evaluate(REMOVE_JS, victim)
    groups = state["groups"]
    check("remove:one-group-left", len(groups) == 1)
    g = groups[0]
    node_ids = {n["id"] for n in page.evaluate("() => window.__frameos_store.getState().nodes")}
    dangling = [m for m in g["memberIds"] if m not in node_ids]
    check("remove:no-dangling-members", dangling == [], f"dangling={dangling}")
    check("remove:group-kept", len(g["memberIds"]) == 1)

    # 分组盒必须按剩余成员重算：x = member.x - 28, 宽 = member.w + 56
    surv = state["surviving"][0]
    exp_x = surv["x"] - GROUP_PADDING
    exp_y = surv["y"] - GROUP_PADDING
    exp_w = surv["w"] + GROUP_PADDING * 2
    exp_h = surv["h"] + GROUP_PADDING * 2
    check(
        "remove:box-recomputed",
        (g["box"]["x"], g["box"]["y"], g["box"]["w"], g["box"]["h"]) == (exp_x, exp_y, exp_w, exp_h),
        f"got={g['box']} expected=({exp_x},{exp_y},{exp_w},{exp_h})",
    )
    check(
        "remove:box-actually-changed",
        g["box"] != setup["box"],
        f"before={setup['box']} after={g['box']}",
    )

    # ── 4 成员删空 → 分组消失，无残留选中态 ──
    page.evaluate("(id) => window.__frameos_store.getState().removeNode(id)", g["memberIds"][0])
    emptied = page.evaluate(
        "() => ({ groups: window.__frameos_store.getState().groups.length,"
        " selectedGroupId: window.__frameos_store.getState().selectedGroupId })"
    )
    check("empty:group-dropped", emptied["groups"] == 0)
    check("empty:selection-cleared", emptied["selectedGroupId"] is None)

    # ── 5 撤销恢复节点，分组不回到悬空状态 ──
    setup3 = page.evaluate(SETUP_JS)
    page.evaluate("(gid) => { window.__groupId = gid; }", setup3["groupId"])
    page.evaluate("(id) => { window.__victimId = id; }", setup3["memberIds"][0])
    page.evaluate("(id) => window.__frameos_store.getState().removeNode(id)", setup3["memberIds"][0])
    page.evaluate("() => window.__frameos_store.getState().undo()")
    page.wait_for_timeout(300)
    after_undo = page.evaluate(
        """() => {
          const st = window.__frameos_store;
          const g = st.getState().groups.find((x) => x.id === window.__groupId);
          const ids = new Set(st.getState().nodes.map((n) => n.id));
          return {
            nodeRestored: ids.has(window.__victimId),
            groupPresent: !!g,
            dangling: g ? g.memberIds.filter((m) => !ids.has(m)) : null,
          };
        }"""
    )
    check("undo:node-restored", after_undo["nodeRestored"])
    check("undo:group-present", after_undo["groupPresent"])
    check("undo:no-dangling", after_undo["dangling"] == [], f"dangling={after_undo['dangling']}")

    # ── 6 排列作用于存活成员，且分组盒始终贴合存活成员 bbox ──
    # 注意：只剩 1 个成员时，水平/垂直/宫格排列**本就不应改变几何**（单元素布局
    # 等于自身 bbox + 28）。因此这里断言的是不变式「盒 = 存活成员 bbox + 28」，
    # 而不是「排列一定改变盒」——后者对单成员是错误断言。
    arrange = page.evaluate(
        """(gid) => {
          const st = window.__frameos_store;
          const P = 28;
          const sizeOf = (n) => ({ w: (n.style && n.style.width) || 300,
                                   h: (n.style && n.style.height) || 200 });
          const measure = () => {
            const g = st.getState().groups.find((x) => x.id === gid);
            const mem = st.getState().nodes.filter((n) => g.memberIds.includes(n.id));
            const minX = Math.min(...mem.map((n) => n.position.x));
            const minY = Math.min(...mem.map((n) => n.position.y));
            const maxX = Math.max(...mem.map((n) => n.position.x + sizeOf(n).w));
            const maxY = Math.max(...mem.map((n) => n.position.y + sizeOf(n).h));
            return { box: {x:g.x,y:g.y,w:g.w,h:g.h}, members: mem.length,
                     expected: { x: minX - P, y: minY - P,
                                 w: maxX - minX + P*2, h: maxY - minY + P*2 } };
          };
          st.getState().arrangeGroup(gid, 'horizontal');
          const after = measure();
          st.getState().arrangeGroup(gid, 'grid');
          const afterGrid = measure();
          return { after, afterGrid };
        }""",
        setup3["groupId"],
    )
    check("arrange:members-kept", arrange["after"]["members"] >= 1)
    for label, snap in (("horizontal", arrange["after"]), ("grid", arrange["afterGrid"])):
        b, e = snap["box"], snap["expected"]
        check(
            f"arrange:{label}-box-tight",
            (b["x"], b["y"], b["w"], b["h"]) == (e["x"], e["y"], e["w"], e["h"]),
            f"box={b} expected={e}",
        )

    # ── 7 无分组时删除普通节点不受影响 ──
    # 用真实 action 解散现有分组（而非 store.set —— zustand v5 不再暴露 set）
    page.evaluate(
        "() => { const st = window.__frameos_store;"
        " st.getState().groups.forEach((g) => st.getState().ungroup(g.id)); }"
    )
    plain = page.evaluate(
        """() => {
          const st = window.__frameos_store;
          const before = st.getState().nodes.length;
          const victim = st.getState().nodes[0].id;
          st.getState().removeNode(victim);
          return { before, after: st.getState().nodes.length, groups: st.getState().groups.length };
        }"""
    )
    check("plain:node-removed", plain["after"] == plain["before"] - 1)
    check("plain:groups-still-empty", plain["groups"] == 0)

    check("diagnostics:zero", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 328,
        "title": "FrameOS group integrity on member delete (dangling refs + stale group box)",
        "defect": (
            "removeNode filtered only nodes/edges; groups[].memberIds kept referencing "
            "deleted nodes and the group box was never recomputed, so the group overlay "
            "kept stale geometry and arrange/drag/ungroup operated on a wrong member set."
        ),
        "fix": (
            "added reconcileGroups(groups, nodes): prune dangling members, recompute the "
            "member bbox + 28 padding, drop groups whose members are all gone, and clear "
            "selectedGroupId when its group disappears"
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
        "Batch 328 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "Deleting a group member prunes dangling refs, recomputes the group box around "
        "surviving members, drops emptied groups, and undo keeps membership consistent."
    )


if __name__ == "__main__":
    main()
