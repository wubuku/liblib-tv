"""Jimeng clone batch 103 verifier — text node editing toolbar (Batch 241).

Contract (SOURCE_FACT 241-source-text-edit.png): double-clicking a text
card enters inline editing and shows a rich-text toolbar above the card —
字体∨ / 无序列表 / 有序列表 / 加粗 / 删除线 / 斜体 / 下划线 / 展开编辑 —
8 buttons in a dark pill; the empty-state hint 双击编辑文本 is
replaced by the focused editor; Escape exits editing.

批 816 订正两处：
- 编辑面从 <textarea> 改成 **contenteditable DIV**（源站实测 activeElement.ce=true，
  按 ⌘B 会把 <p>文字</p> 改写成 <p><strong>文字</strong></p>）。故此处断言
  contenteditable 而不是 textarea。
- 按钮不再是「视觉 mock」，7 个已接上真行为（见 verify-jimeng-batch816.py）。
  本文件只守**结构契约**（按钮顺序/数量/占位提示消失），行为断言归 816。
"""

import os
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "docs" / "design-references" / "jimeng"
BASE_URL = os.environ.get("JIMENG_BASE_URL", "http://localhost:4317")

CANVAS_URL = f"{BASE_URL}/jimeng/canvas/demo"
VIEWPORT = {"width": 1680, "height": 826}

# 批 817 订正：第 1 与第 8 个的名字是批 241 **猜的**（「字体」「展开编辑」）。
# 源站逐项实测的 aria-label 是 "Text style"（48×32，唯一带 chevron）与「全屏」
# （32×32，点开的面板叫「全屏编辑」）。见 verify-jimeng-batch817.py 与 README §26。
WANT_BUTTONS = [
    "Text style",
    "无序列表",
    "有序列表",
    "加粗",
    "删除线",
    "斜体",
    "下划线",
    "全屏",
]


def main() -> None:
    REFERENCE_DIR.mkdir(parents=True, exist_ok=True)
    failures: list[str] = []

    with sync_playwright() as p:
        ctx = p.chromium.launch(headless=True)
        page = ctx.new_page()
        page.set_viewport_size(VIEWPORT)  # type: ignore[arg-type]
        page.goto(CANVAS_URL, wait_until="domcontentloaded")
        page.wait_for_timeout(2200)

        page.locator('aside button[aria-label="文本"]').click()
        page.wait_for_timeout(900)

        card = page.locator(".react-flow__node-text")
        card.dblclick()
        page.wait_for_timeout(600)

        tb = page.evaluate(
            """() => {
                const bar = document.querySelector('[data-testid="text-format-toolbar"]');
                if (!bar) return null;
                return {
                    buttons: [...bar.querySelectorAll('button')]
                        .map(b => b.getAttribute('aria-label')),
                    hasTextarea: !!document.querySelector(
                        '.react-flow__node-text textarea'),
                    // 批 816: 源站编辑面是 contenteditable DIV，不是 textarea
                    hasEditor: !!document.querySelector(
                        '[data-testid="text-rich-editor"]'),
                    editorIsCE: (() => {
                        const ed = document.querySelector(
                            '[data-testid="text-rich-editor"]');
                        return !!ed && ed.isContentEditable;
                    })(),
                    hintGone: ![...document.querySelectorAll(
                        '.react-flow__node-text p')]
                        .some(p => p.textContent.trim() === '双击编辑文本'),
                };
            }"""
        )
        if not tb:
            failures.append("text format toolbar missing in editing mode")
        else:
            if tb["buttons"] != WANT_BUTTONS:
                failures.append(f"toolbar buttons: {tb['buttons']}")
            if not tb["hasEditor"] or not tb["editorIsCE"]:
                # 批 816 订正：源站编辑面是 contenteditable DIV，不是 textarea
                failures.append("contenteditable 编辑面缺失")
            if not tb["hintGone"]:
                failures.append("双击编辑文本 hint still visible while editing")
        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch103-text-toolbar.png")
        )

        # Escape exits editing
        page.keyboard.press("Escape")
        page.wait_for_timeout(400)
        gone = page.evaluate(
            "() => !document.querySelector('[data-testid=\"text-format-toolbar\"]')"
        )
        if not gone:
            failures.append("Escape did not exit editing")

        ctx.close()

    if failures:
        print("FAIL batch 103:")
        for f in failures:
            print("  -", f)
        raise SystemExit(1)
    print("PASS batch 103: text editing rich-text toolbar (8 buttons)")


if __name__ == "__main__":
    main()
