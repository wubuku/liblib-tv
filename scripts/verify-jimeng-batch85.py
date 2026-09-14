"""Jimeng clone batch 85 verifier — progress bars aligned to source.

Contract (SOURCE_FACT batch 85, 85-seek.json):
- card progress: 5px pill track (white/16%) with white/96% fill;
- fullscreen preview: full-width 5px seekable progress bar at the bottom
  (12px hit area); clicking at ~50% seeks the node to ~00:03.
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

        # ---- card progress bar style ----
        c = page.evaluate(
            """() => { const n = document.querySelector('[data-id="video-local-1"]');
                const r = n.getBoundingClientRect();
                return {x: r.x + 60, y: r.y + 20}; }"""
        )
        page.mouse.click(c["x"], c["y"])
        page.wait_for_timeout(700)
        bar = page.evaluate(
            """() => {
                const track = document.querySelector(
                    '[data-id="video-local-1"] .h-\\\\[5px\\\\]');
                if (!track) return null;
                const cs = getComputedStyle(track);
                const fill = track.firstElementChild;
                return {h: cs.height, bg: cs.backgroundColor,
                        radius: cs.borderRadius,
                        fillBg: fill ? getComputedStyle(fill).backgroundColor : null};
            }"""
        )
        if not bar:
            failures.append("card progress track not found")
        else:
            if bar["h"] != "5px":
                failures.append(f"card track height: {bar['h']} want 5px")
            if "0.16" not in bar["bg"]:
                failures.append(f"card track bg: {bar['bg']} want white/16")
            if "0.96" not in bar["fillBg"]:
                failures.append(f"card fill bg: {bar['fillBg']} want white/96")

        # ---- preview seek bar ----
        page.evaluate(
            """() => [...document.querySelectorAll('.react-flow__node-toolbar button')]
                .find(b => b.getAttribute('aria-label') === '全屏预览')?.click()"""
        )
        page.wait_for_timeout(900)
        bar2 = page.evaluate(
            """() => {
                const el = document.querySelector('[data-testid="preview-progress"]');
                if (!el) return null;
                const r = el.getBoundingClientRect();
                const inner = el.firstElementChild;
                const ics = inner ? getComputedStyle(inner) : null;
                return {w: Math.round(r.width), h: Math.round(r.height),
                        trackH: ics ? ics.height : null};
            }"""
        )
        if not bar2:
            failures.append("preview progress not found")
        else:
            if bar2["w"] < VIEWPORT["width"] - 4:
                failures.append(f"preview bar not full width: {bar2['w']}")
            if bar2["h"] != 12:
                failures.append(f"preview hit area: {bar2['h']} want 12")
            if bar2["trackH"] != "5px":
                failures.append(f"preview track: {bar2['trackH']} want 5px")
            # seek to 50%
            r = page.locator('[data-testid="preview-progress"]').bounding_box()
            page.mouse.click(r["x"] + r["width"] * 0.5, r["y"] + r["height"] / 2)
            page.wait_for_timeout(500)
            t = page.evaluate(
                """() => { const s = window.__jimengStore.getState();
                    const n = s.nodes.find(n => n.id === 'video-local-1');
                    return n.data.currentTime; }"""
            )
            if t is None or abs(t - 3.0) > 0.6:
                failures.append(f"preview seek to 50%: {t} want ~3.0")
            page.screenshot(
                path=str(REFERENCE_DIR / "jimeng-clone-batch85-preview-seek.png")
            )

        ctx.close()

    if failures:
        print("FAIL")
        for f in failures:
            print(" -", f)
        raise SystemExit(1)
    print("PASS: jimeng batch 85 progress bars contract")


if __name__ == "__main__":
    main()
