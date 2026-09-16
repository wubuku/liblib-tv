"""Jimeng clone batch 98 verifier — capture-frame upload transient (Batch 197).

Contract (SOURCE_FACT batch 197): a capture-frame image node starts in a
「正在上传图片 N%」 uploading state and settles into the normal node within
~1.5s (mock: 0% → 46% @0.5s → 100% @1.0s, overlay hidden at 100%).

Assertions:
- right after 首帧, [data-jimeng-image-uploading] exists, text matches
  /正在上传图片 \\d+%/, and progress starts at 0%;
- ~2s later the overlay is gone and the title keeps the「…_首帧」form;
- undo restores baseline.
"""

import os
import re
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

        n0 = page.evaluate(
            "() => document.querySelectorAll('.react-flow__node').length"
        )

        # select video-local-1 (off-center: play button swallows center clicks)
        center = page.evaluate(
            """() => {
                const el = document.querySelector('[data-id="video-local-1"]');
                const r = el.getBoundingClientRect();
                return {x: r.x + r.width / 2 - 120, y: r.y + 40};
            }"""
        )
        page.mouse.click(center["x"], center["y"])
        page.wait_for_timeout(600)
        cap = page.evaluate(
            """() => {
                const t = [...document.querySelectorAll('.react-flow__node-toolbar')]
                    .find(t => t.textContent.includes('截取帧'));
                const btn = t && [...t.querySelectorAll('button')]
                    .find(b => b.textContent.trim() === '截取帧');
                if (!btn) return null;
                const r = btn.getBoundingClientRect();
                return {x: r.x + r.width / 2, y: r.y + r.height / 2};
            }"""
        )
        if not cap:
            failures.append("截取帧 button not found")
        else:
            page.mouse.click(cap["x"], cap["y"])
            page.wait_for_timeout(400)
            first = page.evaluate(
                """() => {
                    const btn = [...document.querySelectorAll('button')]
                        .find(b => b.textContent.trim() === '首帧'
                            && b.getBoundingClientRect().height < 50);
                    if (!btn) return null;
                    const r = btn.getBoundingClientRect();
                    return {x: r.x + r.width / 2, y: r.y + r.height / 2};
                }"""
            )
            if not first:
                failures.append("首帧 menu item not found")
            else:
                page.mouse.click(first["x"], first["y"])
                page.wait_for_timeout(300)

                up = page.evaluate(
                    """() => {
                        const el = document.querySelector('[data-jimeng-image-uploading]');
                        if (!el) return null;
                        return {text: (el.textContent || '').trim(),
                                progress: el.getAttribute('data-jimeng-image-progress')};
                    }"""
                )
                if not up:
                    failures.append("uploading overlay not visible right after 首帧")
                elif not re.search(r"正在上传图片 \d+%", up["text"]):
                    failures.append(f"uploading label wrong: {up['text']!r}")
                elif up["text"] != "正在上传图片 0%":
                    failures.append(
                        f"upload should start at 0%: {up['text']!r}"
                    )
                else:
                    page.screenshot(
                        path=str(REFERENCE_DIR / "jimeng-clone-batch98-upload.png")
                    )

                page.wait_for_timeout(2000)
                gone = page.evaluate(
                    "() => !document.querySelector('[data-jimeng-image-uploading]')"
                )
                if not gone:
                    failures.append("uploading overlay still visible after 2.3s")
                img = page.evaluate(
                    """() => {
                        const nodes = [...document.querySelectorAll('.react-flow__node-image')];
                        const el = nodes[nodes.length - 1];
                        return el ? (el.textContent || '').trim().slice(0, 80) : null;
                    }"""
                )
                if not img or "_首帧" not in img:
                    failures.append(f"image title wrong after upload: {img!r}")

                n1 = page.evaluate(
                    "() => document.querySelectorAll('.react-flow__node').length"
                )
                if n1 != n0 + 1:
                    failures.append(f"node count wrong: {n1} vs {n0 + 1}")

        page.keyboard.press("Meta+z")
        page.wait_for_timeout(600)
        n2 = page.evaluate(
            "() => document.querySelectorAll('.react-flow__node').length"
        )
        if n2 != n0:
            failures.append(f"undo failed: {n2} vs {n0}")

        ctx.close()

    if failures:
        print("FAIL batch 98:")
        for f in failures:
            print("  -", f)
        raise SystemExit(1)
    print("PASS batch 98: capture-frame upload transient (0% → hidden ≤2.3s)")


if __name__ == "__main__":
    main()
