#!/usr/bin/env python3

"""Verify Batch 327: 节点克隆 id 碰撞修复 (duplicate/paste 同毫秒唯一性).

缺陷（克隆侧，非源站行为差异）: `duplicateNode` / `duplicateNodeAt` /
`pasteNodeFromClipboard` 此前用裸 `Date.now()` 生成节点 id。React Flow 以
`data-id` 索引节点，同一毫秒内连续两次 ⌘D / ⌘V 会产生**相同 id**，
后写入的副本覆盖前者 —— 用户按两次只多出一个节点（节点静默丢失）。
`addNode`（Batch 223）与 `createGroup`（Batch 272）早已用单调计数器修过同类问题。

修复: 追加 `nodeCloneIdCounter`，与既有解法一致。

断言:
1. 同一 tick 连续两次 duplicateNode → 节点总数 +2，id 全部唯一;
2. 同一 tick 连续两次 pasteNodeFromClipboard → 节点总数 +2，id 全部唯一;
3. 对照组 addNode 同样 tick 两次无碰撞（防回归时误改既有解法）;
4. 真实键盘路径：连按 Meta+d 三次 → DOM 渲染节点数 = store 节点数（不丢节点）;
5. 真实键盘路径：⌘C 后连按 Meta+v 两次 → 同样无丢失且可逐级撤销;
6. 诊断零错误。
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright

from frameos_verify_common import goto_clean_canvas, is_dev_server_noise

ROOT = Path(__file__).resolve().parents[1]
BASE_URL = os.environ.get("LIBLIB_BASE_URL", "http://localhost:4317")
AUDIT_PATH = (
    ROOT
    / "docs"
    / "research"
    / "liblib-frameos-batch327-2026-10-01"
    / "runtime-audit.json"
)

# 同一 JS tick 内连续触发克隆操作 —— 复现同毫秒 id 碰撞的最小条件。
CLONE_ID_JS = """
(mode) => {
  const st = window.__frameos_store;
  if (!st) return { error: 'no store' };
  const target = st.getState().nodes[0];
  if (!target) return { error: 'no nodes' };
  const before = st.getState().nodes.length;

  if (mode === 'duplicate') {
    st.getState().duplicateNode(target.id);
    st.getState().duplicateNode(target.id);
  } else if (mode === 'paste') {
    st.getState().copyNodeToClipboard(target.id);
    st.getState().pasteNodeFromClipboard();
    st.getState().pasteNodeFromClipboard();
  } else {
    st.getState().addNode('text');
    st.getState().addNode('text');
  }

  const ids = st.getState().nodes.map((n) => n.id);
  return {
    before,
    after: ids.length,
    total: ids.length,
    unique: new Set(ids).size,
    collisions: [...new Set(ids.filter((id, i) => ids.indexOf(id) !== i))],
  };
}
"""


def attach_errors(page: Page) -> list[str]:
    errors: list[str] = []
    page.on(
        "console",
        lambda message: errors.append(f"console:{message.type}:{message.text}")
        if message.type == "error"
        else None,
    )
    page.on("pageerror", lambda error: errors.append(f"pageerror:{error}"))
    page.on(
        "requestfailed",
        lambda request: errors.append(
            f"requestfailed:{request.method}:{request.url}:{request.failure}"
        )
        if not is_dev_server_noise(
            f"requestfailed:{request.method}:{request.url}:{request.failure}"
        )
        else None,
    )
    return errors


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool, detail: str = "") -> None:
        assert ok, f"batch327 check failed: {name} {detail}".strip()
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(f"{BASE_URL}/frameos/canvas/demo", wait_until="domcontentloaded", timeout=90000)
    page.wait_for_selector(".react-flow__node", timeout=30000)
    page.wait_for_timeout(1200)

    # ── 1/2/3 store 层：同 tick 连发，id 必须唯一且数量正确增长 ──
    dup = page.evaluate(CLONE_ID_JS, "duplicate")
    check("store:duplicate-no-error", "error" not in dup)
    check("store:duplicate-added-two", dup["after"] - dup["before"] == 2)
    check("store:duplicate-ids-unique", dup["collisions"] == [], f"collisions={dup['collisions']}")

    paste = page.evaluate(CLONE_ID_JS, "paste")
    check("store:paste-no-error", "error" not in paste)
    check("store:paste-added-two", paste["after"] - paste["before"] == 2)
    check("store:paste-ids-unique", paste["collisions"] == [], f"collisions={paste['collisions']}")

    add = page.evaluate(CLONE_ID_JS, "addnode")
    check("store:addnode-ids-unique", add["after"] - add["before"] == 2 and add["unique"] == add["total"])

    # ── 4 真实键盘路径：连按 ⌘D 三次，DOM 渲染数必须等于 store 节点数 ──
    # Batch 334: 自 Batch 333 起内容真的跨刷新持久化，上面 store 层测试造出的
    # 副本会被 restore 回来并互相重叠 → click 被 intercept 而超时。
    # 故此处必须回到**干净起点**再测键盘路径。
    goto_clean_canvas(page, BASE_URL)

    page.locator(".react-flow__node").first.click()
    page.wait_for_timeout(400)
    before_kbd = page.locator(".react-flow__node").count()
    for _ in range(3):
        page.keyboard.press("Meta+d")
        page.wait_for_timeout(120)
    page.wait_for_timeout(700)
    after_kbd = page.locator(".react-flow__node").count()
    store_count = page.evaluate("() => window.__frameos_store.getState().nodes.length")
    store_unique = page.evaluate(
        "() => { const ids = window.__frameos_store.getState().nodes.map((n) => n.id);"
        "return new Set(ids).size; }"
    )
    check("kbd:cmd-d-added-three", after_kbd == before_kbd + 3)
    check("kbd:cmd-d-no-node-loss", after_kbd == store_count, f"dom={after_kbd} store={store_count}")
    check("kbd:cmd-d-ids-unique", store_unique == store_count)

    # ── 5 真实键盘路径：⌘C 后连按 ⌘V 两次，逐级撤销回到初始 ──
    goto_clean_canvas(page, BASE_URL)

    page.locator(".react-flow__node").first.click()
    page.wait_for_timeout(300)
    page.keyboard.press("Meta+c")
    page.wait_for_timeout(250)
    base = page.locator(".react-flow__node").count()
    for _ in range(2):
        page.keyboard.press("Meta+v")
        page.wait_for_timeout(150)
    page.wait_for_timeout(700)
    pasted = page.locator(".react-flow__node").count()
    check("kbd:cmd-v-added-two", pasted == base + 2)

    page.keyboard.press("Meta+z")
    page.wait_for_timeout(500)
    check("kbd:paste-undo-one", page.locator(".react-flow__node").count() == base + 1)
    page.keyboard.press("Meta+z")
    page.wait_for_timeout(500)
    check("kbd:paste-undo-two", page.locator(".react-flow__node").count() == base)

    check("diagnostics:zero", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 327,
        "title": "FrameOS node clone id collision fix (duplicate/paste same-ms uniqueness)",
        "defect": (
            "duplicateNode/duplicateNodeAt/pasteNodeFromClipboard used bare Date.now() "
            "for node ids; two clones within the same millisecond produced identical ids, "
            "React Flow indexed by data-id and the later clone overwrote the earlier one "
            "(silent node loss)."
        ),
        "fix": "added nodeCloneIdCounter, matching the existing addNode/createGroup remedy",
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
        "Batch 327 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "Same-tick duplicate/paste keep unique node ids, no node loss on repeated "
        "Cmd+D/Cmd+V, undo steps back one node at a time."
    )


if __name__ == "__main__":
    main()
