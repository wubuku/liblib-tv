#!/usr/bin/env python3
"""Batch 345 探针：⌘Z / ⌘⇧Z 在「无东西可撤销/重做」时是否谎报成功。

疑点（克隆侧，不依赖源站）:
`page.tsx` 的 ⌘Z 分支此前是
    undo();
    showToast("已撤销", "info");
而 `undo()` 在 `past.length === 0` 时**直接 return，什么都没做**。
于是撤销栈为空时按 ⌘Z，用户看到一条「已撤销」提示，画布纹丝不动。

与 Batch 344 的「已删除分组」是同一类：**UI 声称完成了一个它没有完成的动作**。
⌘Z/⌘⇧Z 是使用频率最高的快捷键之一，这条比右键菜单更容易撞上
（新开画布、刷新后历史清空 —— Batch 333 刻意只持久化内容不持久化历史，
所以**每次刷新后历史栈必然为空**，也就是说刷新后的第一次 ⌘Z 必然撒谎）。

本探针走完整 UI 路径（真实键盘事件），并同时读 store 的 undo 返回值。

用法: ~/.venvs/liblib-harness/bin/python scripts/probe-frameos-batch345-undo-toast.py
"""

import json
import sys

from playwright.sync_api import sync_playwright

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from frameos_verify_common import attach_errors, goto_clean_canvas  # noqa: E402

BASE_URL = "http://localhost:4317"

STATE_JS = """
() => {
  const s = window.__frameos_store.getState();
  return { pastDepth: s.past.length, futureDepth: s.future.length,
           nodeCount: s.nodes.length };
}
"""

# 直接问 store: undo/redo 到底做了什么
RETURN_JS = """
() => {
  const st = window.__frameos_store;
  const before = { past: st.getState().past.length, future: st.getState().future.length };
  const undoResult = st.getState().undo();
  const afterUndo = { past: st.getState().past.length, future: st.getState().future.length };
  const redoResult = st.getState().redo();
  const afterRedo = { past: st.getState().past.length, future: st.getState().future.length };
  return { before, undoResult, afterUndo, redoResult, afterRedo };
}
"""


def toasts(page):
    return page.evaluate(
        """() => Array.from(
             document.querySelectorAll('[data-frameos-toast], .frameos-toast, .toast')
           ).map((e) => e.textContent)"""
    )


def main() -> int:
    out: dict = {}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1600, "height": 950})
        errors = attach_errors(page)
        goto_clean_canvas(page, BASE_URL)

        # ── 场景 1: 干净起点 (past/future 都空) 按 ⌘Z ──
        out["clean_state"] = page.evaluate(STATE_JS)
        page.keyboard.press("Meta+z")
        page.wait_for_timeout(500)
        out["after_undo_empty"] = page.evaluate(STATE_JS)
        out["toast_undo_empty"] = toasts(page)

        # ── 场景 2: 仍无 future 时按 ⌘⇧Z ──
        page.keyboard.press("Meta+Shift+z")
        page.wait_for_timeout(500)
        out["after_redo_empty"] = page.evaluate(STATE_JS)
        out["toast_redo_empty"] = toasts(page)

        # ── 场景 3: store 层面 undo/redo 的返回值 ──
        out["returns_empty"] = page.evaluate(RETURN_JS)

        # ── 场景 4: 制造一次可撤销的编辑, 再按 ⌘Z (应真的撤销且说「已撤销」) ──
        page.evaluate(
            """() => {
              const st = window.__frameos_store;
              st.getState().addNode('text');
              return true;
            }"""
        )
        page.wait_for_timeout(400)
        out["after_add"] = page.evaluate(STATE_JS)
        page.keyboard.press("Meta+z")
        page.wait_for_timeout(500)
        out["after_undo_real"] = page.evaluate(STATE_JS)
        out["toast_undo_real"] = toasts(page)

        # ── 场景 5: 再按一次 ⌘Z (栈已空) ──
        page.wait_for_timeout(2500)   # 等上一条 toast 消失
        page.keyboard.press("Meta+z")
        page.wait_for_timeout(500)
        out["toast_undo_exhausted"] = toasts(page)
        out["returns_exhausted"] = page.evaluate(RETURN_JS)

        out["consoleErrors"] = errors
        browser.close()

    print("=== batch345 撤销/重做 toast 探针 ===")
    print(f"干净起点: {out['clean_state']}")
    print(f"空栈按 ⌘Z  → 栈 {out['after_undo_empty']}  toast={out['toast_undo_empty']}")
    print(f"空栈按 ⌘⇧Z → 栈 {out['after_redo_empty']}  toast={out['toast_redo_empty']}")
    print(f"store 返回值(空栈): undo={out['returns_empty']['undoResult']} "
          f"redo={out['returns_empty']['redoResult']}")
    print(f"加节点后: {out['after_add']}")
    print(f"真按 ⌘Z  → 栈 {out['after_undo_real']}  toast={out['toast_undo_real']}")
    print(f"再按 ⌘Z  → toast={out['toast_undo_exhausted']} "
          f"(past={out['returns_exhausted']['afterUndo']['past']})")
    if out["consoleErrors"]:
        print(f"console errors: {out['consoleErrors']}")

    undo_empty = out["toast_undo_empty"]
    redo_empty = out["toast_redo_empty"]
    exhausted = out["toast_undo_exhausted"]
    print("\n=== 判定 ===")
    print(json.dumps({
        "undo_empty_claims_success": any("已撤销" in t for t in undo_empty),
        "redo_empty_claims_success": any("已重做" in t for t in redo_empty),
        "undo_exhausted_claims_success": any("已撤销" in t for t in exhausted),
        "undo_returns_bool": isinstance(out["returns_empty"]["undoResult"], bool),
        "real_undo_says_done": any("已撤销" in t for t in out["toast_undo_real"]),
        "real_undo_actually_undid": out["after_undo_real"]["nodeCount"] < out["after_add"]["nodeCount"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
