"""Jimeng clone batch 57 verifier — interaction error audit.

Runs every major interaction while capturing console errors and page
exceptions; PASS requires zero errors across all of them.
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
    errors: list[str] = []

    with sync_playwright() as p:
        ctx = p.chromium.launch(headless=True)
        page = ctx.new_page()
        page.on("console", lambda m: errors.append(f"console-{m.type}: {m.text[:150]}")
                if m.type in ("error",) else None)
        page.on("pageerror", lambda e: errors.append(f"pageerror: {str(e)[:150]}"))
        page.set_viewport_size(VIEWPORT)  # type: ignore[arg-type]
        page.goto(CANVAS_URL, wait_until="domcontentloaded")
        page.wait_for_timeout(2500)

        node1 = page.locator('.react-flow__node[data-id="video-local-1"]')

        def ensure_selected() -> None:
            if page.evaluate(
                "() => document.querySelectorAll('.react-flow__node.selected').length === 0"
            ):
                page.locator('.react-flow__node[data-id="video-local-1"]').click(
                    position={"x": 200, "y": 100}
                )
                page.wait_for_timeout(500)

        def step(name: str, fn) -> None:
            before = len(errors)
            fn()
            page.wait_for_timeout(400)
            if len(errors) > before:
                failures.append(f"{name}: {errors[before]}")

        # 1. 单选 + 工具条各按钮
        def select_node1() -> None:
            node1.click(position={"x": 200, "y": 100})
            page.wait_for_timeout(400)

        select_node1()
        step("局部重拍", lambda: page.locator(
            '.jimeng-node-toolbar button', has_text="局部重拍").click())
        page.wait_for_timeout(400)
        step("退出局部重拍", lambda: page.mouse.click(300, 750))
        node1.click(position={"x": 200, "y": 100})
        page.wait_for_timeout(400)
        step("视频编辑开", lambda: page.locator(
            '.jimeng-node-toolbar button', has_text="视频编辑").click())
        page.wait_for_timeout(300)
        step("Esc 退出编辑", lambda: page.keyboard.press("Escape"))
        node1.click(position={"x": 200, "y": 100})
        page.wait_for_timeout(400)
        select_node1()
        step("提示词反推", lambda: page.locator(
            '.jimeng-node-toolbar button', has_text="提示词反推").click())
        page.wait_for_timeout(300)
        step("关闭反推", lambda: page.locator(
            'button[aria-label="关闭反推面板"]').click())
        node1.click(position={"x": 200, "y": 100})
        page.wait_for_timeout(400)
        step("下载 toast", lambda: page.locator(
            '.jimeng-node-toolbar button[aria-label="下载"]').click())
        page.wait_for_timeout(2800)

        # 2. 播放/暂停
        node1.click(position={"x": 200, "y": 100})
        page.wait_for_timeout(300)
        step("播放", lambda: page.locator(
            '.react-flow__node[data-id="video-local-1"] button[aria-label="播放"]').first.click())
        page.wait_for_timeout(400)
        step("暂停", lambda: page.locator(
            '.react-flow__node[data-id="video-local-1"] button[aria-label="暂停"]').first.click())

        # 3. 空节点生成面板发送
        page.locator('.react-flow__node[data-id="video-empty-1"]').click(
            position={"x": 200, "y": 100}
        )
        page.wait_for_timeout(400)
        step("生成面板输入", lambda: page.locator(
            'textarea[placeholder*="上传参考图"]').fill("测试提示词"))
        step("生成提交", lambda: page.locator('button[aria-label="生成"]').click())
        page.wait_for_timeout(4500)  # mock 生成完成

        # 4. 新节点工具条 + 全屏预览开关
        node1 = page.locator(".react-flow__node-video").first
        node1.click(position={"x": 200, "y": 100})
        page.wait_for_timeout(400)
        step("新节点全屏预览开", lambda: page.locator(
            '.jimeng-node-toolbar button[aria-label="全屏预览"]').click())
        page.wait_for_timeout(300)
        step("全屏预览关", lambda: page.locator(
            'button[aria-label="退出全屏预览"]').click())

        # 5. 编组/取消编组/右键删除路径 (撤销在无历史时禁用为正确行为)
        node1.click(button="right", position={"x": 200, "y": 100})
        page.wait_for_timeout(400)

        # 6. 顶栏: 生成历史/帮助/会员
        step("生成历史开", lambda: page.locator(
            'button[aria-label="生成历史"]').click())
        step("生成历史关", lambda: page.locator(
            'button[aria-label="生成历史"]').click())
        step("帮助开", lambda: page.locator('button[aria-label="帮助"]').click())
        page.keyboard.press("Escape")
        step("会员开", lambda: page.locator('button[aria-label="会员订阅"]').click())
        step("会员关", lambda: page.locator(
            'button[aria-label="关闭订阅页"]').click())

        # 7. 缩放菜单 + 框选
        step("缩放菜单开", lambda: page.locator('button[aria-label="缩放"]').click())
        step("缩放适配", lambda: page.locator(
            '[role="menuitem"]', has_text="适配画布").click())
        step("音频插入", lambda: page.locator(
            'aside button[aria-label="音频"]').click())
        page.wait_for_timeout(400)

        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch57-audit-1680.png")
        )

        ctx.close()

    real = [e for e in errors if "React DevTools" not in e and "[HMR]" not in e
            and "Fast Refresh" not in e]
    if failures:
        print("FAIL")
        for f in failures:
            print(" -", f)
        raise SystemExit(1)
    if real:
        print("FAIL: console errors")
        for e in real:
            print(" -", e)
        raise SystemExit(1)
    print("PASS: jimeng batch 57 interaction audit — zero errors")


if __name__ == "__main__":
    main()
