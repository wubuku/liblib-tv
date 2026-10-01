#!/usr/bin/env python
"""batch 836-composer verifier —— 占位符里那枚 `@` 钮，以及面板内部六个 testid。

起因不是「看着缺东西」，是 835 那轮普查面板内部 19 个 `[data-testid]` 时对出来的
两处实缺：

1. **占位符里的 `@` 钮此前是纯装饰**（`span` + `sr-only` 文案，无 `onClick`）。
   源站同位置是一枚真 `<BUTTON>`：@[1428,784] 24×24、`cursor:pointer`、
   aria-label=「引用参考」、文字就是 `@`。点它的实测后果（`jimeng_836_placeholder_probe.py`
   + 截图 `source-placeholder-clicked.png`）：打开「添加参考」浮层
   （主体/图片/视频/音频/文本，每行带 `›`），并往输入区插入一个 `@`。
   ⚠ 那个浮层**不带任何 data-testid** —— 只按 testid 查会得到「点了没反应」的
   错误结论（我自己先踩了一次，`new_tids` 为空）。截图才看得见。

2. **空态标题整行缺失**：源站有 `<h2>`「探索更多专业创作模式」24px 居中
   （`canvas-agent-session-heading` @338×27），复刻此前只把这句写在文件头注释里。

判据落在**契约**（点得动、文案逐字、信号齐全），不落在我抄来的那一堆具体像素上 ——
像素值都在注释与台账 §50，verifier 只钉住「不能退回装饰」这件事。
"""

from __future__ import annotations

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:4317"
VIEWPORT = {"width": 1680, "height": 826}

DRAWER = '[data-testid="canvas-agent-drawer"]'
MENTION_PANEL = '[data-testid="agent-mention-panel"]'
PLACEHOLDER_MENTION = '[data-testid="canvas-agent-composer-placeholder-mention"]'
ROW_MENTION = '[data-testid="canvas-agent-composer-mention"]'

# 源站面板内部这 6 枚 testid 此前复刻一枚都没有（批 835 普查 19 元素时对出来的）
SOURCE_TIDS = [
    "canvas-agent-session-title",
    "canvas-agent-session-heading",
    "canvas-agent-session-modes",
    "canvas-agent-session-composer",
    "canvas-agent-composer-action-row",
    "prompt-composer",
]

# 源站逐字（`jimeng_836_placeholder_probe.py` 文本节点实测）
SRC_PLACEHOLDER_HEAD = "输入想法、剧本或上传参考，支持“/”使用技能，"
SRC_PLACEHOLDER_TAIL = "添加主体，和 Agent 一起创作"
SRC_HEADING = "探索更多专业创作模式"


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

    def n(page, sel: str) -> int:
        return page.locator(sel).count()

    def txt(page, sel: str) -> str:
        loc = page.locator(sel)
        return loc.first.inner_text().strip() if loc.count() else ""

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
            page.locator('[data-testid="canvas-sidecar-launcher"]').first.click()
            page.wait_for_selector(DRAWER, timeout=20000)
            page.wait_for_timeout(700)

            print("— ① 面板内部 6 枚源站 testid 齐了 —")
            for tid in SOURCE_TIDS:
                sel = f'[data-testid="{tid}"]'
                c = n(page, sel)
                check(f"{tid} 存在且唯一", c == 1, f"count={c}")

            print("— ② 空态标题：源站是 H2 / 24px / 居中 —")
            h = page.locator('[data-testid="canvas-agent-session-heading"]').first
            check("标题文案逐字等于源站", txt(page, '[data-testid="canvas-agent-session-heading"]') == SRC_HEADING,
                  txt(page, '[data-testid="canvas-agent-session-heading"]'))
            check("语义是 heading（读屏会当标题念）",
                  h.evaluate("e => e.tagName") in ("H1", "H2", "H3"),
                  h.evaluate("e => e.tagName"))
            fs = h.evaluate("e => getComputedStyle(e).fontSize")
            check("标题字号 24px（源站实测）", fs == "24px", fs)
            check("标题居中", h.evaluate("e => getComputedStyle(e).textAlign") == "center",
                  h.evaluate("e => getComputedStyle(e).textAlign"))
            check("chips 容器包住 5 枚",
                  page.locator('[data-testid="canvas-agent-session-modes"] '
                               '[data-testid="canvas-agent-mode-action"]').count() == 5)

            print("— ③ 占位文案逐字（源站三段：文字 / @钮 / 文字）—")
            ph = txt(page, '[data-testid="prompt-composer"]')
            check("占位首段逐字等于源站（斜杠两侧**无空格**）",
                  page.locator('[data-testid="agent-composer-input"]').first
                  .get_attribute("placeholder") == SRC_PLACEHOLDER_HEAD,
                  page.locator('[data-testid="agent-composer-input"]').first.get_attribute("placeholder"))
            check("尾巴是可见的「添加主体，和 Agent 一起创作」", SRC_PLACEHOLDER_TAIL in ph, ph[:80])
            check("composer 字号 14px（源站实测，此前复刻 13px）",
                  page.locator('[data-testid="prompt-composer"]').first
                  .evaluate("e => getComputedStyle(e).fontSize") == "14px")
            check("可访问名是源站原句",
                  page.locator('[data-testid="prompt-composer"]').first.get_attribute("aria-label")
                  == "说说你的想法或任务，上传参考、输入文字或")

            print("— ④ 占位符里那枚 @ **不是装饰**（本批核心）—")
            pm = page.locator(PLACEHOLDER_MENTION).first
            check("它是 button（此前是 span）", pm.evaluate("e => e.tagName") == "BUTTON",
                  pm.evaluate("e => e.tagName"))
            check("可访问名是「引用参考」（源站实测）", pm.get_attribute("aria-label") == "引用参考",
                  str(pm.get_attribute("aria-label")))
            check("它不再藏一份 sr-only 文案（源站按钮文字就是 @）",
                  pm.locator(".sr-only").count() == 0)
            check("前置：点之前「添加参考」面板是关着的", n(page, MENTION_PANEL) == 0,
                  f"panel={n(page, MENTION_PANEL)}")
            pm.click()
            page.wait_for_timeout(450)
            check("点它 ⇒ 打开「添加参考」面板", n(page, MENTION_PANEL) == 1,
                  f"panel={n(page, MENTION_PANEL)}")
            tabs = n(page, '[data-testid^="agent-ref-kind-"]')
            check("浮层里有 5 个分类 tab", tabs == 5, f"tabs={tabs}")

            print("— ⑤ 与底行「引用参考」**共用同一个面板**（不是两套实现）—")
            check("两个入口此时指向同一块面板（count 仍是 1）", n(page, MENTION_PANEL) == 1,
                  f"panel={n(page, MENTION_PANEL)}")
            page.locator(ROW_MENTION).first.click()
            page.wait_for_timeout(450)
            check("点底行那枚 ⇒ 同一个面板被 toggle 收起（共用一条实现路径）",
                  n(page, MENTION_PANEL) == 0, f"panel={n(page, MENTION_PANEL)}")
            page.locator(ROW_MENTION).first.click()
            page.wait_for_timeout(450)
            check("再点底行 ⇒ 重新打开（两入口对同一状态达成一致）", n(page, MENTION_PANEL) == 1,
                  f"panel={n(page, MENTION_PANEL)}")
            page.locator(PLACEHOLDER_MENTION).first.click()
            page.wait_for_timeout(450)
            check("点占位 @ ⇒ 同一个面板被 toggle 收起", n(page, MENTION_PANEL) == 0,
                  f"panel={n(page, MENTION_PANEL)}")

            print("— ⑥ 反向自检：关掉面板后 @ 钮回到可点状态（③ 不是恒真）—")
            check("面板已收起", n(page, MENTION_PANEL) == 0)
            check("@ 钮仍在 DOM 且 enabled", n(page, PLACEHOLDER_MENTION) == 1
                  and not pm.is_disabled())
            check("composer 外壳是源站那圈**更暗**的底色（不是 white/6%）",
                  "16, 16, 16" in page.locator('[data-testid="canvas-agent-session-composer"]')
                  .first.evaluate("e => getComputedStyle(e).backgroundColor"),
                  page.locator('[data-testid="canvas-agent-session-composer"]')
                  .first.evaluate("e => getComputedStyle(e).backgroundColor"))

            check("页面无运行时错误", not errs, str(errs[:2]))
        finally:
            out = Path("docs/research/jimeng-canvas-batch836-2026-10-04")
            out.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(out / "clone-composer-panel.png"))
            b.close()

    print(f"\n{'PASS' if not failures else 'FAIL'} — batch 836 composer "
          f"{passed}/{passed + len(failures)}")
    for f in failures:
        print("  -", f)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
