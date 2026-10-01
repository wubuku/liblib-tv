"""Batch 349 只读复现探针: 生成完成后「生成完成 ✓」toast 重复派发。

怀疑 (静态): FrameosGenerationOverlay 的 tick 由 setInterval(50ms) 驱动,
`if (p >= 100)` 分支里排一个 setTimeout(500) 清 currentGeneration —— 但
**interval 不会因此停下**, 于是 p>=100 之后的每一个 tick 都会再排一个
setTimeout(500)。第一个 timeout 在 t=30000+500 触发, 把 currentGeneration
置 null 触发 effect 清理; 而它之前排的那 ~10 个 timeout 仍会陆续触发,
每次都 dispatch 一次 frameos-toast 事件 → showToast 无去重 → 堆成一摞。

本探针只读: 不改任何产品代码, 只观测真实 toast 数量。
"""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from playwright.sync_api import sync_playwright  # noqa: E402

from frameos_verify_common import FRAMEOS_DEMO_URL, attach_errors, goto_clean_canvas  # noqa: E402

OUT = Path(__file__).resolve().parent.parent / "docs/research/liblib-frameos-batch349-2026-10-01"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        errs = attach_errors(page)
        goto_clean_canvas(page)

        # 记录所有 frameos-toast 事件派发次数 (不止 DOM 里最终残留的)
        page.evaluate(
            """() => {
                window.__toastEvents = [];
                window.addEventListener('frameos-toast', (e) => {
                    window.__toastEvents.push(e.detail && e.detail.message);
                });
            }"""
        )

        # 7 个 fixture 节点全是 text / 带 imageUrl 的 image+video,
        # FrameosPromptEditor 对它们一律 return null —— 主面板(含生成按钮)只对
        # 「无媒体内容的生成节点」渲染。所以先加一个空图片节点。
        pane = page.locator(".react-flow__pane")
        box = pane.bounding_box()
        cx = box["x"] + box["width"] * 0.25
        cy = box["y"] + box["height"] * 0.30
        pane.dblclick(position={"x": cx, "y": cy})
        page.wait_for_selector("[data-frameos-pane-addnode-type]", timeout=5000)
        page.locator('[data-frameos-pane-addnode-type="image"]').click()
        page.wait_for_timeout(600)

        before = page.locator(".react-flow__node").count()
        # 选中刚加的节点
        page.locator(".react-flow__node").last.click()
        page.wait_for_timeout(600)

        gen_btn = page.get_by_label("生成", exact=True)
        if gen_btn.count() == 0:
            print(f"FAIL: 找不到生成按钮 (节点数 {before})")
            browser.close()
            return 1
        gen_btn.first.click()
        page.wait_for_timeout(500)

        # 覆盖层本身没有任何 data-* 钩子(Batch 347 只覆盖了它普查到的可点元素),
        # 所以用「生成按钮变 disabled」(isRunning) 这个真实可观测量确认流程已启动。
        running = gen_btn.first.evaluate("el => el.disabled === true")

        # 进度浮窗 100% 后再等 1.5s, 让所有多余的 timeout 全部落地
        page.wait_for_timeout(32000)

        events = page.evaluate("() => window.__toastEvents")
        done_events = [m for m in events if m and "生成完成" in m]
        dom_toasts = page.evaluate(
            """() => Array.from(document.querySelectorAll('[data-frameos-toast]'))
                 .map(e => e.textContent)"""
        )
        dom_done = [t for t in dom_toasts if "生成完成" in (t or "")]

        report = {
            "overlay_present_while_running": running,
            "toast_event_count_total": len(events),
            "toast_events": events,
            "done_event_count": len(done_events),
            "dom_toast_count": len(dom_toasts),
            "dom_done_toast_count": len(dom_done),
            "dom_toasts": dom_toasts,
            "errors": errs,
        }
        (OUT / "runtime-audit.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2)
        )
        print(json.dumps(report, ensure_ascii=False, indent=2))
        browser.close()

        if len(done_events) > 1:
            print(f"\nREPRODUCED: 「生成完成」toast 派发 {len(done_events)} 次 (应为 1)")
            return 1
        if len(done_events) == 0:
            print("\nINCONCLUSIVE: 一次都没派发 —— 探针没打中流程")
            return 2
        print("\nOK: 恰好派发 1 次")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
