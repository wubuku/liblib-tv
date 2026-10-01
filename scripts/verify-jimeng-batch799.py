"""Jimeng clone batch 799 verifier — 「更多」两项动作：项目信息模态 + 复制项目反馈。

（编号说明：797 已被并行会话占用 —— Agent 抽屉默认收起 + 触发钮材质契约。
本批是顶栏「更多」菜单两个动作的落地，取 799 以免撞号。）

Contract (SOURCE_FACT 2026-10-01，登录态，1680×826)：
  项目信息  role=dialog 800×546 @[440,140]，`fixed left-1/2 top-1/2` 居中；
           文案逐字 项目信息/基础信息/积分消耗/所有者/创建时间/最新修改/
           节点分布/全部节点/全部/图片/视频/音频/文本/时间线/主体/其他/查看积分明细；
           节点分布计数随 store 实时统计；Esc 可关闭。
  复制项目  写剪贴板 + 顶部 toast「复制画布中…」(127×44 @[776,24]，13px)。
"""

import os
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "docs" / "design-references" / "jimeng"
BASE_URL = os.environ.get("JIMENG_BASE_URL", "http://localhost:4317")
CANVAS_URL = f"{BASE_URL}/jimeng/canvas/demo"
VIEWPORT = {"width": 1680, "height": 826}
MENU = '[data-testid="topbar-more-menu"]'
MODAL = '[data-testid="project-info-modal"]'


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

    def near(a, b, tol=2.0) -> bool:
        return a is not None and abs(a - b) <= tol

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # 授予剪贴板权限，才能断言「复制项目」真的写了链接
        ctx = browser.new_context(viewport=VIEWPORT, locale="zh-CN",
                                  permissions=["clipboard-read", "clipboard-write"])
        page = ctx.new_page()
        errors: list[str] = []
        page.on("console", lambda m: errors.append(f"console.{m.type}: {m.text}") if m.type == "error" else None)
        page.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))

        page.goto(CANVAS_URL, wait_until="domcontentloaded")
        page.wait_for_timeout(2500)

        print("— 复制项目 —")
        page.locator('[data-testid="canvas-more-trigger"]').click()
        page.wait_for_timeout(400)
        check("更多菜单已打开", page.locator(MENU).count() == 1, f"count={page.locator(MENU).count()}")
        page.locator(f'{MENU} [role="menuitem"]', has_text="复制项目").click()
        page.wait_for_timeout(500)
        toast = page.locator('[role="status"]')
        check("出现 toast", toast.count() >= 1, f"count={toast.count()}")
        if toast.count():
            txt = " ".join(toast.nth(i).inner_text() for i in range(toast.count()))
            check("toast 文案「复制画布中…」", "复制画布中" in txt, repr(txt[:80]))
        clip = page.evaluate("() => navigator.clipboard.readText().catch(() => '')")
        check("剪贴板写入画布链接", "jimeng.jianying.com/ai-tool/ai-canvas" in (clip or ""), repr((clip or "")[:90]))
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)

        print("— 项目信息 —")
        page.locator('[data-testid="canvas-more-trigger"]').click()
        page.wait_for_timeout(400)
        page.locator(f'{MENU} [role="menuitem"]', has_text="项目信息").click()
        page.wait_for_timeout(600)
        check("项目信息模态已打开", page.locator(MODAL).count() == 1, f"count={page.locator(MODAL).count()}")
        if page.locator(MODAL).count() == 1:
            b = page.locator(MODAL).bounding_box()
            check("模态 800x546 @[440,140]",
                  near(b["width"], 800) and near(b["height"], 546)
                  and near(b["x"], 440) and near(b["y"], 140),
                  f"实际 [{round(b['x'])},{round(b['y'])} {round(b['width'])}x{round(b['height'])}]")
            st = page.locator(MODAL).evaluate("el => getComputedStyle(el).position")
            check("模态 fixed 居中定位", st == "fixed", st)
            txt = page.locator(MODAL).inner_text()
            for frag in ["项目信息", "基础信息", "积分消耗", "所有者", "创建时间",
                         "最新修改", "节点分布", "全部节点", "图片", "视频", "音频",
                         "文本", "时间线", "主体", "其他", "查看积分明细"]:
                check(f"含「{frag}」", frag in txt, repr(txt[:100]))
            check("节点分布表已渲染", page.locator(MODAL).inner_text().count("全部节点") >= 1, "missing")
            page.screenshot(path=str(REFERENCE_DIR / "jimeng-clone-batch799-project-info-1680.png"))

            page.locator(f'{MODAL} button[aria-label="积分消耗"]').click()
            page.wait_for_timeout(300)
            check("可切到积分消耗页", "暂无积分消耗记录" in page.locator(MODAL).inner_text(),
                  repr(page.locator(MODAL).inner_text()[:80]))

            page.keyboard.press("Escape")
            page.wait_for_timeout(400)
            check("Escape 关闭模态", page.locator(MODAL).count() == 0,
                  f"count={page.locator(MODAL).count()}")

        print("— 回归 —")
        check("顶栏右簇未受影响",
              page.locator('[data-testid="canvas-commerce-entry"]').count() == 1, "credits missing")
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
    print(f"PASS: jimeng batch 799 更多菜单两项动作契约（{checks} 项断言全通过）")


if __name__ == "__main__":
    main()
