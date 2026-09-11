"""Jimeng clone batch 3 verifier — empty-node generation panel.

Contract: selecting the empty "视频 1" node opens the generation panel BELOW it
(680x208, r20, bg rgb(32,32,32)) with upload + button, prompt placeholder with
@主体 chip, model/params/duration selectors, credits and disabled send button;
deselect hides it. The media node keeps its toolbar (no panel).
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

        # select empty node
        node2 = page.locator(".react-flow__node-video").nth(1)
        node2.click(position={"x": 200, "y": 100})
        page.wait_for_timeout(800)

        panel = page.evaluate(
            """() => {
                const tbs = [...document.querySelectorAll('.react-flow__node-toolbar')]
                    .filter(t => t.textContent.includes('Seedance'));
                const tb = tbs[0];
                if (!tb) return null;
                const form = tb.querySelector('form');
                const r = form ? form.getBoundingClientRect() : null;
                const node = [...document.querySelectorAll('.react-flow__node-video')][1];
                const nr = node.getBoundingClientRect();
                return {
                    rect: r ? [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] : null,
                    bg: form ? getComputedStyle(form).backgroundColor : null,
                    radius: form ? getComputedStyle(form).borderRadius : null,
                    gapBelow: r ? Math.round(r.y - nr.bottom) : null,
                    centered: r ? Math.abs((r.x + r.width / 2) - (nr.x + nr.width / 2)) < 3 : null,
                    hasPlus: !!tb.querySelector('button[aria-label="上传参考图"]'),
                    hasMentionChip: tb.textContent.includes('主体'),
                    placeholder: tb.textContent.includes('上传参考图、输入文字或'),
                    selectors: ['即梦 Seedance 2.0 VIP', '16:9 · 720P', '全能参考', '4s']
                        .map(s => tb.textContent.includes(s)),
                    credits56: tb.textContent.includes('56'),
                    sendDisabled: tb.querySelector('button[aria-label="生成"]')?.disabled ?? null,
                    expand: !!tb.querySelector('button[aria-label="展开面板"]'),
                };
            }"""
        )
        if not panel or not panel["rect"]:
            failures.append("generation panel did not open on empty node selection")
        else:
            w, h = panel["rect"][2], panel["rect"][3]
            if abs(w - 680) > 4 or abs(h - 208) > 4:
                failures.append(f"panel size: want 680x208, got {w}x{h}")
            if panel["bg"] != "rgb(32, 32, 32)":
                failures.append(f"panel bg: {panel['bg']}")
            if panel["radius"] != "20px":
                failures.append(f"panel radius: {panel['radius']}")
            if panel["gapBelow"] is None or abs(panel["gapBelow"] - 20) > 3:
                failures.append(f"gap below node: {panel['gapBelow']}")
            if not panel["centered"]:
                failures.append("panel not centered on node")
            for label, ok in zip(
                ["model", "params", "reference", "duration"], panel["selectors"]
            ):
                if not ok:
                    failures.append(f"selector missing: {label}")
            if not panel["placeholder"]:
                failures.append("prompt placeholder missing")
            if not panel["hasMentionChip"]:
                failures.append("@主体 chip missing")
            if not panel["hasPlus"]:
                failures.append("upload + button missing")
            if not panel["credits56"]:
                failures.append("credits 56 missing")
            if panel["sendDisabled"] is not True:
                failures.append(f"send button disabled: {panel['sendDisabled']}")
            if not panel["expand"]:
                failures.append("expand button missing")

        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch3-genpanel-1680.png")
        )

        # media node must NOT show the panel
        node1 = page.locator(".react-flow__node-video").first
        node1.click(position={"x": 200, "y": 100})
        page.wait_for_timeout(700)
        media_panel = page.evaluate(
            "() => [...document.querySelectorAll('.react-flow__node-toolbar')]"
            ".some(t => t.textContent.includes('Seedance'))"
        )
        if media_panel:
            failures.append("generation panel opened for media node (should not)")
        page.mouse.click(300, 700)

        ctx.close()

    if failures:
        print("FAIL")
        for f in failures:
            print(" -", f)
        raise SystemExit(1)
    print("PASS: jimeng batch 3 generation panel contract")
    print(f"screenshot: {REFERENCE_DIR / 'jimeng-clone-batch3-genpanel-1680.png'}")


if __name__ == "__main__":
    main()
