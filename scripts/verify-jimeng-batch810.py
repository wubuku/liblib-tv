"""Jimeng clone batch 810 verifier — AI 抽屉 composer：四个死按钮接成真交互。

## 起因：batch 808 记了一条**错的**结论，batch 810 把它推翻

808 当时写「源站登录态下这 5 个技能 chip / 引用参考 / + / 使用技能 逐个点击
同样没有可观测变化，所以复刻保持 inert 才是对齐」。

**那是探针假象。** 源站的 composer 是 **contenteditable DIV**
（`aria-label="说说你的想法或任务，上传参考、输入文字或…"`），
而 808 的指纹只扫 `textarea,input:not([type=hidden])` —— 压根没扫到它。
判据够不着 ≠ 控件没反应。

把 `[contenteditable],[role=textbox],.ProseMirror` 纳入指纹后，源站行为是：

| 控件 | 源站实测行为 |
|---|---|
| 技能 chip | 把技能名**插入 composer**，渲染成 `node-composerChip` 富文本 token，发送钮转可用 |
| 使用技能 | 弹「搜索技能」面板（占位「搜索技能」），每项「名称 + 官方 + 长描述」 |
| 引用参考 @ | 弹「添加参考」面板，分类 tab：主体 / 图片 / 视频 / 音频 / 文本 |
| + 添加 | 弹菜单：上传 / 从资产库添加 / 从画布添加 |
| 发送消息 | composer 非空时可用；点击发出消息 |

所以这四个按钮是真功能，复刻必须接。本批实现它们，并让「会话列表 / 新建会话」
随会话是否存在而启用 —— 源站它们在**还没有会话**时是 aria-disabled。

## 顺带修正的第二个探针缺陷

batch 809 的普查 v1 报「保存到主体库 / 下载 / 删除」三个死按钮，实测全是活的。
原因：**状态是被点击销毁的** —— 右键菜单一点就关，枚举一次再逐个点，
后面那些点击全打在画布上。`scripts/jimeng_state_audit.py` 因此改成
「每个元素前重新载入并重新进入该状态」。
"""

import os
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "docs" / "design-references" / "jimeng"
BASE_URL = os.environ.get("JIMENG_BASE_URL", "http://localhost:4317")
CANVAS_URL = f"{BASE_URL}/jimeng/canvas/demo"
VIEWPORT = {"width": 1680, "height": 826}


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
        page.wait_for_timeout(600)

        def dis(tid: str) -> bool:
            loc = page.locator(f'[data-testid="{tid}"]')
            return loc.is_disabled() if loc.count() else True

        def n(sel: str) -> int:
            return page.locator(sel).count()

        page.mouse.click(1608, 796)
        page.wait_for_selector('[aria-label="Agent"]', timeout=15000)
        page.wait_for_timeout(500)

        print("— 空态：没有会话，该禁用的都禁用 —")
        check("空输入时发送钮禁用（源站同）", dis("canvas-agent-send"))
        check("无会话时「会话列表」禁用", dis("canvas-agent-session-menu-trigger"))
        check("无会话时「新建会话」禁用", dis("canvas-agent-session-create"))
        check("初始无消息", n('[data-testid="agent-messages"]') == 0)
        check("初始无 token", n('[data-testid="agent-composer-tokens"]') == 0)

        print("— 技能 chip：插入 composer 并解锁发送 —")
        page.locator('[data-testid="canvas-agent-mode-action"]').nth(1).click()
        page.wait_for_timeout(400)
        tok = n('[data-testid="agent-composer-tokens"] span')
        check("点 chip 后 composer 出现 token", tok == 1, f"count={tok}")
        check("token 内容是技能名",
              "创作分镜" in page.locator('[data-testid="agent-composer-tokens"]').inner_text(),
              page.locator('[data-testid="agent-composer-tokens"]').inner_text()[:40])
        check("token 使发送钮可用", not dis("canvas-agent-send"))
        check("token 可单独移除",
              page.locator('[data-testid="agent-composer-tokens"] button[aria-label^="移除"]').count() == 1)

        print("— 发送：真会话闭环 —")
        page.locator('[data-testid="canvas-agent-send"]').click()
        page.wait_for_timeout(600)
        msgs = n('[data-testid="agent-messages"] > div')
        check("发出用户 + Agent 两条消息", msgs == 2, f"count={msgs}")
        check("用户消息含所发内容",
              "创作分镜" in page.locator('[data-testid="agent-msg-user"]').first.inner_text(),
              page.locator('[data-testid="agent-msg-user"]').first.inner_text()[:40])
        check("发送后 composer 清空", n('[data-testid="agent-composer-tokens"]') == 0)
        check("发送钮回到禁用", dis("canvas-agent-send"))
        check("**有会话后**「会话列表」转可用", not dis("canvas-agent-session-menu-trigger"))
        check("**有会话后**「新建会话」转可用", not dis("canvas-agent-session-create"))
        check("空态技能 chips 已退场", n('[data-testid="canvas-agent-mode-action"]') == 0)
        page.screenshot(path=str(REFERENCE_DIR / "jimeng-clone-batch810-agent-sent-1680.png"))

        print("— 使用技能：搜索面板 —")
        page.locator('[data-testid="canvas-agent-skill-trigger"]').click()
        page.wait_for_timeout(400)
        check("弹出「搜索技能」面板", n('[data-testid="agent-skills-panel"]') == 1)
        check("面板有搜索框",
              page.locator('[data-testid="agent-skills-panel"] input[aria-label="搜索技能"]').count() == 1)
        sk = n('[data-testid="agent-skill-item"]')
        check("列出 5 个技能", sk == 5, f"count={sk}")
        check("每项带「官方」标记与描述",
              "官方" in page.locator('[data-testid="agent-skill-item"]').first.inner_text()
              and len(page.locator('[data-testid="agent-skill-item"]').first.inner_text()) > 30,
              page.locator('[data-testid="agent-skill-item"]').first.inner_text()[:40])
        page.locator('[data-testid="agent-skills-panel"] input[aria-label="搜索技能"]').fill("剧情")
        page.wait_for_timeout(300)
        sk2 = n('[data-testid="agent-skill-item"]')
        check("搜索过滤生效", sk2 == 1, f"count={sk2}")
        page.locator('[data-testid="agent-skills-panel"] input[aria-label="搜索技能"]').fill("")
        page.wait_for_timeout(300)
        page.locator('[data-testid="agent-skill-item"]').nth(4).click()
        page.wait_for_timeout(400)
        check("选技能后 token 出现", n('[data-testid="agent-composer-tokens"] span') == 1)
        check("选技能后面板关闭", n('[data-testid="agent-skills-panel"]') == 0)

        print("— 引用参考：分类 tab —")
        page.locator('[data-testid="canvas-agent-composer-mention"]').click()
        page.wait_for_timeout(400)
        check("弹出「添加参考」面板", n('[data-testid="agent-mention-panel"]') == 1)
        tabs = n('[data-testid^="agent-ref-kind-"]')
        check("五个分类 tab", tabs == 5, f"count={tabs}")
        page.locator('[data-testid="agent-ref-kind-视频"]').click()
        page.wait_for_timeout(250)
        check("切 tab 改确认按钮文案",
              "视频" in page.locator('[data-testid="agent-ref-confirm"]').inner_text(),
              page.locator('[data-testid="agent-ref-confirm"]').inner_text())
        page.locator('[data-testid="agent-ref-confirm"]').click()
        page.wait_for_timeout(400)
        tokens = page.locator('[data-testid="agent-composer-tokens"]').inner_text()
        check("引用后 composer 多出 @视频 token", "@视频" in tokens, tokens[:60])

        print("— + 添加：来源菜单 —")
        page.locator('[data-testid="canvas-agent-composer-add"]').click()
        page.wait_for_timeout(400)
        check("弹出添加来源菜单", n('[data-testid="agent-add-panel"]') == 1)
        for src in ["上传", "从资产库添加", "从画布添加"]:
            check(f"菜单含「{src}」", n(f'[data-testid="agent-add-{src}"]') == 1)
        page.locator('[data-testid="agent-add-从画布添加"]').click()
        page.wait_for_timeout(400)
        # batch 812 改过这条文案：原来只是把按钮名复述一遍（「从画布添加（mock）」，
        # 零信息量），现在改成说明下一步（「请在画布中选择节点（mock）」）。
        # 断言跟着改成查**语义**（说明该做什么），不查已经废弃的旧字符串 ——
        # 否则一次文案改进就会把旧验证器打红，而它并没有测坏东西。
        seen = ""
        for _ in range(20):   # toast 短命，120ms 级采样
            seen = " ".join(page.locator('[role="status"]').nth(i).inner_text()
                            for i in range(page.locator('[role="status"]').count()))
            if seen:
                break
            page.wait_for_timeout(120)
        check("选来源后有反馈 toast（说明下一步该做什么）",
              ("画布" in seen and ("选择" in seen or "选中" in seen)), repr(seen[:60]))
        check("选来源后菜单关闭", n('[data-testid="agent-add-panel"]') == 0)

        print("— 新建会话：回到空态 —")
        page.locator('[data-testid="canvas-agent-session-create"]').click()
        page.wait_for_timeout(500)
        check("消息清空", n('[data-testid="agent-messages"]') == 0)
        check("token 清空", n('[data-testid="agent-composer-tokens"]') == 0)
        chips = n('[data-testid="canvas-agent-mode-action"]')
        check("空态技能 chips 回来", chips == 5, f"count={chips}")
        check("会话头回到禁用", dis("canvas-agent-session-create"))
        page.screenshot(path=str(REFERENCE_DIR / "jimeng-clone-batch810-agent-drawer-1680.png"))

        print("— 回归 —")
        page.reload(wait_until="domcontentloaded")
        page.wait_for_selector('[data-testid="canvas-top-bar"]', timeout=25000)
        page.wait_for_timeout(800)
        check("刷新后画布仍是初始 2 节点", n(".react-flow__node") == 2)
        check("无 console/page 错误", not errors, "; ".join(errors[:3]))
        ctx.close()
        browser.close()

    print()
    if failures:
        print(f"FAIL: {len(failures)}/{checks} 项未通过")
        for f in failures:
            print("  -", f)
        raise SystemExit(1)
    print(f"PASS: jimeng batch 810 AI 抽屉 composer 真实交互（{checks} 项断言全通过）")


if __name__ == "__main__":
    main()
