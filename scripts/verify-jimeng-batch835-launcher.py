#!/usr/bin/env python
"""batch 835 verifier —— 抽屉三枚浮层触发器的 `aria-expanded`，外加药丸的往返契约。

起因是**本地死按钮普查**把「与 AI 对话」报成 DEAD，而它自己 UNVERIFIABLE 里的
理由是复刻写的（批 826 照抄批 820 措辞、批 827 撤回过一次 —— 照抄自己写的豁免
同样不算证据）。于是本批去源站量了四刀（`scripts/jimeng_835_*.py`）：

| 源站实测 | 复刻 |
|---|---|
| 关闭态 button 118×34 / 药丸 120×36，`aria-expanded="false"`，面板**关着** | 一致 ✓ |
| 点一下 ⇒ 面板开 | 一致 ✓ |
| 开态那枚按钮仍在 DOM，缩成 59×17，`aria-expanded="true"` | **复刻把它卸载了** |
| 再点 ⇒ 面板关 | 复刻：面板由自己的「收起」钮关 |
| 会话列表 / + / 使用技能 三枚带 `aria-expanded` | **此前都没有** ← 本批补 |
| 引用参考那枚**没有** `aria-expanded` | 复刻也没有 ✓（别补） |

关于开态那 59×17 的残影：截图里它**看不见**，所以复刻卸载它对用户不可区分，
还少一个压在面板底缘的隐形热区 —— 因此**不照抄**（台账 §47 OPEN_QUESTION 835-a）。
但「面板打开时药丸不在 DOM」这件事本身要写成契约：将来谁照抄源站把那枚残影
挂回来，这条会红。

顺带：普查自身的复位漏了关抽屉（Escape 对它无效），已修 —— 见
`jimeng_dead_button_audit.py` 批 835 注释。
"""

from __future__ import annotations

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:4317"
VIEWPORT = {"width": 1680, "height": 826}

LAUNCHER = '[data-testid="canvas-sidecar-launcher"]'
PILL = '[data-testid="ai-trigger-pill"]'
DRAWER = '[data-testid="canvas-agent-drawer"]'

# 源站实测带 aria-expanded 的三枚 → 各自浮层容器
EXPANDABLE = [
    ("canvas-agent-session-menu-trigger", "canvas-agent-session-menu"),
    ("canvas-agent-composer-add", "agent-add-panel"),
    ("canvas-agent-skill-trigger", "agent-skills-panel"),
]
# 源站实测 expanded=None 的那一枚（面板普查 19 元素清单里它是 None）
NOT_EXPANDABLE = "canvas-agent-composer-mention"


def main() -> int:
    failures: list[str] = []
    passed = 0

    def check(name: str, ok: bool, detail: str = "") -> None:
        nonlocal passed
        if ok:
            passed += 1
        else:
            failures.append(f"{name}: {detail}")
        print(f"  [{'ok ' if ok else 'FAIL'}] {name}{'' if ok else ' — ' + detail}")

    def attr(page, sel: str, name: str) -> str | None:
        loc = page.locator(sel)
        return loc.first.get_attribute(name) if loc.count() else None

    def size(page, sel: str) -> tuple:
        box = page.locator(sel).first.bounding_box() or {}
        return (box.get("width"), box.get("height"))

    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        page = b.new_context(viewport=VIEWPORT, locale="zh-CN").new_page()
        errs: list[str] = []
        page.on("pageerror", lambda e: errs.append(str(e)[:160]))
        page.on("console", lambda m: errs.append(f"console.{m.type}: {m.text}") if m.type == "error" else None)
        try:
            page.goto(f"{BASE_URL}/jimeng/canvas/demo", wait_until="domcontentloaded")
            page.wait_for_selector('[data-testid="canvas-fixed-toolbar"]', timeout=60000)
            for _ in range(12):
                if page.evaluate("() => !!document.querySelector('.react-flow__node')"):
                    break
                page.wait_for_timeout(1000)

            print("— ① 默认态（源站实测：加载完成后面板是**关**的）—")
            check("默认态抽屉不存在", page.locator(DRAWER).count() == 0)
            check("药丸在", page.locator(LAUNCHER).count() == 1)
            check("药丸按钮 118×34（批 797 的值没被本批改坏）", size(page, LAUNCHER) == (118, 34),
                  str(size(page, LAUNCHER)))
            check("药丸底衬 120×36", size(page, PILL) == (120, 36), str(size(page, PILL)))
            check("药丸可访问名是「与 AI 对话」", attr(page, LAUNCHER, "aria-label") == "与 AI 对话",
                  str(attr(page, LAUNCHER, "aria-label")))

            print("— ② 点一下：开 —")
            page.locator(LAUNCHER).first.click()
            page.wait_for_selector(DRAWER, timeout=20000)
            page.wait_for_timeout(600)
            check("面板出现", page.locator(DRAWER).count() == 1)
            check("面板打开时药丸**不在 DOM**（复刻选定：不照抄源站那枚 59×17 残影）",
                  page.locator(LAUNCHER).count() == 0,
                  f"launcher={page.locator(LAUNCHER).count()}")

            print("— ③ 先发一条消息（会话列表钮无会话时是**禁用**的，源站契约）—")
            # 直接去点会话列表钮会超时：它 disabled（810/834 已验的源站契约）。
            # 这里顺手把契约也量一遍，再发消息把它解锁。
            check("无会话时「会话列表」禁用（源站契约，顺带量）",
                  page.locator('[data-testid="canvas-agent-session-menu-trigger"]').first.is_disabled())
            check("无会话时 aria-expanded 也是 false（禁用态不发「已展开」信号）",
                  attr(page, '[data-testid="canvas-agent-session-menu-trigger"]', "aria-expanded") == "false")
            page.locator('[data-testid="agent-composer-input"]').first.fill("测一下 aria-expanded")
            page.locator('[data-testid="canvas-agent-send"]').first.click()
            page.wait_for_timeout(700)
            check("发消息后有会话了", page.locator('[data-testid="agent-messages"]').count() == 1)
            check("有会话后「会话列表」解除禁用",
                  not page.locator('[data-testid="canvas-agent-session-menu-trigger"]').first.is_disabled())

            print("— ④ 三枚浮层触发器的 aria-expanded（源站实测有）—")
            for trigger_tid, panel_tid in EXPANDABLE:
                sel = f'[data-testid="{trigger_tid}"]'
                panel_sel = f'[data-testid="{panel_tid}"]'
                check(f"{trigger_tid} 初值 false", attr(page, sel, "aria-expanded") == "false",
                      str(attr(page, sel, "aria-expanded")))
                page.locator(sel).first.click()
                page.wait_for_timeout(400)
                opened, n_open = attr(page, sel, "aria-expanded"), page.locator(panel_sel).count()
                check(f"{trigger_tid} 点开 ⇒ true 且浮层出现", opened == "true" and n_open == 1,
                      f"expanded={opened} panel={n_open}")
                page.locator(sel).first.click()   # 三枚都是 toggle
                page.wait_for_timeout(400)
                closed, n_closed = attr(page, sel, "aria-expanded"), page.locator(panel_sel).count()
                check(f"{trigger_tid} 再点 ⇒ 收起且回 false", closed == "false" and n_closed == 0,
                      f"expanded={closed} panel={n_closed}")

            print("— ⑤ 源站**没有** aria-expanded 的那一枚，复刻也不许有 —")
            ne = f'[data-testid="{NOT_EXPANDABLE}"]'
            check(f"{NOT_EXPANDABLE} 没有 aria-expanded（源站实测 None）",
                  attr(page, ne, "aria-expanded") is None, str(attr(page, ne, "aria-expanded")))

            print("— ⑥ 往返：面板自己的「收起」关掉后，药丸能再把它打开 —")
            page.locator('[data-testid="canvas-agent-session-collapse"]').first.click()
            page.wait_for_timeout(700)
            check("点面板内「收起」能关面板", page.locator(DRAWER).count() == 0,
                  f"drawer={page.locator(DRAWER).count()}")
            check("关掉后药丸回到 DOM（往返闭合，不是单向）", page.locator(LAUNCHER).count() == 1)
            page.locator(LAUNCHER).first.click()
            page.wait_for_selector(DRAWER, timeout=20000)
            page.wait_for_timeout(600)
            check("再点药丸能再打开（② 不是恒真）", page.locator(DRAWER).count() == 1)
            # 量尺寸必须在**面板关着**的时候 —— 开着时药丸已卸载，
            # 早先那版把 bounding_box 写在开着态，直接 30s 超时（自己踩的）。
            page.locator('[data-testid="canvas-agent-session-collapse"]').first.click()
            page.wait_for_timeout(700)
            check("往返两轮后药丸回到 DOM", page.locator(LAUNCHER).count() == 1)
            check("往返两轮后尺寸没漂（仍 118×34 / 120×36）",
                  size(page, LAUNCHER) == (118, 34) and size(page, PILL) == (120, 36),
                  f'{size(page, LAUNCHER)} / {size(page, PILL)}')

            check("页面无运行时错误", not errs, str(errs[:2]))
        finally:
            out = Path("docs/research/jimeng-canvas-batch835-2026-10-04")
            out.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(out / "clone-launcher-toggle.png"))
            b.close()

    print(f"\n{'PASS' if not failures else 'FAIL'} — batch 835 launcher "
          f"{passed}/{passed + len(failures)}")
    for f in failures:
        print("  -", f)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
