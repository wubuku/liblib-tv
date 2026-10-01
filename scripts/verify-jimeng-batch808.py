"""Jimeng clone batch 808 verifier — 交互态普查的第二个教训：「disabled」不是死按钮。

batch 807 的死按钮普查只覆盖了**默认视图**。本批把普查扩到交互态
（选中节点 / AI 抽屉 / 画布右键菜单），结果是**方法论先出了问题**：

  右键菜单的「粘贴 ⌘V」「重做 ⌘⇧Z」「撤销 ⌘Z」被普查报成死按钮，
  实际它们带 `disabled` —— 没有可粘贴内容、没有历史可撤销时，**点了没反应
  是对的**。源站的「新建会话」同理：带 `aria-disabled="true"`（还没有会话
  可新建），也是正确禁用。

  于是本批第一件事不是修产品，是**修判据**：审计脚本过滤
  `disabled` / `aria-disabled` / `data-disabled`。

过滤之后再看，剩下的真缺口是 AI 抽屉缺了源站的会话入口：

  源站头部是三个控件，复刻此前头部是一段纯文本 + 两个按钮：
    会话列表 58×32 @[1314,41] `canvas-agent-session-menu-trigger`（无会话时 disabled）
    新建会话 32×32 @[1599,41] `canvas-agent-session-create`（无会话时 disabled）
    收起     36×36 @[1637,41] `canvas-agent-session-collapse`

以及一个真实的交互 bug：右键菜单「新建节点」hover 打开子菜单后再点一下会
**把它关掉**（onMouseEnter 开、onClick toggle 关），用户点了像没反应。
"""

import os
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "docs" / "design-references" / "jimeng"
BASE_URL = os.environ.get("JIMENG_BASE_URL", "http://localhost:4317")
CANVAS_URL = f"{BASE_URL}/jimeng/canvas/demo"
VIEWPORT = {"width": 1680, "height": 826}

# SOURCE_FACT：源站 AI 抽屉（@1680×826 登录态，aria/testid 逐个提取）
DRAWER = {
    "canvas-agent-session-menu-trigger": (58, 32, True),
    "canvas-agent-session-create": (32, 32, True),
    "canvas-agent-session-collapse": (36, 36, False),
    "canvas-agent-skill-trigger": (90, 32, False),
    "canvas-agent-composer-add": (32, 32, False),
    "canvas-agent-composer-mention": (32, 32, False),
    "canvas-agent-send": (32, 32, True),
}


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

    def near(a: float, b: float, tol: float = 0.6) -> bool:
        return abs(a - b) <= tol

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport=VIEWPORT, locale="zh-CN")
        page = ctx.new_page()
        errors: list[str] = []
        page.on("console", lambda m: errors.append(f"console.{m.type}: {m.text}") if m.type == "error" else None)
        page.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))

        page.goto(CANVAS_URL, wait_until="domcontentloaded")
        # 等真正水合：顶栏出现才算 React 接管，固定 sleep 在重编译窗口会踩空
        page.wait_for_selector('[data-testid="canvas-top-bar"]', timeout=20000)
        page.wait_for_timeout(800)

        print("— 判据本身：disabled 元素不算死按钮 —")
        # 画布右键菜单：无内容可粘贴 / 无历史可撤销时，这三项应当是 disabled
        page.mouse.click(900, 600, button="right")
        # 显式等菜单挂载：固定 sleep 在 dev server 刚重编译时会踩空
        page.wait_for_selector('[role="menu"]', timeout=15000)
        page.wait_for_timeout(300)
        for label in ["粘贴", "重做", "撤销"]:
            item = page.locator('[role="menu"] [role="menuitem"]', has_text=label).first
            dis = item.evaluate("el => el.disabled === true")
            check(f"右键菜单「{label}」无内容时是 disabled", dis, f"disabled={dis}")
        page.screenshot(path=str(REFERENCE_DIR / "jimeng-clone-batch808-pane-menu-1680.png"))
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)

        print("— 右键菜单「新建节点」点了不再自关子菜单 —")
        page.mouse.click(900, 600, button="right")
        page.wait_for_selector('[data-testid="pane-menu-insert"]', timeout=15000)
        page.wait_for_timeout(300)
        n_before = page.locator(".react-flow__node").count()
        page.locator('[data-testid="pane-menu-insert"]').click()
        page.wait_for_timeout(400)
        sub_items = page.locator('[role="menu"] [role="menuitem"]').count()
        check("点「新建节点」后子菜单仍然打开（不再 toggle 关掉）",
              sub_items > 4, f"子菜单项数={sub_items}")
        # 子菜单里挑一项，节点应当真的插入
        target = page.locator('[role="menu"] [role="menuitem"]', has_text="文本").first
        if target.count():
            target.click()
            page.wait_for_timeout(600)
            n_after = page.locator(".react-flow__node").count()
            check("子菜单里选「文本」真的插入节点", n_after == n_before + 1,
                  f"{n_before} -> {n_after}")
        else:
            check("子菜单里能找到「文本」项", False, "未找到")
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)

        print("— AI 抽屉：源站控件契约 —")
        page.mouse.click(1608, 796)
        page.wait_for_selector('[aria-label="Agent"]', timeout=15000)
        page.wait_for_timeout(400)
        check("AI 抽屉已开", page.locator('[aria-label="Agent"]').count() == 1)
        for tid, (w, h, want_disabled) in DRAWER.items():
            loc = page.locator(f'[data-testid="{tid}"]')
            if loc.count() != 1:
                check(f"{tid} 存在", False, f"count={loc.count()}")
                continue
            bb = loc.bounding_box()
            dis = loc.evaluate("el => el.disabled === true")
            check(f"{tid} {w}×{h}",
                  bb is not None and near(bb["width"], w) and near(bb["height"], h),
                  f"{bb and (round(bb['width']), round(bb['height']))}")
            check(f"{tid} disabled={want_disabled}", dis == want_disabled, f"disabled={dis}")
        check("占位符里的 @ 是 24×24 独立节点",
              page.locator('[data-testid="canvas-agent-composer-placeholder-mention"]').count() == 1)

        print("— 技能 chip：高度精确，宽度随文案增长 —")
        chips = page.locator('[data-testid="canvas-agent-mode-action"]')
        check("5 个技能 chip", chips.count() == 5, f"count={chips.count()}")
        widths, heights = [], []
        for i in range(chips.count()):
            bb = chips.nth(i).bounding_box()
            widths.append(round(bb["width"]))
            heights.append(round(bb["height"]))
        check("chip 高度都是 36", all(h == 36 for h in heights), str(heights))
        check("最长的 chip（「/ 全流程广告片导演」）更宽",
              max(widths) == widths[2] and widths[2] > widths[0], str(widths))
        # 源站 105 / 105 / 157；复刻字体度量下 103 / 103 / 155，差 2px。
        # 与 batch 798 分享按钮同因：字体不同，不该写死宽度去凑（那是把
        # 度量误差硬编码成契约）。只断言差值关系，不断言绝对宽度。
        print(f"     实测宽度 {widths}（源站 [105, 105, 157]，字体度量差 2px，不写死）")

        print("— 抽屉仍是活的（795 面板几何不回退）—")
        panel = page.locator('[aria-label="Agent"]').bounding_box()
        check("Agent 面板仍 400×802 @[1268,12]",
              panel is not None and near(panel["width"], 400) and near(panel["height"], 802)
              and near(panel["x"], 1268) and near(panel["y"], 12), str(panel))
        page.screenshot(path=str(REFERENCE_DIR / "jimeng-clone-batch808-agent-drawer-1680.png"))
        page.locator('[data-testid="canvas-agent-session-collapse"]').click()
        page.wait_for_timeout(500)
        check("「收起」能关掉抽屉", page.locator('[aria-label="Agent"]').count() == 0)

        print("— 审计脚本判据已修正 —")
        audit = ROOT / "scripts" / "jimeng_dead_button_audit.py"
        src = audit.read_text(encoding="utf-8")
        check("审计脚本过滤 disabled/aria-disabled/data-disabled",
              "aria-disabled" in src and "data-disabled" in src)

        print("— 回归 —")
        page.reload(wait_until="domcontentloaded")
        page.wait_for_timeout(2000)
        check("刷新后画布仍是初始 2 节点",
              page.locator(".react-flow__node").count() == 2,
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
    print(f"PASS: jimeng batch 808 交互态普查 + disabled 判据 + AI 抽屉控件契约（{checks} 项断言全通过）")


if __name__ == "__main__":
    main()
