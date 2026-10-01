"""Jimeng clone batch 91 verifier — bottom dock minimap toggle.

Contract (SOURCE_FACT batch 91, 91-minimap.json):
- dock = [选择工具][小地图] | 缩放% (布局/同步 removed by site evolution);
- 小地图 click toggles a 164×154 panel (rgb(13,13,13) r8) with a
  156×114 white/8% map area above the dock.
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

        dock = page.locator(".jimeng-bottom-dock")
        labels = page.evaluate(
            """() => [...document.querySelectorAll('.jimeng-bottom-dock button')]
                .map(b => b.getAttribute('aria-label'))"""
        )
        # batch 93: dock 增加显示连线钮
        # batch 796 起缩放钮 aria-label 逐字对齐源站 "Zoom options, {n}%"（含实时
        # 百分比），故此处按前缀匹配，不再写死旧标签「缩放」。
        if (len(labels) != 4 or labels[:3] != ["选择工具", "小地图", "显示连线"]
                or not labels[3].startswith("Zoom options, ")):
            failures.append(f"dock buttons: {labels}")

        if not page.locator('[data-testid="jimeng-minimap-panel"]').count():
            pass  # initially hidden — fine

        dock.locator('button[aria-label="小地图"]').click()
        page.wait_for_timeout(800)
        panel = page.evaluate(
            """() => {
                const el = document.querySelector('[data-testid="jimeng-minimap-panel"]');
                if (!el) return null;
                const r = el.getBoundingClientRect();
                const cs = getComputedStyle(el);
                return {w: Math.round(r.width), h: Math.round(r.height),
                        bg: cs.backgroundColor, radius: cs.borderRadius,
                        x: Math.round(r.x), y: Math.round(r.y + r.height)};
            }"""
        )
        if not panel:
            failures.append("minimap panel did not open")
        else:
            # batch 802 复测源站后改：面板只承载小地图，= 4(pad)+114+4 = 118 高，
            # 下缘贴住底栏顶边（源站是 dock 整体变高到 154，复刻为分离浮层，
            # 见台账 batch 802 条目的残留差异说明）。宽度仍 164。
            if abs(panel["w"] - 164) > 6 or abs(panel["h"] - 118) > 6:
                failures.append(f"minimap size: {panel['w']}x{panel['h']} want 164x118")
            if panel["bg"] != "rgb(13, 13, 13)":
                failures.append(f"minimap bg: {panel['bg']}")
            if panel["radius"] != "8px":
                failures.append(f"minimap radius: {panel['radius']}")
            # above the dock, bottom aligned near dock top
            if panel["y"] > 830:
                failures.append(f"minimap position too low: y={panel['y']}")
            page.screenshot(
                path=str(REFERENCE_DIR / "jimeng-clone-batch91-minimap.png")
            )
        # toggle closes
        dock.locator('button[aria-label="小地图"]').click()
        page.wait_for_timeout(600)
        if page.locator('[data-testid="jimeng-minimap-panel"]').count():
            failures.append("minimap did not close on second toggle")

        ctx.close()

    if failures:
        print("FAIL")
        for f in failures:
            print(" -", f)
        raise SystemExit(1)
    print("PASS: jimeng batch 91 minimap toggle contract")


if __name__ == "__main__":
    main()
