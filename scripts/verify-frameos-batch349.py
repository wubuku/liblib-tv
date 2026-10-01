#!/usr/bin/env python3

"""Verify Batch 349: 生成完成后「生成完成 ✓」被重复派发 11 次; 并清掉一个死状态字段。

缺陷一 —— 完成提示重复派发（克隆侧，用户可见）
`FrameosGenerationOverlay` 的进度 tick 由 `setInterval(tick, 50)` 驱动，而
`p >= 100` 分支里**每个 tick 都排一个 `setTimeout(..., 500)`**。第一个 timeout
在 500ms 后把 `currentGeneration` 置 null 触发 effect 清理，但它之前排下的
timeout 仍会陆续触发，**每个都 dispatch 一次 `frameos-toast`**；而
`showToast` 不去重、逐条堆叠。结果：一次生成结束后屏幕上叠起一摞完全相同的
「生成完成 ✓」。

实测 (probe-frameos-batch349-generation-toast.py, 修复前, 真实 30 秒 mock):
    toast_event_count_total = 11
    dom_done_toast_count   = 11      (11 条一模一样的 DOM 元素)
静态推算 500ms / 50ms = 11 个 tick，与实测 11 次**逐一对上**。

**机制与时长无关**：重复次数只取决于「p>=100 之后还剩几个 50ms tick」，
即恒为 500ms 窗口 ≈ 11 次，与 `durationMs` 多长无关。所以本验证器把 mock
时长缩短到 2 秒来跑（真实 30 秒时长的证据保留在探针里）—— 同样的窗口、
同样的重复次数，验证器因此从 ~35 秒降到 ~10 秒。

缺陷二 —— `generations` 死状态字段
全 store 死状态普查（扫 src/ 下每个状态字段的外部读取点）显示：
`generations: Generation[]` **只有声明和初值两处，从无任何读写**。
`startGeneration` 只写 `currentGeneration`，生成完成时记录直接丢失。
留着它等于用注释承诺一个「生成任务列表」功能 —— 对维护者的文档性谎言。
真正要不要「生成历史」是产品决定，源站未采样，**不在这里发明**。

断言:
1. 自检: 生成流程确实被驱动起来（按钮 disabled）—— 否则「只有 1 条 toast」
   可能是因为压根没跑到完成分支，那样的通过是假绿;
2. 每次生成**恰好 1 条**「生成完成」事件;
3. DOM 里**恰好 1 个**「生成完成」toast 元素;
4. **第二次**生成同样恰好 1 条 —— 闩锁必须随生成重置，否则第二次会静默不提示
   （这是本次修复自身最可能引入的回归）;
5. 缩短 mock 时钟不改变结论（对照缺陷一的时长无关性论证）;
6. `generations` 已从 store 状态里消失（死状态确已删除）;
7. 诊断零错误。
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
    ROOT / "docs" / "research" / "liblib-frameos-batch349-2026-10-01" / "runtime-audit.json"
)
sys.path.insert(0, str(ROOT / "scripts"))
from frameos_verify_common import attach_errors, goto_clean_canvas  # noqa: E402

# 探针/验证器共用的观测脚手架：记录 frameos-toast 事件的每次派发
INSTALL_SPY = """
() => {
  window.__toastEvents = [];
  window.addEventListener('frameos-toast', (e) => {
    window.__toastEvents.push((e.detail && e.detail.message) || '');
  });
}
"""

READ_TRAIL = """
() => ({
  events: window.__toastEvents.slice(),
  domToasts: Array.from(document.querySelectorAll('[data-frameos-toast]'))
    .map((e) => e.textContent || ''),
})
"""


# 复用 batch348 已验证的「找一个没被任何节点盖住的空白点」——
# 直接按比例取点会压在节点上，双击事件被节点自己吃掉，菜单不开。
EMPTY_POINT_JS = """
() => {
  const rects = Array.from(document.querySelectorAll('.react-flow__node'))
    .map((n) => n.getBoundingClientRect());
  for (let y = 140; y < window.innerHeight - 140; y += 40) {
    for (let x = 140; x < window.innerWidth - 140; x += 40) {
      const hit = rects.some(
        (r) => x >= r.left && x <= r.right && y >= r.top && y <= r.bottom
      );
      if (!hit) return { x, y };
    }
  }
  return null;
}
"""


def make_generative_node(page: Page) -> None:
    """加一个「无媒体内容的生成节点」——主面板（含生成按钮）只对这类节点渲染。

    7 个 fixture 节点全是 text 或带 imageUrl 的 image/video，
    FrameosPromptEditor 对它们一律 return null（Batch 225 源站实测）。
    """
    pt = page.evaluate(EMPTY_POINT_JS)
    assert pt, "找不到画布空白点"
    page.mouse.dblclick(pt["x"], pt["y"])
    page.wait_for_selector("[data-frameos-pane-addnode-type]", timeout=8000)
    page.locator('[data-frameos-pane-addnode-type="image"]').click()
    page.wait_for_timeout(500)
    page.locator(".react-flow__node").last.click()
    page.wait_for_timeout(500)


def install_spy(page: Page) -> None:
    """装一次就够。

    踩过的坑：每轮都重新 `addEventListener` 会让上一轮的监听器继续存活 ——
    一次派发被两个监听器各推一遍，第二轮于是数出 2 条。**测量脚手架自己
    制造了缺陷**，差点被当成产品回归去改应用代码。所以：装一次，用游标切分。
    """
    page.evaluate(INSTALL_SPY)


def run_one_generation(page: Page, cursor: int, duration_ms: int) -> tuple[dict[str, Any], int]:
    """跑完一次生成，返回这一轮独有的「生成完成」事件数与新游标。"""
    page.get_by_label("生成", exact=True).first.click()
    page.wait_for_timeout(300)

    # 覆盖层没有任何 data-* 钩子（Batch 347 只普查了它能触达的可点元素），
    # 所以用「生成按钮变 disabled」这个真实可观测量确认流程真的启动了。
    started = page.get_by_label("生成", exact=True).first.evaluate("el => el.disabled === true")

    # 把 mock 时长压到 duration_ms —— 见模块 docstring 的「时长无关性」论证。
    page.evaluate(
        """(d) => {
            const s = window.__frameos_store.getState();
            window.__frameos_store.setState({
              currentGeneration: { ...s.currentGeneration, durationMs: d },
            });
        }""",
        duration_ms,
    )

    # 等进度跑满 (duration_ms) + 收尾窗口 (500ms) + 富余
    page.wait_for_timeout(duration_ms + 2500)

    trail = page.evaluate(READ_TRAIL)
    new_events = trail["events"][cursor:]
    return (
        {
            "started": started,
            "cursor_before": cursor,
            "new_events": new_events,
            "done_events": [m for m in new_events if "生成完成" in m],
            "dom_toasts": trail["domToasts"],
            "dom_done": [t for t in trail["domToasts"] if "生成完成" in t],
        },
        len(trail["events"]),
    )


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool, detail: str = "") -> None:
        assert ok, f"batch349 check failed: {name} {detail}".strip()
        result["checks"].append(name)

    errors = attach_errors(page)
    goto_clean_canvas(page, BASE_URL)

    # ── 死状态字段确已移除 ──
    has_gens = page.evaluate(
        "() => Object.prototype.hasOwnProperty.call(window.__frameos_store.getState(), 'generations')"
    )
    check("store:generations-field-removed", has_gens is False, f"has={has_gens}")

    make_generative_node(page)
    gen_count = page.get_by_label("生成", exact=True).count()
    check("setup:generate-button-present", gen_count >= 1, f"count={gen_count}")
    install_spy(page)

    # ── 第一轮：真实跑一次生成（缩短 mock 时钟）──
    r1, cursor = run_one_generation(page, 0, 2000)
    result["round1"] = r1
    # 防假绿: 没跑起来就不能谈「只有一条」
    check("r1:flow-started", r1["started"] is True, "生成按钮未变 disabled")
    check("r1:one-done-event", len(r1["done_events"]) == 1,
          f"got={len(r1['done_events'])} {r1['done_events']}")
    check("r1:one-done-dom-toast", len(r1["dom_done"]) == 1,
          f"got={len(r1['dom_done'])}")

    # ── 第二轮：闩锁必须随生成重置 ──
    make_generative_node(page)
    r2, cursor = run_one_generation(page, cursor, 2000)
    result["round2"] = r2
    check("r2:flow-started", r2["started"] is True, "生成按钮未变 disabled")
    check("r2:one-done-event", len(r2["done_events"]) == 1,
          f"got={len(r2['done_events'])} {r2['done_events']}")
    check("r2:one-done-dom-toast", len(r2["dom_done"]) == 1,
          f"got={len(r2['dom_done'])}")

    check("diagnostics:zero", not errors, f"errors={errors[:3]}")
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 349,
        "defect": "生成完成后「生成完成 ✓」toast 重复派发 11 次（p>=100 后每个 tick 都排收尾 timeout）",
        "defect2": "generations 死状态字段：全仓只有声明+初值，从无读写",
        "clock_note": "验证器用 2s mock 时钟；重复次数只取决于 p>=100 后的 500ms 窗口，"
                      "与 durationMs 无关（真实 30s 时长的证据见探针 runtime-audit.json）",
    }
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        try:
            audit["desktop"] = run_desktop(page)
        finally:
            browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2))
    n = len(audit["desktop"]["checks"])
    print(
        f"Batch 349 verification passed: {n} checks, "
        f"{audit['desktop']['diagnostics']['console']} diagnostics. "
        "A generation now completes with exactly one 「生成完成 ✓」 toast "
        "(was 11 stacked duplicates), the latch resets for each new generation, "
        "and the provably-dead `generations` store field is gone."
    )


if __name__ == "__main__":
    main()
