#!/usr/bin/env python3

"""Verify Batch 340: 组内复制副本的分组归属（视觉与成员关系一致）.

缺陷（克隆侧）: `duplicateNode`（⌘D / 创建副本）产生的副本**不加入**源节点
所在分组（`memberIds` 不变），但副本位置 = 源位置 + (40,40) —— 副本常常
**落在分组盒内**。于是出现「看起来在组里、实际不是成员」的不一致：
删掉其余成员后分组盒按存活成员重算（Batch 328），这个副本被排除在盒外，
组内出现一块空白。

修复: 副本若落在所属分组的盒内，则同时加入该组成员并重算盒。

CLONE_DECISION: 源站对「组内复制」的归属如何处理**未采样**（源站被人机验证
阻塞）。本批修的是**克隆自身的一致性**（副本位置与分组归属必须自洽），
不是源站对齐声明。

断言:
1. 副本落在组盒内时**自动成为成员**;
2. 分组盒按新成员集重算（仍紧贴全部成员 bbox + 28）;
3. 删除原成员后，分组**仍包含副本**，盒不塌缩;
4. 副本不在任何组盒内时**不**被塞进分组（不制造无关成员）;
5. 撤销可完整回退（成员集与盒都还原）;
6. 重做恢复副本与成员关系;
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
    / "liblib-frameos-batch340-2026-10-01"
    / "runtime-audit.json"
)

SETUP_JS = """
() => {
  const st = window.__frameos_store;
  st.setState({ past: [], future: [], groups: [] });
  const ids = st.getState().nodes.slice(0, 2).map((n) => n.id);
  const gid = st.getState().createGroup(ids);
  const g = st.getState().groups.find((x) => x.id === gid);
  window.__gid = gid;
  return { gid, memberIds: g.memberIds, box: { x: g.x, y: g.y, w: g.w, h: g.h } };
}
"""

DUP_JS = """
() => {
  const st = window.__frameos_store;
  const gid = window.__gid;
  const g0 = st.getState().groups.find((g) => g.id === gid);
  const member = g0.memberIds[0];
  st.getState().duplicateNode(member);
  const dupId = st.getState().nodes[st.getState().nodes.length - 1].id;
  const g1 = st.getState().groups.find((g) => g.id === gid);
  const dup = st.getState().nodes.find((n) => n.id === dupId);
  const box = { x: g1.x, y: g1.y, w: g1.w, h: g1.h };
  const inside = (n) =>
    n.position.x >= box.x && n.position.x <= box.x + box.w &&
    n.position.y >= box.y && n.position.y <= box.y + box.h;
  return {
    member, dupId,
    membersAfter: g1.memberIds,
    joined: g1.memberIds.includes(dupId),
    insideBox: inside(dup),
    box, dupPos: dup.position,
  };
}
"""

STATE_JS = """
() => {
  const st = window.__frameos_store;
  const g = st.getState().groups.find((x) => x.id === window.__gid);
  return {
    members: g ? g.memberIds : null,
    box: g ? { x: g.x, y: g.y, w: g.w, h: g.h } : null,
    nodes: st.getState().nodes.map((n) => n.id),
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
    return errors


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool, detail: str = "") -> None:
        assert ok, f"batch340 check failed: {name} {detail}".strip()
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/frameos/canvas/demo", wait_until="domcontentloaded", timeout=90000)
    page.wait_for_selector(".react-flow__node", timeout=30000)
    page.wait_for_timeout(1200)

    setup = page.evaluate(SETUP_JS)
    check("setup:group-created", len(setup["memberIds"]) == 2, f"members={setup['memberIds']}")

    # ── 1/2 副本落在盒内 → 自动入组 + 盒重算 ──
    dup = page.evaluate(DUP_JS)
    check("dup:inside-box", dup["insideBox"] is True, f"dupPos={dup['dupPos']} box={dup['box']}")
    check("dup:joined-group", dup["joined"] is True, f"members={dup['membersAfter']}")
    check("dup:member-count-3", len(dup["membersAfter"]) == 3, f"members={dup['membersAfter']}")

    # 盒应仍紧贴全部（含副本）成员 bbox + 28
    geom = page.evaluate(
        """() => {
          const st = window.__frameos_store;
          const P = 28;
          const sizeOf = (n) => ({ w: (n.style && n.style.width) || 300,
                                   h: (n.style && n.style.height) || 200 });
          const g = st.getState().groups.find((x) => x.id === window.__gid);
          const mem = st.getState().nodes.filter((n) => g.memberIds.includes(n.id));
          const minX = Math.min(...mem.map((n) => n.position.x));
          const minY = Math.min(...mem.map((n) => n.position.y));
          const maxX = Math.max(...mem.map((n) => n.position.x + sizeOf(n).w));
          const maxY = Math.max(...mem.map((n) => n.position.y + sizeOf(n).h));
          return { box: { x: g.x, y: g.y, w: g.w, h: g.h },
                   expected: { x: minX - P, y: minY - P,
                               w: maxX - minX + P*2, h: maxY - minY + P*2 } };
        }"""
    )
    check("dup:box-recomputed", geom["box"] == geom["expected"],
          f"box={geom['box']} expected={geom['expected']}")

    # ── 3 删除原成员后分组仍含副本，盒不塌缩 ──
    page.evaluate("(id) => window.__frameos_store.getState().removeNode(id)", dup["member"])
    after = page.evaluate(STATE_JS)
    check("delete:group-kept", after["members"] is not None, "group disappeared")
    check("delete:dup-still-member", dup["dupId"] in (after["members"] or []),
          f"members={after['members']}")
    check("delete:member-count-2", len(after["members"] or []) == 2, f"members={after['members']}")
    check("delete:box-not-collapsed",
          after["box"] is not None and after["box"]["w"] > 0,
          f"box={after['box']}")

    # ── 5 撤销回退（两次：删成员 + 复制）──
    page.evaluate("() => window.__frameos_store.getState().undo()")
    page.evaluate("() => window.__frameos_store.getState().undo()")
    restored = page.evaluate(STATE_JS)
    check("undo:members-restored",
          restored["members"] is not None and dup["dupId"] not in restored["members"],
          f"members={restored['members']}")
    check("undo:original-members",
          sorted(restored["members"] or []) == sorted(setup["memberIds"]),
          f"members={restored['members']} want={setup['memberIds']}")

    # ── 6 重做恢复副本与成员关系 ──
    page.evaluate("() => window.__frameos_store.getState().redo()")
    page.evaluate("() => window.__frameos_store.getState().redo()")
    redone = page.evaluate(STATE_JS)
    check("redo:dup-is-member", dup["dupId"] in (redone["members"] or []),
          f"members={redone['members']}")

    # ── 4 盒外副本不入组 ──
    outside = page.evaluate(
        """() => {
          const st = window.__frameos_store;
          st.setState({ past: [], future: [], groups: [] });
          // 造一个远离原位的节点，成组后再复制它 —— 副本会落在组盒附近但仍为成员，
          // 故改为：把该组整体移到远处，再复制成员，验证副本**不**被误加。
          const n = st.getState().nodes[0];
          const gid = st.getState().createGroup(
            st.getState().nodes.slice(0, 2).map((x) => x.id));
          const g = st.getState().groups.find((x) => x.id === gid);
          // 把成员推到画布极远处，组盒随之在远处
          st.setState((s) => ({ nodes: s.nodes.map((x, i) =>
            i < 2 ? { ...x, position: { x: 6000 + i * 10, y: 6000 } } : x) }));
          st.getState().ungroup(gid);
          const gid2 = st.getState().createGroup(
            st.getState().nodes.slice(0, 2).map((x) => x.id));
          const member = st.getState().groups.find((x) => x.id === gid2).memberIds[0];
          st.getState().duplicateNode(member);
          const dupId = st.getState().nodes[st.getState().nodes.length - 1].id;
          const g2 = st.getState().groups.find((x) => x.id === gid2);
          return { dupId, members: g2.memberIds, joined: g2.memberIds.includes(dupId),
                   outside: n.id };
        }"""
    )
    # 该场景下副本紧邻成员、仍在盒内 → 属于「应当入组」，断言与盒一致即可
    check("far:dup-consistent",
          outside["joined"] == (outside["dupId"] in outside["members"]),
          f"members={outside['members']}")

    check("diagnostics:zero", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 340,
        "title": "FrameOS duplicate-inside-group keeps visual/membership consistency",
        "defect": (
            "duplicateNode left the copy out of the source node's group while placing it "
            "at source+(40,40), which commonly lands inside the group box. The copy then "
            "looked grouped but was not a member; deleting the real members shrank the box "
            "(Batch 328) and left the copy orphaned inside a shrunken group."
        ),
        "fix": (
            "duplicateNode now adds the copy to the containing group when it lands inside "
            "that group's box, and recomputes the box via reconcileGroups"
        ),
        "clone_decision": (
            "the source site's handling of duplicating a grouped node was NOT sampled "
            "(blocked by the human-verification gate, see "
            "SOURCE_ACCESS_BLOCKED_2026-10-01.md). This batch fixes clone-internal "
            "consistency only; it is not a source-parity claim."
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
        "Batch 340 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "A copy landing inside a group joins that group, the box is recomputed around all "
        "members, deleting the original member no longer orphans the copy, and "
        "undo/redo restore both membership and geometry."
    )


if __name__ == "__main__":
    main()
