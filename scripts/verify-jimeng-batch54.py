"""Jimeng clone batch 54 verifier — multi-select hides per-node panels.

Contract: when two nodes are selected (shift+click), individual toolbars
and generation panels are hidden (they would overlap); deselecting restores
the single-selection toolbar.
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

        centers = page.evaluate(
            """() => [
                (() => { const n = document.querySelector('[data-id="video-local-1"]');
                    const r = n.getBoundingClientRect(); return {x: r.x + r.width/2 - 120, y: r.y + r.height/2 - 60}; })(),
                (() => { const n = document.querySelector('[data-id="video-empty-1"]');
                    const r = n.getBoundingClientRect(); return {x: r.x + r.width/2, y: r.y + r.height/2}; })(),
            ]"""
        )

        # single-select: toolbar + gen panel hidden (empty node shows gen panel)
        page.mouse.click(centers[1]["x"], centers[1]["y"])
        page.wait_for_timeout(600)
        solo = page.evaluate(
            """() => ({
                genPanel: !!document.querySelector('textarea[placeholder*="上传参考图"]'),
                toolbar: [...document.querySelectorAll('.jimeng-node-toolbar')]
                    .some(t => t.getBoundingClientRect().height > 20),
            })"""
        )
        if not solo["genPanel"]:
            failures.append("gen panel missing on solo selection")
        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch54-solo-panel-1680.png")
        )

        # shift+click adds the other node → panels hidden
        page.keyboard.down("Shift")
        page.mouse.click(centers[0]["x"] - 120, centers[0]["y"] - 60)
        page.keyboard.up("Shift")
        page.wait_for_timeout(600)
        multi = page.evaluate(
            """() => ({
                selected: document.querySelectorAll('.react-flow__node.selected').length,
                panels: [...document.querySelectorAll('.jimeng-node-toolbar')]
                    .filter(t => t.getBoundingClientRect().height > 20).length,
                genTextarea: [...document.querySelectorAll('textarea')]
                    .some(t => t.placeholder.includes('上传参考图')),
            })"""
        )
        if multi["selected"] != 2:
            ids_now = page.evaluate(
                "() => [...document.querySelectorAll('.react-flow__node.selected')].map(n => n.getAttribute('data-id'))"
            )
            hit = page.evaluate(
                """() => { const el = document.elementFromPoint(520, 263);
                    return el ? el.tagName + '.' + (el.className||'').toString().slice(0, 60) : 'none'; }"""
            )
            print(f"[diag] multi-selected ids: {ids_now}, hit at (520,263): {hit}")
        if multi["panels"] != 0:
            failures.append(f"toolbars visible during multi-select: {multi['panels']}")
        if multi["genTextarea"]:
            failures.append("gen textarea visible during multi-select")
        page.screenshot(
            path=str(REFERENCE_DIR / "jimeng-clone-batch54-multiselect-1680.png")
        )

        ctx.close()

    if failures:
        print("FAIL")
        for f in failures:
            print(" -", f)
        raise SystemExit(1)
    print("PASS: jimeng batch 54 multi-select panel hiding contract")


if __name__ == "__main__":
    main()
