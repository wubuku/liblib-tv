"""Jimeng clone batch 12 verifier — 与 AI 对话 drawer.

Contract: clicking the bottom-right button opens the right drawer
(新会话 header, 探索更多专业创作模式 empty state, 5 skill chips, input card
with disabled send), the button hides while open, and 收起/再点按钮 closes it.
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

    with sync_playwright() as p:
        ctx = p.chromium.launch(headless=True)
        page = ctx.new_page()
        page.set_viewport_size(VIEWPORT)  # type: ignore[arg-type]
        page.goto(CANVAS_URL, wait_until="domcontentloaded")
        page.wait_for_timeout(2200)

        page.locator("button", has_text="与 AI 对话").click()
        page.wait_for_timeout(800)

        drawer = page.evaluate(
            """() => {
                const d = document.querySelector('[aria-label="AI 对话"]');
                if (!d) return null;
                const r = d.getBoundingClientRect();
                return {
                    rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
                    header: d.textContent.includes('新会话'),
                    empty: d.textContent.includes('探索更多专业创作模式'),
                    chips: ['/ 视频反解','/ 创作分镜','/ 全流程广告片导演','/ 剧本开发','/ 剧情短片']
                        .map(c => d.textContent.includes(c)),
                    placeholder: !!d.querySelector('input[placeholder*="输入想法"]'),
                    sendDisabled: (() => {
                        const b = d.querySelector('button[aria-label="发送"]');
                        return b ? b.disabled : null;
                    })(),
                };
            }"""
        )
        if not drawer:
            failures.append("AI drawer did not open")
        else:
            x, y, w, h = drawer["rect"]
            if abs(w - 410) > 6 or h < 700:
                failures.append(f"drawer size: {w}x{h}")
            if not drawer["header"] or not drawer["empty"]:
                failures.append("drawer header/empty-state missing")
            if not all(drawer["chips"]):
                failures.append("skill chips missing")
            if not drawer["placeholder"]:
                failures.append("input placeholder missing")
            if drawer["sendDisabled"] is not True:
                failures.append("send should be disabled when empty")
        button_hidden = page.evaluate(
            "() => ![...document.querySelectorAll('button')]"
            ".some(b => b.textContent.includes('与 AI 对话'))"
        )
        if not button_hidden:
            failures.append("AI button should hide while drawer open")
        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch12-ai-drawer-1680.png")
        )

        page.locator('button[aria-label="收起"]').click()
        page.wait_for_timeout(500)
        closed = page.evaluate(
            "() => !document.querySelector('[aria-label=\"AI 对话\"]')"
        )
        if not closed:
            failures.append("drawer did not close on 收起")

        ctx.close()

    if failures:
        print("FAIL")
        for f in failures:
            print(" -", f)
        raise SystemExit(1)
    print("PASS: jimeng batch 12 AI drawer contract")


if __name__ == "__main__":
    main()
