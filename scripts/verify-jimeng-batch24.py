"""Jimeng clone batch 24 verifier — double-click behaviors (source-extracted).

SOURCE_FACT (batch 24 extraction):
- double-click the video card center = restart playback from 0 (time resets,
  pause icon shows);
- double-click the node title opens the 添加节点 menu with the extended
  footer (从资产库添加 / 本地上传); Escape closes it.
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
        page.wait_for_timeout(2500)

        # restart-play on card double-click
        page.locator('.react-flow__node[data-id="video-local-1"]').dblclick(
            position={"x": 200, "y": 100}
        )
        page.wait_for_timeout(600)
        playing = page.evaluate(
            """() => {
                const n = document.querySelector('.react-flow__node[data-id="video-local-1"]');
                const pause = n.querySelector('button[aria-label="暂停"], button[aria-label="底部暂停"]');
                const m = n.textContent.match(/(\\d\\d:\\d\\d) \\/ /);
                return {pauseShown: !!pause && pause.offsetParent !== null,
                        time: m ? m[1] : null};
            }"""
        )
        if not playing["pauseShown"]:
            failures.append("video not playing after card dblclick")
        if playing["time"] not in ("00:00", "00:01"):
            failures.append(f"time after dblclick: {playing['time']} (want 00:00/00:01)")
        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch24-dblclick-replay-1680.png")
        )

        # pause it back
        page.locator('button[aria-label="暂停"]').first.click()
        page.wait_for_timeout(300)

        # title double-click opens extended insert menu
        title = page.evaluate(
            """() => {
                const n = document.querySelector('.react-flow__node[data-id="video-local-1"]');
                const r = n.getBoundingClientRect();
                return {x: r.x + 150, y: r.y - 12};
            }"""
        )
        page.mouse.dblclick(title["x"], title["y"])
        page.wait_for_timeout(700)
        menu = page.evaluate(
            """() => {
                const menus = [...document.querySelectorAll('[role="menu"]')]
                    .filter(m => m.textContent.includes('添加节点'));
                const m = menus[menus.length - 1];
                if (!m) return null;
                return {
                    items: [...m.querySelectorAll('[role="menuitem"]')]
                        .map(b => b.textContent.trim()),
                };
            }"""
        )
        if not menu:
            failures.append("insert menu did not open on title dblclick")
        else:
            want = [
                "文本", "图片", "视频", "音频", "时间线", "主体", "导演台",
                "从资产库添加", "本地上传",
            ]
            if menu["items"] != want:
                failures.append(f"extended menu items: {menu['items']}")
        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch24-title-menu-1680.png")
        )
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)
        closed = page.evaluate(
            "() => ![...document.querySelectorAll('[role=\"menu\"]')]"
            ".some(m => m.textContent.includes('添加节点'))"
        )
        if not closed:
            failures.append("insert menu did not close on Escape")

        ctx.close()

    if failures:
        print("FAIL")
        for f in failures:
            print(" -", f)
        raise SystemExit(1)
    print("PASS: jimeng batch 24 double-click contract")


if __name__ == "__main__":
    main()
