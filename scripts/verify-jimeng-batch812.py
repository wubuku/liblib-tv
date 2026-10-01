"""Jimeng clone batch 812 verifier — 反馈文案的**一致性与信息量**。

前面几批都在查「控件有没有反应」。这一批查反应**说出来的话**：

1. **漏标注**。batch 807 同批新增的三个节点里，主体节点的反馈带「（mock）」，
   时间线的 `已添加「片段 1」到时间线` 却没带 —— 同一批次里就不一致。
2. **零信息量**。`${label}（mock）` 这种纯拼接，用户看到「上传（mock）」
   「从画布添加（mock）」—— 只是把按钮名复述一遍，等于什么都没说。
3. **同一动作多处硬编码**。「视频下载已开始（mock）」在三个文件各写一遍。

处置：文案收敛到 `src/components/jimeng/jimengFeedback.ts` 唯一出处。

验证方式分两层：
- **静态层**：src/ 下不允许再出现散落的「（mock）」字面量
- **行为层**：真的去点，断言 toast 文案 —— 含信息量、且同一动作跨入口一致
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
FEEDBACK_MOD = ROOT / "src" / "components" / "jimeng" / "jimengFeedback.ts"


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

    print("— 静态层：文案唯一出处 —")
    mod_src = FEEDBACK_MOD.read_text(encoding="utf-8")
    check("反馈文案模块存在", FEEDBACK_MOD.exists(), str(FEEDBACK_MOD))
    check("模块提供 mockMsg 统一标注", "export function mockMsg" in mod_src)
    check("模块提供 sourcePickFeedback（修零信息量拼接）",
          "export function sourcePickFeedback" in mod_src)

    # src/ 下除模块自身与注释外，不应再有「（mock）」字面量
    stray: list[str] = []
    for f in (ROOT / "src").rglob("*.ts*"):
        if f == FEEDBACK_MOD:
            continue
        for i, line in enumerate(f.read_text(encoding="utf-8").split("\n"), 1):
            code = line.split("//")[0]
            if code.lstrip().startswith(("*", "/*")):
                continue
            if "（mock）" in code:
                stray.append(f"{f.relative_to(ROOT)}:{i}")
    check("src/ 下无散落的「（mock）」字面量", not stray, "; ".join(stray[:5]))

    # 同一动作不得在多处硬编码。
    # 判据要卡在 **pushToast 上下文** 里：早先只判"文件里出现过这段文字"，
    # 结果 JimengProjectPanel 的**按钮标签**「新建画布项目」被判成硬编码 ——
    # 那是 UI 文本，不是反馈文案。误报的判据比没有判据更费时间。
    dup = []
    toast_re = re.compile(r"pushToast\([^)]*")
    for text in ["视频下载已开始", "已保存到主体库", "新建画布项目", "已新建会话"]:
        hits = []
        for f in (ROOT / "src").rglob("*.ts*"):
            if f == FEEDBACK_MOD:
                continue
            body = f.read_text(encoding="utf-8")
            for m in toast_re.finditer(body):
                if text in m.group(0):
                    hits.append(f.name)
        if hits:
            dup.append(f"{text} → {sorted(set(hits))}")
    check("同一动作文案不在 pushToast 处硬编码", not dup, "; ".join(dup))

    print("— 行为层：真去点，断言 toast —")
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

        def toasts() -> str:
            t = page.locator('[role="status"]')
            return " ".join(t.nth(i).inner_text() for i in range(t.count()))

        def fresh():
            page.reload(wait_until="domcontentloaded")
            page.wait_for_selector('[data-testid="canvas-top-bar"]', timeout=25000)
            page.wait_for_timeout(500)

        # 1 时间线（807 引入、当时漏标注的那个）
        fresh()
        page.locator('[aria-label="时间线"]').first.click()
        page.wait_for_selector('[data-testid="timeline-add-clip"]', timeout=10000)
        page.locator('[data-testid="timeline-add-clip"]').click()
        # toast 是短命的：120ms 级高频采样，等 2.6s 会漏
        seen = ""
        for _ in range(20):
            seen = toasts()
            if seen:
                break
            page.wait_for_timeout(120)
        check("时间线加片段的 toast 带 mock 标注（修 807 的漏标注）",
              "（mock）" in seen, repr(seen[:60]))
        check("时间线 toast 含具体片段名（有信息量）",
              "片段" in seen, repr(seen[:60]))

        # 2 主体
        fresh()
        page.locator('[aria-label="主体"]').first.click()
        page.wait_for_selector('[data-testid="subject-node"]', timeout=10000)
        page.locator('[data-testid="subject-node"] button[aria-label="导入主体"]').click()
        seen = ""
        for _ in range(20):
            seen = toasts()
            if seen:
                break
            page.wait_for_timeout(120)
        check("主体导入 toast 带 mock 标注", "（mock）" in seen, repr(seen[:60]))
        check("主体导入 toast 含素材名", "主体素材" in seen, repr(seen[:60]))

        # 3 AI 抽屉「+」来源菜单：原来只是「上传（mock）」复述按钮名
        fresh()
        page.mouse.click(1608, 796)
        page.wait_for_selector('[aria-label="Agent"]', timeout=10000)
        page.locator('[data-testid="canvas-agent-composer-add"]').click()
        page.wait_for_selector('[data-testid="agent-add-panel"]', timeout=10000)
        page.locator('[data-testid="agent-add-上传"]').click()
        seen = ""
        for _ in range(20):
            seen = toasts()
            if seen:
                break
            page.wait_for_timeout(120)
        check("来源菜单反馈不再是按钮名的复述", seen.strip() != "上传（mock）", repr(seen[:60]))
        check("来源菜单反馈有信息量（说明下一步该做什么）",
              "选择" in seen or "文件" in seen, repr(seen[:60]))
        check("来源菜单反馈带 mock 标注", "（mock）" in seen, repr(seen[:60]))

        # 4 项目面板「新建画布项目」文案未变
        fresh()
        page.locator('[data-testid="canvas-project-trigger"]').click()
        page.wait_for_selector('[data-testid="topbar-project-panel"]', timeout=10000)
        page.locator('[data-testid="topbar-project-panel"] button', has_text="新建画布项目").click()
        seen = ""
        for _ in range(20):
            seen = toasts()
            if seen:
                break
            page.wait_for_timeout(120)
        check("新建画布项目文案保持不变",
              seen.strip() == "新建画布项目（mock）", repr(seen[:60]))
        page.screenshot(path=str(REFERENCE_DIR / "jimeng-clone-batch812-feedback-1680.png"))

        check("无 console/page 错误", not errors, "; ".join(errors[:3]))
        ctx.close()
        browser.close()

    print()
    if failures:
        print(f"FAIL: {len(failures)}/{checks} 项未通过")
        for f in failures:
            print("  -", f)
        raise SystemExit(1)
    print(f"PASS: jimeng batch 812 反馈文案一致性与信息量（{checks} 项断言全通过）")


if __name__ == "__main__":
    main()
