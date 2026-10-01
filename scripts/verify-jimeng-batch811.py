"""Jimeng clone batch 811 verifier — 浮层焦点管理：按**各层源站行为**分别对齐。

## 为什么要按层区别对待

SOURCE_FACT（@1680×826 登录态，逐层实测 activeElement + Tab 序列）显示
源站各浮层的焦点行为**并不一致**：

| 层 | 打开后焦点 | Tab 10 次逃出 | 关闭后焦点 |
|---|---|---|---|
| **节点摘要弹层** | 进入浮层 | **0（有焦点陷阱）** | **回到触发器** |
| AI 抽屉 | 进入 `aside[canvas-feature-sidecar]` | 10 | 停在抽屉内，不回触发器 |
| 分享面板 | **留在触发器**，不在浮层内 | 10 | 跑到页面别处 |

所以：
- 节点摘要弹层是源站**唯一做对了**的一层 → 复刻三项全补（进浮层 / 陷阱 / 归还）
- AI 抽屉只补"焦点进浮层" → 不加陷阱、不归还（源站就没做，加了是偏离）
- 分享 / 更多 / 项目面板**保持现状** → 源站本来就没管，加了是擅自"改进"

「全开」和「全关」都是错的：前者偏离源站，后者漏掉源站已做对的那一层。

## 复刻侧踩到的两个坑（都不是产品问题，是 hook 写法问题）

1. **假卸载会抢焦点**。实测日志 mount→cleanup→mount，且 cleanup 时宿主节点
   仍 `isConnected === true`。若在 cleanup 里同步归还焦点，会把第二次 mount
   刚聚焦的第一项抢回触发器 —— 表现为「焦点从不进浮层」。
   解法：归还推到微任务，并判 `root.isConnected`：真关闭时节点已 detach，
   假卸载时还在，只有前者才归还。
2. **触发器只能记一次**。第二次 mount 时 activeElement 已经是浮层内的项，
   照记就会把"触发器"记成浮层内部的节点，关闭时 `document.contains` 为 false，
   焦点掉到 body。解法：用 ref 存住第一次的值，真关闭时清空。
"""

import os
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "docs" / "design-references" / "jimeng"
BASE_URL = os.environ.get("JIMENG_BASE_URL", "http://localhost:4317")
CANVAS_URL = f"{BASE_URL}/jimeng/canvas/demo"
VIEWPORT = {"width": 1680, "height": 826}
POP = '[data-testid="topbar-node-summary"]'
TRIGGER = '[data-testid="canvas-node-summary-trigger"]'

ACTIVE_JS = """() => {
  const a = document.activeElement;
  if (!a || a === document.body) return {tag: 'body', tid: '', inLayer: false, inAgent: false};
  const pop = document.querySelector('[data-testid="topbar-node-summary"]');
  const agent = document.querySelector('[aria-label="Agent"]');
  return {
    tag: a.tagName.toLowerCase(),
    tid: a.getAttribute('data-testid') || a.getAttribute('aria-label') || '',
    inLayer: !!(pop && pop.contains(a)),
    inAgent: !!(agent && agent.contains(a)),
  };
}"""


def main() -> None:
    REFERENCE_DIR.mkdir(parents=True, exist_ok=True)
    failures: list[str] = []
    checks = 0

    def check(name: str, ok: bool, detail: str = "") -> None:
        nonlocal checks
        checks += 1
        if not ok:
            failures.append(f"{name}: {detail}")
        print(f"  [{'ok ' if ok else 'FAIL'}] {name}{'' if ok else ' — ' + detail}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport=VIEWPORT, locale="zh-CN")
        page = ctx.new_page()
        errors: list[str] = []
        page.on("console", lambda m: errors.append(f"console.{m.type}: {m.text}") if m.type == "error" else None)
        page.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))

        page.goto(CANVAS_URL, wait_until="domcontentloaded")
        page.wait_for_selector('[data-testid="canvas-top-bar"]', timeout=25000)
        page.wait_for_timeout(700)

        print("— 节点摘要弹层：源站唯一做对了焦点的一层，三项全补 —")
        page.locator(TRIGGER).click()
        page.wait_for_selector(POP, timeout=10000)
        page.wait_for_timeout(400)
        act = page.evaluate(ACTIVE_JS)
        check("打开后焦点进入浮层", act["inLayer"], str(act))
        check("落在浮层内的可聚焦元素上（不是 body）", act["tag"] == "button", str(act))

        escaped = 0
        for _ in range(12):
            page.keyboard.press("Tab")
            page.wait_for_timeout(60)
            if not page.evaluate(ACTIVE_JS)["inLayer"]:
                escaped += 1
        check("Tab 12 次全部困在浮层内（焦点陷阱）", escaped == 0, f"逃出 {escaped} 次")

        back = 0
        for _ in range(6):
            page.keyboard.press("Shift+Tab")
            page.wait_for_timeout(60)
            if not page.evaluate(ACTIVE_JS)["inLayer"]:
                back += 1
        check("Shift+Tab 反向也困在浮层内", back == 0, f"逃出 {back} 次")

        page.keyboard.press("Escape")
        page.wait_for_timeout(600)
        check("Escape 关闭浮层", page.locator(POP).count() == 0)
        act = page.evaluate(ACTIVE_JS)
        check("关闭后焦点归还触发器", act["tid"] == "canvas-node-summary-trigger", str(act))

        print("— 再开一次仍然成立（回归：不得被上一次会话影响）—")
        page.locator(TRIGGER).click()
        page.wait_for_selector(POP, timeout=10000)
        page.wait_for_timeout(400)
        check("二次打开焦点仍进浮层", page.evaluate(ACTIVE_JS)["inLayer"])
        page.keyboard.press("Escape")
        page.wait_for_timeout(500)
        act = page.evaluate(ACTIVE_JS)
        check("二次关闭焦点仍归还触发器", act["tid"] == "canvas-node-summary-trigger", str(act))

        print("— 点浮层外部关闭，也要归还 —")
        page.locator(TRIGGER).click()
        page.wait_for_selector(POP, timeout=10000)
        page.wait_for_timeout(300)
        page.mouse.click(900, 600)
        page.wait_for_timeout(600)
        check("点外部关闭浮层", page.locator(POP).count() == 0)
        act = page.evaluate(ACTIVE_JS)
        check("点外部关闭后焦点归还触发器", act["tid"] == "canvas-node-summary-trigger", str(act))

        print("— AI 抽屉：只补「焦点进浮层」，不加陷阱 —")
        page.mouse.click(1608, 796)
        page.wait_for_selector('[aria-label="Agent"]', timeout=10000)
        page.wait_for_timeout(500)
        act = page.evaluate(ACTIVE_JS)
        check("打开后焦点进入抽屉（源站同）", act["inAgent"], str(act))
        esc = 0
        for _ in range(10):
            page.keyboard.press("Tab")
            page.wait_for_timeout(60)
            if not page.evaluate(ACTIVE_JS)["inAgent"]:
                esc += 1
        # 源站是 10/10 逃出；不要求完全一致，但**不能**变成 0 —— 0 说明
        # 我们擅自加了陷阱，那是对源站的偏离。
        check("Tab 会逃出抽屉（未擅自加陷阱）", esc > 0, f"逃出 {esc}/10")
        page.locator('[data-testid="canvas-agent-session-collapse"]').click()
        page.wait_for_timeout(500)
        check("「收起」能关抽屉", page.locator('[aria-label="Agent"]').count() == 0)

        print("— 分享面板：源站本来就没管焦点，复刻保持原样 —")
        page.locator('[data-testid="canvas-share-trigger"]').click()
        page.wait_for_selector('[data-testid="topbar-share-panel"]', timeout=10000)
        page.wait_for_timeout(400)
        act = page.evaluate(ACTIVE_JS)
        check("分享面板焦点仍留在触发器（与源站一致）",
              act["tid"] == "canvas-share-trigger", str(act))
        page.keyboard.press("Escape")
        page.wait_for_timeout(400)

        print("— hook 契约 —")
        hook = (ROOT / "src" / "hooks" / "useLayerFocus.ts").read_text(encoding="utf-8")
        check("hook 提供 trap 与 returnTo 两项独立开关",
              "trap?: boolean" in hook and "returnTo?: boolean" in hook)
        check("归还焦点有 isConnected 守卫（防假卸载抢焦点）", "root.isConnected" in hook)
        check("触发器只记一次（openerRef）", "openerRef" in hook)

        print("— 回归 —")
        page.reload(wait_until="domcontentloaded")
        page.wait_for_selector('[data-testid="canvas-top-bar"]', timeout=25000)
        page.wait_for_timeout(800)
        check("刷新后画布仍是初始 2 节点", page.locator(".react-flow__node").count() == 2)
        check("无 console/page 错误", not errors, "; ".join(errors[:3]))
        ctx.close()
        browser.close()

    print()
    if failures:
        print(f"FAIL: {len(failures)}/{checks} 项未通过")
        for f in failures:
            print("  -", f)
        raise SystemExit(1)
    print(f"PASS: jimeng batch 811 浮层焦点管理按各层源站行为对齐（{checks} 项断言全通过）")


if __name__ == "__main__":
    main()
