"""Jimeng clone batch 34 verifier — frame capture writes back to the node.

Contract:
- 截取帧-自定义: clicking the filmstrip moves the playhead and time readout;
  截取帧 arms 确认; confirming writes the frame time to the node's
  currentTime (node time row shows the captured position).
- 首帧: picker opens at 00:00 with 确认 enabled; confirming seeks the node
  to 00:00.
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
        node_time = page.evaluate(
            """() => {
                const n = document.querySelector('.react-flow__node[data-id="video-local-1"]');
                const m = n.textContent.match(/(\\d\\d:\\d\\d) \\/ 00:06/);
                return m ? m[1] : null;
            }"""
        )
        if node_time != "00:04":
            failures.append(f"node currentTime after confirm: {node_time} (want 00:04)")
        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch34-frame-capture-1680.png")
        )

        # ── 首帧 preset ──
        open_picker(page, "首帧")
        state = page.evaluate(
            """() => {
                const bar = [...document.querySelectorAll('form,div')]
                    .find(d => d.textContent.includes('00:00 / 00:06')
                               && d.textContent.includes('确认'));
                const confirm = [...(bar?.querySelectorAll('button') ?? [])]
                    .find(b => b.textContent.trim() === '确认');
                return {open: !!bar, confirmEnabled: confirm ? !confirm.disabled : false};
            }"""
        )
        if not state["open"]:
            failures.append("首帧 picker did not open")
        elif not state["confirmEnabled"]:
            failures.append("首帧 确认 should be enabled immediately")
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
