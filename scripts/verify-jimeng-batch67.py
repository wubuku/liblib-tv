"""Jimeng clone batch 67 verifier — media error state + grouped context menu.

Contract:
- SOURCE_FACT (67-cap-state.png): mediaError video shows 视频播放失败 text
  + white 重试播放视频 pill; clicking retry clears the error.
- CLONE_DECISION (extraction blocked by source selection container):
  grouped multi-selection context menu shows 解除编组 instead of 编组;
  clicking it ungroups.
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

        def center(node_id):
            return page.evaluate(
                """(id) => { const n = document.querySelector(`[data-id="${id}"]`);
                    const r = n.getBoundingClientRect();
                    return {x: r.x + 60, y: r.y + 20}; }""",
                node_id,
            )

        # ---- A. media error state ----
        page.evaluate(
            "() => window.__jimengStore.getState().setMediaError('video-local-1', true)"
        )
        page.wait_for_timeout(500)
        err = page.evaluate(
            """() => {
                const n = document.querySelector('[data-id="video-local-1"]');
                const text = n?.querySelector('[data-testid="media-error-text"]');
                const retry = n?.querySelector('[data-testid="media-error-retry"]');
                if (!text || !retry) return {present: false};
                const rs = getComputedStyle(retry);
                return {present: true,
                        text: text.textContent,
                        retryBg: rs.backgroundColor,
                        retryText: retry.textContent};
            }"""
        )
        if not err.get("present"):
            failures.append(f"media error overlay not rendered: {err}")
        else:
            if err["text"] != "视频播放失败":
                failures.append(f"error text wrong: {err['text']!r}")
            if err["retryText"] != "重试播放视频":
                failures.append(f"retry label wrong: {err['retryText']!r}")
            if err["retryBg"] != "rgb(255, 255, 255)":
                failures.append(f"retry pill not white: {err['retryBg']}")
            page.screenshot(
                path=str(REFERENCE_DIR / "jimeng-clone-batch67-media-error.png")
            )
            # click retry → error cleared
            page.evaluate(
                "() => window.__jimengStore.getState().setMediaError('video-local-1', true) "
                "=== undefined && document.querySelector('[data-id=\"video-local-1\"] [data-testid=\"media-error-retry\"]').click()"
            )
            page.wait_for_timeout(600)
            gone = page.evaluate(
                """() => !document.querySelector('[data-id="video-local-1"] [data-testid="media-error-text"]')"""
            )
            if not gone:
                failures.append("retry did not clear media error")

        # ---- B. grouped context menu variant ----
        for _ in range(3):
            page.mouse.click(300, 750)
            page.wait_for_timeout(300)
            c1 = center("video-local-1")
            c2 = center("video-empty-1")
            page.mouse.click(c1["x"], c1["y"])
            page.wait_for_timeout(300)
            page.keyboard.down("Shift")
            page.mouse.click(c2["x"], c2["y"])
            page.keyboard.up("Shift")
            page.wait_for_timeout(700)
            if page.evaluate(
                "() => document.querySelectorAll('.react-flow__node.selected').length"
            ) == 2:
                break
        mt = page.locator('[data-testid="jimeng-multi-toolbar"]')
        mt.locator('[data-testid="multi-group"]').click()
        page.wait_for_timeout(800)

        # right-click member → menu should show 解除编组 (grouped variant)
        c1 = center("video-local-1")
        page.mouse.click(c1["x"] + 140, c1["y"] + 130, button="right")
        page.wait_for_timeout(700)
        labels = page.evaluate(
            """() => [...document.querySelectorAll('button[role="menuitem"]')]
                .map(b => (b.textContent.trim().match(/^[\\u4e00-\\u9fff]+/) || [''])[0])"""
        )
        if "解除编组" not in labels:
            failures.append(f"grouped menu missing 解除编组: {labels}")
        if "编组" in labels:
            failures.append(f"grouped menu still has 编组: {labels}")
        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch67-grouped-menu.png")
        )
        # click 解除编组
        page.evaluate(
            """() => [...document.querySelectorAll('button[role="menuitem"]')]
                .find(b => b.textContent.trim().startsWith('解除编组'))?.click()"""
        )
        page.wait_for_timeout(700)
        gids = page.evaluate(
            """() => ['video-local-1', 'video-empty-1'].map(id => {
                const n = document.querySelector(`[data-id="${id}"] [data-group-id]`);
                return n ? n.getAttribute('data-group-id') : null;
            })"""
        )
        if any(gids):
            failures.append(f"menu 解除编组 did not ungroup: {gids}")

        ctx.close()

    if failures:
        print("FAIL")
        for f in failures:
            print(" -", f)
        raise SystemExit(1)
    print("PASS: jimeng batch 67 media error + grouped context menu contract")


if __name__ == "__main__":
    main()
