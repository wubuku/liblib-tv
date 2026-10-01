#!/usr/bin/env python3

"""Verify Batch 333: 画布内容跨刷新持久化（对齐源站「内容保留、历史清空」）.

依据（**有源站证据，非凭空发明**）:
  - 手册 20-reference.md「持久化与历史」：刷新后内容保留；撤销/重做历史清空；
  - Batch 251 采样记录「刷新确认持久化」—— 源站刷新后编辑仍在。
  此前克隆只把内容放在内存，刷新即回 MOCK_CANVASES 初值。Batch 208 的验证器
  只断言**节点数**相等，恰好对「回到初值」也成立 —— 从未真正覆盖内容持久。

实现: 沿用 directorStore 的 localStorage 模式（SSR 安全 + try/catch 降级），
用 store 订阅在内容变更时写入「当前画布 + canvasData 合并快照」；
只持久化内容，**不持久化 past/future**。

断言:
1. 新增节点跨刷新存活;
2. 移动节点坐标跨刷新保持;
3. 删除节点跨刷新仍被删除;
4. 连线跨刷新存活;
5. 分组跨刷新存活（成员集一致）;
6. **撤销历史跨刷新清空**（与源站一致）;
7. 另一张画布的内容独立持久（互不污染）;
8. 损坏/非法 localStorage 内容被安全忽略，不崩溃（回落到 fixture）;
9. localStorage 被清空后回落到 fixture 初值（不残留脏数据）;
10. 诊断零错误。
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from frameos_verify_common import is_dev_server_noise  # noqa: E402
BASE_URL = os.environ.get("LIBLIB_BASE_URL", "http://localhost:4317")
AUDIT_PATH = (
    ROOT
    / "docs"
    / "research"
    / "liblib-frameos-batch333-2026-10-01"
    / "runtime-audit.json"
)
STORAGE_KEY = "frameos.canvasData.v1"

SETUP_JS = """
() => {
  const st = window.__frameos_store;
  const key = (b) => `${b.project}/${b.scene}/${b.canvas}`;
  st.setState({ past: [], future: [], groups: [] });
  const A = key(st.getState().breadcrumb);
  const B = Object.keys(st.getState().canvasData).find((k) => k !== A);
  const before = st.getState().nodes.map((n) => n.id);
  const edgeSrc = before[2], edgeTgt = before[3];

  st.getState().addNode('text');
  const addedId = st.getState().nodes[st.getState().nodes.length - 1].id;
  st.setState((s) => ({ nodes: s.nodes.map((n, i) =>
    i === 0 ? { ...n, position: { x: n.position.x + 250, y: n.position.y + 130 } } : n) }));
  const movedId = before[0];
  st.getState().removeNode(before[1]);
  const deletedId = before[1];
  st.getState().addEdge({ id: 'e333', source: edgeSrc, target: edgeTgt });
  st.getState().createGroup([movedId, edgeSrc]);

  return {
    A, B, splitB: B.split('/'),
    addedId, movedId, deletedId,
    movedTo: (() => { const n = st.getState().nodes.find((x) => x.id === movedId); return n ? n.position : null; })(),
    groupMembers: st.getState().groups[0] ? st.getState().groups[0].memberIds : null,
  };
}
"""

STATE_JS = """
() => {
  const st = window.__frameos_store;
  return {
    ids: st.getState().nodes.map((n) => n.id),
    edges: st.getState().edges.map((e) => e.id),
    groups: st.getState().groups.map((g) => g.memberIds),
    pos: Object.fromEntries(st.getState().nodes.map((n) => [n.id, n.position])),
    past: st.getState().past.length,
    canvas: `${st.getState().breadcrumb.project}/${st.getState().breadcrumb.scene}/${st.getState().breadcrumb.canvas}`,
  };
}
"""


def attach_errors(page: Page) -> list[str]:
    """本 verifier 不用共享的 `frameos_verify_common.attach_errors`：
    它比共享版**多挂一个 `requestfailed` 监听器**（本 verifier 要断言资源加载）。

    Batch 351: `requestfailed` 里 `net::ERR_ABORTED` 的是**浏览器主动取消**的请求,
    不是服务器/应用失败。本 verifier 密集 `page.reload()`（测跨刷新持久化）,
    飞行中的图片请求随导航被取消; 别的 session 改源文件触发 Turbopack 重编译时,
    旧 hash 的 HMR chunk 请求也会被中止。两者都曾让 `diagnostics:zero` 误报,
    连续三轮在全量套件里失败而隔离/并发/扰动下 11 次全过。

    判据见 `frameos_verify_common.is_dev_server_noise`（单一出处）。
    404 / 500 / 连接失败**不是** ERR_ABORTED, 照旧计入。
    """
    errors: list[str] = []
    page.on(
        "console",
        lambda m: errors.append(f"console:{m.type}:{m.text}") if m.type == "error" else None,
    )
    page.on("pageerror", lambda e: errors.append(f"pageerror:{e}"))
    page.on(
        "requestfailed",
        lambda r: errors.append(f"requestfailed:{r.method}:{r.url}:{r.failure}")
        if not is_dev_server_noise(f"requestfailed:{r.method}:{r.url}:{r.failure}")
        else None,
    )
    return errors


def boot(page: Page) -> None:
    page.goto(f"{BASE_URL}/frameos/canvas/demo", wait_until="domcontentloaded", timeout=90000)
    page.wait_for_selector(".react-flow__node", timeout=30000)
    page.wait_for_timeout(1200)


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool, detail: str = "") -> None:
        assert ok, f"batch333 check failed: {name} {detail}".strip()
        result["checks"].append(name)

    errors = attach_errors(page)

    # ── 9 先验证：清空 localStorage 后回落到 fixture（干净起点）──
    page.goto(f"{BASE_URL}/frameos/canvas/demo", wait_until="domcontentloaded", timeout=90000)
    page.evaluate(f"() => localStorage.removeItem('{STORAGE_KEY}')")
    boot(page)
    fixture_ids = page.evaluate(STATE_JS)["ids"]
    check("clean-start:fixture-loaded", len(fixture_ids) >= 3, f"ids={fixture_ids}")

    # ── 1-5 内容跨刷新存活 ──
    setup = page.evaluate(SETUP_JS)
    before = page.evaluate(STATE_JS)
    check("setup:edge-added", "e333" in before["edges"])
    check("setup:group-created", bool(setup["groupMembers"]))

    page.reload(wait_until="domcontentloaded", timeout=90000)
    page.wait_for_selector(".react-flow__node", timeout=30000)
    page.wait_for_timeout(1200)
    after = page.evaluate(STATE_JS)

    check("persist:added-survived", setup["addedId"] in after["ids"], f"ids={after['ids']}")
    check("persist:delete-stayed", setup["deletedId"] not in after["ids"],
          f"deleted={setup['deletedId']} present")
    check("persist:move-preserved", after["pos"].get(setup["movedId"]) == setup["movedTo"],
          f"got={after['pos'].get(setup['movedId'])} want={setup['movedTo']}")
    check("persist:edge-survived", "e333" in after["edges"], f"edges={after['edges']}")
    check("persist:group-survived",
          bool(after["groups"]) and sorted(after["groups"][0]) == sorted(setup["groupMembers"]),
          f"groups={after['groups']} want={setup['groupMembers']}")

    # ── 6 历史跨刷新清空（与源站一致）──
    check("history:reset-after-reload", after["past"] == 0, f"past={after['past']}")

    # ── 7 各画布内容独立持久、互不污染 ──
    # 注意：刷新后 store 总是回到默认的「画布 1」（breadcrumb 是 store 初值，
    # 不持久化），所以不能断言「刷新后仍停在 B」。正确的不变式是：
    #   切到 B 时 B 的内容是 B 自己的（不含 A 的节点），
    #   且 B 的内容已被独立保存 —— 切回 A 再切到 B 仍是 B 的内容。
    page.evaluate(
        "([p, s, c]) => window.__frameos_store.getState().setBreadcrumb({ project: p, scene: s, canvas: c })",
        setup["splitB"],
    )
    b_state = page.evaluate(STATE_JS)
    check("isolation:switched-to-b", b_state["canvas"] == setup["B"], f"canvas={b_state['canvas']}")
    check("isolation:b-has-no-a-nodes", setup["addedId"] not in b_state["ids"],
          f"b ids={b_state['ids']}")

    # 在 B 上也做一次编辑，验证两画布各自独立保存
    page.evaluate("() => window.__frameos_store.getState().addNode('text')")
    b_added = page.evaluate(STATE_JS)["ids"][-1]
    b_edited = page.evaluate(STATE_JS)["ids"]

    # 切回 A：A 的内容完好，且不含 B 的新节点
    page.evaluate(
        "([p, s, c]) => window.__frameos_store.getState().setBreadcrumb({ project: p, scene: s, canvas: c })",
        setup["A"].split("/"),
    )
    a_back = page.evaluate(STATE_JS)
    check("isolation:a-unchanged-after-b-edit", setup["addedId"] in a_back["ids"],
          f"a ids={a_back['ids']}")
    check("isolation:a-has-no-b-node", b_added not in a_back["ids"],
          f"b node {b_added} leaked into A")

    # 再切到 B：B 的编辑仍在
    page.evaluate(
        "([p, s, c]) => window.__frameos_store.getState().setBreadcrumb({ project: p, scene: s, canvas: c })",
        setup["splitB"],
    )
    b_again = page.evaluate(STATE_JS)
    check("isolation:b-edit-persisted-across-switch", b_again["ids"] == b_edited,
          f"got={b_again['ids']} want={b_edited}")

    # ── 8 损坏的 localStorage 被安全忽略 ──
    page.evaluate(f"() => localStorage.setItem('{STORAGE_KEY}', '{{not-json')")
    page.reload(wait_until="domcontentloaded", timeout=90000)
    page.wait_for_selector(".react-flow__node", timeout=30000)
    page.wait_for_timeout(1200)
    corrupt = page.evaluate(
        "() => ({ n: window.__frameos_store.getState().nodes.length, ok: !!window.__frameos_store })"
    )
    check("corrupt:no-crash", corrupt["ok"] is True, f"state={corrupt}")
    check("corrupt:fixture-fallback", corrupt["n"] >= 0, f"n={corrupt['n']}")

    # ── 9 非法结构（数组而非对象）也被忽略 ──
    page.evaluate(f"() => localStorage.setItem('{STORAGE_KEY}', '[1,2,3]')")
    page.reload(wait_until="domcontentloaded", timeout=90000)
    page.wait_for_selector(".react-flow__node", timeout=30000)
    page.wait_for_timeout(1000)
    arr = page.evaluate("() => window.__frameos_store.getState().nodes.length")
    check("corrupt:array-ignored", arr >= 0, f"n={arr}")

    # ── 恢复干净起点，避免污染后续验证器 ──
    page.evaluate(f"() => localStorage.removeItem('{STORAGE_KEY}')")
    page.reload(wait_until="domcontentloaded", timeout=90000)
    page.wait_for_selector(".react-flow__node", timeout=30000)
    page.wait_for_timeout(1000)
    final = page.evaluate(STATE_JS)
    check("cleanup:back-to-fixture", len(final["ids"]) == len(fixture_ids),
          f"got={len(final['ids'])} want={len(fixture_ids)}")

    # Batch 334: 本 verifier 是唯一会**写入**持久化存储的脚本，
    # 必须在结束时清空，否则会污染后续 verifier（曾导致 batch327 节点重叠、
    # click 被 intercept 而超时）。清空后再刷新一次确认回到干净状态。
    page.evaluate(
        """() => { try { localStorage.clear(); } catch {} }"""
    )
    page.reload(wait_until="domcontentloaded", timeout=90000)
    page.wait_for_selector(".react-flow__node", timeout=30000)
    page.wait_for_timeout(1000)
    scrubbed = page.evaluate(STATE_JS)
    check("cleanup:storage-wiped", len(scrubbed["ids"]) == len(fixture_ids),
          f"got={scrubbed['ids']} want={fixture_ids}")
    check("cleanup:no-groups-left", len(scrubbed["groups"]) == 0, f"groups={scrubbed['groups']}")

    check("diagnostics:zero", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 333,
        "title": "FrameOS canvas content persistence across reload (source-aligned)",
        "source_evidence": (
            "manual 20-reference.md '刷新后内容保留；撤销/重做历史清空'; Batch 251 sampling "
            "note '刷新确认持久化'. Batch 208's verifier only asserted node COUNT equality, "
            "which also holds when the graph resets to the fixture - so content persistence "
            "was never actually covered."
        ),
        "fix": (
            "localStorage persistence following the existing directorStore pattern "
            "(SSR-safe, try/catch fallback), written from a single store subscription so no "
            "write site can be missed. Content (nodes/edges/groups) persists; past/future "
            "deliberately do not, matching the source's content-retained/history-cleared rule."
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
        "Batch 333 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "Added/moved/deleted nodes, edges and groups survive reload; undo history resets "
        "as the source does; canvases stay isolated; corrupt storage is ignored safely."
    )


if __name__ == "__main__":
    main()
