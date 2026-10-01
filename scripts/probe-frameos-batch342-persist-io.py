#!/usr/bin/env python3
"""Batch 342 探针：拖动分组时 Batch 333 的持久化订阅是否**每帧**同步写 localStorage。

疑点（克隆侧，不依赖源站）:
Batch 333 用 store 订阅把「内容变更」写进 localStorage，判据是
`state.nodes !== lastNodes || state.edges !== lastEdges || state.groups !== lastGroups`
——**按引用**。而分组拖拽的 `onPointerMove` 每帧调 `moveGroup`
(FrameosGroupCanvas.tsx:76)，每帧都产出新的 nodes/groups 引用 →
每帧一次 `JSON.stringify(全部画布)` + 同步 `localStorage.setItem`。

后果：拖动分组时主线程被序列化 I/O 占住，拖拽掉帧；画布越大越明显
（写的是**所有画布**的完整内容，不只是当前画布）。

本探针只测克隆自身行为（写了几次、写了多久、多大），不声称源站如何实现
（源站阻塞，见 SOURCE_ACCESS_BLOCKED_2026-10-01.md）。

用法: ~/.venvs/liblib-harness/bin/python scripts/probe-frameos-batch342-persist-io.py
"""

import json
import sys

from playwright.sync_api import sync_playwright

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from frameos_verify_common import attach_errors, goto_clean_canvas  # noqa: E402

BASE_URL = "http://localhost:4317"

# 计量 localStorage 写入次数/耗时/字节数
INSTRUMENT_JS = """
() => {
  const orig = Storage.prototype.setItem;
  window.__io = { calls: 0, ms: 0, bytes: 0, maxBytes: 0 };
  Storage.prototype.setItem = function (k, v) {
    const t0 = performance.now();
    orig.call(this, k, v);
    const dt = performance.now() - t0;
    const n = typeof v === 'string' ? v.length : 0;
    window.__io.calls += 1;
    window.__io.ms += dt;
    window.__io.bytes += n;
    if (n > window.__io.maxBytes) window.__io.maxBytes = n;
    return undefined;
  };
  return true;
}
"""

IO_JS = """
() => ({ ...window.__io, payloadKB: Math.round(window.__io.maxBytes / 1024) })
"""

RESET_IO_JS = "() => { window.__io.calls = 0; window.__io.ms = 0; window.__io.bytes = 0; window.__io.maxBytes = 0; return true; }"

SETUP_JS = """
() => {
  const st = window.__frameos_store;
  st.setState({ past: [], future: [], groups: [] });
  const ids = st.getState().nodes.slice(0, 3).map((n) => n.id);
  const gid = st.getState().createGroup(ids);
  return { gid, memberIds: st.getState().groups.find((g) => g.id === gid).memberIds };
}
"""


def main() -> int:
    out: dict = {}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1600, "height": 950})
        errors = attach_errors(page)
        goto_clean_canvas(page, BASE_URL)

        out["setup"] = page.evaluate(SETUP_JS)
        page.wait_for_timeout(600)

        box = page.locator(".frameos-canvas-group").first.bounding_box()
        if not box:
            print("!! 找不到分组盒")
            return 1
        # 分组盒是覆盖层, 标题栏区域最安全 (避开四角 resize 手柄)
        start_x = box["x"] + box["width"] / 2
        start_y = box["y"] + 12

        page.evaluate(INSTRUMENT_JS)
        page.evaluate(RESET_IO_JS)

        STEPS = 40
        page.mouse.move(start_x, start_y)
        page.mouse.down()
        for i in range(STEPS):
            page.mouse.move(start_x + (i + 1) * 6, start_y + (i + 1) * 3)
            page.wait_for_timeout(8)
        page.mouse.up()
        page.wait_for_timeout(400)

        out["io_during_drag"] = page.evaluate(IO_JS)
        out["steps"] = STEPS
        out["group_moved"] = page.evaluate(
            "() => { const g = window.__frameos_store.getState().groups[0];"
            " return g ? { x: g.x, y: g.y } : null; }"
        )

        # 对照: 一次**普通**节点拖拽也每帧写? (onNodesChange → setNodes)
        page.evaluate(RESET_IO_JS)
        node = page.locator(".react-flow__node").first.bounding_box()
        if node:
            page.mouse.move(node["x"] + node["width"] / 2, node["y"] + node["height"] / 2)
            page.mouse.down()
            for i in range(STEPS):
                page.mouse.move(
                    node["x"] + node["width"] / 2 + (i + 1) * 5,
                    node["y"] + node["height"] / 2 + (i + 1) * 4,
                )
                page.wait_for_timeout(8)
            page.mouse.up()
            page.wait_for_timeout(400)
        out["io_during_node_drag"] = page.evaluate(IO_JS)

        # ── 规模化: 载荷随画布大小线性增长, 必须在**真实体量**下再判一次 ──
        scale = page.evaluate(
            """(total) => {
              const st = window.__frameos_store;
              st.setState({ past: [], future: [], groups: [] });
              const base = st.getState().nodes;
              const made = [];
              for (let i = 0; i < total; i += 1) {
                made.push({
                  id: `scale-${i}`,
                  type: 'text',
                  position: { x: 40 + (i % 20) * 320, y: 40 + Math.floor(i / 20) * 220 },
                  style: { width: 300, height: 200 },
                  data: { title: `扩容节点 ${i}`, content: 'x'.repeat(200) },
                });
              }
              st.getState().setNodes([...base, ...made]);
              return { total: base.length + made.length };
            }""",
            280,
        )
        page.wait_for_timeout(500)
        page.evaluate(
            """() => {
              const st = window.__frameos_store;
              st.setState({ groups: [] });
              const ids = st.getState().nodes.slice(0, 60).map((n) => n.id);
              st.getState().createGroup(ids);
              return true;
            }"""
        )
        page.wait_for_timeout(400)
        out["scale_setup"] = page.evaluate(
            "() => { const s = window.__frameos_store.getState();"
            " return { groups: s.groups.length,"
            "         members: s.groups[0] ? s.groups[0].memberIds.length : 0,"
            "         nodes: s.nodes.length }; }"
        )
        # 扩容后的单次载荷 (量一次无关写入的 settle)
        page.evaluate(RESET_IO_JS)
        page.evaluate(
            "() => { window.__frameos_store.getState().toggleMinimap();"
            " window.__frameos_store.getState().toggleMinimap(); return true; }"
        )
        page.wait_for_timeout(200)
        out["scaled_payload"] = page.evaluate(IO_JS)
        # 扩容后分组盒远在视口外, 鼠标事件落不中 → 直接驱动 moveGroup
        # (与 onPointerMove 调的是同一个 action, 存储写入路径完全一致)
        page.evaluate(RESET_IO_JS)
        page.evaluate(
            """(steps) => {
              const st = window.__frameos_store;
              const gid = st.getState().groups[0].id;
              for (let i = 0; i < steps; i += 1) st.getState().moveGroup(gid, 1, 1);
              return true;
            }""",
            STEPS,
        )
        page.wait_for_timeout(400)
        out["io_during_scaled_drag"] = page.evaluate(IO_JS)
        out["scaled_group_moved"] = page.evaluate(
            "() => { const g = window.__frameos_store.getState().groups[0];"
            " return g ? { x: g.x, y: g.y } : null; }"
        )

        out["consoleErrors"] = errors
        browser.close()

    drag = out["io_during_drag"]
    ndrag = out["io_during_node_drag"]
    sdrag = out["io_during_scaled_drag"]
    print("=== batch342 持久化 I/O 探针 ===")
    print(f"[小画布 fixture] 分组拖拽 {out['steps']} 帧 → 写入 {drag['calls']} 次, "
          f"累计 {drag['ms']:.1f} ms, 单次最大载荷 {drag['payloadKB']} KB")
    print(f"[小画布 fixture] 节点拖拽 {out['steps']} 帧 → 写入 {ndrag['calls']} 次, "
          f"累计 {ndrag['ms']:.1f} ms, 单次最大载荷 {ndrag['payloadKB']} KB")
    print(f"[扩容 {out['scale_setup']['nodes']} 节点 / 组内 {out['scale_setup']['members']} 成员] "
          f"{out['steps']} 次 moveGroup → 写入 {sdrag['calls']} 次, "
          f"累计 {sdrag['ms']:.1f} ms, 单次最大载荷 {sdrag['payloadKB']} KB")
    print(f"  扩容场景单次载荷 KB: {out['scaled_payload']['payloadKB']}")
    print(f"  → 每帧一次: 小={drag['calls'] >= out['steps']} "
          f"扩容={sdrag['calls'] >= out['steps']}")
    print(f"分组确实移动了: 小={out['group_moved']} 扩容={out['scaled_group_moved']}")
    if errors:
        print(f"console errors: {errors}")
    print("\n=== 判定 ===")
    print(json.dumps({
        "group_drag_writes": drag["calls"],
        "group_drag_ms": round(drag["ms"], 1),
        "scaled_node_count": out["scale_setup"]["nodes"],
        "scaled_writes": sdrag["calls"],
        "scaled_ms": round(sdrag["ms"], 1),
        "scaled_payloadKB": sdrag["payloadKB"],
        "scaled_ms_per_frame": round(sdrag["ms"] / max(1, out["steps"]), 2),
        "one_write_per_frame": drag["calls"] >= out["steps"] and sdrag["calls"] >= out["steps"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
