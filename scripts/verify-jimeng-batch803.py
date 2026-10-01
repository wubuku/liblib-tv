"""Jimeng clone batch 803 verifier — 顶栏新增控件的**真实交互**闭环。

batch 794/795/799 把顶栏控件的外观与文案复刻出来了，但其中若干按钮是死按钮
（无 onClick / 回调未传）。本批把它们接成真交互，并断言**状态确实变化**，
而不是只断言元素存在。

Contract（交互层 SOURCE_FACT + CLONE_DECISION 标注见各处注释）:
  分享「复制链接」      写剪贴板 + toast 文案
  节点摘要弹层点节点    该节点被选中（store.selectedNodeId）且视口聚焦
  节点摘要「查看项目信息」打开项目信息模态
  项目信息「查看积分明细」跳会员弹层（积分详情）
  项目面板点项目名      项目名被改写（renameProject）+ toast
  项目面板「新建画布项目」toast
"""

import os
import re
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "docs" / "design-references" / "jimeng"
BASE_URL = os.environ.get("JIMENG_BASE_URL", "http://localhost:4317")
CANVAS_URL = f"{BASE_URL}/jimeng/canvas/demo"
VIEWPORT = {"width": 1680, "height": 826}
MENU = '[data-testid="topbar-more-menu"]'
MODAL = '[data-testid="project-info-modal"]'
SUMMARY = '[data-testid="topbar-node-summary"]'


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
        ctx = browser.new_context(viewport=VIEWPORT, locale="zh-CN",
                                  permissions=["clipboard-read", "clipboard-write"])
        page = ctx.new_page()
        errors: list[str] = []
        page.on("console", lambda m: errors.append(f"console.{m.type}: {m.text}") if m.type == "error" else None)
        page.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))

        page.goto(CANVAS_URL, wait_until="domcontentloaded")
        page.wait_for_timeout(2500)

        def toast_text() -> str:
            t = page.locator('[role="status"]')
            return " ".join(t.nth(i).inner_text() for i in range(t.count()))

        def selected_id() -> str | None:
            return page.evaluate(
                """() => {
                  const el = document.querySelector('.react-flow__node.selected');
                  return el ? el.getAttribute('data-id') : null;
                }"""
            )

        print("— 分享「复制链接」是活按钮 —")
        page.locator('[data-testid="canvas-share-trigger"]').click()
        page.wait_for_timeout(400)
        check("分享面板已开", page.locator('[data-testid="topbar-share-panel"]').count() == 1)
        page.locator('[data-testid="topbar-share-panel"] button', has_text="复制链接").click()
        page.wait_for_timeout(500)
        clip = page.evaluate("() => navigator.clipboard.readText().catch(() => '')")
        check("点「复制链接」后剪贴板有画布链接",
              "jimeng.jianying.com/ai-tool/ai-canvas" in (clip or ""), repr((clip or "")[:80]))
        check("点「复制链接」后出 toast", "复制" in toast_text(), repr(toast_text()[:60]))
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)

        print("— 节点摘要弹层点节点 → 选中 + 聚焦 —")
        page.locator('[data-testid="canvas-node-summary-trigger"]').click()
        page.wait_for_timeout(400)
        check("节点摘要弹层已开", page.locator(SUMMARY).count() == 1)
        # 弹层里的第一个节点条目
        entry = page.locator(f'{SUMMARY} button').filter(has_text="视频")
        check("弹层含节点条目", entry.count() >= 1, f"count={entry.count()}")
        if entry.count() >= 1:
            before = page.evaluate(
                """() => document.querySelector('.react-flow__viewport')?.style.transform || ''"""
            )
            entry.first.click()
            page.wait_for_timeout(900)
            sel = selected_id()
            check("点击后有节点被选中", sel is not None, f"selected={sel!r}")
            after = page.evaluate(
                """() => document.querySelector('.react-flow__viewport')?.style.transform || ''"""
            )
            check("视口发生位移（聚焦生效）", before != after,
                  f"before={before!r} after={after!r}")
            # 注意：节点与它的工具条共用 data-id，必须限定 .react-flow__node
            check("选中的是弹层里点的那一项",
                  sel is not None
                  and "视频" in page.locator(f'.react-flow__node[data-id="{sel}"]').inner_text(),
                  f"selected={sel!r}")
            page.screenshot(path=str(REFERENCE_DIR / "jimeng-clone-batch803-focus-node-1680.png"))

        print("— 节点摘要「查看项目信息」→ 打开模态 —")
        page.locator('[data-testid="canvas-node-summary-trigger"]').click()
        page.wait_for_timeout(350)
        page.locator(f'{SUMMARY} button', has_text="查看项目信息").click()
        page.wait_for_timeout(600)
        check("项目信息模态已开", page.locator(MODAL).count() == 1,
              f"count={page.locator(MODAL).count()}")

        print("— 项目信息「查看积分明细」→ 会员弹层 —")
        if page.locator(MODAL).count() == 1:
            page.locator(f'{MODAL} button', has_text="查看积分明细").click()
            page.wait_for_timeout(700)
            body = page.locator("body").inner_text()
            check("跳到会员弹层（积分详情）", "积分详情" in body, body[:120])
            check("模态同时关闭", page.locator(MODAL).count() == 0)
            page.keyboard.press("Escape")
            page.wait_for_timeout(400)

        print("— 项目面板：切项目 / 新建 —")
        page.locator('[data-testid="canvas-project-trigger"]').click()
        page.wait_for_timeout(400)
        check("项目面板已开", page.locator('[data-testid="topbar-project-panel"]').count() == 1)
        before_name = page.locator('[data-testid="canvas-project-title-trigger"]').inner_text()
        page.locator('[data-testid="topbar-project-panel"] button', has_text="未命名项目").click()
        page.wait_for_timeout(600)
        after_name = page.locator('[data-testid="canvas-project-title-trigger"]').inner_text()
        check("点项目名后顶栏标题改名", after_name.strip() == "未命名项目" and after_name != before_name,
              f"{before_name!r} -> {after_name!r}")
        check("切项目有 toast", "已切换到" in toast_text(), repr(toast_text()[:60]))

        page.locator('[data-testid="canvas-project-trigger"]').click()
        page.wait_for_timeout(400)
        page.locator('[data-testid="topbar-project-panel"] button', has_text="新建画布项目").click()
        page.wait_for_timeout(600)
        check("新建画布项目有 toast", "新建画布项目" in toast_text(), repr(toast_text()[:60]))

        print("— 回归 —")
        check("画布仍有 2 节点", page.locator(".react-flow__node").count() == 2,
              f"count={page.locator('.react-flow__node').count()}")
        check("无 console/page 错误", not errors, "; ".join(errors[:3]))
        ctx.close()
        browser.close()

    print()
    if failures:
        print(f"FAIL: {len(failures)}/{checks} 项未通过")
        for f in failures:
            print("  -", f)
        raise SystemExit(1)
    print(f"PASS: jimeng batch 803 顶栏控件真实交互闭环（{checks} 项断言全通过）")


if __name__ == "__main__":
    main()
