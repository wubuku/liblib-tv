#!/usr/bin/env python3

"""Verify Batch 345: ⌘Z / ⌘⇧Z 不再谎报成功。

缺陷（克隆侧，用户高频可达）:
`page.tsx` 的 ⌘Z 分支此前是

    undo();
    showToast("已撤销", "info");

而 `undo()` 在 `past.length === 0` 时**直接 return，什么都没做**。
于是撤销栈为空时按 ⌘Z，用户看到一条「已撤销」，画布纹丝不动。

这条比 Batch 344 的右键菜单更容易撞上：Batch 333 刻意**只持久化内容、不持久化
历史**，所以**每次刷新后撤销栈必然为空** —— 刷新后的第一次 ⌘Z 必然撒谎。

同类的第二个缺陷让本缺陷此前**无法被测出来**：toast 元素只有内联样式、没有任何
标识，任何验证器都抓不到它 —— 而 toast 文案正是「UI 是否谎报」的唯一证据。
现补 `data-frameos-toast` / `data-frameos-toast-variant`（仓库里已有
`data-frameos-context-menu` 等同类约定）。

修复: `undo()` / `redo()` 返回**是否真的执行**（boolean），toast 据此选择
诚实文案：真撤销说「已撤销」，无栈可说「没有可撤销的操作」。

断言:
1. `undo()` / `redo()` 返回**布尔**（不再是 void）;
2. 空栈按 ⌘Z：toast **不含**「已撤销」，而是「没有可撤销的操作」;
3. 空 future 按 ⌘⇧Z：toast 不含「已重做」，而是「没有可重做的操作」;
4. 真编辑后按 ⌘Z：toast 说「已撤销」**且节点数真的减少**（文案与事实一致）;
5. 撤销耗尽后再按 ⌘Z：回到「没有可撤销的操作」;
6. ⌘Z 后按 ⌘⇧Z：说「已重做」**且节点数真的恢复**;
7. toast 元素可被选择器寻址（可测性修复本身）;
8. 诊断零错误。
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
    / "liblib-frameos-batch345-2026-10-01"
    / "runtime-audit.json"
)
sys.path.insert(0, str(ROOT / "scripts"))
from frameos_verify_common import attach_errors, goto_clean_canvas  # noqa: E402

STATE_JS = """
() => {
  const s = window.__frameos_store.getState();
  return { pastDepth: s.past.length, futureDepth: s.future.length,
           nodeCount: s.nodes.length };
}
"""

RETURNS_JS = """
() => {
  const st = window.__frameos_store;
  return {
    undo: st.getState().undo(),
    redo: st.getState().redo(),
  };
}
"""


def toasts(page: Page) -> list[str]:
    return page.evaluate(
        """() => Array.from(document.querySelectorAll('[data-frameos-toast]'))
             .map((e) => e.textContent)"""
    )


def press_and_read(page: Page, key: str, wait: int = 450) -> tuple[list[str], dict]:
    page.keyboard.press(key)
    page.wait_for_timeout(wait)
    return toasts(page), page.evaluate(STATE_JS)


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool, detail: str = "") -> None:
        assert ok, f"batch345 check failed: {name} {detail}".strip()
        result["checks"].append(name)

    errors = attach_errors(page)
    goto_clean_canvas(page, BASE_URL)

    # ── 1 undo/redo 返回布尔 ──
    returns = page.evaluate(RETURNS_JS)
    result["returns_on_empty"] = returns
    check("api:undo-returns-bool", isinstance(returns["undo"], bool),
          f"undo returned {returns['undo']!r}")
    check("api:redo-returns-bool", isinstance(returns["redo"], bool),
          f"redo returned {returns['redo']!r}")
    check("api:empty-stack-returns-false",
          returns["undo"] is False and returns["redo"] is False,
          f"{returns}")

    # ── 2 空栈按 ⌘Z ──
    t_empty_undo, s_empty_undo = press_and_read(page, "Meta+z")
    result["empty_undo"] = {"toasts": t_empty_undo, "state": s_empty_undo}
    check("undo:empty-not-claimed", not any("已撤销" in t for t in t_empty_undo),
          f"toasts={t_empty_undo}")
    check("undo:empty-says-honest", any("没有可撤销" in t for t in t_empty_undo),
          f"toasts={t_empty_undo}")
    check("undo:empty-changed-nothing", s_empty_undo["pastDepth"] == 0,
          f"pastDepth={s_empty_undo['pastDepth']}")

    # ── 7 toast 元素可被选择器寻址（可测性修复本身）──
    # 绑的是**真实性质**: 触发 toast 后, 按 data-frameos-toast 能定位到它,
    # 且文案与文案数组一致。曾经的写法 `count() >= 0` 是恒真式, 被本仓
    # verify-assertions.py 门禁当场抓出 (Batch 336 门禁第一次抓到本会话新增的
    # 违规者 —— 门禁对自己人一样有效)。
    located = page.locator("[data-frameos-toast]")
    check("toast:addressable-by-selector", located.count() >= 1,
          f"count={located.count()} toasts={t_empty_undo}")
    check("toast:text-matches-dom",
          [located.nth(i).inner_text().strip() for i in range(located.count())]
          == [t.strip() for t in t_empty_undo],
          f"dom={[located.nth(i).inner_text() for i in range(located.count())]} "
          f"probe={t_empty_undo}")
    check("toast:variant-exposed",
          located.first.get_attribute("data-frameos-toast-variant") == "info",
          f"variant={located.first.get_attribute('data-frameos-toast-variant')}")

    # ── 3 空 future 按 ⌘⇧Z ──
    t_empty_redo, _ = press_and_read(page, "Meta+Shift+z")
    result["empty_redo"] = {"toasts": t_empty_redo}
    check("redo:empty-not-claimed", not any("已重做" in t for t in t_empty_redo),
          f"toasts={t_empty_redo}")
    check("redo:empty-says-honest", any("没有可重做" in t for t in t_empty_redo),
          f"toasts={t_empty_redo}")

    # ── 4 真编辑后按 ⌘Z: 文案与事实必须一致 ──
    page.wait_for_timeout(2500)          # 等旧 toast 消失
    page.evaluate(
        "() => { window.__frameos_store.getState().addNode('text'); return true; }"
    )
    page.wait_for_timeout(400)
    after_add = page.evaluate(STATE_JS)
    t_real_undo, s_real_undo = press_and_read(page, "Meta+z")
    result["real_undo"] = {"toasts": t_real_undo, "state": s_real_undo,
                           "after_add": after_add}
    check("undo:real-says-done", any("已撤销" == t.strip() for t in t_real_undo),
          f"toasts={t_real_undo}")
    check("undo:real-actually-undid",
          s_real_undo["nodeCount"] == after_add["nodeCount"] - 1,
          f"{after_add['nodeCount']} → {s_real_undo['nodeCount']}")
    check("undo:real-moved-to-future", s_real_undo["futureDepth"] >= 1,
          f"futureDepth={s_real_undo['futureDepth']}")

    # ── 5 撤销耗尽后再按 ⌘Z ──
    page.wait_for_timeout(2500)
    t_exhausted, s_exhausted = press_and_read(page, "Meta+z")
    result["exhausted"] = {"toasts": t_exhausted, "state": s_exhausted}
    check("undo:exhausted-says-honest", any("没有可撤销" in t for t in t_exhausted),
          f"toasts={t_exhausted}")
    check("undo:exhausted-not-claimed", not any("已撤销" in t for t in t_exhausted),
          f"toasts={t_exhausted}")

    # ── 6 ⌘Z 后按 ⌘⇧Z: 说「已重做」且节点数真的恢复 ──
    page.wait_for_timeout(2500)
    page.evaluate(
        "() => { window.__frameos_store.getState().addNode('text'); return true; }"
    )
    page.wait_for_timeout(400)
    before_redo = page.evaluate(STATE_JS)
    press_and_read(page, "Meta+z")
    mid = page.evaluate(STATE_JS)
    t_redo, s_redo = press_and_read(page, "Meta+Shift+z")
    result["redo"] = {"toasts": t_redo, "state": s_redo, "before": before_redo,
                      "mid": mid}
    check("redo:real-says-done", any("已重做" == t.strip() for t in t_redo),
          f"toasts={t_redo}")
    check("redo:real-actually-redid",
          s_redo["nodeCount"] == before_redo["nodeCount"],
          f"{mid['nodeCount']} → {s_redo['nodeCount']} want {before_redo['nodeCount']}")

    check("diagnostics:zero", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 345,
        "title": "FrameOS undo/redo no longer claims success when there is nothing to undo",
        "defect": (
            "The ⌘Z handler called undo() and then unconditionally showed a '已撤销' "
            "toast, but undo() returns early when past is empty -- so with an empty "
            "history the user was told the action had been undone while the canvas did "
            "not move. This is easy to hit: Batch 333 deliberately persists content but "
            "NOT history, so after every page refresh the undo stack is empty and the "
            "first ⌘Z always lies. A second defect made this untestable: the toast "
            "elements had only inline styles and no identifying attribute, so no "
            "verifier could ever assert the toast text -- which is the only evidence of "
            "whether the UI is lying."
        ),
        "fix": (
            "undo()/redo() now return a boolean saying whether they actually ran, and "
            "the keyboard handler picks an honest message from it ('已撤销' vs "
            "'没有可撤销的操作'). Toast elements gained data-frameos-toast / "
            "data-frameos-toast-variant so their text is assertable, matching the "
            "data-frameos-* convention already used elsewhere in the codebase."
        ),
        "clone_decision": (
            "This is clone-internal honesty, not a source-parity claim: showing '已撤销' "
            "for an action that did not happen is wrong regardless of what the source "
            "site does, and the source's behaviour with an empty history was NOT sampled "
            "(blocked by the human-verification gate, see "
            "SOURCE_ACCESS_BLOCKED_2026-10-01.md)."
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
        "Batch 345 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "⌘Z / ⌘⇧Z now say '没有可撤销的操作' / '没有可重做的操作' when there is "
        "nothing to undo, and only say '已撤销' / '已重做' when the canvas actually "
        "changed -- and the toast text is now assertable by verifiers."
    )


if __name__ == "__main__":
    main()
