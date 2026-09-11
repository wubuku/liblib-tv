"""Jimeng clone batch 5 verifier — 局部重拍 editing mode.

Contract: selecting the media node, clicking 局部重拍 in the toolbar enters
repaint mode — title row hidden, filmstrip with 4.0s selection window, panel
with 重拍片段 chip, Seedance 2.5, 6s, credits 96/208, enabled white send button;
pane click exits back to the toolbar state.
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

        node1 = page.locator(".react-flow__node-video").first
        node1.click(position={"x": 200, "y": 100})
        page.wait_for_timeout(700)
        page.locator(".jimeng-node-toolbar button", has_text="局部重拍").click()
        page.wait_for_timeout(900)

        state = page.evaluate(
            """() => {
                const film = document.querySelector('[aria-label="生成"][type="submit"]')
                    ? [...document.querySelectorAll('form')].find(f =>
                        f.textContent.includes('重拍片段'))
                    : null;
                const title = [...document.querySelectorAll('.react-flow__node-video span')]
                    .some(s => s.textContent.includes('sb_518102884867410fb'));
                if (!film) return {panel: false};
                const r = film.getBoundingClientRect();
                const send = film.querySelector('button[aria-label="生成"]');
                return {
                    panel: true,
                    width: Math.round(r.width),
                    chip: film.textContent.includes('00:00—00:04 重拍片段'),
                    seedance25: film.textContent.includes('即梦 Seedance 2.5'),
                    duration6s: film.textContent.includes('6s'),
                    credits: film.textContent.includes('96') && film.textContent.includes('208'),
                    sendEnabled: send ? !send.disabled : false,
                    sendWhite: send ? getComputedStyle(send).backgroundColor === 'rgb(255, 255, 255)' : false,
                    filmstrip: !!film.closest('div').querySelector('div[class*="border-2"]'),
                    titleHidden: !title,
                };
            }"""
        )
        if not state.get("panel"):
            failures.append("repaint panel did not open")
        else:
            if not state["chip"]:
                failures.append("重拍片段 chip missing")
            if not state["seedance25"]:
                failures.append("Seedance 2.5 selector missing")
            if not state["duration6s"]:
                failures.append("6s duration missing")
            if not state["credits"]:
                failures.append("credits 96/208 missing")
            if not state["sendEnabled"] or not state["sendWhite"]:
                failures.append("send button not enabled/white")
            if not state["filmstrip"]:
                failures.append("filmstrip selection window missing")
            if not state["titleHidden"]:
                failures.append("node title should be hidden in repaint mode")
        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch5-repaint-mode-1680.png")
        )

        # pane click exits
        page.mouse.click(300, 700)
        page.wait_for_timeout(600)
        exited = page.evaluate(
            "() => ![...document.querySelectorAll('form')]"
            ".some(f => f.textContent.includes('重拍片段'))"
        )
        if not exited:
            failures.append("repaint mode did not exit on pane click")

        ctx.close()

    if failures:
        print("FAIL")
        for f in failures:
            print(" -", f)
        raise SystemExit(1)
    print("PASS: jimeng batch 5 repaint mode contract")
    print(f"screenshot: {REFERENCE_DIR / 'jimeng-clone-batch5-repaint-mode-1680.png'}")


if __name__ == "__main__":
    main()
