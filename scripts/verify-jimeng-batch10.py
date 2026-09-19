"""Jimeng clone batch 10 verifier — 视频修剪 trim mode + 首帧/尾帧 presets.

Contract (首帧/尾帧 semantics updated by batch 62 source evidence):
- 视频修剪 opens a trim bar: filmstrip with BOTH end brackets, duration label
  (6.0s), time row, white ENABLED 确认; confirming exits.
- 截取帧 首帧/尾帧 DIRECTLY create image nodes (poster + 「… 首帧/尾帧」
  titles) instead of opening the frame picker; the picker is 自定义-only.
"""

import os
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "docs" / "design-references" / "jimeng"
BASE_URL = os.environ.get("JIMENG_BASE_URL", "http://localhost:4317")

CANVAS_URL = f"{BASE_URL}/jimeng/canvas/demo"
VIEWPORT = {"width": 1680, "height": 826}


def open_trim_dropdown_item(page, item_text):
    page.locator(".jimeng-node-toolbar button", has_text="截取帧").click()
    page.wait_for_timeout(500)
    page.locator("button", has_text=item_text).first.click()
    page.wait_for_timeout(700)


def main() -> None:
    REFERENCE_DIR.mkdir(parents=True, exist_ok=True)
    failures: list[str] = []

    with sync_playwright() as p:
        ctx = p.chromium.launch(headless=True)
        page = ctx.new_page()
        page.set_viewport_size(VIEWPORT)  # type: ignore[arg-type]
        page.goto(CANVAS_URL, wait_until="domcontentloaded")
        page.wait_for_timeout(2200)

        node1 = page.locator(".react-flow__node-video").first
        node1.click(position={"x": 200, "y": 100})
        page.wait_for_timeout(700)

        # ── trim mode ──
        page.locator(".jimeng-node-toolbar button", has_text="视频修剪").click()
        page.wait_for_timeout(800)
        trim = page.evaluate(
            """() => {
                const form = [...document.querySelectorAll('form,div')]
                    .find(d => d.querySelector('button') &&
                              /\\d{2}:\\d{2} \\/ 00:06/.test(d.textContent) &&
                              d.textContent.includes('确认'));
                if (!form) return null;
                const confirm = [...form.querySelectorAll('button')]
                    .find(b => b.textContent.trim() === '确认');
                const brackets = form.querySelectorAll('span.h-12').length;
                return {
                    open: true,
                    confirmWhite: confirm ? getComputedStyle(confirm).backgroundColor === 'rgb(255, 255, 255)' : false,
                    confirmEnabled: confirm ? !confirm.disabled : false,
                    brackets,
                    durationLabel: form.textContent.includes('6.0s'),
                };
            }"""
        )
        if not trim:
            failures.append("trim panel did not open")
        else:
            if not trim["confirmWhite"] or not trim["confirmEnabled"]:
                failures.append(f"trim 确认 not white/enabled: {trim}")
            if trim["brackets"] < 2:
                failures.append(f"trim end brackets: {trim['brackets']} (want 2)")
            if not trim["durationLabel"]:
                failures.append("trim duration label missing")
        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch10-trim-1680.png")
        )
        page.locator("button", has_text="确认").first.click()
        page.wait_for_timeout(500)

        # ── 首帧 (batch 62 语义演进): 直接产出 image 节点，不开帧选择器 ──
        open_trim_dropdown_item(page, "首帧")
        first = page.evaluate(
            """() => {
                const nodes = [...document.querySelectorAll('.react-flow__node-image')];
                const el = nodes[nodes.length - 1] ?? null;
                return {count: nodes.length,
                        hasPoster: el ? !!el.querySelector('img') : false,
                        title: el ? (el.textContent || '').trim() : null};
            }"""
        )
        if first["count"] < 1:
            failures.append("首帧 did not create an image node (batch 62 semantics)")
        elif not first["hasPoster"] or not first["title"] or "首帧" not in first["title"]:
            failures.append(f"首帧 image node wrong: {first}")
        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch10-first-frame-1680.png")
        )
        page.keyboard.press("Escape")
        page.mouse.click(300, 700)
        page.wait_for_timeout(400)

        # ── 尾帧 (batch 62 语义演进): 直接产出第二个 image 节点 ──
        node1.click(position={"x": 200, "y": 100})
        page.wait_for_timeout(600)
        open_trim_dropdown_item(page, "尾帧")
        last = page.evaluate(
            """() => {
                const nodes = [...document.querySelectorAll('.react-flow__node-image')];
                const el = nodes[nodes.length - 1] ?? null;
                return {count: nodes.length,
                        title: el ? (el.textContent || '').trim() : null};
            }"""
        )
        if last["count"] < 2:
            failures.append("尾帧 did not create a second image node (batch 62)")
        elif not last["title"] or "尾帧" not in last["title"]:
            failures.append(f"尾帧 image node title wrong: {last}")
        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch10-last-frame-1680.png")
        )

        ctx.close()

    if failures:
        print("FAIL")
        for f in failures:
            print(" -", f)
        raise SystemExit(1)
    print("PASS: jimeng batch 10 trim + frame presets contract")


if __name__ == "__main__":
    main()
