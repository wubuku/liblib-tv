"""Jimeng clone batch 34 verifier — frame capture contract (batch 203 semantics).

Contract (updated per 203 source sampling):
- 截取帧-自定义: clicking the filmstrip moves the playhead and time readout;
  截取帧 arms 确认; confirming CLOSES the picker and directly produces an
  image node titled「…_自定义」(source behavior — the old currentTime
  write-back was a mis-sampling, corrected in batch 203).
- 首帧 (batch 62 semantics): directly creates an image node (poster +
  「…_首帧」 title) instead of opening the frame picker.
"""

import os
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "docs" / "design-references" / "jimeng"
BASE_URL = os.environ.get("JIMENG_BASE_URL", "http://localhost:4317")

CANVAS_URL = f"{BASE_URL}/jimeng/canvas/demo"
VIEWPORT = {"width": 1680, "height": 826}


def open_picker(page, item: str):
    node1 = page.locator('.react-flow__node[data-id="video-local-1"]')
    node1.click(position={"x": 200, "y": 100})
    page.wait_for_timeout(500)
    page.locator(".jimeng-node-toolbar button", has_text="截取帧").click()
    page.wait_for_timeout(500)
    page.locator("button", has_text=item).first.click()
    page.wait_for_timeout(700)


def main() -> None:
    REFERENCE_DIR.mkdir(parents=True, exist_ok=True)
    failures: list[str] = []

    with sync_playwright() as p:
        ctx = p.chromium.launch(headless=True)
        page = ctx.new_page()
        page.set_viewport_size(VIEWPORT)  # type: ignore[arg-type]
        page.goto(CANVAS_URL, wait_until="domcontentloaded")
        page.wait_for_timeout(2500)

        # ── custom capture at ~70% ──
        open_picker(page, "自定义")
        strip = page.evaluate(
            """() => {
                const s = [...document.querySelectorAll('div')]
                    .find(d => d.querySelector('span[style*="width: 0%"], span[style*="left: 0%"]')
                              && d.className.includes('cursor-pointer'));
                const r = s.getBoundingClientRect();
                return {x: r.x, w: r.width, y: r.y + r.height/2};
            }"""
        )
        page.mouse.click(strip["x"] + strip["w"] * 0.7, strip["y"])
        page.wait_for_timeout(400)
        t_playhead = page.evaluate(
            """() => {
                const bar = [...document.querySelectorAll('form,div')]
                    .find(d => d.querySelector('[data-testid="frame-readout"]')
                               && d.textContent.includes('确认'));
                return bar?.querySelector('[data-testid="frame-readout"]')
                    ?.textContent.match(/(\\d\\d:\\d\\d)/)?.[1];
            }"""
        )
        if t_playhead != "00:04":
            failures.append(f"playhead after strip click: {t_playhead} (want 00:04)")

        page.locator("button", has_text="截取帧").click()
        page.wait_for_timeout(300)
        confirm_disabled = page.evaluate(
            """() => [...document.querySelectorAll('button')]
                .find(b => b.textContent.trim() === '确认')?.disabled ?? true"""
        )
        if confirm_disabled:
            failures.append("确认 still disabled after capture")
        page.locator("button", has_text="确认").last.click()
        page.wait_for_timeout(600)
        # batch 203 semantics: confirm → picker closed + image node「…_自定义」
        picker_gone = page.evaluate(
            """() => ![...document.querySelectorAll('form,div')]
                .some(d => d.querySelector('[data-testid="frame-readout"]')
                          && d.textContent.includes('确认'))"""
        )
        if not picker_gone:
            failures.append("picker did not close after 确认")
        img_custom = page.evaluate(
            """() => {
                const nodes = [...document.querySelectorAll('.react-flow__node-image')];
                const el = nodes[nodes.length - 1] ?? null;
                return {count: nodes.length,
                        title: el ? (el.textContent || '').trim().slice(0, 60) : null};
            }"""
        )
        if img_custom["count"] < 1:
            failures.append("确认 did not produce an image node (batch 203 semantics)")
        elif "_截帧_" not in (img_custom["title"] or ""):
            failures.append(f"custom capture title wrong: {img_custom['title']!r}")
        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch34-frame-capture-1680.png")
        )

        # ── 首帧 (batch 62 语义演进): 直接产出 image 节点，不开选择器 ──
        open_picker(page, "首帧")
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
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)
        page.mouse.click(300, 700)

        ctx.close()

    if failures:
        print("FAIL")
        for f in failures:
            print(" -", f)
        raise SystemExit(1)
    print("PASS: jimeng batch 34 frame capture contract")


if __name__ == "__main__":
    main()
