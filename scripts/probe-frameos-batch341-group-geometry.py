#!/usr/bin/env python3
"""Batch 341 探针：分组盒几何不变式在**非 store action 路径**上是否被绕过。

背景（Batch 340 的教训 —— 只测一条分支等于没测）：
Batch 328 给 `reconcileGroups()` 修好了「删成员后分组盒不收敛」，但只挂在
store 的 `removeNode` 一条路径上。本探针审计**其它**会改动 nodes 的路径：

  S1 一键整理 (FrameosMapDock → organizeNodes)  — 用户可达按钮
     整理把**所有**节点重排到网格，成员坐标全变，但分组盒 x/y/w/h 不重算。
  S2 拖拽成员 (page.tsx onNodesChange → setNodes) — 用户可达
     拖动单个成员离开原位，分组盒不跟随。
  S3 节点面板「删除节点」(FrameosNodeEditPanel → setNodes) — 仅 debug 模式
     绕过 removeNode 直接 setNodes(filter) → 悬空成员 + 盒不收敛。

不变式（克隆自洽性，CLONE_DECISION）：分组盒恒等于「存活成员包围盒 + 28 padding」。
本探针只测克隆自身一致性，不声称源站如何处理（源站阻塞，见
SOURCE_ACCESS_BLOCKED_2026-10-01.md）。

用法: ~/.venvs/liblib-harness/bin/python scripts/probe-frameos-batch341-group-geometry.py
"""

import json
import sys

from playwright.sync_api import sync_playwright

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from frameos_verify_common import FRAMEOS_DEMO_URL, attach_errors, goto_clean_canvas  # noqa: E402

# 读取 store 现状并按「存活成员包围盒 + padding」算出应有分组盒
SNAPSHOT_JS = """
() => {
  const st = window.__frameos_store;
  const PAD = 28;
  const s = st.getState();
  const out = s.groups.map((g) => {
    const members = g.memberIds
      .map((id) => s.nodes.find((n) => n.id === id))
      .filter(Boolean);
    const dangling = g.memberIds.filter(
      (id) => !s.nodes.some((n) => n.id === id)
    );
    let expected = null;
    if (members.length > 0) {
      const sizeOf = (n) => ({
        w: (n.style && n.style.width) || 300,
        h: (n.style && n.style.height) || 200,
      });
      const minX = Math.min(...members.map((n) => n.position.x));
      const minY = Math.min(...members.map((n) => n.position.y));
      const maxX = Math.max(...members.map((n) => n.position.x + sizeOf(n).w));
      const maxY = Math.max(...members.map((n) => n.position.y + sizeOf(n).h));
      expected = {
        x: minX - PAD,
        y: minY - PAD,
        w: maxX - minX + PAD * 2,
        h: maxY - minY + PAD * 2,
      };
    }
    const actual = { x: g.x, y: g.y, w: g.w, h: g.h };
    const drift =
      expected === null
        ? null
        : ["x", "y", "w", "h"].filter(
            (k) => Math.abs(actual[k] - expected[k]) > 0.5
          );
    return {
      groupId: g.id,
      memberIds: g.memberIds,
      dangling,
      actual,
      expected,
      driftKeys: drift,
      STALE: drift !== null && drift.length > 0,
      // 成员全被删却还留着分组，或反之
      GONE: expected === null,
    };
  });
  return {
    nodeCount: s.nodes.length,
    groupCount: s.groups.length,
    groups: out,
  };
}
"""

# 建组：清历史/分组后用前两个节点建一组，返回该组 id 与首成员 id
SETUP_JS = """
() => {
  const st = window.__frameos_store;
  st.setState({ past: [], future: [], groups: [] });
  const ids = st.getState().nodes.slice(0, 2).map((n) => n.id);
  const gid = st.getState().createGroup(ids);
  return { gid, members: st.getState().groups.find((g) => g.id === gid).memberIds };
}
"""

DRAG_OUT_JS = """
() => {
  // 把第一个成员直接挪到很远 —— 等价于用户把它拖出分组范围
  const st = window.__frameos_store;
  const s = st.getState();
  const gid = s.groups[0].id;
  const victim = s.groups[0].memberIds[0];
  st.getState().setNodes(
    s.nodes.map((n) =>
      n.id === victim ? { ...n, position: { x: n.position.x + 900, y: n.position.y + 600 } } : n
    )
  );
  return { gid, victim, movedVia: "store.setNodes (与 onNodesChange 拖拽同一入口)" };
}
"""

DELETE_VIA_PANEL_SETUP_JS = """
() => {
  const st = window.__frameos_store;
  st.setState({ past: [], future: [], groups: [] });
  st.getState().toggleDebugMode();   // 节点编辑面板仅 debug 模式渲染
  const ids = st.getState().nodes.slice(0, 2).map((n) => n.id);
  const gid = st.getState().createGroup(ids);
  const member = st.getState().groups.find((g) => g.id === gid).memberIds[0];
  st.getState().selectNode(member);
  return { gid, member, debugMode: st.getState().isDebugMode };
}
"""


def drift_lines(label: str, snap: dict) -> list[str]:
    lines = [f"--- {label} ---"]
    if not snap["groups"]:
        lines.append("  (无分组)")
        return lines
    for g in snap["groups"]:
        flag = "STALE" if g["STALE"] else "ok"
        if g["dangling"]:
            flag += f" DANGLING={g['dangling']}"
        if g["GONE"]:
            flag += " GONE(成员全没了却还在)"
        lines.append(f"  [{flag}] actual={g['actual']}")
        if g["STALE"]:
            lines.append(f"          expected={g['expected']} drift={g['driftKeys']}")
        lines.append(f"          members={g['memberIds']}")
    return lines


def main() -> int:
    out: dict = {}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1600, "height": 950})
        errors = attach_errors(page)
        goto_clean_canvas(page, "http://localhost:4317")

        # ---------- S1: 一键整理 ----------
        page.evaluate(SETUP_JS)
        out["s1_before"] = page.evaluate(SNAPSHOT_JS)
        # 真实点击「一键整理 · 网格整理」按钮 (DockBtn 用的是 aria-label, 不是 title)
        btn = page.locator('button[aria-label="一键整理 · 网格整理"]')
        if btn.count() == 0:
            out["s1_error"] = "找不到「一键整理」按钮"
        else:
            btn.first.click()
            page.wait_for_timeout(900)
        out["s1_after"] = page.evaluate(SNAPSHOT_JS)
        out["s1_organizeReached"] = page.evaluate(
            "() => { const s = window.__frameos_store.getState();"
            " return { pastDepth: s.past.length, positions: s.nodes.slice(0, 3).map(n => n.position) }; }"
        )

        # ---------- S2: 拖拽成员 ----------
        page.evaluate(SETUP_JS)
        out["s2_before"] = page.evaluate(SNAPSHOT_JS)
        out["s2_drag"] = page.evaluate(DRAG_OUT_JS)
        page.wait_for_timeout(400)
        out["s2_after"] = page.evaluate(SNAPSHOT_JS)

        # ---------- S3: 节点面板「删除节点」 ----------
        out["s3_setup"] = page.evaluate(DELETE_VIA_PANEL_SETUP_JS)
        page.wait_for_timeout(500)
        del_btn = page.locator("button", has_text="删除节点")
        # confirm 是同步阻塞弹窗, Playwright 的 dialog 自动处理会与 once 处理器
        # 竞态 ("already handled") → 直接覆写 window.confirm, 行为确定。
        page.evaluate("() => { window.confirm = () => true; }")
        if del_btn.count() == 0:
            out["s3_error"] = "找不到「删除节点」按钮（debug 模式面板未渲染）"
        else:
            try:
                # 面板按节点屏幕坐标 fixed 定位，可能落在视口外 → force
                del_btn.first.click(force=True, timeout=5000)
            except Exception as exc:  # noqa: BLE001
                out["s3_click_error"] = f"{type(exc).__name__}: {exc}"
                del_btn.first.dispatch_event("click")
            page.wait_for_timeout(700)
        out["s3_after"] = page.evaluate(SNAPSHOT_JS)
        out["s3_nodeCount"] = page.evaluate(
            "() => window.__frameos_store.getState().nodes.length"
        )

        out["consoleErrors"] = errors
        browser.close()

    print("=== batch341 分组盒几何不变式探针 ===")
    if out.get("s1_error"):
        print(f"--- S1 --- \n  {out['s1_error']}")
    print(drift_lines("S1 一键整理 前", out["s1_before"]))
    print(drift_lines("S1 一键整理 后", out["s1_after"]))
    print(f"  organize 生效痕迹: {out.get('s1_organizeReached')}")
    print(drift_lines("S2 拖拽成员 前", out["s2_before"]))
    print(drift_lines("S2 拖拽成员 后", out["s2_after"]))
    if out.get("s3_error") or out.get("s3_click_error"):
        print(f"--- S3 --- \n  {out.get('s3_error') or out.get('s3_click_error')}")
    print(drift_lines("S3 面板删除 后", out["s3_after"]))
    print(f"  节点数(前 9): {out.get('s3_nodeCount')}")
    if out["consoleErrors"]:
        print(f"console errors: {out['consoleErrors']}")

    verdicts = {
        "S1_organize_stale": any(g["STALE"] for g in out["s1_after"]["groups"]),
        "S2_drag_stale": any(g["STALE"] for g in out["s2_after"]["groups"]),
        "S3_panel_delete_dangling": any(
            g["dangling"] for g in out["s3_after"]["groups"]
        ),
    }
    print("\n=== 判定 ===")
    print(json.dumps(verdicts, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
